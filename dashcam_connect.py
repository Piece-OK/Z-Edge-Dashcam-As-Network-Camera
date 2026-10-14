"""Initialize a Z-Edge dashcam and keep its RTSP stream awake."""

import argparse
import datetime
import ipaddress
import logging
import math
import socket
import time
import urllib.error
import urllib.request

VERSION = "1.0.0"
LOG = logging.getLogger(__name__)


def positive_seconds(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be a finite number greater than zero")
    return number


def port_number(value):
    number = int(value)
    if not 1 <= number <= 65535:
        raise argparse.ArgumentTypeError("must be between 1 and 65535")
    return number


def ipv4_address(value):
    try:
        return str(ipaddress.IPv4Address(value))
    except ipaddress.AddressValueError as exc:
        raise argparse.ArgumentTypeError("must be an IPv4 address") from exc


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument("--ip", type=ipv4_address, default="192.168.42.1", help="camera IPv4 address (default: %(default)s)")
    parser.add_argument("--http-port", type=port_number, default=80)
    parser.add_argument("--heartbeat-port", type=port_number, default=3333)
    parser.add_argument("--interval", type=positive_seconds, default=3, help="heartbeat interval in seconds (default: %(default)s)")
    parser.add_argument("--timeout", type=positive_seconds, default=5, help="network timeout in seconds (default: %(default)s)")
    parser.add_argument("--retry-delay", type=positive_seconds, default=3, help="reconnection delay in seconds (default: %(default)s)")
    parser.add_argument("--verbose", action="store_true", help="log initialization requests and heartbeat responses")
    return parser.parse_args(argv)


def send_http_init(config):
    """Replay the original app sequence, including its two clock-sync requests."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    paths = [
        "/?custom=1&msg_id=1",
        "/?custom=1&msg_id=20",
        "/?custom=1&msg_id=6",
        f"/?custom=1&msg_id=8&param1=time&param2=auto,{timestamp}",
        "/?custom=1&msg_id=21",
        f"/?custom=1&msg_id=8&param1=time&param2=auto,{timestamp}",
        "/?custom=1&msg_id=19",
    ]
    # Local camera traffic should bypass any system HTTP proxy.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    LOG.info("Initializing camera at %s:%s", config.ip, config.http_port)
    for path in paths:
        LOG.debug("GET %s", path)
        with opener.open(f"http://{config.ip}:{config.http_port}{path}", timeout=config.timeout):
            pass


def heartbeat(config):
    """Run one TCP session; EOF and network failures trigger the caller's retry."""
    with socket.create_connection((config.ip, config.heartbeat_port), timeout=config.timeout) as connection:
        confirmed = False
        while True:
            connection.sendall(b"hi")
            response = connection.recv(1024)
            if not response:
                raise ConnectionError("camera closed the heartbeat connection")
            LOG.debug("Heartbeat response: %r", response)
            if not confirmed:
                LOG.info("Heartbeat responding. Open rtsp://%s/stream0/svc0// in VLC or another RTSP player.", config.ip)
                LOG.info("Leave this window open while streaming. Press Ctrl+C to stop.")
                confirmed = True
            time.sleep(config.interval)


def run(config):
    while True:
        try:
            send_http_init(config)
            heartbeat(config)
        except (OSError, urllib.error.URLError) as exc:
            LOG.warning("Camera connection failed: %s. Retrying in %ss...", exc, config.retry_delay)
            time.sleep(config.retry_delay)


def main(argv=None):
    config = parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if config.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    try:
        run(config)
    except KeyboardInterrupt:
        LOG.info("Stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

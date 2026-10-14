import contextlib
import http.server
import io
import threading
import unittest
import urllib.error
from unittest.mock import patch, MagicMock
from urllib.parse import parse_qs, urlsplit

import dashcam_connect as app


class DashcamTests(unittest.TestCase):
    def test_defaults_and_custom_options(self):
        self.assertEqual(app.parse_args([]).ip, "192.168.42.1")
        config = app.parse_args(["--ip", "127.0.0.1", "--http-port", "8080", "--interval", "0.5"])
        self.assertEqual((config.http_port, config.interval), (8080, 0.5))

    def test_invalid_settings(self):
        for option, value in [("--ip", "host/path"), ("--http-port", "0"), ("--heartbeat-port", "65536"), ("--interval", "0"), ("--timeout", "nan"), ("--retry-delay", "inf"), ("--timeout", "-1")]:
            with self.subTest(option=option, value=value), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    app.parse_args([option, value])
                self.assertEqual(caught.exception.code, 2)

    def test_real_http_sequence_and_error_handling(self):
        paths = []
        status = [200]

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                paths.append(self.path)
                self.send_response(status[0])
                self.end_headers()

            def log_message(self, *args):
                pass

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            config = app.parse_args(["--ip", "127.0.0.1", "--http-port", str(server.server_port)])
            with patch.dict("os.environ", {"http_proxy": "http://127.0.0.1:1"}):
                app.send_http_init(config)
            queries = [parse_qs(urlsplit(path).query) for path in paths]
            self.assertEqual([q["msg_id"][0] for q in queries], ["1", "20", "6", "8", "21", "8", "19"])
            self.assertEqual(queries[3], queries[5])
            self.assertEqual(queries[3]["param1"], ["time"])
            self.assertTrue(queries[3]["param2"][0].startswith("auto,"))
            paths.clear()
            status[0] = 503
            with self.assertRaises(urllib.error.HTTPError):
                app.send_http_init(config)
            self.assertEqual(len(paths), 1)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_heartbeat_eof_closes_socket_without_success_message(self):
        connection = MagicMock()
        connection.__enter__.return_value = connection
        connection.recv.return_value = b""
        with patch.object(app.socket, "create_connection", return_value=connection), patch.object(app.LOG, "info") as log:
            with self.assertRaises(ConnectionError):
                app.heartbeat(app.parse_args([]))
        connection.sendall.assert_called_once_with(b"hi")
        connection.__exit__.assert_called_once()
        log.assert_not_called()

    def test_heartbeat_response_then_disconnect(self):
        connection = MagicMock()
        connection.__enter__.return_value = connection
        connection.recv.side_effect = [b"fuck.", b""]
        with patch.object(app.socket, "create_connection", return_value=connection), patch.object(app.time, "sleep") as sleep, self.assertLogs(app.LOG, level="INFO") as logs:
            with self.assertRaises(ConnectionError):
                app.heartbeat(app.parse_args([]))
        self.assertIn("rtsp://192.168.42.1/stream0/svc0//", logs.output[0])
        sleep.assert_called_once_with(3)

    def test_initialization_failure_retries_before_heartbeat(self):
        config = app.parse_args([])
        with patch.object(app, "send_http_init", side_effect=[OSError("offline"), None]) as init, patch.object(app, "heartbeat", side_effect=KeyboardInterrupt) as heartbeat, patch.object(app.time, "sleep") as sleep, self.assertLogs(app.LOG, level="WARNING"):
            with self.assertRaises(KeyboardInterrupt):
                app.run(config)
        self.assertEqual(init.call_count, 2)
        heartbeat.assert_called_once_with(config)
        sleep.assert_called_once_with(config.retry_delay)

    def test_disconnect_reinitializes_camera(self):
        with patch.object(app, "send_http_init") as init, patch.object(app, "heartbeat", side_effect=[ConnectionError("closed"), KeyboardInterrupt]), patch.object(app.time, "sleep"), self.assertLogs(app.LOG, level="WARNING"):
            with self.assertRaises(KeyboardInterrupt):
                app.run(app.parse_args([]))
        self.assertEqual(init.call_count, 2)

    def test_ctrl_c_exits_cleanly(self):
        with patch.object(app, "run", side_effect=KeyboardInterrupt):
            self.assertEqual(app.main([]), 0)


if __name__ == "__main__":
    unittest.main()

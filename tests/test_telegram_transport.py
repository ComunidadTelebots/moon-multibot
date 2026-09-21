import unittest
from unittest.mock import Mock, patch
from core.telegram_api import create_telegram_session, telegram_api_call


class TelegramTransportTests(unittest.TestCase):
    def test_session_reuses_a_completed_http_connection(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from threading import Thread

        connections = []
        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"
            def setup(self):
                super().setup()
                connections.append(self.connection)
            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length", 0)))
                body = b'{"ok":true}'
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with create_telegram_session() as session:
                # Exercise the Telegram adapter against a local HTTP/1.1 fixture.
                session.mount("http://127.0.0.1/", session.get_adapter("https://api.telegram.org/"))
                url = f"http://127.0.0.1:{server.server_port}/"
                session.mount(url, session.get_adapter("https://api.telegram.org/"))
                for _ in range(3):
                    self.assertTrue(telegram_api_call(session, url, "getMe")["ok"])
                self.assertEqual(len(connections), 1)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_final_rate_limit_returns_immediately_and_preserves_retry_after(self):
        payload = {'ok': False, 'error_code': 429, 'parameters': {'retry_after': 15}}
        session = Mock()
        session.post.return_value.json.return_value = payload
        with patch('core.telegram_api.time.sleep') as sleep:
            result = telegram_api_call(session, 'https://api.telegram.org/bottest/', 'sendMessage')
        self.assertEqual(result, payload)
        self.assertEqual(session.post.call_count, 3)
        self.assertEqual([call.args for call in sleep.call_args_list], [(15,), (15,)])

    def test_single_attempt_rate_limit_never_sleeps(self):
        session = Mock()
        session.post.return_value.json.return_value = {'ok': False, 'error_code': 429}
        with patch('core.telegram_api.time.sleep') as sleep:
            telegram_api_call(session, 'https://api.telegram.org/bottest/', 'sendMessage', _retries=1)
        sleep.assert_not_called()

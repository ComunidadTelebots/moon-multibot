import os
import unittest
from unittest.mock import patch
from core.bot_endpoint import api_root, bot_api_url, bot_file_url, uses_local_api
from core.traffic_control import identity
from core.operations_telemetry import OperationsTelemetry


class EndpointTests(unittest.TestCase):
    def test_only_selected_bot_uses_gateway(self):
        with patch.dict(os.environ, {'MOON_LOCAL_BOT_IDS': '123', 'MOON_BOT_API_URL': 'http://telegram-gateway:8081'}):
            self.assertEqual(bot_api_url('123:test'), 'http://telegram-gateway:8081/bot123:test/')
            self.assertEqual(bot_api_url('456:test'), 'https://api.telegram.org/bot456:test/')
            self.assertTrue(uses_local_api('123:test'))
            self.assertFalse(uses_local_api('456:test'))
            self.assertEqual(bot_file_url('123:test', 'photos/file 1.jpg'), 'http://telegram-gateway:8081/file/bot123:test/photos/file%201.jpg')

    def test_selected_bot_fails_closed_on_invalid_origin(self):
        for origin in ('', 'file:///tmp', 'http://user:secret@host', 'https://host/x', 'https://host?q=1', 'https://host#x'):
            with self.subTest(origin=origin), patch.dict(os.environ, {'MOON_LOCAL_BOT_IDS': '*', 'MOON_BOT_API_URL': origin}):
                with self.assertRaises(ValueError):
                    api_root('123:test')

    def test_files_do_not_escape_to_other_origins_or_local_paths(self):
        for path in ('/etc/passwd', '../secret', 'a/../secret', 'https://evil/file', '\\host\\file'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                bot_file_url('123:test', path)

    def test_identity_and_received_dedup_survive_endpoint_change(self):
        cloud = 'https://api.telegram.org/bot123:test/'
        local = 'http://telegram-gateway:8081/bot123:test/'
        self.assertEqual(identity(cloud), identity(local))
        telemetry = OperationsTelemetry()
        update = {'ok': True, 'result': [{'update_id': 1, 'message': {'text': 'not retained'}}]}
        for url in (cloud, local):
            telemetry.telegram(url, 'getUpdates', update, 2)
        self.assertEqual(telemetry.total['received'], 1)
        self.assertEqual(len(telemetry.bots), 1)

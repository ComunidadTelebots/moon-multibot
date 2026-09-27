import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest import mock
from core.tdlib_migration import migration_snapshot, migration_authorized
from tools.audit_tdlib_compatibility import inventory


class MigrationTests(unittest.TestCase):
    def test_read_only_service_auth_fails_closed_and_retains_jwt(self):
        jwt = mock.Mock(return_value=False)
        with mock.patch.dict('os.environ', {'MOON_ADMIN_API_KEY': 'service-secret'}):
            self.assertTrue(migration_authorized(SimpleNamespace(headers={'X-Moon-Admin-Key': 'service-secret'}), jwt))
            jwt.assert_not_called()
            for headers in ({}, {'X-Moon-Admin-Key': 'wrong'}, {'X-Moon-Admin-Key': 'ñ'}):
                self.assertFalse(migration_authorized(SimpleNamespace(headers=headers), jwt))
            jwt.return_value = True
            self.assertTrue(migration_authorized(SimpleNamespace(headers={}), jwt))
        with mock.patch.dict('os.environ', {'MOON_ADMIN_API_KEY': ''}):
            self.assertFalse(migration_authorized(SimpleNamespace(headers={}), lambda _: False))

    def test_audit_captures_direct_wrapped_dynamic_and_broken_files_without_execution(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'plugin.py').write_text('raise RuntimeError("never execute")\nbot.api_call("getMe")\ntelegram_api_call(s, url, "sendMessage")\nbot.call_api(method)\n', encoding='utf-8')
            (root / 'broken.py').write_text('def ???', encoding='utf-8')
            result = inventory(root)
            self.assertEqual(result['methods'], ['getMe', 'sendMessage'])
            self.assertEqual(result['summary']['dynamic_calls'], 1)
            self.assertEqual(result['summary']['parse_errors'], 1)
            self.assertFalse(result['ready_for_full_migration'])

    def test_status_does_not_publish_bot_token_or_identity(self):
        class Client:
            def get_status(self):
                return {'ready': True, 'me': {'phone': 'secret'}, 'api_hash': 'secret'}
        result = migration_snapshot([SimpleNamespace(url='https://example/botsecret/', _tdlib=Client())], True)
        self.assertTrue(result['bots'][0]['ready'])
        self.assertEqual(result['bots'][0]['incoming'], 'bot_api')
        self.assertFalse(result['ready_for_full_migration'])
        self.assertNotIn('secret', json.dumps(result))

    def test_invalid_gateway_does_not_break_other_bot_status(self):
        bots = [SimpleNamespace(url='https://api.telegram.org/bot123:secret/', token='123:secret'),
                SimpleNamespace(url='https://api.telegram.org/bot456:secret/', token='456:secret')]
        with mock.patch.dict('os.environ', {'MOON_LOCAL_BOT_IDS': '123', 'MOON_BOT_API_URL': 'invalid'}):
            result = migration_snapshot(iter(bots), False)
        self.assertEqual(result['bots'][0]['incoming'], 'unknown')
        self.assertEqual(result['bots'][0]['issue'], 'invalid_gateway_configuration')
        self.assertEqual(result['bots'][1]['incoming'], 'bot_api')
        self.assertNotIn('secret', json.dumps(result))

    def test_audit_finds_downloads_that_bypass_configured_gateway(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'voice.py').write_text('requests.get(f"https://api.telegram.org/file/bot{token}/{path}")',encoding='utf-8')
            result = inventory(root)
            self.assertEqual(result['summary']['direct_http_calls'],1)
            self.assertEqual(result['direct_http'][0]['kind'],'file_download')

    def test_failed_native_session_is_reported_without_exception_details(self):
        client = mock.Mock()
        client.get_status.side_effect = RuntimeError('secret')
        bot = SimpleNamespace(url='https://api.telegram.org/bot123:secret/', token='123:secret', _tdlib=client)
        with mock.patch.dict('os.environ', {'MOON_LOCAL_BOT_IDS': ''}):
            result = migration_snapshot([bot], True)
        self.assertEqual(result['bots'][0]['issue'], 'session_status_unavailable')
        self.assertFalse(result['bots'][0]['ready'])
        self.assertNotIn('secret', json.dumps(result))

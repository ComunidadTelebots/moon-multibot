import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from core.tdlib_migration import migration_snapshot
from tools.audit_tdlib_compatibility import inventory


class MigrationTests(unittest.TestCase):
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

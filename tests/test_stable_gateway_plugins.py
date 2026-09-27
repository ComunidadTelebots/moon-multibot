import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from core.bot_endpoint import bot_file_url


class StableGatewayPluginTests(unittest.TestCase):
    def test_managed_bot_methods_use_the_telegram_user_id_parameter(self):
        source = (Path(__file__).resolve().parents[1]/'moon_multibot.py').read_text(encoding='utf-8-sig')
        cls = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == 'MoonBot')
        names = {'get_managed_bot_token', 'replace_managed_bot_token', 'get_managed_bot_access_settings', 'set_managed_bot_access_settings'}
        functions = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in names]
        self.assertEqual(len(functions), 4)
        namespace = {}
        exec(compile(ast.Module(body=functions, type_ignores=[]), '<managed-contract>', 'exec'), namespace)
        for name in names:
            fake = SimpleNamespace(api_call=Mock(return_value={'ok': True}))
            namespace[name](fake, '123')
            self.assertEqual(fake.api_call.call_args.args[1], {'user_id': '123'})

    def run_plugin(self, name, file_path, failure=None):
        source = (Path(__file__).resolve().parents[1]/'plugins'/f'{name}.py').read_text(encoding='utf-8-sig')
        function = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'handle_command')
        request = Mock(return_value=SimpleNamespace(status_code=503), side_effect=failure)
        namespace = {'requests': SimpleNamespace(get=request), 'bot_file_url': bot_file_url, 'allowed_apis': ['google_speech']}
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<plugin-test>', 'exec'), namespace)
        bot = SimpleNamespace(token='123:secret', send_msg=Mock(), api_call=Mock(return_value={'ok': True, 'result': {'file_path': file_path}}))
        command = '/analyze_image file' if name == 'image_analysis' else '/transcribe  file'
        with patch.dict('os.environ', {'MOON_LOCAL_BOT_IDS': '123', 'MOON_BOT_API_URL': 'http://telegram-gateway:8081'}):
            self.assertTrue(namespace['handle_command'](bot, 1, 1, command, 'user'))
        return request, bot

    def test_both_plugins_download_from_selected_server_with_timeout(self):
        for name in ['image_analysis', 'voice_transcription']:
            with self.subTest(plugin=name):
                request, _ = self.run_plugin(name, 'media/file.ogg')
                request.assert_called_once_with('http://telegram-gateway:8081/file/bot123:secret/media/file.ogg', timeout=(5, 30))

    def test_unsafe_paths_are_rejected_and_request_errors_do_not_leak_tokens(self):
        for name in ['image_analysis', 'voice_transcription']:
            with self.subTest(plugin=name):
                request, _ = self.run_plugin(name, '../private')
                request.assert_not_called()
                _, bot = self.run_plugin(name, 'media/file.ogg', RuntimeError('URL bot123:secret'))
                self.assertNotIn('secret', str(bot.send_msg.call_args))

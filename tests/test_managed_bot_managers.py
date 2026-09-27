import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


class ManagedManagersTests(unittest.TestCase):
    def setUp(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'moon_multibot.py').read_text(encoding='utf-8-sig'))
        names = {'_managed_bot_manager', 'web_managed_bots_action'}
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
        for node in functions:
            node.decorator_list = []
        self.managers = [SimpleNamespace(bot_id=i, can_manage_bots=True,
            get_managed_bot_access_settings=Mock(return_value={'ok': True, 'result': {}})) for i in (1, 2)]
        self.registry = {}
        self.request = SimpleNamespace(json={'action': 'access_get', 'bot_id': '50'})
        self.context = {'active_bots': self.managers, 'bots_data': [], 'request': self.request,
            'check_jwt': lambda _: True, 'jsonify': lambda value: value,
            '_managed_registry': lambda: self.registry}
        exec(compile(ast.Module(body=functions, type_ignores=[]), '<managed-tests>', 'exec'), self.context)

    def test_explicit_manager_does_not_fall_back_to_first(self):
        select = self.context['_managed_bot_manager']
        self.assertIs(select('2'), self.managers[1])
        self.assertIsNone(select('99'))

    def test_stored_parent_wins_over_client_selection(self):
        self.registry['50'] = {'manager_bot_id': '2'}
        self.request.json['manager_id'] = '1'
        self.assertTrue(self.context['web_managed_bots_action']()['ok'])
        self.managers[0].get_managed_bot_access_settings.assert_not_called()
        self.managers[1].get_managed_bot_access_settings.assert_called_once_with('50')

    def test_ambiguous_legacy_parent_requires_selection(self):
        result, status = self.context['web_managed_bots_action']()
        self.assertEqual(status, 409)
        self.assertFalse(result['ok'])
        for manager in self.managers:
            manager.get_managed_bot_access_settings.assert_not_called()

    def test_disconnected_stored_parent_is_not_replaced(self):
        self.registry['50'] = {'manager_bot_id': '99'}
        self.request.json['manager_id'] = '1'
        self.assertEqual(self.context['web_managed_bots_action']()[1], 409)
        for manager in self.managers:
            manager.get_managed_bot_access_settings.assert_not_called()

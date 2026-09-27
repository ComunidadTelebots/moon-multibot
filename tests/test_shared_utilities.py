import unittest
from unittest.mock import Mock
from plugins import unit_converter, date_tools, data_utilities
from plugins.calculator import _safe_eval

class SharedUtilityTests(unittest.TestCase):
    def reply(self, plugin, command):
        bot=Mock()
        self.assertTrue(plugin.handle_command(bot,'chat','user',command,'user'))
        bot.send_msg.assert_called_once()
        return bot.send_msg.call_args.args[1]

    def test_conversions(self):
        self.assertIn('10000',self.reply(unit_converter,'/convertir 10 km m'))
        self.assertIn('32',self.reply(unit_converter,'/convertir 0 c f'))
        for command in ['/convertir NaN m km','/convertir 3 kg km','/convertir -1 k c','/convertir 1e999999 m km']:
            self.assertIn('no válida',self.reply(unit_converter,command))

    def test_dates(self):
        self.assertIn('2 días',self.reply(date_tools,'/diasentre 2024-02-28 2024-03-01'))
        self.assertIn('2024-02-29',self.reply(date_tools,'/sumardias 2024-03-01 -1'))
        self.assertIn('no válida',self.reply(date_tools,'/sumardias 9999-12-31 1'))
        self.assertIn('no válida',self.reply(date_tools,'/diasentre 2023-02-29 2023-03-01'))

    def test_json_is_not_echoed_and_rejects_non_standard(self):
        result=self.reply(data_utilities,'/jsonvalidar {"secret":"private"}')
        self.assertIn('JSON válido',result)
        self.assertNotIn('private',result)
        for body in ['NaN','Infinity','{"a":}','['*1500]:
            self.assertIn('no válido',self.reply(data_utilities,'/jsonvalidar '+body))

    def test_sha256(self):
        self.assertIn('ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad',self.reply(data_utilities,'/hashtexto abc'))

    def test_unknown_commands_are_not_intercepted(self):
        for plugin in [unit_converter,date_tools,data_utilities]:
            bot=Mock()
            self.assertFalse(plugin.handle_command(bot,'c','u','/unrelated','user'))
            bot.send_msg.assert_not_called()

    def test_calculator_limits(self):
        self.assertEqual(_safe_eval('(2+5)*3'),21)
        self.assertEqual(_safe_eval('2**10'),1024)
        self.assertEqual(_safe_eval('-4/2'),-2)
        for expression in ['2**999999999','True','().__class__','__import__("os")','1+'*100+'1']:
            with self.assertRaises((ValueError,SyntaxError)):
                _safe_eval(expression)

    def test_bots_have_no_shared_mutable_state(self):
        for name in ['first','second']:
            bot=Mock(bot_username=name)
            unit_converter.handle_command(bot,'c','u','/convertir 1 m cm','user')
            self.assertIn('100',bot.send_msg.call_args.args[1])

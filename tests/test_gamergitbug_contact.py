import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from core.gamergitbug_contact import handle_contact

class Store(dict):
    def set(self, key, value): self[key] = value

class ContactTests(unittest.TestCase):
    def setUp(self):
        self.db = Store()
        self.bot = SimpleNamespace(bot_username='CintiaBot', bot_id=123, api_call=Mock())
    def call(self, text, cid=42, uid=42, now=100):
        return handle_contact(self.bot, self.db, cid, uid, text, 15, now)
    def test_deep_link_collects_one_message_and_preserves_other_commands(self):
        self.assertTrue(self.call('/start gamergitbug_contact'))
        self.assertFalse(self.call('/calc 2+2'))
        self.assertTrue(self.call('Necesito una web'))
        self.assertEqual(self.db['GAMERGITBUG_CONTACT_123_42']['status'], 'received')
        self.assertEqual(self.db['GAMERGITBUG_CONTACT_123_42']['message_id'], 15)
        self.assertNotIn('Necesito', str(self.db))
        self.assertFalse(self.call('Conversacion normal'))
    def test_normal_start_cancel_and_expiry_restore_regular_behavior(self):
        for exit_command in ['/start', '/inicio', '/cancelar_contacto']:
            self.call('/contacto_gamergitbug')
            self.call(exit_command)
            self.assertFalse(self.call('Normal'))
        self.call('/contacto_gamergitbug')
        self.assertFalse(self.call('Tarde', now=2000))
    def test_no_interception_of_other_users_groups_bots_or_payloads(self):
        self.assertFalse(self.call('/start other_payload'))
        self.assertFalse(self.call('/start gamergitbug_contact', cid=-42))
        self.assertFalse(self.call('/start@OtroBot gamergitbug_contact'))
        self.call('/start gamergitbug_contact')
        self.assertFalse(self.call('Otro usuario', cid=43, uid=43))
        self.bot.bot_username = 'OtroBot'
        self.assertFalse(self.call('/start gamergitbug_contact'))
    def test_nontext_message_keeps_prompt_open(self):
        self.call('/start gamergitbug_contact')
        self.assertTrue(self.call(''))
        self.assertEqual(self.db['GAMERGITBUG_CONTACT_123_42']['status'], 'awaiting_message')

if __name__ == '__main__': unittest.main()

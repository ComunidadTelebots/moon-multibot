import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from flask import Flask

from core.bot_conversations import (
    apply_message_action,
    conversation_snapshot,
    register_bot_conversations,
)


class ConversationsTest(unittest.TestCase):
    def setUp(self):
        self.bots = [SimpleNamespace(bot_id=1, bot_username='first', token='secret-one'),
                     SimpleNamespace(bot_id=2, bot_username='second', token='secret-two')]
        self.db = {'CHATS_secret-one': ['10', '-20'], 'CHATS_secret-two': ['30'],
                   'CHAT_HIST_10': [{'text': 'hello', 'token': 'must-not-leak', 'media': {'file_id': 'private'}}]}

    def test_membership_enforced(self):
        self.assertEqual(conversation_snapshot(self.bots, self.db, '2', '10')[1], 404)
        self.assertEqual(conversation_snapshot(self.bots, self.db, '99')[1], 404)

    def test_history_whitelist_and_shared_scope(self):
        data, status = conversation_snapshot(self.bots, self.db, '1', '10')
        self.assertEqual(status, 200)
        self.assertEqual(data['history'][0]['text'], 'hello')
        self.assertEqual(data['history'][0]['actions'], [])
        self.assertNotIn('token', data['history'][0])
        self.assertEqual(data['history_scope'], 'shared_chat')
        self.assertNotIn('secret', str(conversation_snapshot(self.bots, self.db)))

    def test_filter_and_pagination(self):
        data, _ = conversation_snapshot(self.bots, self.db, '1', kind='private', page=99)
        self.assertEqual([row['id'] for row in data['chats']], ['10'])
        self.assertEqual(data['page'], 1)

    def test_actions_reject_unattributed_and_other_bot(self):
        body = {'bot_id': '1', 'chat_id': '10', 'action': 'delete', 'message_id': 7}
        self.assertEqual(apply_message_action(self.bots, self.db, body)[1], 409)
        self.db['CHAT_HIST_10'] = [{'message_id': 7, 'bot_id': '2', 'text': 'x'}]
        self.assertEqual(apply_message_action(self.bots, self.db, body)[1], 409)

    def test_single_attempt_and_duplicate_rejected(self):
        class Store(dict):
            def set(self, key, value): self[key] = value
        db = Store(self.db)
        db['CHAT_HIST_10'] = [{'message_id': 7, 'bot_id': '1', 'text': 'x'}]
        calls = []
        body = {'bot_id': '1', 'chat_id': '10', 'action': 'react', 'message_id': 7,
                'actor_id': 'master', 'request_id': '12345678-1234-1234-1234-123456789abc'}
        def transport(bot, method, params):
            calls.append(method)
            return {'ok': True}
        self.assertEqual(apply_message_action(self.bots, db, body, transport)[1], 200)
        self.assertEqual(apply_message_action(self.bots, db, body, transport)[1], 409)
        self.assertEqual(calls, ['setMessageReaction'])
        body['action'] = 'edit'
        self.assertEqual(apply_message_action(self.bots, db, body, transport)[1], 409)
        body['action'] = 'forward'
        body['target_chat_id'] = '30'
        self.assertEqual(apply_message_action(self.bots, db, body, transport)[1], 400)

    def test_auth_and_validation(self):
        app = Flask(__name__)
        register_bot_conversations(app, lambda: self.bots, self.db)
        with patch.dict(os.environ, {'MOON_ADMIN_API_KEY': 'key'}):
            client = app.test_client()
            self.assertEqual(client.get('/api/internal/bot-conversations').status_code, 401)
            headers = {'X-Moon-Admin-Key': 'key'}
            self.assertEqual(client.get('/api/internal/bot-conversations?chat_id=10', headers=headers).status_code, 400)
            response = client.get('/api/internal/bot-conversations?bot_id=1&chat_id=10', headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertIn('no-store', response.headers['Cache-Control'])


if __name__ == '__main__':
    unittest.main()

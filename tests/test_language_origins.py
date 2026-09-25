import unittest
from core.language_map import record_language_origin, aggregate_language_counts, ORIGIN_KEY


class Memory:
    def __init__(self):
        self.data = {}

    def get(self, key, fallback):
        return self.data.get(key, fallback)

    def set(self, key, value):
        self.data[key] = value


class OriginTests(unittest.TestCase):
    def test_chat_types_and_missing_channel_language(self):
        db = Memory()
        for kind in ('private', 'group', 'supergroup', 'channel'):
            message = {'chat': {'id': 123, 'type': kind}, 'text': 'private content'}
            if kind != 'channel':
                message['from'] = {'id': 456, 'language_code': 'es'}
            record_language_origin(db, message)
        self.assertEqual(db.data[ORIGIN_KEY], {'private': {'es': 1}, 'group': {'es': 2}, 'channel': {'und': 1}})
        self.assertNotIn('private content', str(db.data))
        result = aggregate_language_counts(db.data[ORIGIN_KEY]['channel'])
        self.assertEqual(result['total_users'], 1)
        self.assertFalse(result['points'][0]['mapped'])

    def test_counts_are_observations_not_unique_users(self):
        db = Memory()
        msg = {'chat': {'type': 'private'}, 'from': {'language_code': 'en'}}
        record_language_origin(db, msg)
        record_language_origin(db, msg)
        self.assertEqual(aggregate_language_counts(db.data[ORIGIN_KEY]['private'])['total_users'], 2)

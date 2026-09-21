import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from core.message_analytics import MessageAnalytics, message_type


class MessageAnalyticsTest(unittest.TestCase):
    def test_media_caption_and_unknown(self):
        self.assertEqual(message_type({'photo': [], 'caption': 'secret'}), 'photo')
        self.assertEqual(message_type({'animation': {}, 'document': {}}), 'animation')
        self.assertEqual(message_type({'new_chat_members': []}), 'other')

    def test_dedup_filters_restart_and_retention(self):
        with tempfile.TemporaryDirectory() as folder:
            clock = [2000000000]
            filename = str(Path(folder) / 'stats.sqlite3')
            store = MessageAnalytics(filename, now=lambda: clock[0])
            message = {'chat': {'id': -100, 'title': 'Group', 'type': 'supergroup'}, 'message_id': 1, 'photo': [{}], 'caption': 'secret'}
            with ThreadPoolExecutor(max_workers=4) as pool:
                list(pool.map(lambda _: store.record(message), range(12)))
            self.assertEqual(store.ranking()['total'], 1)
            store.record({**message, 'chat': {'id': 123, 'type': 'private'}})
            self.assertEqual(store.ranking()['chats'], 1)
            self.assertEqual(store.ranking(kind='text')['total'], 0)
            self.assertNotIn('secret', str(store.ranking()))
            self.assertEqual(MessageAnalytics(filename, now=lambda: clock[0]).ranking()['total'], 1)
            clock[0] += 2 * 86400
            store.record({'chat': message['chat'], 'message_id': 2, 'text': 'private content'})
            self.assertEqual(store.ranking(1)['total'], 1)
            self.assertEqual(store.ranking(7)['total'], 2)
            clock[0] += 31 * 86400
            store.record({'chat': message['chat'], 'message_id': 3, 'text': 'new'})
            self.assertEqual(store.ranking(30)['total'], 1)
            with self.assertRaises(ValueError):
                store.ranking(999)


if __name__ == '__main__':
    unittest.main()

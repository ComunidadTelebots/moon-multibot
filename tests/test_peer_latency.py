import unittest
from unittest.mock import MagicMock
from core.peer_latency import PeerLatency


class PeerLatencyTest(unittest.TestCase):
    def test_fixed_peers_only_and_measures_from_source(self):
        dial = MagicMock()
        monitor = PeerLatency('one', [{'id': 'one', 'url': 'http://self:5000'}, {'id': 'two', 'url': 'http://peer:5000'}], connect=dial, clock=lambda: 123)
        self.assertEqual(len(monitor.targets), 1)
        row = monitor.measure(monitor.targets[0])
        self.assertTrue(row['ok'])
        self.assertEqual(row['target'], 'two')
        self.assertEqual(row['at'], 123)
        dial.assert_called_once_with(('peer', 5000), timeout=1.5)
        dial.side_effect = TimeoutError()
        row = monitor.measure(monitor.targets[0])
        self.assertFalse(row['ok'])
        self.assertIsNone(row['ms'])

    def test_rejects_untrusted_urls_and_duplicate_ids(self):
        for url in ('file:///tmp', 'http://user:secret@host', 'http://host/path', 'http://host/?x=y'):
            with self.assertRaises(ValueError):
                PeerLatency('one', [{'id': 'two', 'url': url}])
        with self.assertRaises(ValueError):
            PeerLatency('one', [{'id': 'two', 'url': 'http://peer'}] * 2)

import unittest
from unittest.mock import Mock, patch
from core.receiver_network import ReceiverNetwork

class ReceiverNetworkTests(unittest.TestCase):
    def test_shared_host_and_no_credentials(self):
        monitor = ReceiverNetwork(connector=Mock())
        with patch('core.receiver_network.threading.Thread') as thread:
            monitor.read('https://api.telegram.org/botSECRET_ONE')
            monitor.read('https://api.telegram.org/botSECRET_TWO')
            self.assertEqual(thread.call_count, 1)
        self.assertEqual(list(monitor.entries), [('api.telegram.org', 443)])
        self.assertNotIn('SECRET', str(monitor.entries))

    def test_probe_timeout_is_explicit_and_cached(self):
        connector = Mock(side_effect=TimeoutError('private detail'))
        monitor = ReceiverNetwork(connector=connector, clock=lambda: 20)
        target = ('api.telegram.org',443)
        monitor.entries[target] = {'busy': True, 'next': 0, 'value': None}
        monitor._probe(target)
        value = monitor.read('https://api.telegram.org/botSECRET')
        self.assertEqual(value['status'], 'unreachable')
        self.assertIsNone(value['ms'])
        self.assertNotIn('private detail', str(value))
        self.assertEqual(connector.call_count, 1)

    def test_success_closes_socket_and_reports_duration(self):
        connection = Mock()
        connection.__enter__ = Mock(return_value=connection)
        connection.__exit__ = Mock(return_value=False)
        monitor = ReceiverNetwork(connector=Mock(return_value=connection), clock=Mock(side_effect=[1,1.025,2]))
        target = ('api.telegram.org',443)
        monitor.entries[target] = {'busy': True, 'next': 0, 'value': None}
        monitor._probe(target)
        self.assertEqual(monitor.entries[target]['value']['ms'],25)
        connection.__exit__.assert_called_once()

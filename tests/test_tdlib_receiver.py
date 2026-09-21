import queue
import threading
import unittest
from unittest.mock import Mock, patch
from core.tdlib_client import TDLibClient
from core.tdlib_receiver import TDLibReceiver


def client(identifier):
    with patch.object(TDLibClient, '_load_library'):
        instance = TDLibClient(1, 'unused-test', Mock())
    instance._client_id = identifier
    instance._running = True
    instance._tdjson = Mock()
    return instance


class ReceiverTests(unittest.TestCase):
    def test_same_request_id_cannot_cross_accounts(self):
        router = TDLibReceiver()
        first, second = client(10), client(20)
        for current in (first, second):
            router.register(current, start=False)
            current._pending['1'] = (threading.Event(), [None])
        router.route({'@client_id': 20, '@extra': '1', '@type': 'user', 'id': 200})
        self.assertFalse(first._pending['1'][0].is_set())
        self.assertEqual(second._pending['1'][1][0]['id'], 200)
        self.assertFalse(router.route({'@client_id': 999, '@extra': '1'}))

    def test_ordered_updates_and_responses_bypass_full_callback_queue(self):
        router, current = TDLibReceiver(), client(10)
        current._events = queue.Queue(maxsize=2)
        router.register(current, start=False)
        for seq in (1, 2):
            router.route({'@client_id': 10, '@type': 'updateNewMessage', 'seq': seq})
        current._pending['1'] = (threading.Event(), [None])
        router.route({'@client_id': 10, '@extra': '1', '@type': 'ok'})
        self.assertTrue(current._pending['1'][0].is_set())
        self.assertEqual([current._events.get()['seq'] for _ in range(2)], [1, 2])

    def test_overflow_stops_and_closed_unregisters(self):
        router, current = TDLibReceiver(), client(10)
        current._events = queue.Queue(maxsize=1)
        router.register(current, start=False)
        router.route({'@client_id': 10, '@type': 'updateNewMessage'})
        self.assertFalse(router.route({'@client_id': 10, '@type': 'updateNewMessage'}))
        self.assertTrue(current._stop_requested.is_set())
        self.assertFalse(current._running)
        self.assertEqual(current.get_status()['receiver']['overflows'], 1)
        router.route({'@client_id': 10, '@type': 'updateAuthorizationState',
                      'authorization_state': {'@type': 'authorizationStateClosed'}})
        self.assertNotIn(10, router._clients)

    def test_intentional_stop_does_not_restart_and_releases_waiters(self):
        current = client(10)
        signal = threading.Event()
        current._pending['1'] = (signal, [None])
        current.stop()
        self.assertTrue(signal.is_set())
        current._watchdog()
        current._tdjson.td_create_client_id.assert_not_called()

    def test_wait_does_not_mutate_payload_and_cleans_timeout(self):
        current = client(10)
        query = {'@type': 'getMe'}
        self.assertIsNone(current.send_await(query, timeout=0))
        self.assertEqual(query, {'@type': 'getMe'})
        self.assertEqual(current._pending, {})

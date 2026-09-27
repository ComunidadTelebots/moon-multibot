import unittest
from unittest.mock import Mock

import requests
from flask import Flask

from core.operations_telemetry import (
    ObservedSession,
    OperationsTelemetry,
    install_http_telemetry,
)


class OperationsTransportTest(unittest.TestCase):
    def test_success_and_deduplication(self):
        counters = OperationsTelemetry()
        response = Mock()
        response.json.return_value = {'ok': True, 'result': [{'update_id': 1, 'message': {'text': 'private'}}]}
        session = Mock()
        session.post.return_value = response
        wrapped = ObservedSession(session, 'https://api.telegram.org/bot1:secret/', 'getUpdates', counters)
        self.assertIs(wrapped.post('url', timeout=1), response)
        wrapped.post('url', timeout=1)
        snapshot = counters.snapshot()
        self.assertEqual(snapshot['last60s']['calls'], 2)
        self.assertEqual(snapshot['last60s']['received'], 1)
        self.assertNotIn('private', str(snapshot))
        self.assertNotIn('secret', str(snapshot))

    def test_timeout_preserves_exception_without_retry(self):
        counters = OperationsTelemetry()
        session = Mock()
        session.post.side_effect = requests.Timeout()
        with self.assertRaises(requests.Timeout):
            ObservedSession(session, 'https://api.telegram.org/bot1:secret/', 'getUpdates', counters).post('url')
        self.assertEqual(session.post.call_count, 1)
        self.assertEqual(counters.snapshot()['last60s']['timeouts'], 1)

    def test_invalid_response_counted(self):
        counters = OperationsTelemetry()
        session = Mock()
        session.post.return_value.json.side_effect = ValueError()
        ObservedSession(session, 'https://api.telegram.org/bot1:secret/', 'sendMessage', counters).post('url')
        self.assertEqual(counters.snapshot()['last60s']['errors'], 1)

    def test_routes_require_auth(self):
        app = Flask(__name__)
        install_http_telemetry(app, lambda req: False)
        for route in ['operations', 'resources']:
            self.assertEqual(app.test_client().get('/api/telemetry/' + route).status_code, 401)

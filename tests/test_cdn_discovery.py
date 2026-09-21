import datetime
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from flask import Flask
from core.cdn_discovery import CdnDiscovery, project_config, install_cdn_discovery


def config():
    return SimpleNamespace(expires=datetime.datetime.fromtimestamp(1000, datetime.timezone.utc),
        dc_options=[SimpleNamespace(cdn=cdn, id=203, ip_address=ip, port=443)
                    for cdn, ip in [(True, '91.105.192.100'), (True, '127.0.0.1'),
                                    (False, '149.154.175.50'), (True, '91.105.192.100')]])


class DiscoveryTests(unittest.TestCase):
    def test_projection_excludes_private_non_cdn_and_duplicates(self):
        data = project_config(config())
        self.assertEqual(len(data['targets']), 1)
        self.assertEqual(data['targets'][0]['host'], '91.105.192.100')
        self.assertEqual(data['expiresAt'], 1000)

    def test_disabled_never_connects(self):
        with patch.dict('os.environ', {}, clear=True):
            result = CdnDiscovery().snapshot()
        self.assertFalse(result['refreshing'])
        self.assertFalse(result['enabled'])

    def test_cache_and_failed_refresh_keep_last_list_without_error_details(self):
        async def good(*args):
            return config()
        async def bad(*args):
            raise ValueError('SECRET')
        now = [100]
        monitor = CdnDiscovery(good, lambda: now[0])
        monitor._refresh(1, 'hash')
        now[0] = 1100
        monitor.fetcher = bad
        monitor._refresh(1, 'hash')
        with patch.dict('os.environ', {'MOON_CDN_DISCOVERY_ENABLED': 'false'}):
            result = monitor.snapshot()
        self.assertTrue(result['stale'])
        self.assertEqual(len(result['targets']), 1)
        self.assertNotIn('SECRET', str(result))
        self.assertEqual(monitor.retry_at, 1160)

    def test_concurrent_snapshots_share_refresh(self):
        gate = threading.Event()
        calls = []
        async def fetcher(*args):
            calls.append(1)
            gate.wait(1)
            return config()
        monitor = CdnDiscovery(fetcher, lambda: 100)
        with patch.dict('os.environ', {'MOON_CDN_DISCOVERY_ENABLED': 'true', 'TDLIB_API_ID': '1', 'TDLIB_API_HASH': 'test'}):
            try:
                self.assertTrue(monitor.snapshot()['refreshing'])
                self.assertTrue(monitor.snapshot()['refreshing'])
            finally:
                gate.set()
        self.assertLessEqual(len(calls), 1)

    def test_route_requires_authentication(self):
        app = Flask(__name__)
        install_cdn_discovery(app, lambda request: request.headers.get('Authorization') == 'test')
        with app.test_client() as client:
            self.assertEqual(client.get('/api/telemetry/cdn').status_code, 401)
            with patch.dict('os.environ', {'MOON_CDN_DISCOVERY_ENABLED': 'false'}):
                response = client.get('/api/telemetry/cdn', headers={'Authorization': 'test'})
            self.assertEqual(response.headers['Cache-Control'], 'no-store')

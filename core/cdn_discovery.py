"""On-demand public MTProto configuration; never signs in or stores a session."""
import asyncio
import ipaddress
import os
import threading
import time


async def fetch_config(api_id, api_hash):
    from telethon import TelegramClient, functions
    from telethon.sessions import MemorySession
    client = TelegramClient(MemorySession(), api_id, api_hash,
                            receive_updates=False, connection_retries=0,
                            request_retries=0, flood_sleep_threshold=0, timeout=5)
    try:
        await client.connect()
        return await client(functions.help.GetConfigRequest())
    finally:
        await asyncio.wait_for(client.disconnect(), 3)


def project_config(config):
    targets = []
    seen = set()
    for option in config.dc_options:
        if not option.cdn:
            continue
        address = ipaddress.ip_address(option.ip_address)
        if not address.is_global or not 1 <= option.port <= 65535:
            continue
        key = (option.id, str(address), option.port)
        if key in seen:
            continue
        seen.add(key)
        targets.append({'dcId': option.id, 'host': str(address), 'port': option.port,
                        'ipv6': address.version == 6})
        if len(targets) == 32:
            break
    return {'targets': targets, 'expiresAt': config.expires.timestamp()}


class CdnDiscovery:
    def __init__(self, fetcher=fetch_config, clock=time.time):
        self.fetcher, self.clock = fetcher, clock
        self.lock = threading.Lock()
        self.data = None
        self.busy = False
        self.retry_at = 0
        self.error = None

    def _refresh(self, api_id, api_hash):
        async def collect():
            return await asyncio.wait_for(self.fetcher(api_id, api_hash), 12)
        try:
            data = project_config(asyncio.run(collect()))
            data['fetchedAt'] = self.clock()
            with self.lock:
                self.data, self.error = data, None
        except Exception:
            with self.lock:
                self.error = 'No se pudo obtener la configuración MTProto.'
        finally:
            with self.lock:
                self.retry_at = self.clock() + 60
                self.busy = False

    def snapshot(self):
        enabled = os.getenv('MOON_CDN_DISCOVERY_ENABLED', '').lower() == 'true'
        api_id = os.getenv('TDLIB_API_ID', '')
        api_hash = os.getenv('TDLIB_API_HASH', '')
        configured = api_id.isdigit() and int(api_id) > 0 and bool(api_hash)
        with self.lock:
            stale = not self.data or self.clock() >= self.data['expiresAt']
            if enabled and configured and stale and not self.busy and self.clock() >= self.retry_at:
                self.busy = True
                threading.Thread(target=self._refresh, args=(int(api_id), api_hash), daemon=True).start()
            return {'ok': True, 'enabled': enabled, 'configured': configured,
                    'refreshing': self.busy, 'stale': stale, 'error': self.error,
                    'source': 'Telegram help.getConfig',
                    **(self.data or {'targets': [], 'expiresAt': None, 'fetchedAt': None})}


discovery = CdnDiscovery()


def install_cdn_discovery(app, check_jwt):
    from flask import jsonify, request

    @app.get('/api/telemetry/cdn')
    def cdn_snapshot():
        if not check_jwt(request):
            return jsonify({'ok': False}), 401
        response = jsonify(discovery.snapshot())
        response.headers['Cache-Control'] = 'no-store'
        return response

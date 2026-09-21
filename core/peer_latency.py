"""TCP connection timing from this node to configured peers; no browser targets."""
import json
import os
import re
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from urllib.parse import urlsplit


class PeerLatency:
    def __init__(self, node, targets, connect=socket.create_connection, clock=time.time):
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', node or '') or not isinstance(targets, list) or len(targets) > 12:
            raise ValueError('Invalid peer configuration')
        self.node, self.connect, self.clock = node, connect, clock
        self.targets = []
        seen = set()
        for row in targets:
            url = urlsplit(row.get('url', ''))
            peer = row.get('id', '')
            if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', peer) or peer in seen or url.scheme not in ('http', 'https') or not url.hostname or url.username or url.password or url.query or url.fragment or url.path not in ('', '/'):
                raise ValueError('Invalid peer target')
            seen.add(peer)
            if peer != node:
                self.targets.append((peer, url.hostname, url.port or (443 if url.scheme == 'https' else 80)))
        self.rows = []
        self.checked = None
        self.refreshing = False
        self.lock = threading.Lock()

    def measure(self, target):
        peer, host, port = target
        started = time.monotonic()
        try:
            with self.connect((host, port), timeout=1.5):
                pass
            return dict(target=peer, ok=True, ms=round((time.monotonic() - started) * 1000, 2), at=self.clock())
        except Exception:
            return dict(target=peer, ok=False, ms=None, at=self.clock())

    def refresh(self):
        try:
            with ThreadPoolExecutor(max_workers=4) as pool:
                rows = list(pool.map(self.measure, self.targets))
            with self.lock:
                self.rows, self.checked = rows, self.clock()
        finally:
            with self.lock:
                self.refreshing = False

    def snapshot(self):
        with self.lock:
            if not self.refreshing and (self.checked is None or self.clock() - self.checked >= 30):
                self.refreshing = True
                threading.Thread(target=self.refresh, daemon=True).start()
            return dict(ok=True, node=self.node, refreshing=self.refreshing, checkedAt=self.checked,
                        rows=list(self.rows), configured=bool(self.targets))


@lru_cache(maxsize=1)
def peer_latency():
    return PeerLatency(os.getenv('MOON_NODE_ID', ''), json.loads(os.getenv('MOON_PEER_NODES', '[]')))

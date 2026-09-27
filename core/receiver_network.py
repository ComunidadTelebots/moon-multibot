"""Cached TCP connection time from this receiver host; never sends a bot request."""
import socket
import threading
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit


class ReceiverNetwork:
    def __init__(self, connector=socket.create_connection, clock=time.monotonic):
        self.connector, self.clock = connector, clock
        self.lock = threading.Lock()
        self.entries = {}

    def read(self, url):
        if not url:
            return None
        parsed = urlsplit(url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname:
            return None
        target = (parsed.hostname, parsed.port or (443 if parsed.scheme == 'https' else 80))
        launch = False
        with self.lock:
            if target not in self.entries:
                if len(self.entries) >= 16:
                    return None
                self.entries[target] = {'busy': False, 'next': 0, 'value': None}
            entry = self.entries[target]
            if not entry['busy'] and self.clock() >= entry['next']:
                entry['busy'] = True
                launch = True
            value = entry['value']
        if launch:
            threading.Thread(target=self._probe, args=(target,), daemon=True, name='receiver-tcp-probe').start()
        return value

    def _probe(self, target):
        started = self.clock()
        try:
            with self.connector(target, timeout=2):
                pass
            value = {'status': 'ok', 'ms': round((self.clock() - started) * 1000, 1)}
        except OSError:
            value = {'status': 'unreachable', 'ms': None}
        value.update({'host': target[0], 'port': target[1], 'kind': 'tcp_dns',
                      'at': datetime.now(timezone.utc).isoformat()})
        with self.lock:
            self.entries[target].update(busy=False, next=self.clock() + 30, value=value)


receiver_network = ReceiverNetwork()

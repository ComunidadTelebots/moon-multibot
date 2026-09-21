"""One process-wide td_receive consumer, routed by TDLib's client identity.

Responses bypass callback queues so a callback can safely use send_await.
The queues preserve update order within each account. They are not the
durable, cross-Docker work queue used for distributed business processing.
"""
import json
import queue
import threading


class TDLibReceiver:
    def __init__(self):
        self._lock = threading.RLock()
        self._clients = {}
        self._thread = None
        self._library = None

    def register(self, client, start=True):
        with self._lock:
            self._clients[client._client_id] = client
            self._library = client._tdjson
            if start and (self._thread is None or not self._thread.is_alive()):
                self._thread = threading.Thread(target=self._receive, daemon=True,
                                                name='tdlib-shared-receiver')
                self._thread.start()

    def unregister(self, client_id):
        with self._lock:
            self._clients.pop(client_id, None)

    def route(self, event):
        with self._lock:
            client = self._clients.get(event.get('@client_id'))
        if client is None:
            return False
        client._receiver_events += 1
        if client._resolve_response(event):
            return True
        # Closed must still be applied after stop() or an overflowing queue.
        if (event.get('@type') == 'updateAuthorizationState' and
                event.get('authorization_state', {}).get('@type') == 'authorizationStateClosed'):
            client._auth_state = 'authorizationStateClosed'
            client._running = False
            client._fail_pending()
            self.unregister(event['@client_id'])
            return True
        if not client._running:
            return False
        try:
            client._events.put_nowait(event)
        except queue.Full:
            # Never pretend that an incomplete stream is still healthy.
            client._receiver_overflows += 1
            client._log('ERROR', 'TDLib: cola de eventos llena; sesión detenida, requiere revisión manual')
            client.stop()
            return False
        return True

    def _receive(self):
        while True:
            try:
                raw = self._library.td_receive(1.0)
                if raw:
                    self.route(json.loads(raw))
            except (ValueError, TypeError):
                continue


receiver = TDLibReceiver()

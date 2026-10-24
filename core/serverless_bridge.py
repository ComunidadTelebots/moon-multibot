import copy
import hashlib
import hmac
import threading
import time
from collections import defaultdict, deque


class ServerlessBridgeStore:
    def __init__(self, max_events=200):
        self._events = defaultdict(lambda: deque(maxlen=max_events))
        self._stats = {}
        self._last_seen = {}
        self._lock = threading.RLock()

    @staticmethod
    def secret(jwt_secret, app_id):
        if not jwt_secret:
            return ""
        return hmac.new(
            jwt_secret.encode("utf-8"),
            f"moonbot-serverless:{app_id}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @classmethod
    def authenticate(cls, authorization, jwt_secret, app_id):
        expected = cls.secret(jwt_secret, app_id)
        supplied = str(authorization or "")
        if supplied.startswith("Bearer "):
            supplied = supplied[7:]
        return bool(expected and supplied and hmac.compare_digest(expected, supplied))

    def ingest(self, bot_id, payload):
        event = payload.get("event") if isinstance(payload, dict) else None
        stats = payload.get("stats") if isinstance(payload, dict) else None
        now = int(time.time())
        with self._lock:
            if isinstance(event, dict):
                clean = {
                    "id": event.get("id"),
                    "kind": str(event.get("kind") or "message")[:32],
                    "telegramId": event.get("telegramId"),
                    "chatId": event.get("chatId"),
                    "messageId": event.get("messageId"),
                    "chatTitle": str(event.get("chatTitle") or "")[:255],
                    "senderName": str(event.get("senderName") or "")[:255],
                    "body": str(event.get("body") or "")[:2000],
                    "createdAt": int(event.get("createdAt") or now),
                }
                self._events[bot_id].appendleft(clean)
            if isinstance(stats, dict):
                self._stats[bot_id] = copy.deepcopy(stats)
            self._last_seen[bot_id] = now
        return self.snapshot(bot_id)

    def merge_pull(self, bot_id, payload):
        if not isinstance(payload, dict):
            return self.snapshot(bot_id)
        with self._lock:
            known = {
                (item.get("chatId"), item.get("messageId"), item.get("createdAt"))
                for item in self._events[bot_id]
            }
            for raw in payload.get("events") or []:
                event = {
                    "id": raw.get("id"),
                    "kind": str(raw.get("kind") or "message")[:32],
                    "telegramId": raw.get("telegram_id"),
                    "chatId": raw.get("chat_id"),
                    "messageId": raw.get("message_id"),
                    "chatTitle": str(raw.get("chat_title") or "")[:255],
                    "senderName": str(raw.get("sender_name") or "")[:255],
                    "body": str(raw.get("body") or "")[:2000],
                    "createdAt": int(raw.get("created_at") or time.time()),
                }
                key = (event["chatId"], event["messageId"], event["createdAt"])
                if key not in known:
                    self._events[bot_id].append(event)
                    known.add(key)
            if isinstance(payload.get("stats"), dict):
                self._stats[bot_id] = copy.deepcopy(payload["stats"])
            self._last_seen[bot_id] = int(time.time())
        return self.snapshot(bot_id)

    def snapshot(self, bot_id):
        with self._lock:
            return {
                "connected": bot_id in self._last_seen,
                "lastSeenAt": self._last_seen.get(bot_id),
                "stats": copy.deepcopy(self._stats.get(bot_id, {})),
                "events": copy.deepcopy(list(self._events.get(bot_id, ()))),
            }

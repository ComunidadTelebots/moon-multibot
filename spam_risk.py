"""Motor local y explicable de puntuación de spam para Moonbot."""

import datetime
import re
import threading
import time
from difflib import SequenceMatcher


_URL_RE = re.compile(r"(?:https?://|t\.me/|www\.)\S+", re.IGNORECASE)
_REPEAT_RE = re.compile(r"(.)\1{7,}", re.IGNORECASE)
_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\u2600-\u27BF]",
    flags=re.UNICODE,
)


class SpamRiskEngine:
    DEFAULT_TERMS = [
        "ganancias garantizadas", "rentabilidad garantizada", "dinero rápido",
        "duplica tu dinero", "inversión sin riesgo", "premio exclusivo",
        "claim your reward", "guaranteed profit", "double your money",
        "crypto giveaway", "contact me privately",
    ]

    def __init__(self, db):
        self.db = db
        self._recent = {}
        self._lock = threading.Lock()

    @staticmethod
    def normalize(text):
        text = _URL_RE.sub("<url>", str(text or "").lower())
        return " ".join(re.sub(r"[^\w<>]+", " ", text, flags=re.UNICODE).split())[:1000]

    def config(self, chat_id):
        raw = self.db.get(f"SPAMCFG_{chat_id}", {})
        if not isinstance(raw, dict):
            raw = {}
        def bounded(value, default, minimum, maximum):
            try:
                return max(minimum, min(int(value), maximum))
            except (TypeError, ValueError):
                return default
        return {
            "enabled": bool(raw.get("enabled", True)),
            "mode": raw.get("mode") if raw.get("mode") in ("observe", "delete") else "observe",
            "watch_score": bounded(raw.get("watch_score"), 40, 20, 80),
            "delete_score": bounded(raw.get("delete_score"), 75, 50, 100),
            "terms": [
                str(term).strip().lower()[:100] for term in raw.get("terms", self.DEFAULT_TERMS)
                if str(term).strip()
            ][:100],
        }

    def _repeat_score(self, chat_id, user_id, normalized):
        if not normalized or len(normalized) < 12:
            return 0
        now = time.time()
        key = f"{chat_id}:{user_id}"
        with self._lock:
            rows = [
                row for row in self._recent.get(key, [])
                if now - row["time"] <= 120
            ]
            matches = sum(row["text"] == normalized for row in rows)
            rows.append({"time": now, "text": normalized})
            self._recent[key] = rows[-20:]
            if len(self._recent) > 5000:
                self._recent.clear()
        return min(35, matches * 18)

    def analyze(self, chat_id, user_id, text, karma=0):
        text = str(text or "")[:5000]
        normalized = self.normalize(text)
        score, reasons = 0, []
        urls = _URL_RE.findall(text)
        if urls:
            points = min(35, 12 + len(urls) * 8)
            score += points
            reasons.append({"signal": "links", "points": points, "value": len(urls)})
            if int(karma or 0) < 5:
                score += 12
                reasons.append({"signal": "new_user_link", "points": 12})

        terms = [term for term in self.config(chat_id)["terms"] if term in text.lower()]
        if terms:
            points = min(45, 25 + (len(terms) - 1) * 10)
            score += points
            reasons.append({"signal": "terms", "points": points, "value": terms[:5]})

        letters = [char for char in text if char.isalpha()]
        if len(letters) >= 20 and sum(char.isupper() for char in letters) / len(letters) >= 0.7:
            score += 10
            reasons.append({"signal": "uppercase", "points": 10})
        emoji_count = len(_EMOJI_RE.findall(text))
        if emoji_count >= 8:
            score += 10
            reasons.append({"signal": "emoji_burst", "points": 10, "value": emoji_count})
        if _REPEAT_RE.search(text):
            score += 10
            reasons.append({"signal": "repeated_characters", "points": 10})

        repeat_points = self._repeat_score(chat_id, user_id, normalized)
        if repeat_points:
            score += repeat_points
            reasons.append({"signal": "repeated_message", "points": repeat_points})

        spam_samples = self.db.get(f"SPAM_SAMPLES_{chat_id}", [])
        ham_samples = self.db.get(f"HAM_SAMPLES_{chat_id}", [])
        spam_similarity = max(
            (SequenceMatcher(None, normalized, self.normalize(sample)).ratio()
             for sample in spam_samples[-100:] if sample),
            default=0,
        )
        ham_similarity = max(
            (SequenceMatcher(None, normalized, self.normalize(sample)).ratio()
             for sample in ham_samples[-100:] if sample),
            default=0,
        )
        if spam_similarity >= 0.82:
            points = min(50, int(spam_similarity * 50))
            score += points
            reasons.append({"signal": "spam_sample", "points": points,
                            "value": round(spam_similarity, 2)})
        if ham_similarity >= 0.9:
            score -= 35
            reasons.append({"signal": "ham_sample", "points": -35,
                            "value": round(ham_similarity, 2)})

        return {"score": max(0, min(score, 100)), "reasons": reasons,
                "normalized": normalized, "checked_at": datetime.datetime.now().isoformat()}

    def record(self, chat_id, user_id, username, text, result, action):
        events = self.db.get(f"SPAMEVENTS_{chat_id}", [])
        if not isinstance(events, list):
            events = []
        events.append({
            "user_id": str(user_id),
            "username": str(username or "")[:100],
            "text": str(text or "")[:500],
            "score": int(result.get("score", 0)),
            "reasons": result.get("reasons", []),
            "action": action,
            "created_at": result.get("checked_at"),
        })
        self.db.set(f"SPAMEVENTS_{chat_id}", events[-200:])

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

        def recent(key, limit):
            values = self.db.get(key, [])
            return values[-limit:] if isinstance(values, list) else []

        spam_samples = recent(f"SPAM_SAMPLES_{chat_id}", 100) + recent("SPAM_SOURCE_SAMPLES", 200)
        ham_samples = recent(f"HAM_SAMPLES_{chat_id}", 100) + recent("HAM_SOURCE_SAMPLES", 200)

        def best_match(samples):
            best = {"similarity": 0, "confidence": 1.0, "sources": []}
            for sample in samples:
                if isinstance(sample, dict):
                    sample_text = sample.get("text", "")
                    confidence = max(0.0, min(float(sample.get("confidence", 100)) / 100, 1.0))
                    sources = sample.get("sources") or ([sample.get("source")] if sample.get("source") else [])
                else:
                    sample_text, confidence, sources = sample, 1.0, []
                if not sample_text:
                    continue
                similarity = SequenceMatcher(None, normalized, self.normalize(sample_text)).ratio()
                if similarity * confidence > best["similarity"] * best["confidence"]:
                    best = {
                        "similarity": similarity,
                        "confidence": confidence,
                        "sources": [str(source) for source in sources if source is not None],
                    }
            return best

        spam_match = best_match(spam_samples)
        ham_match = best_match(ham_samples)
        spam_similarity, spam_confidence = spam_match["similarity"], spam_match["confidence"]
        ham_similarity, ham_confidence = ham_match["similarity"], ham_match["confidence"]
        if spam_similarity >= 0.82:
            points = min(50, int(spam_similarity * 50 * spam_confidence))
            score += points
            reasons.append({"signal": "spam_sample", "points": points,
                            "value": round(spam_similarity, 2),
                            "confidence": round(spam_confidence, 2),
                            "sources": spam_match["sources"]})
            if len(set(spam_match["sources"])) >= 2:
                score += 15
                reasons.append({
                    "signal": "source_consensus", "points": 15,
                    "sources": spam_match["sources"],
                })
        if ham_similarity >= 0.9:
            deduction = int(35 * ham_confidence)
            score -= deduction
            reasons.append({"signal": "ham_sample", "points": -deduction,
                            "value": round(ham_similarity, 2),
                            "confidence": round(ham_confidence, 2),
                            "sources": ham_match["sources"]})

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

    def learn_source(self, source_id, purpose, text, confidence=80):
        clean = str(text or "").strip()
        try:
            confidence = max(0, min(int(confidence), 100))
        except (TypeError, ValueError):
            confidence = 80
        if purpose not in ("spam", "ham") or confidence < 50 or not 15 <= len(clean) <= 500:
            return False
        key = "SPAM_SOURCE_SAMPLES" if purpose == "spam" else "HAM_SOURCE_SAMPLES"
        samples = self.db.get(key, [])
        if not isinstance(samples, list):
            samples = []
        normalized = self.normalize(clean)
        source_id = str(source_id)
        for index, item in enumerate(samples[-1000:], start=max(0, len(samples) - 1000)):
            sample_text = item.get("text", "") if isinstance(item, dict) else item
            if self.normalize(sample_text) != normalized:
                continue
            if not isinstance(item, dict):
                return False
            sources = [str(value) for value in (item.get("sources") or [item.get("source")]) if value is not None]
            if source_id in sources:
                return False
            sources.append(source_id)
            item["sources"] = sources
            item["occurrences"] = int(item.get("occurrences", 1)) + 1
            item["confidence"] = max(int(item.get("confidence", 0)), confidence)
            item["updated_at"] = datetime.datetime.now().isoformat()
            samples[index] = item
            self.db.set(key, samples[-2000:])
            return True
        samples.append({
            "text": clean,
            "source": source_id,
            "sources": [source_id],
            "occurrences": 1,
            "confidence": confidence,
            "created_at": datetime.datetime.now().isoformat(),
        })
        self.db.set(key, samples[-2000:])
        return True

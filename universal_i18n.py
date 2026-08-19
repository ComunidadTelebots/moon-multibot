"""Traducción universal bajo demanda con caché persistente y fallback seguro."""

import hashlib
import re


class UniversalI18n:
    def __init__(self, db, translator):
        self.db = db
        self.translator = translator

    @staticmethod
    def normalize(language):
        value = str(language or "es").strip().lower().replace("_", "-")
        aliases = {"iw": "he", "in": "id", "ji": "yi", "zh-cn": "zh", "zh-sg": "zh",
                   "zh-tw": "zh-tw", "zh-hk": "zh-tw", "pt-br": "pt-br"}
        return aliases.get(value, value.split("-")[0] if "-" in value and value not in ("pt-br", "zh-tw") else value)

    @staticmethod
    def _key(text):
        return hashlib.sha256(str(text).encode("utf-8")).hexdigest()

    def translate(self, text, language):
        language = self.normalize(language)
        text = str(text or "")
        if not text or language == "es" or re.fullmatch(r"[\W\d_]+", text):
            return text
        cache_key = f"I18N_CACHE_{language}"
        cache = self.db.get(cache_key, {})
        cache = cache if isinstance(cache, dict) else {}
        key = self._key(text)
        if key in cache:
            return cache[key]
        translated = self.translator(text, language)
        if not translated:
            return text
        cache[key] = str(translated)
        self.db.set(cache_key, cache)
        return cache[key]

    def batch(self, texts, language, limit=160):
        return [self.translate(text, language) for text in list(texts)[:limit]]

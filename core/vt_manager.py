import base64
import hashlib
import os
import threading
import time
from urllib.parse import urlparse

import requests


class VirusTotalManager:
    """Cliente VT v3 con caché y resultados normalizados para web y bot."""

    def __init__(self, api_key, cache_ttl=900):
        self.api_key = api_key
        self.base_url = "https://www.virustotal.com/api/v3"
        self.cache_ttl = max(60, int(cache_ttl))
        self._cache = {}
        self._lock = threading.Lock()

    def _headers(self):
        return {"x-apikey": self.api_key, "User-Agent": "MoonMultibot/16.85"}

    def _cached(self, key):
        with self._lock:
            row = self._cache.get(key)
            if row and time.time() - row["time"] < self.cache_ttl:
                return {**row["result"], "cached": True, "cached_at": row["time"]}
        return None

    def _store(self, key, result):
        with self._lock:
            self._cache[key] = {"time": time.time(), "result": dict(result)}
            if len(self._cache) > 1000:
                oldest = sorted(self._cache, key=lambda item: self._cache[item]["time"])[:200]
                for item in oldest:
                    self._cache.pop(item, None)
        return result

    @staticmethod
    def _normalise(data, kind, value, gui_path):
        attrs = (data.get("data") or {}).get("attributes") or {}
        stats = attrs.get("last_analysis_stats") or {}
        results = attrs.get("last_analysis_results") or {}
        engines = []
        for name, row in results.items():
            category = str((row or {}).get("category") or "undetected")
            if category not in ("malicious", "suspicious"):
                continue
            engines.append({
                "engine": name,
                "category": category,
                "result": str((row or {}).get("result") or category)[:200],
            })
        engines.sort(key=lambda row: (row["category"] != "malicious", row["engine"].lower()))
        malicious = int(stats.get("malicious", 0))
        suspicious = int(stats.get("suspicious", 0))
        total = sum(int(number or 0) for number in stats.values())
        return {
            "ok": True, "kind": kind, "value": value,
            "malicious": malicious, "suspicious": suspicious,
            "undetected": int(stats.get("undetected", 0)),
            "harmless": int(stats.get("harmless", 0)),
            "total_engines": total,
            "threat": malicious > 0 or suspicious > 1,
            "risk": "high" if malicious >= 3 else "medium" if malicious or suspicious else "clean",
            "engines": engines[:20],
            "tags": [str(tag)[:80] for tag in (attrs.get("tags") or [])[:20]],
            "categories": attrs.get("categories") or {},
            "reputation": int(attrs.get("reputation", 0) or 0),
            "last_analysis_date": attrs.get("last_analysis_date"),
            "link": f"https://www.virustotal.com/gui/{gui_path}",
            "cached": False,
        }

    def _lookup(self, endpoint, cache_key, kind, value, gui_path):
        if not self.api_key:
            return {"ok": False, "error": "API Key de VirusTotal no configurada"}
        cached = self._cached(cache_key)
        if cached:
            return cached
        try:
            response = requests.get(
                f"{self.base_url}/{endpoint}", headers=self._headers(), timeout=(5, 20)
            )
            if response.status_code == 200:
                return self._store(
                    cache_key, self._normalise(response.json(), kind, value, gui_path)
                )
            if response.status_code == 404:
                return {"ok": True, "kind": kind, "value": value, "not_found": True,
                        "malicious": 0, "suspicious": 0, "total_engines": 0, "cached": False}
            if response.status_code == 429:
                return {"ok": False, "error": "Cuota de VirusTotal agotada", "retryable": True}
            return {"ok": False, "error": f"VirusTotal respondió HTTP {response.status_code}"}
        except requests.RequestException as error:
            return {"ok": False, "error": f"VirusTotal no disponible: {error}", "retryable": True}

    def scan_hash(self, file_hash):
        value = str(file_hash or "").strip().lower()
        if len(value) not in (32, 40, 64) or any(ch not in "0123456789abcdef" for ch in value):
            return {"ok": False, "error": "Hash MD5, SHA-1 o SHA-256 inválido"}
        return self._lookup(f"files/{value}", f"hash:{value}", "hash", value, f"file/{value}")

    def scan_url(self, url, submit_if_unknown=True):
        value = str(url or "").strip()
        parsed = urlparse(value)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or len(value) > 2048:
            return {"ok": False, "error": "URL HTTP/HTTPS inválida"}
        url_id = base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")
        result = self._lookup(f"urls/{url_id}", f"url:{value}", "url", value, f"url/{url_id}")
        if not result.get("not_found") or not submit_if_unknown or not self.api_key:
            return result
        try:
            response = requests.post(
                f"{self.base_url}/urls", headers=self._headers(),
                data={"url": value}, timeout=(5, 20),
            )
            if response.status_code in (200, 201):
                return {"ok": True, "kind": "url", "value": value, "queued": True,
                        "analysis_id": (response.json().get("data") or {}).get("id"),
                        "message": "URL enviada a VirusTotal para análisis"}
            return result
        except requests.RequestException:
            return result

    def scan_domain(self, domain):
        value = str(domain or "").strip().lower().rstrip(".")
        if "://" in value:
            value = urlparse(value).hostname or ""
        try:
            ascii_domain = value.encode("idna").decode("ascii")
        except UnicodeError:
            return {"ok": False, "error": "Dominio inválido"}
        if not ascii_domain or "." not in ascii_domain or len(ascii_domain) > 253:
            return {"ok": False, "error": "Dominio inválido"}
        return self._lookup(
            f"domains/{ascii_domain}", f"domain:{ascii_domain}", "domain",
            ascii_domain, f"domain/{ascii_domain}",
        )

    def scan_file(self, path, filename=None):
        digest = hashlib.sha256()
        with open(path, "rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        sha256 = digest.hexdigest()
        known = self.scan_hash(sha256)
        if not known.get("not_found"):
            known["filename"] = filename or os.path.basename(path)
            return known
        if not self.api_key:
            return known
        try:
            with open(path, "rb") as source:
                response = requests.post(
                    f"{self.base_url}/files", headers=self._headers(),
                    files={"file": (filename or os.path.basename(path), source)},
                    timeout=(10, 120),
                )
            if response.status_code in (200, 201):
                return {"ok": True, "kind": "file", "value": sha256,
                        "filename": filename or os.path.basename(path), "queued": True,
                        "analysis_id": (response.json().get("data") or {}).get("id"),
                        "message": "Archivo enviado a VirusTotal para análisis"}
            return {"ok": False, "error": f"VirusTotal respondió HTTP {response.status_code}"}
        except requests.RequestException as error:
            return {"ok": False, "error": f"No se pudo subir el archivo: {error}", "retryable": True}

    def analyze(self, kind, value):
        if kind == "hash":
            return self.scan_hash(value)
        if kind == "url":
            return self.scan_url(value)
        if kind == "domain":
            return self.scan_domain(value)
        return {"ok": False, "error": "Tipo de análisis no compatible"}

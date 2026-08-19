"""Cliente seguro para la Wayback Availability JSON API de Internet Archive."""

import datetime
import ipaddress
import re
from urllib.parse import urlparse

import requests


class WaybackClient:
    API_URL = "https://archive.org/wayback/available"
    _TIMESTAMP = re.compile(r"^\d{1,14}$")

    def __init__(self, db, log=None):
        self.db = db
        self.log = log or (lambda *args: None)

    @staticmethod
    def normalize_url(value):
        value = str(value or "").strip()
        if not value:
            raise ValueError("URL requerida")
        if "://" not in value:
            value = "https://" + value
        parsed = urlparse(value)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError("Solo se admiten URLs HTTP o HTTPS")
        if parsed.username or parsed.password:
            raise ValueError("No se admiten credenciales dentro de la URL")
        host = parsed.hostname.lower().rstrip(".")
        if host in ("localhost", "localhost.localdomain") or host.endswith((".local", ".internal")):
            raise ValueError("No se admiten direcciones locales")
        try:
            if ipaddress.ip_address(host).is_private or ipaddress.ip_address(host).is_loopback:
                raise ValueError("No se admiten direcciones privadas")
        except ValueError as error:
            if "no se admiten" in str(error).lower():
                raise
        if len(value) > 2048:
            raise ValueError("La URL supera 2048 caracteres")
        return value

    def lookup(self, url, timestamp=None):
        try:
            normalized = self.normalize_url(url)
            timestamp = str(timestamp or "").strip()
            if timestamp and not self._TIMESTAMP.fullmatch(timestamp):
                return {"ok": False, "error": "La fecha debe usar 1-14 dígitos: YYYYMMDDhhmmss"}
            params = {"url": normalized}
            if timestamp:
                params["timestamp"] = timestamp
            response = requests.get(self.API_URL, params=params, timeout=12)
            response.raise_for_status()
            closest = (response.json().get("archived_snapshots") or {}).get("closest") or {}
            available = bool(closest.get("available"))
            result = {
                "ok": True, "available": available, "requested_url": normalized,
                "requested_timestamp": timestamp or None,
                "snapshot_url": closest.get("url") if available else None,
                "snapshot_timestamp": closest.get("timestamp") if available else None,
                "status": str(closest.get("status")) if closest.get("status") is not None else None,
            }
            rows = self.db.get("WAYBACK_HISTORY", [])
            rows = rows if isinstance(rows, list) else []
            rows.append({**result, "checked_at": datetime.datetime.now().isoformat()})
            self.db.set("WAYBACK_HISTORY", rows[-200:])
            return result
        except (ValueError, requests.RequestException, TypeError) as error:
            self.log("ERROR", f"Wayback lookup: {error}")
            return {"ok": False, "error": str(error)}

    def history(self, limit=50):
        rows = self.db.get("WAYBACK_HISTORY", [])
        return list(reversed(rows[-max(1, min(int(limit), 200)):])) if isinstance(rows, list) else []

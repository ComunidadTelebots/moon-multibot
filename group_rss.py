"""Suscripciones RSS/Atom independientes por grupo de Telegram."""

import datetime
import hashlib
import ipaddress
import socket
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse


class _SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        GroupRssManager.validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class GroupRssManager:
    MAX_FEEDS = 20
    MAX_BYTES = 1_500_000
    MAX_SEEN = 150

    def __init__(self, db):
        self.db = db
        self.opener = urllib.request.build_opener(_SafeRedirect())

    @staticmethod
    def validate_url(value):
        url = str(value or "").strip()
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("La URL RSS debe ser HTTP o HTTPS y no incluir credenciales")
        try:
            addresses = {row[4][0].split("%")[0] for row in socket.getaddrinfo(parsed.hostname, parsed.port or 443)}
        except socket.gaierror as error:
            raise ValueError("No se pudo resolver el servidor RSS") from error
        for raw in addresses:
            ip = ipaddress.ip_address(raw)
            if any((ip.is_private, ip.is_loopback, ip.is_link_local, ip.is_reserved,
                    ip.is_multicast, ip.is_unspecified)):
                raise ValueError("El RSS apunta a una red privada o no permitida")
        return url

    def _key(self, chat_id):
        return f"GROUP_RSS_{chat_id}"

    def _feeds(self, chat_id):
        value = self.db.get(self._key(chat_id), []) or []
        return value if isinstance(value, list) else []

    def list(self, chat_id):
        output = []
        for item in self._feeds(chat_id):
            row = dict(item)
            row["health"] = ("paused" if row.get("paused_reason") else
                             "error" if row.get("last_error") else
                             "active" if row.get("enabled") else "disabled")
            if row.get("enabled") and row.get("last_checked_at"):
                try:
                    last = datetime.datetime.fromisoformat(row["last_checked_at"])
                    failures = min(4, int(row.get("consecutive_failures", 0)))
                    minutes = min(1440, int(row.get("poll_interval_minutes", 15)) * (2 ** failures))
                    row["next_check_at"] = (last + datetime.timedelta(minutes=minutes)).isoformat()
                except (TypeError, ValueError):
                    row["next_check_at"] = None
            else:
                row["next_check_at"] = None
            output.append(row)
        return output

    def _save(self, chat_id, feeds):
        self.db.set(self._key(chat_id), feeds)
        groups = self.db.get("GROUP_RSS_GROUPS", []) or []
        group_id = str(chat_id)
        groups = [str(item) for item in groups if str(item) != group_id]
        if feeds:
            groups.append(group_id)
        self.db.set("GROUP_RSS_GROUPS", groups)
        return self.list(chat_id)

    def add(self, chat_id, url, title="", created_by=""):
        url = self.validate_url(url)
        feeds = self._feeds(chat_id)
        if len(feeds) >= self.MAX_FEEDS:
            raise ValueError(f"Cada grupo admite un máximo de {self.MAX_FEEDS} RSS")
        if any(item.get("url") == url for item in feeds):
            raise ValueError("Ese RSS ya está añadido al grupo")
        feed_id = hashlib.sha256(f"{chat_id}:{url}".encode()).hexdigest()[:16]
        feed = {"id": feed_id, "url": url, "title": str(title or "").strip()[:120],
                "enabled": False, "created_by": str(created_by)[:40],
                "include_keywords": [], "exclude_keywords": [],
                "template": "📰 **{title}**\n{url}", "message_thread_id": None,
                "poll_interval_minutes": 15, "max_entries_per_cycle": 3,
                "pause_after_failures": 5, "consecutive_failures": 0,
                "quiet_start_utc": None, "quiet_end_utc": None, "paused_reason": None,
                "checks_count": 0, "published_count": 0, "filtered_count": 0,
                "error_count": 0, "last_success_at": None,
                "last_duration_ms": None,
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "last_checked_at": None, "last_published_at": None, "last_error": None,
                "initialized": False, "seen": []}
        feeds.append(feed)
        self._save(chat_id, feeds)
        return dict(feed)

    def set_enabled(self, chat_id, feed_id, enabled):
        feeds = self._feeds(chat_id)
        match = next((item for item in feeds if item.get("id") == str(feed_id)), None)
        if not match:
            raise KeyError("RSS no encontrado")
        match["enabled"] = bool(enabled)
        match["last_error"] = None
        if enabled:
            match["paused_reason"] = None
            match["consecutive_failures"] = 0
        self._save(chat_id, feeds)
        return dict(match)

    def configure(self, chat_id, feed_id, values):
        feeds = self._feeds(chat_id)
        match = next((item for item in feeds if item.get("id") == str(feed_id)), None)
        if not match:
            raise KeyError("RSS no encontrado")
        if "title" in values:
            match["title"] = str(values.get("title") or "").strip()[:120]
        for field in ("include_keywords", "exclude_keywords"):
            if field in values:
                raw = values.get(field) or []
                if isinstance(raw, str):
                    raw = raw.split(",")
                match[field] = list(dict.fromkeys(str(item).strip().casefold() for item in raw if str(item).strip()))[:30]
        if "template" in values:
            template = str(values.get("template") or "").strip()
            if not template or len(template) > 3500 or "{url}" not in template:
                raise ValueError("La plantilla debe incluir {url} y no superar 3500 caracteres")
            match["template"] = template
        if "message_thread_id" in values:
            raw_thread = str(values.get("message_thread_id") or "").strip()
            if raw_thread and not raw_thread.isdigit():
                raise ValueError("El ID del tema debe ser numérico")
            match["message_thread_id"] = int(raw_thread) if raw_thread else None
        for field, minimum, maximum, default in (
            ("poll_interval_minutes", 5, 1440, 15),
            ("max_entries_per_cycle", 1, 10, 3),
            ("pause_after_failures", 1, 20, 5),
        ):
            if field in values:
                try:
                    match[field] = max(minimum, min(maximum, int(values.get(field, default))))
                except (TypeError, ValueError) as error:
                    raise ValueError(f"{field} debe ser numérico") from error
        for field in ("quiet_start_utc", "quiet_end_utc"):
            if field in values:
                raw = str(values.get(field) if values.get(field) is not None else "").strip()
                if raw and (not raw.isdigit() or not 0 <= int(raw) <= 23):
                    raise ValueError("Las horas silenciosas deben estar entre 0 y 23 UTC")
                match[field] = int(raw) if raw else None
        self._save(chat_id, feeds)
        return dict(match)

    def reset_cursor(self, chat_id, feed_id):
        feeds = self._feeds(chat_id)
        match = next((item for item in feeds if item.get("id") == str(feed_id)), None)
        if not match:
            raise KeyError("RSS no encontrado")
        match.update({"initialized": False, "seen": [], "last_checked_at": None,
                      "last_error": None, "consecutive_failures": 0})
        self._save(chat_id, feeds)
        return dict(match)

    def reset_metrics(self, chat_id, feed_id):
        feeds = self._feeds(chat_id)
        match = next((item for item in feeds if item.get("id") == str(feed_id)), None)
        if not match:
            raise KeyError("RSS no encontrado")
        match.update({"checks_count": 0, "published_count": 0, "filtered_count": 0,
                      "error_count": 0, "last_duration_ms": None})
        self._save(chat_id, feeds)
        return dict(match)

    def clear_history(self, chat_id):
        self.db.set(f"GROUP_RSS_HISTORY_{chat_id}", [])

    def history(self, chat_id, limit=50):
        rows = self.db.get(f"GROUP_RSS_HISTORY_{chat_id}", []) or []
        return list(rows)[-max(1, min(200, int(limit))):][::-1]

    def remove(self, chat_id, feed_id):
        feeds = self._feeds(chat_id)
        kept = [item for item in feeds if item.get("id") != str(feed_id)]
        if len(kept) == len(feeds):
            raise KeyError("RSS no encontrado")
        self._save(chat_id, kept)

    @staticmethod
    def _tag(node):
        return node.tag.rsplit("}", 1)[-1].lower()

    @classmethod
    def _child_text(cls, node, names):
        for child in list(node):
            if cls._tag(child) in names and (child.text or "").strip():
                return (child.text or "").strip()
        return ""

    def fetch(self, url):
        safe_url = self.validate_url(url)
        request = urllib.request.Request(safe_url, headers={"User-Agent": "Moonbot-RSS/1.0", "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"})
        with self.opener.open(request, timeout=10) as response:
            data = response.read(self.MAX_BYTES + 1)
            final_url = self.validate_url(response.geturl())
        if len(data) > self.MAX_BYTES:
            raise ValueError("El RSS supera el tamaño permitido")
        root = ET.fromstring(data)
        entries = [node for node in root.iter() if self._tag(node) in ("item", "entry")]
        output = []
        for node in entries[:50]:
            title = self._child_text(node, {"title"}) or "Nueva publicación"
            link = self._child_text(node, {"link"})
            if not link:
                link_node = next((child for child in list(node) if self._tag(child) == "link"), None)
                link = (link_node.attrib.get("href", "") if link_node is not None else "")
            link = urljoin(final_url, link.strip()) if link else final_url
            uid = self._child_text(node, {"guid", "id"}) or link or title
            output.append({"id": hashlib.sha256(uid.encode("utf-8", "ignore")).hexdigest(),
                           "title": title[:300], "url": link[:2000]})
        if not output:
            raise ValueError("No se encontraron entradas RSS o Atom")
        return output

    @staticmethod
    def _in_quiet_hours(feed, now):
        start, end = feed.get("quiet_start_utc"), feed.get("quiet_end_utc")
        if start is None or end is None or start == end:
            return False
        return start <= now.hour < end if start < end else now.hour >= start or now.hour < end

    def poll(self, chat_filter=None, feed_filter=None, force=False):
        """Devuelve entradas nuevas. La primera lectura inicializa sin publicar históricos."""
        pending = []
        now = datetime.datetime.now(datetime.timezone.utc)
        for chat_id in list(self.db.get("GROUP_RSS_GROUPS", []) or []):
            if chat_filter is not None and str(chat_id) != str(chat_filter):
                continue
            feeds = self._feeds(chat_id)
            changed = False
            for feed in feeds:
                if not feed.get("enabled") and not force:
                    continue
                if feed_filter is not None and str(feed.get("id")) != str(feed_filter):
                    continue
                try:
                    last = datetime.datetime.fromisoformat(feed["last_checked_at"]) if feed.get("last_checked_at") else None
                except (TypeError, ValueError):
                    last = None
                failures = min(4, int(feed.get("consecutive_failures", 0)))
                effective_minutes = min(1440, int(feed.get("poll_interval_minutes", 15)) * (2 ** failures))
                if not force and last and (now - last).total_seconds() < effective_minutes * 60:
                    continue
                if not force and self._in_quiet_hours(feed, now):
                    continue
                try:
                    started = time.monotonic()
                    feed["checks_count"] = int(feed.get("checks_count", 0)) + 1
                    entries = self.fetch(feed["url"])
                    feed["last_duration_ms"] = round((time.monotonic() - started) * 1000)
                    known = set(feed.get("seen") or [])
                    if feed.get("initialized"):
                        fresh = [item for item in entries if item["id"] not in known][:int(feed.get("max_entries_per_cycle", 3))]
                        for entry in reversed(fresh):
                            searchable = entry["title"].casefold()
                            includes = feed.get("include_keywords") or []
                            excludes = feed.get("exclude_keywords") or []
                            if includes and not any(word in searchable for word in includes):
                                feed["seen"] = [entry["id"]] + list(feed.get("seen") or [])
                                feed["filtered_count"] = int(feed.get("filtered_count", 0)) + 1
                                continue
                            if any(word in searchable for word in excludes):
                                feed["seen"] = [entry["id"]] + list(feed.get("seen") or [])
                                feed["filtered_count"] = int(feed.get("filtered_count", 0)) + 1
                                continue
                            pending.append({"chat_id": str(chat_id), "feed_id": feed["id"],
                                            "source": feed.get("title") or feed.get("url"),
                                            "template": feed.get("template") or "📰 **{title}**\n{url}",
                                            "message_thread_id": feed.get("message_thread_id"), **entry})
                    else:
                        feed["seen"] = [item["id"] for item in entries][:self.MAX_SEEN]
                    feed["initialized"] = True
                    feed["last_error"] = None
                    feed["consecutive_failures"] = 0
                    feed["last_success_at"] = now.isoformat()
                except Exception as error:
                    if "started" in locals():
                        feed["last_duration_ms"] = round((time.monotonic() - started) * 1000)
                    feed["last_error"] = str(error)[:240]
                    feed["error_count"] = int(feed.get("error_count", 0)) + 1
                    feed["consecutive_failures"] = int(feed.get("consecutive_failures", 0)) + 1
                    if feed["consecutive_failures"] >= int(feed.get("pause_after_failures", 5)):
                        feed["enabled"] = False
                        feed["paused_reason"] = "Pausado automáticamente por fallos consecutivos"
                feed["last_checked_at"] = now.isoformat()
                changed = True
            if changed:
                self._save(chat_id, feeds)
        return pending

    def mark_published(self, chat_id, feed_id, entry=None):
        entry_data = entry if isinstance(entry, dict) else {"id": entry}
        entry_id = entry_data.get("id")
        feeds = self._feeds(chat_id)
        for feed in feeds:
            if feed.get("id") == str(feed_id):
                feed["last_published_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                feed["published_count"] = int(feed.get("published_count", 0)) + 1
                if entry_id:
                    feed["seen"] = [str(entry_id)] + [item for item in (feed.get("seen") or []) if item != str(entry_id)]
                    feed["seen"] = feed["seen"][:self.MAX_SEEN]
        self._save(chat_id, feeds)
        if entry_id:
            history = self.db.get(f"GROUP_RSS_HISTORY_{chat_id}", []) or []
            history.append({"feed_id": str(feed_id), "entry_id": str(entry_id),
                            "title": str(entry_data.get("title") or "")[:300],
                            "url": str(entry_data.get("url") or "")[:2000],
                            "source": str(entry_data.get("source") or "")[:120],
                            "published_at": datetime.datetime.now(datetime.timezone.utc).isoformat()})
            self.db.set(f"GROUP_RSS_HISTORY_{chat_id}", history[-200:])

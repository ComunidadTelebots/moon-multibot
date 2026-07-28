"""Suscripciones RSS/Atom independientes por grupo de Telegram."""

import datetime
import hashlib
import ipaddress
import socket
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
        return [dict(item) for item in self._feeds(chat_id)]

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
        self._save(chat_id, feeds)
        return dict(match)

    def configure(self, chat_id, feed_id, values):
        feeds = self._feeds(chat_id)
        match = next((item for item in feeds if item.get("id") == str(feed_id)), None)
        if not match:
            raise KeyError("RSS no encontrado")
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
        self._save(chat_id, feeds)
        return dict(match)

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

    def poll(self):
        """Devuelve entradas nuevas. La primera lectura inicializa sin publicar históricos."""
        pending = []
        for chat_id in list(self.db.get("GROUP_RSS_GROUPS", []) or []):
            feeds = self._feeds(chat_id)
            changed = False
            for feed in feeds:
                if not feed.get("enabled"):
                    continue
                try:
                    entries = self.fetch(feed["url"])
                    known = set(feed.get("seen") or [])
                    if feed.get("initialized"):
                        fresh = [item for item in entries if item["id"] not in known][:3]
                        for entry in reversed(fresh):
                            searchable = entry["title"].casefold()
                            includes = feed.get("include_keywords") or []
                            excludes = feed.get("exclude_keywords") or []
                            if includes and not any(word in searchable for word in includes):
                                feed["seen"] = [entry["id"]] + list(feed.get("seen") or [])
                                continue
                            if any(word in searchable for word in excludes):
                                feed["seen"] = [entry["id"]] + list(feed.get("seen") or [])
                                continue
                            pending.append({"chat_id": str(chat_id), "feed_id": feed["id"],
                                            "source": feed.get("title") or feed.get("url"),
                                            "template": feed.get("template") or "📰 **{title}**\n{url}",
                                            "message_thread_id": feed.get("message_thread_id"), **entry})
                    else:
                        feed["seen"] = [item["id"] for item in entries][:self.MAX_SEEN]
                    feed["initialized"] = True
                    feed["last_error"] = None
                except Exception as error:
                    feed["last_error"] = str(error)[:240]
                feed["last_checked_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                changed = True
            if changed:
                self._save(chat_id, feeds)
        return pending

    def mark_published(self, chat_id, feed_id, entry_id=None):
        feeds = self._feeds(chat_id)
        for feed in feeds:
            if feed.get("id") == str(feed_id):
                feed["last_published_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                if entry_id:
                    feed["seen"] = [str(entry_id)] + [item for item in (feed.get("seen") or []) if item != str(entry_id)]
                    feed["seen"] = feed["seen"][:self.MAX_SEEN]
        self._save(chat_id, feeds)

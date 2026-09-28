"""Bounded public article reader. URLs come from AllTech posts, never request input."""
import http.client
import ipaddress
import json
import re
import socket
import ssl
import threading
import time
from collections import OrderedDict
from html.parser import HTMLParser
from urllib.parse import urlsplit, urljoin

MAX_BYTES = 2 * 1024 * 1024
_slots = threading.BoundedSemaphore(2)
_cache = OrderedDict()
_lock = threading.Lock()


def public_address(host):
    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(row[4][0]).is_global for row in addresses):
        raise ValueError('Destino no permitido')
    return next((row[4][0] for row in addresses if row[0] == socket.AF_INET), addresses[0][4][0])


class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host, address, timeout):
        super().__init__(host, timeout=timeout)
        self.address = address

    def connect(self):
        raw = socket.create_connection((self.address, 443), self.timeout)
        try:
            self.sock = ssl.create_default_context().wrap_socket(raw, server_hostname=self.host)
        except Exception:
            raw.close()
            raise


def fetch_page(url, deadline):
    for _ in range(6):
        p = urlsplit(url)
        if p.scheme != 'https' or not p.hostname or p.username or p.password or p.port not in (None, 443):
            raise ValueError('Enlace no permitido')
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('Tiempo agotado')
        connection = PinnedHTTPS(p.hostname, public_address(p.hostname), min(6, remaining))
        try:
            connection.request('GET', (p.path or '/') + ('?' + p.query if p.query else ''),
                               headers={'User-Agent': 'MoonbotHubReader/1.0', 'Accept': 'text/html', 'Accept-Encoding': 'identity'})
            response = connection.getresponse()
            if response.status in (301, 302, 303, 307, 308):
                url = urljoin(url, response.getheader('Location', ''))
                continue
            if response.status != 200 or 'text/html' not in response.getheader('Content-Type', ''):
                raise ValueError('La fuente no permite la lectura')
            chunks, size = [], 0
            while True:
                if time.monotonic() > deadline:
                    raise TimeoutError('Tiempo agotado')
                chunk = response.read(32768)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_BYTES:
                    raise ValueError('Artículo demasiado grande')
                chunks.append(chunk)
            return b''.join(chunks).decode('utf-8', errors='replace'), url
        finally:
            connection.close()
    raise ValueError('Demasiadas redirecciones')


class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.blocks = []
        self.active = None
        self.title = []
        self.jsonld = []
        self.script = None
        self.links = []
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get('class', '')
        if tag == 'meta':
            self.meta[attrs.get('property', attrs.get('name', '')).lower()] = attrs.get('content', '')
        if tag == 'a' and ('tgme_widget_message_link_preview' in classes or any('tgme_widget_message_text' in c for _, c in self.stack)):
            self.links.append(attrs.get('href', ''))
        if tag == 'script':
            self.script = [] if attrs.get('type') == 'application/ld+json' else None
        if tag not in ('img', 'meta', 'link', 'br', 'hr', 'input', 'source', 'wbr'):
            self.stack.append((tag, classes))
        if tag in ('p', 'h1', 'h2', 'h3', 'li', 'blockquote') and not any(t in ('nav', 'footer', 'header', 'aside', 'script', 'style') for t, _ in self.stack):
            self.active = [tag, [], any(t in ('article', 'main') for t, _ in self.stack)]

    def handle_data(self, data):
        if self.stack and self.stack[-1][0] == 'script':
            if self.script is not None:
                self.script.append(data)
            return
        if any(t in ('script', 'style', 'noscript') for t, _ in self.stack):
            return
        if self.stack and self.stack[-1][0] == 'title':
            self.title.append(data)
        if self.active:
            self.active[1].append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.script is not None:
            try:
                self.jsonld.append(json.loads(''.join(self.script)))
            except ValueError:
                pass
            self.script = None
        if self.active and tag == self.active[0]:
            text = re.sub(r'\s+', ' ', ''.join(self.active[1])).strip()
            if text:
                self.blocks.append((tag, text, self.active[2]))
            self.active = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break


def extract_article(markup):
    parser = ArticleParser()
    parser.feed(markup)
    def body(value):
        if isinstance(value, dict):
            if value.get('isAccessibleForFree') in (False, 'False', 'false'):
                raise ValueError('Este artículo requiere acceso en el medio original')
            if isinstance(value.get('articleBody'), str) and len(value['articleBody']) > 300:
                return value['articleBody']
            for child in value.values():
                found = body(child)
                if found:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = body(child)
                if found:
                    return found
        return None
    full = body(parser.jsonld)
    def nodes(value):
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from nodes(child)
        elif isinstance(value, list):
            for child in value:
                yield from nodes(child)
    news = next((node for node in nodes(parser.jsonld) if any('Article' in str(t) or str(t) == 'BlogPosting' for t in (node.get('@type') if isinstance(node.get('@type'), list) else [node.get('@type', '')]))), {})
    def names(value):
        if isinstance(value, list):
            return ', '.join(filter(None, (names(item) for item in value)))
        if isinstance(value, dict):
            return str(value.get('name') or '')
        return value if isinstance(value, str) else ''
    author = names(news.get('author')) or parser.meta.get('author', '')
    metadata = {
        'author': author[:300],
        'editor': names(news.get('editor'))[:300],
        'published_at': str(news.get('datePublished') or parser.meta.get('article:published_time', ''))[:100],
        'publisher_name': (names(news.get('publisher')) or parser.meta.get('og:site_name', ''))[:200],
    }
    blocks = [{'type': 'p', 'text': p.strip()} for p in full.split('\n') if p.strip()] if full else [
        {'type': tag, 'text': text} for tag, text, inside in parser.blocks if inside]
    if sum(len(p['text']) for p in blocks) < 300:
        raise ValueError('La fuente no ofrece un artículo legible completo')
    if len(blocks) > 250:
        raise ValueError('Artículo demasiado largo para este lector')
    while blocks and author and blocks[0]['text'] == author:
        blocks.pop(0)
    return {'title': ''.join(parser.title).strip()[:300], 'blocks': blocks, **metadata}


def read_article(post_id):
    if not re.fullmatch(r'[1-9]\d{0,11}', str(post_id)):
        raise ValueError('Publicación no válida')
    with _lock:
        cached = _cache.get(post_id)
        if cached and time.monotonic() - cached[0] < (900 if cached[1].get('ok') else 60):
            return cached[1]
    if not _slots.acquire(blocking=False):
        return {'ok': False, 'error': 'El lector está ocupado. Reintenta en unos segundos.'}
    try:
        deadline = time.monotonic() + 22
        markup, _ = fetch_page(f'https://t.me/TodoSobreAllTech/{post_id}?embed=1&mode=tme', deadline)
        parser = ArticleParser()
        parser.feed(markup)
        source = next((u for u in parser.links if urlsplit(u).scheme == 'https' and urlsplit(u).hostname not in ('t.me', 'telegram.me')), None)
        if not source:
            raise ValueError('Esta publicación no contiene un enlace de noticia')
        markup, source = fetch_page(source, deadline)
        article = extract_article(markup)
        result = {'ok': True, 'post_id': post_id, 'source': source, 'publisher': urlsplit(source).hostname, **article}
    except (ValueError, OSError, http.client.HTTPException):
        result = {'ok': False, 'error': 'No se puede mostrar el artículo completo: la fuente no ofrece lectura pública compatible. Puedes volver a las noticias.'}
    finally:
        _slots.release()
    with _lock:
        _cache[post_id] = (time.monotonic(), result)
        _cache.move_to_end(post_id)
        while len(_cache) > 128:
            _cache.popitem(last=False)
    return result

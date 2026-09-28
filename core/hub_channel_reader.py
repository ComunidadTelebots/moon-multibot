"""Read-only AllTech channel view adapted from the Hub reader in release channels."""
import json
import threading
import time
import urllib.request
from urllib.parse import urlsplit
from flask import Blueprint, jsonify, send_from_directory
from pathlib import Path
from .hub_article_reader import read_article

bp = Blueprint('hub_channel_reader', __name__)
_cache = None
_cache_time = 0
_lock = threading.Lock()

def normalize_posts(payload):
    if not isinstance(payload, dict):
        raise ValueError('Invalid channel response')
    posts = []
    for row in (payload.get('messages') or [])[:40]:
        if not isinstance(row, dict):
            continue
        link = str(row.get('url') or '')
        parsed = urlsplit(link)
        parts = parsed.path.strip('/').split('/')
        if parsed.scheme != 'https' or parsed.netloc.lower() != 't.me' or len(parts) != 2 or parts[0].lower() != 'todosobrealltech' or not parts[1].isdigit():
            continue
        posts.append({'id': parts[1], 'url': link, 'text': str(row.get('text') or '')[:5000],
                      'date': str(row.get('date') or '')[:100], 'views': str(row.get('views') or '')[:30]})
    return posts

@bp.get('/api/public/network/instant/alltech')
def alltech_reader():
    global _cache, _cache_time
    stale = time.monotonic() - _cache_time > 180
    if _cache is not None and not stale:
        return jsonify({**_cache, 'cached': True, 'stale': False})
    if _lock.acquire(blocking=False):
        try:
            req = urllib.request.Request('https://todosobreall.tech/hcgi/api/telegram-channel/TodoSobreAllTech', headers={'Accept':'application/json'})
            with urllib.request.urlopen(req, timeout=10) as response:
                raw = response.read(1024*1024+1)
                if len(raw) > 1024*1024:
                    raise ValueError('Response too large')
                payload = json.loads(raw)
            _cache = {'ok':True, 'title':'TodoSobreAllTech', 'channel':'TodoSobreAllTech', 'posts':normalize_posts(payload)}
            _cache_time = time.monotonic()
            return jsonify({**_cache, 'cached':False, 'stale':False})
        except (OSError, ValueError):
            pass
        finally:
            _lock.release()
    if _cache is not None:
        return jsonify({**_cache, 'cached':True, 'stale':True})
    response = jsonify({'ok':False,'error':'No se pueden cargar las publicaciones ahora. Puedes abrir el canal en Telegram.'})
    response.headers['Retry-After'] = '15'
    return response, 503

@bp.get('/hub-channel-reader.js')
def reader_script():
    return send_from_directory(Path(__file__).resolve().parents[1] / 'web', 'hub-channel-reader.js', max_age=300)

@bp.get('/api/public/network/instant/alltech/article/<post_id>')
def alltech_article(post_id):
    try:
        result = read_article(post_id)
    except ValueError:
        return jsonify(ok=False, error='Publicación no válida'), 400
    response = jsonify(result)
    response.headers['Cache-Control'] = 'no-store'
    return response, 200 if result['ok'] else 422

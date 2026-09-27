"""Read-only, service-authenticated exploration of existing chat records."""
import hmac
import os
import re

from flask import jsonify, request


def conversation_snapshot(bots, db, bot_id=None, chat_id=None, query='', kind='all', page=1):
    bots = list(bots)
    if bot_id is None:
        return {'ok': True, 'bots': [
            {'id': str(bot.bot_id), 'username': str(bot.bot_username),
             'chats': len(set(map(str, db.get(f'CHATS_{bot.token}', []))))}
            for bot in bots if getattr(bot, 'bot_id', None)]}, 200
    bot = next((b for b in bots if str(getattr(b, 'bot_id', '')) == bot_id), None)
    if bot is None:
        return {'ok': False, 'error': 'Bot no disponible'}, 404
    ids = set(map(str, db.get(f'CHATS_{bot.token}', [])))
    if chat_id is not None:
        if chat_id not in ids:
            return {'ok': False, 'error': 'Chat no asociado al bot'}, 404
        history = db.get(f'CHAT_HIST_{chat_id}', [])
        safe = [{key: str(row[key])[:8000] for key in ('time', 'sender', 'text') if key in row}
                for row in history[-100:] if isinstance(row, dict)]
        return {'ok': True, 'history': safe, 'history_scope': 'shared_chat',
                'notice': 'Historial registrado por chat, compartido entre los bots presentes. No permite atribuir cada mensaje a este bot ni recuperar mensajes anteriores no guardados.'}, 200
    names = db.get('CHAT_NAMES', {})
    seen = db.get('U_FILE', {})
    rows = []
    for cid in sorted(ids):
        if not re.fullmatch(r'-?[1-9]\d*', cid):
            continue
        value = seen.get(cid, {})
        value = value if isinstance(value, dict) else {}
        ctype = 'private' if not cid.startswith('-') else 'community'
        name = str(names.get(cid) or value.get('name') or cid)
        if kind != 'all' and kind != ctype:
            continue
        if query.lower() not in (name + ' ' + cid).lower():
            continue
        rows.append({'id': cid, 'name': name, 'type': ctype, 'last_seen': value.get('last_seen')})
    pages = max(1, (len(rows) + 39) // 40)
    page = min(max(1, page), pages)
    return {'ok': True, 'chats': rows[(page-1)*40:page*40], 'page': page, 'pages': pages, 'total': len(rows)}, 200


def register_bot_conversations(app, get_bots, db):
    @app.get('/api/internal/bot-conversations')
    def bot_conversations():
        expected = os.getenv('MOON_ADMIN_API_KEY', '').strip()
        supplied = request.headers.get('X-Moon-Admin-Key', '').strip()
        if not expected or not supplied or not hmac.compare_digest(expected.encode(), supplied.encode()):
            return jsonify({'ok': False}), 401
        bot_id = request.args.get('bot_id') or None
        chat_id = request.args.get('chat_id') or None
        kind = request.args.get('type', 'all')
        if ((bot_id and not re.fullmatch(r'[1-9]\d{0,19}', bot_id)) or
                (chat_id and (not bot_id or not re.fullmatch(r'-?[1-9]\d{0,19}', chat_id))) or
                kind not in ('all', 'private', 'community')):
            return jsonify({'ok': False, 'error': 'Filtro inválido'}), 400
        try:
            page = max(1, int(request.args.get('page', '1')))
        except ValueError:
            return jsonify({'ok': False}), 400
        payload, status = conversation_snapshot(get_bots(), db, bot_id, chat_id,
                                                request.args.get('q', '')[:100], kind, page)
        response = jsonify(payload)
        response.headers['Cache-Control'] = 'private, no-store'
        return response, status

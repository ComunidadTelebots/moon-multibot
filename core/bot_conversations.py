"""Read-only, service-authenticated exploration of existing chat records."""
import hmac
import os
import re
import threading
import time

import requests
from flask import jsonify, request

ACTION_LOCK = threading.Lock()


def message_actions(row, bot_id):
    if (str(row.get('bot_id', '')) != bot_id or
            not isinstance(row.get('message_id'), int) or row['message_id'] <= 0 or
            row.get('deleted')):
        return []
    return ['reply', 'delete', 'forward', 'react'] + (['edit'] if row.get('outgoing') and row.get('text') else [])


def apply_message_action(bots, db, body, transport=None):
    """Validate recorded provenance before making exactly one HTTP attempt."""
    if not isinstance(body, dict):
        return {'ok': False, 'error': 'Solicitud inválida'}, 400
    bot_id, cid = str(body.get('bot_id', '')), str(body.get('chat_id', ''))
    bot = next((b for b in bots if str(getattr(b, 'bot_id', '')) == bot_id), None)
    if not bot or cid not in set(map(str, db.get(f'CHATS_{bot.token}', []))):
        return {'ok': False, 'error': 'Bot o chat no disponible'}, 404
    if type(body.get('message_id')) is not int:
        return {'ok': False, 'error': 'Identificador inválido'}, 400
    action = body.get('action')
    history = db.get(f'CHAT_HIST_{cid}', [])
    row = next((r for r in history if isinstance(r, dict) and
                r.get('message_id') == body.get('message_id') and
                str(r.get('bot_id', '')) == bot_id), None)
    if not row or action not in message_actions(row, bot_id):
        return {'ok': False, 'error': 'El mensaje no tiene identidad verificable para esta acción y este bot'}, 409
    params = {'chat_id': cid, 'message_id': row['message_id']}
    methods = {'reply': 'sendMessage', 'edit': 'editMessageText', 'delete': 'deleteMessage',
               'forward': 'forwardMessage', 'react': 'setMessageReaction'}
    if action in ('reply', 'edit'):
        text = body.get('text')
        if not isinstance(text, str) or not text.strip() or len(text) > 4096:
            return {'ok': False, 'error': 'Texto obligatorio, máximo 4096 caracteres'}, 400
        params['text'] = text
        if action == 'reply':
            params.pop('message_id')
            params['reply_parameters'] = {'message_id': row['message_id'], 'allow_sending_without_reply': False}
    if action == 'forward':
        target = str(body.get('target_chat_id', ''))
        if target not in set(map(str, db.get(f'CHATS_{bot.token}', []))):
            return {'ok': False, 'error': 'El destino debe ser un chat conocido por este bot'}, 400
        params.update(chat_id=target, from_chat_id=cid)
    if action == 'react':
        params['reaction'] = [{'type': 'emoji', 'emoji': '👍'}]
    request_id = str(body.get('request_id', ''))
    if not re.fullmatch(r'[a-f0-9-]{36}', request_id) or not body.get('actor_id'):
        return {'ok': False, 'error': 'Falta identidad de la operación'}, 400
    if not ACTION_LOCK.acquire(blocking=False):
        return {'ok': False, 'error': 'Hay otra acción en curso'}, 429
    try:
        audit = db.get('WEB_MESSAGE_ACTIONS', [])
        if any(item.get('id') == request_id for item in audit):
            return {'ok': False, 'error': 'Operación ya registrada; actualiza antes de repetir'}, 409
        event = {'id': request_id, 'actor': str(body['actor_id'])[:100], 'bot_id': bot_id,
                 'chat_id': cid, 'message_id': row['message_id'], 'action': action,
                 'time': int(time.time()), 'status': 'pending'}
        audit = (audit + [event])[-500:]
        db.set('WEB_MESSAGE_ACTIONS', audit)
        try:
            if transport:
                result = transport(bot, methods[action], params)
            else:
                result = requests.post(f"{bot.url.rstrip('/')}/{methods[action]}", json=params, timeout=(5, 20)).json()
        except (requests.RequestException, ValueError):
            event['status'] = 'unknown'
            db.set('WEB_MESSAGE_ACTIONS', audit)
            return {'ok': False, 'error': 'Resultado sin confirmar. Comprueba Telegram antes de repetir; no se reintentó automáticamente.'}, 502
        if not result.get('ok'):
            event['status'] = 'rejected'
            db.set('WEB_MESSAGE_ACTIONS', audit)
            return {'ok': False, 'error': 'Telegram rechazó la acción. Revisa permisos, antigüedad del mensaje y tipo de chat.'}, 409
        event['status'] = 'completed'
        db.set('WEB_MESSAGE_ACTIONS', audit)
        if action == 'delete':
            row['deleted'] = True
        if action == 'edit':
            row['text'] = body['text']
        sent = result.get('result')
        if action == 'reply' and isinstance(sent, dict) and sent.get('message_id'):
            history.append({'sender': 'Bot', 'text': body['text'], 'bot_id': bot_id,
                            'message_id': sent['message_id'], 'outgoing': True,
                            'time': time.strftime('%Y-%m-%d %H:%M:%S')})
            history = history[-200:]
        db.set(f'CHAT_HIST_{cid}', history)
        return {'ok': True, 'action': action}, 200
    finally:
        ACTION_LOCK.release()


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
        safe = [{**{key: str(row[key])[:8000] for key in ('time', 'sender', 'text') if key in row},
                 'message_id': row.get('message_id'), 'actions': message_actions(row, bot_id),
                 'deleted': bool(row.get('deleted'))}
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


def register_bot_conversations(app, get_bots, db, history_cache=None):
    @app.route('/api/internal/bot-conversations', methods=['GET', 'POST'])
    def bot_conversations():
        expected = os.getenv('MOON_ADMIN_API_KEY', '').strip()
        supplied = request.headers.get('X-Moon-Admin-Key', '').strip()
        if not expected or not supplied or not hmac.compare_digest(expected.encode(), supplied.encode()):
            return jsonify({'ok': False}), 401
        if request.method == 'POST':
            body = request.get_json(silent=True)
            payload, status = apply_message_action(get_bots(), db, body)
            if status == 200 and history_cache is not None:
                cid = str(body['chat_id'])
                history_cache[cid] = db.get(f'CHAT_HIST_{cid}', [])
            response = jsonify(payload)
            response.headers['Cache-Control'] = 'private, no-store'
            return response, status
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

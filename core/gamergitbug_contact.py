"""Opt-in portfolio contact flow; other bot commands retain their handlers."""
import time

PAYLOAD = 'gamergitbug_contact'
TTL = 1800


def handle_contact(bot, db, cid, uid, text, message_id=None, now=None):
    if str(getattr(bot, 'bot_username', '')).lstrip('@').lower() != 'cintiabot':
        return False
    if str(cid) != str(uid) or not str(cid).isdigit():
        return False
    text = str(text or '').strip()
    parts = text.split(maxsplit=1)
    command = parts[0].split('@', 1)[0].lower() if parts else ''
    if parts and '@' in parts[0] and parts[0].split('@', 1)[1].lower() != 'cintiabot':
        return False
    now = time.time() if now is None else now
    key = f'GAMERGITBUG_CONTACT_{bot.bot_id}_{cid}'
    state = db.get(key, {}) or {}
    opening = (command == '/start' and len(parts) == 2 and parts[1] == PAYLOAD) or command == '/contacto_gamergitbug'
    if opening:
        db.set(key, {**state, 'expires_at': now + TTL, 'status': 'awaiting_message'})
        bot.api_call('sendMessage', {'chat_id': cid, 'text':
            'Contacto oficial de GamerGitBug. Escribe tu consulta en el siguiente mensaje; '
            'el responsable podrá responderte aquí desde la web. No envíes contraseñas. '
            'Usa /cancelar_contacto para salir. Todas mis otras funciones siguen disponibles.'})
        return True
    if command in ('/cancelar_contacto', '/start', '/inicio'):
        if state.get('status') == 'awaiting_message':
            db.set(key, {**state, 'expires_at': 0, 'status': 'cancelled'})
        if command == '/cancelar_contacto':
            bot.api_call('sendMessage', {'chat_id': cid, 'text': 'Contacto cancelado. Puedes seguir usando el bot normalmente.'})
            return True
        return False
    if text.startswith('/') or state.get('status') != 'awaiting_message':
        return False
    if state.get('expires_at', 0) <= now:
        db.set(key, {**state, 'expires_at': 0, 'status': 'expired'})
        return False
    if not text:
        bot.api_call('sendMessage', {'chat_id': cid, 'text': 'Escribe tu consulta en texto para que podamos atenderla, o usa /cancelar_contacto.'})
        return True
    # The regular chat history already stores the content. Persist only routing metadata here.
    db.set(key, {'expires_at': 0, 'status': 'received', 'source': PAYLOAD,
                 'message_id': message_id, 'received_at': now})
    bot.api_call('sendMessage', {'chat_id': cid, 'text':
        'Consulta de GamerGitBug registrada. La respuesta del responsable llegará a este chat. '
        'Para otra consulta usa /contacto_gamergitbug. Ya puedes seguir usando las demás funciones del bot.'})
    return True

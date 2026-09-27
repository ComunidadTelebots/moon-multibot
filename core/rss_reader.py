"""Authenticated feed reader and explicit channel sharing from server-resolved entries."""
import hashlib
import html
import re
from urllib.parse import urlparse
from flask import jsonify, request
from core.rss_catalog import CATALOG
from core.rss_channels import channel_bot

WEBAPP_URL = "https://t.me/CintiaBot?startapp=rss"


def source_for(service, uid, source_id):
    source_id = str(source_id)
    if source_id.startswith("channel:"):
        parts=source_id.split(':',2)
        if len(parts)!=3 or not channel_bot(service,uid,parts[1]): return None
        return next((f for f in service.manager.list(parts[1]) if f.get('id')==parts[2]),None)
    if source_id.startswith("own:"):
        return next((f for f in service.manager.list(uid) if f.get("id") == source_id[4:]), None)
    return next((f for f in CATALOG if f['id'] == source_id), None)


def read_entries(service, uid, source_id):
    source = source_for(service, uid, source_id)
    if not source: raise KeyError("Fuente no encontrada")
    entries = service.manager.fetch(source['url'])
    safe = []
    for entry in entries[:50]:
        parsed = urlparse(str(entry.get('url','')))
        if len(str(entry.get('url',''))) > 2000 or parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password:
            continue
        safe.append({key: str(entry.get(key) or '') for key in ('id','title','url','summary','published_at')})
    return source, safe


def share_entry(service, uid, source_id, entry_id, cid):
    bot = channel_bot(service, uid, cid)
    if not bot: return {'ok':False,'error':'No tienes permiso para publicar en ese canal o el bot no puede publicar.'},403
    source, entries = read_entries(service, uid, source_id)
    entry = next((e for e in entries if e['id'] == str(entry_id)), None)
    if not entry: return {'ok':False,'error':'La noticia ya no está disponible. Actualiza el lector.'},404
    chat = bot.api_call('getChat', {'chat_id':cid})
    if not chat.get('ok'): return {'ok':False,'error':'No se pudo verificar el canal.'},503
    username = str(chat.get('result',{}).get('username','')).lower()
    link = urlparse(entry['url'])
    if username and (username in source.get('blocked_channels',[]) or (link.hostname in ('t.me','telegram.me') and link.path.lower().split('/')[1:2] == [username])):
        return {'ok':False,'error':'Esta noticia refleja el propio canal; no se reenviará para evitar bucles.'},400
    digest = hashlib.sha256(entry['url'].encode()).hexdigest()
    key = f"RSS_MANUAL_SHARES_{cid}"
    with service.lock:
        records = service.db.get(key, []) or []
        existing = next((r for r in records if r.get('digest') == digest),None)
        if existing:
            if existing.get('state') == 'sent': return {'ok':True,'already_sent':True},200
            return {'ok':False,'error':'Hay un envío pendiente de revisión; no se repetirá para evitar duplicados.'},409
        text = f"<b>{html.escape(entry['title'][:300])}</b>\n\n{html.escape(entry['url'])}\n\nFuente: {html.escape(str(source.get('title') or 'RSS')[:120])}\nDescubre más noticias en nuestra WebApp."
        record = {'digest':digest,'actor':str(uid),'state':'pending','at':service.clock().isoformat()}
        records = records[-499:] + [record]; service.db.set(key, records)
        try:
            result = bot.api_call('sendMessage', {'chat_id':cid,'text':text,'parse_mode':'HTML',
                 'reply_markup':{'inline_keyboard':[[{'text':'Abrir lector RSS · WebApp','url':WEBAPP_URL}]]}})
        except Exception:
            return {'ok':False,'error':'No se pudo confirmar el envío. No lo repitas hasta revisarlo.'},503
        if not isinstance(result,dict) or not result.get('ok'):
            return {'ok':False,'error':'Telegram no confirmó la publicación; queda pendiente de revisión.'},503
        record['state']='sent'; record['message_id']=result.get('result',{}).get('message_id')
        service.db.set(key,records)
        return {'ok':True,'sent':True},200


def register_reader_routes(app, service, public, authorized):
    def handle(uid, body):
        if not isinstance(body,dict): return jsonify(ok=False),400
        try:
            if body.get('action','read') == 'share':
                if not re.fullmatch(r'[1-9]\d{0,19}',str(uid)):return jsonify(ok=False,error='Vincula tu Telegram para publicar.'),403
                payload,status=share_entry(service,uid,str(body.get('source_id','')),str(body.get('entry_id','')),str(body.get('channel_id','')))
                return jsonify(payload),status
            if body.get('action','read') != 'read':return jsonify(ok=False),400
            source,entries=read_entries(service,uid,str(body.get('source_id','')))
            response=jsonify(ok=True,source={'title':source.get('title','RSS')},entries=entries,webapp_url=WEBAPP_URL)
            response.headers['Cache-Control']='no-store'
            return response
        except KeyError:return jsonify(ok=False,error='Fuente no encontrada'),404
        except Exception:return jsonify(ok=False,error='La fuente RSS no está disponible en este momento.'),502
    @app.post('/api/internal/rss/reader/<uid>')
    def internal_reader(uid):
        if not authorized():return jsonify(ok=False),401
        if not re.fullmatch(r'\d{1,20}',uid):return jsonify(ok=False),400
        return handle(uid,request.get_json(silent=True))
    @app.post('/api/public/rss/reader')
    def hub_reader():
        body=request.get_json(silent=True) or {}
        user=public._verify_init_data(body.get('initData','')) if isinstance(body,dict) else None
        if not user:return jsonify(ok=False,error='Abre el Hub desde Telegram.'),401
        return handle(str(user['id']),body)

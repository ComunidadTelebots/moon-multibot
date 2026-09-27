"""Channel RSS with live Telegram administrator and publishing-rights checks."""
import re
from flask import jsonify, request
from core.rss_catalog import CATALOG

def known_channels(public, uid):
    rows = public._channel_stats.get_user_channels(int(uid)) if public._channel_stats else []
    return [{"id":str(r.get("chat_id")), "name":str(r.get("name") or r.get("chat_id"))[:120]}
            for r in rows if r.get("ctype")=="channel" and re.fullmatch(r"-\d+",str(r.get("chat_id")))]


def channel_bot(service, uid, cid):
    if not re.fullmatch(r"-\d+", str(cid)) or not str(uid).isdigit():
        return None
    for bot in service.get_bots():
        if str(cid) not in {str(x) for x in service.db.get(f"CHATS_{bot.token}", [])}:
            continue
        try:
            chat=bot.api_call("getChat", {"chat_id":str(cid)})
            if not chat.get("ok") or chat.get("result",{}).get("type")!="channel": continue
            own=bot.api_call("getChatMember", {"chat_id":str(cid), "user_id":str(bot.token).split(":",1)[0]})
            rights=own.get("result",{}) if own.get("ok") else {}
            if rights.get("status") not in ("administrator","creator") or not rights.get("can_post_messages",rights.get("status")=="creator"): continue
            member=bot.api_call("getChatMember", {"chat_id":str(cid), "user_id":str(uid)})
            rights=member.get("result",{}) if member.get("ok") else {}
            if rights.get("status")=="creator" or (rights.get("status")=="administrator" and rights.get("can_post_messages")):
                return bot
        except Exception:
            continue
    return None


def register_channel_routes(app, service, public, authorized):
    def action(uid,cid,body):
        if not isinstance(body,dict): return {"ok":False,"error":"Solicitud no válida"},400
        if not channel_bot(service,uid,cid):
            return {"ok":False,"error":"Debes administrar el canal y tanto tú como el bot debéis tener permiso para publicar."},403
        if body.get("action") == "add" or (body.get("action") == "toggle" and body.get("enabled") is True):
            url = body.get("url") if body.get("action") == "add" else next((f.get("url") for f in service.manager.list(cid) if f.get("id") == body.get("feed_id")), None)
            rules = next((f.get("blocked_channels", []) for f in CATALOG if f["url"] == url), [])
            if rules:
                bot = channel_bot(service,uid,cid)
                chat = bot.api_call("getChat", {"chat_id":cid}) if bot else {}
                if not chat.get("ok"): return {"ok":False,"error":"No se pudo verificar el destino"},503
                if str(chat.get("result",{}).get("username","")).lower() in rules:
                    return {"ok":False,"error":"Esta fuente refleja ese mismo canal. No puede reenviarse a sí misma."},400
        if body.get("action")=="toggle" and not isinstance(body.get("enabled"),bool): return {"ok":False},400
        clean={k:body[k] for k in ("action","url","title","feed_id","enabled") if k in body}
        with service.lock:
            payload,status=service.action(cid,clean,uid)
            if status==200 and body.get("action") in ("add","toggle","delete"):
                service.db.set(f"PERSONAL_RSS_CHANNEL_OWNER_{cid}",str(uid))
            payload["destination"]={"id":cid,"type":"channel"}
        return payload,status
    @app.get("/api/internal/rss/channels/<uid>")
    def channels(uid):
        if not authorized(): return jsonify(ok=False),401
        if not re.fullmatch(r"[1-9]\d{0,19}",uid):return jsonify(ok=False),400
        return jsonify(ok=True,channels=known_channels(public,uid))
    @app.route("/api/internal/rss/channels/<uid>/<cid>",methods=["GET","POST"])
    def manage(uid,cid):
        if not authorized(): return jsonify(ok=False),401
        body=request.get_json(silent=True) or {} if request.method=='POST' else {"action":"list"}
        payload,status=action(uid,cid,body);return jsonify(payload),status
    @app.post("/api/public/rss/destinations")
    def destinations():
        body=request.get_json(silent=True) or {}
        user=public._verify_init_data(body.get("initData","")) if isinstance(body,dict) else None
        if not user:return jsonify(ok=False),401
        return jsonify(ok=True,channels=known_channels(public,str(user['id'])),catalog=CATALOG)
    @app.post("/api/public/rss/channel")
    def hub_channel():
        body=request.get_json(silent=True) or {}
        user=public._verify_init_data(body.get("initData","")) if isinstance(body,dict) else None
        if not user:return jsonify(ok=False),401
        payload,status=action(str(user['id']),str(body.get('chat_id','')),body)
        return jsonify(payload),status

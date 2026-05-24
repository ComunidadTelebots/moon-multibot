import json
import time

from flask import Blueprint, jsonify, request

bp = Blueprint("admin", __name__)

_check_jwt = None
_db = None
_add_audit_log = None
_get_global_chat_names = None
_get_proxy_bot = None
_get_global_user_stats = None
_get_global_msg_log = None
_get_ia_nativa = None
_get_maintenance_mode = None
_set_maintenance_mode = None


def setup(
    check_jwt,
    db,
    add_audit_log,
    get_global_chat_names,
    get_proxy_bot,
    get_global_user_stats,
    get_global_msg_log,
    get_ia_nativa,
    get_maintenance_mode,
    set_maintenance_mode,
):
    global _check_jwt, _db, _add_audit_log, _get_global_chat_names, _get_proxy_bot
    global _get_global_user_stats, _get_global_msg_log, _get_ia_nativa
    global _get_maintenance_mode, _set_maintenance_mode
    _check_jwt = check_jwt
    _db = db
    _add_audit_log = add_audit_log
    _get_global_chat_names = get_global_chat_names
    _get_proxy_bot = get_proxy_bot
    _get_global_user_stats = get_global_user_stats
    _get_global_msg_log = get_global_msg_log
    _get_ia_nativa = get_ia_nativa
    _get_maintenance_mode = get_maintenance_mode
    _set_maintenance_mode = set_maintenance_mode
    return bp


@bp.route("/api/admin/broadcast", methods=["POST"])
def web_admin_broadcast():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    msg = request.json.get("message", "")
    if not msg:
        return jsonify({"ok": False, "msg": "Mensaje vacio"}), 400
    proxy_bot = _get_proxy_bot()
    count = 0
    for cid in _get_global_chat_names():
        if proxy_bot and proxy_bot.send_msg(cid, f"COMUNICADO GLOBAL:\n\n{msg}"):
            count += 1
    _add_audit_log(f"Broadcast enviado a {count} chats")
    return jsonify({"ok": True, "count": count})


@bp.route("/api/admin/maintenance", methods=["POST"])
def web_admin_maintenance():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    new_status = not bool(_get_maintenance_mode())
    _set_maintenance_mode(new_status)
    return jsonify({"ok": True, "enabled": new_status})


@bp.route("/api/admin/shield", methods=["POST"])
def web_admin_shield():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    status = not _db.get("NEURAL_SHIELD", True)
    _db.set("NEURAL_SHIELD", status)
    return jsonify({"ok": True, "enabled": status})


@bp.route("/api/admin/summary")
def web_admin_summary():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    global_bans = _db.get("GLOBAL_BANS", {})
    if not isinstance(global_bans, dict):
        global_bans = {}
    return jsonify({
        "ok": True,
        "total_users": len(_db.keys("USER_")),
        "total_groups": len(_db.keys("ADMINS_")),
        "total_banned": len(global_bans.get("users", [])),
        "photos": _db.get("STATS_PHOTOS", 0),
        "videos": _db.get("STATS_VIDEOS", 0),
        "stats_24h": _db.get("IA_STATS_24H", {}),
    })


@bp.route("/api/admin/backup", methods=["POST"])
def web_admin_backup():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    ia_nativa = _get_ia_nativa()
    data = {
        "stats": _get_global_user_stats(),
        "history": _get_global_msg_log(),
        "brain": ia_nativa.brain if ia_nativa else {},
    }
    fname = f"data/backup_{int(time.time())}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return jsonify({"ok": True, "file": fname})

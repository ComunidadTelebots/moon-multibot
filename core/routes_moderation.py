import time

from flask import Blueprint, request, jsonify
from group_suite import GroupSuite

bp = Blueprint("moderation", __name__)

_check_jwt = None
_db = None
_ban_manager = None
_add_web_log = None
_add_audit_log = None
_global_user_stats = None
_get_bot_for_chat = None


def setup(check_jwt, db, ban_manager, add_web_log, add_audit_log, global_user_stats, get_bot_for_chat):
    global _check_jwt, _db, _ban_manager, _add_web_log, _add_audit_log
    global _global_user_stats, _get_bot_for_chat
    _check_jwt = check_jwt
    _db = db
    _ban_manager = ban_manager
    _add_web_log = add_web_log
    _add_audit_log = add_audit_log
    _global_user_stats = global_user_stats
    _get_bot_for_chat = get_bot_for_chat
    return bp


@bp.route("/api/users/leaderboard")
def web_leaderboard():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    sorted_u = sorted(_global_user_stats.items(), key=lambda x: x[1].get("count", 0), reverse=True)[:20]
    result = []
    for k, v in sorted_u:
        k_score = v.get("karma", 0)
        badge = "🏆 Leyenda" if k_score > 50 else "⭐ Colaborador" if k_score > 20 else "👤 Miembro"
        result.append({"id": k, "name": v.get("name", k), "count": v.get("count", 0), "karma": k_score, "badge": badge})
    return jsonify({"ok": True, "leaderboard": result})


@bp.route("/api/moderation/<cid>")
def web_mod_get(cid):
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    warns = _db.get(f"WARNS_{cid}", {})
    notes = _db.get(f"NOTES_{cid}", "")
    config = _db.get(f"CONFIG_{cid}", {
        "ia_learning": False, "auto_mod": True, "welcome": False, "security_shield": True,
    })
    feeders = _db.get("IA_FEEDERS", [])
    if str(cid) in [str(x) for x in feeders]:
        config["ia_learning"] = True
    return jsonify({
        "ok": True, "warns": warns, "notes": notes, "config": config,
        "local_bans": _ban_manager.get_local_bans(cid).get("users", []),
    })


@bp.route("/api/moderation/settings", methods=["POST"])
def web_mod_settings():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    d = request.json
    cid, config = d.get("cid"), d.get("config")
    if not cid or not config:
        return jsonify({"ok": False})
    _db.set(f"CONFIG_{cid}", config)
    feeders = _db.get("IA_FEEDERS", [])
    cid_str = str(cid)
    if config.get("ia_learning"):
        if cid_str not in [str(x) for x in feeders]:
            feeders.append(cid_str)
    else:
        if cid_str in [str(x) for x in feeders]:
            feeders.remove(cid_str)
    _db.set("IA_FEEDERS", feeders)
    _add_web_log("ADMIN", f"Configuración actualizada para grupo {cid}")
    return jsonify({"ok": True})


@bp.route("/api/moderation/notes", methods=["POST"])
def web_mod_notes():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    d = request.json
    cid, note = str(d.get("cid", "")), d.get("note", "")
    if not cid:
        return jsonify({"ok": False})
    _db.set(f"NOTES_{cid}", note)
    _add_audit_log(f"Nota guardada para grupo {cid}")
    return jsonify({"ok": True})


@bp.route("/api/moderation/unwarn", methods=["POST"])
def web_mod_unwarn():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    d = request.json
    cid, target = str(d.get("cid", "")), d.get("target", "")
    warns = _db.get(f"WARNS_{cid}", {})
    if target in warns:
        del warns[target]
        _db.set(f"WARNS_{cid}", warns)
    return jsonify({"ok": True})


@bp.route("/api/moderation/warn", methods=["POST"])
def web_warn():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    d = request.json
    cid, uid = d["cid"], d["uid"]
    warns = _db.get(f"WARNS_{cid}", {})
    warns[uid] = warns.get(uid, 0) + 1
    _db.set(f"WARNS_{cid}", warns)
    bot = _get_bot_for_chat(cid)
    if not bot:
        return jsonify({"ok": False, "msg": "Bot no encontrado para este grupo"}), 404
    bot.send_msg(cid, f"⚠️ Usuario `{uid}` advertido ({warns[uid]}/3)")
    if warns[uid] >= 3:
        _ban_manager.ban_local_user(cid, uid, reason="3 warns", source="warns")
        bot.kick_user(cid, uid)
        _add_web_log("SECURITY", f"Usuario {uid} auto-baneado por acumulación de warns.")
    return jsonify({"ok": True, "count": warns[uid]})


@bp.route("/api/moderation/mute", methods=["POST"])
def web_mute():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    d = request.json
    cid, uid = d["cid"], d["uid"]
    bot = _get_bot_for_chat(cid)
    if not bot:
        return jsonify({"ok": False, "msg": "Bot no encontrado para este grupo"}), 404
    bot.restrict_user(cid, uid, until=int(time.time()) + 1800, can_send=False)
    return jsonify({"ok": True})


@bp.route("/api/moderation/karma", methods=["POST"])
def web_karma():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    d = request.json
    uid, val = d["uid"], d.get("val", 5)
    if uid in _global_user_stats:
        _global_user_stats[uid]["karma"] += val
        return jsonify({"ok": True, "karma": _global_user_stats[uid]["karma"]})
    return jsonify({"ok": False})


@bp.route("/api/moderation/unmute", methods=["POST"])
def web_mod_unmute():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    d = request.json
    cid, target = str(d.get("cid", "")), d.get("target", "")
    muted = _db.get(f"MUTED_{cid}", [])
    if target in muted:
        muted.remove(target)
        _db.set(f"MUTED_{cid}", muted)
    return jsonify({"ok": True})


def _suite():
    return GroupSuite(_db)


@bp.route("/api/moderation/<cid>/suite")
def web_suite_get(cid):
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    return jsonify({"ok": True, **_suite().snapshot(cid)})


@bp.route("/api/moderation/suite/settings", methods=["POST"])
def web_suite_settings():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    body = request.json or {}
    cid = str(body.get("cid", ""))
    if not cid:
        return jsonify({"ok": False, "error": "grupo requerido"}), 400
    return jsonify({"ok": True, "config": _suite().save_config(cid, body.get("config") or {})})


@bp.route("/api/moderation/suite/action", methods=["POST"])
def web_suite_action():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    body = request.json or {}
    cid, action = str(body.get("cid", "")), body.get("action")
    suite = _suite()
    result = None
    if action == "resolve_report":
        if body.get("decision") not in ("reviewed", "dismissed"):
            return jsonify({"ok": False, "error": "decisión no válida"}), 400
        result = suite.resolve_report(cid, body.get("report_id"), body.get("decision"), "master_web")
    elif action == "proposal":
        if body.get("moderation_action") not in ("ban", "mute", "warn"):
            return jsonify({"ok": False, "error": "acción de moderación no válida"}), 400
        result = suite.proposal(cid, body.get("target_id"), body.get("moderation_action"),
                                body.get("reason", ""), "master_web")
    elif action == "vote":
        result = suite.vote(cid, body.get("proposal_id"), "master_web")
    elif action == "role":
        result = suite.set_role(cid, body.get("user_id"), body.get("role"), body.get("expires_at"))
    elif action == "template_save":
        result = suite.save_template(cid, body.get("name") or "Plantilla")
    elif action == "template_apply":
        result = suite.apply_template(cid, body.get("template_id"))
    if not result:
        return jsonify({"ok": False, "error": "acción o elemento no válido"}), 400
    return jsonify({"ok": True, "result": result})


@bp.route("/api/moderation/<cid>/suite/context/<uid>")
def web_suite_context(cid, uid):
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    return jsonify({"ok": True, "context": _suite().user_context(cid, uid)})


@bp.route("/api/moderation/<cid>/suite/summary")
def web_suite_summary(cid):
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    return jsonify({"ok": True, "summary": _suite().summary(cid)})

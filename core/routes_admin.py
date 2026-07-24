import json
import csv
import datetime
import io
import time

from flask import Blueprint, Response, jsonify, request

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
_ban_manager = None
_check_cas_status = None


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
    ban_manager=None,
    check_cas_status=None,
):
    global _check_jwt, _db, _add_audit_log, _get_global_chat_names, _get_proxy_bot
    global _get_global_user_stats, _get_global_msg_log, _get_ia_nativa
    global _get_maintenance_mode, _set_maintenance_mode, _ban_manager, _check_cas_status
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
    _ban_manager = ban_manager
    _check_cas_status = check_cas_status
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


@bp.route("/api/admin/bans")
def web_admin_bans():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    global_bans = _db.get("GLOBAL_BANS", {})
    if not isinstance(global_bans, dict):
        global_bans = {}
    user_ids = [str(uid) for uid in global_bans.get("users", [])]

    # Recuperar la razon mas reciente de cada baneo global desde el historial.
    reasons = {}
    history = _db.get("BAN_HISTORY", [])
    if isinstance(history, list):
        for record in history:
            if not isinstance(record, dict):
                continue
            if record.get("scope") == "global" and record.get("action", "ban") == "ban":
                reason = record.get("reason")
                if reason:
                    reasons[str(record.get("uid", ""))] = reason

    bans = [{"user_id": uid, "reason": reasons.get(uid, "")} for uid in user_ids]
    return jsonify({"ok": True, "bans": bans})


def _registry_stats(records):
    return {
        "active": sum(row.get("status", "active") == "active" for row in records),
        "cas_active": sum(
            row.get("status", "active") == "active"
            and str(row.get("source", "")).lower() in ("cas", "cas_feed", "export.csv")
            for row in records
        ),
        "revoked": sum(row.get("status") == "revoked" for row in records),
        "expired": sum(row.get("status") == "expired" for row in records),
        "pending_review": sum(
            row.get("status", "active") == "active" and not row.get("reviewed", False)
            for row in records
        ),
    }


def _safe_csv(value):
    text = str(value or "")
    return f"'{text}" if text.startswith(("=", "+", "-", "@")) else text


@bp.route("/api/admin/ban-registry", methods=["GET", "POST"])
def web_admin_ban_registry():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    if _ban_manager is None:
        return jsonify({"ok": False, "msg": "Registro no disponible"}), 503
    if request.method == "GET":
        # Migra metadatos antiguos sin hacer llamadas remotas: primero usa el
        # historial y después el export/feed local de CAS ya descargado.
        _ban_manager.enrich_legacy_records(_check_cas_status)
        status = request.args.get("status", "active")
        if status not in ("active", "revoked", "expired", "all"):
            status = "active"
        try:
            limit = int(request.args.get("limit", 500))
        except (TypeError, ValueError):
            limit = 500
        records = _ban_manager.list_ban_records(
            query=request.args.get("q", ""), status=status, limit=limit
        )
        all_records = _ban_manager.list_ban_records(status="all", limit=2000)
        return jsonify({"ok": True, "records": records, "stats": _registry_stats(all_records)})

    body = request.json or {}
    user_id = str(body.get("user_id", "")).strip()
    reason = str(body.get("reason", "")).strip()
    if not user_id.isdigit() or not reason:
        return jsonify({"ok": False, "msg": "Faltan user_id y motivo"}), 400
    severity = body.get("severity", "medium")
    if severity not in ("low", "medium", "high", "critical"):
        return jsonify({"ok": False, "msg": "Gravedad inválida"}), 400
    try:
        expires_in_days = int(body.get("expires_in_days") or 0)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "msg": "Duración inválida"}), 400
    if expires_in_days not in (0, 1, 7, 30, 90, 365):
        return jsonify({"ok": False, "msg": "Duración no permitida"}), 400
    expires_at = (
        datetime.datetime.now() + datetime.timedelta(days=expires_in_days)
    ).isoformat() if expires_in_days else None
    created = _ban_manager.ban_user(
        user_id,
        reason=reason,
        source=body.get("source") or "master_panel",
        reported_by="master",
        evidence=body.get("evidence"),
        groups=body.get("groups"),
        reviewed=bool(body.get("reviewed", True)),
        severity=severity,
        expires_at=expires_at,
    )
    record = _ban_manager.get_ban_record(user_id)
    _add_audit_log(f"Registro global {'creado' if created else 'actualizado'} para {user_id}")
    return jsonify({"ok": True, "created": created, "record": record})


@bp.route("/api/admin/ban-registry/review", methods=["POST"])
def web_admin_ban_registry_review():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    body = request.json or {}
    user_id = str(body.get("user_id", "")).strip()
    record = _ban_manager.review_ban_record(
        user_id, reviewed_by="master", reason=body.get("reason"),
        evidence=body.get("evidence") if "evidence" in body else None,
    ) if _ban_manager else None
    if not record:
        return jsonify({"ok": False, "msg": "Registro no encontrado"}), 404
    _add_audit_log(f"Registro global revisado para {user_id}")
    return jsonify({"ok": True, "record": record})


@bp.route("/api/admin/ban-reports")
def web_admin_ban_reports():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    status = request.args.get("status", "pending")
    if status not in ("pending", "approved", "rejected", "all"):
        status = "pending"
    reports = _ban_manager.list_ban_reports(status=status, limit=500) if _ban_manager else []
    return jsonify({"ok": True, "reports": reports})


@bp.route("/api/admin/ban-reports/resolve", methods=["POST"])
def web_admin_ban_reports_resolve():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    body = request.json or {}
    report_id = str(body.get("report_id", "")).strip()
    decision = body.get("decision")
    if decision not in ("approved", "rejected"):
        return jsonify({"ok": False, "msg": "Decisión inválida"}), 400
    pending = next((
        item for item in (_ban_manager.list_ban_reports(status="pending", limit=2000) if _ban_manager else [])
        if str(item.get("id")) == report_id
    ), None)
    if not pending:
        return jsonify({"ok": False, "msg": "Reporte no encontrado o ya resuelto"}), 404
    if decision == "approved":
        _ban_manager.ban_user(
            pending.get("user_id"), reason=pending.get("reason"),
            source="group_admin_report", reported_by=pending.get("reported_by"),
            evidence=pending.get("evidence"), groups=[pending.get("chat_id")],
            reviewed=True,
        )
    report = _ban_manager.resolve_ban_report(report_id, decision, "master")
    _add_audit_log(
        f"Reporte {report_id} {decision}: usuario {pending.get('user_id')} "
        f"desde el grupo {pending.get('chat_id')}"
    )
    return jsonify({"ok": True, "report": report})


@bp.route("/api/admin/ban-appeals")
def web_admin_ban_appeals():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    status = request.args.get("status", "pending")
    if status not in ("pending", "approved", "rejected", "all"):
        status = "pending"
    appeals = _ban_manager.list_ban_appeals(status=status, limit=500) if _ban_manager else []
    return jsonify({"ok": True, "appeals": appeals})


@bp.route("/api/admin/ban-appeals/resolve", methods=["POST"])
def web_admin_ban_appeals_resolve():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    body = request.json or {}
    appeal_id = str(body.get("appeal_id", "")).strip()
    decision = body.get("decision")
    if decision not in ("approved", "rejected"):
        return jsonify({"ok": False, "msg": "Decisión inválida"}), 400
    pending = next((
        item for item in (_ban_manager.list_ban_appeals(status="pending", limit=2000) if _ban_manager else [])
        if str(item.get("id")) == appeal_id
    ), None)
    if not pending:
        return jsonify({"ok": False, "msg": "Apelación no encontrada o ya resuelta"}), 404
    if decision == "approved":
        _ban_manager.unban_user(pending.get("user_id"))
    appeal = _ban_manager.resolve_ban_appeal(appeal_id, decision, "master")
    _add_audit_log(
        f"Apelación {appeal_id} {decision}: usuario {pending.get('user_id')}"
    )
    return jsonify({"ok": True, "appeal": appeal})


@bp.route("/api/admin/ban-api-keys", methods=["GET", "POST"])
def web_admin_ban_api_keys():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    if not _ban_manager:
        return jsonify({"ok": False, "msg": "Registro no disponible"}), 503
    if request.method == "GET":
        return jsonify({"ok": True, "keys": _ban_manager.list_api_keys()})
    label = str((request.json or {}).get("label", "")).strip()
    key = _ban_manager.create_api_key(label, "master")
    if not key:
        return jsonify({"ok": False, "msg": "Falta la etiqueta"}), 400
    _add_audit_log(f"Clave de consulta comunitaria creada: {label}")
    return jsonify({"ok": True, "api_key": key}), 201


@bp.route("/api/admin/ban-api-keys/revoke", methods=["POST"])
def web_admin_ban_api_keys_revoke():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    key_id = str((request.json or {}).get("key_id", "")).strip()
    if not _ban_manager or not _ban_manager.revoke_api_key(key_id):
        return jsonify({"ok": False, "msg": "Clave no encontrada o ya revocada"}), 404
    _add_audit_log(f"Clave de consulta comunitaria revocada: {key_id}")
    return jsonify({"ok": True, "key_id": key_id})


@bp.route("/api/admin/ban-registry/export")
def web_admin_ban_registry_export():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    records = _ban_manager.list_ban_records(status="all", limit=2000) if _ban_manager else []
    if request.args.get("format", "json").lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(("user_id", "status", "severity", "expires_at", "reason", "source", "reviewed",
                         "reported_by", "groups", "evidence", "created_at", "updated_at"))
        for row in records:
            writer.writerow((
                _safe_csv(row.get("user_id")), _safe_csv(row.get("status")),
                _safe_csv(row.get("severity")), row.get("expires_at"),
                _safe_csv(row.get("reason")), _safe_csv(row.get("source")),
                row.get("reviewed"), _safe_csv(row.get("reported_by")),
                _safe_csv(" | ".join(row.get("groups") or [])),
                _safe_csv(" | ".join(row.get("evidence") or [])),
                row.get("created_at"), row.get("updated_at"),
            ))
        return Response(
            output.getvalue(), mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=community-ban-registry.csv"},
        )
    return Response(
        json.dumps({"exported_at": int(time.time()), "records": records}, ensure_ascii=False, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=community-ban-registry.json"},
    )


@bp.route("/api/admin/unban", methods=["POST"])
def web_admin_unban():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    user_id = str((request.json or {}).get("user_id", "")).strip()
    if not user_id:
        return jsonify({"ok": False, "msg": "Falta user_id"}), 400

    global_bans = _db.get("GLOBAL_BANS", {})
    if not isinstance(global_bans, dict):
        global_bans = {"users": [], "hashes": []}
    global_bans.setdefault("users", [])

    if user_id not in [str(uid) for uid in global_bans["users"]]:
        return jsonify({"ok": False, "msg": "El usuario no esta baneado globalmente"}), 404

    # Usar el BanManager para que el set en memoria quede sincronizado y el
    # enforcer global no vuelva a banear al usuario en el siguiente mensaje.
    if _ban_manager is not None:
        _ban_manager.unban_user(user_id)
    else:
        global_bans["users"] = [uid for uid in global_bans["users"] if str(uid) != user_id]
        _db.set("GLOBAL_BANS", global_bans)
    _add_audit_log(f"Usuario {user_id} desbaneado globalmente desde el panel")
    return jsonify({"ok": True, "user_id": user_id})


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

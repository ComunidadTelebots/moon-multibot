"""
routes_public.py — Endpoints PÚBLICOS (sin JWT) del hub.

Zona pública del panel: estadísticas de canales y obtención de proxy MTProto.
Solo lectura / acciones seguras. Todo lo administrativo sigue en sus blueprints
protegidos por check_jwt.

CORS abierto para que canales.todosobreall.tech (y el propio panel) puedan
consumir la API desde el navegador.
"""

import hmac
import hashlib
import json
import datetime
import os
import time
import secrets
import re
from urllib.parse import parse_qsl

import jwt
from flask import Blueprint, request, jsonify

try:
    import psutil
except ImportError:  # pragma: no cover - la imagen oficial incluye psutil
    psutil = None

from . import image_gen
from spam_risk import SpamRiskEngine
from group_suite import GroupSuite
from community_members import CommunityMembers
from community_engagement import CommunityEngagement
from roadmap_engine import RoadmapEngine
from core.language_map import aggregate_language_map

bp = Blueprint("public", __name__)

_channel_stats = None
_proxy_mgr = None
_master_id = None
_jwt_secret = None
_get_active_bots = None
_db = None
_ban_manager = None
_get_bot_for_chat = None
_check_cas = None
_hub_bot_username = "cintiabot"
_get_global_user_stats = None
_get_global_chat_names = None
_add_audit_log = None
_vt_manager = None
_community_api_usage = {}


def setup(channel_stats, proxy_mgr, master_id=None, jwt_secret=None, get_active_bots=None,
          db=None, ban_manager=None, get_bot_for_chat=None, check_cas=None,
          hub_bot_username="cintiabot", get_global_user_stats=None, get_global_chat_names=None,
          add_audit_log=None, vt_manager=None):
    global _channel_stats, _proxy_mgr, _master_id, _jwt_secret, _get_active_bots
    global _db, _ban_manager, _get_bot_for_chat, _check_cas
    global _hub_bot_username, _get_global_user_stats, _get_global_chat_names, _add_audit_log, _vt_manager
    _check_cas = check_cas
    _channel_stats = channel_stats
    _proxy_mgr = proxy_mgr
    _master_id = master_id
    _jwt_secret = jwt_secret
    _get_active_bots = get_active_bots
    _db = db
    _ban_manager = ban_manager
    _get_bot_for_chat = get_bot_for_chat
    _hub_bot_username = hub_bot_username or "cintiabot"
    _get_global_user_stats = get_global_user_stats
    _get_global_chat_names = get_global_chat_names
    _add_audit_log = add_audit_log
    _vt_manager = vt_manager
    return bp


# Desfase máximo (s) permitido hacia el futuro: un auth_date muy adelantado
# indica reloj manipulado / firma falsificada.
_AUTH_DATE_SKEW = 300


def _hub_bot():
    """La ÚNICA instancia de bot que sirve la Mini App del hub (por username).
    Devuelve None si no está activa → fail-closed (se deniega la validación)."""
    if not _get_active_bots:
        return None
    want = (_hub_bot_username or "").lower()
    for b in _get_active_bots() or []:
        if (getattr(b, "bot_username", "") or "").lower() == want:
            return b
    return None


def _verify_init_data(init_data, max_age=86400):
    """Valida el initData de la Mini App del hub. Endurecido:
      1) auth_date obligatorio: rechaza firmas de más de `max_age` s (24h por
         defecto) o con reloj en el futuro (> _AUTH_DATE_SKEW).
      2) firma SOLO contra el token del bot del hub, no contra cualquier bot.
    Devuelve el dict de usuario si la firma es válida y vigente, o None."""
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception:
        return None
    recv_hash = pairs.pop("hash", None)
    if not recv_hash:
        return None
    # 1) Vigencia (auth_date sí forma parte del data_check_string; solo se saca 'hash').
    try:
        auth_date = int(pairs.get("auth_date", ""))
    except (TypeError, ValueError):
        return None
    now = int(time.time())
    if auth_date <= 0 or now - auth_date > max_age or auth_date - now > _AUTH_DATE_SKEW:
        return None
    # 2) Firma: únicamente el bot del hub (fail-closed si no está activo).
    bot = _hub_bot()
    token = getattr(bot, "token", None) if bot else None
    if not token:
        return None
    data_check = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    calc = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    if hmac.compare_digest(calc, recv_hash):
        try:
            return json.loads(pairs.get("user", "{}"))
        except Exception:
            return {}
    return None


@bp.after_request
def _cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Community-Key, X-Moon-Admin-Key"
    return resp


def _internal_admin_authorized():
    """Autenticacion servidor-a-servidor; el secreto nunca llega al navegador."""
    expected = os.getenv("MOON_ADMIN_API_KEY", "").strip()
    supplied = request.headers.get("X-Moon-Admin-Key", "").strip()
    return bool(expected and supplied and hmac.compare_digest(expected, supplied))


def _safe_list(value):
    return value if isinstance(value, list) else []


@bp.route("/api/internal/admin-overview")
def internal_admin_overview():
    """Resumen real y sin secretos para el panel central de TodoSobreAllTech."""
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    bots = list(_get_active_bots() or []) if _get_active_bots else []
    group_ids = set()
    instances = []
    for bot in bots:
        token = getattr(bot, "token", "")
        chats = {str(chat_id) for chat_id in _safe_list(_db.get(f"CHATS_{token}", [])) if chat_id}
        group_ids.update(chats)
        instances.append({
            "id": str(getattr(bot, "bot_id", "") or getattr(bot, "user_id", "")),
            "username": str(getattr(bot, "bot_username", "") or "Moonbot"),
            "status": "online",
            "groups": len(chats),
        })

    users = (_get_global_user_stats() or {}) if _get_global_user_stats else {}
    now = datetime.datetime.now(datetime.timezone.utc)
    active_24h = 0
    for stats in users.values():
        try:
            seen = datetime.datetime.fromisoformat(str(stats.get("last_seen", "")).replace("Z", "+00:00"))
            if seen.tzinfo is None:
                seen = seen.replace(tzinfo=datetime.timezone.utc)
            active_24h += (now - seen).total_seconds() <= 86400
        except (TypeError, ValueError):
            continue

    audit = _safe_list(_db.get("SECURITY_AUDIT_LOGS", []))[-20:]
    timeline = [{
        "time": row.get("time"),
        "action": row.get("action", "Actividad administrativa"),
    } for row in reversed(audit) if isinstance(row, dict)]

    resource = {"cpu": None, "ram": None, "disk": None}
    if psutil:
        resource = {
            "cpu": psutil.cpu_percent(interval=0.05),
            "ram": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage("C:" if os.name == "nt" else "/").percent,
        }

    pending_sources = {
        "reports": _safe_list(_db.get("REPORTS", [])),
        "appeals": _safe_list(_db.get("BAN_APPEALS", [])),
        "join_requests": _safe_list(_db.get("JOIN_REQUESTS", [])),
    }
    pending = {name: sum(
        not isinstance(item, dict) or item.get("status", "pending") in ("pending", "open", "new")
        for item in values
    ) for name, values in pending_sources.items()}

    names = (_get_global_chat_names() or {}) if _get_global_chat_names else {}
    groups = [{"id": cid, "name": str(names.get(cid) or names.get(str(cid)) or f"Grupo {cid}")[:160]}
              for cid in sorted(group_ids)]
    return jsonify({
        "ok": True,
        "generated_at": now.isoformat(),
        "summary": {
            "instances_online": len(instances),
            "users_observed": len(users),
            "users_active_24h": active_24h,
            "groups": len(group_ids),
        },
        "resources": resource,
        "services": [
            {"name": "Moonbot API", "status": "online"},
            {"name": "Telegram", "status": "online" if instances else "degraded"},
            {"name": "Base de datos", "status": "online" if _db else "offline"},
        ],
        "pending": {**pending, "total": sum(pending.values())},
        "instances": instances,
        "groups": groups,
        "timeline": timeline,
    })


def _known_internal_group(cid):
    for bot in (_get_active_bots() or []) if _get_active_bots else []:
        if str(cid) in {str(item) for item in _safe_list(_db.get(f"CHATS_{getattr(bot, 'token', '')}", []))}:
            return bot
    return None


def _known_internal_group_ids():
    ids = set()
    for bot in (_get_active_bots() or []) if _get_active_bots else []:
        ids.update(str(item) for item in _safe_list(_db.get(f"CHATS_{getattr(bot, 'token', '')}", [])))
    return ids


@bp.route("/api/internal/groups/<cid>", methods=["GET", "POST"])
def internal_group_admin(cid):
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    bot = _known_internal_group(cid)
    if not bot:
        return jsonify({"ok": False, "error": "group_not_found"}), 404
    suite = GroupSuite(_db)
    if request.method == "POST":
        body = request.json or {}
        action = body.get("action")
        if action == "save_config" and isinstance(body.get("config"), dict):
            config = suite.save_config(cid, body["config"])
        elif action == "copy_config":
            source = str(body.get("source_id", ""))
            if not _known_internal_group(source):
                return jsonify({"ok": False, "error": "source_group_not_found"}), 404
            config = suite.save_config(cid, suite.config(source))
        else:
            return jsonify({"ok": False, "error": "invalid_action"}), 400
        return jsonify({"ok": True, "config": config})

    response = bot.api_call("getChatMember", {"chat_id": cid, "user_id": bot.bot_id}, silent=True)
    member = response.get("result", {}) if isinstance(response, dict) and response.get("ok") else {}
    required = {
        "can_manage_chat": "Gestionar el grupo",
        "can_delete_messages": "Eliminar mensajes",
        "can_restrict_members": "Restringir miembros",
        "can_invite_users": "Aprobar usuarios",
        "can_pin_messages": "Fijar mensajes",
    }
    missing = [] if member.get("status") == "creator" else [
        {"permission": key, "label": label} for key, label in required.items() if not member.get(key)
    ]
    history = _safe_list(_db.get(f"CHAT_HIST_{cid}", []))
    return jsonify({
        "ok": True,
        "group": {"id": str(cid), "name": str((_get_global_chat_names() or {}).get(str(cid), f"Grupo {cid}"))[:160]},
        "permissions": {"healthy": not missing, "status": member.get("status", "unknown"), "missing": missing},
        "config": suite.config(cid),
        "activity": {"stored_messages": len(history), "warnings": len(_db.get(f"WARNS_{cid}", {}) or {}),
                     "media_events": len(suite.media_events(cid, 100))},
    })


def _user_view(uid, stats):
    record = _ban_manager.get_ban_record(uid) if _ban_manager else None
    return {
        "id": str(uid),
        "name": str(stats.get("name") or f"Usuario {uid}")[:160],
        "messages": int(stats.get("count", 0) or 0),
        "karma": int(stats.get("karma", 0) or 0),
        "engagement": int(stats.get("engagement", 0) or 0),
        "language": str(stats.get("language_code") or "und")[:16],
        "last_seen": stats.get("last_seen"),
        "notes": str(stats.get("notes") or "")[:1000],
        "banned": bool(record and record.get("status", "active") == "active"),
        "ban": ({key: record.get(key) for key in ("reason", "source", "scope", "status", "created_at", "expires_at")}
                if record else None),
    }


@bp.route("/api/internal/users")
def internal_users():
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    users = (_get_global_user_stats() or {}) if _get_global_user_stats else {}
    query = str(request.args.get("q", "")).strip().lower()[:100]
    rows = [_user_view(uid, stats if isinstance(stats, dict) else {}) for uid, stats in users.items()]
    if query:
        rows = [row for row in rows if query in row["id"].lower() or query in row["name"].lower()]
    rows.sort(key=lambda row: (row["banned"], row["messages"]), reverse=True)
    return jsonify({"ok": True, "total": len(rows), "users": rows[:500],
                    "ban_stats": _ban_manager.get_ban_stats() if _ban_manager else {}})


@bp.route("/api/internal/users/<uid>", methods=["GET", "POST"])
def internal_user_admin(uid):
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    uid = str(uid).strip()
    if not uid.isdigit():
        return jsonify({"ok": False, "error": "invalid_user_id"}), 400
    users = (_get_global_user_stats() or {}) if _get_global_user_stats else {}
    stats = users.get(uid, {}) if isinstance(users.get(uid, {}), dict) else {}
    if request.method == "GET":
        local_groups = []
        for bot in (_get_active_bots() or []) if _get_active_bots else []:
            for cid in _safe_list(_db.get(f"CHATS_{getattr(bot, 'token', '')}", [])):
                if _ban_manager and _ban_manager.is_local_banned(cid, uid):
                    local_groups.append(str(cid))
        appeals = _ban_manager.list_ban_appeals(status="all", limit=100, uid=uid) if _ban_manager else []
        try:
            cas = _check_cas(uid, use_cache=True, local_only=True) if _check_cas else {"ok": False, "source": "disabled"}
        except Exception:
            cas = {"ok": False, "source": "unavailable"}
        return jsonify({"ok": True, "user": _user_view(uid, stats), "local_bans": sorted(set(local_groups)),
                        "appeals": appeals[-20:], "cas": {
                            "available": bool(cas.get("ok")), "banned": bool(cas.get("banned")),
                            "offenses": cas.get("offenses"), "source": cas.get("source"),
                            "description": str(cas.get("description") or "")[:300],
                        }})

    body = request.json or {}
    action = str(body.get("action", ""))
    cid = str(body.get("group_id", ""))
    reason = str(body.get("reason") or "Accion administrativa desde TodoSobreAllTech")[:500]
    telegram_results = []
    if action in ("ban_global", "ban_local"):
        if action == "ban_local" and not _known_internal_group(cid):
            return jsonify({"ok": False, "error": "group_not_found"}), 404
        if action == "ban_global":
            _ban_manager.ban_user(uid, reason=reason, source="todosobrealltech")
            targets = [(bot, group) for bot in (_get_active_bots() or []) for group in _safe_list(_db.get(f"CHATS_{getattr(bot, 'token', '')}", []))]
        else:
            _ban_manager.ban_local_user(cid, uid, reason=reason, source="todosobrealltech")
            targets = [(_known_internal_group(cid), cid)]
        for bot, group in targets:
            result = bot.api_call("banChatMember", {"chat_id": group, "user_id": uid}, silent=True)
            telegram_results.append({"group_id": str(group), "ok": bool(result.get("ok"))})
    elif action in ("unban_global", "unban_local"):
        if action == "unban_local" and not _known_internal_group(cid):
            return jsonify({"ok": False, "error": "group_not_found"}), 404
        if action == "unban_global":
            _ban_manager.unban_user(uid)
            targets = [(bot, group) for bot in (_get_active_bots() or []) for group in _safe_list(_db.get(f"CHATS_{getattr(bot, 'token', '')}", []))]
        else:
            _ban_manager.unban_local_user(cid, uid)
            targets = [(_known_internal_group(cid), cid)]
        for bot, group in targets:
            result = bot.api_call("unbanChatMember", {"chat_id": group, "user_id": uid, "only_if_banned": True}, silent=True)
            telegram_results.append({"group_id": str(group), "ok": bool(result.get("ok"))})
    elif action == "quarantine":
        if not _known_internal_group(cid):
            return jsonify({"ok": False, "error": "group_not_found"}), 404
        rows = _db.get(f"QUARANTINE_{cid}", {})
        rows = rows if isinstance(rows, dict) else {}
        rows[uid] = {"joined_at": int(time.time()), "messages": 0, "name": stats.get("name", "")}
        _db.set(f"QUARANTINE_{cid}", rows)
    elif action == "save_note":
        stats["notes"] = str(body.get("note") or "")[:1000]
        users[uid] = stats
    elif action == "resolve_appeal":
        decision = str(body.get("decision", ""))
        if decision not in ("approved", "rejected"):
            return jsonify({"ok": False, "error": "invalid_decision"}), 400
        appeal = _ban_manager.resolve_ban_appeal(body.get("appeal_id"), decision, "todosobrealltech")
        if not appeal:
            return jsonify({"ok": False, "error": "appeal_not_found"}), 404
    else:
        return jsonify({"ok": False, "error": "invalid_action"}), 400
    if _add_audit_log:
        _add_audit_log(f"TodoSobreAllTech: {action} para usuario {uid}" + (f" en {cid}" if cid else ""))
    return jsonify({"ok": True, "user": _user_view(uid, stats), "telegram_results": telegram_results})


def _security_snapshot():
    threats = _safe_list(_db.get("THREAT_ANALYSIS_HISTORY", []))
    recent = [row for row in threats[-100:] if isinstance(row, dict)]
    records = _ban_manager.list_ban_records(status="all", limit=2000) if _ban_manager else []
    sources = {}
    for row in records:
        source = str(row.get("source") or "unknown").lower()
        sources[source] = sources.get(source, 0) + 1
    raids, media_events = [], 0
    for bot in (_get_active_bots() or []) if _get_active_bots else []:
        for cid in _safe_list(_db.get(f"CHATS_{getattr(bot, 'token', '')}", [])):
            state = GroupSuite(_db).raid_state(cid)
            if state.get("active"):
                raids.append({"group_id": str(cid), **state})
            media_events += len(GroupSuite(_db).media_events(cid, 100))
    return {
        "threats_total": len(threats),
        "threats_high": sum(row.get("risk") == "high" or int(row.get("malicious", 0) or 0) > 0 for row in threats if isinstance(row, dict)),
        "media_events": media_events,
        "active_raids": raids,
        "ban_sources": sources,
        "shield_enabled": bool(_db.get("NEURAL_SHIELD", True)),
        "history": list(reversed(recent)),
    }


@bp.route("/api/internal/security", methods=["GET", "POST"])
def internal_security():
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    if request.method == "GET":
        return jsonify({"ok": True, **_security_snapshot()})
    body = request.json or {}
    action = str(body.get("action", ""))
    if action == "analyze":
        kind = str(body.get("kind", "")).lower()
        value = str(body.get("value", "")).strip()
        if kind not in ("url", "domain", "hash") or not value or len(value) > 2048:
            return jsonify({"ok": False, "error": "invalid_analysis"}), 400
        if not _vt_manager:
            return jsonify({"ok": False, "error": "virustotal_unavailable"}), 503
        result = _vt_manager.analyze(kind, value)
        if result.get("ok"):
            rows = _safe_list(_db.get("THREAT_ANALYSIS_HISTORY", []))
            rows.append({"time": int(time.time()), "source": "virustotal", "kind": kind,
                         "value": value[:500], "risk": result.get("risk", "pending"),
                         "malicious": result.get("malicious", 0), "suspicious": result.get("suspicious", 0)})
            _db.set("THREAT_ANALYSIS_HISTORY", rows[-300:])
        if _add_audit_log:
            _add_audit_log(f"TodoSobreAllTech: analisis VirusTotal de tipo {kind}")
        return jsonify(result), 200 if result.get("ok") else 400
    if action == "secret_scan":
        text = str(body.get("text", ""))[:20000]
        patterns = {
            "telegram_bot_token": r"\b\d{6,12}:[A-Za-z0-9_-]{30,}\b",
            "private_key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            "generic_api_key": r"(?i)\b(?:api[_-]?key|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}",
            "jwt": r"\beyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b",
        }
        findings = [{"type": name, "count": len(re.findall(pattern, text))}
                    for name, pattern in patterns.items() if re.search(pattern, text)]
        return jsonify({"ok": True, "safe": not findings, "findings": findings,
                        "note": "El texto no se almacena y los valores detectados no se devuelven."})
    return jsonify({"ok": False, "error": "invalid_action"}), 400


@bp.route("/api/internal/security/evidence")
def internal_security_evidence():
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    snapshot = _security_snapshot()
    payload = {"generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "summary": {key: value for key, value in snapshot.items() if key != "history"},
               "events": snapshot["history"]}
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    key = os.getenv("MOON_ADMIN_API_KEY", "").encode()
    signature = hmac.new(key, canonical.encode(), hashlib.sha256).hexdigest()
    return jsonify({"ok": True, "algorithm": "HMAC-SHA256", "payload": payload, "signature": signature})


def _editorial_templates():
    rows = _db.get("EDITORIAL_TEMPLATES", [])
    return rows if isinstance(rows, list) else []


@bp.route("/api/internal/editorial", methods=["GET", "POST"])
def internal_editorial():
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    engine = RoadmapEngine(_db)
    if request.method == "GET":
        content = engine.snapshot().get("content", {})
        return jsonify({"ok": True, **content, "templates": list(reversed(_editorial_templates()))[:100],
                        "series": list(reversed(_safe_list(_db.get("H202_EDITORIAL_SERIES", []))))[:100],
                        "announcements": list(reversed(_safe_list(_db.get("H202_PUBLIC_ANNOUNCEMENTS", []))))[:100]})
    body = request.json or {}
    action = str(body.get("action", ""))
    title = str(body.get("title") or "")[:300]
    content = str(body.get("body") or "")[:12000]
    known = _known_internal_group_ids()
    targets = [str(item) for item in body.get("targets", []) if str(item) in known]
    try:
        if action == "preview":
            result = {"title": title, "rendered": engine.render_template(content, body.get("variables") or {}),
                      "characters": len(content), "targets": targets}
        elif action == "publish_now":
            if not content or not targets:
                return jsonify({"ok": False, "error": "content_and_targets_required"}), 400
            item = engine.content_create("telegram_post", title, content, "todosobrealltech")
            deliveries = []
            for cid in targets:
                bot = _known_internal_group(cid)
                response = bot.send_rich_message(cid, markdown=content, fallback_text=content)
                deliveries.append({"group_id": cid, "ok": bool(response.get("ok"))})
            engine.editorial_decision(item["id"], "todosobrealltech", "approved", "PublicaciÃ³n inmediata")
            result = {"item": item, "deliveries": deliveries}
        elif action == "schedule":
            if not content or not targets or not body.get("execute_at"):
                return jsonify({"ok": False, "error": "content_targets_and_date_required"}), 400
            recurrence = body.get("recurrence") or None
            if recurrence not in (None, "daily", "weekly", "monthly"):
                return jsonify({"ok": False, "error": "invalid_recurrence"}), 400
            when = datetime.datetime.fromisoformat(str(body["execute_at"]).replace("Z", "+00:00"))
            if when.tzinfo is not None:
                when = when.astimezone().replace(tzinfo=None)
            expires_at = body.get("expires_at")
            if expires_at:
                expiry = datetime.datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
                expires_at = (expiry.astimezone().replace(tzinfo=None) if expiry.tzinfo else expiry).isoformat()
            item = engine.content_create("telegram_post", title, content, "todosobrealltech")
            schedule = engine.content_schedule(item["id"], targets, when.isoformat(), recurrence, expires_at)
            result = {"item": item, "schedule": schedule}
        elif action == "template_save":
            if not title or not content:
                return jsonify({"ok": False, "error": "title_and_body_required"}), 400
            rows = _editorial_templates()
            template = {"id": secrets.token_hex(6), "name": title, "body": content,
                        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
            rows.append(template); _db.set("EDITORIAL_TEMPLATES", rows[-200:]); result = template
        elif action == "headline_compare":
            result = engine.compare_headlines(body.get("headlines") or [])
        elif action == "series":
            result = engine.editorial_series(body.get("operation", "create"), body.get("series_id"), title,
                                             body.get("description", ""), body.get("content_id"), body.get("position"))
        elif action == "announcement":
            result = engine.public_announcement_version(body.get("operation", "publish"), body.get("announcement_id"),
                                                        title, content, body.get("correction_note", ""), "todosobrealltech")
        else:
            return jsonify({"ok": False, "error": "invalid_action"}), 400
    except (TypeError, ValueError) as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    if _add_audit_log:
        _add_audit_log(f"TodoSobreAllTech editorial: {action}")
    return jsonify({"ok": True, "result": result})


def _community_api_auth():
    raw_key = request.headers.get("X-Community-Key", "")
    token = _ban_manager.authenticate_api_key(raw_key) if _ban_manager else None
    if not token:
        return None, (jsonify({"ok": False, "error": "clave inválida"}), 401)
    now_minute = int(time.time() // 60)
    bucket = f"{token.get('id')}:{now_minute}"
    # Mantener únicamente los contadores del minuto actual.
    if len(_community_api_usage) > 500:
        _community_api_usage.clear()
    used = int(_community_api_usage.get(bucket, 0)) + 1
    _community_api_usage[bucket] = used
    if used > 120:
        response = jsonify({"ok": False, "error": "límite de peticiones alcanzado"})
        response.headers["Retry-After"] = str(60 - int(time.time()) % 60)
        return None, (response, 429)
    return token, None


@bp.route("/api/community/v1/check", methods=["POST", "OPTIONS"])
def community_registry_check():
    """Consulta servidor-a-servidor; nunca expone evidencias, autores ni notas."""
    if request.method == "OPTIONS":
        return ("", 204)
    _, err = _community_api_auth()
    if err:
        return err
    body = request.json or {}
    raw_ids = body.get("user_ids")
    if not isinstance(raw_ids, list) or not raw_ids or len(raw_ids) > 100:
        return jsonify({"ok": False, "error": "user_ids debe contener entre 1 y 100 IDs"}), 400
    user_ids = []
    for value in raw_ids:
        uid = str(value).strip()
        if not uid.isdigit():
            return jsonify({"ok": False, "error": "todos los IDs deben ser numéricos"}), 400
        if uid not in user_ids:
            user_ids.append(uid)
    results = []
    for uid in user_ids:
        record = _ban_manager.get_ban_record(uid)
        active = bool(record and record.get("status", "active") == "active")
        results.append({
            "user_id": uid,
            "listed": active,
            "source": record.get("source") if active else None,
            "severity": record.get("severity", "medium") if active else None,
            "expires_at": record.get("expires_at") if active else None,
            "updated_at": record.get("updated_at") if active else None,
        })
    return jsonify({"ok": True, "count": len(results), "results": results})


# ─────────────────────────── Auth Mini App (Telegram) ──────────────────────────

@bp.route("/api/public/tg_auth", methods=["POST", "OPTIONS"])
def tg_auth():
    """Valida el initData de la Mini App y dice si el usuario es el master.
    Si lo es, emite un JWT válido para el panel admin (auto-login)."""
    if request.method == "OPTIONS":
        return ("", 204)
    init_data = (request.json or {}).get("initData", "")
    user = _verify_init_data(init_data)
    if user is None:
        return jsonify({"ok": False, "error": "initData inválido"}), 401
    is_master = _master_id is not None and str(user.get("id")) == str(_master_id)
    resp = {"ok": True, "is_master": is_master, "user": {
        "id": user.get("id"), "first_name": user.get("first_name"), "username": user.get("username"),
    }}
    if is_master and _jwt_secret:
        resp["token"] = jwt.encode(
            {"exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
            _jwt_secret, algorithm="HS256",
        )
    return jsonify(resp)


def _is_master(user):
    return _master_id is not None and str(user.get("id")) == str(_master_id)


@bp.route("/api/public/admin/channels", methods=["POST", "OPTIONS"])
def admin_all_channels():
    """TODOS los canales/grupos donde está el bot. Solo el dueño del bot (master)."""
    if request.method == "OPTIONS":
        return ("", 204)
    user = _verify_init_data((request.json or {}).get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData inválido"}), 401
    if not _is_master(user):
        return jsonify({"ok": False, "error": "solo el dueño del bot"}), 403
    try:
        return jsonify({"ok": True, "channels": _channel_stats.get_all_channels()})
    except Exception as error:
        return jsonify({"ok": False, "error": f"PocketBase no disponible: {error}"}), 503


@bp.route("/api/public/admin/set_listed", methods=["POST", "OPTIONS"])
def admin_set_listed():
    """Publicar/ocultar un canal en el directorio público. Master o dueño del chat."""
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData inválido"}), 401
    chat_id = body.get("chat_id")
    listed = bool(body.get("listed"))
    if chat_id is None:
        return jsonify({"ok": False, "error": "falta chat_id"}), 400
    allowed = _is_master(user) or _channel_stats.is_user_admin_of(user.get("id"), chat_id)
    if not allowed:
        return jsonify({"ok": False, "error": "sin permiso sobre ese canal"}), 403
    _channel_stats.set_listed(chat_id, listed)
    return jsonify({"ok": True, "chat_id": chat_id, "listed": listed})


# ─────────────────────── Gestión de grupo (admin/creador) ──────────────────────

def _group_auth(body):
    """Devuelve (user, chat_id) si el usuario puede gestionar ese chat, o (None, resp_error)."""
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return None, (jsonify({"ok": False, "error": "initData inválido"}), 401)
    chat_id = body.get("chat_id")
    if chat_id is None:
        return None, (jsonify({"ok": False, "error": "falta chat_id"}), 400)
    if not (_is_master(user) or _channel_stats.is_user_admin_of(user.get("id"), chat_id)):
        return None, (jsonify({"ok": False, "error": "sin permiso sobre ese chat"}), 403)
    return (user, chat_id), None


_SETTING_KEYS = {"auto_mod", "welcome", "ia_learning", "security_shield"}


def _banned_hit(chat_id, text):
    """Devuelve la primera palabra prohibida del chat que aparece en `text`, o None."""
    bw = _db.get(f"BADWORDS_{chat_id}", {}) if _db else {}
    words = bw.get("words", []) if isinstance(bw, dict) else []
    if not words or not text:
        return None
    low = text.lower()
    return next((w for w in words if w and w.lower() in low), None)


@bp.route("/api/public/group/get", methods=["POST", "OPTIONS"])
def group_get():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    user, chat_id = res
    meta = _channel_stats.get_channel_meta(chat_id) or {}
    config = _db.get(f"CONFIG_{chat_id}", {"auto_mod": True, "welcome": False, "ia_learning": False, "security_shield": True})
    warns = _db.get(f"WARNS_{chat_id}", {})
    bans = _ban_manager.get_local_bans(chat_id).get("users", []) if _ban_manager else []
    sched = [{"id": s["id"], "text": s.get("text"), "send_at": s.get("send_at")}
             for s in _channel_stats.list_scheduled(chat_id)]
    bw = _db.get(f"BADWORDS_{chat_id}", {"words": [], "action": "delete"})
    if not isinstance(bw, dict):
        bw = {"words": [], "action": "delete"}
    return jsonify({"ok": True, "meta": meta, "role": ("creator" if _is_master(user) else None),
                    "config": {k: bool(config.get(k)) for k in _SETTING_KEYS},
                    "notes": _db.get(f"NOTES_{chat_id}", ""),
                    "warns": [{"user_id": k, "count": v} for k, v in warns.items()],
                    "bans": bans, "scheduled": sched,
                    "badwords": {"words": bw.get("words", []), "action": bw.get("action", "delete")}})


@bp.route("/api/public/group/unban", methods=["POST", "OPTIONS"])
def group_unban():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    uid = body.get("user_id")
    bot = _get_bot_for_chat(chat_id) if _get_bot_for_chat else None
    if bot:
        bot.api_call("unbanChatMember", {"chat_id": chat_id, "user_id": uid, "only_if_banned": True})
    key = f"BANS_{chat_id}"
    data = _db.get(key, {"users": []})
    data["users"] = [u for u in data.get("users", []) if str(u) != str(uid)]
    _db.set(key, data)
    return jsonify({"ok": True})


@bp.route("/api/public/group/ban-report", methods=["POST", "OPTIONS"])
def group_ban_report():
    """Propone un usuario al registro global; nunca aplica el ban automáticamente."""
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    user, chat_id = res
    user_id = str(body.get("user_id", "")).strip()
    reason = str(body.get("reason", "")).strip()
    if not user_id.isdigit() or not reason:
        return jsonify({"ok": False, "error": "faltan usuario y motivo"}), 400
    if not _ban_manager:
        return jsonify({"ok": False, "error": "registro no disponible"}), 503
    duplicate = next((
        report for report in _ban_manager.list_ban_reports(status="pending", limit=2000)
        if str(report.get("user_id")) == user_id and str(report.get("chat_id")) == str(chat_id)
    ), None)
    if duplicate:
        return jsonify({"ok": False, "error": "ya existe un reporte pendiente para este usuario"}), 409
    report = _ban_manager.create_ban_report(
        user_id, reason, user.get("id"), chat_id, evidence=body.get("evidence")
    )
    return jsonify({"ok": True, "report": report}), 201


@bp.route("/api/public/group/ban-reports", methods=["POST", "OPTIONS"])
def group_ban_reports():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    reports = [
        report for report in (_ban_manager.list_ban_reports(status="all", limit=2000) if _ban_manager else [])
        if str(report.get("chat_id")) == str(chat_id)
    ][:100]
    return jsonify({"ok": True, "reports": reports})


@bp.route("/api/public/group/spam/get", methods=["POST", "OPTIONS"])
def group_spam_get():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    engine = SpamRiskEngine(_db)
    events = _db.get(f"SPAMEVENTS_{chat_id}", [])
    if not isinstance(events, list):
        events = []
    visible = list(reversed(events[-50:]))
    return jsonify({
        "ok": True,
        "config": engine.config(chat_id),
        "events": visible,
        "stats": {
            "detected": len(events),
            "deleted": sum(item.get("action") == "deleted" for item in events if isinstance(item, dict)),
            "quarantined": sum(item.get("action") == "quarantined" for item in events if isinstance(item, dict)),
            "average_score": round(
                sum(int(item.get("score", 0)) for item in events if isinstance(item, dict)) / len(events), 1
            ) if events else 0,
            "spam_samples": len(_db.get(f"SPAM_SAMPLES_{chat_id}", [])),
            "ham_samples": len(_db.get(f"HAM_SAMPLES_{chat_id}", [])),
        },
    })


@bp.route("/api/public/group/spam/settings", methods=["POST", "OPTIONS"])
def group_spam_settings():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    mode = body.get("mode", "observe")
    if mode not in ("observe", "delete"):
        return jsonify({"ok": False, "error": "modo inválido"}), 400
    try:
        watch_score = max(20, min(int(body.get("watch_score", 40)), 80))
        delete_score = max(50, min(int(body.get("delete_score", 75)), 100))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "umbrales inválidos"}), 400
    if delete_score <= watch_score:
        return jsonify({"ok": False, "error": "el umbral de borrado debe ser mayor"}), 400
    terms = [
        str(term).strip().lower()[:100] for term in (body.get("terms") or [])
        if str(term).strip()
    ][:100]
    config = {
        "enabled": bool(body.get("enabled", True)),
        "mode": mode,
        "watch_score": watch_score,
        "delete_score": delete_score,
        "terms": terms or SpamRiskEngine.DEFAULT_TERMS,
    }
    _db.set(f"SPAMCFG_{chat_id}", config)
    return jsonify({"ok": True, "config": config})


@bp.route("/api/public/group/spam/feedback", methods=["POST", "OPTIONS"])
def group_spam_feedback():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    event_id = str(body.get("event_id", ""))
    verdict = body.get("verdict")
    if verdict not in ("spam", "ham"):
        return jsonify({"ok": False, "error": "veredicto inválido"}), 400
    events = _db.get(f"SPAMEVENTS_{chat_id}", [])
    event = next((
        item for item in reversed(events) if isinstance(item, dict)
        and str(item.get("created_at")) == event_id
    ), None)
    if not event or not event.get("text"):
        return jsonify({"ok": False, "error": "detección no encontrada"}), 404
    if event.get("feedback"):
        return jsonify({"ok": False, "error": "esta detección ya fue revisada"}), 409
    key = f"{'SPAM' if verdict == 'spam' else 'HAM'}_SAMPLES_{chat_id}"
    samples = _db.get(key, [])
    if not isinstance(samples, list):
        samples = []
    text = str(event["text"])[:500]
    if text not in samples:
        samples.append(text)
        _db.set(key, samples[-200:])
    event["feedback"] = verdict
    _db.set(f"SPAMEVENTS_{chat_id}", events[-200:])
    configs = _db.get("IA_FEEDER_CONFIG", {})
    if not isinstance(configs, dict):
        configs = {}
    affected_sources = set()
    for reason in event.get("reasons", []):
        if not isinstance(reason, dict) or reason.get("signal") not in ("spam_sample", "ham_sample"):
            continue
        expected = "spam" if reason.get("signal") == "spam_sample" else "ham"
        for source in reason.get("sources") or []:
            source = str(source)
            current = configs.get(source)
            if not isinstance(current, dict):
                continue
            field = "confirmed_hits" if verdict == expected else "false_positives"
            current[field] = int(current.get(field, 0)) + 1
            reviewed = int(current.get("confirmed_hits", 0)) + int(current.get("false_positives", 0))
            current["reviewed"] = reviewed
            current["precision"] = round(int(current.get("confirmed_hits", 0)) * 100 / reviewed, 1)
            current["last_review_at"] = datetime.datetime.now().isoformat()
            configs[source] = current
            affected_sources.add(source)
    if affected_sources:
        _db.set("IA_FEEDER_CONFIG", configs)
    return jsonify({"ok": True, "verdict": verdict, "samples": len(samples),
                    "sources_updated": len(affected_sources)})


def _group_suite():
    return GroupSuite(_db)


@bp.route("/api/public/group/bot-permissions", methods=["POST", "OPTIONS"])
def group_bot_permissions():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    bot = _get_bot_for_chat(chat_id)
    if not bot:
        return jsonify({"ok": False, "error": "bot no disponible"}), 503
    response = bot.api_call("getChatMember", {
        "chat_id": chat_id, "user_id": bot.bot_id,
    }, silent=True)
    if not isinstance(response, dict) or not response.get("ok"):
        return jsonify({"ok": False, "error": response.get("description", "no se pudieron consultar los permisos") if isinstance(response, dict) else "sin respuesta"}), 502
    member = response.get("result") or {}
    status = member.get("status", "left")
    creator = status == "creator"
    chat_response = bot.api_call("getChat", {"chat_id": chat_id}, silent=True)
    chat_type = ((chat_response.get("result") or {}).get("type")
                 if isinstance(chat_response, dict) and chat_response.get("ok") else "supergroup")
    required = ({
        "can_post_messages": "Publicar mensajes",
        "can_edit_messages": "Editar mensajes",
        "can_delete_messages": "Eliminar mensajes",
        "can_invite_users": "Invitar miembros",
    } if chat_type == "channel" else {
        "can_manage_chat": "Gestionar el grupo",
        "can_delete_messages": "Eliminar mensajes",
        "can_restrict_members": "Restringir y banear miembros",
        "can_invite_users": "Invitar y aprobar miembros",
        "can_pin_messages": "Fijar mensajes",
    })
    missing = [] if creator else [
        {"permission": key, "label": label}
        for key, label in required.items() if not member.get(key, False)
    ]
    if status not in ("administrator", "creator"):
        missing.insert(0, {"permission": "administrator", "label": "Añadir el bot como administrador"})
    return jsonify({
        "ok": True,
        "healthy": not missing,
        "status": status,
        "chat_type": chat_type,
        "missing": missing,
        "bot_username": getattr(bot, "bot_username", "MoonBot"),
        "instructions": [
            "Abre el grupo en Telegram.",
            "Toca el nombre del grupo y entra en Administradores.",
            f"Selecciona @{getattr(bot, 'bot_username', 'MoonBot')} o añádelo como administrador.",
            "Activa los permisos indicados y guarda los cambios.",
            "Vuelve a esta pantalla y pulsa Comprobar de nuevo.",
        ],
        "checked_at": datetime.datetime.now().isoformat(),
    })


@bp.route("/api/public/group/suite/get", methods=["POST", "OPTIONS"])
def group_suite_get():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    return jsonify({"ok": True, **_group_suite().snapshot(chat_id)})


@bp.route("/api/public/group/suite/settings", methods=["POST", "OPTIONS"])
def group_suite_settings():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    config = _group_suite().save_config(chat_id, body.get("config") or {})
    return jsonify({"ok": True, "config": config})


@bp.route("/api/public/group/suite/report", methods=["POST", "OPTIONS"])
def group_suite_report():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    user, chat_id = res
    target = str(body.get("target_id", "")).strip()
    if not target.isdigit():
        return jsonify({"ok": False, "error": "usuario inválido"}), 400
    report = _group_suite().create_report(
        chat_id, user.get("id"), target, body.get("message_id"), body.get("reason")
    )
    return jsonify({"ok": True, "report": report}), 201


@bp.route("/api/public/group/suite/report/resolve", methods=["POST", "OPTIONS"])
def group_suite_report_resolve():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    user, chat_id = res
    decision = body.get("decision")
    if decision not in ("reviewed", "dismissed"):
        return jsonify({"ok": False, "error": "decisión inválida"}), 400
    report = _group_suite().resolve_report(chat_id, body.get("report_id"), decision, user.get("id"))
    if not report:
        return jsonify({"ok": False, "error": "reporte no encontrado"}), 404
    return jsonify({"ok": True, "report": report})


@bp.route("/api/public/group/suite/consensus", methods=["POST", "OPTIONS"])
def group_suite_consensus():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    user, chat_id = res
    action = body.get("action")
    target = str(body.get("target_id", "")).strip()
    if action not in ("ban", "mute", "warn") or not target.isdigit():
        return jsonify({"ok": False, "error": "propuesta inválida"}), 400
    proposal = _group_suite().proposal(
        chat_id, target, action, body.get("reason", ""), user.get("id")
    )
    return jsonify({"ok": True, "proposal": proposal}), 201


@bp.route("/api/public/group/suite/consensus/vote", methods=["POST", "OPTIONS"])
def group_suite_consensus_vote():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    user, chat_id = res
    proposal = _group_suite().vote(chat_id, body.get("proposal_id"), user.get("id"))
    if not proposal:
        return jsonify({"ok": False, "error": "propuesta no encontrada"}), 404
    executed = False
    if proposal.get("status") == "approved" and not proposal.get("executed_at"):
        target, action = proposal.get("target_id"), proposal.get("action")
        bot = _get_bot_for_chat(chat_id) if _get_bot_for_chat else None
        if action == "ban":
            _ban_manager.ban_local_user(chat_id, target, reason=proposal.get("reason"), source="admin_consensus")
            if bot:
                bot.api_call("banChatMember", {"chat_id": chat_id, "user_id": target}, silent=True)
        elif action == "mute" and bot:
            bot.restrict_user(chat_id, target, until=int(time.time()) + 3600)
        elif action == "warn":
            warns = _db.get(f"WARNS_{chat_id}", {})
            warns[str(target)] = int(warns.get(str(target), 0)) + 1
            _db.set(f"WARNS_{chat_id}", warns)
        proposal["executed_at"] = datetime.datetime.now().isoformat()
        rows = _db.get(f"CONSENSUS_{chat_id}", [])
        for row in rows:
            if row.get("id") == proposal.get("id"):
                row.update(proposal)
        _db.set(f"CONSENSUS_{chat_id}", rows[-200:])
        executed = True
    return jsonify({"ok": True, "proposal": proposal, "executed": executed})


@bp.route("/api/public/group/suite/role", methods=["POST", "OPTIONS"])
def group_suite_role():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    role = _group_suite().set_role(
        chat_id, body.get("user_id"), body.get("role"), body.get("expires_at")
    )
    if not role:
        return jsonify({"ok": False, "error": "rol inválido"}), 400
    return jsonify({"ok": True, "role": role})


@bp.route("/api/public/group/suite/context", methods=["POST", "OPTIONS"])
def group_suite_context():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    return jsonify({"ok": True, "context": _group_suite().user_context(chat_id, body.get("user_id"))})


@bp.route("/api/public/group/suite/summary", methods=["POST", "OPTIONS"])
def group_suite_summary():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    return jsonify({"ok": True, "summary": _group_suite().summary(chat_id)})


@bp.route("/api/public/group/suite/simulate", methods=["POST", "OPTIONS"])
def group_suite_simulate():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    return jsonify({"ok": True, "simulation": _group_suite().simulate_message(chat_id, body.get("text", ""))})


@bp.route("/api/public/group/suite/sanctions/review", methods=["POST", "OPTIONS"])
def group_suite_sanctions_review():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    return jsonify({"ok": True, **_ban_manager.review_local_expirations(chat_id)})


@bp.route("/api/public/group/suite/sanctions/temporary-ban", methods=["POST", "OPTIONS"])
def group_suite_temporary_ban():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    uid = str(body.get("user_id", "")).strip()
    hours = _bounded_int(body.get("hours"), 24, 1, 720)
    if not uid.isdigit():
        return jsonify({"ok": False, "error": "ID de usuario inválido"}), 400
    expires = datetime.datetime.now() + datetime.timedelta(hours=hours)
    _ban_manager.ban_local_user(chat_id, uid, body.get("reason") or "Sanción temporal",
                                "group_admin", expires.isoformat())
    bot = _get_bot_for_chat(chat_id) if _get_bot_for_chat else None
    if bot:
        bot.api_call("banChatMember", {"chat_id": chat_id, "user_id": uid,
                                       "until_date": int(expires.timestamp())}, silent=True)
    return jsonify({"ok": True, "user_id": uid, "expires_at": expires.isoformat()})


@bp.route("/api/public/group/suite/template", methods=["POST", "OPTIONS"])
def group_suite_template():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    action = body.get("action")
    if action == "save":
        template = _group_suite().save_template(chat_id, body.get("name") or "Plantilla")
    elif action == "apply":
        template = _group_suite().apply_template(chat_id, body.get("template_id"))
    else:
        return jsonify({"ok": False, "error": "acción inválida"}), 400
    if not template:
        return jsonify({"ok": False, "error": "plantilla no encontrada"}), 404
    return jsonify({"ok": True, "template": template})


@bp.route("/api/public/group/unwarn", methods=["POST", "OPTIONS"])
def group_unwarn():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    warns = _db.get(f"WARNS_{chat_id}", {})
    warns.pop(str(body.get("user_id")), None)
    _db.set(f"WARNS_{chat_id}", warns)
    return jsonify({"ok": True})


@bp.route("/api/public/group/settings", methods=["POST", "OPTIONS"])
def group_settings():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    key = body.get("key")
    if key not in _SETTING_KEYS:
        return jsonify({"ok": False, "error": "ajuste no permitido"}), 400
    config = _db.get(f"CONFIG_{chat_id}", {})
    config[key] = bool(body.get("value"))
    _db.set(f"CONFIG_{chat_id}", config)
    return jsonify({"ok": True, "config": {k: bool(config.get(k)) for k in _SETTING_KEYS}})


@bp.route("/api/public/group/notes", methods=["POST", "OPTIONS"])
def group_notes():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    _db.set(f"NOTES_{chat_id}", str(body.get("notes", ""))[:2000])
    return jsonify({"ok": True})


@bp.route("/api/public/group/send", methods=["POST", "OPTIONS"])
def group_send():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    text = (body.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "mensaje vacío"}), 400
    bot = _get_bot_for_chat(chat_id) if _get_bot_for_chat else None
    if not bot:
        return jsonify({"ok": False, "error": "sin bot para este chat"}), 503
    r = bot.send_msg(chat_id, text)
    return jsonify({"ok": bool(r.get("ok")) if isinstance(r, dict) else True})


@bp.route("/api/public/group/schedule", methods=["POST", "OPTIONS"])
def group_schedule():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    user, chat_id = res
    text = (body.get("text") or "").strip()
    send_at = (body.get("send_at") or "").strip()  # "YYYY-MM-DD HH:MM:SS" UTC
    if not text or not send_at:
        return jsonify({"ok": False, "error": "faltan texto o fecha"}), 400
    tok = _channel_stats.get_channel_bot_token(chat_id)
    rec = _channel_stats.schedule_message(chat_id, text, send_at, created_by=user.get("id"), bot_token=tok)
    return jsonify({"ok": True, "id": rec.get("id"), "send_at": send_at})


@bp.route("/api/public/group/badwords", methods=["POST", "OPTIONS"])
def group_badwords():
    """Guarda la lista de palabras prohibidas y la acción (delete|warn|ban)."""
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    words = body.get("words") or []
    words = [str(w).strip() for w in words if str(w).strip()][:200]
    action = body.get("action", "delete")
    if action not in ("delete", "warn", "ban"):
        action = "delete"
    _db.set(f"BADWORDS_{chat_id}", {"words": words, "action": action})
    return jsonify({"ok": True, "words": words, "action": action})


@bp.route("/api/public/group/sendphoto", methods=["POST", "OPTIONS"])
def group_sendphoto():
    """Envía una imagen (por URL) al grupo. Usado por el generador de imágenes."""
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    photo = (body.get("photo_url") or "").strip()
    if not photo:
        return jsonify({"ok": False, "error": "falta la imagen"}), 400
    bot = _get_bot_for_chat(chat_id) if _get_bot_for_chat else None
    if not bot:
        return jsonify({"ok": False, "error": "sin bot para este chat"}), 503
    caption = (body.get("caption") or "")[:1024]
    # Descarga la imagen (con UA válido) y la sube a Telegram como archivo,
    # para no depender de que Telegram pueda con la URL del generador.
    data = image_gen.fetch_bytes(photo)
    if data:
        import requests
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{bot.token}/sendPhoto",
                data={"chat_id": str(chat_id), "caption": caption},
                files={"photo": ("imagen.jpg", data)}, timeout=45,
            )
            return jsonify({"ok": bool(resp.json().get("ok"))})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)[:120]}), 502
    # Fallback: pasar la URL directamente a Telegram
    r = bot.api_call("sendPhoto", {"chat_id": chat_id, "photo": photo, "caption": caption})
    return jsonify({"ok": bool(r.get("ok")) if isinstance(r, dict) else True})


@bp.route("/api/public/image/generate", methods=["POST", "OPTIONS"])
def image_generate():
    """Genera imágenes a partir de una descripción (varias variantes para elegir)."""
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user, err = _auth_user(body)
    if err:
        return err
    prompt = (body.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"ok": False, "error": "describe la imagen"}), 400
    return jsonify({"ok": True, "prompt": prompt, "images": image_gen.generate_variants(prompt, n=4)})


@bp.route("/api/public/group/cas", methods=["POST", "OPTIONS"])
def group_cas():
    """Info CAS (cas.chat) de un usuario + su estado real en el grupo (getChatMember)."""
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    uid = body.get("user_id")
    cas = _check_cas(uid) if _check_cas else {"ok": False, "banned": False}
    tg_status = None
    bot = _get_bot_for_chat(chat_id) if _get_bot_for_chat else None
    if bot:
        r = bot.api_call("getChatMember", {"chat_id": chat_id, "user_id": uid})
        if isinstance(r, dict) and r.get("ok"):
            tg_status = (r.get("result") or {}).get("status")
    return jsonify({"ok": True, "user_id": uid, "cas": cas, "tg_status": tg_status})


@bp.route("/api/public/group/unschedule", methods=["POST", "OPTIONS"])
def group_unschedule():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    ok = _channel_stats.cancel_scheduled(body.get("id"), chat_id)
    return jsonify({"ok": ok})


@bp.route("/api/public/group/stats", methods=["POST", "OPTIONS"])
def group_stats():
    """Estadísticas tipo TGStat del grupo/canal (admin/creador del chat)."""
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    return jsonify({"ok": True, "stats": _channel_stats.get_stats_by_chat(chat_id)})


# ─────────────────────────── Anuncios mutuos (InsideAds) ────────────────────────
def _auth_user(body):
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return None, (jsonify({"ok": False, "error": "initData inválido"}), 401)
    return user, None


@bp.route("/api/public/registry/status", methods=["POST", "OPTIONS"])
def registry_status():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user, err = _auth_user(body)
    if err:
        return err
    uid = str(user.get("id"))
    record = _ban_manager.get_ban_record(uid) if _ban_manager else None
    appeals = _ban_manager.list_ban_appeals(status="all", limit=20, uid=uid) if _ban_manager else []
    safe_record = None
    if record:
        safe_record = {
            "status": record.get("status", "active"),
            "reason": record.get("reason", ""),
            "source": record.get("source", ""),
            "severity": record.get("severity", "medium"),
            "expires_at": record.get("expires_at"),
            "created_at": record.get("created_at"),
            "updated_at": record.get("updated_at"),
        }
    return jsonify({"ok": True, "listed": bool(record and record.get("status") == "active"),
                    "record": safe_record, "appeals": appeals})


@bp.route("/api/public/registry/appeal", methods=["POST", "OPTIONS"])
def registry_appeal():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user, err = _auth_user(body)
    if err:
        return err
    if not _ban_manager:
        return jsonify({"ok": False, "error": "registro no disponible"}), 503
    appeal = _ban_manager.create_ban_appeal(user.get("id"), body.get("message"))
    if appeal is False:
        return jsonify({"ok": False, "error": "ya tienes una apelación pendiente"}), 409
    if not appeal:
        return jsonify({"ok": False, "error": "no hay un bloqueo activo o falta el motivo"}), 400
    return jsonify({"ok": True, "appeal": appeal}), 201


@bp.route("/api/public/ads/partners", methods=["POST", "OPTIONS"])
def ads_partners():
    """Canales disponibles como socios (donde el bot está), excepto el propio."""
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    out = [{"chat_id": c["chat_id"], "name": c["name"], "username": c["username"],
            "subscribers": c["subscribers"], "ctype": c["ctype"]}
           for c in _channel_stats.get_all_channels() if str(c["chat_id"]) != str(chat_id)]
    return jsonify({"ok": True, "partners": out})


@bp.route("/api/public/ads/request", methods=["POST", "OPTIONS"])
def ads_request():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user, err = _auth_user(body)
    if err:
        return err
    from_chat = body.get("from_chat")
    to_chat = body.get("to_chat")
    from_ad = (body.get("from_ad") or "").strip()
    when = (body.get("when") or "").strip()
    if not (from_chat and to_chat and from_ad and when):
        return jsonify({"ok": False, "error": "faltan datos"}), 400
    if not (_is_master(user) or _channel_stats.is_user_admin_of(user.get("id"), from_chat)):
        return jsonify({"ok": False, "error": "no gestionas el canal de origen"}), 403
    hit = _banned_hit(to_chat, from_ad)
    if hit:
        return jsonify({"ok": False, "error": f"El anuncio contiene una palabra no permitida en el canal destino: «{hit}»"}), 400
    fm = _channel_stats.get_channel_meta(from_chat) or {}
    tm = _channel_stats.get_channel_meta(to_chat) or {}
    rec = _channel_stats.create_ad_request(from_chat, user.get("id"), fm.get("name"),
                                           to_chat, tm.get("name"), from_ad, when,
                                           from_image=(body.get("from_image") or "").strip())
    return jsonify({"ok": True, "id": rec.get("id")})


@bp.route("/api/public/ads/incoming", methods=["POST", "OPTIONS"])
def ads_incoming_ep():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user, err = _auth_user(body)
    if err:
        return err
    chat_id = body.get("chat_id")
    if chat_id is not None:
        rows = _channel_stats.ads_for_channel(chat_id)
    else:
        rows = _channel_stats.ads_incoming(user.get("id"))
    ads = [{"id": r["id"], "from_name": r.get("from_name"), "from_chat": r.get("from_chat"),
            "to_name": r.get("to_name"), "from_ad": r.get("from_ad"),
            "from_image": r.get("from_ad_image"), "when": r.get("when")} for r in rows]
    return jsonify({"ok": True, "ads": ads})


@bp.route("/api/public/ads/outgoing", methods=["POST", "OPTIONS"])
def ads_outgoing_ep():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user, err = _auth_user(body)
    if err:
        return err
    rows = _channel_stats.ads_outgoing(user.get("id"))
    ads = [{"id": r["id"], "to_name": r.get("to_name"), "from_ad": r.get("from_ad"),
            "when": r.get("when"), "status": r.get("status")} for r in rows]
    return jsonify({"ok": True, "ads": ads})


@bp.route("/api/public/ads/accept", methods=["POST", "OPTIONS"])
def ads_accept():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user, err = _auth_user(body)
    if err:
        return err
    ad = _channel_stats.get_ad(body.get("id"))
    if not ad:
        return jsonify({"ok": False, "error": "solicitud no encontrada"}), 404
    if not (_is_master(user) or _channel_stats.is_user_admin_of(user.get("id"), ad.get("to_chat"))):
        return jsonify({"ok": False, "error": "no gestionas el canal destino"}), 403
    to_ad = (body.get("to_ad") or "").strip()
    if not to_ad:
        return jsonify({"ok": False, "error": "falta tu anuncio"}), 400
    to_image = (body.get("to_image") or "").strip()
    hit = _banned_hit(ad.get("from_chat"), to_ad)
    if hit:
        return jsonify({"ok": False, "error": f"Tu anuncio contiene una palabra no permitida en el canal destino: «{hit}»"}), 400
    when = ad.get("when")
    # Programa ambos anuncios (con imagen si la hay): el de origen va al destino y viceversa.
    _channel_stats.schedule_message(ad["to_chat"], ad["from_ad"], when, created_by=user.get("id"),
                                    bot_token=_channel_stats.get_channel_bot_token(ad["to_chat"]),
                                    photo=ad.get("from_ad_image"))
    _channel_stats.schedule_message(ad["from_chat"], to_ad, when, created_by=user.get("id"),
                                    bot_token=_channel_stats.get_channel_bot_token(ad["from_chat"]),
                                    photo=to_image)
    _channel_stats.set_ad(ad["id"], "accepted", to_ad, to_image)
    return jsonify({"ok": True})


@bp.route("/api/public/ads/decline", methods=["POST", "OPTIONS"])
def ads_decline():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user, err = _auth_user(body)
    if err:
        return err
    ad = _channel_stats.get_ad(body.get("id"))
    if not ad:
        return jsonify({"ok": False, "error": "no encontrada"}), 404
    if not (_is_master(user) or _channel_stats.is_user_admin_of(user.get("id"), ad.get("to_chat"))):
        return jsonify({"ok": False, "error": "sin permiso"}), 403
    _channel_stats.set_ad(ad["id"], "declined")
    return jsonify({"ok": True})


@bp.route("/api/public/stats/mine", methods=["POST", "OPTIONS"])
def public_mine():
    """Canales del usuario que abre la Mini App (validado por initData)."""
    if request.method == "OPTIONS":
        return ("", 204)
    init_data = (request.json or {}).get("initData", "")
    user = _verify_init_data(init_data)
    if user is None:
        return jsonify({"ok": False, "error": "initData inválido"}), 401
    try:
        return jsonify({"ok": True, "channels": _channel_stats.get_user_channels(user.get("id"))})
    except Exception as error:
        return jsonify({"ok": False, "error": f"PocketBase no disponible: {error}"}), 503


@bp.route("/api/public/notifications", methods=["POST", "OPTIONS"])
def public_notifications():
    """Alertas relevantes para los grupos que el usuario puede administrar."""
    if request.method == "OPTIONS":
        return ("", 204)
    user = _verify_init_data((request.json or {}).get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData inválido"}), 401
    preferences = CommunityMembers(_db).preferences(user.get("id"))
    channels = (
        _channel_stats.get_all_channels() if _is_master(user)
        else _channel_stats.get_user_channels(user.get("id"))
    )
    rows = []
    for channel in channels or []:
        cid, name = str(channel.get("chat_id")), channel.get("name") or "Grupo"
        reports = _db.get(f"GROUP_REPORTS_{cid}", []) if _db else []
        for report in reports[-30:] if isinstance(reports, list) else []:
            if report.get("status") == "pending":
                rows.append({
                    "id": f"report:{cid}:{report.get('id')}",
                    "type": "report", "title": f"Reporte pendiente · {name}",
                    "body": f"Usuario {report.get('target_id')}: {report.get('reason') or 'Sin motivo'}",
                    "created_at": report.get("created_at"), "chat_id": cid,
                })
        events = _db.get(f"MEDIA_SECURITY_EVENTS_{cid}", []) if _db else []
        for event in events[-20:] if isinstance(events, list) else []:
            if event.get("matched"):
                rows.append({
                    "id": f"media:{cid}:{event.get('message_id')}:{event.get('created_at')}",
                    "type": "security", "title": f"Alerta multimedia · {name}",
                    "body": f"{event.get('user') or event.get('user_id')}: {event.get('reason')}",
                    "created_at": event.get("created_at"), "chat_id": cid,
                })
    if _is_master(user):
        appeals = _db.get("BAN_APPEALS", []) if _db else []
        for appeal in appeals[-30:] if isinstance(appeals, list) else []:
            if appeal.get("status") == "pending":
                rows.append({
                    "id": f"appeal:{appeal.get('id')}", "type": "appeal",
                    "title": "Apelación pendiente",
                    "body": f"Usuario {appeal.get('user_id')}: {appeal.get('message') or 'Revisión solicitada'}",
                    "created_at": appeal.get("created_at"),
                })
    rows = [row for row in rows if (
        (row.get("type") == "security" and preferences["security"]) or
        (row.get("type") in ("report", "appeal") and preferences["reports"]) or
        row.get("type") not in ("security", "report", "appeal")
    )]
    rows.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return jsonify({"ok": True, "notifications": rows[:100]})


def _community_members():
    return CommunityMembers(_db)


@bp.route("/api/public/community/me", methods=["POST", "OPTIONS"])
def community_me():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData inválido"}), 401
    manager = _community_members()
    if body.get("profile") and isinstance(body["profile"], dict):
        profile = manager.update_profile(user.get("id"), {**body["profile"], "name": user.get("first_name")})
    else:
        profile = manager.profile(user.get("id"), user.get("first_name"))
    return jsonify({"ok": True, "profile": profile,
                    "preferences": manager.preferences(user.get("id")),
                    "reminders": manager.reminders(user.get("id"))})


@bp.route("/api/public/community/role-request", methods=["POST", "OPTIONS"])
def community_role_request():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData inválido"}), 401
    item = _community_members().request_role(user.get("id"), body.get("role"), body.get("reason"))
    return jsonify({"ok": bool(item), "request": item}), 200 if item else 400


@bp.route("/api/public/community/reminder", methods=["POST", "OPTIONS"])
def community_reminder():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData inválido"}), 401
    try:
        item = _community_members().reminder(user.get("id"), body.get("text", ""), body.get("remind_at"))
        return jsonify({"ok": True, "reminder": item})
    except (TypeError, ValueError) as error:
        return jsonify({"ok": False, "error": str(error)}), 400


@bp.route("/api/public/community/preferences", methods=["POST", "OPTIONS"])
def community_preferences():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData inválido"}), 401
    return jsonify({"ok": True, "preferences": _community_members().preferences(user.get("id"), body.get("preferences") or {})})


@bp.route("/api/public/community/directory", methods=["POST", "OPTIONS"])
def community_directory():
    if request.method == "OPTIONS":
        return ("", 204)
    user = _verify_init_data((request.json or {}).get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData inválido"}), 401
    return jsonify({"ok": True, "members": _community_members().directory()})


@bp.route("/api/public/community/engagement", methods=["POST", "OPTIONS"])
def community_engagement_snapshot():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}; user = _verify_init_data(body.get("initData", ""))
    if user is None: return jsonify({"ok": False, "error": "initData inválido"}), 401
    service = CommunityEngagement(_db)
    return jsonify({"ok": True, "surveys": service.surveys(), "events": service.events(),
                    "challenges": list(reversed(service._rows(_db, "COMMUNITY_CHALLENGES")))})


@bp.route("/api/public/community/engagement/action", methods=["POST", "OPTIONS"])
def community_engagement_action():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}; user = _verify_init_data(body.get("initData", ""))
    if user is None: return jsonify({"ok": False, "error": "initData inválido"}), 401
    service, uid, action = CommunityEngagement(_db), user.get("id"), body.get("action")
    try:
        if action == "survey_vote": result = service.vote_survey(body.get("survey_id"), uid, body.get("option_id"))
        elif action == "anonymous": result = service.anonymous_message(uid, body.get("text"), body.get("category"))
        elif action == "event_register": result = service.register_event(body.get("event_id"), uid)
        elif action == "event_cancel": result = service.cancel_registration(body.get("event_id"), uid)
        elif action == "event_checkin": result = service.checkin(body.get("event_id"), uid)
        elif action == "challenge": result = service.challenge_progress(body.get("challenge_id"), uid, body.get("amount", 1))
        elif action == "mentor": result = service.mentor_match(uid, body.get("skills") or [])
        elif action == "mentor_profile": result = service.mentor_profile(uid, body.get("skills") or [], body.get("capacity", 3), body.get("active", True))
        elif action == "certificate": result = service.certificate(body.get("event_id"), uid)
        elif action == "contest_submit": result = service.submit_contest(body.get("event_id"), uid, body.get("title"), body.get("content"))
        elif action == "contest_vote": result = service.vote_contest(body.get("event_id"), body.get("submission_id"), uid)
        elif action == "qa_question": result = service.qa_question(body.get("event_id"), uid, body.get("text"))
        elif action == "agenda": result = service.agenda_ics()
        else: return jsonify({"ok": False, "error": "acción inválida"}), 400
        return jsonify({"ok": bool(result), "result": result}), 200 if result else 404
    except (TypeError, ValueError) as error:
        return jsonify({"ok": False, "error": str(error)}), 400


@bp.route("/api/public/community/form/submit", methods=["POST", "OPTIONS"])
def community_form_submit():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData inválido"}), 401
    result = RoadmapEngine(_db).form_submit(body.get("form_id"), user.get("id"), body.get("answers") or {})
    return jsonify({"ok": bool(result), "result": result}), 200 if result else 404


# ─────────────────────────── Captcha de entrada (Join Request Queries) ──────────
# Pool de iconos del captcha (los mismos nombres que join.html mapea a SVG).
_JOIN_ICONS = ["star", "heart", "bolt", "moon", "cloud", "leaf"]


def _bounded_int(value, default, minimum, maximum):
    try:
        return max(minimum, min(int(value), maximum))
    except (TypeError, ValueError):
        return default


def _join_config(chat_id):
    raw = _db.get(f"JOINCFG_{chat_id}", {}) if _db else {}
    return {
        "enabled": bool(raw.get("enabled", True)),
        "max_attempts": _bounded_int(raw.get("max_attempts"), 3, 1, 10),
        "challenge_ttl": _bounded_int(raw.get("challenge_ttl"), 120, 30, 600),
        "request_ttl": _bounded_int(raw.get("request_ttl"), 86400, 300, 604800),
    }


def _join_stats(chat_id):
    raw = _db.get(f"JOINSTATS_{chat_id}", {}) if _db else {}
    return {key: int(raw.get(key, 0)) for key in ("approved", "declined", "expired")}


def _bump_join_stat(chat_id, key):
    stats = _join_stats(chat_id)
    stats[key] = stats.get(key, 0) + 1
    _db.set(f"JOINSTATS_{chat_id}", stats)


def _notify_join_review(bot, chat_id, pending, source, details=None):
    """Avisa por privado al master y a los administradores que puedan recibir al bot."""
    recipients = {str(_master_id)} if _master_id else set()
    admins = bot.api_call("getChatAdministrators", {"chat_id": chat_id}, silent=True)
    if isinstance(admins, dict) and admins.get("ok"):
        for member in admins.get("result", []):
            admin = member.get("user") or {}
            if not admin.get("is_bot") and admin.get("id") is not None:
                recipients.add(str(admin["id"]))
    user_id = pending.get("user_id")
    full_name = " ".join(filter(None, [pending.get("first_name"), pending.get("last_name")])).strip()
    username = f"@{pending.get('username')}" if pending.get("username") else "sin username"
    result = details if isinstance(details, dict) else {}
    source_label = "registro global de ComunidadTelebots" if source == "community" else "CAS"
    detail_line = (
        f"Motivo registrado: {result.get('reason') or 'sin motivo'}"
        if source == "community"
        else f"Ofensas CAS: {result.get('offenses', 'desconocidas')}"
    )
    text = (
        f"⚠️ Solicitud retenida por {source_label}\n\n"
        f"Usuario: {full_name or 'Sin nombre'} ({username})\n"
        f"ID: {user_id}\n"
        f"Grupo: {pending.get('chat_title') or chat_id}\n"
        f"{detail_line}\n\n"
        "El usuario completó correctamente el captcha. Revisa el caso antes de permitir su entrada."
    )
    keyboard = {"inline_keyboard": [[
        {"text": "✅ Aprobar igualmente", "callback_data": f"casjoin:a:{chat_id}:{user_id}"},
        {"text": "🚫 Banear y rechazar", "callback_data": f"casjoin:b:{chat_id}:{user_id}"},
    ]]}
    delivered = 0
    for recipient in recipients:
        response = bot.api_call("sendMessage", {
            "chat_id": recipient, "text": text, "reply_markup": json.dumps(keyboard),
        }, silent=True)
        if not isinstance(response, dict) or response.get("ok"):
            delivered += 1
    return delivered


@bp.route("/api/public/group/join/get", methods=["POST", "OPTIONS"])
def group_join_get():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    now = int(time.time())
    pending = []
    prefix = f"JOINQ_{chat_id}_"
    for key in (_db.keys(prefix) if _db else []):
        item = _db.get(key, {})
        if item.get("exp", 0) < now:
            _db.delete(key)
            _bump_join_stat(chat_id, "expired")
            continue
        pending.append({
            "user_id": item.get("user_id"),
            "first_name": item.get("first_name", ""),
            "last_name": item.get("last_name", ""),
            "username": item.get("username", ""),
            "attempts": int(item.get("attempts", 0)),
            "created_at": item.get("created_at"),
            "expires_at": item.get("exp"),
            "captcha_passed": bool(item.get("captcha_passed")),
            "cas_flagged": bool(item.get("cas_flagged")),
            "cas_offenses": item.get("cas_offenses"),
            "community_flagged": bool(item.get("community_flagged")),
            "community_reason": item.get("community_reason"),
        })
    pending.sort(key=lambda item: item.get("created_at") or 0, reverse=True)
    return jsonify({"ok": True, "config": _join_config(chat_id),
                    "stats": _join_stats(chat_id), "pending": pending})


@bp.route("/api/public/group/join/settings", methods=["POST", "OPTIONS"])
def group_join_settings():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    config = _join_config(chat_id)
    for key in ("enabled", "max_attempts", "challenge_ttl", "request_ttl"):
        if key in body:
            config[key] = body[key]
    config = {
        "enabled": bool(config["enabled"]),
        "max_attempts": _bounded_int(config["max_attempts"], 3, 1, 10),
        "challenge_ttl": _bounded_int(config["challenge_ttl"], 120, 30, 600),
        "request_ttl": _bounded_int(config["request_ttl"], 86400, 300, 604800),
    }
    _db.set(f"JOINCFG_{chat_id}", config)
    return jsonify({"ok": True, "config": config})


@bp.route("/api/public/group/join/decide", methods=["POST", "OPTIONS"])
def group_join_decide():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    try:
        user_id = int(body.get("user_id"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "user_id inválido"}), 400
    action = body.get("action")
    if action not in ("approve", "decline"):
        return jsonify({"ok": False, "error": "acción inválida"}), 400
    key = f"JOINQ_{chat_id}_{user_id}"
    pending = _db.get(key) if _db else None
    if not pending:
        return jsonify({"ok": False, "error": "solicitud no encontrada"}), 404
    bot = _hub_bot()
    if not bot:
        return jsonify({"ok": False, "error": "bot no disponible"}), 503
    if action == "approve":
        result = bot.api_call("answerChatJoinRequestQuery", {"query_id": pending.get("query_id")})
        stat = "approved"
    else:
        result = bot.api_call("declineChatJoinRequest", {"chat_id": chat_id, "user_id": user_id})
        stat = "declined"
    if isinstance(result, dict) and not result.get("ok", False):
        return jsonify({"ok": False, "error": result.get("description", "Telegram rechazó la acción")}), 502
    if action == "approve" and pending.get("community_flagged") and _ban_manager:
        _ban_manager.unban_user(user_id)
    _db.delete(key)
    _db.delete(f"JOINC_{chat_id}_{user_id}")
    _bump_join_stat(chat_id, stat)
    return jsonify({"ok": True, "action": action})


def _new_join_challenge():
    """9 celdas con EXACTAMENTE 3 iconos objetivo. Devuelve (target, grid, correct)."""
    rnd = secrets.SystemRandom()
    target = rnd.choice(_JOIN_ICONS)
    others = [i for i in _JOIN_ICONS if i != target]
    correct = sorted(rnd.sample(range(9), 3))
    grid = [target if i in correct else rnd.choice(others) for i in range(9)]
    return target, grid, correct


@bp.route("/api/public/join/challenge", methods=["POST", "OPTIONS"])
def join_challenge():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData inválido"}), 401
    cid, uid = body.get("chat"), user.get("id")
    if cid is None:
        return jsonify({"ok": False, "error": "falta chat"}), 400
    pend = _db.get(f"JOINQ_{cid}_{uid}") if _db else None
    if not pend or pend.get("exp", 0) < time.time():
        return jsonify({"ok": False, "error": "sin solicitud pendiente"}), 410
    if pend.get("captcha_passed") and (pend.get("cas_flagged") or pend.get("community_flagged")):
        return jsonify({"ok": False, "under_review": True,
                        "error": "solicitud en revisión administrativa"}), 423
    config = _join_config(cid)
    if not config["enabled"]:
        return jsonify({"ok": False, "error": "captcha desactivado"}), 403
    target, grid, correct = _new_join_challenge()
    _db.set(f"JOINC_{cid}_{uid}", {"correct": correct, "exp": int(time.time()) + config["challenge_ttl"]})
    return jsonify({"ok": True, "target": target, "grid": grid, "expires_in": config["challenge_ttl"]})


@bp.route("/api/public/join/verify", methods=["POST", "OPTIONS"])
def join_verify():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData inválido"}), 401
    cid, uid = body.get("chat"), user.get("id")
    pend = _db.get(f"JOINQ_{cid}_{uid}") if _db else None
    if not pend or pend.get("exp", 0) < time.time():
        return jsonify({"ok": False, "expired": True, "error": "solicitud expirada"}), 410
    chal = _db.get(f"JOINC_{cid}_{uid}")
    if not chal or chal.get("exp", 0) < time.time():
        return jsonify({"ok": False, "expired": True, "error": "reto expirado"})
    try:
        sel = sorted(int(i) for i in (body.get("selected") or []))
    except (TypeError, ValueError):
        sel = []
    bot = _hub_bot()
    config = _join_config(cid)
    # ── ÉXITO ──
    if sel and sel == sorted(chal.get("correct", [])):
        community = _ban_manager.get_ban_record(uid) if _ban_manager else None
        if community and community.get("status", "active") == "active":
            pend["captcha_passed"] = True
            pend["community_flagged"] = True
            pend["community_reason"] = community.get("reason", "")
            pend["community_checked_at"] = int(time.time())
            _db.set(f"JOINQ_{cid}_{uid}", pend)
            _db.delete(f"JOINC_{cid}_{uid}")
            notified = _notify_join_review(
                bot, cid, pend, "community", community
            ) if bot else 0
            return jsonify({"ok": True, "under_review": True, "notified": notified})
        cas = _check_cas(uid) if _check_cas else {"ok": False, "banned": False}
        if cas.get("ok") and cas.get("banned"):
            result = cas.get("result") if isinstance(cas.get("result"), dict) else {}
            pend["captcha_passed"] = True
            pend["cas_flagged"] = True
            pend["cas_offenses"] = result.get("offenses")
            pend["cas_checked_at"] = int(time.time())
            _db.set(f"JOINQ_{cid}_{uid}", pend)
            _db.delete(f"JOINC_{cid}_{uid}")
            notified = _notify_join_review(bot, cid, pend, "cas", result) if bot else 0
            return jsonify({"ok": True, "under_review": True, "notified": notified})
        if bot:
            bot.api_call("answerChatJoinRequestQuery", {"query_id": pend.get("query_id")})
        _db.delete(f"JOINC_{cid}_{uid}"); _db.delete(f"JOINQ_{cid}_{uid}")  # query_id de un solo uso
        _bump_join_stat(cid, "approved")
        return jsonify({"ok": True, "approved": True})
    # ── FALLO ──
    attempts = int(pend.get("attempts", 0)) + 1
    _db.delete(f"JOINC_{cid}_{uid}")  # fuerza reto nuevo (no resetea intentos)
    if attempts >= config["max_attempts"]:
        if bot:
            bot.api_call("declineChatJoinRequest", {"chat_id": cid, "user_id": uid})
        _db.delete(f"JOINQ_{cid}_{uid}")
        _bump_join_stat(cid, "declined")
        return jsonify({"ok": False, "declined": True, "attempts_left": 0})
    pend["attempts"] = attempts
    _db.set(f"JOINQ_{cid}_{uid}", pend)
    return jsonify({"ok": False, "attempts_left": config["max_attempts"] - attempts})


# ─────────────────────────────── Canales ───────────────────────────────────────

@bp.route("/api/public/stats/global")
def public_global():
    return jsonify({"ok": True, **_channel_stats.get_global_stats()})


@bp.route("/api/public/stats/language-map")
def public_language_map():
    data = aggregate_language_map(_db.get("TELEGRAM_USER_LANGUAGES", {}) if _db else {})
    return jsonify({"ok": True, **data})


@bp.route("/api/public/stats/channels")
def public_channels():
    rows = _channel_stats.get_channels(
        q=request.args.get("q", ""),
        sort=request.args.get("sort", "subscribers"),
        category=request.args.get("category", "all"),
    )
    return jsonify({"ok": True, "channels": rows})


@bp.route("/api/public/stats/channels/<username>")
def public_channel(username):
    ch = _channel_stats.get_channel(username)
    if not ch:
        return jsonify({"ok": False, "error": "not found"}), 404
    return jsonify({"ok": True, "channel": ch})


@bp.route("/api/public/stats/ranking")
def public_ranking():
    cat = request.args.get("category", "sin-categoria")
    return jsonify({"ok": True, "ranking": _channel_stats.get_ranking(cat)})


# ─────────────────────────────── Proxy ──────────────────────────────────────────

@bp.route("/api/public/proxy")
def public_proxy():
    """Devuelve un proxy MTProto activo listo para conectar (sin login)."""
    if not _proxy_mgr:
        return jsonify({"ok": False, "error": "proxy no disponible"}), 503
    try:
        vps = _proxy_mgr.get_vps_config(include_secret=True) or {}
    except Exception:
        vps = {}
    host = vps.get("host")
    candidates = []
    for p in getattr(_proxy_mgr, "proxies", []) or []:
        port, secret = p.get("port"), p.get("secret")
        if host and port and secret:
            candidates.append({
                "server": host,
                "port": port,
                "secret": secret,
                "tg_link": f"tg://proxy?server={host}&port={port}&secret={secret}",
                "https_link": f"https://t.me/proxy?server={host}&port={port}&secret={secret}",
                "tag": p.get("tag", ""),
            })
    if not candidates:
        return jsonify({"ok": False, "error": "sin proxies activos configurados"}), 404
    return jsonify({"ok": True, "count": len(candidates), "proxies": candidates})

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
import threading
import secrets
import re
import ipaddress
import urllib.request
import urllib.error
from urllib.parse import parse_qsl, urlparse

import jwt
from flask import Blueprint, request, jsonify, redirect

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
_get_ai_runtime_config = None
_set_ai_runtime_config = None
_task_queue = None
_group_administration = None
_community_api_usage = {}


def setup(channel_stats, proxy_mgr, master_id=None, jwt_secret=None, get_active_bots=None,
          db=None, ban_manager=None, get_bot_for_chat=None, check_cas=None,
          hub_bot_username="cintiabot", get_global_user_stats=None, get_global_chat_names=None,
          add_audit_log=None, vt_manager=None, get_ai_runtime_config=None, set_ai_runtime_config=None,
          task_queue=None, group_administration=None):
    global _channel_stats, _proxy_mgr, _master_id, _jwt_secret, _get_active_bots
    global _db, _ban_manager, _get_bot_for_chat, _check_cas
    global _hub_bot_username, _get_global_user_stats, _get_global_chat_names, _add_audit_log, _vt_manager
    global _get_ai_runtime_config, _set_ai_runtime_config, _task_queue, _group_administration
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
    _get_ai_runtime_config = get_ai_runtime_config
    _set_ai_runtime_config = set_ai_runtime_config
    _task_queue = task_queue
    _group_administration = group_administration
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
      2) firma contra un token de bot activo gestionado por Moonbot. Telegram
         usa el bot concreto desde el que se abrió la MiniApp.
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
    hub = _hub_bot()
    candidates = ([hub] if hub else []) + [
        bot for bot in ((_get_active_bots() or []) if _get_active_bots else []) if bot is not hub
    ]
    tokens = []
    for bot in candidates:
        token = getattr(bot, "token", None)
        if token and token not in tokens:
            tokens.append(token)
    if not tokens:
        return None
    data_check = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    for token in tokens:
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


def _admin_channel_union():
    """Une PocketBase con los chats activos de todos los bots sin duplicados."""
    try:
        channels = list(_channel_stats.get_all_channels())
    except Exception:
        channels = []
    by_id = {str(row.get("chat_id")): row for row in channels if row.get("chat_id") is not None}
    persisted = _db.get("U_FILE", {}) or {}
    names = {}
    names.update((_get_global_chat_names() or {}) if _get_global_chat_names else {})
    owners = {}
    for bot in (_get_active_bots() or []) if _get_active_bots else []:
        identity = {"id": str(getattr(bot, "bot_id", "") or getattr(bot, "user_id", "")),
                    "username": str(getattr(bot, "bot_username", "") or "Moonbot")}
        for chat_id in _safe_list(_db.get(f"CHATS_{getattr(bot, 'token', '')}", [])):
            owners.setdefault(str(chat_id), []).append(identity)
    for cid, state in persisted.items():
        if isinstance(state, dict) and state.get("name"):
            names.setdefault(str(cid), state["name"])
    for cid in _known_internal_group_ids():
        if cid not in by_id:
            by_id[cid] = {"chat_id": cid, "username": cid, "name": str(names.get(cid) or f"Grupo {cid}"),
                          "description": "", "category": "sin-categoria", "subscribers": 0,
                          "growth30d": 0, "postsPerDay": 0, "ctype": "supergroup",
                          "listed": False, "collecting": True}
        elif str(by_id[cid].get("name") or "") in ("", "Canal", cid):
            by_id[cid]["name"] = str(names.get(cid) or by_id[cid].get("name") or f"Grupo {cid}")
    for cid, channel in by_id.items():
        channel["bots"] = owners.get(cid, [])
        if channel["bots"]:
            channel["bot_id"] = channel["bots"][0]["id"]
            channel["bot_username"] = channel["bots"][0]["username"]
    return list(by_id.values())


@bp.route("/api/internal/admin-overview")
def internal_admin_overview():
    """Resumen real y sin secretos para el panel central de TodoSobreAllTech."""
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    bots = list(_get_active_bots() or []) if _get_active_bots else []
    group_ids = set()
    instances = []
    chat_owners = {}
    for bot in bots:
        token = getattr(bot, "token", "")
        chats = {str(chat_id) for chat_id in _safe_list(_db.get(f"CHATS_{token}", [])) if chat_id}
        group_ids.update(chats)
        owner = {
            "id": str(getattr(bot, "bot_id", "") or getattr(bot, "user_id", "")),
            "name": str(getattr(bot, "bot_display_name", "") or getattr(bot, "bot_username", "") or "Moonbot"),
            "username": str(getattr(bot, "bot_username", "") or "Moonbot"),
        }
        for chat_id in chats:
            chat_owners.setdefault(chat_id, []).append(owner)
        instances.append({
            **owner,
            "status": "online" if getattr(bot, "running", False) else "offline",
            "groups": len(chats),
            "uptime_seconds": max(0, int(time.time() - float(getattr(bot, "runtime_started_at", time.time())))),
            "api_calls": int(getattr(bot, "runtime_api_calls", 0)),
            "api_errors": int(getattr(bot, "runtime_api_errors", 0)),
            "latency_ms": getattr(bot, "runtime_last_latency_ms", None),
            "updates_processed": int(getattr(bot, "runtime_updates", 0)),
            "last_update_at": getattr(bot, "runtime_last_update_at", None),
            "poll_failures": int(getattr(bot, "runtime_poll_failures", 0)),
            "_chat_ids": chats,
        })
    shared_group_ids = {chat_id for chat_id, owners in chat_owners.items() if len(owners) > 1}
    for instance in instances:
        chats = instance.pop("_chat_ids")
        instance["shared_groups"] = len(chats & shared_group_ids)
        instance["exclusive_groups"] = len(chats - shared_group_ids)

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
    persisted = _db.get("U_FILE", {}) or {}
    for cid, state in persisted.items():
        if isinstance(state, dict) and state.get("name"):
            names.setdefault(str(cid), state["name"])
    for channel in _admin_channel_union():
        if channel.get("chat_id") is not None and channel.get("name"):
            names.setdefault(str(channel["chat_id"]), channel["name"])
    channel_map = {str(row.get("chat_id")): row for row in _admin_channel_union()}
    groups = [{"id": cid, "name": str(names.get(cid) or names.get(str(cid)) or f"Grupo {cid}")[:160],
               "bots": chat_owners.get(cid) or channel_map.get(cid, {}).get("bots", []),
               "bot_count": len(chat_owners.get(cid, [])),
               "shared": cid in shared_group_ids,
               "bot_id": channel_map.get(cid, {}).get("bot_id"),
               "bot_username": channel_map.get(cid, {}).get("bot_username")}
              for cid in sorted(group_ids)]
    return jsonify({
        "ok": True,
        "generated_at": now.isoformat(),
        "summary": {
            "instances_online": len(instances),
            "users_observed": len(users),
            "users_active_24h": active_24h,
            "groups": len(group_ids),
            "shared_groups": len(shared_group_ids),
            "exclusive_groups": len(group_ids - shared_group_ids),
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


@bp.route("/api/internal/roadmap/action", methods=["POST"])
def internal_roadmap_action():
    """Funciones avanzadas expuestas a TodoSobreAllTech mediante la clave servidor-a-servidor."""
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    body = request.json or {}
    action, data = str(body.get("action") or ""), body.get("data") or {}
    service = RoadmapEngine(_db)
    handlers = {
        "rule_impact": lambda: service.rule_impact_simulation(data.get("group_id"), data.get("rule"), data.get("samples")),
        "library": lambda: service.library_save(data.get("title"), data.get("body"), data.get("tags")),
        "report_schedule": lambda: service.report_schedule(data.get("group_id"), data.get("channel"), data.get("frequency"), data.get("recipients")),
        "translation": lambda: service.translation_job(data.get("content_id"), data.get("languages")),
        "public_announcement": lambda: service.public_announcement_version("publish", title=data.get("title"), body=data.get("body"), actor_id="master_web"),
    }
    if action not in handlers:
        return jsonify({"ok": False, "error": "acción no permitida"}), 400
    try:
        result = handlers[action]()
        return jsonify({"ok": True, "result": result})
    except (TypeError, ValueError) as error:
        return jsonify({"ok": False, "error": str(error)}), 400


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


def _start_bulk_captcha(bot, cid, actor="admin"):
    """Reverifica en segundo plano a los miembros observados sin bloquear la API."""
    job_key = f"JOIN_BULK_JOB_{cid}"
    current = _db.get(job_key, {}) if _db else {}
    if current.get("status") == "running":
        return current, False
    observed = _db.get(f"TELEGRAM_GROUP_LANGUAGES_{cid}", {}) if _db else {}
    config = _join_config(cid)
    exempt = set(config.get("exempt_user_ids") or [])
    user_ids = [uid for uid in (observed or {}).keys() if str(uid) not in exempt] if isinstance(observed, dict) else []
    job = {"status": "running", "total": len(user_ids), "processed": 0, "muted": 0,
           "private_sent": 0, "private_blocked": 0, "skipped": 0,
           "started_at": int(time.time()), "actor": str(actor)[:80]}
    _db.set(job_key, job)
    _db.set(f"JOIN_BULK_LAST_{cid}", job["started_at"])

    def run():
        ttl = _join_config(cid)["request_ttl"]
        stats = (_get_global_user_stats() or {}) if _get_global_user_stats else {}
        for raw_uid in user_ids:
            latest = _db.get(job_key, {}) or {}
            if latest.get("status") == "cancel_requested":
                job["status"] = "cancelled"
                break
            try:
                uid = int(raw_uid)
                membership = bot.api_call("getChatMember", {"chat_id": cid, "user_id": uid}, silent=True)
                member = membership.get("result", {}) if isinstance(membership, dict) and membership.get("ok") else {}
                user = member.get("user") or {}
                if member.get("status") not in ("member", "restricted") or user.get("is_bot"):
                    job["skipped"] += 1
                    continue
                muted = bot.restrict_user(cid, uid, can_send=False)
                if not isinstance(muted, dict) or not muted.get("ok"):
                    job["skipped"] += 1
                    continue
                profile = stats.get(str(uid), {}) or stats.get(uid, {}) or {}
                _db.set(f"JOINQ_{cid}_{uid}", {
                    "query_id": None, "chat_id": cid, "user_id": uid,
                    "first_name": user.get("first_name") or profile.get("name", ""),
                    "last_name": user.get("last_name", ""), "username": user.get("username", ""),
                    "chat_title": str((_get_global_chat_names() or {}).get(str(cid), cid)),
                    "attempts": 0, "created_at": int(time.time()), "exp": int(time.time()) + ttl,
                    "admitted": True, "telegram_muted": True, "bulk_reverification": True,
                })
                job["muted"] += 1
                url = f"https://cintiabot.todosobreall.tech/join.html?chat={cid}"
                sent = bot.api_call("sendMessage", {"chat_id": uid,
                    "text": "🔐 El grupo requiere una nueva verificación. Completa el captcha para recuperar tus permisos de envío.",
                    "reply_markup": json.dumps({"inline_keyboard": [[{"text": "Completar captcha", "web_app": {"url": url}}]]})}, silent=True)
                if isinstance(sent, dict) and sent.get("ok"):
                    job["private_sent"] += 1
                else:
                    job["private_blocked"] += 1
            except Exception:
                job["skipped"] += 1
            finally:
                job["processed"] += 1
                if job["processed"] % 10 == 0:
                    _db.set(job_key, job)
                time.sleep(0.04)
        if job.get("status") != "cancelled":
            job["status"] = "completed"
        job["finished_at"] = int(time.time())
        _db.set(job_key, job)
        history_key = f"JOIN_BULK_HISTORY_{cid}"
        history = _safe_list(_db.get(history_key, []))
        history.append(dict(job))
        _db.set(history_key, history[-20:])

    threading.Thread(target=run, daemon=True, name=f"captcha-bulk-{cid}").start()
    return job, True


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
        elif action == "save_join_config":
            join_config = _join_config(cid)
            join_config["enabled"] = bool(body.get("enabled", join_config["enabled"]))
            join_config["mute_until_verified"] = bool(body.get("mute_until_verified", join_config["mute_until_verified"]))
            join_config["strict_enforcement"] = bool(body.get("strict_enforcement", join_config["strict_enforcement"]))
            if "reverify_interval_days" in body:
                join_config["reverify_interval_days"] = _bounded_int(body.get("reverify_interval_days"), 0, 0, 90)
            if "exempt_user_ids" in body:
                values = body.get("exempt_user_ids") or []
                join_config["exempt_user_ids"] = [str(value).strip() for value in values if str(value).strip().isdigit()][:100]
            _db.set(f"JOINCFG_{cid}", join_config)
            return jsonify({"ok": True, "join_config": _join_config(cid)})
        elif action == "reverify_all":
            job, started = _start_bulk_captcha(bot, cid, "web-master")
            return jsonify({"ok": True, "started": started, "captcha_job": job})
        elif action == "preview_reverify":
            observed = _db.get(f"TELEGRAM_GROUP_LANGUAGES_{cid}", {}) or {}
            return jsonify({"ok": True, "captcha_preview": {"observed": len(observed),
                "note": "Se comprobará en Telegram y se excluirán administradores, bots y miembros que ya salieron."}})
        elif action == "cancel_reverify":
            job = _db.get(f"JOIN_BULK_JOB_{cid}", {}) or {}
            if job.get("status") == "running":
                job["status"] = "cancel_requested"
                _db.set(f"JOIN_BULK_JOB_{cid}", job)
            return jsonify({"ok": True, "captcha_job": job})
        elif action == "sync_commands":
            return jsonify({"ok": True, "command_menu": bot.sync_command_menu(cid)})
        elif action == "copy_config":
            source = str(body.get("source_id", ""))
            if not _known_internal_group(source):
                return jsonify({"ok": False, "error": "source_group_not_found"}), 404
            config = suite.save_config(cid, suite.config(source))
        elif action == "compare_config":
            source = str(body.get("source_id", ""))
            if not _known_internal_group(source):
                return jsonify({"ok": False, "error": "source_group_not_found"}), 404
            left, right = suite.config(cid), suite.config(source)
            differences = []
            for section in sorted(set(left) | set(right)):
                if left.get(section) != right.get(section):
                    differences.append({"section": section, "current": left.get(section), "source": right.get(section)})
            return jsonify({"ok": True, "comparison": {"source_id": source, "differences": differences,
                                                         "identical": not differences}})
        else:
            return jsonify({"ok": False, "error": "invalid_action"}), 400
        return jsonify({"ok": True, "config": config, "command_menu": bot.sync_command_menu(cid)})

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
    safe_history = [{"time": row.get("time"), "sender": str(row.get("sender") or row.get("uid") or "")[:100],
                     "text": str(row.get("text") or "")[:500], "has_media": bool(row.get("media"))}
                    for row in history[-50:] if isinstance(row, dict)]
    repair_steps = (["Abre la informaciÃ³n del grupo en Telegram", "Entra en Administradores",
                     f"Selecciona @{getattr(bot, 'bot_username', 'MoonBot')}",
                     "Activa los permisos indicados y guarda los cambios"] if missing else [])
    return jsonify({
        "ok": True,
        "group": {"id": str(cid), "name": str((_get_global_chat_names() or {}).get(str(cid), f"Grupo {cid}"))[:160]},
        "permissions": {"healthy": not missing, "status": member.get("status", "unknown"), "missing": missing},
        "repair_steps": repair_steps,
        "config": suite.config(cid),
        "join_config": _join_config(cid),
        "captcha_job": _db.get(f"JOIN_BULK_JOB_{cid}", {}),
        "captcha_history": list(reversed(_safe_list(_db.get(f"JOIN_BULK_HISTORY_{cid}", []))))[:10],
        "captcha_schedule": {"last_run": int(_db.get(f"JOIN_BULK_LAST_{cid}", 0) or 0)},
        "command_menu": bot.command_menu_preview(cid),
        "activity": {"stored_messages": len(history), "warnings": len(_db.get(f"WARNS_{cid}", {}) or {}),
                     "media_events": len(suite.media_events(cid, 100))},
        "history": safe_history,
    })


def _internal_ads_payload(cid):
    preferences = _channel_stats.partner_preferences(cid)
    partners = []
    for row in _channel_stats.get_all_channels():
        if str(row.get("chat_id")) == str(cid) or preferences.get(str(row.get("chat_id"))) == "blocked":
            continue
        partners.append({"chat_id": str(row.get("chat_id")), "name": row.get("name"),
                         "subscribers": int(row.get("subscribers", 0) or 0),
                         "category": row.get("category"),
                         "favorite": preferences.get(str(row.get("chat_id"))) == "favorite"})
    partners.sort(key=lambda row: (not row["favorite"], -row["subscribers"]))
    campaigns = _channel_stats.ads_history(cid, 100)
    return {"partners": partners, "campaigns": [{"id": row["id"], "from_chat": row.get("from_chat"),
        "to_chat": row.get("to_chat"), "from_name": row.get("from_name"), "to_name": row.get("to_name"),
        "from_ad": row.get("from_ad"), "to_ad": row.get("to_ad"), "when": row.get("when"),
        "status": row.get("status"), "deliveries": int(row.get("delivered_count", 0) or 0),
        "failures": int(row.get("failed_count", 0) or 0), "clicks": int(row.get("clicks", 0) or 0)}
        for row in campaigns]}


@bp.route("/api/internal/groups/<cid>/ads", methods=["GET", "POST"])
def internal_group_ads(cid):
    if not _internal_admin_authorized(): return jsonify({"ok": False, "error": "unauthorized"}), 401
    if not _known_internal_group(cid): return jsonify({"ok": False, "error": "group_not_found"}), 404
    if request.method == "GET": return jsonify({"ok": True, **_internal_ads_payload(cid)})
    body = request.json or {}; action = body.get("action")
    if action == "request":
        target, text, when = str(body.get("to_chat", "")), str(body.get("text", "")).strip(), str(body.get("when", ""))
        if not _known_internal_group(target) or not text or len(text) > 3500:
            return jsonify({"ok": False, "error": "campaña no válida"}), 400
        try: scheduled = datetime.datetime.fromisoformat(when.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError: return jsonify({"ok": False, "error": "fecha no válida"}), 400
        if scheduled < datetime.datetime.utcnow() + datetime.timedelta(minutes=10):
            return jsonify({"ok": False, "error": "la fecha debe estar al menos a 10 minutos"}), 400
        target_url = str(body.get("target_url") or "").strip()
        if target_url and (urlparse(target_url).scheme not in ("http", "https") or not urlparse(target_url).netloc):
            return jsonify({"ok": False, "error": "enlace no válido"}), 400
        source, destination = _channel_stats.get_channel_meta(cid) or {}, _channel_stats.get_channel_meta(target) or {}
        _channel_stats.create_ad_request(cid, MASTER_ID, source.get("name", f"Grupo {cid}"), target,
            destination.get("name", f"Grupo {target}"), text, when, from_image=body.get("image"),
            from_url=target_url, variants=json.dumps(body.get("variants") or [], ensure_ascii=False))
    else:
        ad = _channel_stats.get_ad(body.get("id"))
        if not ad or str(cid) not in (str(ad.get("from_chat")), str(ad.get("to_chat"))):
            return jsonify({"ok": False, "error": "campaña no encontrada"}), 404
        if action == "cancel" and ad.get("status") in ("pending", "countered", "master_review"):
            _channel_stats.update_ad(ad["id"], {"status": "cancelled"})
        elif action == "decline": _channel_stats.update_ad(ad["id"], {"status": "declined"})
        elif action == "accept":
            reciprocal = str(body.get("text") or "").strip()
            if not reciprocal: return jsonify({"ok": False, "error": "falta anuncio recíproco"}), 400
            target_url = str(body.get("target_url") or "").strip()
            if target_url and (urlparse(target_url).scheme not in ("http", "https") or not urlparse(target_url).netloc):
                return jsonify({"ok": False, "error": "enlace no válido"}), 400
            _schedule_ad_pair(ad, MASTER_ID, reciprocal, body.get("image"), target_url, ad.get("when"))
        else: return jsonify({"ok": False, "error": "acción no permitida"}), 400
    return jsonify({"ok": True, **_internal_ads_payload(cid)})


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
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = max(10, min(100, int(request.args.get("per_page", 50))))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "invalid_pagination"}), 400
    rows = [_user_view(uid, stats if isinstance(stats, dict) else {}) for uid, stats in users.items()]
    if query:
        rows = [row for row in rows if query in row["id"].lower() or query in row["name"].lower()]
    rows.sort(key=lambda row: (row["banned"], row["messages"]), reverse=True)
    total = len(rows)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, total_pages)
    start = (page - 1) * per_page
    return jsonify({"ok": True, "total": total, "page": page, "per_page": per_page,
                    "total_pages": total_pages, "users": rows[start:start + per_page],
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
    elif action in ("mute", "unmute"):
        bot = _known_internal_group(cid)
        if not bot:
            return jsonify({"ok": False, "error": "group_not_found"}), 404
        if action == "mute":
            try:
                minutes = max(1, min(int(body.get("minutes", 30)), 10080))
            except (TypeError, ValueError):
                minutes = 30
            result = bot.api_call("restrictChatMember", {"chat_id": cid, "user_id": uid,
                "until_date": int(time.time()) + minutes * 60,
                "permissions": {"can_send_messages": False}}, silent=True)
        else:
            result = bot.api_call("restrictChatMember", {"chat_id": cid, "user_id": uid,
                "permissions": {"can_send_messages": True, "can_send_audios": True, "can_send_documents": True,
                                "can_send_photos": True, "can_send_videos": True, "can_send_other_messages": True,
                                "can_add_web_page_previews": True}}, silent=True)
        telegram_results.append({"group_id": cid, "ok": bool(result.get("ok"))})
    elif action == "peer_review":
        result = RoadmapEngine(_db).peer_review(body.get("operation", "create"), body.get("case_id"),
                                               "todosobrealltech", body.get("verdict"),
                                               {"user_id": uid, "reason": reason}, body.get("quorum", 3))
        return jsonify({"ok": bool(result), "review": result}), 200 if result else 404
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
    local_bans = _ban_manager.get_all_local_bans() if _ban_manager else {}
    source_summary = {
        "cas": sum(count for source, count in sources.items() if source in ("cas", "cas_feed", "export.csv")),
        "spamwatch": sum(count for source, count in sources.items() if "spamwatch" in source),
        "community": sum(count for source, count in sources.items() if source in ("community", "community_api", "reported")),
        "local": sum(len(users) for users in local_bans.values()),
        "other": sum(count for source, count in sources.items() if source not in ("cas", "cas_feed", "export.csv", "community", "community_api", "reported") and "spamwatch" not in source),
    }
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
        "source_summary": source_summary,
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
    if action == "impersonation":
        candidate = body.get("candidate") if isinstance(body.get("candidate"), dict) else {}
        administrators = body.get("administrators") if isinstance(body.get("administrators"), list) else []
        result = RoadmapEngine(_db).impersonation_check(candidate, administrators[:100])
        return jsonify({"ok": True, "result": result})
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


@bp.route("/api/internal/ai-center", methods=["GET", "POST"])
def internal_ai_center():
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    engine = RoadmapEngine(_db)
    if request.method == "GET":
        runtime = _get_ai_runtime_config() if _get_ai_runtime_config else {}
        evaluations = list(reversed(_safe_list(_db.get("AI_MODEL_EVALUATIONS", []))))[:100]
        sources = list(reversed(_safe_list(_db.get("AI_APPROVED_SOURCES", []))))[:200]
        reviews = list(reversed(_safe_list(_db.get("AI_HUMAN_REVIEWS", []))))[:200]
        group_configs = {cid: _db.get(f"AI_GROUP_CONFIG_{cid}", {}) for cid in _known_internal_group_ids()}
        memories = {cid: len(_safe_list(_db.get(f"AI_MEMORY_{cid}", []))) for cid in _known_internal_group_ids()}
        return jsonify({"ok": True, "runtime": {
            "use_external": bool(runtime.get("USE_EXTERNAL_LLM")), "hybrid_ratio": int(runtime.get("HYBRID_PERCENTAGE", 0)),
            "provider": runtime.get("LLM_PROVIDER", "local"), "model": runtime.get("OLLAMA_MODEL", ""),
            "deep_dream": bool(runtime.get("DEEP_DREAM_MODE")),
        }, "group_configs": group_configs, "sources": sources, "evaluations": evaluations,
            "reviews": reviews, "memories": memories})
    body = request.json or {}; action = str(body.get("action", "")); result = None
    try:
        if action == "runtime":
            provider = str(body.get("provider", "local")).lower()
            if provider not in ("local", "ollama", "gemini"):
                return jsonify({"ok": False, "error": "invalid_provider"}), 400
            cfg = _get_ai_runtime_config() if _get_ai_runtime_config else {}
            cfg.update({"USE_EXTERNAL_LLM": bool(body.get("use_external")), "HYBRID_PERCENTAGE": max(0, min(int(body.get("hybrid_ratio", 0)), 100)),
                        "LLM_PROVIDER": provider, "OLLAMA_MODEL": str(body.get("model", ""))[:200], "DEEP_DREAM_MODE": bool(body.get("deep_dream"))})
            if _set_ai_runtime_config: _set_ai_runtime_config(cfg)
            result = {key: cfg[key] for key in ("USE_EXTERNAL_LLM", "HYBRID_PERCENTAGE", "LLM_PROVIDER", "OLLAMA_MODEL", "DEEP_DREAM_MODE")}
        elif action == "group_config":
            cid = str(body.get("group_id", ""))
            if cid not in _known_internal_group_ids(): return jsonify({"ok": False, "error": "group_not_found"}), 404
            result = {"provider": str(body.get("provider", "inherit"))[:50], "model": str(body.get("model", ""))[:200],
                      "purpose": str(body.get("purpose", "conversation"))[:50], "updated_at": datetime.datetime.now().isoformat()}
            _db.set(f"AI_GROUP_CONFIG_{cid}", result)
        elif action == "source_add":
            cid = str(body.get("group_id", ""))
            if cid not in _known_internal_group_ids(): return jsonify({"ok": False, "error": "group_not_found"}), 404
            result = engine.ai_source(cid, body.get("title", ""), body.get("content", ""), True)
        elif action == "source_delete":
            rows = _safe_list(_db.get("AI_APPROVED_SOURCES", [])); before = len(rows)
            rows = [item for item in rows if str(item.get("id")) != str(body.get("source_id"))]; _db.set("AI_APPROVED_SOURCES", rows)
            result = {"deleted": before - len(rows)}
        elif action == "memory_delete":
            cid = str(body.get("group_id", "")); index = int(body.get("index", -1)); rows = _safe_list(_db.get(f"AI_MEMORY_{cid}", []))
            if index < 0 or index >= len(rows): return jsonify({"ok": False, "error": "memory_not_found"}), 404
            rows.pop(index); _db.set(f"AI_MEMORY_{cid}", rows); result = {"remaining": len(rows)}
        elif action == "evaluate":
            result = engine.model_evaluation(body.get("model"), body.get("correct", 0), body.get("total", 0), body.get("latency_ms", 0), body.get("cost", 0))
        elif action == "unanswered":
            result = {"questions": engine.unanswered_questions(body.get("messages") or [], body.get("response_window", 10))}
        elif action == "review_create":
            rows = _safe_list(_db.get("AI_HUMAN_REVIEWS", [])); result = {"id": secrets.token_hex(6), "question": str(body.get("question", ""))[:1000], "answer": str(body.get("answer", ""))[:5000], "status": "pending", "created_at": datetime.datetime.now().isoformat()}; rows.append(result); _db.set("AI_HUMAN_REVIEWS", rows[-1000:])
        elif action == "review_resolve":
            rows = _safe_list(_db.get("AI_HUMAN_REVIEWS", [])); result = next((item for item in rows if item.get("id") == body.get("review_id")), None)
            if not result: return jsonify({"ok": False, "error": "review_not_found"}), 404
            result.update({"status": "approved" if body.get("approved") else "rejected", "comment": str(body.get("comment", ""))[:1000], "resolved_at": datetime.datetime.now().isoformat()}); _db.set("AI_HUMAN_REVIEWS", rows)
        else: return jsonify({"ok": False, "error": "invalid_action"}), 400
    except (TypeError, ValueError) as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    if _add_audit_log: _add_audit_log(f"TodoSobreAllTech IA: {action}")
    return jsonify({"ok": True, "result": result})


def _automation_templates():
    return [
        {"id": "welcome", "name": "Bienvenida automática", "description": "Responde al primer saludo del grupo.",
         "kind": "rule", "keyword": "hola", "response": "¡Bienvenido! Consulta las normas fijadas antes de participar."},
        {"id": "support", "name": "Derivación a soporte", "description": "Orienta las solicitudes de ayuda.",
         "kind": "rule", "keyword": "ayuda", "response": "Cuéntanos el problema y un administrador lo revisará."},
        {"id": "report", "name": "Formulario de incidencias", "description": "Recoge informes estructurados.",
         "kind": "form", "title": "Informar de una incidencia", "fields": [
             {"name": "description", "label": "Descripción", "type": "textarea", "required": True},
             {"name": "evidence", "label": "Enlace a evidencia", "type": "url", "required": False}]},
    ]


def _safe_webhook_url(value):
    raw = str(value or "").strip()[:1000]
    parsed = urlparse(raw)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("el webhook debe usar HTTPS y no incluir credenciales")
    host = parsed.hostname.casefold()
    if host == "localhost" or host.endswith(".local"):
        raise ValueError("destino de webhook no permitido")
    try:
        address = ipaddress.ip_address(host.strip("[]"))
        if not address.is_global:
            raise ValueError("destino de webhook privado no permitido")
    except ValueError as error:
        if "privado" in str(error):
            raise
    return raw


def _public_webhook(item):
    return {key: value for key, value in item.items() if key not in ("secret", "signature", "payload")}


@bp.route("/api/internal/automations", methods=["GET", "POST"])
def internal_automations():
    """Centro de automatizaciones para todosobreall.tech, sin exponer secretos."""
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    engine = RoadmapEngine(_db)
    if request.method == "GET":
        rules = list(reversed(_safe_list(_db.get("CONTENT_KEYWORD_RULES", []))))[:200]
        forms = list(reversed(_safe_list(_db.get("CONTENT_FORMS", []))))[:100]
        hooks = [_public_webhook(row) for row in reversed(_safe_list(_db.get("INTEGRATION_WEBHOOKS", [])))][:100]
        webhook_jobs = [_public_webhook(row) for row in reversed(_safe_list(_db.get("WEBHOOK_QUEUE", [])))][:100]
        tasks = _task_queue.get_all() if _task_queue else []
        calendar = list(reversed(_safe_list(_db.get("GROUP_ADMIN_CALENDAR", []))))[:200]
        return jsonify({"ok": True, "rules": rules, "forms": forms, "webhooks": hooks,
                        "queue": tasks, "webhook_queue": webhook_jobs, "calendar": calendar,
                        "templates": _automation_templates()})
    body = request.json or {}
    action = str(body.get("action", ""))
    group_id = str(body.get("group_id", ""))
    result = None
    try:
        if action in ("rule_save", "form_save", "webhook_save", "calendar", "automation_install"):
            if group_id not in _known_internal_group_ids():
                return jsonify({"ok": False, "error": "group_not_found"}), 404
        if action == "rule_save":
            keyword, response = str(body.get("keyword", "")).strip(), str(body.get("response", "")).strip()
            if not keyword or not response:
                raise ValueError("palabra clave y respuesta son obligatorias")
            conditions = body.get("conditions") if isinstance(body.get("conditions"), dict) else {}
            result = engine.keyword_rule(group_id, keyword, response, conditions)
        elif action == "rule_toggle":
            rows = _safe_list(_db.get("CONTENT_KEYWORD_RULES", []))
            result = next((row for row in rows if row.get("id") == body.get("rule_id")), None)
            if not result:
                return jsonify({"ok": False, "error": "rule_not_found"}), 404
            result["active"] = bool(body.get("active")); _db.set("CONTENT_KEYWORD_RULES", rows)
        elif action == "simulate":
            if group_id not in _known_internal_group_ids():
                return jsonify({"ok": False, "error": "group_not_found"}), 404
            result = {"matched": engine.keyword_match(group_id, body.get("text", ""), body.get("context") or {})}
        elif action == "form_save":
            fields = body.get("fields") if isinstance(body.get("fields"), list) else []
            if not str(body.get("title", "")).strip() or not fields:
                raise ValueError("título y campos son obligatorios")
            result = engine.form_save(body.get("title"), fields, group_id)
        elif action == "webhook_save":
            events = [str(value)[:80] for value in (body.get("events") or []) if str(value).strip()][:20]
            if not events: raise ValueError("selecciona al menos un evento")
            result = _public_webhook(engine.webhook_save(group_id, _safe_webhook_url(body.get("url")), events))
        elif action == "calendar":
            if not _group_administration: raise ValueError("calendario no disponible")
            result = _group_administration.calendar_action(group_id, body.get("calendar_action", "message"),
                                                            body.get("execute_at"), body.get("payload") or {})
        elif action in ("queue_cancel", "queue_prioritize"):
            if not _task_queue: raise ValueError("cola no disponible")
            task_id = int(body.get("task_id"))
            result = {"task_id": task_id, "action": action}
            (_task_queue.cancel if action == "queue_cancel" else _task_queue.prioritize)(task_id)
        elif action == "webhook_retry":
            rows = _safe_list(_db.get("WEBHOOK_QUEUE", []))
            result = next((row for row in rows if row.get("id") == body.get("job_id")), None)
            if not result: return jsonify({"ok": False, "error": "job_not_found"}), 404
            result.update({"status": "retry", "next_attempt": datetime.datetime.now(datetime.timezone.utc).isoformat()})
            _db.set("WEBHOOK_QUEUE", rows); result = _public_webhook(result)
        elif action == "automation_install":
            template = next((row for row in _automation_templates() if row["id"] == body.get("template_id")), None)
            if not template: return jsonify({"ok": False, "error": "template_not_found"}), 404
            result = (engine.keyword_rule(group_id, template["keyword"], template["response"], {})
                      if template["kind"] == "rule" else engine.form_save(template["title"], template["fields"], group_id))
        else:
            return jsonify({"ok": False, "error": "invalid_action"}), 400
    except (TypeError, ValueError) as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    if action != "simulate" and _add_audit_log:
        _add_audit_log(f"TodoSobreAllTech automatizaciones: {action}")
    return jsonify({"ok": True, "result": result})


@bp.route("/api/internal/integrations", methods=["GET", "POST"])
def internal_integrations():
    """Administración de extensiones y API; los tokens solo se muestran al crearlos."""
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    engine = RoadmapEngine(_db, _jwt_secret or "moonbot")
    if request.method == "GET":
        tokens = [{key: value for key, value in row.items() if key != "hash"}
                  for row in reversed(_safe_list(_db.get("API_TOKENS", [])))]
        calendars = [{key: value for key, value in row.items() if key != "sync_token"}
                     for row in reversed(_safe_list(_db.get("INTEGRATION_CALENDARS", [])))]
    return jsonify({"ok": True,
                        "modules": list(reversed(_safe_list(_db.get("MODULE_MARKETPLACE", []))))[:200],
                        "tokens": tokens[:200], "sandboxes": _db.get("BOT_SANDBOXES", {}) or {},
                        "quotas": _db.get("BOT_QUOTAS", {}) or {},
                        "incidents": list(reversed(_safe_list(_db.get("INTEGRATION_INCIDENTS", []))))[:200],
                        "calendars": calendars[:200], "sdk": engine.sdk_manifest()})
    body = request.json or {}; action = str(body.get("action", "")); result = None
    allowed_scopes = {"groups:read", "groups:write", "users:read", "moderation:write",
                      "analytics:read", "content:write", "webhooks:write"}
    try:
        if action == "module_register":
            name, version, checksum = (str(body.get(key, "")).strip() for key in ("name", "version", "checksum"))
            permissions = [str(value)[:80] for value in (body.get("permissions") or [])][:30]
            if not name or not version or not re.fullmatch(r"[a-fA-F0-9]{32,128}", checksum):
                raise ValueError("nombre, versión y checksum hexadecimal son obligatorios")
            result = engine.module_register(name, version, permissions, checksum.lower(), False)
        elif action == "token_create":
            scopes = sorted(set(body.get("scopes") or []))
            if not scopes or any(scope not in allowed_scopes for scope in scopes):
                raise ValueError("ámbitos de API no válidos")
            result = engine.api_token(body.get("name", "Integración"), scopes, body.get("expires_at") or None)
        elif action == "token_rotate":
            result = engine.rotate_token(body.get("token_id"))
            if not result: return jsonify({"ok": False, "error": "token_not_found"}), 404
        elif action == "token_revoke":
            rows = _safe_list(_db.get("API_TOKENS", [])); result = next((row for row in rows if row.get("id") == body.get("token_id")), None)
            if not result: return jsonify({"ok": False, "error": "token_not_found"}), 404
            result["status"] = "revoked"; result["revoked_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat(); _db.set("API_TOKENS", rows)
            result = {key: value for key, value in result.items() if key != "hash"}
        elif action == "sandbox":
            bot_id = str(body.get("bot_id", "")).strip()
            if not bot_id: raise ValueError("bot_id obligatorio")
            result = engine.sandbox(bot_id, body.get("enabled", True))
        elif action == "quota":
            bot_id, method = str(body.get("bot_id", "")).strip(), str(body.get("method", "")).strip()
            if not bot_id or not method: raise ValueError("bot y método son obligatorios")
            result = engine.quota(bot_id, method, body.get("used", 0), body.get("limit", 1), body.get("reset_at"))
        elif action == "config_export":
            group_id = str(body.get("group_id", ""))
            if group_id not in _known_internal_group_ids(): return jsonify({"ok": False, "error": "group_not_found"}), 404
            result = engine.signed_config({"group_id": group_id, "config": GroupSuite(_db).config(group_id),
                                           "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat()})
        elif action == "config_import":
            bundle = body.get("bundle") if isinstance(body.get("bundle"), dict) else {}
            if not engine.verify_config(bundle): raise ValueError("firma de configuración inválida")
            payload = bundle.get("payload") or {}; group_id = str(payload.get("group_id", ""))
            if group_id not in _known_internal_group_ids() or not isinstance(payload.get("config"), dict):
                raise ValueError("grupo o configuración no válidos")
            result = {"group_id": group_id, "config": GroupSuite(_db).save_config(group_id, payload["config"])}
        elif action == "incident_link":
            group_id = str(body.get("group_id", ""))
            if group_id not in _known_internal_group_ids(): return jsonify({"ok": False, "error": "group_not_found"}), 404
            result = engine.incident_link(body.get("provider", "custom"), body.get("external_id", ""), group_id, body.get("title", ""))
        elif action == "calendar_link":
            group_id = str(body.get("group_id", ""))
            if group_id not in _known_internal_group_ids(): return jsonify({"ok": False, "error": "group_not_found"}), 404
            result = engine.calendar_link(body.get("provider", "custom"), body.get("calendar_id", ""), group_id, body.get("sync_token"))
            result = {key: value for key, value in result.items() if key != "sync_token"}
        else: return jsonify({"ok": False, "error": "invalid_action"}), 400
    except (TypeError, ValueError) as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    if _add_audit_log: _add_audit_log(f"TodoSobreAllTech integraciones: {action}")
    return jsonify({"ok": True, "result": result})


def _operations_metrics():
    if not psutil:
        return {"cpu": 0, "memory": 0, "disk": 0, "latency": 0}
    return {"cpu": psutil.cpu_percent(interval=0.05), "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage("C:" if os.name == "nt" else "/").percent, "latency": 0}


@bp.route("/api/internal/operations", methods=["GET", "POST"])
def internal_operations():
    """Planificación operativa; no ejecuta restauraciones ni despliegues destructivos."""
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    engine = RoadmapEngine(_db, _jwt_secret or "moonbot")
    if request.method == "GET":
        metrics = _operations_metrics(); dependencies = _db.get("OPS_DEPENDENCIES", {}) or {}
        dependency_states = {name: row.get("status", "unknown") for name, row in dependencies.items() if isinstance(row, dict)}
        errors = _safe_list(_db.get("SYSTEM_ERRORS", []))[-500:]
        return jsonify({"ok": True, "metrics": metrics, "alerts": engine.resource_alerts(metrics),
                        "diagnosis": engine.diagnose(metrics, [row.get("message", row) if isinstance(row, dict) else row for row in errors]),
                        "error_groups": engine.group_errors([row for row in errors if isinstance(row, dict)]),
                        "degraded": engine.degraded_mode(dependency_states),
                        "deployments": list(reversed(_safe_list(_db.get("OPS_DEPLOYMENTS", []))))[:100],
                        "backup_policy": _db.get("OPS_BACKUP_POLICY", {}),
                        "restore_plans": list(reversed(_safe_list(_db.get("OPS_RESTORE_PLANS", []))))[:100],
                        "dependencies": dependencies,
                        "maintenance": list(reversed(_safe_list(_db.get("OPS_MAINTENANCE_WINDOWS", []))))[:100]})
    body = request.json or {}; action = str(body.get("action", "")); result = None
    try:
        if action == "deployment":
            version = str(body.get("version", "")).strip(); instances = [str(x).strip()[:100] for x in (body.get("instances") or []) if str(x).strip()]
            if not version or not instances: raise ValueError("versión e instancias son obligatorias")
            result = engine.deployment(version, instances, body.get("batch_size", 1))
        elif action == "health_result":
            result = engine.health_result(body.get("deployment_id"), str(body.get("instance", "")), bool(body.get("healthy")))
            if not result: return jsonify({"ok": False, "error": "deployment_not_found"}), 404
        elif action == "backup_policy":
            result = engine.backup_policy(body.get("retention_days", 30), bool(body.get("encrypted", True)), body.get("modules") or ["all"])
        elif action == "restore_plan":
            if not str(body.get("backup_id", "")).strip(): raise ValueError("backup_id obligatorio")
            result = engine.restore_plan(body.get("backup_id"), body.get("groups") or [], body.get("modules") or [])
        elif action == "restore_cancel":
            rows = _safe_list(_db.get("OPS_RESTORE_PLANS", [])); result = next((x for x in rows if x.get("id") == body.get("plan_id")), None)
            if not result: return jsonify({"ok": False, "error": "restore_plan_not_found"}), 404
            result["status"] = "cancelled"; result["cancelled_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat(); _db.set("OPS_RESTORE_PLANS", rows)
        elif action == "dependency":
            status = str(body.get("status", "unknown"));
            if not str(body.get("name", "")).strip(): raise ValueError("nombre de dependencia obligatorio")
            if status not in ("ok", "healthy", "degraded", "offline", "unknown"): raise ValueError("estado de dependencia no válido")
            result = engine.dependency_status(body.get("name", ""), status, body.get("latency_ms"), body.get("detail", ""))
        elif action == "diagnose":
            result = engine.diagnose(body.get("metrics") or _operations_metrics(), body.get("errors") or [])
        elif action == "maintenance":
            result = engine.maintenance_window(body.get("starts_at"), body.get("ends_at"), body.get("modules") or [], body.get("message", ""))
        elif action == "maintenance_cancel":
            rows = _safe_list(_db.get("OPS_MAINTENANCE_WINDOWS", [])); result = next((x for x in rows if x.get("id") == body.get("window_id")), None)
            if not result: return jsonify({"ok": False, "error": "maintenance_not_found"}), 404
            result["status"] = "cancelled"; _db.set("OPS_MAINTENANCE_WINDOWS", rows)
        else: return jsonify({"ok": False, "error": "invalid_action"}), 400
    except (TypeError, ValueError) as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    if _add_audit_log: _add_audit_log(f"TodoSobreAllTech operaciones: {action}")
    return jsonify({"ok": True, "result": result})


def _experience_actions():
    return [
        {"id": "groups", "name": "Administrar grupos", "area": "Administración"},
        {"id": "users", "name": "Usuarios y baneos", "area": "Seguridad"},
        {"id": "security", "name": "Centro de seguridad", "area": "Seguridad"},
        {"id": "editorial", "name": "Centro editorial", "area": "Contenido"},
        {"id": "ai", "name": "Centro de inteligencia artificial", "area": "IA"},
        {"id": "automations", "name": "Automatizaciones", "area": "Operaciones"},
        {"id": "integrations", "name": "Integraciones y API", "area": "Operaciones"},
        {"id": "operations", "name": "Fiabilidad y mantenimiento", "area": "Operaciones"},
    ]


@bp.route("/api/internal/experience", methods=["GET", "POST"])
def internal_experience():
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    defaults = {"favorites": [], "compact": False, "font_scale": 100, "high_contrast": False,
                "reduced_motion": False, "widgets": ["summary", "groups", "security", "operations"],
                "tour_completed": False, "history": []}
    preferences = _db.get("WEB_ADMIN_EXPERIENCE", {}) or {}
    state = {**defaults, **preferences}
    if request.method == "GET":
        pending = []
        for key, label in (("REPORTS", "Informes pendientes"), ("BAN_APPEALS", "Apelaciones pendientes"),
                           ("JOIN_REQUESTS", "Solicitudes de acceso")):
            count = sum(not isinstance(row, dict) or row.get("status", "pending") in ("pending", "open", "new")
                        for row in _safe_list(_db.get(key, [])))
            if count: pending.append({"id": key.lower(), "title": label, "count": count, "read": False})
        themes = _db.get("WEB_GROUP_THEMES", {}) or {}
        return jsonify({"ok": True, "preferences": state, "themes": themes,
                        "notifications": pending, "actions": _experience_actions()})
    body = request.json or {}; action = str(body.get("action", "")); result = None
    if action == "preferences":
        allowed = {"favorites", "compact", "font_scale", "high_contrast", "reduced_motion", "widgets", "tour_completed", "history"}
        changes = {key: value for key, value in (body.get("preferences") or {}).items() if key in allowed}
        if "font_scale" in changes: changes["font_scale"] = max(80, min(140, int(changes["font_scale"])))
        if "favorites" in changes: changes["favorites"] = [str(x)[:50] for x in changes["favorites"]][:20]
        if "widgets" in changes: changes["widgets"] = [str(x)[:50] for x in changes["widgets"]][:20]
        if "history" in changes: changes["history"] = [x for x in changes["history"] if isinstance(x, dict)][-30:]
        state.update(changes); _db.set("WEB_ADMIN_EXPERIENCE", state); result = state
    elif action == "theme":
        group_id = str(body.get("group_id", "")); theme = str(body.get("theme", "default"))
        if group_id not in _known_internal_group_ids(): return jsonify({"ok": False, "error": "group_not_found"}), 404
        if theme not in ("default", "moon", "ocean", "forest", "sunset", "contrast"): return jsonify({"ok": False, "error": "invalid_theme"}), 400
        themes = _db.get("WEB_GROUP_THEMES", {}) or {}; themes[group_id] = theme; _db.set("WEB_GROUP_THEMES", themes)
        result = {"group_id": group_id, "theme": theme}
    else: return jsonify({"ok": False, "error": "invalid_action"}), 400
    if _add_audit_log: _add_audit_log(f"TodoSobreAllTech experiencia: {action}")
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
        channels = _admin_channel_union()
        shared = sum(len(row.get("bots") or []) > 1 for row in channels)
        instances = sorted({bot.get("username") for row in channels for bot in (row.get("bots") or []) if bot.get("username")})
        channels.sort(key=lambda row: str(row.get("name") or row.get("chat_id") or "").casefold())
        return jsonify({"ok": True, "channels": channels, "summary": {
            "unique_groups": len(channels), "shared_groups": shared,
            "instances": len(instances), "bot_usernames": instances,
        }})
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


def _house_ads_payload(placement=None):
    rows = _safe_list(_db.get("HOUSE_ADS", [])) if _db else []
    if placement:
        rows = [row for row in rows if row.get("enabled", True) and row.get("placement", "all") in ("all", placement)]
    return sorted(rows, key=lambda row: (-int(row.get("priority", 0) or 0), str(row.get("title", ""))))


def _official_house_ads():
    """Catálogo versionado que se instala automáticamente con Moonbot."""
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "official_house_ads.json")
    try:
        with open(path, "r", encoding="utf-8") as source:
            rows = json.load(source)
        return [row for row in rows if isinstance(row, dict) and row.get("id") and row.get("url")]
    except (OSError, TypeError, ValueError):
        return []


def _sync_master_channel_ads():
    """Mantiene campañas automáticas para los canales de Telegram del master."""
    if not _db or not _master_id:
        return {"ok": False, "error": "master_or_database_unavailable"}
    try:
        channels = _channel_stats.channels_for_admin(_master_id)
        rows = [row for row in _safe_list(_db.get("HOUSE_ADS", [])) if isinstance(row, dict)]
        existing = {str(row.get("source_chat_id")): row for row in rows if row.get("source") == "master_channel"}
        existing_official = {str(row.get("id")): row for row in rows if row.get("source") == "official_channel"}
        official_generated = []
        official_usernames = set()
        for seed in _official_house_ads():
            previous = existing_official.get(str(seed["id"]), {})
            username = str(seed.get("url", "")).rstrip("/").rsplit("/", 1)[-1].lower()
            if username: official_usernames.add(username)
            official_generated.append({
                **seed, **previous, "id": str(seed["id"]), "title": str(seed.get("title") or "Canal oficial")[:80],
                "description": str(seed.get("description") or "Canal oficial de ComunidadTelebots")[:800],
                "url": str(seed["url"])[:500], "image": previous.get("image", seed.get("image", "")),
                "placement": str(seed.get("placement", "all")), "cta": str(seed.get("cta", "Abrir"))[:24],
                "background": str(seed.get("background", "#eef7ff")), "foreground": str(seed.get("foreground", "#155f9b")),
                "accent": str(seed.get("accent", "#1982d1")), "priority": int(seed.get("priority", 50)),
                "enabled": previous.get("enabled", True), "approval_status": "approved", "automatic": True,
                "source": "official_channel", "source_chat_id": str(previous.get("source_chat_id") or ""),
                "submitted_by": str(_master_id), "starts_at": "", "ends_at": "", "max_clicks": 0,
                "goal_reached": False, "clicks": int(previous.get("clicks", 0) or 0),
                "impressions": int(previous.get("impressions", 0) or 0),
                "clicks_by_placement": dict(previous.get("clicks_by_placement") or {}),
                "impressions_by_placement": dict(previous.get("impressions_by_placement") or {}),
            })
        generated = []
        suppressed = set(str(value) for value in _safe_list(_db.get("HOUSE_ADS_SUPPRESSED_CHANNELS", [])))
        for channel in channels:
            if not isinstance(channel, dict):
                continue
            username = str(channel.get("username") or "").strip().lstrip("@")
            if channel.get("ctype") != "channel" or not re.fullmatch(r"[A-Za-z0-9_]{5,64}", username):
                continue
            if username.lower() in official_usernames:
                continue
            chat_id = str(channel.get("chat_id"))
            if chat_id in suppressed:
                continue
            previous = existing.get(chat_id, {})
            generated.append({
                **previous, "id": previous.get("id") or f"master-channel-{hashlib.sha256(chat_id.encode()).hexdigest()[:16]}",
                "title": str(channel.get("name") or f"@{username}")[:80],
                "description": str(channel.get("description") or "Canal oficial de la red ComunidadTelebots")[:800],
                "url": f"https://t.me/{username}", "image": previous.get("image", ""), "placement": "all",
                "cta": "Suscribirme", "background": previous.get("background", "#edfdf8"),
                "foreground": previous.get("foreground", "#123c35"), "accent": previous.get("accent", "#0f9f7a"),
                "starts_at": "", "ends_at": "", "approval_status": "approved", "submitted_by": str(_master_id),
                "max_clicks": 0, "goal_reached": False, "enabled": previous.get("enabled", True), "priority": 45,
                "clicks": int(previous.get("clicks", 0) or 0), "impressions": int(previous.get("impressions", 0) or 0),
                "clicks_by_placement": dict(previous.get("clicks_by_placement") or {}),
                "impressions_by_placement": dict(previous.get("impressions_by_placement") or {}),
                "source": "master_channel", "source_chat_id": chat_id, "automatic": True,
            })
        manual = [row for row in rows if row.get("source") not in ("master_channel", "official_channel")]
        _db.set("HOUSE_ADS", manual + official_generated + generated)
        return {"ok": True, "channels": len(generated) + len(official_generated), "official": len(official_generated)}
    except Exception as error:
        return {"ok": False, "error": str(error)[:200]}


def _house_ads_update(body):
    rows = _house_ads_payload()
    action, ad_id = body.get("action", "upsert"), str(body.get("id") or "")
    if action == "delete":
        removed = next((row for row in rows if str(row.get("id")) == ad_id), None)
        if removed and removed.get("source") == "master_channel":
            suppressed = set(str(value) for value in _safe_list(_db.get("HOUSE_ADS_SUPPRESSED_CHANNELS", [])))
            suppressed.add(str(removed.get("source_chat_id")))
            _db.set("HOUSE_ADS_SUPPRESSED_CHANNELS", sorted(suppressed))
        rows = [row for row in rows if str(row.get("id")) != ad_id]
    elif action in ("approve", "reject"):
        for row in rows:
            if str(row.get("id")) == ad_id:
                row["approval_status"] = "approved" if action == "approve" else "rejected"
                row["enabled"] = action == "approve"
    elif action == "clone":
        source = next((row for row in rows if str(row.get("id")) == ad_id), None)
        if not source: raise ValueError("campaña no encontrada")
        item = dict(source)
        item.update({"id": secrets.token_hex(8), "title": f"{source.get('title', 'Campaña')} (copia)"[:80],
                     "enabled": False, "approval_status": "pending", "clicks": 0, "impressions": 0,
                     "clicks_by_placement": {}, "impressions_by_placement": {}})
        rows.append(item)
    elif action == "click":
        for row in rows:
            if str(row.get("id")) == ad_id:
                row["clicks"] = int(row.get("clicks", 0) or 0) + 1
                place = str(body.get("placement") or "unknown"); by = dict(row.get("clicks_by_placement") or {}); by[place] = int(by.get(place, 0)) + 1; row["clicks_by_placement"] = by
                if int(row.get("max_clicks", 0) or 0) and row["clicks"] >= int(row["max_clicks"]):
                    row["enabled"] = False
                    row["goal_reached"] = True
    elif action == "impression":
        for row in rows:
            if str(row.get("id")) == ad_id:
                row["impressions"] = int(row.get("impressions", 0) or 0) + 1
                place = str(body.get("placement") or "unknown"); by = dict(row.get("impressions_by_placement") or {}); by[place] = int(by.get(place, 0)) + 1; row["impressions_by_placement"] = by
    elif action == "reset_metrics":
        for row in rows:
            if str(row.get("id")) == ad_id:
                row.update({"clicks": 0, "impressions": 0, "clicks_by_placement": {}, "impressions_by_placement": {}})
    else:
        raw = body.get("ad") or body
        url = str(raw.get("url") or "").strip()
        if not url.startswith(("https://", "tg://")): raise ValueError("enlace no válido")
        item = {"id": str(raw.get("id") or secrets.token_hex(8)), "title": str(raw.get("title") or "")[:80],
                "description": str(raw.get("description") or "")[:800], "url": url[:500],
                "image": str(raw.get("image") or "")[:500], "placement": str(raw.get("placement") or "all"),
                "cta": str(raw.get("cta") or "Abrir")[:24],
                "background": str(raw.get("background") or "#eef7ff")[:32],
                "foreground": str(raw.get("foreground") or "#155f9b")[:32],
                "accent": str(raw.get("accent") or "#1982d1")[:32],
                "starts_at": str(raw.get("starts_at") or "")[:40],
                "ends_at": str(raw.get("ends_at") or "")[:40],
                "approval_status": str(raw.get("approval_status") or "approved")[:16],
                "submitted_by": str(raw.get("submitted_by") or "")[:64],
                "max_clicks": max(0, int(raw.get("max_clicks", 0) or 0)),
                "goal_reached": bool(raw.get("goal_reached", False)),
                "enabled": bool(raw.get("enabled", True)), "priority": max(0, min(100, int(raw.get("priority", 50) or 0))),
                "clicks": int(raw.get("clicks", 0) or 0), "impressions": int(raw.get("impressions", 0) or 0),
                "clicks_by_placement": dict(raw.get("clicks_by_placement") or {}), "impressions_by_placement": dict(raw.get("impressions_by_placement") or {}),
                "source": str(raw.get("source") or "manual")[:32], "source_chat_id": str(raw.get("source_chat_id") or "")[:32],
                "automatic": bool(raw.get("automatic", False))}
        if item["placement"] not in ("all", "top", "right", "inline"): raise ValueError("ubicación no válida")
        if not item["title"]: raise ValueError("título obligatorio")
        rows = [row for row in rows if str(row.get("id")) != item["id"]] + [item]
    _db.set("HOUSE_ADS", rows)
    return _house_ads_payload()


@bp.route("/api/internal/house-ads", methods=["GET", "POST"])
def internal_house_ads():
    if not _internal_admin_authorized(): return jsonify({"ok": False, "error": "unauthorized"}), 401
    try:
        sync = _sync_master_channel_ads()
        if request.method == "POST": _house_ads_update(request.json or {})
        return jsonify({"ok": True, "ads": _house_ads_payload(), "channel_sync": sync})
    except (TypeError, ValueError) as error: return jsonify({"ok": False, "error": str(error)}), 400
    except Exception as error: return jsonify({"ok": False, "error": "house_ads_internal_error", "detail": str(error)[:200]}), 500


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
    bot = _get_bot_for_chat(chat_id)
    command_menu = bot.command_menu_preview(chat_id) if bot else None
    return jsonify({"ok": True, **_group_suite().snapshot(chat_id), "command_menu": command_menu})


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
    bot = _get_bot_for_chat(chat_id)
    if bot:
        bot.sync_command_menu(chat_id)
    return jsonify({"ok": True, "config": config})


@bp.route("/api/public/group/commands/sync", methods=["POST", "OPTIONS"])
def group_commands_sync():
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
    return jsonify({"ok": True, "command_menu": bot.sync_command_menu(chat_id)})


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


def _ad_tracking_text(ad, text, side, target_url):
    rendered = str(text or "").strip()
    if not rendered.startswith("🤝"):
        rendered = "🤝 Colaboración entre comunidades\n\n" + rendered
    if target_url:
        base = os.getenv("MOON_PUBLIC_URL", "https://cintiabot.todosobreall.tech").rstrip("/")
        rendered += f"\n\n[Más información]({base}/api/public/ads/click/{ad['id']}/{side})"
    return rendered


def _schedule_ad_pair(ad, user_id, to_ad, to_image, to_url, when):
    variants = []
    try:
        variants = json.loads(ad.get("variants") or "[]")
    except (TypeError, ValueError):
        pass
    origin_text = variants[hash(str(ad["id"])) % len(variants)] if variants else ad["from_ad"]
    _channel_stats.schedule_message(
        ad["to_chat"], _ad_tracking_text(ad, origin_text, "from", ad.get("from_url")), when,
        created_by=user_id, bot_token=_channel_stats.get_channel_bot_token(ad["to_chat"]),
        photo=ad.get("from_ad_image"), ad_id=ad["id"], ad_side="origin_to_partner",
    )
    _channel_stats.schedule_message(
        ad["from_chat"], _ad_tracking_text(ad, to_ad, "to", to_url), when,
        created_by=user_id, bot_token=_channel_stats.get_channel_bot_token(ad["from_chat"]),
        photo=to_image, ad_id=ad["id"], ad_side="partner_to_origin",
    )
    _channel_stats.update_ad(ad["id"], {"status": "accepted", "to_ad": to_ad,
                                         "to_ad_image": to_image or "", "to_url": to_url or "", "when": when})


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
    source = _channel_stats.get_channel_meta(chat_id) or {}
    policy = _group_suite().config(chat_id)["ad_exchange"]
    preferences = _channel_stats.partner_preferences(chat_id)
    if not policy["enabled"]:
        return jsonify({"ok": True, "partners": [], "disabled": True})
    out = []
    for candidate in _channel_stats.get_all_channels():
        if str(candidate["chat_id"]) == str(chat_id):
            continue
        preference = preferences.get(str(candidate["chat_id"]), "neutral")
        if preference == "blocked":
            continue
        destination_policy = _group_suite().config(candidate["chat_id"])["ad_exchange"]
        if not destination_policy["enabled"]:
            continue
        source_known = int(source.get("subscribers", 0) or 0)
        destination_known = int(candidate.get("subscribers", 0) or 0)
        source_size, destination_size = max(1, source_known), max(1, destination_known)
        ratio = max(source_size, destination_size) / min(source_size, destination_size)
        if source_known and destination_known and ratio > policy["max_size_ratio"]:
            continue
        same_category = bool(source.get("category") and source.get("category") == candidate.get("category"))
        size_score = (max(0, 40 - round(abs(source_size - destination_size) * 40 / max(source_size, destination_size)))
                      if source_known and destination_known else 15)
        score = 40 + size_score + (20 if same_category and policy["same_category_priority"] else 0)
        history = _channel_stats.ads_history(candidate["chat_id"], 100)
        completed = sum(1 for row in history if row.get("status") == "completed")
        declined = sum(1 for row in history if row.get("status") == "declined")
        failures = sum(int(row.get("failed_count", 0) or 0) for row in history)
        reputation = max(0, min(100, 70 + completed * 3 - declined * 2 - failures * 5))
        if preference == "favorite":
            score += 15
        out.append({"chat_id": candidate["chat_id"], "name": candidate["name"],
                    "username": candidate["username"], "subscribers": candidate["subscribers"],
                    "ctype": candidate["ctype"], "category": candidate.get("category"),
                    "match_score": min(100, score),
                    "match_reason": "socio favorito" if preference == "favorite" else ("misma categoría y audiencia similar" if same_category else "audiencia compatible"),
                    "favorite": preference == "favorite", "reputation": reputation,
                    "campaigns_completed": completed})
    out.sort(key=lambda item: (-item["match_score"], abs(int(item.get("subscribers") or 0) - int(source.get("subscribers") or 0))))
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
    from_url = (body.get("from_url") or "").strip()
    variants = body.get("variants") or []
    when = (body.get("when") or "").strip()
    if not (from_chat and to_chat and from_ad and when):
        return jsonify({"ok": False, "error": "faltan datos"}), 400
    if str(from_chat) == str(to_chat):
        return jsonify({"ok": False, "error": "origen y destino no pueden ser iguales"}), 400
    if len(from_ad) > 3500:
        return jsonify({"ok": False, "error": "el anuncio supera 3500 caracteres"}), 400
    if from_url and (urlparse(from_url).scheme not in ("http", "https") or not urlparse(from_url).netloc):
        return jsonify({"ok": False, "error": "enlace de campaña no válido"}), 400
    if not isinstance(variants, list) or len(variants) > 5 or any(not isinstance(item, str) or len(item) > 3500 for item in variants):
        return jsonify({"ok": False, "error": "las variantes no son válidas"}), 400
    if not (_is_master(user) or _channel_stats.is_user_admin_of(user.get("id"), from_chat)):
        return jsonify({"ok": False, "error": "no gestionas el canal de origen"}), 403
    source_policy = _group_suite().config(from_chat)["ad_exchange"]
    destination_policy = _group_suite().config(to_chat)["ad_exchange"]
    if not source_policy["enabled"] or not destination_policy["enabled"]:
        return jsonify({"ok": False, "error": "el intercambio de anuncios está desactivado en uno de los destinos"}), 409
    try:
        scheduled_at = datetime.datetime.fromisoformat(when.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return jsonify({"ok": False, "error": "fecha no válida"}), 400
    now = datetime.datetime.utcnow()
    if scheduled_at < now + datetime.timedelta(minutes=10) or scheduled_at > now + datetime.timedelta(days=30):
        return jsonify({"ok": False, "error": "programa el intercambio entre 10 minutos y 30 días"}), 400
    history = _channel_stats.ads_history(from_chat)
    pair = [row for row in history if {str(row.get("from_chat")), str(row.get("to_chat"))} == {str(from_chat), str(to_chat)}]
    if any(row.get("status") == "pending" for row in pair):
        return jsonify({"ok": False, "error": "ya existe una solicitud pendiente entre estos grupos"}), 409
    today = now.strftime("%Y-%m-%d")
    daily = sum(1 for row in history if str(row.get("created", "")).startswith(today) and row.get("status") in ("accepted", "completed"))
    if daily >= source_policy["max_daily"]:
        return jsonify({"ok": False, "error": "se alcanzó el límite diario de intercambios"}), 429
    week_start = now - datetime.timedelta(days=7)
    weekly = 0
    recent_failures = 0
    for row in history:
        try:
            created_at = datetime.datetime.fromisoformat(str(row.get("created", "")).replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            continue
        if created_at >= week_start and row.get("status") in ("accepted", "completed", "delivery_failed"):
            weekly += 1
            recent_failures += int(row.get("failed_count", 0) or 0)
    if weekly >= source_policy["max_weekly"]:
        return jsonify({"ok": False, "error": "se alcanzó el límite semanal de intercambios"}), 429
    if recent_failures >= source_policy["pause_after_failures"]:
        return jsonify({"ok": False, "error": "las campañas están pausadas por fallos recientes de entrega"}), 503
    recent = next((row for row in pair if row.get("status") in ("accepted", "completed")), None)
    if recent:
        try:
            created = datetime.datetime.fromisoformat(str(recent.get("created", "")).replace("Z", "+00:00")).replace(tzinfo=None)
            if now - created < datetime.timedelta(hours=source_policy["cooldown_hours"]):
                return jsonify({"ok": False, "error": "estos grupos siguen dentro del periodo de descanso"}), 429
        except ValueError:
            pass
    hit = _banned_hit(to_chat, from_ad)
    if hit:
        return jsonify({"ok": False, "error": f"El anuncio contiene una palabra no permitida en el canal destino: «{hit}»"}), 400
    fm = _channel_stats.get_channel_meta(from_chat) or {}
    tm = _channel_stats.get_channel_meta(to_chat) or {}
    sensitive_terms = ("casino", "apuestas", "inversión", "criptomoneda", "préstamo", "contenido adulto")
    master_review = not _is_master(user) and any(term in from_ad.lower() for term in sensitive_terms)
    if from_url and _vt_manager:
        scan = _vt_manager.scan_url(from_url, submit_if_unknown=False)
        if scan.get("ok") and (int(scan.get("malicious", 0) or 0) > 0 or int(scan.get("suspicious", 0) or 0) > 1):
            return jsonify({"ok": False, "error": "VirusTotal considera peligroso el enlace del anuncio"}), 400
    rec = _channel_stats.create_ad_request(from_chat, user.get("id"), fm.get("name"),
                                           to_chat, tm.get("name"), from_ad, when,
                                           from_image=(body.get("from_image") or "").strip(),
                                           from_url=from_url, variants=json.dumps(variants, ensure_ascii=False),
                                           status="master_review" if master_review else "pending")
    return jsonify({"ok": True, "id": rec.get("id"), "status": "master_review" if master_review else "pending"})


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
            "when": r.get("when"), "status": r.get("status"),
            "delivered_count": int(r.get("delivered_count", 0) or 0),
            "failed_count": int(r.get("failed_count", 0) or 0), "clicks": int(r.get("clicks", 0) or 0),
            "last_error": r.get("last_error"), "counter_when": r.get("counter_when"),
            "counter_ad": r.get("counter_ad")} for r in rows]
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
    to_url = (body.get("to_url") or "").strip()
    if to_url and (urlparse(to_url).scheme not in ("http", "https") or not urlparse(to_url).netloc):
        return jsonify({"ok": False, "error": "enlace recíproco no válido"}), 400
    hit = _banned_hit(ad.get("from_chat"), to_ad)
    if hit:
        return jsonify({"ok": False, "error": f"Tu anuncio contiene una palabra no permitida en el canal destino: «{hit}»"}), 400
    when = ad.get("when")
    _schedule_ad_pair(ad, user.get("id"), to_ad, to_image, to_url, when)
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


@bp.route("/api/public/ads/preview", methods=["POST", "OPTIONS"])
def ads_preview():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}
    user, err = _auth_user(body)
    if err: return err
    text = str(body.get("text") or "").strip()
    if not text or len(text) > 3500:
        return jsonify({"ok": False, "error": "texto no válido"}), 400
    fake = {"id": "preview"}
    return jsonify({"ok": True, "rendered": _ad_tracking_text(fake, text, "preview", body.get("target_url")),
                    "characters": len(text), "has_image": bool(body.get("image")),
                    "label_added": not text.startswith("🤝")})


@bp.route("/api/public/ads/cancel", methods=["POST", "OPTIONS"])
def ads_cancel():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}; user, err = _auth_user(body)
    if err: return err
    ad = _channel_stats.get_ad(body.get("id"))
    if not ad: return jsonify({"ok": False, "error": "campaña no encontrada"}), 404
    if not (_is_master(user) or _channel_stats.is_user_admin_of(user.get("id"), ad.get("from_chat"))):
        return jsonify({"ok": False, "error": "sin permiso"}), 403
    if ad.get("status") not in ("pending", "countered", "master_review"):
        return jsonify({"ok": False, "error": "la campaña ya no se puede cancelar"}), 409
    _channel_stats.update_ad(ad["id"], {"status": "cancelled"})
    return jsonify({"ok": True})


@bp.route("/api/public/ads/counter", methods=["POST", "OPTIONS"])
def ads_counter():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}; user, err = _auth_user(body)
    if err: return err
    ad = _channel_stats.get_ad(body.get("id"))
    if not ad: return jsonify({"ok": False, "error": "campaña no encontrada"}), 404
    if not (_is_master(user) or _channel_stats.is_user_admin_of(user.get("id"), ad.get("to_chat"))):
        return jsonify({"ok": False, "error": "sin permiso"}), 403
    counter_ad = str(body.get("to_ad") or "").strip()
    counter_when = str(body.get("when") or "").strip()
    counter_url = str(body.get("to_url") or "").strip()
    if not counter_ad or not counter_when:
        return jsonify({"ok": False, "error": "faltan contrapropuesta y fecha"}), 400
    if len(counter_ad) > 3500 or _banned_hit(ad.get("from_chat"), counter_ad):
        return jsonify({"ok": False, "error": "el texto de la contrapropuesta no está permitido"}), 400
    if counter_url and (urlparse(counter_url).scheme not in ("http", "https") or not urlparse(counter_url).netloc):
        return jsonify({"ok": False, "error": "enlace no válido"}), 400
    try:
        proposed_at = datetime.datetime.fromisoformat(counter_when.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return jsonify({"ok": False, "error": "fecha no válida"}), 400
    if proposed_at < datetime.datetime.utcnow() + datetime.timedelta(minutes=10) or proposed_at > datetime.datetime.utcnow() + datetime.timedelta(days=30):
        return jsonify({"ok": False, "error": "fecha fuera del intervalo permitido"}), 400
    _channel_stats.update_ad(ad["id"], {"status": "countered", "counter_ad": counter_ad,
        "counter_when": counter_when, "counter_image": str(body.get("to_image") or ""),
        "counter_url": counter_url})
    return jsonify({"ok": True})


@bp.route("/api/public/ads/counter/accept", methods=["POST", "OPTIONS"])
def ads_counter_accept():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}; user, err = _auth_user(body)
    if err: return err
    ad = _channel_stats.get_ad(body.get("id"))
    if not ad or ad.get("status") != "countered":
        return jsonify({"ok": False, "error": "contrapropuesta no disponible"}), 404
    if not (_is_master(user) or _channel_stats.is_user_admin_of(user.get("id"), ad.get("from_chat"))):
        return jsonify({"ok": False, "error": "sin permiso"}), 403
    _schedule_ad_pair(ad, user.get("id"), ad.get("counter_ad"), ad.get("counter_image"),
                      ad.get("counter_url"), ad.get("counter_when"))
    return jsonify({"ok": True})


@bp.route("/api/public/ads/master/approve", methods=["POST", "OPTIONS"])
def ads_master_approve():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}; user, err = _auth_user(body)
    if err: return err
    if not _is_master(user): return jsonify({"ok": False, "error": "solo master"}), 403
    ad = _channel_stats.get_ad(body.get("id"))
    if not ad or ad.get("status") != "master_review": return jsonify({"ok": False, "error": "revisión no disponible"}), 404
    _channel_stats.update_ad(ad["id"], {"status": "pending", "approved_by_master": True})
    return jsonify({"ok": True})


@bp.route("/api/public/ads/master/review", methods=["POST", "OPTIONS"])
def ads_master_review():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}; user, err = _auth_user(body)
    if err: return err
    if not _is_master(user): return jsonify({"ok": False, "error": "solo master"}), 403
    rows = _channel_stats.ads_master_review()
    return jsonify({"ok": True, "ads": [{"id": row["id"], "from_name": row.get("from_name"),
        "to_name": row.get("to_name"), "from_ad": row.get("from_ad"), "when": row.get("when")} for row in rows]})


@bp.route("/api/public/ads/partner-preference", methods=["POST", "OPTIONS"])
def ads_partner_preference():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}; user, err = _auth_user(body)
    if err: return err
    chat_id, partner = body.get("chat_id"), body.get("partner_chat")
    if not (_is_master(user) or _channel_stats.is_user_admin_of(user.get("id"), chat_id)):
        return jsonify({"ok": False, "error": "sin permiso"}), 403
    if not _channel_stats.set_partner_preference(chat_id, partner, body.get("status"), user.get("id")):
        return jsonify({"ok": False, "error": "preferencia no válida"}), 400
    return jsonify({"ok": True})


@bp.route("/api/public/ads/templates", methods=["POST", "OPTIONS"])
def ads_templates():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}; user, err = _auth_user(body)
    if err: return err
    chat_id = body.get("chat_id")
    if not (_is_master(user) or _channel_stats.is_user_admin_of(user.get("id"), chat_id)):
        return jsonify({"ok": False, "error": "sin permiso"}), 403
    if body.get("operation") == "save":
        text = str(body.get("text") or "").strip(); name = str(body.get("name") or "").strip()
        if not text or not name: return jsonify({"ok": False, "error": "nombre y texto requeridos"}), 400
        target_url = str(body.get("target_url") or "").strip()
        if target_url and (urlparse(target_url).scheme not in ("http", "https") or not urlparse(target_url).netloc):
            return jsonify({"ok": False, "error": "enlace no válido"}), 400
        _channel_stats.save_ad_template(chat_id, name[:80], text[:3500], body.get("image"), target_url, user.get("id"))
    rows = _channel_stats.ad_templates(chat_id)
    return jsonify({"ok": True, "templates": [{"id": row["id"], "name": row.get("name"), "text": row.get("text"), "image": row.get("image"), "target_url": row.get("target_url")} for row in rows]})


@bp.route("/api/public/ads/recommended-slots", methods=["POST", "OPTIONS"])
def ads_recommended_slots():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}; _, err = _group_auth(body)
    if err: return err
    now = datetime.datetime.utcnow()
    candidates = []
    for day in range(1, 5):
        for hour in (12, 18, 21):
            value = (now + datetime.timedelta(days=day)).replace(hour=hour, minute=0, second=0, microsecond=0)
            candidates.append({"when": value.isoformat() + "Z", "score": 92 if hour == 21 else 84 if hour == 18 else 72,
                               "reason": "franja de mayor actividad estimada" if hour in (18, 21) else "franja alternativa"})
    return jsonify({"ok": True, "slots": sorted(candidates, key=lambda row: -row["score"])[:6]})


@bp.route("/api/public/ads/report/<ad_id>", methods=["POST", "OPTIONS"])
def ads_report(ad_id):
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}; user, err = _auth_user(body)
    if err: return err
    ad = _channel_stats.get_ad(ad_id)
    if not ad: return jsonify({"ok": False, "error": "campaña no encontrada"}), 404
    if not (_is_master(user) or _channel_stats.is_user_admin_of(user.get("id"), ad.get("from_chat")) or _channel_stats.is_user_admin_of(user.get("id"), ad.get("to_chat"))):
        return jsonify({"ok": False, "error": "sin permiso"}), 403
    return jsonify({"ok": True, "report": {"status": ad.get("status"), "deliveries": int(ad.get("delivered_count", 0) or 0),
        "failures": int(ad.get("failed_count", 0) or 0), "clicks": int(ad.get("clicks", 0) or 0),
        "scheduled_at": ad.get("when"), "last_delivery": ad.get("last_delivery"), "last_error": ad.get("last_error")}})


@bp.route("/api/public/ads/click/<ad_id>/<side>", methods=["GET"])
def ads_click(ad_id, side):
    ad = _channel_stats.get_ad(ad_id)
    if not ad: return redirect("https://todosobreall.tech", code=302)
    target = ad.get("from_url") if side == "from" else ad.get("to_url")
    _channel_stats.update_ad(ad_id, {"clicks": int(ad.get("clicks", 0) or 0) + 1})
    parsed = urlparse(str(target or ""))
    safe_target = target if parsed.scheme in ("http", "https") and parsed.netloc else "https://todosobreall.tech"
    return redirect(safe_target, code=302)


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
    required = raw.get("required_channels") or []
    if not isinstance(required, list):
        required = [required]
    exempt = raw.get("exempt_user_ids") or []
    if not isinstance(exempt, list):
        exempt = [exempt]
    return {
        "enabled": bool(raw.get("enabled", True)),
        "mute_until_verified": bool(raw.get("mute_until_verified", True)),
        "strict_enforcement": bool(raw.get("strict_enforcement", False)),
        "max_attempts": _bounded_int(raw.get("max_attempts"), 3, 1, 10),
        "challenge_ttl": _bounded_int(raw.get("challenge_ttl"), 120, 30, 600),
        "request_ttl": _bounded_int(raw.get("request_ttl"), 86400, 300, 604800),
        "reverify_interval_days": _bounded_int(raw.get("reverify_interval_days"), 0, 0, 90),
        "exempt_user_ids": [str(value).strip() for value in exempt if str(value).strip().isdigit()][:100],
        "required_channels": [str(value).strip().lstrip("@")[:100] for value in required if str(value).strip()][:1],
    }


def _global_join_channel():
    value = _db.get("JOIN_GLOBAL_REQUIRED_CHANNEL", "") if _db else ""
    channel = str(value or "").strip().lstrip("@")[:100]
    enabled = bool(_db.get("JOIN_GLOBAL_REQUIRED_ENABLED", bool(channel))) if _db else False
    return channel if enabled else ""


def _global_join_settings():
    value = _db.get("JOIN_GLOBAL_REQUIRED_CHANNEL", "") if _db else ""
    channel = str(value or "").strip().lstrip("@")[:100]
    enabled = bool(_db.get("JOIN_GLOBAL_REQUIRED_ENABLED", bool(channel))) if _db else False
    strict_enforcement = bool(_db.get("JOIN_GLOBAL_STRICT_ENFORCEMENT", False)) if _db else False
    return {"enabled": enabled, "channel": channel, "strict_enforcement": strict_enforcement}


def _set_join_member_muted(bot, chat_id, user_id, muted):
    """Aplica o retira el bloqueo de Telegram usando todos los permisos modernos."""
    if hasattr(bot, "restrict_user"):
        return bot.restrict_user(chat_id, user_id, can_send=not muted)
    allowed = not muted
    permissions = {name: allowed for name in (
        "can_send_messages", "can_send_audios", "can_send_documents", "can_send_photos",
        "can_send_videos", "can_send_video_notes", "can_send_voice_notes", "can_send_polls",
        "can_send_other_messages", "can_add_web_page_previews",
    )}
    return bot.api_call("restrictChatMember", {
        "chat_id": chat_id, "user_id": user_id, "permissions": permissions,
    }, silent=True)


@bp.route("/api/public/admin/join-global", methods=["POST", "OPTIONS"])
def admin_join_global():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData inválido"}), 401
    if not _is_master(user):
        return jsonify({"ok": False, "error": "solo el master puede cambiar el acceso global"}), 403
    if "channel" in body:
        channel = str(body.get("channel") or "").strip().lstrip("@")[:100]
        _db.set("JOIN_GLOBAL_REQUIRED_CHANNEL", channel)
    settings = _global_join_settings()
    if "enabled" in body:
        enabled = bool(body.get("enabled"))
        if enabled and not settings["channel"]:
            return jsonify({"ok": False, "error": "configura primero un canal"}), 400
        _db.set("JOIN_GLOBAL_REQUIRED_ENABLED", enabled)
    if "strict_enforcement" in body:
        _db.set("JOIN_GLOBAL_STRICT_ENFORCEMENT", bool(body.get("strict_enforcement")))
    return jsonify({"ok": True, **_global_join_settings()})


def _missing_required_channels(bot, chat_id, user_id):
    missing = []
    group_channels = _join_config(chat_id)["required_channels"][:1]
    global_channel = _global_join_channel()
    channels = [(channel, "group") for channel in group_channels]
    if global_channel and global_channel not in group_channels:
        channels.append((global_channel, "global"))
    for channel, scope in channels:
        target = channel if channel.startswith("-100") else f"@{channel}"
        result = bot.api_call("getChatMember", {"chat_id": target, "user_id": user_id}, silent=True)
        member = result.get("result", {}) if isinstance(result, dict) and result.get("ok") else {}
        status = member.get("status")
        joined = status in ("member", "administrator", "creator") or (
            status == "restricted" and bool(member.get("is_member"))
        )
        if not joined:
            missing.append({"channel": channel, "scope": scope,
                            "url": f"https://t.me/{channel}" if not channel.startswith("-100") else ""})
    return missing


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
            if item.get("admitted"):
                bot = _hub_bot()
                if bot:
                    bot.api_call("banChatMember", {"chat_id": chat_id, "user_id": item.get("user_id")}, silent=True)
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
            "telegram_muted": bool(item.get("telegram_muted")),
            "cas_flagged": bool(item.get("cas_flagged")),
            "cas_offenses": item.get("cas_offenses"),
            "community_flagged": bool(item.get("community_flagged")),
            "community_reason": item.get("community_reason"),
        })
    pending.sort(key=lambda item: item.get("created_at") or 0, reverse=True)
    return jsonify({"ok": True, "config": _join_config(chat_id),
                    "global_required_channel": _global_join_channel(),
                    "global_strict_enforcement": _global_join_settings()["strict_enforcement"],
                    "can_manage_global": _is_master(res[0]),
                    "stats": _join_stats(chat_id), "pending": pending,
                    "bulk_job": _db.get(f"JOIN_BULK_JOB_{chat_id}", {}),
                    "bulk_last_run": int(_db.get(f"JOIN_BULK_LAST_{chat_id}", 0) or 0),
                    "bulk_history": list(reversed(_safe_list(_db.get(f"JOIN_BULK_HISTORY_{chat_id}", []))))[:10]})


@bp.route("/api/public/group/join/reverify-all", methods=["POST", "OPTIONS"])
def group_join_reverify_all():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    user, chat_id = res
    bot = _hub_bot()
    if not bot:
        return jsonify({"ok": False, "error": "bot no disponible"}), 503
    job, started = _start_bulk_captcha(bot, chat_id, user.get("id"))
    return jsonify({"ok": True, "started": started, "job": job})


@bp.route("/api/public/group/join/reverify-control", methods=["POST", "OPTIONS"])
def group_join_reverify_control():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    action = body.get("action")
    job_key = f"JOIN_BULK_JOB_{chat_id}"
    if action == "preview":
        observed = _db.get(f"TELEGRAM_GROUP_LANGUAGES_{chat_id}", {}) or {}
        return jsonify({"ok": True, "preview": {"observed": len(observed),
            "note": "Antes de silenciar se excluirán administradores, bots y usuarios que ya no pertenezcan al grupo."}})
    if action == "cancel":
        job = _db.get(job_key, {}) or {}
        if job.get("status") == "running":
            job["status"] = "cancel_requested"
            _db.set(job_key, job)
        return jsonify({"ok": True, "job": job})
    return jsonify({"ok": False, "error": "acción no válida"}), 400


@bp.route("/api/public/group/join/settings", methods=["POST", "OPTIONS"])
def group_join_settings():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    if "global_required_channel" in body and not _is_master(res[0]):
        return jsonify({"ok": False, "error": "solo el master puede cambiar el canal global"}), 403
    config = _join_config(chat_id)
    for key in ("enabled", "mute_until_verified", "strict_enforcement", "max_attempts", "challenge_ttl", "request_ttl", "reverify_interval_days", "exempt_user_ids", "required_channels"):
        if key in body:
            config[key] = body[key]
    required = config.get("required_channels") or []
    if not isinstance(required, list):
        required = [required]
    exempt = config.get("exempt_user_ids") or []
    if not isinstance(exempt, list):
        exempt = [exempt]
    config = {
        "enabled": bool(config["enabled"]),
        "mute_until_verified": bool(config["mute_until_verified"]),
        "strict_enforcement": bool(config["strict_enforcement"]),
        "max_attempts": _bounded_int(config["max_attempts"], 3, 1, 10),
        "challenge_ttl": _bounded_int(config["challenge_ttl"], 120, 30, 600),
        "request_ttl": _bounded_int(config["request_ttl"], 86400, 300, 604800),
        "reverify_interval_days": _bounded_int(config["reverify_interval_days"], 0, 0, 90),
        "exempt_user_ids": [str(value).strip() for value in exempt if str(value).strip().isdigit()][:100],
        "required_channels": [str(value).strip().lstrip("@")[:100] for value in required if str(value).strip()][:1],
    }
    _db.set(f"JOINCFG_{chat_id}", config)
    if "global_required_channel" in body:
        global_channel = str(body.get("global_required_channel") or "").strip().lstrip("@")[:100]
        _db.set("JOIN_GLOBAL_REQUIRED_CHANNEL", global_channel)
        _db.set("JOIN_GLOBAL_REQUIRED_ENABLED", bool(global_channel))
    return jsonify({"ok": True, "config": config,
                    "global_required_channel": _global_join_channel()})


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
        missing = _missing_required_channels(bot, chat_id, user_id)
        if missing:
            return jsonify({
                "ok": False,
                "error": "El usuario aún no está suscrito a todos los canales obligatorios",
                "code": "subscription_required",
                "missing_channels": missing,
            }), 409
        result = (_set_join_member_muted(bot, chat_id, user_id, False) if pending.get("admitted")
                  else bot.api_call("answerChatJoinRequestQuery", {"query_id": pending.get("query_id")}))
        stat = "approved"
    else:
        result = (bot.api_call("banChatMember", {"chat_id": chat_id, "user_id": user_id}) if pending.get("admitted")
                  else bot.api_call("declineChatJoinRequest", {"chat_id": chat_id, "user_id": user_id}))
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
    if pend.get("captcha_passed") and pend.get("subscription_pending"):
        missing = _missing_required_channels(_hub_bot(), cid, uid) if _hub_bot() else []
        if missing:
            return jsonify({"ok": False, "subscription_required": True, "missing_channels": missing}), 423
        return jsonify({"ok": True, "resume": True})
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
    if not body.get("resume") and (not chal or chal.get("exp", 0) < time.time()):
        return jsonify({"ok": False, "expired": True, "error": "reto expirado"})
    try:
        sel = sorted(int(i) for i in (body.get("selected") or []))
    except (TypeError, ValueError):
        sel = []
    bot = _hub_bot()
    if not bot:
        return jsonify({"ok": False, "error": "bot no disponible"}), 503
    config = _join_config(cid)
    # ── ÉXITO ──
    resumed = bool(body.get("resume") and pend.get("captcha_passed"))
    if resumed or (sel and sel == sorted(chal.get("correct", []))):
        missing = _missing_required_channels(bot, cid, uid)
        if missing:
            pend["captcha_passed"] = True
            pend["subscription_pending"] = True
            _db.set(f"JOINQ_{cid}_{uid}", pend); _db.delete(f"JOINC_{cid}_{uid}")
            return jsonify({"ok": False, "subscription_required": True, "missing_channels": missing}), 423
        pend.pop("subscription_pending", None)
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
            result = (_set_join_member_muted(bot, cid, uid, False) if pend.get("admitted")
                      else bot.api_call("answerChatJoinRequestQuery", {"query_id": pend.get("query_id")}))
            if isinstance(result, dict) and not result.get("ok", False):
                pend["permission_restore_error"] = result.get("description", "Telegram rechazó la restauración")
                _db.set(f"JOINQ_{cid}_{uid}", pend)
                return jsonify({"ok": False, "error": "captcha superado, pero no se pudieron restaurar los permisos"}), 502
        _db.delete(f"JOINC_{cid}_{uid}"); _db.delete(f"JOINQ_{cid}_{uid}")  # query_id de un solo uso
        _bump_join_stat(cid, "approved")
        return jsonify({"ok": True, "approved": True})
    # ── FALLO ──
    attempts = int(pend.get("attempts", 0)) + 1
    _db.delete(f"JOINC_{cid}_{uid}")  # fuerza reto nuevo (no resetea intentos)
    if attempts >= config["max_attempts"]:
        if bot:
            if pend.get("admitted"):
                bot.api_call("banChatMember", {"chat_id": cid, "user_id": uid})
            else:
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
    chat_id = str(request.args.get("chat_id") or "").strip()
    key = f"TELEGRAM_GROUP_LANGUAGES_{chat_id}" if chat_id else "TELEGRAM_USER_LANGUAGES"
    data = aggregate_language_map(_db.get(key, {}) if _db else {})
    data["scope"] = "group" if chat_id else "all_groups"
    if chat_id:
        data["chat_id"] = chat_id
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
    """Devuelve proxies MTProto activos, usando el catálogo de red como respaldo."""
    limit = max(1, min(10, request.args.get("limit", 5, type=int)))
    try:
        vps = _proxy_mgr.get_vps_config(include_secret=True) or {} if _proxy_mgr else {}
    except Exception:
        vps = {}
    host = vps.get("host")
    candidates = []
    for p in getattr(_proxy_mgr, "proxies", []) or [] if _proxy_mgr else []:
        port, secret = p.get("port"), p.get("secret")
        if host and port and secret:
            candidates.append({
                "server": host,
                "port": port,
                "secret": secret,
                "tg_link": f"tg://proxy?server={host}&port={port}&secret={secret}",
                "https_link": f"https://t.me/proxy?server={host}&port={port}&secret={secret}",
                "tag": p.get("tag", ""),
                "source": "moonbot",
                "status": "online",
            })
    if not candidates:
        upstream = os.environ.get("MTPROTO_PROXY_API", "http://api:3001/mtproto-proxies")
        try:
            suffix = "&refresh=1" if request.args.get("refresh") == "1" and "?" in upstream else "?refresh=1" if request.args.get("refresh") == "1" else ""
            with urllib.request.urlopen(upstream + suffix, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
            rows = payload.get("proxies", []) if isinstance(payload, dict) else []
            rows.sort(key=lambda p: (p.get("source") != "own", p.get("status") != "online", p.get("pingMs") is None, p.get("pingMs") or 999999))
            for p in rows:
                server, port, secret = p.get("server"), p.get("port"), p.get("secret")
                if not server or not port or not secret or p.get("status") == "offline":
                    continue
                link = p.get("link") or f"tg://proxy?server={server}&port={port}&secret={secret}"
                candidates.append({
                    "server": server, "port": port, "secret": secret,
                    "tg_link": link,
                    "https_link": link.replace("tg://proxy", "https://t.me/proxy", 1),
                    "tag": p.get("name") or p.get("country") or "MTProto",
                    "source": p.get("source", "network"), "status": p.get("status", "online"),
                    "ping_ms": p.get("pingMs"), "country": p.get("country"),
                })
                if len(candidates) >= limit:
                    break
        except (OSError, ValueError, urllib.error.URLError) as exc:
            return jsonify({"ok": False, "error": "catálogo de proxies no disponible", "detail": str(exc)[:160]}), 502
    if not candidates:
        return jsonify({"ok": False, "error": "sin proxies activos configurados"}), 404
    return jsonify({"ok": True, "count": len(candidates[:limit]), "proxies": candidates[:limit]})


@bp.route("/api/public/house-ads/manage", methods=["POST", "OPTIONS"])
def public_house_ads_manage():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}; user = _verify_init_data(body.get("initData", ""))
    if user is None or not _is_master(user): return jsonify({"ok": False, "error": "solo master"}), 403
    try:
        _sync_master_channel_ads()
        if body.get("action") and body.get("action") != "list": _house_ads_update(body)
        return jsonify({"ok": True, "ads": _house_ads_payload()})
    except (TypeError, ValueError) as error: return jsonify({"ok": False, "error": str(error)}), 400

"""
routes_public.py â€” Endpoints PÃšBLICOS (sin JWT) del hub.

Zona pÃºblica del panel: estadÃ­sticas de canales y obtenciÃ³n de proxy MTProto.
Solo lectura / acciones seguras. Todo lo administrativo sigue en sus blueprints
protegidos por check_jwt.

CORS abierto para que canales.todosobreall.tech (y el propio panel) puedan
consumir la API desde el navegador.
"""
import os
import requests
import hmac
import hashlib
import html
import json
import datetime
import os
import math
import time
import threading
import secrets
import re
import ipaddress
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from urllib.parse import parse_qsl, urlparse

import jwt
from flask import Blueprint, Response, current_app, request, jsonify, redirect

try:
    import psutil
except ImportError:  # pragma: no cover - la imagen oficial incluye psutil
    psutil = None

from . import image_gen
from spam_risk import SpamRiskEngine
from group_suite import GroupSuite
from group_rss import GroupRssManager
from community_members import CommunityMembers
from community_engagement import CommunityEngagement
from roadmap_engine import RoadmapEngine
from horizon_full import FullHorizonSuite
from horizon_completion import HorizonCompletion, FEATURES as HORIZON_COMPLETION_FEATURES
from permission_history import record_permission_snapshot
from core.language_map import aggregate_language_map
from core.feature_runtime import execute as execute_verified_feature, list_features as list_verified_features, registry as verified_feature_registry
from core.feature_access import normalize_release_channel
from core.config import APP_VERSION
from core.hub_release_assets import read_hub_release_asset
from core.release_channels import ensure_schema as ensure_release_schema, list_assignments as list_release_assignments, assign as assign_release_channel, revoke as revoke_release_channel
from core.pb_client import PBError
from plugins.todo_manager import add_task, list_tasks, update_task
from plugins.url_tools import inspect_url
from core.moderation_insights import build_snapshot, compare_snapshots, diagnose, signed_export

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
_game_stats_lock = threading.RLock()
_game_stats = {"events": [], "players": {}}
_game_stats_file = os.environ.get("MOON_GAME_STATS_FILE", "/app/data/game-analytics.json")

def _load_game_stats():
    try:
        with open(_game_stats_file, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict) and isinstance(data.get("events"), list) and isinstance(data.get("players"), dict):
            _game_stats.update({"events": data["events"][-25000:], "players": data["players"]})
    except (OSError, ValueError, TypeError):
        pass

def _save_game_stats():
    try:
        directory = os.path.dirname(_game_stats_file); os.makedirs(directory, exist_ok=True)
        temporary = f"{_game_stats_file}.tmp"
        with open(temporary, "w", encoding="utf-8") as handle: json.dump(_game_stats, handle, ensure_ascii=False, separators=(",", ":"))
        os.replace(temporary, _game_stats_file)
    except OSError:
        current_app.logger.warning("No se pudieron persistir las estadÃ­sticas de MoonJuegos")

_load_game_stats()
_get_global_user_stats = None
_get_global_chat_names = None
_get_cas_export_status = None
_add_audit_log = None
_vt_manager = None
_get_ai_runtime_config = None
_set_ai_runtime_config = None
_task_queue = None
_group_administration = None
_tdlib_client = None
_community_api_usage = {}
_instant_news_cache = {"at": 0, "articles": []}
_instant_channel_cache = {}
_community_campaign_cache = {}
_royale_lock = threading.Lock()
_royale_rooms = {}
_convoy_lock = threading.Lock()
_convoy_rooms = {}
_NOTICIAS_API_ENDPOINTS = tuple(dict.fromkeys((
    os.environ.get("NOTICIAS_API_INTERNAL_URL", "http://todosobrealltech-api:3001").rstrip("/"),
    "https://api.todosobreall.tech",
)))


def _noticias_api_read(path, *, data=None, timeout=12, limit=2 * 1024 * 1024):
    last_error = None
    for endpoint in _NOTICIAS_API_ENDPOINTS:
        try:
            headers = {"User-Agent": "MoonMultibot-InstantNews/1.0"}
            if data is not None:
                headers["Content-Type"] = "application/json"
            req = urllib.request.Request(endpoint + path, data=data, headers=headers,
                                         method="POST" if data is not None else "GET")
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read(limit)
        except Exception as exc:
            last_error = exc
    raise last_error or RuntimeError("NoticiasWeb3 API unavailable")


def _royale_advance(room, now):
    dt = min(max(now - float(room.get("updated", now)), 0), 0.5)
    room["updated"] = now
    elapsed = now - room["started"]
    room["zone"] = max(90.0, 370.0 - elapsed * 1.35)
    live = [player for player in room["players"].values() if player["hp"] > 0]
    next_bullets = []
    for bullet in room["bullets"]:
        bullet["x"] += bullet["vx"] * dt; bullet["y"] += bullet["vy"] * dt
        bullet["ttl"] -= dt
        if bullet["ttl"] <= 0 or not 0 <= bullet["x"] <= 800 or not 0 <= bullet["y"] <= 800:
            continue
        hit = None
        for player in live:
            if player["id"] != bullet["owner"] and math.hypot(player["x"] - bullet["x"], player["y"] - bullet["y"]) < 18:
                hit = player; break
        if hit:
            hit["hp"] = max(0, hit["hp"] - 25)
            if hit["hp"] == 0:
                owner = room["players"].get(bullet["owner"])
                if owner: owner["kills"] += 1
        else:
            next_bullets.append(bullet)
    room["bullets"] = next_bullets[-80:]
    for player in live:
        if math.hypot(player["x"] - 400, player["y"] - 400) > room["zone"]:
            player["hp"] = max(0, player["hp"] - 12 * dt)
    alive = [player for player in room["players"].values() if player["hp"] > 0]
    if len(room["players"]) > 1 and len(alive) <= 1:
        room["winner"] = alive[0]["id"] if alive else ""


@bp.route("/api/public/games/royale", methods=["POST", "OPTIONS"])
def public_block_royale():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}; user = _verify_init_data(body.get("initData", ""))
    if user is None: return jsonify({"ok": False, "error": "Abre el juego desde Telegram"}), 401
    uid = str(user.get("id")); action = str(body.get("action") or "state")
    now = time.time()
    with _royale_lock:
        for key in list(_royale_rooms):
            if now - _royale_rooms[key].get("updated", now) > 1800: _royale_rooms.pop(key, None)
        room = next((value for value in _royale_rooms.values() if uid in value["players"] and not value.get("winner")), None)
        if action == "join" and room is None:
            room = next((value for value in _royale_rooms.values() if not value.get("winner") and len(value["players"]) < 12 and now-value["started"] < 45), None)
            if room is None:
                rid = secrets.token_hex(4); room = {"id": rid, "started": now, "updated": now, "zone": 370.0, "players": {}, "bullets": [], "winner": ""}; _royale_rooms[rid] = room
            seed = int(hashlib.sha256(f"{room['id']}:{uid}".encode()).hexdigest()[:8], 16)
            room["players"][uid] = {"id": uid, "name": str(user.get("first_name") or "Jugador")[:24], "x": 100 + seed % 600, "y": 100 + (seed // 7) % 600, "hp": 100.0, "kills": 0, "shot_at": 0.0, "seen": now}
        if room is None: return jsonify({"ok": False, "error": "Ãšnete primero"}), 409
        _royale_advance(room, now); player = room["players"].get(uid)
        if not player: return jsonify({"ok": False, "error": "Partida finalizada"}), 409
        player["seen"] = now
        if action == "move" and player["hp"] > 0 and not room.get("winner"):
            dx = max(-1.0, min(1.0, float(body.get("dx") or 0))); dy = max(-1.0, min(1.0, float(body.get("dy") or 0)))
            length = math.hypot(dx, dy) or 1; speed = 22
            player["x"] = max(16, min(784, player["x"] + dx / length * speed)); player["y"] = max(16, min(784, player["y"] + dy / length * speed))
        elif action == "shoot" and player["hp"] > 0 and now - player["shot_at"] >= 0.45 and not room.get("winner"):
            angle = float(body.get("angle") or 0); player["shot_at"] = now
            room["bullets"].append({"x": player["x"], "y": player["y"], "vx": math.cos(angle)*330, "vy": math.sin(angle)*330, "owner": uid, "ttl": 1.8})
        players = [{key: (round(value, 1) if key in ("x", "y", "hp") else value) for key, value in row.items() if key not in ("shot_at", "seen")} for row in room["players"].values() if now-row.get("seen", now) < 30]
        return jsonify({"ok": True, "room": room["id"], "you": uid, "zone": round(room["zone"], 1), "players": players, "bullets": room["bullets"], "winner": room.get("winner", "")})


@bp.route("/api/public/games/convoy", methods=["POST", "OPTIONS"])
def public_games_convoy():
    """Sincroniza convoyes y operaciones multimodales entre juegos del Hub."""
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}; user = _verify_init_data(body.get("initData", ""))
    if user is None: return jsonify({"ok": False, "error": "Abre el juego desde Telegram"}), 401
    uid, now = str(user.get("id")), time.time(); action = str(body.get("action") or "state")
    requested = re.sub(r"[^A-Z0-9]", "", str(body.get("room") or "").upper())[:8]
    with _convoy_lock:
        for key in list(_convoy_rooms):
            room = _convoy_rooms[key]
            room["players"] = {pid: row for pid, row in room["players"].items() if now-row.get("seen", now) < 45}
            if not room["players"] and now-room.get("updated", now) > 300: _convoy_rooms.pop(key, None)
        room = next((value for value in _convoy_rooms.values() if uid in value["players"]), None)
        if action == "join" and room is None:
            rid = requested or secrets.token_hex(3).upper()
            room = _convoy_rooms.setdefault(rid, {"id": rid, "created": now, "updated": now, "players": {}, "cargo": [], "seed": secrets.randbelow(999999)})
            if len(room["players"]) >= 16: return jsonify({"ok": False, "error": "Convoy completo"}), 409
            room["players"][uid] = {"id": uid, "name": str(user.get("first_name") or "Conductor")[:24], "game": "truck", "vehicle": "truck", "x": 0.0, "y": 0.0, "z": 0.0, "altitude": 0.0, "speed": 0.0, "heading": 0.0, "cargo": "", "seen": now}
        if room is None: return jsonify({"ok": False, "error": "Ãšnete a un convoy"}), 409
        player = room["players"][uid]; player["seen"] = now; room["updated"] = now
        if action == "update":
            player["game"] = str(body.get("game") or player["game"])[:16]
            player["vehicle"] = str(body.get("vehicle") or player.get("vehicle") or player["game"])[:16]
            for key in ("x", "y", "z", "altitude", "speed", "heading"):
                try: player[key] = max(-100000.0, min(100000.0, float(body.get(key, player[key]))))
                except (TypeError, ValueError): pass
            player["cargo"] = str(body.get("cargo") or "")[:80]
            for key in ("engine", "headlights", "braking", "hazards", "siren"):
                player[key] = bool(body.get(key, False))
            try: player["indicator"] = max(-1, min(1, int(body.get("indicator") or 0)))
            except (TypeError, ValueError): player["indicator"] = 0
            player["weather"] = str(body.get("weather") or "clear")[:12]
            player["snapshotTime"] = round(now, 3)
        elapsed = now-room["created"]
        ai = []
        for index, game in enumerate(("truck", "rail", "air", "sea")):
            phase = elapsed * (0.18 + index * 0.035) + room["seed"] * 0.001 + index * 1.7
            ai.append({"id": f"ai-{index}", "name": ("Aster IA", "Expreso IA", "CargoJet IA", "Marina IA")[index], "game": game, "vehicle": ("truck", "train", "plane", "ship")[index], "x": round(math.sin(phase)*260, 1), "y": round(math.cos(phase*.73)*420, 1), "z": round(math.cos(phase*.73)*420, 1), "altitude": 55 if game == "air" else 0, "speed": 55+index*18, "heading": round(phase % (math.pi*2), 3), "ai": True})
        players = [{key: value for key, value in row.items() if key != "seen"} for row in room["players"].values()]
        return jsonify({"ok": True, "room": room["id"], "you": uid, "players": players, "ai": ai, "serverTime": round(now, 3)})


@bp.route("/api/public/games/analytics", methods=["POST", "OPTIONS"])
def public_games_analytics():
    """TelemetrÃ­a mÃ­nima de MoonJuegos y resumen privado para el master."""
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}; user = _verify_init_data(body.get("initData", ""))
    if user is None: return jsonify({"ok": False, "error": "Abre MoonJuegos desde Telegram"}), 401
    action = str(body.get("action") or "event"); uid = str(user.get("id")); now = time.time()
    with _game_stats_lock:
        if action == "summary":
            if not _is_master(user): return jsonify({"ok": False, "error": "solo master"}), 403
            events = list(_game_stats["events"]); by_game = {}; by_player = {}
            for row in events:
                item = by_game.setdefault(row["game"], {"game": row["game"], "sessions": 0, "plays": 0, "wins": 0, "losses": 0, "missions": 0, "score": 0, "progress": 0, "duration": 0, "players": set(), "last_at": 0})
                item["sessions"] += row["event"] == "open"; item["plays"] += row["event"] == "play"
                item["wins"] += row.get("result") == "win"; item["losses"] += row.get("result") == "loss"
                item["missions"] += row["event"] == "mission"; item["score"] = max(item["score"], row.get("score", 0)); item["progress"] = max(item["progress"], row.get("progress", 0)); item["duration"] += row.get("duration", 0)
                item["players"].add(row["user_id"]); item["last_at"] = max(item["last_at"], row["at"])
                player = by_player.setdefault(row["user_id"], {"user_id": row["user_id"], "name": (_game_stats["players"].get(row["user_id"]) or {}).get("name", "Jugador"), "plays": 0, "wins": 0, "missions": 0, "score": 0, "progress": 0, "last_at": 0})
                player["plays"] += row["event"] == "play"; player["wins"] += row.get("result") == "win"; player["missions"] += row["event"] == "mission"; player["score"] = max(player["score"], row.get("score", 0)); player["progress"] = max(player["progress"], row.get("progress", 0)); player["last_at"] = max(player["last_at"], row["at"])
            games = [{**item, "players": len(item["players"])} for item in by_game.values()]
            games.sort(key=lambda row: (-row["plays"], -row["sessions"], row["game"]))
            active_day = {row["user_id"] for row in events if now-row["at"] <= 86400}
            players = sorted(by_player.values(), key=lambda row: (-row["wins"], -row["missions"], -row["score"]))[:100]
            return jsonify({"ok": True, "totals": {"players": len(_game_stats["players"]), "active_24h": len(active_day), "sessions": sum(row["event"] == "open" for row in events), "plays": sum(row["event"] == "play" for row in events), "wins": sum(row.get("result") == "win" for row in events), "missions": sum(row["event"] == "mission" for row in events), "duration": round(sum(row.get("duration", 0) for row in events))}, "games": games, "players": players, "generated_at": round(now)})
        game = re.sub(r"[^a-z0-9_-]", "", str(body.get("game") or "unknown").lower())[:48] or "unknown"
        event = str(body.get("event") or "open").lower(); event = event if event in {"open", "play", "finish", "mission", "progress"} else "open"
        result = str(body.get("result") or "").lower(); result = result if result in {"win", "loss", "draw", "abandoned"} else ""
        def bounded_number(name, maximum):
            try: return max(0, min(maximum, float(body.get(name) or 0)))
            except (TypeError, ValueError): return 0
        _game_stats["players"][uid] = {"name": str(user.get("first_name") or "Jugador")[:80], "seen": now}
        _game_stats["events"].append({"user_id": uid, "game": game, "event": event, "result": result, "score": bounded_number("score", 100000000), "progress": bounded_number("progress", 100), "duration": bounded_number("duration", 86400), "mission": str(body.get("mission") or "")[:120], "at": now})
        _game_stats["events"] = _game_stats["events"][-25000:]
        _save_game_stats()
    return jsonify({"ok": True})


def _community_campaigns_for_audience(owner_verified=False):
    """Fetch approved community campaigns without exposing audience decisions to JS."""
    audience = "channel_owner" if owner_verified else "general"
    cached = _community_campaign_cache.get(audience) or {}
    if time.time() - float(cached.get("at", 0) or 0) < 120:
        return cached.get("ads", [])
    endpoint = os.getenv("COMMUNITY_CARDS_URL", "https://todosobreall.tech/hcgi/api/community-cards").rstrip("/")
    query = f"placement=hub&site=hub&audience={audience}"
    internal_key = str(os.getenv("MOON_ADMIN_API_KEY") or "").strip()
    headers = {"Accept": "application/json", "User-Agent": "MoonMultibot-Hub/1.0"}
    if internal_key:
        headers["X-Moon-Admin-Key"] = internal_key
    req = urllib.request.Request(f"{endpoint}?{query}", headers=headers)
    with urllib.request.urlopen(req, timeout=5) as response:
        payload = json.loads(response.read(512 * 1024))
    rows = payload.get("ads", []) if isinstance(payload, dict) else []
    normalized = []
    for raw in rows[:20]:
        if not isinstance(raw, dict) or raw.get("enabled") is False:
            continue
        item_audience = str(raw.get("audience") or "general").strip().lower()
        if item_audience == "channel_owner" and not owner_verified:
            continue
        if item_audience not in {"general", "channel_owner", "all"}:
            continue
        ad_id = re.sub(r"[^A-Za-z0-9_-]", "", str(raw.get("id") or ""))[:80]
        destination = str(raw.get("url") or "").strip()
        parsed = urlparse(destination)
        if not ad_id or parsed.scheme != "https" or not parsed.netloc:
            continue
        tracking_url = f"{endpoint}/{ad_id}/click?placement=hub&site=hub"
        normalized.append({
            "id": ad_id, "title": str(raw.get("title") or "Comunidad recomendada")[:160],
            "description": str(raw.get("description") or "")[:500],
            "cta": str(raw.get("cta") or "Abrir en Telegram")[:40],
            "image": str(raw.get("image") or "")[:500], "url": destination,
            "click_url": tracking_url, "audience": item_audience,
            "source": "todosobrealltech", "campaign_type": str(raw.get("campaign_type") or "community")[:40],
        })
    owner_rows = [row for row in normalized if row["audience"] == "channel_owner"]
    selected = owner_rows if owner_verified and owner_rows else [row for row in normalized if row["audience"] in {"general", "all"}]
    _community_campaign_cache[audience] = {"at": time.time(), "ads": selected}
    return selected


def _has_verified_channel_ownership(user):
    """Only Telegram-backed creator records prove channel ownership; master is not ownership."""
    user_id = str((user or {}).get("id") or "").strip()
    if not user_id or not _channel_stats:
        return False
    try:
        rows = _channel_stats.get_user_channels(user_id) or []
    except Exception:
        return False
    return any(
        str(row.get("role") or row.get("status") or row.get("admin_status") or "").strip().lower() == "creator"
        for row in rows if isinstance(row, dict)
    )


def setup(channel_stats, proxy_mgr, master_id=None, jwt_secret=None, get_active_bots=None,
          db=None, ban_manager=None, get_bot_for_chat=None, check_cas=None,
          hub_bot_username="cintiabot", get_global_user_stats=None, get_global_chat_names=None,
          add_audit_log=None, vt_manager=None, get_ai_runtime_config=None, set_ai_runtime_config=None,
          task_queue=None, group_administration=None, tdlib_client=None, get_cas_export_status=None):
    global _channel_stats, _proxy_mgr, _master_id, _jwt_secret, _get_active_bots
    global _db, _ban_manager, _get_bot_for_chat, _check_cas
    global _hub_bot_username, _get_global_user_stats, _get_global_chat_names, _add_audit_log, _vt_manager
    global _get_ai_runtime_config, _set_ai_runtime_config, _task_queue, _group_administration, _tdlib_client, _get_cas_export_status
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
    _tdlib_client = tdlib_client
    _get_cas_export_status = get_cas_export_status
    try:
        pb = getattr(channel_stats, "_pb", None)
        if pb:
            ensure_release_schema(pb)
    except Exception as error:
        if add_audit_log:
            add_audit_log(f"No se pudo preparar feature_release_access: {error}")
    return bp


@bp.route("/api/public/news/instant")
def public_news_instant():
    """Vista rÃ¡pida y segura de NoticiasWeb3 para el Hub de Telegram."""
    now = time.time()
    articles = _instant_news_cache.get("articles", [])
    stale = now - float(_instant_news_cache.get("at", 0) or 0) > 600
    if stale:
        try:
            payload = _noticias_api_read("/noticias/rss")
            root = ET.fromstring(payload)
            parsed = []
            for item in root.findall("./channel/item")[:60]:
                value = lambda name: str(item.findtext(name) or "").strip()
                link = value("link")
                if not link.startswith("https://noticiasweb3.todosobreall.tech/"):
                    continue
                description = html.unescape(re.sub(r"<[^>]+>", " ", value("description")))
                description = re.sub(r"\s+", " ", description).strip()
                parsed.append({
                    "id": hashlib.sha256(link.encode()).hexdigest()[:16],
                    "title": value("title")[:240], "summary": description[:1200],
                    "category": value("category")[:80] or "TecnologÃ­a",
                    "date": value("pubDate")[:100], "url": link,
                    "views": max(0, int(value("views") or 0)),
                })
            if parsed:
                articles = parsed
                _instant_news_cache.update({"at": now, "articles": articles})
        except Exception as exc:
            current_app.logger.warning("NoticiasWeb3 instant feed unavailable: %s", exc)
    _sync_master_channel_ads()
    ads = [{key: row.get(key) for key in ("id", "title", "description", "url", "image", "cta",
                                            "background", "foreground", "accent", "community_id", "display_format",
                                            "community_items")}
           for row in _house_ads_payload("inline")[:12]
           if row.get("enabled", True) and row.get("approval_status") == "approved"
           and str(row.get("url") or "").startswith(("https://", "http://"))]
    return jsonify({"ok": True, "mode": "instant_view", "articles": articles[:60], "ads": ads,
                    "cached": stale and bool(articles), "source": "NoticiasWeb3 2026"})


@bp.route("/api/public/network/instant/<service>")
def public_network_instant(service):
    """Vista mÃ³vil propia del Hub para los canales de la red."""
    sources = {
        "gameplays": ("TodoSobreGameplaysCanal", "Gameplays", "Comunidad y contenidos gaming", "#a63a2e"),
        "resistencia": ("resistencia_censura", "Resistencia", "Privacidad y resistencia a la censura", "#9f2f35"),
        "comunidad": ("comunidadtelebots", "Comunidad Telebots", "Canales, bots y comunidad", "#168f9c"),
    }
    config = sources.get(str(service or "").lower())
    if not config:
        return jsonify({"ok": False, "error": "Servicio no disponible"}), 404
    channel, title, description, accent = config
    now = time.time()
    cached = _instant_channel_cache.get(service) or {}
    payload = cached.get("payload")
    stale = now - float(cached.get("at", 0) or 0) > 300
    if stale:
        try:
            raw = json.loads(_noticias_api_read(f"/telegram-channel/{channel}", timeout=10))
            posts = []
            for row in (raw.get("messages") or [])[:40]:
                if not isinstance(row, dict):
                    continue
                url = str(row.get("url") or "").strip()
                if not url.startswith(f"https://t.me/{channel}/"):
                    continue
                posts.append({
                    "id": str(row.get("id") or hashlib.sha256(url.encode()).hexdigest()[:16]),
                    "text": str(row.get("text") or "")[:5000], "date": str(row.get("date") or "")[:100],
                    "views": str(row.get("views") or "")[:30], "image": str(row.get("photoUrl") or "")[:1000],
                    "mediaType": str(row.get("mediaType") or ("photo" if row.get("hasPhoto") else ""))[:20],
                    "url": url,
                })
            payload = {"ok": True, "mode": "network_instant", "service": service, "channel": channel,
                       "title": title, "description": description, "accent": accent, "posts": posts,
                       "stats": raw.get("stats") or {}, "fetchedAt": raw.get("fetchedAt")}
            _instant_channel_cache[service] = {"at": now, "payload": payload}
        except Exception as exc:
            current_app.logger.warning("Network instant view unavailable for %s: %s", service, exc)
    if not payload:
        return jsonify({"ok": False, "error": "No se pudieron cargar las publicaciones"}), 502
    return jsonify({**payload, "cached": stale})


@bp.route("/api/public/news/view", methods=["POST", "OPTIONS"])
def public_news_view():
    """Suma en NoticiasWeb3 la misma visita que muestra el Hub."""
    if request.method == "OPTIONS":
        return ("", 204)
    slug = str((request.json or {}).get("slug") or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,159}", slug):
        return jsonify({"ok": False, "error": "Noticia no vÃ¡lida"}), 400
    try:
        result = json.loads(_noticias_api_read(
            f"/noticias/view/{slug}",
            data=json.dumps({"source": "hub"}).encode("utf-8"),
            limit=64 * 1024,
        ))
        return jsonify({"ok": True, "visitas": max(0, int(result.get("visitas") or 0))})
    except urllib.error.HTTPError as exc:
        return jsonify({"ok": False, "error": "Noticia no encontrada"}), exc.code
    except Exception:
        return jsonify({"ok": False, "error": "No se pudo registrar la visualizaciÃ³n"}), 502


@bp.route("/api/public/community-campaigns", methods=["POST", "OPTIONS"])
def public_community_campaigns():
    if request.method == "OPTIONS":
        return ("", 204)
    user = _verify_init_data((request.json or {}).get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
    # La propiedad se resuelve exclusivamente con roles que Moonbot obtuvo del backend.
    # Nunca se acepta una bandera owner procedente del navegador.
    owner_verified = _has_verified_channel_ownership(user)
    try:
        ads = _community_campaigns_for_audience(owner_verified)
    except Exception:
        # Fail closed: si el catÃ¡logo no responde no inventamos destinos ni elevamos audiencia.
        ads = []
    return jsonify({"ok": True, "ads": ads, "audience": "channel_owner" if owner_verified else "general"})


# Desfase mÃ¡ximo (s) permitido hacia el futuro: un auth_date muy adelantado
# indica reloj manipulado / firma falsificada.
_AUTH_DATE_SKEW = 300


def _hub_bot():
    """La ÃšNICA instancia de bot que sirve la Mini App del hub (por username).
    Devuelve None si no estÃ¡ activa -> fail-closed (se deniega la validaciÃ³n)."""
    if not _get_active_bots:
        return None
    want = (_hub_bot_username or "").lower()
    for b in _get_active_bots() or []:
        if (getattr(b, "bot_username", "") or "").lower() == want:
            return b
    return None


def _verify_init_data(init_data, max_age=86400):
    """Valida el initData de la Mini App del hub. Endurecido:
      1) auth_date obligatorio: rechaza firmas de mas de `max_age` s (24h por
         defecto) o con reloj en el futuro (> _AUTH_DATE_SKEW).
      2) firma contra un token de bot activo gestionado por Moonbot. Telegram
         usa el bot concreto desde el que se abriÃ³ la MiniApp.
    Devuelve el dict de usuario si la firma es vÃ¡lida y vigente, o None."""
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception:
        return None
    recv_hash = pairs.pop("hash", None)
    if not recv_hash:
        return None
    # 1) Vigencia (auth_date sÃ­ forma parte del data_check_string; solo se saca 'hash').
    try:
        auth_date = int(pairs.get("auth_date", ""))
    except (TypeError, ValueError):
        return None
    now = int(time.time())
    if auth_date <= 0 or now - auth_date > max_age or auth_date - now > _AUTH_DATE_SKEW:
        return None
    # 2) Firma: Ãºnicamente el bot del hub (fail-closed si no estÃ¡ activo).
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
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Community-Key, X-Moon-Admin-Key"
    if request.path in {"/api/internal/features", "/api/public/features"}:
        resp.headers["Cache-Control"] = "private, no-store, max-age=0"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Vary"] = "Authorization, X-Moon-Actor-Role, X-Moon-Actor-Id, X-Moon-Release-Channel"
    return resp


def _internal_admin_authorized():
    """Autoriza la clave servidor-a-servidor o el JWT temporal del master de la MiniApp."""
    expected = os.getenv("MOON_ADMIN_API_KEY", "").strip()
    supplied = request.headers.get("X-Moon-Admin-Key", "").strip()
    if expected and supplied and hmac.compare_digest(expected, supplied):
        return True
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer ") or not _jwt_secret:
        return False
    try:
        claims = jwt.decode(authorization[7:].strip(), _jwt_secret, algorithms=["HS256"])
        return claims.get("scope") == "miniapp_master"
    except (jwt.InvalidTokenError, ValueError, TypeError):
        return False


@bp.route("/api/internal/features", methods=["GET", "POST"])
def internal_verified_features():
    """Lista o ejecuta exclusivamente funciones verificadas y registradas."""
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    actor_role = request.headers.get("X-Moon-Actor-Role", "master").strip().lower()
    actor_id = request.headers.get("X-Moon-Actor-Id", "").strip()
    release_channel = normalize_release_channel(request.headers.get("X-Moon-Release-Channel"))
    if actor_role not in {"user", "group_admin", "group_creator", "master"}:
        return jsonify({"ok": False, "error": "invalid actor role"}), 400
    actor = {"id": actor_id}
    if actor_role == "master":
        actor["id"] = str(_master_id or actor_id)
    groups = _miniapp_feature_groups(actor)
    contextual_roles = {row.get("actor_role") for row in groups}
    catalog_role = ("master" if actor_role == "master" else
                    "group_creator" if "group_creator" in contextual_roles else
                    "group_admin" if "group_admin" in contextual_roles else "user")
    if request.method == "GET":
        features = list_verified_features(catalog_role, release_channel)
        return jsonify({"ok": True, "actor_role": catalog_role, "total": len(features),
                        "release_channel": release_channel, "features": features, "groups": groups})
    body = request.get_json(silent=True) or {}
    try:
        # El rol lo aporta el proxy interno despuÃ©s de autenticar al usuario;
        # nunca se acepta desde el cuerpo controlado por el navegador.
        item = verified_feature_registry().get(body.get("feature_id"))
        if item is None:
            raise KeyError(body.get("feature_id"))
        group_scoped = item.get("scope") in {"group_operation", "group_configuration"}
        selected = None
        payload = body.get("payload", {})
        if group_scoped:
            requested_group = _feature_payload_group_id(item, payload)
            selected = next((row for row in groups if row["chat_id"] == requested_group), None)
            if selected is None:
                raise PermissionError("grupo no autorizado")
            payload = _bind_feature_group_payload(item, payload, selected["chat_id"])
            if not _payload_uses_only_group(payload, selected["chat_id"]):
                raise PermissionError("el payload referencia otro grupo")
        effective_role = selected["actor_role"] if selected else catalog_role
        result = execute_verified_feature(body.get("feature_id"), payload, effective_role, release_channel)
        return jsonify({"ok": True, "actor_role": effective_role,
                        "group_id": selected and selected["chat_id"],
                        "feature_id": body.get("feature_id"), "result": result})
    except KeyError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 404
    except PermissionError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 403
    except (TypeError, ValueError) as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


_TELEGRAM_EXPERIENCE_SLUGS = tuple(
    slug for slug, (_, category) in HORIZON_COMPLETION_FEATURES.items()
    if category == "telegram"
)


@bp.route("/api/internal/telegram-experience", methods=["GET", "POST"])
def internal_telegram_experience():
    """Expone al master las capacidades Telegram ya implementadas y auditadas."""
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    if _db is None:
        return jsonify({"ok": False, "error": "storage unavailable"}), 503
    service = HorizonCompletion(_db)
    catalog = [row for row in service.catalog() if row["slug"] in _TELEGRAM_EXPERIENCE_SLUGS]
    if request.method == "GET":
        return jsonify({"ok": True, "total": len(catalog), "features": catalog})
    if request.content_length and request.content_length > 65536:
        return jsonify({"ok": False, "error": "payload too large"}), 413
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"ok": False, "error": "invalid payload"}), 400
    slug = str(body.get("slug") or "").strip()
    if slug not in _TELEGRAM_EXPERIENCE_SLUGS:
        return jsonify({"ok": False, "error": "unknown feature"}), 400
    payload = body.get("payload", {})
    if not isinstance(payload, dict):
        return jsonify({"ok": False, "error": "payload must be an object"}), 400
    try:
        result = service.execute(slug, payload)
    except (ValueError, TypeError, KeyError) as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    if _add_audit_log:
        _add_audit_log(f"Experiencia Telegram ejecutada por master: {slug}")
    return jsonify({"ok": True, "feature": slug, "result": result})


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


def _admin_group_rows():
    """Inventario normalizado de chats que pertenecen al menos a un bot activo."""
    communities = _db.get("TELEGRAM_COMMUNITIES", {}) or {}
    rows = []
    for channel in _admin_channel_union():
        bots = channel.get("bots") or []
        if not bots or channel.get("chat_id") is None:
            continue
        chat_id = str(channel["chat_id"])
        rows.append({**channel, "id": chat_id,
                     "community": communities.get(chat_id),
                     "name": str(channel.get("name") or channel.get("username") or f"Grupo {channel['chat_id']}")[:160]})
    return rows


def _sync_telegram_community(chat_id, chat):
    """Actualiza la pertenencia real usando ChatFullInfo de Bot API 10.2."""
    if not isinstance(chat, dict):
        return None
    cid = str(chat_id)
    registry = _db.get("TELEGRAM_COMMUNITIES", {}) or {}
    community = chat.get("community")
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if isinstance(community, dict) and community.get("id") is not None:
        registry[cid] = {
            "chat_id": cid,
            "chat_title": chat.get("title") or registry.get(cid, {}).get("chat_title"),
            "community": community,
            "community_id": str(community.get("id")),
            "active": True,
            "source": "getChat",
            "updated_at": now,
        }
    elif "community" in chat:
        current = registry.get(cid, {"chat_id": cid, "chat_title": chat.get("title")})
        current.update({"active": False, "community": None, "community_id": "",
                        "source": "getChat", "updated_at": now})
        registry[cid] = current
    _db.set("TELEGRAM_COMMUNITIES", registry)
    return registry.get(cid)


def _telegram_community_overview(chat_id):
    cid = str(chat_id)
    registry = _db.get("TELEGRAM_COMMUNITIES", {}) or {}
    current = registry.get(cid) or {}
    community_id = str(current.get("community_id") or "") if current.get("active") else ""
    rows = _admin_group_rows()
    members = [row for row in rows if community_id and str((row.get("community") or {}).get("community_id") or "") == community_id
               and (row.get("community") or {}).get("active")]
    current_bots = {str(bot.get("id") or bot.get("username") or "") for row in rows if str(row.get("id")) == cid for bot in row.get("bots", [])}
    candidates = []
    if community_id:
        for row in rows:
            if str(row.get("id")) == cid or any(str(member.get("id")) == str(row.get("id")) for member in members):
                continue
            row_bots = {str(bot.get("id") or bot.get("username") or "") for bot in row.get("bots", [])}
            if current_bots and not current_bots.intersection(row_bots):
                continue
            username = str(row.get("username") or "").lstrip("@")
            candidates.append({**row, "telegram_url": f"https://t.me/{username}" if username and username != str(row.get("id")) else None})
    return {"detected": bool(community_id), "current": current or None,
            "members": members, "candidates": candidates,
            "bot_api_can_add": False,
            "add_note": "Bot API 10.2 detecta comunidades, pero la incorporaciÃ³n se confirma desde los ajustes de la comunidad en Telegram."}


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
    learning_notifications = [row for row in _safe_list(_db.get("AI_LEARNING_NOTIFICATIONS", []))
                              if isinstance(row, dict)][-10:]

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
        "notifications": list(reversed(learning_notifications)),
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
        "incident_correlation": lambda: service.correlate_incidents(data.get("group_ids") or [], data.get("window_minutes", 30), data.get("minimum_events", 2)),
    }
    if action not in handlers:
        return jsonify({"ok": False, "error": "acciÃ³n no permitida"}), 400
    try:
        result = handlers[action]()
        return jsonify({"ok": True, "result": result})
    except (TypeError, ValueError) as error:
        return jsonify({"ok": False, "error": str(error)}), 400


@bp.route("/api/internal/horizon", methods=["GET", "POST"])
def internal_horizon():
    """NÃºcleo ejecutable del catÃ¡logo Horizonte unificado."""
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    service = FullHorizonSuite(_db)
    if request.method == "GET":
        catalog = service.catalog()
        return jsonify({"ok": True, "features": catalog, "total": len(catalog),
                        "categories": sorted({row["category"] for row in catalog}),
                        "audit": list(reversed(service.audit()))[:100]})
    body = request.json or {}
    slug = str(body.get("slug") or "").strip()
    try:
        result = service.execute(slug, body.get("payload") or {})
        if _add_audit_log:
            _add_audit_log(f"Horizonte unificado ejecutado desde TodoSobreAllTech: {slug}")
        return jsonify({"ok": True, "slug": slug, "result": result})
    except (TypeError, ValueError, KeyError) as error:
        return jsonify({"ok": False, "error": str(error)}), 400


@bp.route("/api/internal/horizon/features/<slug>", methods=["GET", "POST", "PUT", "DELETE"])
def internal_horizon_feature(slug):
    """REST resource for one Horizonte capability."""
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    service = FullHorizonSuite(_db)
    feature = service.describe(slug)
    if not feature:
        return jsonify({"ok": False, "error": "feature_not_found"}), 404
    if not str(slug).startswith("future-") and request.method != "POST":
        if request.method == "GET":
            return jsonify({"ok": True, "feature": feature})
        return jsonify({"ok": False, "error": "operation_not_supported_for_legacy_feature"}), 405
    payload = request.json if request.is_json else request.args.to_dict()
    payload = payload if isinstance(payload, dict) else {}
    operations = {"GET": "status", "POST": payload.get("operation", "run"),
                  "PUT": "configure", "DELETE": "rollback"}
    payload = {**payload, "operation": operations[request.method]}
    try:
        result = service.execute(slug, payload)
        _add_audit_log(f"Horizonte REST {request.method} {slug}")
        return jsonify({"ok": True, "slug": slug, "operation": payload["operation"], "result": result})
    except (TypeError, ValueError, KeyError) as error:
        return jsonify({"ok": False, "error": str(error)}), 400


def _known_internal_group(cid, bot_id=None):
    requested = str(bot_id or "").strip().lower()
    for bot in (_get_active_bots() or []) if _get_active_bots else []:
        identities = {str(getattr(bot, "bot_id", "")).lower(), str(getattr(bot, "user_id", "")).lower(),
                      str(getattr(bot, "bot_username", "")).lower().lstrip("@")}
        if requested and requested.lstrip("@") not in identities:
            continue
        if str(cid) in {str(item) for item in _safe_list(_db.get(f"CHATS_{getattr(bot, 'token', '')}", []))}:
            return bot
    return None


def _known_internal_group_ids():
    ids = set()
    for bot in (_get_active_bots() or []) if _get_active_bots else []:
        ids.update(str(item) for item in _safe_list(_db.get(f"CHATS_{getattr(bot, 'token', '')}", [])))
    return ids


def _start_bulk_captcha(bot, cid, actor="admin", only_pending=False):
    """Reverifica en segundo plano a los miembros observados sin bloquear la API."""
    job_key = f"JOIN_BULK_JOB_{cid}"
    current = _db.get(job_key, {}) if _db else {}
    if current.get("status") == "running":
        return current, False
    observed = _db.get(f"TELEGRAM_GROUP_LANGUAGES_{cid}", {}) if _db else {}
    config = _join_config(cid)
    exempt = {str(uid) for uid in (config.get("exempt_user_ids") or [])}
    if _master_id is not None:
        exempt.add(str(_master_id))
    user_ids = [uid for uid in (observed or {}).keys() if str(uid) not in exempt] if isinstance(observed, dict) else []
    if only_pending:
        user_ids = [uid for uid in user_ids
                    if (_db.get(f"CAPTCHA_STATUS_{cid}_{uid}", {}) or {}).get("status") != "passed"]
    job = {"status": "running", "total": len(user_ids), "processed": 0, "muted": 0,
           "private_sent": 0, "private_blocked": 0, "skipped": 0,
           "started_at": int(time.time()), "actor": str(actor)[:80], "only_pending": bool(only_pending)}
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
                if (str(uid) == str(_master_id)
                        or member.get("status") in ("creator", "administrator")
                        or member.get("status") not in ("member", "restricted")
                        or user.get("is_bot")):
                    _db.set(f"CAPTCHA_STATUS_{cid}_{uid}", {"status": "exempt", "at": int(time.time()),
                            "reason": "protected_role_bot_or_not_member"})
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
                    "text": "ðŸ” El grupo requiere una nueva verificaciÃ³n. Completa el captcha para recuperar tus permisos de envÃ­o.",
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


@bp.route("/api/internal/groups")
def internal_groups():
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    query = str(request.args.get("q", "")).strip().casefold()[:100]
    bot_id = str(request.args.get("bot_id", "")).strip().casefold()[:100]
    kind = str(request.args.get("type", "all")).lower()
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = max(10, min(100, int(request.args.get("per_page", 40))))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "invalid_pagination"}), 400
    if kind not in ("all", "group", "channel"):
        return jsonify({"ok": False, "error": "invalid_type"}), 400
    rows = _admin_group_rows()
    if bot_id:
        rows = [row for row in rows if any(bot_id.lstrip("@") in {
            str(bot.get("id", "")).casefold(), str(bot.get("username", "")).casefold().lstrip("@")
        } for bot in row.get("bots", []))]
    if kind == "channel": rows = [row for row in rows if str(row.get("ctype", "")).lower() == "channel"]
    elif kind == "group": rows = [row for row in rows if str(row.get("ctype", "")).lower() != "channel"]
    if query:
        rows = [row for row in rows if query in " ".join([str(row.get("name", "")), str(row.get("id", "")),
            str(row.get("username", "")), *[str(bot.get("username", "")) for bot in row.get("bots", [])]]).casefold()]
    rows.sort(key=lambda row: str(row.get("name") or row.get("id")).casefold())
    total = len(rows); total_pages = max(1, (total + per_page - 1) // per_page); page = min(page, total_pages)
    start = (page - 1) * per_page
    return jsonify({"ok": True, "groups": rows[start:start + per_page], "total": total,
                    "page": page, "per_page": per_page, "total_pages": total_pages, "type": kind})


@bp.route("/api/internal/get_user_channels")
def internal_get_user_channels():
    """Contract used by TodoSobreAllTech to verify Telegram channel ownership."""
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    telegram_id = str(request.args.get("telegram_id") or "").strip()
    if not re.fullmatch(r"[1-9][0-9]{4,19}", telegram_id):
        return jsonify({"ok": False, "error": "invalid_telegram_id"}), 400
    try:
        rows = _channel_stats.get_user_channels(telegram_id) or []
    except Exception as error:
        return jsonify({"ok": False, "error": "channel_directory_unavailable", "detail": str(error)[:160]}), 503
    channels = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        role = str(row.get("role") or row.get("status") or row.get("admin_status") or "").strip().lower()
        if role not in {"creator", "administrator", "member"}:
            role = "unknown"
        channels.append({
            "chat_id": str(row.get("chat_id") or row.get("id") or "")[:32],
            "title": str(row.get("title") or row.get("name") or "")[:160],
            "username": str(row.get("username") or "").lstrip("@")[0:64],
            "role": role, "is_owner": role == "creator",
        })
    return jsonify({"ok": True, "telegram_id": telegram_id, "channels": channels,
                    "owner_verified": any(row["is_owner"] for row in channels)})


@bp.route("/api/internal/groups/<cid>", methods=["GET", "POST"])
def internal_group_admin(cid):
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    body = (request.json or {}) if request.method == "POST" else {}
    bot = _known_internal_group(cid, body.get("bot_id"))
    if not bot:
        return jsonify({"ok": False, "error": "group_not_found"}), 404
    suite = GroupSuite(_db)
    if request.method == "POST":
        action = body.get("action")
        if action == "save_config" and isinstance(body.get("config"), dict):
            config = suite.save_config(cid, body["config"], actor="web-master",
                                       source="todosobrealltech")
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
            if "required_channels" in body:
                join_config["required_channels"] = _normalize_required_channels(body.get("required_channels"))
            _db.set(f"JOINCFG_{cid}", join_config)
            return jsonify({"ok": True, "join_config": _join_config(cid)})
        elif action == "reverify_all":
            job, started = _start_bulk_captcha(bot, cid, "web-master")
            return jsonify({"ok": True, "started": started, "captcha_job": job})
        elif action == "preview_reverify":
            observed = _db.get(f"TELEGRAM_GROUP_LANGUAGES_{cid}", {}) or {}
            return jsonify({"ok": True, "captcha_preview": {"observed": len(observed),
                "note": "Se comprobarÃ¡ en Telegram y se excluirÃ¡n administradores, bots y miembros que ya salieron."}})
        elif action == "cancel_reverify":
            job = _db.get(f"JOIN_BULK_JOB_{cid}", {}) or {}
            if job.get("status") == "running":
                job["status"] = "cancel_requested"
                _db.set(f"JOIN_BULK_JOB_{cid}", job)
            return jsonify({"ok": True, "captcha_job": job})
        elif action == "sync_commands":
            return jsonify({"ok": True, "command_menu": bot.sync_command_menu(cid)})
        elif action == "send_message":
            text = str(body.get("text") or "").strip()
            if not text or len(text) > 4096:
                return jsonify({"ok": False, "error": "invalid_message"}), 400
            parse_mode = "Markdown" if body.get("markdown", True) else None
            reply_to = str(body.get("reply_to_message_id") or "").strip()
            reply_parameters = {"message_id": int(reply_to)} if reply_to.isdigit() else None
            result = bot.send_msg(cid, text, parse_mode=parse_mode, reply_parameters=reply_parameters,
                                  disable_notification=bool(body.get("disable_notification")),
                                  protect_content=bool(body.get("protect_content")))
            if not isinstance(result, dict) or not result.get("ok"):
                return jsonify({"ok": False, "error": "telegram_send_failed",
                                "detail": (result or {}).get("description") if isinstance(result, dict) else None}), 502
            history = _safe_list(_db.get(f"CHAT_HIST_{cid}", []))
            if not history or history[-1].get("sender") != "Bot" or history[-1].get("text") != text[:1000]:
                history.append({"time": datetime.datetime.now().strftime("%H:%M"), "sender": "Bot",
                                "uid": str(getattr(bot, "bot_username", "Moonbot")),
                                "message_id": (result.get("result") or {}).get("message_id"),
                                "reply_to_message_id": int(reply_to) if reply_to.isdigit() else None,
                                "text": text[:1000], "media": None})
                _db.set(f"CHAT_HIST_{cid}", history[-200:])
            if _add_audit_log:
                _add_audit_log(f"TodoSobreAllTech: mensaje enviado a {cid} mediante @{getattr(bot, 'bot_username', 'Moonbot')}")
            return jsonify({"ok": True, "sent": {"time": datetime.datetime.now().strftime("%H:%M"),
                            "sender": "Bot", "text": text[:1000], "has_media": False},
                            "message_id": (result.get("result") or {}).get("message_id"),
                            "bot": {"id": str(getattr(bot, "bot_id", "")),
                                    "username": str(getattr(bot, "bot_username", "Moonbot"))}})
        elif action == "chat_message_action":
            message_id = str(body.get("message_id") or "").strip()
            operation = str(body.get("operation") or "").strip()
            allowed_operations = {"delete", "pin", "unpin", "react", "edit", "copy", "forward",
                                  "clear_reactions", "unpin_all"}
            if (operation != "unpin_all" and not message_id.isdigit()) or operation not in allowed_operations:
                return jsonify({"ok": False, "error": "invalid_chat_message_action"}), 400
            mid = int(message_id) if message_id.isdigit() else None
            if operation == "delete":
                result = bot.delete_msg(cid, mid)
            elif operation == "pin":
                result = bot.pin_msg(cid, mid)
            elif operation == "unpin":
                result = bot.unpin_msg(cid, mid)
            elif operation == "unpin_all":
                result = bot.unpin_all_messages(cid)
            elif operation == "edit":
                new_text = str(body.get("text") or "").strip()
                if not new_text or len(new_text) > 4096:
                    return jsonify({"ok": False, "error": "invalid_message"}), 400
                result = bot.edit_msg(cid, mid, new_text)
            elif operation in {"copy", "forward"}:
                target_chat_id = str(body.get("target_chat_id") or "").strip()
                if not target_chat_id or not _known_internal_group(target_chat_id):
                    return jsonify({"ok": False, "error": "target_group_not_found"}), 404
                result = (bot.copy_message(target_chat_id, cid, mid, body.get("caption"))
                          if operation == "copy" else bot.forward_message(target_chat_id, cid, mid))
            elif operation == "clear_reactions":
                result = bot.delete_all_message_reactions(cid, mid)
            else:
                reaction = str(body.get("reaction") or "ðŸ‘")[:16]
                result = bot.set_message_reaction(cid, mid, reaction, is_big=bool(body.get("is_big")))
            if not isinstance(result, dict) or not result.get("ok"):
                return jsonify({"ok": False, "error": "telegram_message_action_failed",
                                "detail": (result or {}).get("description") if isinstance(result, dict) else None}), 502
            if operation == "delete":
                history = [row for row in _safe_list(_db.get(f"CHAT_HIST_{cid}", []))
                           if str(row.get("message_id") or "") != message_id]
                _db.set(f"CHAT_HIST_{cid}", history[-200:])
            elif operation == "edit":
                history = _safe_list(_db.get(f"CHAT_HIST_{cid}", []))
                for row in history:
                    if str(row.get("message_id") or "") == message_id:
                        row["text"] = str(body.get("text"))[:1000]
                        row["edited"] = True
                _db.set(f"CHAT_HIST_{cid}", history[-200:])
            if _add_audit_log:
                _add_audit_log(f"Chat master: {operation} sobre mensaje {message_id} en {cid}")
            return jsonify({"ok": True, "operation": operation, "message_id": mid})
        elif action == "send_poll":
            question = str(body.get("question") or "").strip()
            options = body.get("options") or []
            if not question or not isinstance(options, list) or not 1 <= len(options) <= 12:
                return jsonify({"ok": False, "error": "invalid_poll"}), 400
            result = bot.send_poll(cid, question, options,
                                   is_anonymous=bool(body.get("is_anonymous", True)),
                                   allows_multiple_answers=bool(body.get("allows_multiple_answers")),
                                   quiz=bool(body.get("quiz")),
                                   correct_option_ids=body.get("correct_option_ids"),
                                   explanation=body.get("explanation"),
                                   open_period=body.get("open_period"),
                                   protect_content=bool(body.get("protect_content")))
            if not isinstance(result, dict) or not result.get("ok"):
                return jsonify({"ok": False, "error": "telegram_poll_failed",
                                "detail": (result or {}).get("description") if isinstance(result, dict) else None}), 502
            if _add_audit_log:
                _add_audit_log(f"Encuesta enviada desde chat master a {cid}")
            return jsonify({"ok": True, "message_id": (result.get("result") or {}).get("message_id")})
        elif action == "send_ephemeral_message":
            text = str(body.get("text") or "").strip()
            receiver_user_id = str(body.get("receiver_user_id") or "").strip()
            if not text or len(text) > 4096 or not receiver_user_id.isdigit():
                return jsonify({"ok": False, "error": "invalid_ephemeral_message"}), 400
            result = bot.send_msg(cid, text, parse_mode="Markdown" if body.get("markdown", True) else None,
                                  receiver_user_id=int(receiver_user_id),
                                  callback_query_id=body.get("callback_query_id"),
                                  disable_notification=bool(body.get("disable_notification")),
                                  protect_content=bool(body.get("protect_content")))
            if not isinstance(result, dict) or not result.get("ok"):
                return jsonify({"ok": False, "error": "telegram_ephemeral_send_failed",
                                "detail": (result or {}).get("description") if isinstance(result, dict) else None}), 502
            sent = result.get("result") or {}
            ephemeral_id = sent.get("ephemeral_message_id")
            events = _safe_list(_db.get(f"EPHEMERAL_HIST_{cid}", []))
            events.append({"time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                           "receiver_user_id": receiver_user_id, "ephemeral_message_id": ephemeral_id,
                           "text": text[:300], "bot_id": str(getattr(bot, "bot_id", ""))})
            _db.set(f"EPHEMERAL_HIST_{cid}", events[-100:])
            if _add_audit_log:
                _add_audit_log(f"Mensaje efÃ­mero 10.2 enviado a {receiver_user_id} en {cid}")
            return jsonify({"ok": True, "ephemeral": True, "receiver_user_id": receiver_user_id,
                            "ephemeral_message_id": ephemeral_id})
        elif action in {"edit_ephemeral_message", "delete_ephemeral_message"}:
            receiver_user_id = str(body.get("receiver_user_id") or "").strip()
            ephemeral_id = str(body.get("ephemeral_message_id") or "").strip()
            if not receiver_user_id.isdigit() or not ephemeral_id.isdigit():
                return jsonify({"ok": False, "error": "invalid_ephemeral_target"}), 400
            if action == "delete_ephemeral_message":
                result = bot.delete_ephemeral_message(cid, receiver_user_id, ephemeral_id)
            else:
                text = str(body.get("text") or "").strip()
                if not text or len(text) > 4096:
                    return jsonify({"ok": False, "error": "invalid_message"}), 400
                result = bot.edit_ephemeral_message_text(cid, receiver_user_id, ephemeral_id, text)
            if not isinstance(result, dict) or not result.get("ok"):
                return jsonify({"ok": False, "error": "telegram_ephemeral_action_failed",
                                "detail": (result or {}).get("description") if isinstance(result, dict) else None}), 502
            return jsonify({"ok": True, "action": action})
        elif action == "send_rich_message":
            text = str(body.get("text") or "").strip()
            rich_format = str(body.get("format") or "markdown").lower()
            if not text or len(text) > 32768 or rich_format not in {"markdown", "html"}:
                return jsonify({"ok": False, "error": "invalid_rich_message"}), 400
            media = None
            media_url = str(body.get("media_url") or "").strip()
            if media_url:
                media = [{"id": str(body.get("media_id") or "media_1"), "media": {
                    "type": str(body.get("media_type") or "photo").lower(), "media": media_url}}]
            rich_reply_to = str(body.get("reply_to_message_id") or "").strip()
            kwargs = {rich_format: text, "media": media, "is_rtl": bool(body.get("is_rtl")),
                      "skip_entity_detection": bool(body.get("skip_entity_detection")),
                      "reply_parameters": ({"message_id": int(rich_reply_to)} if rich_reply_to.isdigit() else None),
                      "disable_notification": bool(body.get("disable_notification")),
                      "protect_content": bool(body.get("protect_content")),
                      "fallback_text": str(body.get("fallback_text") or text)[:4096]}
            result = bot.send_rich_message(cid, **kwargs)
            if not isinstance(result, dict) or not result.get("ok"):
                return jsonify({"ok": False, "error": "telegram_rich_send_failed",
                                "detail": (result or {}).get("description") if isinstance(result, dict) else None}), 502
            history = _safe_list(_db.get(f"CHAT_HIST_{cid}", []))
            history.append({"time": datetime.datetime.now().strftime("%H:%M"), "sender": "Bot",
                            "uid": str(getattr(bot, "bot_username", "Moonbot")), "text": text[:1000],
                            "message_id": (result.get("result") or {}).get("message_id"),
                            "reply_to_message_id": int(rich_reply_to) if rich_reply_to.isdigit() else None,
                            "media": None, "format": f"rich_{rich_format}"})
            _db.set(f"CHAT_HIST_{cid}", history[-200:])
            if _add_audit_log:
                _add_audit_log(f"TodoSobreAllTech: mensaje Rich 10.2 enviado a {cid}")
            return jsonify({"ok": True, "sent": {"time": datetime.datetime.now().strftime("%H:%M"),
                            "sender": "Bot", "text": text[:1000], "format": f"rich_{rich_format}"},
                            "message_id": (result.get("result") or {}).get("message_id")})
        elif action == "refresh_telegram":
            chat_response = bot.api_call("getChat", {"chat_id": cid}, silent=True)
            if not isinstance(chat_response, dict) or not chat_response.get("ok"):
                return jsonify({"ok": False, "error": "telegram_chat_unavailable",
                                "detail": (chat_response or {}).get("description") if isinstance(chat_response, dict) else None}), 502
            chat = chat_response.get("result") or {}
            community_record = _sync_telegram_community(cid, chat)
            title = chat.get("title") or chat.get("first_name") or f"Grupo {cid}"
            username = chat.get("username") or ""
            description = chat.get("description") or chat.get("bio") or ""
            _channel_stats.register_channel(cid, username=username, title=title, description=description,
                                            ctype=chat.get("type"), bot_token=getattr(bot, "token", None))
            names = (_get_global_chat_names() or {}) if _get_global_chat_names else {}
            names[str(cid)] = title
            _db.set("CHAT_NAMES", names)
            count_response = bot.api_call("getChatMemberCount", {"chat_id": cid}, silent=True)
            if isinstance(count_response, dict) and count_response.get("ok"):
                _channel_stats.record_snapshot(cid, int(count_response.get("result") or 0))
            admins_response = bot.api_call("getChatAdministrators", {"chat_id": cid}, silent=True)
            if isinstance(admins_response, dict) and admins_response.get("ok"):
                admins = [{"user_id": row.get("user", {}).get("id"), "status": row.get("status"),
                           "name": row.get("user", {}).get("first_name"),
                           "username": row.get("user", {}).get("username")}
                          for row in (admins_response.get("result") or []) if row.get("user", {}).get("id")]
                _channel_stats.set_channel_admins(cid, admins)
            return jsonify({"ok": True, "refreshed": True, "group": {
                "id": str(cid), "name": str(title)[:160], "username": username,
                "ctype": chat.get("type"), "subscribers": (count_response or {}).get("result")
                    if isinstance(count_response, dict) and count_response.get("ok") else None,
                "community": community_record,
                "synced_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }})
        elif action == "directory_review":
            status = str(body.get("status") or "")
            record = _channel_stats.review_listing(cid, status, "todosobrealltech-admin")
            if not record:
                return jsonify({"ok": False, "error": "channel_not_found"}), 404
            if _add_audit_log:
                _add_audit_log(f"TodoSobreAllTech: directorio {status} para {cid}")
            return jsonify({"ok": True, "group": {"id": str(cid), **record}})
        elif action == "scan_community":
            rows = _admin_group_rows()
            job_key = "TELEGRAM_COMMUNITY_SCAN"
            existing = _db.get(job_key, {}) or {}
            if existing.get("status") == "running":
                return jsonify({"ok": True, "community": _telegram_community_overview(cid),
                                "scan": existing, "started": False})
            job = {"status": "running", "total": len(rows), "scanned": 0, "detected": 0,
                   "failed": 0, "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
            _db.set(job_key, job)

            def scan_all_communities():
                for row in rows:
                    target_id = str(row.get("id") or "")
                    target_bot = _known_internal_group(target_id)
                    if not target_bot:
                        job["failed"] += 1
                        continue
                    response = target_bot.api_call("getChat", {"chat_id": target_id}, silent=True)
                    if isinstance(response, dict) and response.get("ok"):
                        record = _sync_telegram_community(target_id, response.get("result") or {})
                        job["detected"] += bool(record and record.get("active"))
                        job["scanned"] += 1
                    else:
                        job["failed"] += 1
                    if (job["scanned"] + job["failed"]) % 5 == 0:
                        _db.set(job_key, dict(job))
                    time.sleep(0.05)
                job["status"] = "completed"
                job["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                _db.set(job_key, job)

            threading.Thread(target=scan_all_communities, daemon=True,
                             name="telegram-community-scan").start()
            return jsonify({"ok": True, "community": _telegram_community_overview(cid),
                            "scan": job, "started": True})
        elif action == "copy_config":
            source = str(body.get("source_id", ""))
            if not _known_internal_group(source):
                return jsonify({"ok": False, "error": "source_group_not_found"}), 404
            config = suite.save_config(cid, suite.config(source), actor="web-master",
                                       source=f"copy_config:{source}")
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

    community_response = bot.api_call("getChat", {"chat_id": cid}, silent=True)
    if isinstance(community_response, dict) and community_response.get("ok"):
        _sync_telegram_community(cid, community_response.get("result") or {})
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
    if member.get("status") not in ("administrator", "creator"):
        missing.insert(0, {"permission": "administrator", "label": "AÃ±adir el bot como administrador"})
    chat_type = ((community_response.get("result") or {}).get("type")
                 if isinstance(community_response, dict) and community_response.get("ok") else "supergroup")
    permission_history, permission_changed = _record_permission_snapshot(
        cid, bot, member.get("status", "unknown"), chat_type, missing, "web-master"
    )
    history = _safe_list(_db.get(f"CHAT_HIST_{cid}", []))
    safe_history = [{"time": row.get("time"), "sender": str(row.get("sender") or row.get("uid") or "")[:100],
                     "uid": str(row.get("uid") or "")[:40], "text": str(row.get("text") or "")[:1000],
                     "message_id": row.get("message_id"), "reply_to_message_id": row.get("reply_to_message_id"),
                     "has_media": bool(row.get("media")),
                     "media": ({"type": str(row["media"].get("type") or "document")[:20],
                                "file_id": str(row["media"].get("file_id") or "")[:300],
                                "name": str(row["media"].get("name") or "")[:160]}
                               if isinstance(row.get("media"), dict) and row["media"].get("file_id") else None)}
                    for row in history[-50:] if isinstance(row, dict)]
    repair_steps = (["Abre la informaciÃƒÂ³n del grupo en Telegram", "Entra en Administradores",
                     f"Selecciona @{getattr(bot, 'bot_username', 'MoonBot')}",
                     "Activa los permisos indicados y guarda los cambios"] if missing else [])
    return jsonify({
        "ok": True,
        "group": {"id": str(cid), "name": str((_get_global_chat_names() or {}).get(str(cid), f"Grupo {cid}"))[:160]},
        "permissions": {"healthy": not missing, "status": member.get("status", "unknown"), "missing": missing},
        "permission_changed": permission_changed,
        "permission_history": permission_history,
        "sensitive_changes": suite.sensitive_changes(cid),
        "repair_steps": repair_steps,
        "config": suite.config(cid),
        "join_config": _join_config(cid),
        "required_channel_suggestions": _required_channel_suggestions(cid),
        "global_required_channels": _global_join_channels(),
        "captcha_job": _db.get(f"JOIN_BULK_JOB_{cid}", {}),
        "captcha_history": list(reversed(_safe_list(_db.get(f"JOIN_BULK_HISTORY_{cid}", []))))[:10],
        "captcha_schedule": {"last_run": int(_db.get(f"JOIN_BULK_LAST_{cid}", 0) or 0)},
        "command_menu": bot.command_menu_preview(cid),
        "administrators": _channel_stats.admins_for_chat(cid),
        "directory": _channel_stats.get_channel_meta(cid) or {"chat_id": str(cid), "listed": False, "directory_status": "unreviewed"},
        "administrators_checked_at": (_channel_stats.get_stats_by_chat(cid) or {}).get("admins_checked_at"),
        "activity": {"stored_messages": len(history), "warnings": len(_db.get(f"WARNS_{cid}", {}) or {}),
                     "media_events": len(suite.media_events(cid, 100))},
        "community": _telegram_community_overview(cid),
        "community_scan": _db.get("TELEGRAM_COMMUNITY_SCAN", {}),
        "ephemeral_history": list(reversed(_safe_list(_db.get(f"EPHEMERAL_HIST_{cid}", []))))[:20],
        "history": safe_history,
    })


def _paid_subscription_links(cid):
    """Return only the fields needed by the administration interfaces."""
    rows = _safe_list(_db.get(f"PAID_SUBSCRIPTION_LINKS_{cid}", []))
    return [{
        "invite_link": str(row.get("invite_link") or "")[:512],
        "name": str(row.get("name") or "")[:32],
        "subscription_period": int(row.get("subscription_period") or 2592000),
        "subscription_price": int(row.get("subscription_price") or 0),
        "is_revoked": bool(row.get("is_revoked")),
        "created_at": str(row.get("created_at") or "")[:40],
        "updated_at": str(row.get("updated_at") or "")[:40],
    } for row in rows if isinstance(row, dict) and row.get("invite_link")]


@bp.route("/api/internal/groups/<cid>/paid-subscriptions", methods=["GET", "POST"])
def internal_paid_subscriptions(cid):
    """Manage Telegram's official paid channel invite links (Telegram Stars)."""
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    bot = _known_internal_group(cid)
    if not bot:
        return jsonify({"ok": False, "error": "channel_not_found"}), 404

    chat_response = bot.api_call("getChat", {"chat_id": cid}, silent=True)
    chat = chat_response.get("result", {}) if isinstance(chat_response, dict) and chat_response.get("ok") else {}
    if chat.get("type") != "channel":
        return jsonify({"ok": False, "error": "paid_subscriptions_require_channel"}), 400
    member_response = bot.api_call("getChatMember", {"chat_id": cid, "user_id": bot.bot_id}, silent=True)
    member = member_response.get("result", {}) if isinstance(member_response, dict) and member_response.get("ok") else {}
    if member.get("status") != "creator" and not member.get("can_invite_users"):
        return jsonify({"ok": False, "error": "bot_missing_invite_permission"}), 403

    key = f"PAID_SUBSCRIPTION_LINKS_{cid}"
    links = _paid_subscription_links(cid)
    if request.method == "GET":
        return jsonify({"ok": True, "channel_id": str(cid), "currency": "XTR",
                        "period_seconds": 2592000, "links": links})

    body = request.json or {}
    action = str(body.get("action") or "").strip().lower()
    invite_link = str(body.get("invite_link") or "").strip()
    name = str(body.get("name") or "").strip()
    if len(name) > 32:
        return jsonify({"ok": False, "error": "name_too_long"}), 400

    if action == "create":
        try:
            price = int(body.get("subscription_price"))
        except (TypeError, ValueError):
            return jsonify({"ok": False, "error": "invalid_subscription_price"}), 400
        if not 1 <= price <= 10000:
            return jsonify({"ok": False, "error": "invalid_subscription_price"}), 400
        result = bot.api_call("createChatSubscriptionInviteLink", {
            "chat_id": cid, "name": name, "subscription_period": 2592000,
            "subscription_price": price,
        }, silent=True)
        if not isinstance(result, dict) or not result.get("ok"):
            return jsonify({"ok": False, "error": "telegram_subscription_link_failed",
                            "detail": (result or {}).get("description") if isinstance(result, dict) else None}), 502
        telegram_link = result.get("result") or {}
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        links.insert(0, {"invite_link": telegram_link.get("invite_link"),
                         "name": telegram_link.get("name") or name,
                         "subscription_period": telegram_link.get("subscription_period") or 2592000,
                         "subscription_price": telegram_link.get("subscription_price") or price,
                         "is_revoked": bool(telegram_link.get("is_revoked")), "created_at": now,
                         "updated_at": now})
    elif action == "rename":
        if not invite_link:
            return jsonify({"ok": False, "error": "invite_link_required"}), 400
        result = bot.api_call("editChatSubscriptionInviteLink", {
            "chat_id": cid, "invite_link": invite_link, "name": name,
        }, silent=True)
        if not isinstance(result, dict) or not result.get("ok"):
            return jsonify({"ok": False, "error": "telegram_subscription_link_failed",
                            "detail": (result or {}).get("description") if isinstance(result, dict) else None}), 502
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        for row in links:
            if row["invite_link"] == invite_link:
                row["name"], row["updated_at"] = name, now
    elif action == "revoke":
        if not invite_link:
            return jsonify({"ok": False, "error": "invite_link_required"}), 400
        result = bot.api_call("revokeChatInviteLink", {"chat_id": cid, "invite_link": invite_link}, silent=True)
        if not isinstance(result, dict) or not result.get("ok"):
            return jsonify({"ok": False, "error": "telegram_subscription_link_failed",
                            "detail": (result or {}).get("description") if isinstance(result, dict) else None}), 502
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        for row in links:
            if row["invite_link"] == invite_link:
                row["is_revoked"], row["updated_at"] = True, now
    else:
        return jsonify({"ok": False, "error": "invalid_action"}), 400

    _db.set(key, links[:100])
    if _add_audit_log:
        _add_audit_log(f"Suscripcion Telegram Stars: {action} en canal {cid}")
    return jsonify({"ok": True, "channel_id": str(cid), "currency": "XTR",
                    "period_seconds": 2592000, "links": _paid_subscription_links(cid)})


@bp.route("/api/internal/groups/<cid>/photo")
def internal_group_photo(cid):
    """Entrega la foto de una comunidad sin revelar el token del bot."""
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    bot = _known_internal_group(cid)
    if not bot:
        return jsonify({"ok": False, "error": "group_not_found"}), 404
    chat_response = bot.api_call("getChat", {"chat_id": cid}, silent=True)
    chat = chat_response.get("result", {}) if isinstance(chat_response, dict) and chat_response.get("ok") else {}
    file_id = (chat.get("photo") or {}).get("small_file_id")
    if not file_id:
        return jsonify({"ok": False, "error": "photo_not_found"}), 404
    file_response = bot.api_call("getFile", {"file_id": file_id}, silent=True)
    file_path = (file_response.get("result") or {}).get("file_path") if isinstance(file_response, dict) and file_response.get("ok") else None
    if not file_path or ".." in file_path:
        return jsonify({"ok": False, "error": "photo_unavailable"}), 502
    try:
        photo_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"
        with urllib.request.urlopen(photo_url, timeout=8) as upstream:
            content = upstream.read(5 * 1024 * 1024 + 1)
            content_type = upstream.headers.get_content_type()
        if len(content) > 5 * 1024 * 1024 or not str(content_type).startswith("image/"):
            return jsonify({"ok": False, "error": "invalid_photo"}), 502
        return Response(content, mimetype=content_type, headers={"Cache-Control": "private, max-age=3600"})
    except (OSError, urllib.error.URLError):
        return jsonify({"ok": False, "error": "photo_download_failed"}), 502


@bp.route("/api/internal/groups/<cid>/media/<file_id>")
def internal_group_media(cid, file_id):
    """Proxy autenticado para medios que pertenecen al historial del chat."""
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    if not file_id or len(file_id) > 300 or "/" in file_id or ".." in file_id:
        return jsonify({"ok": False, "error": "invalid_file_id"}), 400
    history = _safe_list(_db.get(f"CHAT_HIST_{cid}", []))
    media = next((row.get("media") for row in reversed(history[-200:])
                  if isinstance(row, dict) and isinstance(row.get("media"), dict)
                  and str(row["media"].get("file_id")) == file_id), None)
    if not media:
        return jsonify({"ok": False, "error": "media_not_in_history"}), 404
    bots = []
    for candidate in (_get_active_bots() or []) if _get_active_bots else []:
        if str(cid) in {str(item) for item in _safe_list(_db.get(f"CHATS_{getattr(candidate, 'token', '')}", []))}:
            bots.append(candidate)
    for bot in bots:
        file_response = bot.api_call("getFile", {"file_id": file_id}, silent=True)
        file_path = (file_response.get("result") or {}).get("file_path") if isinstance(file_response, dict) and file_response.get("ok") else None
        if not file_path or ".." in file_path:
            continue
        try:
            url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"
            with urllib.request.urlopen(url, timeout=12) as upstream:
                content = upstream.read(20 * 1024 * 1024 + 1)
                content_type = upstream.headers.get_content_type()
            if len(content) > 20 * 1024 * 1024:
                return jsonify({"ok": False, "error": "media_too_large"}), 413
            filename = re.sub(r"[^A-Za-z0-9._-]", "_", str(media.get("name") or file_path.rsplit("/", 1)[-1]))[:160]
            disposition = "inline" if str(content_type).startswith(("image/", "video/", "audio/")) else "attachment"
            return Response(content, mimetype=content_type, headers={
                "Cache-Control": "private, max-age=1800",
                "Content-Disposition": f'{disposition}; filename="{filename or "telegram-file"}"',
            })
        except (OSError, urllib.error.URLError):
            continue
    return jsonify({"ok": False, "error": "media_download_failed"}), 502


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
            return jsonify({"ok": False, "error": "campaÃ±a no vÃ¡lida"}), 400
        try: scheduled = datetime.datetime.fromisoformat(when.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError: return jsonify({"ok": False, "error": "fecha no vÃ¡lida"}), 400
        if scheduled < datetime.datetime.utcnow() + datetime.timedelta(minutes=10):
            return jsonify({"ok": False, "error": "la fecha debe estar al menos a 10 minutos"}), 400
        target_url = str(body.get("target_url") or "").strip()
        if target_url and (urlparse(target_url).scheme not in ("http", "https") or not urlparse(target_url).netloc):
            return jsonify({"ok": False, "error": "enlace no vÃ¡lido"}), 400
        source, destination = _channel_stats.get_channel_meta(cid) or {}, _channel_stats.get_channel_meta(target) or {}
        _channel_stats.create_ad_request(cid, _master_id, source.get("name", f"Grupo {cid}"), target,
            destination.get("name", f"Grupo {target}"), text, when, from_image=body.get("image"),
            from_url=target_url, variants=json.dumps(body.get("variants") or [], ensure_ascii=False))
    else:
        ad = _channel_stats.get_ad(body.get("id"))
        if not ad or str(cid) not in (str(ad.get("from_chat")), str(ad.get("to_chat"))):
            return jsonify({"ok": False, "error": "campaÃ±a no encontrada"}), 404
        if action == "cancel" and ad.get("status") in ("pending", "countered", "master_review"):
            _channel_stats.update_ad(ad["id"], {"status": "cancelled"})
        elif action == "decline": _channel_stats.update_ad(ad["id"], {"status": "declined"})
        elif action == "accept":
            reciprocal = str(body.get("text") or "").strip()
            if not reciprocal: return jsonify({"ok": False, "error": "falta anuncio recÃ­proco"}), 400
            target_url = str(body.get("target_url") or "").strip()
            if target_url and (urlparse(target_url).scheme not in ("http", "https") or not urlparse(target_url).netloc):
                return jsonify({"ok": False, "error": "enlace no vÃ¡lido"}), 400
            _schedule_ad_pair(ad, _master_id, reciprocal, body.get("image"), target_url, ad.get("when"))
        else: return jsonify({"ok": False, "error": "acciÃ³n no permitida"}), 400
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
    elif action in ("warn", "unwarn"):
        bot = _known_internal_group(cid)
        if not bot:
            return jsonify({"ok": False, "error": "group_not_found"}), 404
        warns = _db.get(f"WARNS_{cid}", {}) or {}
        if not isinstance(warns, dict):
            warns = {}
        if action == "unwarn":
            warns.pop(uid, None)
            count = 0
        else:
            count = int(warns.get(uid, 0) or 0) + 1
            warns[uid] = count
        _db.set(f"WARNS_{cid}", warns)
        if action == "warn":
            bot.send_msg(cid, f"âš ï¸ Usuario `{uid}` advertido ({count}/3). Motivo: {reason}")
            if count >= 3:
                _ban_manager.ban_local_user(cid, uid, reason="3 advertencias", source="todosobrealltech")
                result = bot.api_call("banChatMember", {"chat_id": cid, "user_id": uid}, silent=True)
                telegram_results.append({"group_id": cid, "ok": bool(result.get("ok")), "auto_ban": True})
    elif action == "karma":
        try:
            value = max(-100, min(100, int(body.get("value", 5))))
        except (TypeError, ValueError):
            value = 5
        stats = stats or {"name": f"Usuario {uid}", "count": 0, "karma": 0}
        stats["karma"] = int(stats.get("karma", 0) or 0) + value
        users[uid] = stats
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


@bp.route("/api/internal/ban-directory")
def internal_ban_directory():
    """Paginated unified view for the trusted TodoSobreAllTech master panel."""
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    source = str(request.args.get("source", "all")).lower()
    query = str(request.args.get("q", "")).strip()
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = max(1, min(200, int(request.args.get("per_page", 100))))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "invalid_pagination"}), 400

    moon_records = _ban_manager.list_ban_records(query=query, status="all", limit=2000) if _ban_manager else []
    local_bans = _ban_manager.get_all_local_bans() if _ban_manager else {}
    local_rows = [{"user_id": str(uid), "source": "moonbot_local", "scope": "group",
                   "group_id": str(cid), "reason": "Baneo local del grupo", "status": "active"}
                  for cid, users in local_bans.items() for uid in users]
    profiles = (_get_global_user_stats() or {}) if _get_global_user_stats else {}
    moon_rows = list(moon_records) + local_rows
    for row in moon_rows:
        uid = str(row.get("user_id") or row.get("id") or "")
        profile = profiles.get(uid, {}) or {}
        if not isinstance(profile, dict):
            profile = {}
        row["user_id"] = uid
        row["name"] = str(row.get("name") or profile.get("name") or profile.get("first_name") or "")[:160]
        row["username"] = str(row.get("username") or profile.get("username") or "").lstrip("@")[:64]
        row["language"] = str(row.get("language") or profile.get("language_code") or "")[:16]
        row["last_seen"] = row.get("last_seen") or profile.get("last_seen")
        row["messages"] = int(row.get("messages") or profile.get("count") or 0)
    if query:
        needle = query.lower()
        moon_rows = [row for row in moon_rows if needle in str(row.get("user_id", "")).lower()
                     or needle in str(row.get("name", "")).lower()
                     or needle in str(row.get("username", "")).lower()
                     or needle in str(row.get("reason", "")).lower()
                     or needle in str(row.get("source", "")).lower()]
    cas_sources = {"cas", "cas_feed", "export.csv", "cas_export"}
    cas_rows = [row for row in moon_rows if str(row.get("source", "")).lower() in cas_sources]
    if source == "cas":
        moon_rows = cas_rows
    elif source == "moonbot":
        moon_rows = [row for row in moon_rows if str(row.get("source", "")).lower() not in cas_sources]
    moon_total = len(moon_rows)
    start = (page - 1) * per_page
    moon_page = moon_rows[start:start + per_page]
    return jsonify({"ok": True, "records": moon_page, "stats": {
        "cas": len(cas_rows), "moonbot": len(moon_records) + len(local_rows),
        "global": len(moon_records), "local": len(local_rows),
    }, "page": page, "per_page": per_page,
        "has_more": page * per_page < moon_total})


@bp.route("/api/internal/cas-sources/status")
def internal_cas_sources_status():
    """Estado agregado, sin exponer la lista CAS ni rutas internas del servidor."""
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    status = _get_cas_export_status() if _get_cas_export_status else {}
    count = max(0, int((status or {}).get("count", 0) or 0))
    loaded = bool((status or {}).get("loaded")) and count > 0
    return jsonify({"ok": True, "local_export": {"available": loaded, "loaded": loaded, "records": count},
                    "feed": {"available": bool((status or {}).get("feed_loaded")),
                             "records": max(0, int((status or {}).get("feed_count", 0) or 0))}})


def _global_captcha_status():
    _ensure_global_join_defaults()
    campaign = _db.get("GLOBAL_CAPTCHA_CAMPAIGN", {}) if _db else {}
    group_ids = [str(cid) for cid in campaign.get("group_ids", [])]
    jobs = [(_db.get(f"JOIN_BULK_JOB_{cid}", {}) or {}) for cid in group_ids]
    totals = {key: sum(int(job.get(key, 0) or 0) for job in jobs)
              for key in ("total", "processed", "muted", "private_sent", "private_blocked", "skipped")}
    running = sum(job.get("status") in ("running", "cancel_requested") for job in jobs)
    status = "running" if running else ("completed" if group_ids else "idle")
    percentage = round((totals["processed"] / totals["total"] * 100), 1) if totals["total"] else 0.0
    delivery_percentage = round((totals["private_sent"] / totals["processed"] * 100), 1) if totals["processed"] else 0.0
    names = (_get_global_chat_names() or {}) if _get_global_chat_names else {}
    profiles = (_get_global_user_stats() or {}) if _get_global_user_stats else {}
    group_details, remaining_users, user_details = [], [], []
    verified_users = 0
    unverified_users = 0
    for cid, job in zip(group_ids, jobs):
        observed = _db.get(f"TELEGRAM_GROUP_LANGUAGES_{cid}", {}) or {}
        remaining = []
        exempt = set(_join_config(cid).get("exempt_user_ids") or [])
        for raw_uid in observed.keys() if isinstance(observed, dict) else []:
            uid = str(raw_uid)
            if uid in exempt:
                continue
            captcha = _db.get(f"CAPTCHA_STATUS_{cid}_{uid}", {}) or {}
            captcha_status = captcha.get("status") or "pending"
            verified = captcha_status in ("passed", "exempt")
            verified_users += int(verified)
            unverified_users += int(not verified)
            pending = _db.get(f"JOINQ_{cid}_{uid}", {}) or {}
            appeal = _db.get(f"CAPTCHA_APPEAL_{cid}_{uid}", {}) or {}
            profile = profiles.get(uid, {}) or profiles.get(raw_uid, {}) or {}
            row = {"user_id": uid, "name": profile.get("name") or pending.get("first_name") or f"Usuario {uid}",
                   "group_id": cid, "group_name": str(names.get(cid) or f"Grupo {cid}"),
                   "verified": verified, "verification": "yes" if verified else "no",
                   "protocols": {
                       "telegram_mute": "applied" if pending.get("telegram_muted") else "pending",
                       "captcha": captcha_status,
                       "cas": "flagged" if pending.get("cas_flagged") else "pending",
                       "required_channels": "pending" if pending.get("subscription_pending") else
                           ("configured" if (_join_config(cid)["required_channels"] or _global_join_channel()) else "not_required"),
                       "appeal": appeal.get("status") or "available",
                   }}
            if len(user_details) < 500:
                user_details.append(row)
            if not verified:
                remaining.append(row)
                if len(remaining_users) < 250:
                    remaining_users.append(row)
        group_details.append({"group_id": cid, "name": str(names.get(cid) or f"Grupo {cid}"),
                              "status": job.get("status", "pending"), "total": int(job.get("total", 0) or 0),
                              "processed": int(job.get("processed", 0) or 0), "remaining": len(remaining)})
    total_remaining = sum(row["remaining"] for row in group_details)
    return {**campaign, **totals, "status": status, "running_groups": running,
            "groups": len(group_ids), "percentage": percentage,
            "delivery_percentage": delivery_percentage, "total_remaining": total_remaining,
            "verified_users": verified_users, "unverified_users": unverified_users,
            "all_verified": unverified_users == 0 and verified_users > 0,
            "group_details": group_details, "remaining_users": remaining_users,
            "user_details": user_details,
            "remaining_truncated": total_remaining > len(remaining_users),
            "users_truncated": verified_users + unverified_users > len(user_details)}


@bp.route("/api/internal/captcha-global", methods=["GET", "POST"])
def internal_captcha_global():
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    if request.method == "GET":
        return jsonify({"ok": True, "campaign": _global_captcha_status(),
                        "settings": _global_join_settings()})
    body = request.json or {}
    action = str(body.get("action", "start"))
    if action == "settings":
        channels, enabled, validation_error = _global_join_update_candidate(body)
        if validation_error:
            return jsonify({"ok": False, "error": validation_error}), 400
        if "channels" in body or "channel" in body:
            _db.set("JOIN_GLOBAL_REQUIRED_CHANNELS", channels)
            _db.set("JOIN_GLOBAL_REQUIRED_CHANNEL", channels[0] if channels else "")
        if "enabled" in body:
            _db.set("JOIN_GLOBAL_REQUIRED_ENABLED", enabled)
        if "strict_enforcement" in body:
            _db.set("JOIN_GLOBAL_STRICT_ENFORCEMENT", bool(body.get("strict_enforcement")))
        if "reverify_interval_days" in body:
            _db.set("JOIN_GLOBAL_REVERIFY_INTERVAL_DAYS",
                    _bounded_int(body.get("reverify_interval_days"), 0, 0, 90))
        if "reverify_interval_hours" in body:
            _db.set("JOIN_GLOBAL_REVERIFY_INTERVAL_HOURS",
                    _bounded_int(body.get("reverify_interval_hours"), 12, 0, 2160))
        if _add_audit_log:
            _add_audit_log("TodoSobreAllTech: configuraciÃ³n global de acceso actualizada")
        return jsonify({"ok": True, "campaign": _global_captcha_status(),
                        "settings": _global_join_settings()})
    if action == "cancel":
        campaign = _db.get("GLOBAL_CAPTCHA_CAMPAIGN", {}) or {}
        for cid in campaign.get("group_ids", []):
            job = _db.get(f"JOIN_BULK_JOB_{cid}", {}) or {}
            if job.get("status") == "running":
                job["status"] = "cancel_requested"
                _db.set(f"JOIN_BULK_JOB_{cid}", job)
        return jsonify({"ok": True, "campaign": _global_captcha_status()})
    if action != "start":
        return jsonify({"ok": False, "error": "invalid_action"}), 400
    current = _global_captcha_status()
    if current.get("status") == "running":
        return jsonify({"ok": True, "started": False, "campaign": current})
    started_groups = []
    # Solo grupos reales de Telegram. El inventario administrativo tambiÃ©n
    # contiene chats privados e identidades con ID positivo; nunca deben
    # convertirse en destinos de una campaÃ±a global.
    group_ids = {str(row.get("id")) for row in _admin_group_rows()
                 if str(row.get("ctype", "")).lower() in ("group", "supergroup")
                 and str(row.get("id", "")).startswith("-")}
    for cid in sorted(group_ids):
        bot = _known_internal_group(cid)
        if not bot:
            continue
        _, started = _start_bulk_captcha(bot, cid, "web-master-global", only_pending=True)
        if started:
            started_groups.append(str(cid))
    campaign = {"id": secrets.token_urlsafe(12), "group_ids": started_groups,
                "started_at": int(time.time()), "mode": "pending_only",
                "protocols": ["telegram_mute", "captcha", "cas", "required_channels", "appeal"]}
    _db.set("GLOBAL_CAPTCHA_CAMPAIGN", campaign)
    if _add_audit_log:
        _add_audit_log(f"TodoSobreAllTech: captcha global iniciado en {len(started_groups)} grupos")
    return jsonify({"ok": True, "started": True, "campaign": _global_captcha_status()})


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
            engine.editorial_decision(item["id"], "todosobrealltech", "approved", "PublicaciÃƒÂ³n inmediata")
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
        {"id": "welcome", "name": "Bienvenida automÃ¡tica", "description": "Responde al primer saludo del grupo.",
         "kind": "rule", "keyword": "hola", "response": "Â¡Bienvenido! Consulta las normas fijadas antes de participar."},
        {"id": "support", "name": "DerivaciÃ³n a soporte", "description": "Orienta las solicitudes de ayuda.",
         "kind": "rule", "keyword": "ayuda", "response": "CuÃ©ntanos el problema y un administrador lo revisarÃ¡."},
        {"id": "report", "name": "Formulario de incidencias", "description": "Recoge informes estructurados.",
         "kind": "form", "title": "Informar de una incidencia", "fields": [
             {"name": "description", "label": "DescripciÃ³n", "type": "textarea", "required": True},
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
                raise ValueError("tÃ­tulo y campos son obligatorios")
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
    """AdministraciÃ³n de extensiones y API; los tokens solo se muestran al crearlos."""
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
                raise ValueError("nombre, versiÃ³n y checksum hexadecimal son obligatorios")
            result = engine.module_register(name, version, permissions, checksum.lower(), False)
        elif action == "token_create":
            scopes = sorted(set(body.get("scopes") or []))
            if not scopes or any(scope not in allowed_scopes for scope in scopes):
                raise ValueError("Ã¡mbitos de API no vÃ¡lidos")
            result = engine.api_token(body.get("name", "IntegraciÃ³n"), scopes, body.get("expires_at") or None)
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
            if not bot_id or not method: raise ValueError("bot y mÃ©todo son obligatorios")
            result = engine.quota(bot_id, method, body.get("used", 0), body.get("limit", 1), body.get("reset_at"))
        elif action == "config_export":
            group_id = str(body.get("group_id", ""))
            if group_id not in _known_internal_group_ids(): return jsonify({"ok": False, "error": "group_not_found"}), 404
            result = engine.signed_config({"group_id": group_id, "config": GroupSuite(_db).config(group_id),
                                           "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat()})
        elif action == "config_import":
            bundle = body.get("bundle") if isinstance(body.get("bundle"), dict) else {}
            if not engine.verify_config(bundle): raise ValueError("firma de configuraciÃ³n invÃ¡lida")
            payload = bundle.get("payload") or {}; group_id = str(payload.get("group_id", ""))
            if group_id not in _known_internal_group_ids() or not isinstance(payload.get("config"), dict):
                raise ValueError("grupo o configuraciÃ³n no vÃ¡lidos")
            result = {"group_id": group_id, "config": GroupSuite(_db).save_config(
                group_id, payload["config"], actor="web-master", source="signed_import"
            )}
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
    """PlanificaciÃ³n operativa; no ejecuta restauraciones ni despliegues destructivos."""
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
            if not version or not instances: raise ValueError("versiÃ³n e instancias son obligatorias")
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
            if status not in ("ok", "healthy", "degraded", "offline", "unknown"): raise ValueError("estado de dependencia no vÃ¡lido")
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
        {"id": "groups", "name": "Administrar grupos", "area": "AdministraciÃ³n"},
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
        for alert in reversed(_safe_list(_db.get("AI_LEARNING_NOTIFICATIONS", []))[-20:]):
            if isinstance(alert, dict):
                pending.append({**alert, "count": 1, "read": False})
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
        return None, (jsonify({"ok": False, "error": "clave invÃ¡lida"}), 401)
    now_minute = int(time.time() // 60)
    bucket = f"{token.get('id')}:{now_minute}"
    # Mantener Ãºnicamente los contadores del minuto actual.
    if len(_community_api_usage) > 500:
        _community_api_usage.clear()
    used = int(_community_api_usage.get(bucket, 0)) + 1
    _community_api_usage[bucket] = used
    if used > 120:
        response = jsonify({"ok": False, "error": "lÃ­mite de peticiones alcanzado"})
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
            return jsonify({"ok": False, "error": "todos los IDs deben ser numÃ©ricos"}), 400
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


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Auth Mini App (Telegram) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@bp.route("/api/public/tg_auth", methods=["POST", "OPTIONS"])
def tg_auth():
    """Valida el initData de la Mini App y dice si el usuario es el master.
    Si lo es, emite un JWT vÃ¡lido para el panel admin (auto-login)."""
    if request.method == "OPTIONS":
        return ("", 204)
    init_data = (request.json or {}).get("initData", "")
    user = _verify_init_data(init_data)
    if user is None:
        return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
    is_master = _master_id is not None and str(user.get("id")) == str(_master_id)
    release_channel = _miniapp_release_channel(user)
    resp = {"ok": True, "is_master": is_master, "is_web_admin": _verified_web_admin(user),
            "release_channel": release_channel, "app_version": APP_VERSION,
            "user": {
        "id": user.get("id"), "first_name": user.get("first_name"), "username": user.get("username"),
    }}
    if _jwt_secret:
        resp["token"] = jwt.encode(
            {"exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
             "scope": "miniapp_master" if is_master else "miniapp_user", "sub": str(user.get("id"))},
            _jwt_secret, algorithm="HS256",
        )
    return jsonify(resp)


@bp.route("/api/public/release-channels/admin", methods=["POST", "OPTIONS"])
def release_channels_admin():
    """List and assign Telegram users to simulator channels. Master only."""
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.get_json(silent=True) or {}
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
    if not _is_master(user):
        return jsonify({"ok": False, "error": "solo el master puede asignar canales"}), 403
    pb = getattr(_channel_stats, "_pb", None)
    if not pb:
        return jsonify({"ok": False, "error": "PocketBase no disponible"}), 503
    try:
        ensure_release_schema(pb)
        action = str(body.get("action") or "list").lower()
        if action == "assign":
            assign_release_channel(
                pb, body.get("telegram_id"), body.get("release_channel"),
                display_name=body.get("display_name"), assigned_by=user.get("id"),
                assigned_at=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.000Z"),
            )
        elif action == "revoke":
            revoke_release_channel(pb, body.get("telegram_id"))
        elif action != "list":
            return jsonify({"ok": False, "error": "acciÃ³n no vÃ¡lida"}), 400
        rows = list_release_assignments(pb)
        assignments = [{key: row.get(key) for key in (
            "telegram_id", "display_name", "release_channel", "enabled", "assigned_at"
        )} for row in rows]
        return jsonify({"ok": True, "assignments": assignments})
    except ValueError as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    except Exception as error:
        return jsonify({"ok": False, "error": f"No se pudieron guardar los canales: {error}"}), 503


@bp.route("/api/public/hub-release-asset", methods=["POST", "OPTIONS"])
def hub_release_asset():
    """Serve an allowlisted asset for the Telegram-verified release channel only."""
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.get_json(silent=True) or {}
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
    channel = _miniapp_release_channel(user)
    try:
        payload, content_type = read_hub_release_asset(channel, body.get("asset", "manifest"))
    except KeyError:
        return jsonify({"ok": False, "error": "asset no disponible"}), 404
    except (OSError, TypeError, ValueError):
        return jsonify({"ok": False, "error": "asset invÃ¡lido"}), 400
    response = Response(payload, content_type=content_type)
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Moon-Release-Channel"] = channel
    return response


def _is_master(user):
    return _master_id is not None and str(user.get("id")) == str(_master_id)


@bp.route("/api/public/admin/channels", methods=["POST", "OPTIONS"])
def admin_all_channels():
    """TODOS los canales/grupos donde estÃ¡ el bot. Solo el dueÃ±o del bot (master)."""
    if request.method == "OPTIONS":
        return ("", 204)
    user = _verify_init_data((request.json or {}).get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
    if not _is_master(user):
        return jsonify({"ok": False, "error": "solo el dueÃ±o del bot"}), 403
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


@bp.route("/api/internal/groups/<cid>/rss", methods=["GET", "POST"])
def internal_group_rss(cid):
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    if not _known_internal_group(cid):
        return jsonify({"ok": False, "error": "group_not_found"}), 404
    body = (request.json or {}) if request.method == "POST" else {"action": "list"}
    payload, status = _rss_action(cid, body, "web-master")
    return jsonify(payload), status


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Master Suite Endpoints â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bp.route("/api/public/master/stats", methods=["POST", "OPTIONS"])
def master_stats_ep():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}
    user, err = _auth_user(body)
    if err: return err
    if not _is_master(user): return jsonify({"ok": False, "error": "solo master"}), 403
    
    import psutil, os
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.1) if psutil.cpu_percent() == 0 else psutil.cpu_percent()
    ram_used = round(mem.used / (1024**3), 2)
    ram_total = round(mem.total / (1024**3), 2)
    
    active_bots_list = _get_active_bots() if _get_active_bots else []
    bots_info = [{"name": getattr(b, "bot_username", "bot"), "token_mask": f"{b.token[:4]}...{b.token[-4:]}" if getattr(b, "token", None) else "â€”"} for b in active_bots_list]
    
    settings = _db.get("GLOBAL_SETTINGS", {}) if _db else {}
    bans = _db.get("GLOBAL_BANS", {"users": []}) if _db else {"users": []}
    
    plugins = []
    if os.path.exists("plugins"):
        for f in os.listdir("plugins"):
            if f.endswith(".py"): plugins.append({"name": f.replace(".py", ""), "status": "enabled"})
            elif f.endswith(".disabled"): plugins.append({"name": f.replace(".disabled", ""), "status": "disabled"})
            
    return jsonify({
        "ok": True,
        "cpu": cpu,
        "ram": mem.percent,
        "ram_used": ram_used,
        "ram_total": ram_total,
        "bots": bots_info,
        "settings": settings,
        "bans_count": len(bans.get("users", [])),
        "plugins": plugins,
        "total_channels": len(_channel_stats.get_all_channels()) if _channel_stats else 0,
    })


@bp.route("/api/public/master/setting", methods=["POST", "OPTIONS"])
def master_set_setting():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}
    user, err = _auth_user(body)
    if err: return err
    if not _is_master(user): return jsonify({"ok": False, "error": "solo master"}), 403
    key, val = body.get("key"), body.get("value")
    if not key or _db is None: return jsonify({"ok": False, "error": "datos invÃ¡lidos"}), 400
    st = _db.get("GLOBAL_SETTINGS", {})
    st[key] = val
    _db.set("GLOBAL_SETTINGS", st)
    return jsonify({"ok": True, "key": key, "value": val})


@bp.route("/api/public/master/broadcast", methods=["POST", "OPTIONS"])
def master_broadcast():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}
    user, err = _auth_user(body)
    if err: return err
    if not _is_master(user): return jsonify({"ok": False, "error": "solo master"}), 403
    text = (body.get("text") or "").strip()
    if not text: return jsonify({"ok": False, "error": "mensaje vacÃ­o"}), 400
    
    all_ch = _channel_stats.get_all_channels() if _channel_stats else []
    sent = 0
    bot = _hub_bot()
    is_pin = bool(body.get("pin", False))
    is_silent = bool(body.get("silent", False))
    if bot:
        for ch in all_ch:
            cid = ch.get("chat_id")
            if cid:
                try:
                    res = bot.api_call("sendMessage", {
                        "chat_id": cid,
                        "text": text,
                        "parse_mode": "Markdown",
                        "disable_notification": is_silent
                    })
                    if is_pin and res.get("ok") and res.get("result", {}).get("message_id"):
                        bot.api_call("pinChatMessage", {
                            "chat_id": cid,
                            "message_id": res["result"]["message_id"],
                            "disable_notification": is_silent
                        })
                    sent += 1
                except Exception:
                    pass
    return jsonify({"ok": True, "sent": sent, "total": len(all_ch)})


@bp.route("/api/public/master/backup_now", methods=["POST", "OPTIONS"])
def master_backup_now():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}
    user, err = _auth_user(body)
    if err: return err
    if not _is_master(user): return jsonify({"ok": False, "error": "solo master"}), 403
    bot = _hub_bot()
    if not bot: return jsonify({"ok": False, "error": "sin bot activo"}), 503
    master_id = os.getenv("MASTER_ID")
    if not master_id: return jsonify({"ok": False, "error": "MASTER_ID no configurado"}), 400
    db_paths = ["data/moon_database.db", "data/multibot.db", "data/bots.json"]
    sent = 0
    for p in db_paths:
        if os.path.exists(p):
            try:
                bot.send_document(master_id, p, f"ðŸ“¦ Backup Moonbot: {os.path.basename(p)}")
                sent += 1
            except Exception as e:
                pass
    return jsonify({"ok": True, "sent_files": sent})


@bp.route("/api/public/master/diagnostics", methods=["POST", "OPTIONS"])
def master_diagnostics():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}
    user, err = _auth_user(body)
    if err: return err
    if not _is_master(user): return jsonify({"ok": False, "error": "solo master"}), 403
    
    # 1. Telegram check
    bot = _hub_bot()
    tg_ok = False
    if bot:
        me = bot.api_call("getMe", {})
        tg_ok = bool(me.get("ok"))
        
    # 2. Ollama check
    ollama_ok = False
    try:
        r = requests.get(f"{os.getenv('OLLAMA_HOST', 'http://localhost:11434')}/api/tags", timeout=3)
        ollama_ok = (r.status_code == 200)
    except:
        pass

    # 3. Gemini check
    gemini_configured = bool(os.getenv("GEMINI_API_KEY"))
    
    # 4. DB check
    db_ok = _db is not None
    db_size_mb = 0
    for db_f in ["data/moon_database.db", "data/multibot.db"]:
        if os.path.exists(db_f):
            db_size_mb = round(os.path.getsize(db_f) / (1024 * 1024), 2)
            break
            
    return jsonify({
        "ok": True,
        "checks": {
            "telegram_api": {"status": "ok" if tg_ok else "error", "label": "Telegram Bot API"},
            "ollama_local": {"status": "ok" if ollama_ok else "warning", "label": "Ollama LLM Local"},
            "gemini_api": {"status": "ok" if gemini_configured else "warning", "label": "Google Gemini API"},
            "database_sqlite": {"status": "ok" if db_ok else "error", "label": f"SQLite WAL ({db_size_mb} MB)"}
        }
    })


@bp.route("/api/public/ia/query", methods=["POST", "OPTIONS"])
def ia_query():
    """Consulta directa a la IA Moon Core desde el Hub."""
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}
    user, err = _auth_user(body)
    if err: return err
    prompt = (body.get("prompt") or "").strip()
    if not prompt: return jsonify({"ok": False, "error": "falta prompt"}), 400
    bot = _hub_bot()
    if not bot or not hasattr(bot, "ia_nativa") or not bot.ia_nativa:
        return jsonify({"ok": False, "error": "IA no disponible en este momento"}), 503
    try:
        pref = body.get("ai_preference")
        reply = bot.ia_nativa.generate(prompt, chat_id=user.get("id"))
        return jsonify({"ok": True, "reply": reply})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@bp.route("/api/public/ia/vision", methods=["POST", "OPTIONS"])
def ia_vision():
    """AnÃ¡lisis de imagen simulado (VisiÃ³n IA)."""
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}
    user, err = _auth_user(body)
    if err: return err
    url = (body.get("url") or "").strip()
    if not url: return jsonify({"ok": False, "error": "falta url"}), 400
    
    # Simulate vision OCR & NSFW detection
    import time
    time.sleep(1.2) # Simulate processing time
    
    is_nsfw = "nsfw" in url.lower() or "adult" in url.lower()
    ocr_result = "TEXTO DETECTADO:\n- 1.0 kg de azÃºcar\n- Lote 4509B" if "ticket" in url.lower() or "factura" in url.lower() else "TELEBOTS MOON CORE v16.85"
    
    return jsonify({
        "ok": True,
        "nsfw": is_nsfw,
        "ocr_text": ocr_result
    })


@bp.route("/api/public/ia/brain_stats", methods=["POST", "OPTIONS"])
def ia_brain_stats():
    """EstadÃ­sticas en vivo del Cerebro IA Moon Core."""
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}
    user, err = _auth_user(body)
    if err: return err
    bot = _hub_bot()
    words = 0
    conns = 0
    if bot and hasattr(bot, "ia_nativa") and bot.ia_nativa:
        words = len(getattr(bot.ia_nativa, "knowledge", {}) or {})
        conns = len(getattr(bot.ia_nativa, "associations", {}) or {})
    if _db:
        words = words or len(_db.get("IA_KNOWLEDGE", {}) or {})
        conns = conns or len(_db.get("IA_ASSOCIATIONS", {}) or {})
        feeders = len(_db.get("IA_FEEDERS", []) or [])
    else:
        feeders = 0
    return jsonify({
        "ok": True,
        "words": words,
        "connections": conns,
        "feeders": feeders,
        "rate": "12.4 p/min",
        "maturity": "Neuronal Nivel 4"
    })


@bp.route("/api/public/business/config", methods=["GET", "POST", "OPTIONS"])
def business_config():
    """Obtener o guardar automatizaciones de Telegram Business."""
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}
    user, err = _auth_user(body)
    if err: return err
    if request.method == "GET" or not body.get("save"):
        cfg = _db.get("BUSINESS_CONFIG", {}) if _db else {}
        conns = _db.get("BUSINESS_CONNECTIONS", {}) if _db else {}
        return jsonify({
            "ok": True,
            "config": {
                "greeting_msg": cfg.get("greeting_msg", ""),
                "away_msg": cfg.get("away_msg", ""),
                "away_mode": bool(cfg.get("away_mode", False)),
                "ia_auto": bool(cfg.get("ia_auto", False)),
                "quick_replies": cfg.get("quick_replies", [
                    {"cmd": "/info", "text": "Â¡Hola! Somos ComunidadTelebots."},
                    {"cmd": "/soporte", "text": "Nuestro equipo te responderÃ¡ enseguida."}
                ])
            },
            "connections_count": len(conns)
        })
    # Guardar
    cfg = _db.get("BUSINESS_CONFIG", {}) if _db else {}
    for k in ["greeting_msg", "away_msg", "away_mode", "ia_auto", "quick_replies"]:
        if k in body:
            cfg[k] = body[k]
    if _db:
        _db.set("BUSINESS_CONFIG", cfg)
    return jsonify({"ok": True, "config": cfg})


@bp.route("/api/public/admin/set_listed", methods=["POST", "OPTIONS"])
def admin_set_listed():
    """Solicitar publicaciÃ³n; el master puede aprobarla directamente."""
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
    chat_id = body.get("chat_id")
    listed = bool(body.get("listed"))
    if chat_id is None:
        return jsonify({"ok": False, "error": "falta chat_id"}), 400
    allowed = _is_master(user) or _channel_stats.is_user_admin_of(user.get("id"), chat_id)
    if not allowed:
        return jsonify({"ok": False, "error": "sin permiso sobre ese canal"}), 403
    if listed and _is_master(user):
        record = _channel_stats.review_listing(chat_id, "approved", user.get("id"))
    else:
        record = _channel_stats.request_listing(chat_id, listed, user.get("id"))
    return jsonify({"ok": True, "chat_id": chat_id, "listed": bool(record and record.get("listed")),
                    "directory_status": (record or {}).get("directory_status", "unreviewed")})


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ GestiÃ³n de grupo (admin/creador) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _group_auth(body):
    """Devuelve (user, chat_id) si el usuario puede gestionar ese chat, o (None, resp_error)."""
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return None, (jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401)
    chat_id = body.get("chat_id")
    if chat_id is None:
        return None, (jsonify({"ok": False, "error": "falta chat_id"}), 400)
    if not (_is_master(user) or _channel_stats.is_user_admin_of(user.get("id"), chat_id)):
        return None, (jsonify({"ok": False, "error": "sin permiso sobre ese chat"}), 403)
    return (user, chat_id), None


def _rss_manager():
    return GroupRssManager(_db)


def _rss_action(chat_id, body, actor):
    manager = _rss_manager()
    action = str(body.get("action") or "list")
    try:
        if action == "add":
            feed = manager.add(chat_id, body.get("url"), body.get("title"), actor)
            return {"ok": True, "feed": feed, "feeds": manager.list(chat_id)}, 201
        if action == "toggle":
            feed = manager.set_enabled(chat_id, body.get("feed_id"), body.get("enabled"))
            return {"ok": True, "feed": feed, "feeds": manager.list(chat_id)}, 200
        if action == "configure":
            feed = manager.configure(chat_id, body.get("feed_id"), body)
            return {"ok": True, "feed": feed, "feeds": manager.list(chat_id)}, 200
        if action == "reset_cursor":
            feed = manager.reset_cursor(chat_id, body.get("feed_id"))
            return {"ok": True, "feed": feed, "feeds": manager.list(chat_id)}, 200
        if action == "reset_metrics":
            feed = manager.reset_metrics(chat_id, body.get("feed_id"))
            return {"ok": True, "feed": feed, "feeds": manager.list(chat_id),
                    "history": manager.history(chat_id)}, 200
        if action == "clear_history":
            manager.clear_history(chat_id)
            return {"ok": True, "feeds": manager.list(chat_id), "history": []}, 200
        if action == "delete":
            manager.remove(chat_id, body.get("feed_id"))
            return {"ok": True, "feeds": manager.list(chat_id)}, 200
        if action == "test":
            feed = next((row for row in manager.list(chat_id) if row.get("id") == str(body.get("feed_id"))), None)
            if not feed:
                return {"ok": False, "error": "RSS no encontrado"}, 404
            return {"ok": True, "entries": manager.fetch(feed["url"])[:5], "feeds": manager.list(chat_id)}, 200
        if action == "run_now":
            feed_id = str(body.get("feed_id") or "")
            if not any(row.get("id") == feed_id for row in manager.list(chat_id)):
                return {"ok": False, "error": "RSS no encontrado"}, 404
            bot = _get_bot_for_chat(chat_id) if _get_bot_for_chat else None
            if not bot:
                return {"ok": False, "error": "bot no disponible"}, 503
            entries = manager.poll(chat_filter=chat_id, feed_filter=feed_id, force=True)
            sent = 0
            for entry in entries:
                title = str(entry.get("title") or "Nueva publicaciÃ³n").replace("[", "\\[").replace("]", "\\]")
                source = str(entry.get("source") or "RSS").replace("[", "\\[").replace("]", "\\]")
                text = str(entry.get("template") or "ðŸ“° **{title}**\n{url}")
                text = text.replace("{title}", title).replace("{url}", entry["url"]).replace("{source}", source)
                result = bot.send_msg(chat_id, text[:4096], parse_mode="Markdown",
                                      message_thread_id=entry.get("message_thread_id"))
                if isinstance(result, dict) and result.get("ok"):
                    manager.mark_published(chat_id, feed_id, entry)
                    sent += 1
            return {"ok": True, "sent": sent, "initialized": not entries,
                    "feeds": manager.list(chat_id)}, 200
        return {"ok": True, "feeds": manager.list(chat_id), "history": manager.history(chat_id),
                "limit": manager.MAX_FEEDS}, 200
    except KeyError as error:
        return {"ok": False, "error": str(error).strip("'")}, 404
    except (ValueError, urllib.error.URLError, ET.ParseError) as error:
        return {"ok": False, "error": str(error)}, 400


@bp.route("/api/public/group/rss", methods=["POST", "OPTIONS"])
def group_rss():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    user, chat_id = res
    payload, status = _rss_action(chat_id, body, user.get("id"))
    return jsonify(payload), status


@bp.route("/api/public/group/paid-subscriptions", methods=["POST", "OPTIONS"])
def group_paid_subscriptions():
    """Official Telegram Stars subscription links for channel administrators."""
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    user, chat_id = res
    bot = _get_bot_for_chat(chat_id) if _get_bot_for_chat else None
    if not bot:
        return jsonify({"ok": False, "error": "bot no disponible"}), 503
    chat_response = bot.api_call("getChat", {"chat_id": chat_id}, silent=True)
    chat = chat_response.get("result", {}) if isinstance(chat_response, dict) and chat_response.get("ok") else {}
    if chat.get("type") != "channel":
        return jsonify({"ok": False, "error": "Las suscripciones de pago solo estÃ¡n disponibles en canales"}), 400
    member_response = bot.api_call("getChatMember", {"chat_id": chat_id, "user_id": bot.bot_id}, silent=True)
    member = member_response.get("result", {}) if isinstance(member_response, dict) and member_response.get("ok") else {}
    if member.get("status") != "creator" and not member.get("can_invite_users"):
        return jsonify({"ok": False, "error": "El bot necesita permiso para invitar usuarios"}), 403
    action = str(body.get("action") or "list").lower()
    links = _paid_subscription_links(chat_id)
    if action == "list":
        return jsonify({"ok": True, "currency": "XTR", "period_seconds": 2592000, "links": links})
    name = str(body.get("name") or "").strip()
    invite_link = str(body.get("invite_link") or "").strip()
    if len(name) > 32:
        return jsonify({"ok": False, "error": "El nombre no puede superar 32 caracteres"}), 400
    if action == "create":
        try:
            price = int(body.get("subscription_price"))
        except (TypeError, ValueError):
            return jsonify({"ok": False, "error": "Precio no vÃ¡lido"}), 400
        if not 1 <= price <= 10000:
            return jsonify({"ok": False, "error": "El precio debe estar entre 1 y 10.000 Stars"}), 400
        result = bot.api_call("createChatSubscriptionInviteLink", {"chat_id": chat_id, "name": name,
            "subscription_period": 2592000, "subscription_price": price}, silent=True)
        if not isinstance(result, dict) or not result.get("ok"):
            return jsonify({"ok": False, "error": (result or {}).get("description", "Telegram rechazÃ³ el enlace")}), 502
        item = result.get("result") or {}
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        links.insert(0, {"invite_link": item.get("invite_link"), "name": item.get("name") or name,
            "subscription_period": item.get("subscription_period") or 2592000,
            "subscription_price": item.get("subscription_price") or price, "is_revoked": False,
            "created_at": now, "updated_at": now})
    elif action in {"rename", "revoke"}:
        if not invite_link:
            return jsonify({"ok": False, "error": "Falta el enlace"}), 400
        method = "editChatSubscriptionInviteLink" if action == "rename" else "revokeChatInviteLink"
        params = {"chat_id": chat_id, "invite_link": invite_link}
        if action == "rename":
            params["name"] = name
        result = bot.api_call(method, params, silent=True)
        if not isinstance(result, dict) or not result.get("ok"):
            return jsonify({"ok": False, "error": (result or {}).get("description", "Telegram rechazÃ³ la operaciÃ³n")}), 502
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        for item in links:
            if item["invite_link"] == invite_link:
                item["updated_at"] = now
                if action == "rename": item["name"] = name
                else: item["is_revoked"] = True
    else:
        return jsonify({"ok": False, "error": "AcciÃ³n no vÃ¡lida"}), 400
    _db.set(f"PAID_SUBSCRIPTION_LINKS_{chat_id}", links[:100])
    if _add_audit_log:
        _add_audit_log(f"Suscripcion Telegram Stars: {action} en canal {chat_id} por {user.get('id')}")
    return jsonify({"ok": True, "currency": "XTR", "period_seconds": 2592000,
                    "links": _paid_subscription_links(chat_id)})


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
    config = _db.get(f"CONFIG_{chat_id}", {"auto_mod": True, "welcome": False, "ia_learning": False, "security_shield": True, "captcha_enabled": False, "captcha_type": "button", "captcha_timeout": 60, "captcha_action": "kick", "anti_link": False, "anti_flood": False, "anti_forward": False, "anti_stickers": False, "night_mode": False, "warn_limit": 3})
    warns = _db.get(f"WARNS_{chat_id}", {})
    bans = _ban_manager.get_local_bans(chat_id).get("users", []) if _ban_manager else []
    sched = [{"id": s["id"], "text": s.get("text"), "send_at": s.get("send_at")}
             for s in _channel_stats.list_scheduled(chat_id)]
    bw = _db.get(f"BADWORDS_{chat_id}", {"words": [], "action": "delete"})
    if not isinstance(bw, dict):
        bw = {"words": [], "action": "delete"}
    welcome_text = _db.get(f"PLUGIN_WELCOME_{chat_id}", "")
    return jsonify({"ok": True, "meta": meta, "role": ("creator" if _is_master(user) else None),
                    "config": config,
                    "welcome_msg": welcome_text,
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
    """Propone un usuario al registro global; nunca aplica el ban automÃ¡ticamente."""
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
    evidence = report.get("evidence", []) if report else []
    analysis_text = " ".join([reason] + [str(item) for item in evidence])[:5000]
    spam_result = SpamRiskEngine(_db).analyze(chat_id, user_id, analysis_text, karma=0)
    try:
        cas_result = _check_cas(user_id) if _check_cas else None
    except Exception:
        cas_result = None
    context = {"local_ban_groups": [], "captcha_fail_groups": [], "warning_count": 0,
               "spam_events": 0, "ham_events": 0}
    channels = (_channel_stats.get_all_channels() if _channel_stats else []) or []
    seen = set()
    for channel in channels[:500]:
        cid = str(channel.get("chat_id", "")).strip() if isinstance(channel, dict) else ""
        if not cid or cid in seen:
            continue
        seen.add(cid)
        if user_id in {str(value) for value in _ban_manager.get_local_bans(cid).get("users", [])}:
            context["local_ban_groups"].append(cid)
        warns = _db.get(f"WARNS_{cid}", {}) if _db else {}
        context["warning_count"] += int((warns if isinstance(warns, dict) else {}).get(user_id, 0) or 0)
        captcha = _db.get(f"CAPTCHA_STATUS_{cid}_{user_id}", {}) if _db else {}
        if isinstance(captcha, dict) and captcha.get("status") == "failed":
            context["captcha_fail_groups"].append(cid)
        events = _db.get(f"SPAMEVENTS_{cid}", []) if _db else []
        for event in events[-200:] if isinstance(events, list) else []:
            if not isinstance(event, dict) or str(event.get("user_id")) != user_id:
                continue
            if event.get("feedback") == "ham":
                context["ham_events"] += 1
            elif event.get("feedback") == "spam" or int(event.get("score", 0) or 0) >= 70:
                context["spam_events"] += 1
    report = _ban_manager.analyze_ban_report(
        report.get("id"), spam_result=spam_result, cas_result=cas_result, context=context
    ) if report else report
    if _add_audit_log and report:
        analysis = report.get("analysis") or {}
        _add_audit_log(
            f"Propuesta GBAN {report.get('id')} Â· usuario {user_id} Â· "
            f"riesgo {analysis.get('score', 0)}/100 Â· automÃ¡tico {bool(report.get('auto_ban_applied'))}"
        )
    hub = _hub_bot()
    if hub and report and _master_id:
        rich = _ban_manager.gban_intelligence.render_markdown(report)
        keyboard = {"inline_keyboard": [[
            {"text": "âœ… Confirmar GBAN", "callback_data": f"gban_report:approved:{report.get('id')}"},
            {"text": "â†©ï¸ Revocar", "callback_data": f"gban_report:rejected:{report.get('id')}"},
        ]]}
        sent = hub.send_rich_message(
            _master_id, markdown=rich, fallback_text=rich, reply_markup=keyboard,
            protect_content=True,
        )
        message_id = ((sent or {}).get("result") or {}).get("message_id") if isinstance(sent, dict) else None
        if message_id:
            _ban_manager.attach_report_notification(report.get("id"), _master_id, message_id)
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


@bp.route("/api/public/master/ban-report/resolve", methods=["POST", "OPTIONS"])
def master_ban_report_resolve():
    """Permite al master confirmar o revocar una propuesta desde la Mini App."""
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user = _verify_init_data(body.get("initData", ""))
    if user is None or not _is_master(user):
        return jsonify({"ok": False, "error": "solo el master puede resolver reportes"}), 403
    report_id = str(body.get("report_id", "")).strip()
    decision = str(body.get("decision", "")).strip()
    if decision not in ("approved", "rejected"):
        return jsonify({"ok": False, "error": "decisiÃ³n invÃ¡lida"}), 400
    pending = next((item for item in _ban_manager.list_ban_reports(status="pending", limit=2000)
                    if str(item.get("id")) == report_id), None) if _ban_manager else None
    if not pending:
        return jsonify({"ok": False, "error": "reporte no encontrado o ya resuelto"}), 404
    if decision == "approved":
        _ban_manager.ban_user(
            pending.get("user_id"), reason=pending.get("reason"), source="group_admin_report",
            reported_by=pending.get("reported_by"), evidence=pending.get("evidence"),
            groups=[pending.get("chat_id")], reviewed=True,
        )
    elif pending.get("auto_ban_applied"):
        _ban_manager.unban_user(pending.get("user_id"))
    report = _ban_manager.resolve_ban_report(report_id, decision, user.get("id"))
    if _add_audit_log:
        _add_audit_log(f"Reporte GBAN {report_id} {decision} desde Mini App por {user.get('id')}")
    return jsonify({"ok": True, "report": report})


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


def _house_ad_metric_context(row, body, metric):
    """Actualiza contadores diarios y dimensiones Telegram sin guardar datos personales."""
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    if row.get("metrics_day") != today:
        row.update({"metrics_day": today, "clicks_today": 0, "impressions_today": 0})
    daily_key = "clicks_today" if metric == "click" else "impressions_today"
    row[daily_key] = int(row.get(daily_key, 0) or 0) + 1
    for body_key, field in (("chat_id", f"{metric}s_by_chat"), ("bot_id", f"{metric}s_by_bot")):
        raw = str(body.get(body_key) or "").strip()
        pattern = r"-?\d{5,24}" if body_key == "chat_id" else r"\d{5,24}"
        if not re.fullmatch(pattern, raw):
            continue
        values = dict(row.get(field) or {})
        values[raw] = int(values.get(raw, 0) or 0) + 1
        row[field] = values


def _house_ads_insights(rows):
    """Resume la entrega para el master sin exponer datos personales."""
    totals = {"campaigns": len(rows), "enabled": 0, "clicks": 0, "impressions": 0,
              "clicks_today": 0, "impressions_today": 0}
    chats, bots, campaigns = {}, {}, []
    for row in rows:
        clicks = int(row.get("clicks", 0) or 0)
        impressions = int(row.get("impressions", 0) or 0)
        clicks_today = int(row.get("clicks_today", 0) or 0)
        impressions_today = int(row.get("impressions_today", 0) or 0)
        enabled = bool(row.get("enabled", True) and row.get("approval_status", "approved") == "approved")
        totals["enabled"] += int(enabled)
        totals["clicks"] += clicks; totals["impressions"] += impressions
        totals["clicks_today"] += clicks_today; totals["impressions_today"] += impressions_today
        for dimension, destination in (("chat", chats), ("bot", bots)):
            for metric in ("clicks", "impressions"):
                values = row.get(f"{metric}_by_{dimension}") or {}
                if not isinstance(values, dict):
                    continue
                for identifier, value in values.items():
                    if not re.fullmatch(r"-?\d{5,24}", str(identifier)):
                        continue
                    item = destination.setdefault(str(identifier), {"id": str(identifier), "clicks": 0, "impressions": 0})
                    item[metric] += int(value or 0)
        daily_click_cap = int(row.get("daily_click_cap", 0) or 0)
        daily_impression_cap = int(row.get("daily_impression_cap", 0) or 0)
        max_clicks = int(row.get("max_clicks", 0) or 0)
        max_impressions = int(row.get("max_impressions", 0) or 0)
        diagnostics = []
        if not enabled: diagnostics.append("paused_or_unapproved")
        if max_clicks and clicks >= max_clicks: diagnostics.append("click_goal_reached")
        if max_impressions and impressions >= max_impressions: diagnostics.append("impression_goal_reached")
        if daily_click_cap and clicks_today >= daily_click_cap: diagnostics.append("daily_click_cap_reached")
        if daily_impression_cap and impressions_today >= daily_impression_cap: diagnostics.append("daily_impression_cap_reached")
        if not row.get("url"): diagnostics.append("missing_destination")
        campaigns.append({
            "id": str(row.get("id") or "")[:80], "title": str(row.get("title") or "CampaÃƒÂ±a")[:80],
            "enabled": enabled, "clicks": clicks, "impressions": impressions,
            "ctr": round(clicks * 100 / impressions, 2) if impressions else 0,
            "clicks_today": clicks_today, "impressions_today": impressions_today,
            "daily_click_cap": daily_click_cap, "daily_impression_cap": daily_impression_cap,
            "max_clicks": max_clicks, "max_impressions": max_impressions,
            "diagnostics": diagnostics,
        })
    rank = lambda values: sorted(values.values(), key=lambda item: (-item["clicks"], -item["impressions"], item["id"]))[:20]
    totals["ctr"] = round(totals["clicks"] * 100 / totals["impressions"], 2) if totals["impressions"] else 0
    return {"totals": totals, "campaigns": campaigns, "top_chats": rank(chats), "top_bots": rank(bots)}


def _house_ads_insights_csv(insights):
    def csv_cell(value):
        text = str(value or "").replace("\r", " ").replace("\n", " ")
        if text.lstrip().startswith(("=", "+", "-", "@")):
            text = "'" + text
        return '"' + text.replace('"', '""') + '"'
    lines = ["campaign_id,title,enabled,clicks,impressions,ctr,clicks_today,impressions_today,diagnostics"]
    for row in insights.get("campaigns", []):
        values = [row.get("id"), row.get("title"), str(bool(row.get("enabled"))).lower(), row.get("clicks"),
                  row.get("impressions"), row.get("ctr"), row.get("clicks_today"), row.get("impressions_today"),
                  "|".join(row.get("diagnostics") or [])]
        lines.append(",".join(csv_cell(value) for value in values))
    return "\n".join(lines)


def _official_house_ads():
    """CatÃ¡logo versionado que se instala automÃ¡ticamente con Moonbot."""
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "official_house_ads.json")
    try:
        with open(path, "r", encoding="utf-8") as source:
            rows = json.load(source)
        return [row for row in rows if isinstance(row, dict) and row.get("id") and row.get("url")]
    except (OSError, TypeError, ValueError):
        return []


def _sync_master_channel_ads():
    """Mantiene campaÃ±as automÃ¡ticas para los canales de Telegram del master."""
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
                "clicks_by_country": dict(previous.get("clicks_by_country") or {}),
                "impressions_by_country": dict(previous.get("impressions_by_country") or {}),
                "relationship_type": "official", "community_verified": True,
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
                "starts_at": "", "ends_at": "", "approval_status": previous.get("approval_status", "pending"), "submitted_by": str(_master_id),
                "max_clicks": 0, "goal_reached": False, "enabled": previous.get("enabled", True), "priority": 45,
                "clicks": int(previous.get("clicks", 0) or 0), "impressions": int(previous.get("impressions", 0) or 0),
                "clicks_by_placement": dict(previous.get("clicks_by_placement") or {}),
                "impressions_by_placement": dict(previous.get("impressions_by_placement") or {}),
                "clicks_by_country": dict(previous.get("clicks_by_country") or {}),
                "impressions_by_country": dict(previous.get("impressions_by_country") or {}),
                "source": "master_channel", "source_chat_id": chat_id, "automatic": True,
                "relationship_type": "official", "community_verified": True,
            })
        manual = [row for row in rows if row.get("source") not in ("master_channel", "official_channel")]
        _db.set("HOUSE_ADS", manual + official_generated + generated)
        return {"ok": True, "channels": len(generated) + len(official_generated), "official": len(official_generated)}
    except Exception as error:
        return {"ok": False, "error": str(error)[:200]}


def _telegram_campaign_verification(raw, previous=None):
    """Lee Telegram con TDLib; el navegador no puede autodeclarar este distintivo."""
    previous = previous or {}
    if str(raw.get("relationship_type") or "affiliate") != "verified":
        return {"telegram_verified": False, "telegram_verification_status": "not_requested",
                "telegram_verification_checked_at": ""}
    if not _tdlib_client:
        return {"telegram_verified": bool(previous.get("telegram_verified", False)),
                "telegram_verification_status": "tdlib_unavailable",
                "telegram_verification_checked_at": str(previous.get("telegram_verification_checked_at") or "")}
    result = _tdlib_client.get_chat_verification(raw.get("source_chat_id") or raw.get("url"))
    if not result.get("checked"):
        return {"telegram_verified": bool(previous.get("telegram_verified", False)),
                "telegram_verification_status": str(result.get("status") or "unavailable")[:40],
                "telegram_verification_checked_at": str(result.get("checked_at") or ""),
                "telegram_verification_error": str(result.get("error") or "")[:160]}
    return {"telegram_verified": result.get("verified") is True,
            "telegram_verification_status": str(result.get("status") or "not_verified")[:40],
            "telegram_verification_checked_at": str(result.get("checked_at") or ""),
            "telegram_chat_id": str(result.get("chat_id") or "")[:32]}


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
    elif action == "toggle":
        for row in rows:
            if str(row.get("id")) == ad_id:
                if body.get("enabled") and row.get("approval_status") != "approved":
                    raise ValueError("la campaÃ±a debe aprobarse antes de activarla")
                row["enabled"] = bool(body.get("enabled"))
    elif action == "clone":
        source = next((row for row in rows if str(row.get("id")) == ad_id), None)
        if not source: raise ValueError("campaÃ±a no encontrada")
        item = dict(source)
        item.update({"id": secrets.token_hex(8), "title": f"{source.get('title', 'CampaÃ±a')} (copia)"[:80],
                     "enabled": False, "approval_status": "pending", "clicks": 0, "impressions": 0,
                     "clicks_by_placement": {}, "impressions_by_placement": {},
                     "clicks_by_country": {}, "impressions_by_country": {}, "clicks_by_item": {},
                     "clicks_by_chat": {}, "impressions_by_chat": {}, "clicks_by_bot": {}, "impressions_by_bot": {},
                     "clicks_today": 0, "impressions_today": 0, "metrics_day": ""})
        rows.append(item)
    elif action == "click":
        for row in rows:
            if str(row.get("id")) == ad_id:
                row["clicks"] = int(row.get("clicks", 0) or 0) + 1
                _house_ad_metric_context(row, body, "click")
                place = str(body.get("placement") or "unknown"); by = dict(row.get("clicks_by_placement") or {}); by[place] = int(by.get(place, 0)) + 1; row["clicks_by_placement"] = by
                country = str(body.get("country") or "UNK").upper(); country = country if re.fullmatch(r"[A-Z]{2}", country) else "UNK"; by_country = dict(row.get("clicks_by_country") or {}); by_country[country] = int(by_country.get(country, 0)) + 1; row["clicks_by_country"] = by_country
                item_id = str(body.get("item_id") or "")[:64]
                if item_id:
                    by_item = dict(row.get("clicks_by_item") or {}); by_item[item_id] = int(by_item.get(item_id, 0)) + 1; row["clicks_by_item"] = by_item
                if int(row.get("max_clicks", 0) or 0) and row["clicks"] >= int(row["max_clicks"]):
                    row["enabled"] = False
                    row["goal_reached"] = True
    elif action == "impression":
        for row in rows:
            if str(row.get("id")) == ad_id:
                row["impressions"] = int(row.get("impressions", 0) or 0) + 1
                _house_ad_metric_context(row, body, "impression")
                place = str(body.get("placement") or "unknown"); by = dict(row.get("impressions_by_placement") or {}); by[place] = int(by.get(place, 0)) + 1; row["impressions_by_placement"] = by
                country = str(body.get("country") or "UNK").upper(); country = country if re.fullmatch(r"[A-Z]{2}", country) else "UNK"; by_country = dict(row.get("impressions_by_country") or {}); by_country[country] = int(by_country.get(country, 0)) + 1; row["impressions_by_country"] = by_country
    elif action == "reset_metrics":
        for row in rows:
            if str(row.get("id")) == ad_id:
                row.update({"clicks": 0, "impressions": 0, "clicks_by_placement": {}, "impressions_by_placement": {}, "clicks_by_country": {}, "impressions_by_country": {}, "clicks_by_item": {}, "clicks_by_chat": {}, "impressions_by_chat": {}, "clicks_by_bot": {}, "impressions_by_bot": {}, "clicks_today": 0, "impressions_today": 0, "metrics_day": ""})
    elif action == "verify_telegram":
        target = next((row for row in rows if str(row.get("id")) == ad_id), None)
        if not target:
            raise ValueError("campaÃ±a no encontrada")
        if target.get("relationship_type") != "verified":
            raise ValueError("la campaÃ±a no estÃ¡ marcada para verificaciÃ³n")
        target.update(_telegram_campaign_verification(target, target))
    else:
        raw = body.get("ad") or body
        previous = next((row for row in rows if str(row.get("id")) == str(raw.get("id") or "")), None)
        url = str(raw.get("url") or "").strip()
        if not url.startswith(("https://", "tg://")): raise ValueError("enlace no vÃ¡lido")
        community_items = []
        for entry in _safe_list(raw.get("community_items"))[:16]:
            if not isinstance(entry, dict): continue
            entry_url = str(entry.get("url") or "").strip()
            if not entry_url.startswith(("https://", "tg://")): continue
            community_items.append({"id": str(entry.get("id") or secrets.token_hex(4))[:64],
                                    "title": str(entry.get("title") or "Chat Telegram")[:80],
                                    "url": entry_url[:500], "image": str(entry.get("image") or "")[:500],
                                    "type": "channel" if entry.get("type") == "channel" else "group"})
        item = {"id": str(raw.get("id") or secrets.token_hex(8)), "title": str(raw.get("title") or "")[:80],
                "description": str(raw.get("description") or "")[:800], "url": url[:500],
                "image": str(raw.get("image") or "")[:500], "placement": str(raw.get("placement") or "all"),
                "cta": str(raw.get("cta") or "Abrir")[:24],
                "background": str(raw.get("background") or "#eef7ff")[:32],
                "foreground": str(raw.get("foreground") or "#155f9b")[:32],
                "accent": str(raw.get("accent") or "#1982d1")[:32],
                "starts_at": str(raw.get("starts_at") or "")[:40],
                "ends_at": str(raw.get("ends_at") or "")[:40],
                "approval_status": "pending",
                "submitted_by": str(raw.get("submitted_by") or "")[:64],
                "max_clicks": max(0, int(raw.get("max_clicks", 0) or 0)),
                "max_impressions": max(0, int(raw.get("max_impressions", 0) or 0)),
                "daily_click_cap": max(0, min(1000000, int(raw.get("daily_click_cap", 0) or 0))),
                "daily_impression_cap": max(0, min(10000000, int(raw.get("daily_impression_cap", 0) or 0))),
                "goal_reached": bool(raw.get("goal_reached", False)),
                "enabled": bool(raw.get("enabled", True)), "priority": max(0, min(100, int(raw.get("priority", 50) or 0))),
                "clicks": int(raw.get("clicks", 0) or 0), "impressions": int(raw.get("impressions", 0) or 0),
                "clicks_by_placement": dict(raw.get("clicks_by_placement") or {}), "impressions_by_placement": dict(raw.get("impressions_by_placement") or {}),
                "clicks_by_country": dict(raw.get("clicks_by_country") or {}), "impressions_by_country": dict(raw.get("impressions_by_country") or {}),
                "clicks_by_chat": dict(raw.get("clicks_by_chat") or {}), "impressions_by_chat": dict(raw.get("impressions_by_chat") or {}),
                "clicks_by_bot": dict(raw.get("clicks_by_bot") or {}), "impressions_by_bot": dict(raw.get("impressions_by_bot") or {}),
                "clicks_today": max(0, int(raw.get("clicks_today", 0) or 0)), "impressions_today": max(0, int(raw.get("impressions_today", 0) or 0)),
                "metrics_day": str(raw.get("metrics_day") or "")[:10],
                "content_categories": [str(value).strip().lower()[:48] for value in _safe_list(raw.get("content_categories")) if str(value).strip()][:30],
                "include_keywords": [str(value).strip().lower()[:64] for value in _safe_list(raw.get("include_keywords")) if str(value).strip()][:40],
                "exclude_keywords": [str(value).strip().lower()[:64] for value in _safe_list(raw.get("exclude_keywords")) if str(value).strip()][:40],
                "target_channel_ids": [str(value) for value in _safe_list(raw.get("target_channel_ids")) if re.fullmatch(r"-?\d{5,24}", str(value))][:500],
                "target_group_ids": [str(value) for value in _safe_list(raw.get("target_group_ids")) if re.fullmatch(r"-?\d{5,24}", str(value))][:500],
                "source": str(raw.get("source") or "manual")[:32], "source_chat_id": str(raw.get("source_chat_id") or "")[:32],
                "automatic": bool(raw.get("automatic", False)),
                "display_format": str(raw.get("display_format") or "auto") if str(raw.get("display_format") or "auto") in ("auto", "mosaic", "compact", "cards", "spotlight", "ticker") else "auto",
                "community_id": str(raw.get("community_id") or "")[:64],
                "community_items": community_items,
                "clicks_by_item": dict(raw.get("clicks_by_item") or {}),
                "relationship_type": str(raw.get("relationship_type") or "affiliate") if str(raw.get("relationship_type") or "affiliate") in ("official", "verified", "affiliate") else "affiliate",
                "community_verified": bool(raw.get("community_verified", False)),
                **_telegram_campaign_verification(raw, previous)}
        if item["placement"] not in ("all", "top", "right", "left", "inline", "telegram_channel", "telegram_react_channel", "hub"): raise ValueError("ubicaciÃ³n no vÃ¡lida")
        if not item["title"]: raise ValueError("tÃ­tulo obligatorio")
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
        return jsonify({"ok": False, "error": "modo invÃ¡lido"}), 400
    try:
        watch_score = max(20, min(int(body.get("watch_score", 40)), 80))
        delete_score = max(50, min(int(body.get("delete_score", 75)), 100))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "umbrales invÃ¡lidos"}), 400
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
        return jsonify({"ok": False, "error": "veredicto invÃ¡lido"}), 400
    events = _db.get(f"SPAMEVENTS_{chat_id}", [])
    event = next((
        item for item in reversed(events) if isinstance(item, dict)
        and str(item.get("created_at")) == event_id
    ), None)
    if not event or not event.get("text"):
        return jsonify({"ok": False, "error": "detecciÃ³n no encontrada"}), 404
    if event.get("feedback"):
        return jsonify({"ok": False, "error": "esta detecciÃ³n ya fue revisada"}), 409
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


def _record_permission_snapshot(chat_id, bot, status, chat_type, missing, actor):
    return record_permission_snapshot(_db, chat_id, bot, status, chat_type, missing, actor)


@bp.route("/api/public/group/bot-permissions", methods=["POST", "OPTIONS"])
def group_bot_permissions():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    user, chat_id = res
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
        missing.insert(0, {"permission": "administrator", "label": "AÃ±adir el bot como administrador"})
    permission_history, changed = _record_permission_snapshot(
        chat_id, bot, status, chat_type, missing,
        user.get("id") if isinstance(user, dict) else "group-admin",
    )
    return jsonify({
        "ok": True,
        "healthy": not missing,
        "status": status,
        "chat_type": chat_type,
        "missing": missing,
        "changed": changed,
        "permission_history": permission_history,
        "bot_username": getattr(bot, "bot_username", "MoonBot"),
        "instructions": [
            "Abre el grupo en Telegram.",
            "Toca el nombre del grupo y entra en Administradores.",
            f"Selecciona @{getattr(bot, 'bot_username', 'MoonBot')} o aÃ±Ã¡delo como administrador.",
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
    suite = _group_suite()
    return jsonify({"ok": True, **suite.snapshot(chat_id),
                    "sensitive_changes": suite.sensitive_changes(chat_id),
                    "command_menu": command_menu})


@bp.route("/api/public/group/moderation/insights", methods=["POST", "OPTIONS"])
def group_moderation_insights():
    """Versioned, explainable moderation health for an authorized group admin."""
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    cid = str(chat_id)
    suite_state = _group_suite().snapshot(cid)
    current = build_snapshot(
        suite_state,
        _db.get(f"WARNS_{cid}", {}),
        _db.get(f"BANS_{cid}", {}),
        _db.get(f"SPAMEVENTS_{cid}", []),
    )
    key = f"MODERATION_INSIGHTS_{cid}"
    history = _safe_list(_db.get(key, []))
    comparable = lambda row: {k: v for k, v in row.items() if k != "captured_at"}
    if not history or comparable(history[-1]) != comparable(current):
        history.append(current)
        history = history[-30:]
        _db.set(key, history)
    else:
        current = history[-1]
    previous = history[-2] if len(history) > 1 else {}
    comparison = compare_snapshots(previous, current)
    diagnostics = diagnose(current, comparison)
    if body.get("action") == "export":
        if not _jwt_secret:
            return jsonify({"ok": False, "error": "firma no configurada"}), 503
        return jsonify({"ok": True, "export": signed_export(cid, history, _jwt_secret)})
    return jsonify({"ok": True, "current": current, "previous": previous or None,
                    "comparison": comparison, "diagnostics": diagnostics,
                    "history": list(reversed(history))})


@bp.route("/api/public/group/suite/settings", methods=["POST", "OPTIONS"])
def group_suite_settings():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    user, chat_id = res
    try:
        config = _group_suite().save_config(
            chat_id, body.get("config") or {}, actor=str((user or {}).get("id") or "group-admin"),
            source="telegram-webapp"
        )
    except (TypeError, ValueError) as error:
        return jsonify({"ok": False, "error": str(error)}), 400
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
        return jsonify({"ok": False, "error": "usuario invÃ¡lido"}), 400
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
        return jsonify({"ok": False, "error": "decisiÃ³n invÃ¡lida"}), 400
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
        return jsonify({"ok": False, "error": "propuesta invÃ¡lida"}), 400
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
        return jsonify({"ok": False, "error": "rol invÃ¡lido"}), 400
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
        return jsonify({"ok": False, "error": "ID de usuario invÃ¡lido"}), 400
    expires = datetime.datetime.now() + datetime.timedelta(hours=hours)
    _ban_manager.ban_local_user(chat_id, uid, body.get("reason") or "SanciÃ³n temporal",
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
        return jsonify({"ok": False, "error": "acciÃ³n invÃ¡lida"}), 400
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
    config[key] = body.get("value")
    _db.set(f"CONFIG_{chat_id}", config)
    return jsonify({"ok": True, "config": config})


@bp.route("/api/public/group/welcome", methods=["POST", "OPTIONS"])
def group_welcome_set():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    msg = str(body.get("message", "")).strip()[:1000]
    _db.set(f"PLUGIN_WELCOME_{chat_id}", msg)
    return jsonify({"ok": True, "welcome_msg": msg})


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
        return jsonify({"ok": False, "error": "mensaje vacÃ­o"}), 400
    bot = _get_bot_for_chat(chat_id) if _get_bot_for_chat else None
    if not bot:
        return jsonify({"ok": False, "error": "sin bot para este chat"}), 503
    r = bot.send_msg(chat_id, text)
    if body.get("pin") and isinstance(r, dict) and r.get("result", {}).get("message_id"):
        mid = r["result"]["message_id"]
        bot.api_call("pinChatMessage", {"chat_id": chat_id, "message_id": mid, "disable_notification": bool(body.get("silent", False))})
    return jsonify({"ok": bool(r.get("ok")) if isinstance(r, dict) else True})


@bp.route("/api/public/group/send_poll", methods=["POST", "OPTIONS"])
def group_send_poll():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    question = (body.get("question") or "").strip()
    options = [str(o).strip() for o in (body.get("options") or []) if str(o).strip()]
    if not question or len(options) < 2:
        return jsonify({"ok": False, "error": "Pregunta y al menos 2 opciones requeridas"}), 400
    is_anonymous = bool(body.get("is_anonymous", True))
    allows_multiple = bool(body.get("allows_multiple", False))
    bot = _get_bot_for_chat(chat_id) if _get_bot_for_chat else None
    if not bot:
        return jsonify({"ok": False, "error": "sin bot para este chat"}), 503
    r = bot.api_call("sendPoll", {
        "chat_id": chat_id,
        "question": question,
        "options": json.dumps(options),
        "is_anonymous": is_anonymous,
        "allows_multiple_answers": allows_multiple
    })
    return jsonify({"ok": bool(r.get("ok")), "error": r.get("description") if not r.get("ok") else None})


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
    """Guarda la lista de palabras prohibidas y la acciÃ³n (delete|warn|ban)."""
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
    """EnvÃ­a una imagen (por URL) al grupo. Usado por el generador de imÃ¡genes."""
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
    # Descarga la imagen (con UA vÃ¡lido) y la sube a Telegram como archivo,
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
    """Genera imÃ¡genes a partir de una descripciÃ³n (varias variantes para elegir)."""
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
    """EstadÃ­sticas tipo TGStat del grupo/canal (admin/creador del chat)."""
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    res, err = _group_auth(body)
    if err:
        return err
    _, chat_id = res
    return jsonify({"ok": True, "stats": _channel_stats.get_stats_by_chat(chat_id)})


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Anuncios mutuos (InsideAds) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _auth_user(body):
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return None, (jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401)
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
        return jsonify({"ok": False, "error": "ya tienes una apelaciÃ³n pendiente"}), 409
    if not appeal:
        return jsonify({"ok": False, "error": "no hay un bloqueo activo o falta el motivo"}), 400
    return jsonify({"ok": True, "appeal": appeal}), 201


def _ad_tracking_text(ad, text, side, target_url):
    rendered = str(text or "").strip()
    if not rendered.startswith("ðŸ¤"):
        rendered = "ðŸ¤ ColaboraciÃ³n entre comunidades\n\n" + rendered
    if target_url:
        base = os.getenv("MOON_PUBLIC_URL", "https://cintiabot.todosobreall.tech").rstrip("/")
        rendered += f"\n\n[MÃ¡s informaciÃ³n]({base}/api/public/ads/click/{ad['id']}/{side})"
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
    """Canales disponibles como socios (donde el bot estÃ¡), excepto el propio."""
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
                    "match_reason": "socio favorito" if preference == "favorite" else ("misma categorÃ­a y audiencia similar" if same_category else "audiencia compatible"),
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
        return jsonify({"ok": False, "error": "enlace de campaÃ±a no vÃ¡lido"}), 400
    if not isinstance(variants, list) or len(variants) > 5 or any(not isinstance(item, str) or len(item) > 3500 for item in variants):
        return jsonify({"ok": False, "error": "las variantes no son vÃ¡lidas"}), 400
    if not (_is_master(user) or _channel_stats.is_user_admin_of(user.get("id"), from_chat)):
        return jsonify({"ok": False, "error": "no gestionas el canal de origen"}), 403
    source_policy = _group_suite().config(from_chat)["ad_exchange"]
    destination_policy = _group_suite().config(to_chat)["ad_exchange"]
    if not source_policy["enabled"] or not destination_policy["enabled"]:
        return jsonify({"ok": False, "error": "el intercambio de anuncios estÃ¡ desactivado en uno de los destinos"}), 409
    try:
        scheduled_at = datetime.datetime.fromisoformat(when.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return jsonify({"ok": False, "error": "fecha no vÃ¡lida"}), 400
    now = datetime.datetime.utcnow()
    if scheduled_at < now + datetime.timedelta(minutes=10) or scheduled_at > now + datetime.timedelta(days=30):
        return jsonify({"ok": False, "error": "programa el intercambio entre 10 minutos y 30 dÃ­as"}), 400
    history = _channel_stats.ads_history(from_chat)
    pair = [row for row in history if {str(row.get("from_chat")), str(row.get("to_chat"))} == {str(from_chat), str(to_chat)}]
    if any(row.get("status") == "pending" for row in pair):
        return jsonify({"ok": False, "error": "ya existe una solicitud pendiente entre estos grupos"}), 409
    today = now.strftime("%Y-%m-%d")
    daily = sum(1 for row in history if str(row.get("created", "")).startswith(today) and row.get("status") in ("accepted", "completed"))
    if daily >= source_policy["max_daily"]:
        return jsonify({"ok": False, "error": "se alcanzÃ³ el lÃ­mite diario de intercambios"}), 429
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
        return jsonify({"ok": False, "error": "se alcanzÃ³ el lÃ­mite semanal de intercambios"}), 429
    if recent_failures >= source_policy["pause_after_failures"]:
        return jsonify({"ok": False, "error": "las campaÃ±as estÃ¡n pausadas por fallos recientes de entrega"}), 503
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
        return jsonify({"ok": False, "error": f"El anuncio contiene una palabra no permitida en el canal destino: Â«{hit}Â»"}), 400
    fm = _channel_stats.get_channel_meta(from_chat) or {}
    tm = _channel_stats.get_channel_meta(to_chat) or {}
    sensitive_terms = ("casino", "apuestas", "inversiÃ³n", "criptomoneda", "prÃ©stamo", "contenido adulto")
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
        return jsonify({"ok": False, "error": "enlace recÃ­proco no vÃ¡lido"}), 400
    hit = _banned_hit(ad.get("from_chat"), to_ad)
    if hit:
        return jsonify({"ok": False, "error": f"Tu anuncio contiene una palabra no permitida en el canal destino: Â«{hit}Â»"}), 400
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
        return jsonify({"ok": False, "error": "texto no vÃ¡lido"}), 400
    fake = {"id": "preview"}
    return jsonify({"ok": True, "rendered": _ad_tracking_text(fake, text, "preview", body.get("target_url")),
                    "characters": len(text), "has_image": bool(body.get("image")),
                    "label_added": not text.startswith("ðŸ¤")})


@bp.route("/api/public/ads/cancel", methods=["POST", "OPTIONS"])
def ads_cancel():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}; user, err = _auth_user(body)
    if err: return err
    ad = _channel_stats.get_ad(body.get("id"))
    if not ad: return jsonify({"ok": False, "error": "campaÃ±a no encontrada"}), 404
    if not (_is_master(user) or _channel_stats.is_user_admin_of(user.get("id"), ad.get("from_chat"))):
        return jsonify({"ok": False, "error": "sin permiso"}), 403
    if ad.get("status") not in ("pending", "countered", "master_review"):
        return jsonify({"ok": False, "error": "la campaÃ±a ya no se puede cancelar"}), 409
    _channel_stats.update_ad(ad["id"], {"status": "cancelled"})
    return jsonify({"ok": True})


@bp.route("/api/public/ads/counter", methods=["POST", "OPTIONS"])
def ads_counter():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}; user, err = _auth_user(body)
    if err: return err
    ad = _channel_stats.get_ad(body.get("id"))
    if not ad: return jsonify({"ok": False, "error": "campaÃ±a no encontrada"}), 404
    if not (_is_master(user) or _channel_stats.is_user_admin_of(user.get("id"), ad.get("to_chat"))):
        return jsonify({"ok": False, "error": "sin permiso"}), 403
    counter_ad = str(body.get("to_ad") or "").strip()
    counter_when = str(body.get("when") or "").strip()
    counter_url = str(body.get("to_url") or "").strip()
    if not counter_ad or not counter_when:
        return jsonify({"ok": False, "error": "faltan contrapropuesta y fecha"}), 400
    if len(counter_ad) > 3500 or _banned_hit(ad.get("from_chat"), counter_ad):
        return jsonify({"ok": False, "error": "el texto de la contrapropuesta no estÃ¡ permitido"}), 400
    if counter_url and (urlparse(counter_url).scheme not in ("http", "https") or not urlparse(counter_url).netloc):
        return jsonify({"ok": False, "error": "enlace no vÃ¡lido"}), 400
    try:
        proposed_at = datetime.datetime.fromisoformat(counter_when.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return jsonify({"ok": False, "error": "fecha no vÃ¡lida"}), 400
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
    if not ad or ad.get("status") != "master_review": return jsonify({"ok": False, "error": "revisiÃ³n no disponible"}), 404
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
        return jsonify({"ok": False, "error": "preferencia no vÃ¡lida"}), 400
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
            return jsonify({"ok": False, "error": "enlace no vÃ¡lido"}), 400
        _channel_stats.save_ad_template(chat_id, name[:80], text[:3500], body.get("image"), target_url, user.get("id"))
    try:
        rows = _channel_stats.ad_templates(chat_id)
    except PBError as exc:
        current_app.logger.warning("Plantillas publicitarias no disponibles: %s", exc)
        return jsonify({"ok": False, "error": "plantillas temporalmente no disponibles"}), 503
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
    if not ad: return jsonify({"ok": False, "error": "campaÃ±a no encontrada"}), 404
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
        return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
    try:
        return jsonify({"ok": True, "channels": _channel_stats.get_user_channels(user.get("id"))})
    except Exception as error:
        return jsonify({"ok": False, "error": f"PocketBase no disponible: {error}"}), 503


def _miniapp_feature_groups(user):
    """Return only server-verified groups and the contextual role in each one."""
    user_id = str(user.get("id") or "")
    try:
        channels = (_channel_stats.get_all_channels() if _is_master(user)
                    else _channel_stats.get_user_channels(user_id)) or []
    except Exception:
        channels = []
    result = []
    for row in channels:
        chat_id = str(row.get("chat_id") or "").strip()
        if not chat_id:
            continue
        telegram_role = str(row.get("role") or row.get("admin_status") or "").lower()
        role = "master" if _is_master(user) else "group_creator" if telegram_role == "creator" else "group_admin"
        result.append({"chat_id": chat_id, "name": str(row.get("name") or row.get("title") or chat_id)[:160], "actor_role": role})
    return result


def _miniapp_feature_context(user, requested_group_id=None):
    groups = _miniapp_feature_groups(user)
    requested = str(requested_group_id or "").strip()
    selected = next((row for row in groups if row["chat_id"] == requested), None) if requested else None
    if requested and selected is None:
        raise PermissionError("grupo no autorizado")
    return (selected["actor_role"] if selected else "master" if _is_master(user) else "user"), groups, selected


@bp.route("/api/public/personal/tasks", methods=["POST", "OPTIONS"])
def public_personal_tasks():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}; user = _verify_init_data(body.get("initData", ""))
    if user is None: return jsonify({"ok": False, "error": "initData invÃƒÂ¡lido"}), 401
    try:
        _, groups, selected = _miniapp_feature_context(user, body.get("chat_id"))
    except PermissionError:
        return jsonify({"ok": False, "error": "grupo no autorizado"}), 403
    chat_id = selected and selected["chat_id"]
    action = str(body.get("action") or "list"); user_id = str(user.get("id"))
    try:
        if action == "add": rows = add_task(_db, user_id, chat_id, body.get("title"))
        elif action == "complete": rows = update_task(_db, user_id, chat_id, body.get("id"), done=body.get("done", True))
        elif action == "delete": rows = update_task(_db, user_id, chat_id, body.get("id"), delete=True)
        elif action == "list": rows = list_tasks(_db, user_id, chat_id)
        else: return jsonify({"ok": False, "error": "acciÃƒÂ³n no vÃƒÂ¡lida"}), 400
    except ValueError as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    return jsonify({"ok": True, "tasks": rows, "selected_chat_id": chat_id,
                    "available_groups": groups, "scope": "group" if chat_id else "personal"})


@bp.route("/api/internal/security/url-inspect", methods=["POST"])
def internal_security_url_inspect():
    if not _internal_admin_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    result = inspect_url((request.json or {}).get("url"))
    return jsonify(result), (200 if result.get("ok") else 400)


def _miniapp_release_channel(user):
    """Resolve the release channel from the linked web account; fail closed to stable."""
    if _is_master(user):
        return "alpha"
    user_id = str(user.get("id") or "").strip()
    if not user_id:
        return "stable"
    try:
        pb = getattr(_channel_stats, "_pb", None)
        record = pb.first("feature_release_access", f"telegram_id='{pb.esc(user_id)}' && enabled=true") if pb else None
        return normalize_release_channel((record or {}).get("release_channel"))
    except Exception:
        return "stable"


def _verified_web_admin(user):
    """Resolve a web administrator only from the PB account linked to Telegram."""
    user_id = str(user.get("id") or "").strip()
    if not user_id:
        return False
    try:
        pb = getattr(_channel_stats, "_pb", None)
        record = pb.first("users", f"telegram_id='{pb.esc(user_id)}'") if pb else None
        return bool(record and record.get("role") in {"admin", "creator"} and not record.get("is_frozen"))
    except Exception:
        return False


def _bind_feature_group_payload(item, payload, group_id):
    """Overwrite direct group identifiers so client JSON cannot escape its authorized context."""
    if not isinstance(payload, dict):
        return payload
    args = list(payload.get("args") or [])
    kwargs = dict(payload.get("kwargs") or {})
    for index, parameter in enumerate((item.get("input_schema") or {}).get("parameters") or []):
        if parameter.get("name") not in {"group_id", "chat_id", "channel_id"} or parameter.get("variadic"):
            continue
        if parameter.get("binding") == "args":
            if index < len(args):
                args[index] = group_id
        else:
            kwargs[parameter["name"]] = group_id
    return {"args": args, "kwargs": kwargs}


def _feature_payload_group_id(item, payload):
    """Read the formal group parameter; arbitrary nested IDs never grant access."""
    if not isinstance(payload, dict):
        return ""
    args = list(payload.get("args") or [])
    kwargs = dict(payload.get("kwargs") or {})
    for index, parameter in enumerate((item.get("input_schema") or {}).get("parameters") or []):
        name = parameter.get("name")
        if name not in {"group_id", "chat_id", "channel_id"} or parameter.get("variadic"):
            continue
        value = args[index] if parameter.get("binding") == "args" and index < len(args) else kwargs.get(name)
        return str(value or "").strip()
    return ""


def _payload_uses_only_group(value, group_id):
    singular = {"group_id", "chat_id", "channel_id"}
    plural = {"group_ids", "chat_ids", "channel_ids"}
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in singular and str(nested) != str(group_id):
                return False
            if key in plural and (not isinstance(nested, (list, tuple)) or any(str(item) != str(group_id) for item in nested)):
                return False
            if not _payload_uses_only_group(nested, group_id):
                return False
    elif isinstance(value, (list, tuple)):
        return all(_payload_uses_only_group(item, group_id) for item in value)
    return True


def _bind_feature_actor_payload(item, payload, user, actor_role):
    """Prevent public callers from forging the identity or master role consumed by feature engines."""
    if not isinstance(payload, dict):
        return payload
    args = list(payload.get("args") or [])
    kwargs = dict(payload.get("kwargs") or {})
    for index, parameter in enumerate((item.get("input_schema") or {}).get("parameters") or []):
        name, binding = parameter.get("name"), parameter.get("binding")
        current = args[index] if binding == "args" and index < len(args) else kwargs.get(name)
        if name == "actor":
            requested_scopes = current.get("scopes", []) if isinstance(current, dict) else []
            scopes = [str(scope)[:160] for scope in requested_scopes[:100] if isinstance(scope, str)]
            value = {"id": str(user.get("id") or "miniapp-user"), "roles": [actor_role], "scopes": scopes}
        elif name == "actor_id":
            value = str(user.get("id") or "miniapp-user")
        elif name == "actor_role":
            value = actor_role
        elif name == "is_master":
            value = actor_role == "master"
        elif name == "is_admin":
            value = actor_role in {"group_admin", "group_creator", "master"}
        else:
            continue
        if binding == "args":
            if index < len(args):
                args[index] = value
        else:
            kwargs[name] = value
    return {"args": args, "kwargs": kwargs}


@bp.route("/api/public/features", methods=["POST", "OPTIONS"])
def public_role_features():
    """Interfaz de capacidades limitada al rol real de la Mini App."""
    if request.method == "OPTIONS":
        return ("", 204)
    request.max_content_length = 128 * 1024
    body = request.get_json(silent=True) or {}
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
    try:
        actor_role, available_groups, selected_group = _miniapp_feature_context(user, body.get("group_id"))
    except PermissionError as error:
        return jsonify({"ok": False, "error": str(error)}), 403
    release_channel = _miniapp_release_channel(user)
    if body.get("action", "list") == "list":
        features = list_verified_features(actor_role, release_channel)
        return jsonify({"ok": True, "actor_role": actor_role, "selected_group_id": selected_group and selected_group["chat_id"],
                        "release_channel": release_channel, "available_groups": available_groups,
                        "total": len(features), "features": features})
    if body.get("action") != "execute":
        return jsonify({"ok": False, "error": "acciÃ³n no compatible"}), 400
    try:
        item = verified_feature_registry().get(body.get("feature_id"))
        if item is None:
            raise KeyError(body.get("feature_id"))
        group_scoped = item.get("scope") in {"group_operation", "group_configuration"}
        if group_scoped and selected_group is None:
            return jsonify({"ok": False, "error": "selecciona un grupo autorizado"}), 400
        payload = _bind_feature_group_payload(item, body.get("payload", {}), selected_group["chat_id"]) if group_scoped else body.get("payload", {})
        if group_scoped and not _payload_uses_only_group(payload, selected_group["chat_id"]):
            return jsonify({"ok": False, "error": "el payload referencia otro grupo"}), 403
        payload = _bind_feature_actor_payload(item, payload, user, actor_role)
        result = execute_verified_feature(body.get("feature_id"), payload, actor_role, release_channel)
        return jsonify({"ok": True, "actor_role": actor_role, "group_id": selected_group and selected_group["chat_id"],
                        "feature_id": body.get("feature_id"), "result": result})
    except KeyError as error:
        return jsonify({"ok": False, "error": str(error)}), 404
    except PermissionError as error:
        return jsonify({"ok": False, "error": str(error)}), 403
    except (TypeError, ValueError) as error:
        return jsonify({"ok": False, "error": str(error)}), 400


@bp.route("/api/public/notifications", methods=["POST", "OPTIONS"])
def public_notifications():
    """Alertas relevantes para los grupos que el usuario puede administrar."""
    if request.method == "OPTIONS":
        return ("", 204)
    user = _verify_init_data((request.json or {}).get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
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
                    "type": "report", "title": f"Reporte pendiente Â· {name}",
                    "body": f"Usuario {report.get('target_id')}: {report.get('reason') or 'Sin motivo'}",
                    "created_at": report.get("created_at"), "chat_id": cid,
                })
        events = _db.get(f"MEDIA_SECURITY_EVENTS_{cid}", []) if _db else []
        for event in events[-20:] if isinstance(events, list) else []:
            if event.get("matched"):
                rows.append({
                    "id": f"media:{cid}:{event.get('message_id')}:{event.get('created_at')}",
                    "type": "security", "title": f"Alerta multimedia Â· {name}",
                    "body": f"{event.get('user') or event.get('user_id')}: {event.get('reason')}",
                    "created_at": event.get("created_at"), "chat_id": cid,
                })
    if _is_master(user):
        global_reports = _ban_manager.list_ban_reports(status="pending", limit=100) if _ban_manager else []
        for report in global_reports:
            analysis = report.get("analysis") or {}
            automatic = bool(report.get("auto_ban_applied"))
            rows.append({
                "id": f"gban-report:{report.get('id')}", "type": "gban_report",
                "title": "GBAN automÃ¡tico pendiente" if automatic else "Propuesta de GBAN pendiente",
                "body": (
                    f"Usuario {report.get('user_id')} Â· riesgo {analysis.get('score', 0)}/100 Â· "
                    f"{report.get('reason') or 'Sin motivo'}"
                ),
                "created_at": report.get("created_at"),
                "chat_id": str(report.get("chat_id") or ""),
                "report_id": report.get("id"),
                "priority": "critical" if automatic else analysis.get("level", "medium"),
            })
        appeals = _db.get("BAN_APPEALS", []) if _db else []
        for appeal in appeals[-30:] if isinstance(appeals, list) else []:
            if appeal.get("status") == "pending":
                rows.append({
                    "id": f"appeal:{appeal.get('id')}", "type": "appeal",
                    "title": "ApelaciÃ³n pendiente",
                    "body": f"Usuario {appeal.get('user_id')}: {appeal.get('message') or 'RevisiÃ³n solicitada'}",
                    "created_at": appeal.get("created_at"),
                })
    rows = [row for row in rows if (
        (row.get("type") == "security" and preferences["security"]) or
        (row.get("type") in ("report", "gban_report", "appeal") and preferences["reports"]) or
        row.get("type") not in ("security", "report", "gban_report", "appeal")
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
        return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
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
        return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
    item = _community_members().request_role(user.get("id"), body.get("role"), body.get("reason"))
    return jsonify({"ok": bool(item), "request": item}), 200 if item else 400


@bp.route("/api/public/community/reminder", methods=["POST", "OPTIONS"])
def community_reminder():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
    try:
        if body.get("local_time"):
            item = _community_members().persistent_reminder(
                user.get("id"), body.get("text", ""), body.get("local_time"),
                body.get("timezone") or "Europe/Madrid", body.get("recurrence") or "once",
                body.get("fold"),
            )
        else:
            item = _community_members().reminder(user.get("id"), body.get("text", ""), body.get("remind_at"))
        return jsonify({"ok": True, "reminder": item})
    except (TypeError, ValueError) as error:
        return jsonify({"ok": False, "error": str(error)}), 400


@bp.route("/api/public/community/reminder/action", methods=["POST", "OPTIONS"])
def community_reminder_action():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
    action = str(body.get("action") or "")
    manager = _community_members()
    try:
        if action == "snooze":
            item = manager.snooze_persistent_reminder(user.get("id"), body.get("reminder_id"), body.get("minutes", 10))
        elif action == "cancel":
            item = manager.cancel_persistent_reminder(user.get("id"), body.get("reminder_id"))
        else:
            return jsonify({"ok": False, "error": "acciÃ³n no compatible"}), 400
        return jsonify({"ok": bool(item), "reminder": item}), 200 if item else 404
    except (TypeError, ValueError) as error:
        return jsonify({"ok": False, "error": str(error)}), 400


@bp.route("/api/public/community/preferences", methods=["POST", "OPTIONS"])
def community_preferences():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
    return jsonify({"ok": True, "preferences": _community_members().preferences(user.get("id"), body.get("preferences") or {})})


@bp.route("/api/public/community/directory", methods=["POST", "OPTIONS"])
def community_directory():
    if request.method == "OPTIONS":
        return ("", 204)
    user = _verify_init_data((request.json or {}).get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
    return jsonify({"ok": True, "members": _community_members().directory()})


@bp.route("/api/public/community/engagement", methods=["POST", "OPTIONS"])
def community_engagement_snapshot():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}; user = _verify_init_data(body.get("initData", ""))
    if user is None: return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
    service = CommunityEngagement(_db)
    return jsonify({"ok": True, "surveys": service.surveys(), "events": service.events(),
                    "challenges": list(reversed(service._rows(_db, "COMMUNITY_CHALLENGES")))})


@bp.route("/api/public/community/engagement/action", methods=["POST", "OPTIONS"])
def community_engagement_action():
    if request.method == "OPTIONS": return ("", 204)
    body = request.json or {}; user = _verify_init_data(body.get("initData", ""))
    if user is None: return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
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
        else: return jsonify({"ok": False, "error": "acciÃ³n invÃ¡lida"}), 400
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
        return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
    result = RoadmapEngine(_db).form_submit(body.get("form_id"), user.get("id"), body.get("answers") or {})
    return jsonify({"ok": bool(result), "result": result}), 200 if result else 404


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Captcha de entrada (Join Request Queries) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Pool de iconos del captcha (los mismos nombres que join.html mapea a SVG).
_JOIN_ICONS = ["star", "heart", "bolt", "moon", "cloud", "leaf"]
_JOIN_SHAPES = ["circle", "square", "triangle", "diamond", "hexagon", "ring"]
_JOIN_COLORS = ["teal", "cyan", "amber", "violet"]
_JOIN_CHALLENGE_TYPES = ("icons", "sequence", "shapes", "math")


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
        "challenge_types": [
            value for value in (raw.get("challenge_types") or _JOIN_CHALLENGE_TYPES)
            if value in _JOIN_CHALLENGE_TYPES
        ] or list(_JOIN_CHALLENGE_TYPES),
        "request_ttl": _bounded_int(raw.get("request_ttl"), 86400, 300, 604800),
        "reverify_interval_days": _bounded_int(raw.get("reverify_interval_days"), 0, 0, 90),
        "exempt_user_ids": [str(value).strip() for value in exempt if str(value).strip().isdigit()][:100],
        "required_channels": _normalize_required_channels(required),
    }


def _normalize_required_channels(values, limit=10):
    if not isinstance(values, list):
        values = [values]
    result = []
    seen = set()
    for value in values:
        channel = str(value or "").strip().lstrip("@")[:100]
        key = channel.casefold()
        if not channel or key in seen:
            continue
        seen.add(key)
        result.append(channel)
        if len(result) >= limit:
            break
    return result


def _bot_identity_keys(bot):
    """Devuelve todas las identidades comparables de un bot, no solo la primera disponible."""
    if isinstance(bot, dict):
        values = (bot.get("id"), bot.get("bot_id"), bot.get("user_id"),
                  bot.get("username"), bot.get("bot_username"))
    else:
        values = (getattr(bot, "id", None), getattr(bot, "bot_id", None),
                  getattr(bot, "user_id", None), getattr(bot, "username", None),
                  getattr(bot, "bot_username", None))
    return {str(value).strip().casefold().lstrip("@") for value in values
            if str(value or "").strip()}


def _required_channel_suggestions(chat_id=None):
    """Canales donde participa un bot activo; opcionalmente limita al bot del grupo."""
    rows = _admin_group_rows()
    allowed_bots = set()
    if chat_id is not None:
        for row in rows:
            if str(row.get("id")) == str(chat_id):
                allowed_bots = set().union(*(_bot_identity_keys(bot) for bot in row.get("bots", []))) \
                    if row.get("bots") else set()
                break
    active_bots = [{"id": str(getattr(bot, "bot_id", "")),
                    "username": str(getattr(bot, "bot_username", "")).lstrip("@"),
                    "identities": _bot_identity_keys(bot)}
                   for bot in ((_get_active_bots() or []) if _get_active_bots else [])
                   if getattr(bot, "bot_username", None)]
    suggestions = []
    seen = set()
    for row in rows:
        if str(row.get("ctype", "")).lower() != "channel":
            continue
        row_bots = set().union(*(_bot_identity_keys(bot) for bot in row.get("bots", []))) \
            if row.get("bots") else set()
        if allowed_bots and not allowed_bots.intersection(row_bots):
            continue
        username = str(row.get("username") or "").strip().lstrip("@")
        channel = username or str(row.get("id") or "").strip()
        key = channel.casefold()
        if not channel or key in seen:
            continue
        seen.add(key)
        review = _channel_candidate_review(row)
        if not review["eligible"]:
            continue
        missing_bot = next((bot for bot in active_bots
                            if not bot["identities"].intersection(row_bots)), None)
        suggestions.append({
            "channel": channel,
            "chat_id": str(row.get("id") or ""),
            "title": str(row.get("name") or username or channel)[:160],
            "username": username,
            "url": f"https://t.me/{username}" if username else "",
            "photo_url": f"https://t.me/i/userpic/320/{username}.jpg" if username else "",
            "bots": row.get("bots", []),
            "bot_joined": missing_bot is None,
            "join_bot": ({key: missing_bot[key] for key in ("id", "username")} if missing_bot else None),
            "join_bot_url": (f"https://t.me/{missing_bot['username']}?startchannel&admin=post_messages+edit_messages+delete_messages+invite_users+manage_chat"
                             if missing_bot else ""),
            "content_review": review,
        })
    return sorted(suggestions, key=lambda item: item["title"].casefold())[:100]


def _channel_candidate_review(row):
    """RevisiÃ³n explicable del contenido observado; excluye solo seÃ±ales de alto riesgo."""
    cid = str(row.get("id") or row.get("chat_id") or "")
    history = [item for item in _safe_list(_db.get(f"CHAT_HIST_{cid}", []) if _db else [])
               if isinstance(item, dict) and str(item.get("text") or "").strip()][-100:]
    texts = [str(item.get("text") or "")[:2000] for item in history]
    history_fingerprint = hashlib.sha256(json.dumps([
        [item.get("message_id"), item.get("time"), str(item.get("text") or "")[:2000]]
        for item in history
    ], ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    cache_key = f"JOIN_CHANNEL_REVIEW_{cid}"
    cached = _db.get(cache_key, {}) if _db and cid else {}
    if isinstance(cached, dict) and cached.get("history_fingerprint") == history_fingerprint:
        return cached
    corpus = "\n".join(texts).casefold()
    reasons = []
    score = 0
    severe_groups = {
        "phishing o robo de credenciales": (("seed phrase", "frase semilla", "verify wallet", "verifica tu wallet", "robar cuenta"), 25),
        "malware o archivos peligrosos": (("stealer download", "ransomware builder", "cryptominer oculto", "descarga el crack"), 25),
        "explotaciÃ³n sexual infantil": (("child sexual abuse", "csam", "pornografÃ­a infantil"), 70),
        "captaciÃ³n terrorista": (("Ãºnete a la yihad", "join the jihad", "manual de explosivos", "bomb making manual"), 70),
    }
    for label, (terms, weight) in severe_groups.items():
        hits = sum(corpus.count(term) for term in terms)
        if hits:
            points = min(70, weight * hits)
            score += points
            reasons.append({"signal": label, "hits": hits, "points": points})
    url_count = sum(len(re.findall(r"https?://|t\.me/", text.casefold())) for text in texts)
    if len(texts) >= 10 and url_count >= max(12, len(texts) * 2):
        score += 25
        reasons.append({"signal": "densidad anÃ³mala de enlaces", "hits": url_count, "points": 25})
    repeated = len(texts) - len({re.sub(r"\s+", " ", text.casefold()).strip() for text in texts})
    if len(texts) >= 10 and repeated >= max(6, len(texts) // 2):
        score += 25
        reasons.append({"signal": "contenido repetitivo", "hits": repeated, "points": 25})
    score = min(100, score)
    review = {
        "eligible": score < 70,
        "status": "pending" if not texts else ("rejected" if score >= 70 else "approved"),
        "score": score,
        "messages_analyzed": len(texts),
        "reasons": reasons,
        "history_fingerprint": history_fingerprint,
        "reviewed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    if _db and cid:
        _db.set(cache_key, review)
    return review


def _global_join_channels():
    _ensure_global_join_defaults()
    values = _db.get("JOIN_GLOBAL_REQUIRED_CHANNELS", []) if _db else []
    channels = _normalize_required_channels(values)
    enabled = bool(_db.get("JOIN_GLOBAL_REQUIRED_ENABLED", bool(channels))) if _db else False
    return channels if enabled else []


def _global_join_channel():
    """Compatibilidad con clientes antiguos que esperan un Ãºnico canal."""
    channels = _global_join_channels()
    return channels[0] if channels else ""


def _global_join_settings():
    _ensure_global_join_defaults()
    channels = _normalize_required_channels(_db.get("JOIN_GLOBAL_REQUIRED_CHANNELS", []) if _db else [])
    channel = channels[0] if channels else ""
    enabled = bool(_db.get("JOIN_GLOBAL_REQUIRED_ENABLED", bool(channels))) if _db else False
    strict_enforcement = bool(_db.get("JOIN_GLOBAL_STRICT_ENFORCEMENT", False)) if _db else False
    reverify_interval_hours = _bounded_int(
        _db.get("JOIN_GLOBAL_REVERIFY_INTERVAL_HOURS", 12) if _db else 12, 12, 0, 2160
    )
    return {"enabled": enabled, "channel": channel, "channels": channels,
            "suggested_channels": _required_channel_suggestions(),
            "strict_enforcement": strict_enforcement,
            "reverify_interval_hours": reverify_interval_hours,
            "reverify_interval_days": round(reverify_interval_hours / 24, 2) if reverify_interval_hours else 0}


def _global_join_update_candidate(body):
    """Valida canales y activaciÃ³n juntos para evitar escrituras parciales."""
    current_channels = _normalize_required_channels(
        _db.get("JOIN_GLOBAL_REQUIRED_CHANNELS", []) if _db else []
    )
    channels = current_channels
    if "channels" in body or "channel" in body:
        channels = _normalize_required_channels(
            body.get("channels") if "channels" in body else [body.get("channel")]
        )
    current_enabled = bool(_db.get("JOIN_GLOBAL_REQUIRED_ENABLED", bool(current_channels))) if _db else False
    enabled = bool(body.get("enabled")) if "enabled" in body else current_enabled
    if enabled and not channels:
        return None, None, "configura al menos un canal"
    return channels, enabled, None


def _ensure_global_join_defaults():
    """Aplica una sola vez los valores globales seguros solicitados por el master."""
    if not _db:
        return
    if not _db.get("JOIN_GLOBAL_DEFAULTS_V3", False):
        _db.set("JOIN_GLOBAL_REQUIRED_CHANNEL", "TodoSobreAllTech")
        _db.set("JOIN_GLOBAL_REQUIRED_ENABLED", True)
        _db.set("JOIN_GLOBAL_REVERIFY_INTERVAL_HOURS", 12)
        _db.set("JOIN_GLOBAL_DEFAULTS_V3", True)
    if not _db.get("JOIN_GLOBAL_DEFAULTS_V4", False):
        previous = _db.get("JOIN_GLOBAL_REQUIRED_CHANNEL", "TodoSobreAllTech")
        existing = _normalize_required_channels(_db.get("JOIN_GLOBAL_REQUIRED_CHANNELS", []))
        _db.set("JOIN_GLOBAL_REQUIRED_CHANNELS", existing or _normalize_required_channels([previous]))
        _db.set("JOIN_GLOBAL_DEFAULTS_V4", True)


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
        return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
    if not _is_master(user):
        return jsonify({"ok": False, "error": "solo el master puede cambiar el acceso global"}), 403
    channels, enabled, validation_error = _global_join_update_candidate(body)
    if validation_error:
        return jsonify({"ok": False, "error": validation_error}), 400
    if "channels" in body or "channel" in body:
        _db.set("JOIN_GLOBAL_REQUIRED_CHANNELS", channels)
        _db.set("JOIN_GLOBAL_REQUIRED_CHANNEL", channels[0] if channels else "")
    if "enabled" in body:
        _db.set("JOIN_GLOBAL_REQUIRED_ENABLED", enabled)
    if "strict_enforcement" in body:
        _db.set("JOIN_GLOBAL_STRICT_ENFORCEMENT", bool(body.get("strict_enforcement")))
    if "reverify_interval_days" in body:
        _db.set("JOIN_GLOBAL_REVERIFY_INTERVAL_DAYS",
                _bounded_int(body.get("reverify_interval_days"), 0, 0, 90))
    if "reverify_interval_hours" in body:
        _db.set("JOIN_GLOBAL_REVERIFY_INTERVAL_HOURS",
                _bounded_int(body.get("reverify_interval_hours"), 12, 0, 2160))
    return jsonify({"ok": True, **_global_join_settings(), "captcha": _global_captcha_status()})


def _missing_required_channels(bot, chat_id, user_id):
    missing = []
    group_channels = _join_config(chat_id)["required_channels"]
    global_channels = _global_join_channels()
    channels = [(channel, "group") for channel in group_channels]
    group_keys = {channel.casefold() for channel in group_channels}
    channels.extend((channel, "global") for channel in global_channels
                    if channel.casefold() not in group_keys)
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
        f"âš ï¸ Solicitud retenida por {source_label}\n\n"
        f"Usuario: {full_name or 'Sin nombre'} ({username})\n"
        f"ID: {user_id}\n"
        f"Grupo: {pending.get('chat_title') or chat_id}\n"
        f"{detail_line}\n\n"
        "El usuario completÃ³ correctamente el captcha. Revisa el caso antes de permitir su entrada."
    )
    keyboard = {"inline_keyboard": [[
        {"text": "âœ… Aprobar igualmente", "callback_data": f"casjoin:a:{chat_id}:{user_id}"},
        {"text": "ðŸš« Banear y rechazar", "callback_data": f"casjoin:b:{chat_id}:{user_id}"},
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
                    "global_required_channels": _global_join_channels(),
                    "required_channel_suggestions": _required_channel_suggestions(chat_id),
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
            "note": "Antes de silenciar se excluirÃ¡n administradores, bots y usuarios que ya no pertenezcan al grupo."}})
    if action == "cancel":
        job = _db.get(job_key, {}) or {}
        if job.get("status") == "running":
            job["status"] = "cancel_requested"
            _db.set(job_key, job)
        return jsonify({"ok": True, "job": job})
    return jsonify({"ok": False, "error": "acciÃ³n no vÃ¡lida"}), 400


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
    for key in ("enabled", "mute_until_verified", "strict_enforcement", "max_attempts", "challenge_ttl", "challenge_types", "request_ttl", "reverify_interval_days", "exempt_user_ids", "required_channels"):
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
        "challenge_types": [
            value for value in (config.get("challenge_types") or [])
            if value in _JOIN_CHALLENGE_TYPES
        ] or list(_JOIN_CHALLENGE_TYPES),
        "request_ttl": _bounded_int(config["request_ttl"], 86400, 300, 604800),
        "reverify_interval_days": _bounded_int(config["reverify_interval_days"], 0, 0, 90),
        "exempt_user_ids": [str(value).strip() for value in exempt if str(value).strip().isdigit()][:100],
        "required_channels": _normalize_required_channels(required),
    }
    _db.set(f"JOINCFG_{chat_id}", config)
    if "global_required_channel" in body:
        global_channel = str(body.get("global_required_channel") or "").strip().lstrip("@")[:100]
        _db.set("JOIN_GLOBAL_REQUIRED_CHANNELS", [global_channel] if global_channel else [])
        _db.set("JOIN_GLOBAL_REQUIRED_CHANNEL", global_channel)
        _db.set("JOIN_GLOBAL_REQUIRED_ENABLED", bool(global_channel))
    return jsonify({"ok": True, "config": config,
                    "global_required_channel": _global_join_channel(),
                    "global_required_channels": _global_join_channels(),
                    "required_channel_suggestions": _required_channel_suggestions(chat_id)})


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
        return jsonify({"ok": False, "error": "user_id invÃ¡lido"}), 400
    action = body.get("action")
    if action not in ("approve", "decline"):
        return jsonify({"ok": False, "error": "acciÃ³n invÃ¡lida"}), 400
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
                "error": "El usuario aÃºn no estÃ¡ suscrito a todos los canales obligatorios",
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
        return jsonify({"ok": False, "error": result.get("description", "Telegram rechazÃ³ la acciÃ³n")}), 502
    if action == "approve" and pending.get("community_flagged") and _ban_manager:
        _ban_manager.unban_user(user_id)
    _db.delete(key)
    _db.delete(f"JOINC_{chat_id}_{user_id}")
    _bump_join_stat(chat_id, stat)
    return jsonify({"ok": True, "action": action})


def _challenge_digest(chat_id, user_id, challenge_id, salt, answer):
    """Firma la soluciÃ³n vinculÃ¡ndola al usuario, grupo y reto sin guardarla en claro."""
    canonical = json.dumps(answer, separators=(",", ":"), ensure_ascii=True)
    secret = str(_jwt_secret or current_app.config.get("SECRET_KEY") or "moonbot-captcha")
    payload = f"{chat_id}|{user_id}|{challenge_id}|{salt}|{canonical}".encode()
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def _new_join_challenge(challenge_type=None, difficulty=1):
    """Genera un reto accesible. Devuelve Ãºnicamente datos pÃºblicos y la soluciÃ³n."""
    rnd = secrets.SystemRandom()
    kind = challenge_type if challenge_type in _JOIN_CHALLENGE_TYPES else rnd.choice(_JOIN_CHALLENGE_TYPES)
    difficulty = max(1, min(int(difficulty or 1), 3))
    if kind == "icons":
        target = rnd.choice(_JOIN_ICONS)
        count = 3 if difficulty < 3 else 4
        size = 9 if difficulty < 2 else 12
        correct = sorted(rnd.sample(range(size), count))
        others = [icon for icon in _JOIN_ICONS if icon != target]
        grid = [target if index in correct else rnd.choice(others) for index in range(size)]
        return {"type": kind, "target": target, "grid": grid, "required": count}, correct
    if kind == "sequence":
        size = 6 if difficulty < 3 else 8
        options = rnd.sample(_JOIN_ICONS, min(size, len(_JOIN_ICONS)))
        length = 2 if difficulty == 1 else 3
        sequence = rnd.sample(options, length)
        return {"type": kind, "sequence": sequence, "grid": options, "required": length}, [
            options.index(icon) for icon in sequence
        ]
    if kind == "shapes":
        size = 9 if difficulty < 3 else 12
        target = {"shape": rnd.choice(_JOIN_SHAPES), "color": rnd.choice(_JOIN_COLORS)}
        correct_index = rnd.randrange(size)
        grid = []
        for index in range(size):
            if index == correct_index:
                grid.append(target)
                continue
            candidate = target
            while candidate == target:
                candidate = {"shape": rnd.choice(_JOIN_SHAPES), "color": rnd.choice(_JOIN_COLORS)}
            grid.append(candidate)
        return {"type": kind, "target": target, "grid": grid, "required": 1}, [correct_index]
    upper = (9, 20, 50)[difficulty - 1]
    left, right = rnd.randint(2, upper), rnd.randint(1, upper)
    operator = rnd.choice(["+", "-"])
    if operator == "-" and right > left:
        left, right = right, left
    result = left + right if operator == "+" else left - right
    options = {result}
    while len(options) < 4:
        options.add(max(0, result + rnd.choice((-7, -5, -3, -2, -1, 1, 2, 3, 5, 7))))
    options = list(options)
    rnd.shuffle(options)
    return {
        "type": kind, "prompt": f"{left} {operator} {right}", "grid": options, "required": 1
    }, [options.index(result)]


@bp.route("/api/public/join/challenge", methods=["POST", "OPTIONS"])
def join_challenge():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
    cid, uid = body.get("chat"), user.get("id")
    if cid is None:
        return jsonify({"ok": False, "error": "falta chat"}), 400
    pend = _db.get(f"JOINQ_{cid}_{uid}") if _db else None
    if not pend or pend.get("exp", 0) < time.time():
        return jsonify({"ok": False, "error": "sin solicitud pendiente"}), 410
    if pend.get("captcha_passed") and (pend.get("cas_flagged") or pend.get("community_flagged")):
        return jsonify({"ok": False, "under_review": True,
                        "error": "solicitud en revisiÃ³n administrativa"}), 423
    config = _join_config(cid)
    if not config["enabled"]:
        return jsonify({"ok": False, "error": "captcha desactivado"}), 403
    if pend.get("captcha_passed") and pend.get("subscription_pending"):
        missing = _missing_required_channels(_hub_bot(), cid, uid) if _hub_bot() else []
        if missing:
            return jsonify({"ok": False, "subscription_required": True, "missing_channels": missing}), 423
        return jsonify({"ok": True, "resume": True})
    challenge_key = f"JOINC_{cid}_{uid}"
    existing = _db.get(challenge_key, {}) if _db else {}
    now = int(time.time())
    if existing.get("exp", 0) > now and isinstance(existing.get("public"), dict):
        return jsonify({"ok": True, **existing["public"],
                        "expires_in": max(1, existing["exp"] - now)})
    attempts = int(pend.get("attempts", 0))
    difficulty = min(3, 1 + attempts)
    enabled_types = config["challenge_types"]
    previous_type = str(pend.get("last_challenge_type") or "")
    candidates = [kind for kind in enabled_types if kind != previous_type] or enabled_types
    public, answer = _new_join_challenge(secrets.choice(candidates), difficulty)
    challenge_id = secrets.token_urlsafe(18)
    salt = secrets.token_hex(16)
    public.update({"challenge_id": challenge_id, "difficulty": difficulty})
    expires_at = now + config["challenge_ttl"]
    _db.set(challenge_key, {
        "challenge_id": challenge_id,
        "answer_digest": _challenge_digest(cid, uid, challenge_id, salt, answer),
        "salt": salt,
        "public": public,
        "exp": expires_at,
        "used": False,
    })
    pend["last_challenge_type"] = public["type"]
    pend["challenge_issued_at"] = now
    _db.set(f"JOINQ_{cid}_{uid}", pend)
    return jsonify({"ok": True, **public, "expires_in": config["challenge_ttl"]})


@bp.route("/api/public/join/verify", methods=["POST", "OPTIONS"])
def join_verify():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
    cid, uid = body.get("chat"), user.get("id")
    pend = _db.get(f"JOINQ_{cid}_{uid}") if _db else None
    if not pend or pend.get("exp", 0) < time.time():
        return jsonify({"ok": False, "expired": True, "error": "solicitud expirada"}), 410
    chal = _db.get(f"JOINC_{cid}_{uid}")
    if not body.get("resume") and (not chal or chal.get("exp", 0) < time.time()):
        return jsonify({"ok": False, "expired": True, "error": "reto expirado"})
    try:
        sel = [int(i) for i in (body.get("selected") or [])]
    except (TypeError, ValueError):
        sel = []
    bot = _hub_bot()
    if not bot:
        return jsonify({"ok": False, "error": "bot no disponible"}), 503
    config = _join_config(cid)
    # â”€â”€ Ã‰XITO â”€â”€
    resumed = bool(body.get("resume") and pend.get("captcha_passed"))
    challenge_matches = False
    if not resumed and chal:
        supplied_id = str(body.get("challenge_id") or "")
        stored_id = str(chal.get("challenge_id") or "")
        if supplied_id and hmac.compare_digest(supplied_id, stored_id) and not chal.get("used"):
            expected = str(chal.get("answer_digest") or "")
            actual = _challenge_digest(cid, uid, stored_id, chal.get("salt", ""), sel)
            challenge_matches = bool(expected) and hmac.compare_digest(actual, expected)
        # El reto se consume incluso si la respuesta es errÃ³nea: impide repeticiÃ³n.
        _db.delete(f"JOINC_{cid}_{uid}")
    if resumed or challenge_matches:
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
                pend["permission_restore_error"] = result.get("description", "Telegram rechazÃ³ la restauraciÃ³n")
                _db.set(f"JOINQ_{cid}_{uid}", pend)
                return jsonify({"ok": False, "error": "captcha superado, pero no se pudieron restaurar los permisos"}), 502
        _db.set(f"CAPTCHA_STATUS_{cid}_{uid}", {"status": "passed", "at": int(time.time()), "reason": pend.get("reason", "")})
        _db.delete(f"JOINC_{cid}_{uid}"); _db.delete(f"JOINQ_{cid}_{uid}")  # query_id de un solo uso
        _bump_join_stat(cid, "approved")
        return jsonify({"ok": True, "approved": True})
    # â”€â”€ FALLO â”€â”€
    attempts = int(pend.get("attempts", 0)) + 1
    _db.delete(f"JOINC_{cid}_{uid}")  # fuerza reto nuevo (no resetea intentos)
    if attempts >= config["max_attempts"]:
        if pend.get("forced"):
            _db.set(f"CAPTCHA_APPEAL_{cid}_{uid}", {
                "status": "available", "chat_id": cid, "user_id": uid,
                "reason": pend.get("reason", "Lista de IDs detectada"),
                "created_at": int(time.time()),
            })
            _db.set(f"CAPTCHA_STATUS_{cid}_{uid}", {"status": "failed", "at": int(time.time()), "reason": pend.get("reason", "")})
        elif bot:
            if pend.get("admitted"):
                bot.api_call("banChatMember", {"chat_id": cid, "user_id": uid})
            else:
                bot.api_call("declineChatJoinRequest", {"chat_id": cid, "user_id": uid})
        _db.delete(f"JOINQ_{cid}_{uid}")
        _bump_join_stat(cid, "declined")
        return jsonify({"ok": False, "declined": True, "appeal_available": bool(pend.get("forced")), "attempts_left": 0})
    pend["attempts"] = attempts
    _db.set(f"JOINQ_{cid}_{uid}", pend)
    return jsonify({"ok": False, "attempts_left": config["max_attempts"] - attempts})


@bp.route("/api/public/join/appeal", methods=["POST", "OPTIONS"])
def join_appeal():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.json or {}
    user = _verify_init_data(body.get("initData", ""))
    if user is None:
        return jsonify({"ok": False, "error": "initData invÃ¡lido"}), 401
    cid, uid = body.get("chat"), user.get("id")
    appeal = _db.get(f"CAPTCHA_APPEAL_{cid}_{uid}") if _db else None
    if not appeal or appeal.get("status") != "available":
        return jsonify({"ok": False, "error": "sin apelaciÃ³n disponible"}), 404
    text = str(body.get("text") or "").strip()[:1000]
    if len(text) < 10:
        return jsonify({"ok": False, "error": "explica el motivo con mÃ¡s detalle"}), 400
    appeal.update({"status": "pending", "text": text, "submitted_at": int(time.time())})
    _db.set(f"CAPTCHA_APPEAL_{cid}_{uid}", appeal)
    bot = _hub_bot()
    if bot and _master_id:
        bot.send_msg(_master_id, f"ðŸ“¨ ApelaciÃ³n de captcha\nUsuario: {uid}\nGrupo: {cid}\nMotivo original: {appeal.get('reason')}\n\n{text}")
    return jsonify({"ok": True, "submitted": True})


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Canales â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@bp.route("/api/public/stats/global")
def public_global():
    v_lower = (APP_VERSION or "").lower()
    ch = "alfa" if "alpha" in v_lower or "alfa" in v_lower else "beta" if "beta" in v_lower else "rc" if "rc" in v_lower else "estable"
    return jsonify({"ok": True, "app_version": APP_VERSION, "channel": ch, **_channel_stats.get_global_stats()})


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
    registry = _db.get("TELEGRAM_COMMUNITIES", {}) or {}
    public_rows = []
    for row in rows:
        chat_id = str(row.get("chat_id") or row.get("id") or "")
        record = registry.get(chat_id) or {}
        community = record.get("community") or {}
        public_rows.append({**row, "community": {
            "id": str(record.get("community_id") or community.get("id") or ""),
            "title": str(community.get("title") or community.get("name") or "")[:120],
            "active": bool(record.get("active")),
        } if record.get("active") else None})
    return jsonify({"ok": True, "channels": public_rows})


@bp.route("/api/public/stats/channels/<username>")
def public_channel(username):
    ch = _channel_stats.get_channel(username)
    if not ch:
        return jsonify({"ok": False, "error": "not found"}), 404
    registry = _db.get("TELEGRAM_COMMUNITIES", {}) or {}
    chat_id = str(ch.get("chat_id") or ch.get("id") or "")
    record = registry.get(chat_id) or {}
    community = record.get("community") or {}
    public_community = None
    if record.get("active"):
        community_id = str(record.get("community_id") or community.get("id") or "")
        peers = []
        for row in _channel_stats.get_channels():
            peer_id = str(row.get("chat_id") or row.get("id") or "")
            peer_record = registry.get(peer_id) or {}
            if peer_id == chat_id or not peer_record.get("active") or str(peer_record.get("community_id") or "") != community_id:
                continue
            peers.append({"name": row.get("name") or row.get("username"), "username": row.get("username")})
        public_community = {
            "id": community_id,
            "title": str(community.get("title") or community.get("name") or f"Comunidad {community_id}")[:120],
            "active": True,
            "channels": peers[:24],
        }
    return jsonify({"ok": True, "channel": {**ch, "community": public_community}})


@bp.route("/api/public/stats/ranking")
def public_ranking():
    cat = request.args.get("category", "sin-categoria")
    return jsonify({"ok": True, "ranking": _channel_stats.get_ranking(cat)})


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Proxy â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@bp.route("/api/public/proxy")
def public_proxy():
    """Devuelve proxies MTProto activos, usando el catÃ¡logo de red como respaldo."""
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
            return jsonify({"ok": False, "error": "catÃ¡logo de proxies no disponible", "detail": str(exc)[:160]}), 502
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
        action = str(body.get("action") or "list")
        if action in {"insights", "export_metrics"}:
            insights = _house_ads_insights(_house_ads_payload())
            if action == "export_metrics":
                return jsonify({"ok": True, "filename": "moonbot-house-ads-metrics.csv",
                                "content_type": "text/csv;charset=utf-8", "csv": _house_ads_insights_csv(insights)})
            return jsonify({"ok": True, "insights": insights})
        if action != "list": _house_ads_update(body)
        grouped = {}
        for row in _admin_group_rows():
            record = row.get("community") or {}
            community_id = str(record.get("community_id") or (record.get("community") or {}).get("id") or "")
            username = str(row.get("username") or "").strip().lstrip("@")
            if not record.get("active") or not community_id or not re.fullmatch(r"[A-Za-z0-9_]{5,64}", username):
                continue
            community = grouped.setdefault(community_id, {"id": community_id,
                "title": (record.get("community") or {}).get("title") or (record.get("community") or {}).get("name") or f"Comunidad {community_id}", "items": []})
            community["items"].append({"id": str(row.get("id"))[:64], "title": str(row.get("name") or username)[:80],
                                       "url": f"https://t.me/{username}",
                                       "type": "channel" if row.get("ctype") == "channel" else "group", "image": ""})
        communities = [{**community, "items": community["items"][:16]} for community in grouped.values() if community["items"]]
        return jsonify({"ok": True, "ads": _house_ads_payload(), "communities": communities})
    except (TypeError, ValueError) as error: return jsonify({"ok": False, "error": str(error)}), 400


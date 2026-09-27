"""One personal RSS scheduler, with persistent daily quota and Telegram membership gate."""
import datetime
import hmac
import os
import threading
import time
from pathlib import Path
from flask import jsonify, request, send_from_directory
from core.personal_rss_engine import PersonalRssManager
from core.rss_subscriptions import install_rss_routes
from core.rss_catalog import CATALOG
from core.rss_channels import channel_bot, register_channel_routes

CHANNEL = "@TodoSobreAllTech"
DAILY_LIMIT = 50


class PersonalRssService:
    def __init__(self, db, get_bots, clock=None):
        self.db, self.get_bots = db, get_bots
        self.manager = PersonalRssManager(db)
        self.lock = threading.RLock()
        self.members = {}
        self.admin_checks = {}
        self.clock = clock or (lambda: datetime.datetime.now(datetime.timezone.utc))

    def bot(self, uid):
        return next((b for b in self.get_bots() if str(uid) in {str(x) for x in self.db.get(f"CHATS_{b.token}", [])}), None)

    def quota(self, uid):
        day = self.clock().date().isoformat()
        row = self.db.get(f"PERSONAL_RSS_DAILY_{uid}", {}) or {}
        return dict(day=day, used=max(0, int(row.get("used", 0))) if row.get("day") == day else 0)

    def membership(self, uid, refresh=False):
        cached = self.members.get(str(uid))
        if cached and time.monotonic() - cached[0] < (15 if refresh else 300):
            return cached[1]
        state = "unavailable"
        for bot in self.get_bots():
            try:
                key = str(bot.token).split(":", 1)[0]
                admin = self.admin_checks.get(key)
                if not admin or time.monotonic() - admin[0] > 300:
                    own = bot.api_call("getChatMember", {"chat_id": CHANNEL, "user_id": key})
                    allowed = isinstance(own, dict) and own.get("ok") and own.get("result", {}).get("status") in ("administrator", "creator")
                    admin = (time.monotonic(), bool(allowed)); self.admin_checks[key] = admin
                if not admin[1]:
                    continue
                result = bot.api_call("getChatMember", {"chat_id": CHANNEL, "user_id": str(uid)})
                if not isinstance(result, dict) or not result.get("ok"):
                    continue
                member = result.get("result", {})
                status = member.get("status")
                if status in ("member", "administrator", "creator") or (status == "restricted" and member.get("is_member")):
                    state = "member"
                    break
                if status in ("left", "kicked") or status == "restricted":
                    state = "not_member"
                    break
            except Exception:
                continue
        if len(self.members) >= 2000:
            self.members.clear()
        self.members[str(uid)] = (time.monotonic(), state)
        return state

    def allowance(self, uid, refresh=False):
        quota = self.quota(uid)
        state = self.membership(uid, refresh) if refresh or quota["used"] >= DAILY_LIMIT else "not_checked"
        return {**quota, "limit": DAILY_LIMIT, "timezone": "UTC", "channel": CHANNEL,
                "membership": state, "delivery_uncertain": bool(self.db.get(f"PERSONAL_RSS_INFLIGHT_{uid}")),
                "blocked": quota["used"] >= DAILY_LIMIT and state != "member"}

    def action(self, uid, body, actor):
        with self.lock:
            action = body.get("action", "list")
            try:
                if action == "add":
                    if not isinstance(body.get("url"), str) or len(body["url"]) > 2000:
                        raise ValueError("Invalid URL")
                    self.manager.add(uid, body.get("url"), body.get("title"), actor)
                elif action == "toggle": self.manager.set_enabled(uid, body.get("feed_id"), body.get("enabled"))
                elif action == "delete": self.manager.remove(uid, body.get("feed_id"))
                elif action not in ("list", "verify_membership"):
                    return {"ok": False, "error": "Acción no permitida"}, 400
                return {"ok": True, "feeds": self.manager.list(uid), "limit": self.manager.MAX_FEEDS,
                        "catalog": CATALOG, "quota": self.allowance(uid, action == "verify_membership") if str(uid).isdigit() else None}, 200
            except KeyError:
                return {"ok": False, "error": "Suscripción no encontrada"}, 404
            except (ValueError, TypeError, OSError):
                return {"ok": False, "error": "No se pudo guardar. Revisa la URL pública y los datos de la fuente."}, 400

    def cycle(self):
        for uid in list(self.db.get("GROUP_RSS_GROUPS", []) or []):
            uid = str(uid)
            private = uid.isdigit()
            owner = self.db.get(f"PERSONAL_RSS_CHANNEL_OWNER_{uid}")
            target_bot = self.bot(uid) if private else channel_bot(self, owner, uid) if owner else None
            if not target_bot or self.db.get(f"PERSONAL_RSS_INFLIGHT_{uid}"):
                continue
            with self.lock:
                feed_ids = [f["id"] for f in self.manager.list(uid) if f.get("enabled")]
            for feed_id in feed_ids:
                with self.lock:
                    if private and self.allowance(uid)["blocked"]:
                        break
                    entries = self.manager.poll(chat_filter=uid, feed_filter=feed_id)
                for entry in entries:
                    with self.lock:
                        if self.db.get(f"PERSONAL_RSS_INFLIGHT_{uid}") or (private and self.allowance(uid)["blocked"]):
                            break
                        feed = next((f for f in self.manager.list(uid) if f.get("id") == entry["feed_id"] and f.get("enabled")), None)
                        if not feed:
                            continue
                        # Reserve before sending: an uncertain result must not be replayed.
                        if private:
                            quota = self.quota(uid); quota["used"] += 1
                            self.db.set(f"PERSONAL_RSS_DAILY_{uid}", quota)
                        marker = f"PERSONAL_RSS_INFLIGHT_{uid}"
                        self.db.set(marker, {"feed_id": entry["feed_id"], "entry_id": entry["id"]})
                        message = f"{entry['title']}\n{entry['url']}"[:3600]
                        if not private:
                            from core.rss_reader import WEBAPP_URL
                            message += "\n\nDescubre más noticias en nuestra WebApp: " + WEBAPP_URL
                        result = target_bot.send_msg(uid, message, parse_mode=None)
                        if isinstance(result, dict) and result.get("ok"):
                            self.manager.mark_published(uid, entry["feed_id"], entry)
                            self.db.set(marker, None)
                        else:
                            break
                    # Do not hold the configuration lock while rate-limiting this chat.
                    time.sleep(1.05)

    def start(self):
        def run():
            import fcntl
            folder = Path(os.getenv("MOON_GOVERNOR_PATH", "/app/data/governor")); folder.mkdir(parents=True, exist_ok=True)
            with (folder / "personal-rss.lock").open("a") as handle:
                try: fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError: return
                while True:
                    try: self.cycle()
                    except Exception: pass  # Keep the scheduler alive; no secret URLs in logs.
                    time.sleep(60)
        self.thread = threading.Thread(target=run, name="personal-rss", daemon=True)
        self.thread.start()


def register_personal_rss(app, public):
    service = PersonalRssService(public._db, lambda: public._get_active_bots() or [])
    def authorized():
        expected = os.getenv("MOON_ADMIN_API_KEY", "").strip()
        supplied = request.headers.get("X-Moon-Admin-Key", "").strip()
        return bool(expected and supplied and hmac.compare_digest(expected.encode(), supplied.encode()))
    install_rss_routes(app, authorized, lambda: service.manager, service.action, lambda: public._db, service.get_bots)
    @app.get("/api/internal/rss/catalog")
    def rss_catalog():
        if not authorized(): return jsonify(ok=False), 401
        return jsonify(ok=True, catalog=CATALOG)
    @app.post("/api/public/rss/mine")
    def rss_mine():
        body = request.get_json(silent=True) or {}
        if not isinstance(body, dict): return jsonify(ok=False), 400
        user = public._verify_init_data(body.get("initData", ""))
        if not user: return jsonify(ok=False, error="Abre el Hub desde Telegram para ver tus RSS."), 401
        uid = str(user.get("id", ""))
        if not service.bot(uid): return jsonify(ok=False, error="Pulsa Iniciar en el chat privado del bot antes de activar RSS."), 409
        if body.get("action") == "toggle" and not isinstance(body.get("enabled"), bool): return jsonify(ok=False), 400
        clean = {k: body[k] for k in ("action", "url", "title", "feed_id", "enabled") if k in body}
        payload, status = service.action(uid, clean, uid)
        return jsonify(payload), status
    @app.get("/hub-rss.js")
    def rss_asset():
        response = send_from_directory(str(Path(__file__).resolve().parents[1] / "web"), "hub-rss.js")
        response.headers["Cache-Control"] = "no-cache"
        return response
    register_channel_routes(app, service, public, authorized)
    from core.rss_reader import register_reader_routes
    register_reader_routes(app, service, public, authorized)
    @app.get("/api/internal/rss/health")
    def rss_health():
        if not authorized(): return jsonify(ok=False), 401
        can_verify = False
        for bot in service.get_bots():
            try:
                value = bot.api_call("getChatMember", {"chat_id": CHANNEL, "user_id": str(bot.token).split(":",1)[0]})
                if value.get("ok") and value.get("result",{}).get("status") in ("administrator","creator"):
                    can_verify = True
                    break
            except Exception: pass
        return jsonify(ok=True, scheduler_alive=service.thread.is_alive(), membership_verification_ready=can_verify, catalog_sources=len(CATALOG))
    service.start()
    return service

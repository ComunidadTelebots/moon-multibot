"""Personal RSS and aggregate master metrics using the existing delivery engine."""
import hashlib
import re
import threading
import time
from flask import jsonify, request


def aggregate_rss(manager, db):
    sources, recipients = {}, []
    totals = dict(subscriptions=0, enabled=0, published=0, checks=0, errors=0)
    for cid in dict.fromkeys(str(x) for x in (db.get("GROUP_RSS_GROUPS", []) or [])):
        feeds = manager.list(cid)
        if not feeds:
            continue
        recipient = dict(id=cid, kind="user" if re.fullmatch(r"[1-9]\d*", cid) else "community",
                         subscriptions=len(feeds), published=0, errors=0)
        for feed in feeds:
            def count(key):
                try:
                    return max(0, int(feed.get(key, 0)))
                except (TypeError, ValueError):
                    return 0
            key = hashlib.sha256(str(feed.get("url", "")).encode()).hexdigest()[:16]
            row = sources.setdefault(key, dict(id=key, title=str(feed.get("title") or "Fuente sin título")[:120],
                                              subscriptions=0, published=0, checks=0, errors=0, enabled=0))
            values = dict(subscriptions=1, enabled=int(bool(feed.get("enabled"))),
                          published=count("published_count"), checks=count("checks_count"), errors=count("error_count"))
            for name, value in values.items():
                row[name] += value
                totals[name] += value
            recipient["published"] += values["published"]
            recipient["errors"] += values["errors"]
        recipients.append(recipient)
    return dict(ok=True, totals=totals, recipient_count=len(recipients),
                sources=sorted(sources.values(), key=lambda r: (-r["published"], r["id"]))[:30],
                recipients=sorted(recipients, key=lambda r: (-r["published"], r["id"]))[:30],
                period="Contadores acumulados disponibles; pueden reiniciarse. Entregas, no lecturas.")


def install_rss_routes(bp, authorized, manager_factory, action_handler, get_db, get_bots):
    lock = threading.RLock()
    cache = {"at": 0, "data": None}

    @bp.route("/api/internal/rss/users/<uid>", methods=["GET", "POST"])
    def personal_rss(uid):
        if not authorized():
            return jsonify(ok=False, error="unauthorized"), 401
        if not re.fullmatch(r"[1-9]\d{0,19}", uid):
            return jsonify(ok=False, error="Usuario no válido"), 400
        known = any(uid in {str(x) for x in (get_db().get(f"CHATS_{bot.token}", []) or [])}
                    for bot in (get_bots() or []))
        if not known:
            return jsonify(ok=False, error="Abre un chat privado con Moonbot y pulsa Iniciar antes de suscribirte."), 409
        body = (request.get_json(silent=True) or {}) if request.method == "POST" else {"action": "list"}
        if not isinstance(body, dict):
            return jsonify(ok=False, error="Solicitud no válida"), 400
        action = body.get("action", "list")
        if action not in {"list", "add", "toggle", "delete", "verify_membership"}:
            return jsonify(ok=False, error="Acción no permitida"), 400
        if action == "toggle" and not isinstance(body.get("enabled"), bool):
            return jsonify(ok=False, error="Estado no válido"), 400
        if action == "add" and (not isinstance(body.get("url"), str) or len(body["url"]) > 2000):
            return jsonify(ok=False, error="URL no válida"), 400
        # Explicit allowlist prevents thread/template or destination injection.
        clean = {k: body[k] for k in ("action", "url", "title", "feed_id", "enabled") if k in body}
        with lock:
            payload, status = action_handler(uid, clean, uid)
            cache["at"] = 0
        return jsonify(payload), status

    @bp.get("/api/internal/rss/activity")
    def rss_activity():
        if not authorized():
            return jsonify(ok=False, error="unauthorized"), 401
        with lock:
            if cache["data"] is None or time.monotonic() - cache["at"] > 30:
                cache["data"] = aggregate_rss(manager_factory(), get_db())
                cache["at"] = time.monotonic()
            response = jsonify(cache["data"])
        response.headers["Cache-Control"] = "no-store"
        return response

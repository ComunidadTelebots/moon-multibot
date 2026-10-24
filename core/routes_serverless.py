import os
from pathlib import Path

from flask import Blueprint, jsonify, request

from core.serverless_bridge import ServerlessBridgeStore
from core.serverless_manager import ServerlessError, ServerlessManager


bp = Blueprint("serverless", __name__)
_check_jwt = None
_add_audit_log = None
_manager = None
_jwt_secret = ""
_bridge_url = ""
_bridge = ServerlessBridgeStore()


def setup(check_jwt, add_audit_log, jwt_secret):
    global _check_jwt, _add_audit_log, _manager, _jwt_secret, _bridge_url
    _check_jwt = check_jwt
    _add_audit_log = add_audit_log
    app_root = Path(__file__).resolve().parent.parent
    root = os.getenv("SERVERLESS_PROJECTS_ROOT", str(app_root))
    registry = os.getenv(
        "SERVERLESS_BOTS_REGISTRY",
        str(app_root / "config" / "serverless_bots.json"),
    )
    enabled = os.getenv("SERVERLESS_CONTROL_ENABLED", "false").lower() in ("1", "true", "yes", "on")
    _manager = ServerlessManager(root, registry, enabled=enabled)
    _jwt_secret = str(jwt_secret or "")
    _bridge_url = os.getenv(
        "SERVERLESS_BRIDGE_PUBLIC_URL", "https://cintiabot.todosobreall.tech"
    ).rstrip("/")
    return bp


@bp.route("/api/serverless/bots")
def serverless_bots():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    try:
        return jsonify({"ok": True, "bots": _manager.list_status()})
    except ServerlessError as exc:
        return jsonify({"ok": False, "msg": str(exc)}), 503


@bp.route("/api/serverless/bots/<bot_id>/actions", methods=["POST"])
def serverless_action(bot_id):
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    action = str((request.get_json(silent=True) or {}).get("action", "")).strip()
    try:
        result = _manager.action(bot_id, action)
    except ServerlessError as exc:
        return jsonify({"ok": False, "msg": str(exc)}), 400
    _add_audit_log(f"Serverless {bot_id}: {action}")
    return jsonify({"ok": True, **result})


@bp.route("/api/serverless/ingest/<bot_id>", methods=["POST"])
def serverless_ingest(bot_id):
    try:
        row = _manager.bot_config(bot_id)
    except ServerlessError:
        return jsonify({"ok": False}), 404
    if not _bridge.authenticate(request.headers.get("Authorization"), _jwt_secret, row.get("app_id")):
        return jsonify({"ok": False}), 401
    payload = request.get_json(silent=True) or {}
    if payload.get("botId") != bot_id:
        return jsonify({"ok": False, "msg": "Bot no coincide"}), 400
    snapshot = _bridge.ingest(bot_id, payload)
    return jsonify({"ok": True, "lastSeenAt": snapshot["lastSeenAt"]})


@bp.route("/api/serverless/bots/<bot_id>/bridge/connect", methods=["POST"])
def serverless_bridge_connect(bot_id):
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    try:
        row = _manager.bot_config(bot_id)
        secret = _bridge.secret(_jwt_secret, row.get("app_id"))
        result = _manager.configure_bridge(
            bot_id,
            f"{_bridge_url}/api/serverless/ingest/{bot_id}",
            secret,
        )
    except ServerlessError as exc:
        return jsonify({"ok": False, "msg": str(exc)}), 400
    _add_audit_log(f"Serverless {bot_id}: puente conectado")
    return jsonify({"ok": True, "bridge": result})


@bp.route("/api/serverless/bots/<bot_id>/live")
def serverless_live(bot_id):
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    snapshot = _bridge.snapshot(bot_id)
    if not snapshot["connected"] or request.args.get("refresh") == "1":
        try:
            pulled = _manager.bridge_pull(bot_id, after=0, limit=40)
            snapshot = _bridge.merge_pull(bot_id, pulled)
        except ServerlessError as exc:
            if not snapshot["events"]:
                return jsonify({"ok": False, "msg": str(exc)}), 503
    return jsonify({"ok": True, **snapshot})


@bp.route("/api/serverless/bots/<bot_id>/commands", methods=["POST"])
def serverless_command(bot_id):
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    payload = request.get_json(silent=True) or {}
    try:
        result = _manager.bridge_command(bot_id, payload)
    except ServerlessError as exc:
        return jsonify({"ok": False, "msg": str(exc)}), 400
    action = str(payload.get("action") or "")
    _add_audit_log(f"Serverless {bot_id}: accion remota {action}")
    return jsonify({"ok": True, "result": result})

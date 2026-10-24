import os
from pathlib import Path

from flask import Blueprint, jsonify, request

from core.serverless_manager import ServerlessError, ServerlessManager


bp = Blueprint("serverless", __name__)
_check_jwt = None
_add_audit_log = None
_manager = None


def setup(check_jwt, add_audit_log):
    global _check_jwt, _add_audit_log, _manager
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

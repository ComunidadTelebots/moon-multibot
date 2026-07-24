import os
import tempfile
import time

import requests as _requests

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from core.media_analyzer import analyze_image

bp = Blueprint("security", __name__)

_check_jwt = None
_db = None
_vt_mgr = None
_add_web_log = None
_check_cas_status = None
_MAX_SCAN_BYTES = 10 * 1024 * 1024


def _append_threat_history(item):
    rows = _db.get("THREAT_ANALYSIS_HISTORY", [])
    if not isinstance(rows, list):
        rows = []
    rows.append(item)
    _db.set("THREAT_ANALYSIS_HISTORY", rows[-300:])


def setup(check_jwt, db, vt_mgr, add_web_log, check_cas_status):
    global _check_jwt, _db, _vt_mgr, _add_web_log, _check_cas_status
    _check_jwt = check_jwt
    _db = db
    _vt_mgr = vt_mgr
    _add_web_log = add_web_log
    _check_cas_status = check_cas_status
    return bp


@bp.route("/api/health/telegram")
def api_health_telegram():
    try:
        r = _requests.get("https://api.telegram.org", timeout=5)
        return jsonify({
            "ok": True,
            "status": "ONLINE" if r.status_code == 200 else "DEGRADED",
            "ping": f"{int(r.elapsed.total_seconds() * 1000)}ms",
        })
    except Exception:
        return jsonify({"ok": True, "status": "OFFLINE", "ping": "N/A"})


@bp.route("/api/security/vt/scan", methods=["POST"])
def api_security_vt_scan():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    file_hash = request.json.get("hash")
    if not file_hash:
        return jsonify({"ok": False, "error": "Hash faltante"}), 400
    return jsonify(_vt_mgr.scan_hash(file_hash))


@bp.route("/api/security/vt/analyze", methods=["POST"])
def api_security_vt_analyze():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    body = request.json or {}
    kind, value = str(body.get("kind", "")).lower(), str(body.get("value", "")).strip()
    result = _vt_mgr.analyze(kind, value)
    if result.get("ok"):
        _append_threat_history({
            "time": int(time.time()), "source": "virustotal",
            "kind": kind, "value": value[:500], "risk": result.get("risk", "pending"),
            "malicious": result.get("malicious", 0),
            "suspicious": result.get("suspicious", 0),
            "cached": bool(result.get("cached")),
        })
    return jsonify(result), 200 if result.get("ok") else 400


@bp.route("/api/security/vt/file", methods=["POST"])
def api_security_vt_file():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    upload = request.files.get("file")
    if not upload or not upload.filename:
        return jsonify({"ok": False, "error": "Archivo faltante"}), 400
    if request.content_length and request.content_length > _MAX_SCAN_BYTES + 1024 * 128:
        return jsonify({"ok": False, "error": "El archivo supera 10 MB"}), 413
    suffix = os.path.splitext(secure_filename(upload.filename))[1][:12]
    path = None
    try:
        with tempfile.NamedTemporaryFile(prefix="moon-vt-", suffix=suffix, delete=False) as target:
            path = target.name
            total = 0
            while True:
                chunk = upload.stream.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > _MAX_SCAN_BYTES:
                    return jsonify({"ok": False, "error": "El archivo supera 10 MB"}), 413
                target.write(chunk)
        result = _vt_mgr.scan_file(path, secure_filename(upload.filename))
        if result.get("ok"):
            _append_threat_history({
                "time": int(time.time()), "source": "virustotal",
                "kind": "file", "value": result.get("value"),
                "filename": secure_filename(upload.filename),
                "risk": result.get("risk", "pending"),
                "malicious": result.get("malicious", 0),
                "suspicious": result.get("suspicious", 0),
            })
        return jsonify(result), 200 if result.get("ok") else 400
    finally:
        if path:
            try:
                os.remove(path)
            except OSError:
                pass


@bp.route("/api/security/media/analyze", methods=["POST"])
def api_security_media_analyze():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    upload = request.files.get("image")
    if not upload or not upload.filename:
        return jsonify({"ok": False, "error": "Imagen faltante"}), 400
    if request.content_length and request.content_length > _MAX_SCAN_BYTES + 1024 * 128:
        return jsonify({"ok": False, "error": "La imagen supera 10 MB"}), 413
    suffix = os.path.splitext(secure_filename(upload.filename))[1][:12]
    path = None
    try:
        with tempfile.NamedTemporaryFile(prefix="moon-image-", suffix=suffix, delete=False) as target:
            path = target.name
            total = 0
            while True:
                chunk = upload.stream.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > _MAX_SCAN_BYTES:
                    return jsonify({"ok": False, "error": "La imagen supera 10 MB"}), 413
                target.write(chunk)
        options = {
            "ocr": request.form.get("ocr", "true") == "true",
            "impersonation": request.form.get("impersonation", "true") == "true",
            "sensitive": request.form.get("sensitive", "true") == "true",
        }
        result = analyze_image(path, options)
        result["filename"] = secure_filename(upload.filename)
        if result.get("ok"):
            _db.set("STATS_PHOTOS", int(_db.get("STATS_PHOTOS", 0)) + 1)
            _append_threat_history({
                "time": int(time.time()), "source": "vision",
                "kind": "image", "value": result.get("sha256"),
                "filename": result.get("filename"), "risk": result.get("risk"),
                "score": result.get("score"), "signals": result.get("signals", []),
            })
        return jsonify(result), 200 if result.get("ok") else 400
    finally:
        if path:
            try:
                os.remove(path)
            except OSError:
                pass


@bp.route("/api/security/threat-history")
def api_security_threat_history():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    rows = _db.get("THREAT_ANALYSIS_HISTORY", [])
    return jsonify({"ok": True, "history": list(reversed(rows[-100:])) if isinstance(rows, list) else []})


@bp.route("/api/security/cas/check/<uid>")
def api_security_cas_check(uid):
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    status = _check_cas_status(uid, use_cache=False)
    return jsonify({"ok": True, "cas_banned": status.get("banned", False), "cas": status})


@bp.route("/api/security/audit")
def api_security_audit():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    return jsonify({"ok": True, "logs": _db.get("SECURITY_AUDIT_LOGS", [])})


@bp.route("/api/vision/stats")
def get_vision_stats():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    history = _db.get("THREAT_ANALYSIS_HISTORY", [])
    history = history if isinstance(history, list) else []
    analysed = len(history)
    detected = sum(
        row.get("risk") in ("high", "medium") or int(row.get("malicious", 0) or 0) > 0
        for row in history
    )
    return jsonify({
        "ok": True,
        "photos": _db.get("STATS_PHOTOS", 0),
        "videos": _db.get("STATS_VIDEOS", 0),
        "threats": detected,
        "analyses": analysed,
        "clean_rate": round((analysed - detected) * 100 / analysed, 1) if analysed else 100,
        "shield_enabled": _db.get("NEURAL_SHIELD", True),
    })


@bp.route("/api/security/blacklist")
def get_security_blacklist():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    return jsonify({
        "ok": True,
        "blacklist": _db.get("BANNED_HASHES", []),
        "sync_urls": _db.get("SECURITY_SYNC_URLS", []),
    })


@bp.route("/api/security/add_sync_url", methods=["POST"])
def add_security_sync_url():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    url = request.json.get("url")
    if url:
        urls = _db.get("SECURITY_SYNC_URLS", [])
        if url not in urls:
            urls.append(url)
            _db.set("SECURITY_SYNC_URLS", urls)
        return jsonify({"ok": True})
    return jsonify({"ok": False})


@bp.route("/api/security/ban_hash", methods=["POST"])
def add_security_hash():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    h = request.json.get("hash")
    if h:
        banned = _db.get("BANNED_HASHES", [])
        if h not in banned:
            banned.append(h)
            _db.set("BANNED_HASHES", banned)
            _add_web_log("SECURITY", f"Manual Ban (Web): Hash {h} añadido.")
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "No hash provided"})

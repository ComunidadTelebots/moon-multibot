import os
import re
from urllib.parse import urlparse

import requests

CODE_RE = re.compile(r"^WEB-[A-Z0-9_-]{12}$")


def confirm_web_admin(code, telegram_id, telegram_username="", session=requests):
    code = str(code or "").strip().upper()
    telegram_id = str(telegram_id or "").strip()
    if not CODE_RE.fullmatch(code) or not telegram_id.isdigit():
        raise ValueError("código o identidad no válidos")
    key = os.getenv("MOON_ADMIN_API_KEY", "").strip()
    if len(key) < 32:
        raise RuntimeError("verificación web no configurada")
    url = os.getenv(
        "WEB_ADMIN_VERIFY_URL",
        "http://todosobrealltech-api:3001/moonbot-admin/web-admin-verifications/confirm",
    ).strip()
    parsed = urlparse(url)
    internal_http = parsed.scheme == "http" and parsed.hostname in {
        "todosobrealltech-api", "api", "127.0.0.1", "localhost",
    }
    if not (parsed.scheme == "https" or internal_http):
        raise RuntimeError("URL de verificación web insegura")
    response = session.post(url, json={"code": code, "telegram_id": telegram_id,
        "telegram_username": str(telegram_username or "").lstrip("@")},
        headers={"X-Moon-Admin-Key": key}, timeout=12)
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("respuesta inválida del servicio web") from exc
    if response.status_code >= 400 or not payload.get("ok"):
        raise ValueError(payload.get("error") or "no se pudo verificar la cuenta")
    return payload

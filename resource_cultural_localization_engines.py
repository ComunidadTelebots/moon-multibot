"""Cultural localisation contracts for seven Moonbot operational resources."""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any, Callable


IDS = tuple(f"future-{number}" for number in (5021, 5024, 5027, 5030, 5033, 5036, 5039))

LOCALES = {
    "es-ES": {"language": "es", "direction": "ltr", "date": "%d/%m/%Y", "decimal": ",", "thousands": "."},
    "en-US": {"language": "en", "direction": "ltr", "date": "%m/%d/%Y", "decimal": ".", "thousands": ","},
    "fr-FR": {"language": "fr", "direction": "ltr", "date": "%d/%m/%Y", "decimal": ",", "thousands": " "},
    "ar": {"language": "ar", "direction": "rtl", "date": "%Y/%m/%d", "decimal": "٫", "thousands": "٬"},
}


def _context(locale: str) -> dict[str, str]:
    code = str(locale or "").replace("_", "-")
    if code not in LOCALES:
        raise ValueError("locale no soportado")
    return {"locale": code, **LOCALES[code]}


def _text(value: Any, field: str, maximum: int = 500) -> str:
    clean = " ".join(str(value or "").split())
    if not clean or len(clean) > maximum:
        raise ValueError(f"{field} no válido")
    return clean


def _date(value: Any, context: dict[str, str]) -> str:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("fecha no válida") from exc
    if parsed.tzinfo is None:
        raise ValueError("fecha sin zona horaria")
    return parsed.astimezone(timezone.utc).strftime(context["date"])


def _number(value: Any, context: dict[str, str], decimals: int = 0) -> str:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError("número no válido")
    raw = f"{float(value):,.{decimals}f}"
    return raw.replace(",", "\0").replace(".", context["decimal"]).replace("\0", context["thousands"])


def _base(feature_id: str, resource: str, locale: str) -> dict[str, Any]:
    context = _context(locale)
    return {
        "feature_id": feature_id,
        "resource": resource,
        **context,
        "identifiers_preserved": True,
        "user_content_translated": False,
        "executed": False,
    }


def localize_mtproto_proxy(data: dict[str, Any], locale: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("data debe ser un objeto")
    result = _base(IDS[0], "mtproto_proxy", locale)
    host = _text(data.get("host"), "host", 253)
    if not re.fullmatch(r"[A-Za-z0-9.-]+", host):
        raise ValueError("host no válido")
    port = data.get("port")
    latency = data.get("latency_ms")
    if not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535:
        raise ValueError("port no válido")
    if not isinstance(latency, (int, float)) or isinstance(latency, bool) or latency < 0:
        raise ValueError("latency_ms no válida")
    return {**result, "host": host, "port": port, "latency_ms": latency, "latency_display": _number(latency, result) + " ms"}


def localize_persistent_task(data: dict[str, Any], locale: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("data debe ser un objeto")
    result = _base(IDS[1], "persistent_task", locale)
    status = data.get("status")
    if status not in {"pending", "running", "completed", "failed"}:
        raise ValueError("status no válido")
    return {**result, "task_id": _text(data.get("task_id"), "task_id", 128), "title": _text(data.get("title"), "title", 200), "status": status, "due_date": _date(data.get("due_at"), result)}


def localize_moderation_rule(data: dict[str, Any], locale: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("data debe ser un objeto")
    result = _base(IDS[2], "moderation_rule", locale)
    severity = data.get("severity")
    if severity not in {"info", "warning", "high", "critical"}:
        raise ValueError("severity no válida")
    return {**result, "rule_id": _text(data.get("rule_id"), "rule_id", 128), "name": _text(data.get("name"), "name", 160), "severity": severity, "enabled": data.get("enabled") is True}


def localize_language_metric(data: dict[str, Any], locale: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("data debe ser un objeto")
    result = _base(IDS[3], "language_metric", locale)
    language_code = str(data.get("language_code") or "").lower()
    if not re.fullmatch(r"[a-z]{2,3}(?:-[a-z0-9]{2,8})?", language_code):
        raise ValueError("language_code no válido")
    users = data.get("users")
    percentage = data.get("percentage")
    if not isinstance(users, int) or isinstance(users, bool) or users < 0:
        raise ValueError("users no válido")
    if not isinstance(percentage, (int, float)) or isinstance(percentage, bool) or not 0 <= percentage <= 100:
        raise ValueError("percentage no válido")
    return {**result, "language_code": language_code, "users": users, "users_display": _number(users, result), "percentage": percentage, "percentage_display": _number(percentage, result, 1) + "%"}


def localize_community_translation(data: dict[str, Any], locale: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("data debe ser un objeto")
    result = _base(IDS[4], "community_translation", locale)
    source_locale = _text(data.get("source_locale"), "source_locale", 20)
    target_locale = _text(data.get("target_locale"), "target_locale", 20)
    if source_locale == target_locale:
        raise ValueError("Los locales de origen y destino deben ser distintos")
    return {**result, "translation_id": _text(data.get("translation_id"), "translation_id", 128), "source_locale": source_locale, "target_locale": target_locale, "text": _text(data.get("text"), "text", 10000), "community_reviewed": data.get("community_reviewed") is True}


def localize_personal_consent(data: dict[str, Any], locale: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("data debe ser un objeto")
    result = _base(IDS[5], "personal_consent", locale)
    state = data.get("state")
    if state not in {"granted", "revoked", "expired"}:
        raise ValueError("state no válido")
    scopes = data.get("scopes")
    if not isinstance(scopes, list) or not scopes or len(scopes) > 50:
        raise ValueError("scopes no válido")
    clean_scopes = tuple(sorted({_text(scope, "scope", 80) for scope in scopes}))
    return {**result, "subject_id": _text(data.get("subject_id"), "subject_id", 128), "state": state, "scopes": clean_scopes, "recorded_date": _date(data.get("recorded_at"), result)}


def localize_telegram_reaction(data: dict[str, Any], locale: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("data debe ser un objeto")
    result = _base(IDS[6], "telegram_reaction", locale)
    reaction = _text(data.get("reaction"), "reaction", 32)
    count = data.get("count")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        raise ValueError("count no válido")
    return {**result, "message_id": _text(data.get("message_id"), "message_id", 128), "reaction": reaction, "count": count, "count_display": _number(count, result), "observed_date": _date(data.get("observed_at"), result)}


ALL_APIS = (
    localize_mtproto_proxy,
    localize_persistent_task,
    localize_moderation_rule,
    localize_language_metric,
    localize_community_translation,
    localize_personal_consent,
    localize_telegram_reaction,
)

assert len(IDS) == len(ALL_APIS) == 7
assert len({operation.__name__ for operation in ALL_APIS}) == 7

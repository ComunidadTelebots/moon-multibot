"""Cultural localisation and resource-aware easy-reading transformations."""

from __future__ import annotations

import re
from typing import Any, Callable
from urllib.parse import urlsplit

from resource_cultural_localization_engines import _base, _date, _number, _text


IDS = tuple(
    f"future-{number}"
    for number in (
        5042, 5045, 5048, 5051, 5054, 5057, 5060, 5063, 5066, 5069,
        5072, 5075, 5078, 5081, 5084, 5087, 5090, 5093, 5096, 5099,
    )
)


def localize_master_panel(data: dict[str, Any], locale: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("data debe ser un objeto")
    result = _base(IDS[0], "master_panel", locale)
    widgets = data.get("visible_widgets")
    if not isinstance(widgets, list) or len(widgets) > 100:
        raise ValueError("visible_widgets no válido")
    return {
        **result,
        "panel_id": _text(data.get("panel_id"), "panel_id", 128),
        "title": _text(data.get("title"), "title", 160),
        "visible_widgets": tuple(_text(item, "widget", 80) for item in widgets),
        "updated_date": _date(data.get("updated_at"), result),
    }


def localize_channel_directory(data: dict[str, Any], locale: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("data debe ser un objeto")
    result = _base(IDS[1], "channel_directory", locale)
    entries = data.get("entry_count")
    verified = data.get("verified_count")
    if not all(isinstance(value, int) and not isinstance(value, bool) and value >= 0 for value in (entries, verified)):
        raise ValueError("contadores no válidos")
    if verified > entries:
        raise ValueError("verified_count supera entry_count")
    return {
        **result,
        "directory_id": _text(data.get("directory_id"), "directory_id", 128),
        "title": _text(data.get("title"), "title", 160),
        "entry_count": entries,
        "entry_count_display": _number(entries, result),
        "verified_count": verified,
        "verified_count_display": _number(verified, result),
    }


def localize_external_link(data: dict[str, Any], locale: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("data debe ser un objeto")
    result = _base(IDS[2], "external_link", locale)
    url = str(data.get("url") or "")
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Se requiere una URL HTTPS sin credenciales")
    reputation = data.get("reputation")
    if reputation not in {"unknown", "safe", "warning", "blocked"}:
        raise ValueError("reputation no válida")
    return {
        **result,
        "url": url,
        "hostname": parsed.hostname.lower(),
        "label": _text(data.get("label"), "label", 200),
        "reputation": reputation,
        "checked_date": _date(data.get("checked_at"), result),
    }


_EASY_SPECS = (
    ("administrative_sessions", {"credential": "dato de acceso", "terminate": "cerrar"}),
    ("community_profiles", {"visibility": "quién puede verlo", "metadata": "datos del perfil"}),
    ("telegram_communities", {"federated": "con varios grupos", "moderation": "control de mensajes"}),
    ("house_ads", {"placement": "lugar del anuncio", "impression": "visualización"}),
    ("voice_notes", {"transcription": "texto de la nota de voz", "retention": "tiempo guardado"}),
    ("suspicious_files", {"quarantine": "zona segura", "malware": "programa dañino"}),
    ("captcha_decisions", {"challenge": "prueba", "confidence": "nivel de seguridad"}),
    ("managed_bots", {"instance": "bot", "permission": "permiso"}),
    ("recurring_reminders", {"recurrence": "repetición", "defer": "aplazar"}),
    ("security_events", {"severity": "importancia", "incident": "problema de seguridad"}),
    ("regional_maps", {"approximate": "aproximado", "geolocation": "zona estimada"}),
    ("backups", {"snapshot": "copia", "restore": "recuperar"}),
    ("ai_learning_data", {"dataset": "conjunto de datos", "training": "aprendizaje"}),
    ("rich_commands", {"entity": "elemento", "fallback": "respuesta alternativa"}),
    ("hub_notifications", {"priority": "importancia", "digest": "resumen"}),
    ("cookie_policies", {"consent": "permiso", "optional": "no obligatorio"}),
    ("wayback_history", {"snapshot": "copia archivada", "capture": "guardar una copia"}),
)

_TOKEN = re.compile(r"https://\S+|@[A-Za-z0-9_]{5,32}|#[A-Za-z0-9_-]+|\b(?:ID|id)[-_:]?[A-Za-z0-9_-]+\b")


def _replace_jargon(text: str, glossary: dict[str, str]) -> tuple[str, tuple[str, ...]]:
    protected: list[str] = []

    def protect(match: re.Match[str]) -> str:
        protected.append(match.group(0))
        return f"TOKENPROTECTED{len(protected) - 1}TOKEN"

    result = _TOKEN.sub(protect, text)
    used = []
    for jargon, simple in glossary.items():
        pattern = re.compile(rf"\b{re.escape(jargon)}\b", re.IGNORECASE)
        if pattern.search(result):
            result = pattern.sub(simple, result)
            used.append(jargon)
    for index, token in enumerate(protected):
        result = result.replace(f"TOKENPROTECTED{index}TOKEN", token)
    return result, tuple(used)


def _short_sentences(text: str, max_words: int) -> tuple[str, ...]:
    pieces = [piece.strip(" \t\r\n-•") for piece in re.split(r"(?<=[.!?;])\s+|\n+", text) if piece.strip()]
    output = []
    for piece in pieces:
        words = piece.split()
        for start in range(0, len(words), max_words):
            chunk = " ".join(words[start : start + max_words]).strip()
            if chunk and chunk[-1] not in ".!?":
                chunk += "."
            if chunk:
                output.append(chunk)
    return tuple(output)


def _easy_read(
    feature_id: str,
    resource: str,
    glossary: dict[str, str],
    content: dict[str, Any],
    max_words: int,
) -> dict[str, Any]:
    if not isinstance(content, dict):
        raise ValueError("content debe ser un objeto")
    if not isinstance(max_words, int) or isinstance(max_words, bool) or not 8 <= max_words <= 24:
        raise ValueError("max_words debe estar entre 8 y 24")
    title = _text(content.get("title"), "title", 200)
    summary = _text(content.get("summary"), "summary", 5000)
    steps = content.get("steps", [])
    warnings = content.get("warnings", [])
    if not isinstance(steps, list) or len(steps) > 30 or not isinstance(warnings, list) or len(warnings) > 20:
        raise ValueError("steps o warnings no válidos")
    raw_sections = [("summary", summary)]
    raw_sections.extend(("step", _text(item, "step", 1000)) for item in steps)
    raw_sections.extend(("warning", _text(item, "warning", 1000)) for item in warnings)
    sentences = []
    jargon_used = set()
    for kind, raw in raw_sections:
        replaced, used = _replace_jargon(raw, glossary)
        jargon_used.update(used)
        for sentence in _short_sentences(replaced, max_words):
            sentences.append({"kind": kind, "text": sentence})
    plain_lines = [title]
    plain_lines.extend(
        ("Atención: " if row["kind"] == "warning" else "• ") + row["text"]
        for row in sentences
    )
    return {
        "feature_id": feature_id,
        "resource": resource,
        "title": title,
        "sentences": tuple(sentences),
        "sentence_count": len(sentences),
        "max_words_per_sentence": max_words,
        "glossary_terms_used": tuple(sorted(jargon_used)),
        "plain_text": "\n".join(plain_lines),
        "identifiers_preserved": True,
        "reading_level": "easy",
        "executed": False,
    }


def _easy_api(index: int) -> Callable[..., dict[str, Any]]:
    resource, glossary = _EASY_SPECS[index]

    def operation(content: dict[str, Any], *, max_words: int = 16) -> dict[str, Any]:
        return _easy_read(IDS[3 + index], resource, glossary, content, max_words)

    operation.__name__ = f"easy_read_{resource}"
    operation.__doc__ = f"Transform structured {resource} content into deterministic easy reading."
    return operation


easy_read_administrative_sessions = _easy_api(0)
easy_read_community_profiles = _easy_api(1)
easy_read_telegram_communities = _easy_api(2)
easy_read_house_ads = _easy_api(3)
easy_read_voice_notes = _easy_api(4)
easy_read_suspicious_files = _easy_api(5)
easy_read_captcha_decisions = _easy_api(6)
easy_read_managed_bots = _easy_api(7)
easy_read_recurring_reminders = _easy_api(8)
easy_read_security_events = _easy_api(9)
easy_read_regional_maps = _easy_api(10)
easy_read_backups = _easy_api(11)
easy_read_ai_learning_data = _easy_api(12)
easy_read_rich_commands = _easy_api(13)
easy_read_hub_notifications = _easy_api(14)
easy_read_cookie_policies = _easy_api(15)
easy_read_wayback_history = _easy_api(16)


LOCALIZATION_APIS = (localize_master_panel, localize_channel_directory, localize_external_link)
EASY_READ_APIS = (
    easy_read_administrative_sessions, easy_read_community_profiles,
    easy_read_telegram_communities, easy_read_house_ads, easy_read_voice_notes,
    easy_read_suspicious_files, easy_read_captcha_decisions, easy_read_managed_bots,
    easy_read_recurring_reminders, easy_read_security_events, easy_read_regional_maps,
    easy_read_backups, easy_read_ai_learning_data, easy_read_rich_commands,
    easy_read_hub_notifications, easy_read_cookie_policies, easy_read_wayback_history,
)
ALL_APIS = LOCALIZATION_APIS + EASY_READ_APIS

assert len(IDS) == len(ALL_APIS) == 20
assert len({operation.__name__ for operation in ALL_APIS}) == 20

"""Closed-grammar voice navigation and privacy-safe grouped notifications."""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
import hashlib
import re
import unicodedata
from typing import Any, Callable

from resource_incident_temporal_engines import _redact, _utc_datetime


IDS = tuple(
    f"future-{number}"
    for number in (
        5102, 5105, 5108, 5111, 5114, 5117, 5120, 5123, 5126, 5129,
        5132, 5135, 5138, 5141, 5144, 5147, 5150, 5153, 5156, 5159,
    )
)

_VOICE_SPECS = (
    ("temporary_roles", frozenset({"list", "search", "create", "edit", "revoke", "back", "help"}), frozenset({"revoke"})),
    ("managed_groups", frozenset({"list", "search", "open", "edit", "leave", "back", "help"}), frozenset({"leave"})),
    ("scheduled_messages", frozenset({"list", "search", "create", "edit", "cancel", "back", "help"}), frozenset({"cancel"})),
    ("rss_feeds", frozenset({"list", "search", "create", "edit", "disable", "back", "help"}), frozenset({"disable"})),
    ("telegram_videos", frozenset({"list", "search", "open", "quarantine", "release", "back", "help"}), frozenset({"quarantine", "release"})),
    ("blocklists", frozenset({"list", "search", "create", "edit", "disable", "back", "help"}), frozenset({"disable"})),
    ("required_subscriptions", frozenset({"list", "search", "create", "edit", "disable", "back", "help"}), frozenset({"disable"})),
    ("signed_webhooks", frozenset({"list", "search", "create", "edit", "disable", "back", "help"}), frozenset({"disable"})),
    ("quiet_hours", frozenset({"list", "open", "edit", "disable", "back", "help"}), frozenset({"disable"})),
    ("correlated_incidents", frozenset({"list", "search", "open", "resolve", "back", "help"}), frozenset({"resolve"})),
    ("accessible_preferences", frozenset({"list", "open", "edit", "reset", "back", "help"}), frozenset({"reset"})),
    ("integration_secrets", frozenset({"list", "search", "rotate", "revoke", "back", "help"}), frozenset({"rotate", "revoke"})),
    ("contextual_responses", frozenset({"list", "search", "open", "edit", "disable", "back", "help"}), frozenset({"disable"})),
    ("miniapp_menus", frozenset({"list", "search", "open", "edit", "back", "help"}), frozenset()),
    ("bot_statistics", frozenset({"list", "search", "open", "refresh", "back", "help"}), frozenset()),
    ("advertising_preferences", frozenset({"list", "open", "edit", "reset", "back", "help"}), frozenset({"reset"})),
    ("processing_queues", frozenset({"list", "search", "open", "pause", "resume", "cancel", "back", "help"}), frozenset({"pause", "cancel"})),
)

_ALIASES = {
    "es": {
        "listar": "list", "lista": "list", "buscar": "search", "abrir": "open",
        "crear": "create", "editar": "edit", "revocar": "revoke", "salir": "leave",
        "cancelar": "cancel", "desactivar": "disable", "poner en cuarentena": "quarantine",
        "liberar": "release", "resolver": "resolve", "restablecer": "reset",
        "rotar": "rotate", "actualizar": "refresh", "pausar": "pause",
        "reanudar": "resume", "atras": "back", "ayuda": "help",
    },
    "en": {
        "list": "list", "search": "search", "open": "open", "create": "create",
        "edit": "edit", "revoke": "revoke", "leave": "leave", "cancel": "cancel",
        "disable": "disable", "quarantine": "quarantine", "release": "release",
        "resolve": "resolve", "reset": "reset", "rotate": "rotate", "refresh": "refresh",
        "pause": "pause", "resume": "resume", "back": "back", "help": "help",
    },
}


def _normalise_transcript(value: Any) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 300 or "\n" in value or "\r" in value:
        raise ValueError("transcript no válido")
    normalised = unicodedata.normalize("NFKD", value.casefold())
    return " ".join("".join(char for char in normalised if not unicodedata.combining(char)).split())


def _voice_plan(
    feature_id: str,
    resource: str,
    allowed: frozenset[str],
    destructive: frozenset[str],
    transcript: str,
    locale: str,
) -> dict[str, Any]:
    if locale not in _ALIASES:
        raise ValueError("locale debe ser es o en")
    clean = _normalise_transcript(transcript)
    matched_alias = None
    action = None
    for alias in sorted(_ALIASES[locale], key=len, reverse=True):
        if clean == alias or clean.startswith(alias + " "):
            matched_alias = alias
            action = _ALIASES[locale][alias]
            break
    if action is None or action not in allowed:
        return {
            "feature_id": feature_id, "resource": resource, "matched": False,
            "intent": None, "query": "", "requires_confirmation": False,
            "confirmation_token": None, "executed": False,
        }
    query = clean[len(matched_alias):].strip()
    if action in {"search", "open", "edit", "revoke", "cancel", "disable", "resolve", "rotate", "pause", "resume", "quarantine", "release"} and not query:
        raise ValueError("La acción requiere un objetivo explícito")
    requires_confirmation = action in destructive
    token = None
    if requires_confirmation:
        token = hashlib.sha256(f"{feature_id}:{resource}:{action}:{query}".encode("utf-8")).hexdigest()[:24]
    return {
        "feature_id": feature_id,
        "resource": resource,
        "matched": True,
        "intent": action,
        "query": query,
        "requires_confirmation": requires_confirmation,
        "confirmation_token": token,
        "available_intents": tuple(sorted(allowed)),
        "executed": False,
    }


def _voice_api(index: int) -> Callable[..., dict[str, Any]]:
    resource, allowed, destructive = _VOICE_SPECS[index]

    def operation(transcript: str, *, locale: str = "es") -> dict[str, Any]:
        return _voice_plan(IDS[index], resource, allowed, destructive, transcript, locale)

    operation.__name__ = f"navigate_{resource}_by_voice"
    operation.__doc__ = f"Plan closed-grammar voice navigation for {resource}; never execute it."
    return operation


navigate_temporary_roles_by_voice = _voice_api(0)
navigate_managed_groups_by_voice = _voice_api(1)
navigate_scheduled_messages_by_voice = _voice_api(2)
navigate_rss_feeds_by_voice = _voice_api(3)
navigate_telegram_videos_by_voice = _voice_api(4)
navigate_blocklists_by_voice = _voice_api(5)
navigate_required_subscriptions_by_voice = _voice_api(6)
navigate_signed_webhooks_by_voice = _voice_api(7)
navigate_quiet_hours_by_voice = _voice_api(8)
navigate_correlated_incidents_by_voice = _voice_api(9)
navigate_accessible_preferences_by_voice = _voice_api(10)
navigate_integration_secrets_by_voice = _voice_api(11)
navigate_contextual_responses_by_voice = _voice_api(12)
navigate_miniapp_menus_by_voice = _voice_api(13)
navigate_bot_statistics_by_voice = _voice_api(14)
navigate_advertising_preferences_by_voice = _voice_api(15)
navigate_processing_queues_by_voice = _voice_api(16)


_GROUP_SPECS = (
    ("creator_accounts", "account_id", frozenset({"login", "role_change", "freeze", "security"})),
    ("associated_channels", "channel_id", frozenset({"associate", "permission", "health", "publication"})),
    ("community_campaigns", "campaign_id", frozenset({"publish", "impression", "click", "moderation"})),
)


def _group_notifications(
    feature_id: str,
    resource: str,
    entity_field: str,
    allowed_kinds: frozenset[str],
    events: list[dict[str, Any]],
    window_minutes: int,
    max_items: int,
) -> dict[str, Any]:
    if not isinstance(events, list) or len(events) > 5000:
        raise ValueError("events debe ser una lista acotada")
    if not isinstance(window_minutes, int) or isinstance(window_minutes, bool) or not 1 <= window_minutes <= 1440:
        raise ValueError("window_minutes no válido")
    if not isinstance(max_items, int) or isinstance(max_items, bool) or not 1 <= max_items <= 100:
        raise ValueError("max_items no válido")
    unique = {}
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("evento no válido")
        event_id = event.get("id")
        entity_id = event.get(entity_field)
        kind = event.get("kind")
        severity = event.get("severity")
        if not isinstance(event_id, str) or not event_id or len(event_id) > 128:
            raise ValueError("id de evento no válido")
        if not isinstance(entity_id, str) or not entity_id or len(entity_id) > 128:
            raise ValueError(f"{entity_field} no válido")
        if kind not in allowed_kinds or severity not in {"info", "warning", "high", "critical"}:
            raise ValueError("kind o severity no válido")
        occurred_at = _utc_datetime(event.get("occurred_at"), "occurred_at")
        title = event.get("title")
        if not isinstance(title, str) or not title.strip() or len(title) > 300:
            raise ValueError("title no válido")
        unique.setdefault(event_id, {
            "id": event_id, "entity_id": entity_id, "kind": kind, "severity": severity,
            "occurred_at": occurred_at, "title": title.strip(), "details": _redact(event.get("details", {})),
        })
    grouped = defaultdict(list)
    epoch = _utc_datetime("1970-01-01T00:00:00Z", "epoch")
    for event in unique.values():
        bucket = int((event["occurred_at"] - epoch).total_seconds() // (window_minutes * 60))
        grouped[(event["entity_id"], event["kind"], bucket)].append(event)
    notifications = []
    severity_rank = {"info": 0, "warning": 1, "high": 2, "critical": 3}
    for (entity_id, kind, _), rows in sorted(grouped.items()):
        rows.sort(key=lambda row: (row["occurred_at"], row["id"]))
        visible = rows[:max_items]
        severity = max((row["severity"] for row in rows), key=severity_rank.get)
        notifications.append({
            "entity_id": entity_id, "kind": kind, "severity": severity,
            "event_ids": tuple(row["id"] for row in visible),
            "titles": tuple(row["title"] for row in visible),
            "count": len(rows), "overflow": max(0, len(rows) - len(visible)),
            "start_at": rows[0]["occurred_at"].isoformat().replace("+00:00", "Z"),
            "end_at": rows[-1]["occurred_at"].isoformat().replace("+00:00", "Z"),
        })
    return {
        "feature_id": feature_id, "resource": resource, "input_count": len(events),
        "unique_count": len(unique), "notifications": tuple(notifications),
        "notification_count": len(notifications), "delivery_requested": False,
        "executed": False, "auditable": True,
    }


def _group_api(index: int) -> Callable[..., dict[str, Any]]:
    resource, entity_field, kinds = _GROUP_SPECS[index]

    def operation(events: list[dict[str, Any]], *, window_minutes: int = 30, max_items: int = 20) -> dict[str, Any]:
        return _group_notifications(IDS[17 + index], resource, entity_field, kinds, events, window_minutes, max_items)

    operation.__name__ = f"group_{resource}_notifications"
    operation.__doc__ = f"Build deduplicated, bounded grouped notifications for {resource}."
    return operation


group_creator_accounts_notifications = _group_api(0)
group_associated_channels_notifications = _group_api(1)
group_community_campaigns_notifications = _group_api(2)


VOICE_APIS = (
    navigate_temporary_roles_by_voice, navigate_managed_groups_by_voice,
    navigate_scheduled_messages_by_voice, navigate_rss_feeds_by_voice,
    navigate_telegram_videos_by_voice, navigate_blocklists_by_voice,
    navigate_required_subscriptions_by_voice, navigate_signed_webhooks_by_voice,
    navigate_quiet_hours_by_voice, navigate_correlated_incidents_by_voice,
    navigate_accessible_preferences_by_voice, navigate_integration_secrets_by_voice,
    navigate_contextual_responses_by_voice, navigate_miniapp_menus_by_voice,
    navigate_bot_statistics_by_voice, navigate_advertising_preferences_by_voice,
    navigate_processing_queues_by_voice,
)
GROUP_APIS = (
    group_creator_accounts_notifications, group_associated_channels_notifications,
    group_community_campaigns_notifications,
)
ALL_APIS = VOICE_APIS + GROUP_APIS

assert len(IDS) == len(ALL_APIS) == 20
assert len({operation.__name__ for operation in ALL_APIS}) == 20

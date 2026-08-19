"""Grouped notification extensions and capacity-aware smart routing."""

from __future__ import annotations

import html
from typing import Any, Callable

from resource_voice_grouped_notification_engines import _group_notifications
from resource_security_contracts import authorize, bounded_json, redact_sensitive, safe_identifier


IDS = tuple(
    f"future-{number}"
    for number in (
        5162, 5165, 5168, 5171, 5174, 5177, 5180, 5183, 5186, 5189,
        5192, 5195, 5198, 5201, 5204, 5207, 5210, 5213, 5216, 5219,
        5222, 5225, 5228, 5231, 5234, 5237, 5240, 5243, 5246, 5249,
    )
)


_GROUP_SPECS = (
    ("editorial_articles", "article_id", frozenset({"draft", "publish", "update", "source"})),
    ("moderated_images", "media_hash", frozenset({"detect", "quarantine", "release", "appeal"})),
    ("user_appeals", "appeal_id", frozenset({"submit", "review", "evidence", "resolve"})),
    ("mtproto_proxies", "proxy_id", frozenset({"health", "traffic", "rotation", "incident"})),
    ("persistent_tasks", "task_id", frozenset({"due", "run", "fail", "complete"})),
    ("moderation_rules", "rule_id", frozenset({"match", "change", "disable", "enable"})),
    ("language_metrics", "language_code", frozenset({"sample", "anomaly", "map_update"})),
    ("community_translations", "translation_id", frozenset({"submit", "vote", "approve", "reject"})),
    ("personal_consents", "subject_id", frozenset({"grant", "revoke", "expire"})),
    ("telegram_reactions", "message_id", frozenset({"add", "remove", "spike"})),
    ("master_panels", "panel_id", frozenset({"open", "error", "change"})),
    ("channel_directories", "directory_id", frozenset({"add", "remove", "verify"})),
    ("external_links", "normalized_url", frozenset({"observed", "redirect", "reputation", "block"})),
)


def _group_api(index: int) -> Callable[..., dict[str, Any]]:
    resource, entity_field, kinds = _GROUP_SPECS[index]

    def operation(events: list[dict[str, Any]], *, actor: dict[str, Any], window_minutes: int = 30, max_items: int = 20) -> dict[str, Any]:
        actor_id = authorize(actor, f"notifications:group:{resource}")
        bounded_json(events, maximum_bytes=262144)
        safe_events = []
        for event in events:
            if isinstance(event, dict):
                safe_identifier(event.get("id"), "event.id")
                title = event.get("title")
                if isinstance(title, str) and any(ord(char) < 32 and char not in "\t\n\r" for char in title):
                    raise ValueError("title contiene caracteres de control")
                safe_events.append({**event, "title": html.escape(title, quote=True) if isinstance(title, str) else title,
                                    "details": redact_sensitive(event.get("details", {}))})
            else:
                safe_events.append(event)
        result = _group_notifications(IDS[index], resource, entity_field, kinds, safe_events, window_minutes, max_items)
        return {**result, "planned_by": actor_id, "render_mode": "escaped_plain_text"}

    operation.__name__ = f"group_{resource}_notifications"
    operation.__doc__ = f"Build bounded and deduplicated notification groups for {resource}."
    return operation


group_editorial_articles_notifications = _group_api(0)
group_moderated_images_notifications = _group_api(1)
group_user_appeals_notifications = _group_api(2)
group_mtproto_proxies_notifications = _group_api(3)
group_persistent_tasks_notifications = _group_api(4)
group_moderation_rules_notifications = _group_api(5)
group_language_metrics_notifications = _group_api(6)
group_community_translations_notifications = _group_api(7)
group_personal_consents_notifications = _group_api(8)
group_telegram_reactions_notifications = _group_api(9)
group_master_panels_notifications = _group_api(10)
group_channel_directories_notifications = _group_api(11)
group_external_links_notifications = _group_api(12)


_CLEARANCE = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}
_ROUTE_SPECS = (
    ("administrative_sessions", "session", "session_security", "confidential"),
    ("community_profiles", "profile", "privacy_review", "confidential"),
    ("telegram_communities", "community", "community_admin", "internal"),
    ("house_ads", "campaign", "campaign_manager", "public"),
    ("voice_notes", "media", "media_moderator", "confidential"),
    ("suspicious_files", "file", "malware_analyst", "restricted"),
    ("captcha_decisions", "decision", "security_admin", "confidential"),
    ("managed_bots", "bot", "bot_operator", "internal"),
    ("recurring_reminders", "automation", "automation_owner", "confidential"),
    ("security_events", "incident", "security_admin", "restricted"),
    ("regional_maps", "geo", "privacy_admin", "restricted"),
    ("backups", "backup", "backup_operator", "restricted"),
    ("ai_learning_data", "dataset", "ai_reviewer", "restricted"),
    ("rich_commands", "command", "command_editor", "internal"),
    ("hub_notifications", "notification", "support", "internal"),
    ("cookie_policies", "policy", "privacy_admin", "internal"),
    ("wayback_history", "archive", "archivist", "internal"),
)


def _smart_route(
    feature_id: str,
    resource: str,
    expected_kind: str,
    required_skill: str,
    required_clearance: str,
    item: dict[str, Any],
    destinations: list[dict[str, Any]],
    actor: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(item, dict) or not isinstance(destinations, list) or len(destinations) > 500:
        raise ValueError("item o destinations no válidos")
    actor_id = authorize(actor, f"route:plan:{resource}")
    bounded_json(item, maximum_bytes=32768)
    bounded_json(destinations, maximum_bytes=262144)
    item_id = safe_identifier(item.get("id"), "item.id")
    if item.get("kind") != expected_kind:
        raise ValueError("id o kind del elemento no válido")
    severity = item.get("severity", "info")
    if severity not in {"info", "warning", "high", "critical"}:
        raise ValueError("severity no válida")
    region = item.get("region")
    if region is not None and (not isinstance(region, str) or len(region) > 32):
        raise ValueError("region no válida")
    candidates = []
    seen = set()
    for destination in destinations:
        if not isinstance(destination, dict):
            raise ValueError("destino no válido")
        destination_id = safe_identifier(destination.get("id"), "destination.id")
        skills = destination.get("skills")
        regions = destination.get("regions", ["*"])
        clearance = destination.get("clearance")
        capacity = destination.get("capacity")
        load = destination.get("load")
        active = destination.get("active", True)
        if destination_id in seen:
            raise ValueError("id de destino duplicado")
        seen.add(destination_id)
        if not isinstance(skills, list) or len(skills) > 100 or not all(isinstance(skill, str) and len(skill) <= 80 for skill in skills):
            raise ValueError("skills no válido")
        if not isinstance(regions, list) or len(regions) > 250 or not all(isinstance(value, str) and len(value) <= 32 for value in regions):
            raise ValueError("regions no válido")
        if clearance not in _CLEARANCE:
            raise ValueError("clearance no válido")
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1:
            raise ValueError("capacity no válida")
        if not isinstance(load, int) or isinstance(load, bool) or not 0 <= load <= capacity:
            raise ValueError("load no válido")
        reasons = []
        eligible = bool(active)
        if required_skill not in skills:
            eligible = False; reasons.append("missing_skill")
        if _CLEARANCE[clearance] < _CLEARANCE[required_clearance]:
            eligible = False; reasons.append("insufficient_clearance")
        if load >= capacity:
            eligible = False; reasons.append("at_capacity")
        if region and "*" not in regions and region not in regions:
            eligible = False; reasons.append("region_mismatch")
        if not active:
            reasons.append("inactive")
        free_ratio = (capacity - load) / capacity
        region_bonus = 0.15 if region and region in regions else 0.05 if "*" in regions else 0
        severity_bonus = 0.1 if severity in {"high", "critical"} and _CLEARANCE[clearance] >= 3 else 0
        score = round(free_ratio + region_bonus + severity_bonus, 4) if eligible else 0.0
        candidates.append({"id": destination_id, "eligible": eligible, "score": score, "reasons": tuple(reasons), "free_slots": capacity - load})
    candidates.sort(key=lambda row: (-row["score"], row["id"]))
    selected = next((row["id"] for row in candidates if row["eligible"]), None)
    return {
        "feature_id": feature_id, "resource": resource, "item_id": item_id,
        "selected_destination": selected, "candidates": tuple(candidates),
        "routable": selected is not None, "requires_manual_route": selected is None,
        "planned_by": actor_id, "dispatched": False, "executed": False, "auditable": True,
    }


def _route_api(index: int) -> Callable[..., dict[str, Any]]:
    resource, kind, skill, clearance = _ROUTE_SPECS[index]

    def operation(item: dict[str, Any], destinations: list[dict[str, Any]], *, actor: dict[str, Any]) -> dict[str, Any]:
        return _smart_route(IDS[13 + index], resource, kind, skill, clearance, item, destinations, actor)

    operation.__name__ = f"route_{resource}_intelligently"
    operation.__doc__ = f"Select an eligible destination for {resource} without dispatching it."
    return operation


route_administrative_sessions_intelligently = _route_api(0)
route_community_profiles_intelligently = _route_api(1)
route_telegram_communities_intelligently = _route_api(2)
route_house_ads_intelligently = _route_api(3)
route_voice_notes_intelligently = _route_api(4)
route_suspicious_files_intelligently = _route_api(5)
route_captcha_decisions_intelligently = _route_api(6)
route_managed_bots_intelligently = _route_api(7)
route_recurring_reminders_intelligently = _route_api(8)
route_security_events_intelligently = _route_api(9)
route_regional_maps_intelligently = _route_api(10)
route_backups_intelligently = _route_api(11)
route_ai_learning_data_intelligently = _route_api(12)
route_rich_commands_intelligently = _route_api(13)
route_hub_notifications_intelligently = _route_api(14)
route_cookie_policies_intelligently = _route_api(15)
route_wayback_history_intelligently = _route_api(16)


GROUP_APIS = (
    group_editorial_articles_notifications, group_moderated_images_notifications,
    group_user_appeals_notifications, group_mtproto_proxies_notifications,
    group_persistent_tasks_notifications, group_moderation_rules_notifications,
    group_language_metrics_notifications, group_community_translations_notifications,
    group_personal_consents_notifications, group_telegram_reactions_notifications,
    group_master_panels_notifications, group_channel_directories_notifications,
    group_external_links_notifications,
)
ROUTE_APIS = (
    route_administrative_sessions_intelligently, route_community_profiles_intelligently,
    route_telegram_communities_intelligently, route_house_ads_intelligently,
    route_voice_notes_intelligently, route_suspicious_files_intelligently,
    route_captcha_decisions_intelligently, route_managed_bots_intelligently,
    route_recurring_reminders_intelligently, route_security_events_intelligently,
    route_regional_maps_intelligently, route_backups_intelligently,
    route_ai_learning_data_intelligently, route_rich_commands_intelligently,
    route_hub_notifications_intelligently, route_cookie_policies_intelligently,
    route_wayback_history_intelligently,
)
ALL_APIS = GROUP_APIS + ROUTE_APIS

assert len(IDS) == len(ALL_APIS) == 30
assert len({operation.__name__ for operation in ALL_APIS}) == 30

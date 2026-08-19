"""Version-aware reconcilable caches and reversible resource rotation plans."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

from resource_incident_temporal_engines import _redact, _utc_datetime
from resource_security_contracts import authorize, bounded_json, safe_identifier


IDS = tuple(
    f"future-{number}"
    for number in (
        5252, 5255, 5258, 5261, 5264, 5267, 5270, 5273, 5276, 5279,
        5282, 5285, 5288, 5291, 5294, 5297, 5300, 5303, 5306, 5309,
        5312, 5315, 5318, 5321, 5324, 5327, 5330, 5333, 5336, 5339,
    )
)


_CACHE_SPECS = (
    ("temporary_roles", frozenset({"role", "expires_at", "scope", "enabled"}), 60),
    ("managed_groups", frozenset({"title", "config", "bot_ids", "status"}), 60),
    ("scheduled_messages", frozenset({"text", "send_at", "targets", "status"}), 30),
    ("rss_feeds", frozenset({"url", "filters", "template", "enabled"}), 120),
    ("telegram_videos", frozenset({"caption", "status", "file_unique_id", "duration"}), 300),
    ("blocklists", frozenset({"enabled", "entries_hash", "source", "count"}), 60),
    ("required_subscriptions", frozenset({"channels", "enabled", "grace_minutes"}), 60),
    ("signed_webhooks", frozenset({"url", "events", "enabled", "secret_version"}), 30),
    ("quiet_hours", frozenset({"timezone", "start", "end", "exceptions", "enabled"}), 60),
    ("correlated_incidents", frozenset({"status", "links", "assignee", "severity"}), 30),
    ("accessible_preferences", frozenset({"language", "reading_level", "output_channel"}), 300),
    ("integration_secrets", frozenset({"secret_version", "rotated_at", "expires_at", "status"}), 30),
    ("contextual_responses", frozenset({"intent", "template", "enabled", "confidence"}), 120),
    ("miniapp_menus", frozenset({"items", "role", "visibility", "version"}), 120),
    ("bot_statistics", frozenset({"bot_id", "period", "counts", "updated_at"}), 30),
    ("advertising_preferences", frozenset({"consent", "placements", "frequency", "updated_at"}), 300),
    ("processing_queues", frozenset({"priority", "capacity", "paused", "retry_limit"}), 10),
)


def cache_etag(value: dict[str, Any]) -> str:
    if not isinstance(value, dict):
        raise ValueError("value debe ser un objeto")
    bounded_json(value, maximum_bytes=65536, reject_secrets=True)
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _cache_entry(raw: dict[str, Any] | None, allowed: frozenset[str], label: str) -> dict[str, Any] | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError(f"{label} debe ser un objeto")
    bounded_json(raw, maximum_bytes=98304, reject_secrets=True)
    entry_id = safe_identifier(raw.get("id"), f"{label}.id")
    version = raw.get("version")
    tombstone = raw.get("tombstone", False)
    value = raw.get("value", {})
    if not isinstance(version, int) or isinstance(version, bool) or version < 0:
        raise ValueError(f"version de {label} no válida")
    if not isinstance(tombstone, bool) or not isinstance(value, dict):
        raise ValueError(f"tombstone/value de {label} no válido")
    if tombstone and value:
        raise ValueError("Un tombstone no puede contener value")
    unknown = set(value) - allowed
    if unknown:
        raise ValueError(f"Campos no cacheables: {sorted(unknown)}")
    updated_at = _utc_datetime(raw.get("updated_at"), f"{label}.updated_at")
    expected = cache_etag(value)
    etag = raw.get("etag")
    if etag != expected:
        raise ValueError(f"etag de {label} no coincide con value")
    return {"id": entry_id, "version": version, "tombstone": tombstone, "value": value, "updated_at": updated_at, "etag": etag}


def _reconcile_cache(
    feature_id: str,
    resource: str,
    allowed: frozenset[str],
    default_ttl: int,
    cached: dict[str, Any] | None,
    source: dict[str, Any],
    strategy: str,
    ttl_seconds: int | None,
    actor: dict[str, Any],
) -> dict[str, Any]:
    actor_id = authorize(actor, f"cache:reconcile:{resource}")
    if strategy not in {"manual", "source_wins", "cache_wins"}:
        raise ValueError("strategy no válida")
    ttl = default_ttl if ttl_seconds is None else ttl_seconds
    if not isinstance(ttl, int) or isinstance(ttl, bool) or not 1 <= ttl <= 86400:
        raise ValueError("ttl_seconds no válido")
    local = _cache_entry(cached, allowed, "cached")
    remote = _cache_entry(source, allowed, "source")
    if local is not None and local["id"] != remote["id"]:
        raise ValueError("cached y source pertenecen a entidades distintas")
    conflict = False
    if local is None:
        action = "delete" if remote["tombstone"] else "fill"
        selected = remote
    elif remote["version"] > local["version"]:
        action = "delete" if remote["tombstone"] else "refresh"
        selected = remote
    elif remote["version"] == local["version"] and remote["etag"] == local["etag"] and remote["tombstone"] == local["tombstone"]:
        action = "hit"
        selected = local
    else:
        conflict = True
        if strategy == "source_wins":
            action, selected = ("delete" if remote["tombstone"] else "refresh"), remote
        elif strategy == "cache_wins":
            action, selected = "retain_and_publish", local
        else:
            action, selected = "manual_review", None
    return {
        "feature_id": feature_id, "resource": resource, "entity_id": remote["id"],
        "action": action, "conflict": conflict, "strategy": strategy,
        "selected_version": selected["version"] if selected else None,
        "selected_value": _redact(selected["value"]) if selected and not selected["tombstone"] else None,
        "selected_etag": selected["etag"] if selected else None, "ttl_seconds": ttl,
        "mutation_planned": action not in {"hit", "manual_review"},
        "planned_by": actor_id, "render_mode": "data_only", "applied": False, "auditable": True,
    }


def _cache_api(index: int) -> Callable[..., dict[str, Any]]:
    resource, fields, ttl = _CACHE_SPECS[index]

    def operation(cached: dict[str, Any] | None, source: dict[str, Any], *, actor: dict[str, Any], strategy: str = "manual", ttl_seconds: int | None = None) -> dict[str, Any]:
        return _reconcile_cache(IDS[index], resource, fields, ttl, cached, source, strategy, ttl_seconds, actor)

    operation.__name__ = f"reconcile_{resource}_cache"
    operation.__doc__ = f"Reconcile a versioned {resource} cache without applying mutations."
    return operation


reconcile_temporary_roles_cache = _cache_api(0)
reconcile_managed_groups_cache = _cache_api(1)
reconcile_scheduled_messages_cache = _cache_api(2)
reconcile_rss_feeds_cache = _cache_api(3)
reconcile_telegram_videos_cache = _cache_api(4)
reconcile_blocklists_cache = _cache_api(5)
reconcile_required_subscriptions_cache = _cache_api(6)
reconcile_signed_webhooks_cache = _cache_api(7)
reconcile_quiet_hours_cache = _cache_api(8)
reconcile_correlated_incidents_cache = _cache_api(9)
reconcile_accessible_preferences_cache = _cache_api(10)
reconcile_integration_secrets_cache = _cache_api(11)
reconcile_contextual_responses_cache = _cache_api(12)
reconcile_miniapp_menus_cache = _cache_api(13)
reconcile_bot_statistics_cache = _cache_api(14)
reconcile_advertising_preferences_cache = _cache_api(15)
reconcile_processing_queues_cache = _cache_api(16)


_ROTATION_SPECS = (
    ("creator_accounts", "account_id", 60),
    ("associated_channels", "channel_id", 30),
    ("community_campaigns", "campaign_id", 15),
    ("editorial_articles", "article_id", 5),
    ("moderated_images", "media_hash", 10),
    ("user_appeals", "appeal_id", 30),
    ("mtproto_proxies", "proxy_id", 10),
    ("persistent_tasks", "task_id", 5),
    ("moderation_rules", "rule_id", 30),
    ("language_metrics", "language_code", 60),
    ("community_translations", "translation_id", 30),
    ("personal_consents", "subject_id", 60),
    ("telegram_reactions", "message_id", 5),
)


def _rotation_item(raw: dict[str, Any], artifact_field: str, expected_state: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("Elemento de rotación no válido")
    bounded_json(raw, maximum_bytes=65536, reject_secrets=True)
    rotation_key = safe_identifier(raw.get("rotation_key"), "rotation_key")
    artifact_id = safe_identifier(raw.get(artifact_field), artifact_field, 256)
    version = raw.get("version")
    dependencies = raw.get("dependencies", [])
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise ValueError("version no válida")
    if raw.get("state") != expected_state:
        raise ValueError(f"state debe ser {expected_state}")
    if not isinstance(dependencies, list) or len(dependencies) > 100:
        raise ValueError("dependencies no válidas")
    normalised_dependencies = []
    for dependency in dependencies:
        if not isinstance(dependency, dict) or set(dependency) != {"id", "healthy"}:
            raise ValueError("dependency no válida")
        safe_identifier(dependency.get("id"), "dependency.id")
        if not isinstance(dependency["healthy"], bool):
            raise ValueError("dependency no válida")
        normalised_dependencies.append(dict(dependency))
    return {"rotation_key": rotation_key, "artifact_id": artifact_id, "version": version, "dependencies": normalised_dependencies}


def _safe_rotation(
    feature_id: str,
    resource: str,
    artifact_field: str,
    minimum_grace: int,
    current: dict[str, Any],
    replacement: dict[str, Any],
    policy: dict[str, Any],
    actor: dict[str, Any],
) -> dict[str, Any]:
    actor_id = authorize(actor, f"rotation:plan:{resource}")
    old = _rotation_item(current, artifact_field, "active")
    new = _rotation_item(replacement, artifact_field, "candidate")
    if old["rotation_key"] != new["rotation_key"] or old["artifact_id"] == new["artifact_id"]:
        raise ValueError("La sustitución debe compartir rotation_key y usar otro artefacto")
    if new["version"] <= old["version"]:
        raise ValueError("La versión de sustitución debe ser posterior")
    if not isinstance(policy, dict):
        raise ValueError("policy debe ser un objeto")
    bounded_json(policy, maximum_bytes=32768, reject_secrets=True)
    grace = policy.get("grace_minutes")
    batch_size = policy.get("batch_size", 1)
    health_checks = policy.get("health_checks")
    if not isinstance(grace, int) or isinstance(grace, bool) or grace < minimum_grace or grace > 10080:
        raise ValueError(f"grace_minutes debe ser al menos {minimum_grace}")
    if not isinstance(batch_size, int) or isinstance(batch_size, bool) or not 1 <= batch_size <= 100:
        raise ValueError("batch_size no válido")
    if not isinstance(health_checks, list) or not health_checks or len(health_checks) > 20 or not all(isinstance(check, str) and check and len(check) <= 80 and ".." not in check and "/" not in check and "\\" not in check for check in health_checks):
        raise ValueError("health_checks no válido")
    unhealthy = tuple(dep["id"] for dep in new["dependencies"] if not dep["healthy"])
    rotation_key = hashlib.sha256(f"{feature_id}:{old['rotation_key']}:{old['version']}:{new['version']}".encode("utf-8")).hexdigest()
    phases = (
        {"order": 1, "action": "validate_candidate", "reversible": True},
        {"order": 2, "action": "shadow_health_checks", "reversible": True},
        {"order": 3, "action": "batch_cutover", "reversible": True},
        {"order": 4, "action": "grace_observation", "reversible": True},
        {"order": 5, "action": "retire_previous", "reversible": False},
    )
    return {
        "feature_id": feature_id, "resource": resource, "rotation_key": rotation_key,
        "logical_key": old["rotation_key"], "current_artifact": old["artifact_id"],
        "replacement_artifact": new["artifact_id"], "from_version": old["version"],
        "to_version": new["version"], "grace_minutes": grace, "batch_size": batch_size,
        "health_checks": tuple(health_checks), "blockers": unhealthy,
        "safe_to_start": not unhealthy, "requires_approval": True,
        "phases": phases, "rollback_until_phase": 4, "planned_by": actor_id,
        "executed": False, "auditable": True,
    }


def _rotation_api(index: int) -> Callable[..., dict[str, Any]]:
    resource, artifact_field, minimum_grace = _ROTATION_SPECS[index]

    def operation(current: dict[str, Any], replacement: dict[str, Any], policy: dict[str, Any], *, actor: dict[str, Any]) -> dict[str, Any]:
        return _safe_rotation(IDS[17 + index], resource, artifact_field, minimum_grace, current, replacement, policy, actor)

    operation.__name__ = f"plan_safe_{resource}_rotation"
    operation.__doc__ = f"Build a health-gated and reversible rotation plan for {resource}."
    return operation


plan_safe_creator_accounts_rotation = _rotation_api(0)
plan_safe_associated_channels_rotation = _rotation_api(1)
plan_safe_community_campaigns_rotation = _rotation_api(2)
plan_safe_editorial_articles_rotation = _rotation_api(3)
plan_safe_moderated_images_rotation = _rotation_api(4)
plan_safe_user_appeals_rotation = _rotation_api(5)
plan_safe_mtproto_proxies_rotation = _rotation_api(6)
plan_safe_persistent_tasks_rotation = _rotation_api(7)
plan_safe_moderation_rules_rotation = _rotation_api(8)
plan_safe_language_metrics_rotation = _rotation_api(9)
plan_safe_community_translations_rotation = _rotation_api(10)
plan_safe_personal_consents_rotation = _rotation_api(11)
plan_safe_telegram_reactions_rotation = _rotation_api(12)


CACHE_APIS = (
    reconcile_temporary_roles_cache, reconcile_managed_groups_cache,
    reconcile_scheduled_messages_cache, reconcile_rss_feeds_cache,
    reconcile_telegram_videos_cache, reconcile_blocklists_cache,
    reconcile_required_subscriptions_cache, reconcile_signed_webhooks_cache,
    reconcile_quiet_hours_cache, reconcile_correlated_incidents_cache,
    reconcile_accessible_preferences_cache, reconcile_integration_secrets_cache,
    reconcile_contextual_responses_cache, reconcile_miniapp_menus_cache,
    reconcile_bot_statistics_cache, reconcile_advertising_preferences_cache,
    reconcile_processing_queues_cache,
)
ROTATION_APIS = (
    plan_safe_creator_accounts_rotation, plan_safe_associated_channels_rotation,
    plan_safe_community_campaigns_rotation, plan_safe_editorial_articles_rotation,
    plan_safe_moderated_images_rotation, plan_safe_user_appeals_rotation,
    plan_safe_mtproto_proxies_rotation, plan_safe_persistent_tasks_rotation,
    plan_safe_moderation_rules_rotation, plan_safe_language_metrics_rotation,
    plan_safe_community_translations_rotation, plan_safe_personal_consents_rotation,
    plan_safe_telegram_reactions_rotation,
)
ALL_APIS = CACHE_APIS + ROTATION_APIS

assert len(IDS) == len(ALL_APIS) == 30
assert len({operation.__name__ for operation in ALL_APIS}) == 30

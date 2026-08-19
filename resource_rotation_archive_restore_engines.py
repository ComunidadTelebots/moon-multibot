"""Safe rotation extensions, scheduled archive plans and point-in-time restore plans."""

from __future__ import annotations

from datetime import timedelta
import hashlib
import json
from typing import Any, Callable

from resource_cache_rotation_engines import _CACHE_SPECS, _safe_rotation, cache_etag
from resource_incident_temporal_engines import _redact, _utc_datetime
from resource_security_contracts import authorize, bounded_json, safe_identifier


IDS = tuple(
    f"future-{number}"
    for number in (
        5342, 5345, 5348, 5351, 5354, 5357, 5360, 5363, 5366, 5369,
        5372, 5375, 5378, 5381, 5384, 5387, 5390, 5393, 5396, 5399,
        5402, 5405, 5408, 5411, 5414, 5417, 5420, 5423, 5426, 5429,
        5432, 5435, 5438, 5441, 5444, 5447, 5450,
    )
)


_ROTATION_SPECS = (
    ("master_panels", "panel_id", 15),
    ("channel_directories", "directory_id", 30),
    ("external_links", "link_id", 10),
)


def _rotation_api(index: int) -> Callable[..., dict[str, Any]]:
    resource, artifact_field, grace = _ROTATION_SPECS[index]

    def operation(current: dict[str, Any], replacement: dict[str, Any], policy: dict[str, Any], *, actor: dict[str, Any]) -> dict[str, Any]:
        return _safe_rotation(IDS[index], resource, artifact_field, grace, current, replacement, policy, actor)

    operation.__name__ = f"plan_safe_{resource}_rotation"
    operation.__doc__ = f"Build a health-gated reversible rotation plan for {resource}."
    return operation


plan_safe_master_panels_rotation = _rotation_api(0)
plan_safe_channel_directories_rotation = _rotation_api(1)
plan_safe_external_links_rotation = _rotation_api(2)


_ARCHIVE_SPECS = (
    ("administrative_sessions", 365, True),
    ("community_profiles", 180, True),
    ("telegram_communities", 180, False),
    ("house_ads", 365, False),
    ("voice_notes", 30, True),
    ("suspicious_files", 365, True),
    ("captcha_decisions", 180, True),
    ("managed_bots", 365, False),
    ("recurring_reminders", 90, True),
    ("security_events", 730, True),
    ("regional_maps", 30, True),
    ("backups", 365, True),
    ("ai_learning_data", 90, True),
    ("rich_commands", 180, False),
    ("hub_notifications", 90, True),
    ("cookie_policies", 1095, True),
    ("wayback_history", 3650, False),
)


def _scheduled_archive(
    feature_id: str,
    resource: str,
    minimum_retention: int,
    encryption_required: bool,
    records: list[dict[str, Any]],
    schedule: dict[str, Any],
    actor: dict[str, Any],
) -> dict[str, Any]:
    actor_id = authorize(actor, f"archive:plan:{resource}")
    bounded_json(records, maximum_bytes=524288, reject_secrets=True)
    bounded_json(schedule, maximum_bytes=32768, reject_secrets=True)
    if len(records) > 5000:
        raise ValueError("records supera el límite")
    evaluated_at = _utc_datetime(schedule.get("evaluated_at"), "evaluated_at")
    run_at = _utc_datetime(schedule.get("run_at"), "run_at")
    cutoff = _utc_datetime(schedule.get("cutoff_before"), "cutoff_before")
    if run_at < evaluated_at or cutoff >= run_at:
        raise ValueError("Ventana temporal de archivo no válida")
    retention = schedule.get("retention_days")
    batch_size = schedule.get("batch_size", 100)
    destination = safe_identifier(schedule.get("destination_id"), "destination_id")
    key_version = schedule.get("encryption_key_version")
    if not isinstance(retention, int) or isinstance(retention, bool) or not minimum_retention <= retention <= 36500:
        raise ValueError(f"retention_days debe ser al menos {minimum_retention}")
    if not isinstance(batch_size, int) or isinstance(batch_size, bool) or not 1 <= batch_size <= 1000:
        raise ValueError("batch_size no válido")
    if encryption_required and (not isinstance(key_version, int) or isinstance(key_version, bool) or key_version < 1):
        raise ValueError("Se requiere encryption_key_version")
    eligible, held, skipped = [], [], []
    for record in records:
        record_id = safe_identifier(record.get("id"), "record.id")
        updated_at = _utc_datetime(record.get("updated_at"), "record.updated_at")
        state = record.get("state")
        legal_hold = record.get("legal_hold", False)
        size_bytes = record.get("size_bytes", 0)
        version = record.get("version")
        if state not in {"active", "archived"} or not isinstance(legal_hold, bool):
            raise ValueError("state/legal_hold no válido")
        if not isinstance(size_bytes, int) or isinstance(size_bytes, bool) or not 0 <= size_bytes <= 10_000_000_000:
            raise ValueError("size_bytes no válido")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise ValueError("version no válida")
        if legal_hold:
            held.append(record_id)
        elif state == "active" and updated_at < cutoff:
            eligible.append({"id": record_id, "version": version, "size_bytes": size_bytes})
        else:
            skipped.append(record_id)
    batches = tuple(
        tuple(row["id"] for row in eligible[start : start + batch_size])
        for start in range(0, len(eligible), batch_size)
    )
    digest = hashlib.sha256(json.dumps(eligible, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return {
        "feature_id": feature_id, "resource": resource, "planned_by": actor_id,
        "run_at": run_at.isoformat().replace("+00:00", "Z"),
        "cutoff_before": cutoff.isoformat().replace("+00:00", "Z"),
        "destination_id": destination, "retention_days": retention,
        "encryption_required": encryption_required, "encryption_key_version": key_version,
        "eligible_ids": tuple(row["id"] for row in eligible), "held_ids": tuple(held),
        "skipped_ids": tuple(skipped), "batches": batches, "manifest_checksum": digest,
        "total_bytes": sum(row["size_bytes"] for row in eligible),
        "delete_source": False, "requires_approval": True, "executed": False, "auditable": True,
    }


def _archive_api(index: int) -> Callable[..., dict[str, Any]]:
    resource, retention, encrypted = _ARCHIVE_SPECS[index]

    def operation(records: list[dict[str, Any]], schedule: dict[str, Any], *, actor: dict[str, Any]) -> dict[str, Any]:
        return _scheduled_archive(IDS[3 + index], resource, retention, encrypted, records, schedule, actor)

    operation.__name__ = f"plan_{resource}_scheduled_archive"
    operation.__doc__ = f"Select immutable archive batches for {resource}; never write or delete data."
    return operation


plan_administrative_sessions_scheduled_archive = _archive_api(0)
plan_community_profiles_scheduled_archive = _archive_api(1)
plan_telegram_communities_scheduled_archive = _archive_api(2)
plan_house_ads_scheduled_archive = _archive_api(3)
plan_voice_notes_scheduled_archive = _archive_api(4)
plan_suspicious_files_scheduled_archive = _archive_api(5)
plan_captcha_decisions_scheduled_archive = _archive_api(6)
plan_managed_bots_scheduled_archive = _archive_api(7)
plan_recurring_reminders_scheduled_archive = _archive_api(8)
plan_security_events_scheduled_archive = _archive_api(9)
plan_regional_maps_scheduled_archive = _archive_api(10)
plan_backups_scheduled_archive = _archive_api(11)
plan_ai_learning_data_scheduled_archive = _archive_api(12)
plan_rich_commands_scheduled_archive = _archive_api(13)
plan_hub_notifications_scheduled_archive = _archive_api(14)
plan_cookie_policies_scheduled_archive = _archive_api(15)
plan_wayback_history_scheduled_archive = _archive_api(16)


_RESTORE_SPECS = tuple((resource, fields) for resource, fields, _ in _CACHE_SPECS)


def _point_in_time_restore(
    feature_id: str,
    resource: str,
    allowed_fields: frozenset[str],
    entity_id: str,
    current: dict[str, Any],
    history: list[dict[str, Any]],
    target_at: str,
    expected_current_version: int,
    actor: dict[str, Any],
) -> dict[str, Any]:
    actor_id = authorize(actor, f"restore:plan:{resource}")
    entity_id = safe_identifier(entity_id, "entity_id")
    bounded_json(current, maximum_bytes=98304, reject_secrets=True)
    bounded_json(history, maximum_bytes=524288, reject_secrets=True)
    if len(history) > 5000:
        raise ValueError("history supera el límite")
    target = _utc_datetime(target_at, "target_at")
    current_version = current.get("version")
    current_value = current.get("value")
    if not isinstance(current_version, int) or isinstance(current_version, bool) or current_version < 1 or current_version != expected_current_version:
        raise ValueError("Conflicto de versión actual")
    if not isinstance(current_value, dict) or set(current_value) - allowed_fields:
        raise ValueError("current.value contiene campos no permitidos")
    cache_etag(current_value)
    candidates = []
    versions = set()
    for snapshot in history:
        if safe_identifier(snapshot.get("entity_id"), "snapshot.entity_id") != entity_id:
            raise ValueError("Snapshot de otra entidad")
        version = snapshot.get("version")
        value = snapshot.get("value")
        tombstone = snapshot.get("tombstone", False)
        if not isinstance(version, int) or isinstance(version, bool) or version < 1 or version in versions:
            raise ValueError("version de snapshot no válida o duplicada")
        versions.add(version)
        if not isinstance(value, dict) or set(value) - allowed_fields or not isinstance(tombstone, bool):
            raise ValueError("snapshot.value/tombstone no válido")
        if tombstone and value:
            raise ValueError("Un tombstone no puede contener value")
        checksum = cache_etag(value)
        if snapshot.get("checksum") != checksum:
            raise ValueError("Checksum de snapshot incorrecto")
        valid_from = _utc_datetime(snapshot.get("valid_from"), "valid_from")
        valid_to = _utc_datetime(snapshot["valid_to"], "valid_to") if snapshot.get("valid_to") else None
        if valid_to is not None and valid_to <= valid_from:
            raise ValueError("Intervalo de snapshot no válido")
        if valid_from <= target and (valid_to is None or target < valid_to):
            candidates.append({"version": version, "value": value, "tombstone": tombstone, "checksum": checksum, "valid_from": valid_from})
    if not candidates:
        return {
            "feature_id": feature_id, "resource": resource, "entity_id": entity_id,
            "planned_by": actor_id, "restorable": False, "reason": "no_snapshot_at_target",
            "applied": False, "executed": False, "auditable": True,
        }
    selected = max(candidates, key=lambda row: (row["valid_from"], row["version"]))
    changed_fields = tuple(sorted(key for key in allowed_fields if current_value.get(key) != selected["value"].get(key)))
    return {
        "feature_id": feature_id, "resource": resource, "entity_id": entity_id,
        "planned_by": actor_id, "restorable": True, "target_at": target.isoformat().replace("+00:00", "Z"),
        "from_version": current_version, "snapshot_version": selected["version"],
        "snapshot_checksum": selected["checksum"], "restore_value": None if selected["tombstone"] else _redact(selected["value"]),
        "restore_tombstone": selected["tombstone"], "changed_fields": changed_fields,
        "requires_approval": True, "expected_current_version": expected_current_version,
        "applied": False, "executed": False, "auditable": True,
    }


def _restore_api(index: int) -> Callable[..., dict[str, Any]]:
    resource, fields = _RESTORE_SPECS[index]

    def operation(entity_id: str, current: dict[str, Any], history: list[dict[str, Any]], target_at: str, expected_current_version: int, *, actor: dict[str, Any]) -> dict[str, Any]:
        return _point_in_time_restore(IDS[20 + index], resource, fields, entity_id, current, history, target_at, expected_current_version, actor)

    operation.__name__ = f"plan_{resource}_point_in_time_restore"
    operation.__doc__ = f"Select a checksum-verified {resource} snapshot without applying it."
    return operation


plan_temporary_roles_point_in_time_restore = _restore_api(0)
plan_managed_groups_point_in_time_restore = _restore_api(1)
plan_scheduled_messages_point_in_time_restore = _restore_api(2)
plan_rss_feeds_point_in_time_restore = _restore_api(3)
plan_telegram_videos_point_in_time_restore = _restore_api(4)
plan_blocklists_point_in_time_restore = _restore_api(5)
plan_required_subscriptions_point_in_time_restore = _restore_api(6)
plan_signed_webhooks_point_in_time_restore = _restore_api(7)
plan_quiet_hours_point_in_time_restore = _restore_api(8)
plan_correlated_incidents_point_in_time_restore = _restore_api(9)
plan_accessible_preferences_point_in_time_restore = _restore_api(10)
plan_integration_secrets_point_in_time_restore = _restore_api(11)
plan_contextual_responses_point_in_time_restore = _restore_api(12)
plan_miniapp_menus_point_in_time_restore = _restore_api(13)
plan_bot_statistics_point_in_time_restore = _restore_api(14)
plan_advertising_preferences_point_in_time_restore = _restore_api(15)
plan_processing_queues_point_in_time_restore = _restore_api(16)


ROTATION_APIS = (plan_safe_master_panels_rotation, plan_safe_channel_directories_rotation, plan_safe_external_links_rotation)
ARCHIVE_APIS = (
    plan_administrative_sessions_scheduled_archive, plan_community_profiles_scheduled_archive,
    plan_telegram_communities_scheduled_archive, plan_house_ads_scheduled_archive,
    plan_voice_notes_scheduled_archive, plan_suspicious_files_scheduled_archive,
    plan_captcha_decisions_scheduled_archive, plan_managed_bots_scheduled_archive,
    plan_recurring_reminders_scheduled_archive, plan_security_events_scheduled_archive,
    plan_regional_maps_scheduled_archive, plan_backups_scheduled_archive,
    plan_ai_learning_data_scheduled_archive, plan_rich_commands_scheduled_archive,
    plan_hub_notifications_scheduled_archive, plan_cookie_policies_scheduled_archive,
    plan_wayback_history_scheduled_archive,
)
RESTORE_APIS = (
    plan_temporary_roles_point_in_time_restore, plan_managed_groups_point_in_time_restore,
    plan_scheduled_messages_point_in_time_restore, plan_rss_feeds_point_in_time_restore,
    plan_telegram_videos_point_in_time_restore, plan_blocklists_point_in_time_restore,
    plan_required_subscriptions_point_in_time_restore, plan_signed_webhooks_point_in_time_restore,
    plan_quiet_hours_point_in_time_restore, plan_correlated_incidents_point_in_time_restore,
    plan_accessible_preferences_point_in_time_restore, plan_integration_secrets_point_in_time_restore,
    plan_contextual_responses_point_in_time_restore, plan_miniapp_menus_point_in_time_restore,
    plan_bot_statistics_point_in_time_restore, plan_advertising_preferences_point_in_time_restore,
    plan_processing_queues_point_in_time_restore,
)
ALL_APIS = ROTATION_APIS + ARCHIVE_APIS + RESTORE_APIS

assert len(IDS) == len(ALL_APIS) == 37
assert len({operation.__name__ for operation in ALL_APIS}) == 37

"""Incident lifecycle escalation and temporal correlation contracts.

The functions in this module are pure planning operations: they validate and
normalise input, but never send notifications or mutate Moonbot state.  That
makes every result safe to audit and idempotent before a caller executes it.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
from typing import Any, Callable, Iterable


IDS = tuple(
    f"future-{number}"
    for number in (
        4802, 4805, 4808, 4811, 4814, 4817, 4820, 4823, 4826, 4829,
        4832, 4835, 4838, 4841, 4844, 4847, 4850, 4853, 4856, 4859,
    )
)

SEVERITIES = ("info", "warning", "high", "critical")
SENSITIVE_KEYS = {
    "token", "secret", "password", "authorization", "cookie", "api_key",
    "signature", "payload_raw",
}


def _utc_datetime(value: Any, field: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"{field} debe ser ISO-8601") from exc
    else:
        raise ValueError(f"{field} es obligatorio")
    if parsed.tzinfo is None:
        raise ValueError(f"{field} debe incluir zona horaria")
    return parsed.astimezone(timezone.utc)


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if str(key).lower() in SENSITIVE_KEYS else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _validate_policy(policy: dict[str, Any] | None, default_chain: tuple[str, ...]) -> dict[str, Any]:
    candidate = dict(policy or {})
    chain = candidate.get("owner_chain", default_chain)
    if not isinstance(chain, (list, tuple)) or not chain or len(chain) > 6:
        raise ValueError("owner_chain debe contener entre 1 y 6 roles")
    chain = tuple(str(role).strip() for role in chain)
    if any(not role for role in chain) or len(set(chain)) != len(chain):
        raise ValueError("owner_chain contiene roles vacíos o duplicados")
    raw_sla = candidate.get(
        "ack_sla_minutes",
        {"info": 240, "warning": 60, "high": 20, "critical": 5},
    )
    if not isinstance(raw_sla, dict) or set(raw_sla) != set(SEVERITIES):
        raise ValueError("ack_sla_minutes debe definir todas las severidades")
    sla = {}
    for severity in SEVERITIES:
        minutes = raw_sla[severity]
        if not isinstance(minutes, int) or isinstance(minutes, bool) or not 1 <= minutes <= 10080:
            raise ValueError("Los SLA deben ser minutos enteros entre 1 y 10080")
        sla[severity] = minutes
    max_attempts = candidate.get("max_attempts_per_tier", 3)
    if not isinstance(max_attempts, int) or isinstance(max_attempts, bool) or not 1 <= max_attempts <= 20:
        raise ValueError("max_attempts_per_tier debe estar entre 1 y 20")
    return {"owner_chain": chain, "ack_sla_minutes": sla, "max_attempts_per_tier": max_attempts}


def _escalate_incident(
    feature_id: str,
    resource: str,
    incident: dict[str, Any],
    policy: dict[str, Any] | None,
    default_chain: tuple[str, ...],
) -> dict[str, Any]:
    if not isinstance(incident, dict):
        raise ValueError("incident debe ser un objeto")
    incident_id = incident.get("id")
    if not isinstance(incident_id, str) or not incident_id.strip() or len(incident_id) > 128:
        raise ValueError("id de incidente no válido")
    severity = incident.get("severity")
    if severity not in SEVERITIES:
        raise ValueError("severity no válida")
    occurred_at = _utc_datetime(incident.get("occurred_at"), "occurred_at")
    now = _utc_datetime(incident.get("evaluated_at"), "evaluated_at")
    if occurred_at > now + timedelta(minutes=1):
        raise ValueError("occurred_at no puede estar en el futuro")
    attempts = incident.get("notification_attempts", 0)
    if not isinstance(attempts, int) or isinstance(attempts, bool) or attempts < 0:
        raise ValueError("notification_attempts no válido")
    acknowledged = incident.get("acknowledged", False)
    if not isinstance(acknowledged, bool):
        raise ValueError("acknowledged debe ser booleano")
    evidence = incident.get("evidence", {})
    if not isinstance(evidence, dict) or len(evidence) > 50:
        raise ValueError("evidence debe ser un objeto acotado")

    resolved_policy = _validate_policy(policy, default_chain)
    sla = resolved_policy["ack_sla_minutes"][severity]
    age_minutes = max(0, int((now - occurred_at).total_seconds() // 60))
    overdue_steps = age_minutes // sla
    retry_steps = attempts // resolved_policy["max_attempts_per_tier"]
    requested_tier = max(overdue_steps, retry_steps)
    tier = 0 if acknowledged else min(len(resolved_policy["owner_chain"]) - 1, requested_tier)
    assigned_role = resolved_policy["owner_chain"][tier]
    should_notify = not acknowledged and (attempts == 0 or requested_tier > 0)
    fingerprint_source = {
        "resource": resource,
        "incident_id": incident_id.strip(),
        "severity": severity,
        "tier": tier,
    }
    fingerprint = hashlib.sha256(
        json.dumps(fingerprint_source, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    next_ack_due = occurred_at + timedelta(minutes=sla * (tier + 1))
    return {
        "feature_id": feature_id,
        "resource": resource,
        "incident_id": incident_id.strip(),
        "severity": severity,
        "state": "acknowledged" if acknowledged else ("escalated" if tier else "awaiting_ack"),
        "tier": tier,
        "assigned_role": assigned_role,
        "owner_chain": resolved_policy["owner_chain"],
        "age_minutes": age_minutes,
        "ack_sla_minutes": sla,
        "next_ack_due": next_ack_due.isoformat().replace("+00:00", "Z"),
        "should_notify": should_notify,
        "idempotency_key": fingerprint,
        "evidence": _redact(evidence),
        "executed": False,
        "auditable": True,
    }


_ESCALATION_SPECS = (
    ("temporary_roles", ("group_owner", "security_admin", "master")),
    ("managed_groups", ("group_admin", "bot_operator", "master")),
    ("scheduled_messages", ("content_editor", "group_admin", "master")),
    ("rss_feeds", ("feed_manager", "group_admin", "master")),
    ("telegram_videos", ("media_moderator", "group_admin", "master")),
    ("blocklists", ("moderator", "security_admin", "master")),
    ("required_subscriptions", ("group_admin", "community_admin", "master")),
    ("signed_webhooks", ("integration_owner", "security_admin", "master")),
    ("quiet_hours", ("automation_owner", "group_admin", "master")),
    ("correlated_incidents", ("incident_owner", "security_admin", "master")),
    ("accessible_preferences", ("support", "accessibility_admin", "master")),
    ("integration_secrets", ("integration_owner", "security_admin", "master")),
    ("contextual_responses", ("ai_reviewer", "group_admin", "master")),
    ("miniapp_menus", ("ui_operator", "bot_operator", "master")),
    ("bot_statistics", ("metrics_operator", "bot_operator", "master")),
    ("advertising_preferences", ("campaign_manager", "privacy_admin", "master")),
    ("processing_queues", ("queue_operator", "platform_admin", "master")),
)


def _escalation_api(index: int) -> Callable[[dict[str, Any], dict[str, Any] | None], dict[str, Any]]:
    resource, chain = _ESCALATION_SPECS[index]

    def operation(incident: dict[str, Any], policy: dict[str, Any] | None = None) -> dict[str, Any]:
        return _escalate_incident(IDS[index], resource, incident, policy, chain)

    operation.__name__ = f"escalate_{resource}_incident"
    operation.__doc__ = f"Plan an auditable incident escalation for {resource}."
    return operation


escalate_temporary_roles_incident = _escalation_api(0)
escalate_managed_groups_incident = _escalation_api(1)
escalate_scheduled_messages_incident = _escalation_api(2)
escalate_rss_feeds_incident = _escalation_api(3)
escalate_telegram_videos_incident = _escalation_api(4)
escalate_blocklists_incident = _escalation_api(5)
escalate_required_subscriptions_incident = _escalation_api(6)
escalate_signed_webhooks_incident = _escalation_api(7)
escalate_quiet_hours_incident = _escalation_api(8)
escalate_correlated_incidents_incident = _escalation_api(9)
escalate_accessible_preferences_incident = _escalation_api(10)
escalate_integration_secrets_incident = _escalation_api(11)
escalate_contextual_responses_incident = _escalation_api(12)
escalate_miniapp_menus_incident = _escalation_api(13)
escalate_bot_statistics_incident = _escalation_api(14)
escalate_advertising_preferences_incident = _escalation_api(15)
escalate_processing_queues_incident = _escalation_api(16)


def _correlate_temporal(
    feature_id: str,
    resource: str,
    events: Iterable[dict[str, Any]],
    entity_field: str,
    allowed_kinds: frozenset[str],
    window_minutes: int,
    min_events: int,
) -> dict[str, Any]:
    if not isinstance(events, list) or len(events) > 5000:
        raise ValueError("events debe ser una lista de hasta 5000 elementos")
    if not isinstance(window_minutes, int) or isinstance(window_minutes, bool) or not 1 <= window_minutes <= 10080:
        raise ValueError("window_minutes fuera de rango")
    if not isinstance(min_events, int) or isinstance(min_events, bool) or not 2 <= min_events <= 50:
        raise ValueError("min_events fuera de rango")
    deduplicated: dict[str, dict[str, Any]] = {}
    for raw in events:
        if not isinstance(raw, dict):
            raise ValueError("evento no válido")
        event_id = raw.get("id")
        entity_id = raw.get(entity_field)
        kind = raw.get("kind")
        if not isinstance(event_id, str) or not event_id or len(event_id) > 128:
            raise ValueError("id de evento no válido")
        if not isinstance(entity_id, str) or not entity_id or len(entity_id) > 128:
            raise ValueError(f"{entity_field} no válido")
        if kind not in allowed_kinds:
            raise ValueError(f"kind no admitido para {resource}")
        occurred_at = _utc_datetime(raw.get("occurred_at"), "occurred_at")
        confidence = raw.get("confidence", 1.0)
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
            raise ValueError("confidence debe estar entre 0 y 1")
        deduplicated.setdefault(event_id, {
            "id": event_id,
            "entity_id": entity_id,
            "kind": kind,
            "occurred_at": occurred_at,
            "confidence": float(confidence),
        })

    by_entity: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in deduplicated.values():
        by_entity[event["entity_id"]].append(event)
    window = timedelta(minutes=window_minutes)
    clusters = []
    for entity_id, entity_events in sorted(by_entity.items()):
        ordered = sorted(entity_events, key=lambda event: (event["occurred_at"], event["id"]))
        start = 0
        for end, current in enumerate(ordered):
            while current["occurred_at"] - ordered[start]["occurred_at"] > window:
                start += 1
            candidate = ordered[start : end + 1]
            if len(candidate) < min_events:
                continue
            score = round(sum(event["confidence"] for event in candidate) / len(candidate), 4)
            clusters.append({
                "entity_id": entity_id,
                "event_ids": tuple(event["id"] for event in candidate),
                "kinds": tuple(sorted({event["kind"] for event in candidate})),
                "start_at": candidate[0]["occurred_at"].isoformat().replace("+00:00", "Z"),
                "end_at": candidate[-1]["occurred_at"].isoformat().replace("+00:00", "Z"),
                "confidence": score,
            })
            break
    return {
        "feature_id": feature_id,
        "resource": resource,
        "entity_field": entity_field,
        "window_minutes": window_minutes,
        "min_events": min_events,
        "input_count": len(events),
        "unique_event_count": len(deduplicated),
        "clusters": tuple(clusters),
        "cluster_count": len(clusters),
        "executed": False,
        "auditable": True,
    }


def correlate_creator_accounts(events: list[dict[str, Any]], window_minutes: int = 60, min_events: int = 2) -> dict[str, Any]:
    return _correlate_temporal(
        IDS[17], "creator_accounts", events, "account_id",
        frozenset({"login", "role_change", "freeze", "unfreeze", "credential_change"}),
        window_minutes, min_events,
    )


def correlate_associated_channels(events: list[dict[str, Any]], window_minutes: int = 60, min_events: int = 2) -> dict[str, Any]:
    return _correlate_temporal(
        IDS[18], "associated_channels", events, "channel_id",
        frozenset({"associate", "disassociate", "bot_join", "bot_leave", "permission_change"}),
        window_minutes, min_events,
    )


def correlate_community_campaigns(events: list[dict[str, Any]], window_minutes: int = 60, min_events: int = 2) -> dict[str, Any]:
    return _correlate_temporal(
        IDS[19], "community_campaigns", events, "campaign_id",
        frozenset({"publish", "impression_spike", "click_spike", "pause", "resume"}),
        window_minutes, min_events,
    )


ESCALATION_APIS = (
    escalate_temporary_roles_incident,
    escalate_managed_groups_incident,
    escalate_scheduled_messages_incident,
    escalate_rss_feeds_incident,
    escalate_telegram_videos_incident,
    escalate_blocklists_incident,
    escalate_required_subscriptions_incident,
    escalate_signed_webhooks_incident,
    escalate_quiet_hours_incident,
    escalate_correlated_incidents_incident,
    escalate_accessible_preferences_incident,
    escalate_integration_secrets_incident,
    escalate_contextual_responses_incident,
    escalate_miniapp_menus_incident,
    escalate_bot_statistics_incident,
    escalate_advertising_preferences_incident,
    escalate_processing_queues_incident,
)

TEMPORAL_APIS = (
    correlate_creator_accounts,
    correlate_associated_channels,
    correlate_community_campaigns,
)

ALL_APIS = ESCALATION_APIS + TEMPORAL_APIS

assert len(IDS) == len(ALL_APIS) == 20
assert len({operation.__name__ for operation in ALL_APIS}) == 20

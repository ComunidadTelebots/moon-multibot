"""Local distributed-trace analysis and non-mutating resource quality checks."""

from __future__ import annotations

from collections import defaultdict
import ipaddress
import re
from typing import Any, Callable
from urllib.parse import urlsplit

from resource_incident_temporal_engines import _utc_datetime
from resource_security_contracts import authorize, bounded_json, safe_identifier


IDS = tuple(
    f"future-{number}"
    for number in (
        5453, 5456, 5459, 5462, 5465, 5468, 5471, 5474, 5477, 5480,
        5483, 5486, 5489, 5492, 5495, 5498, 5501, 5504, 5507, 5510,
        5513, 5516, 5519,
    )
)


_OBS_SPECS = (
    ("creator_accounts", frozenset({"authenticate", "authorize", "update"})),
    ("associated_channels", frozenset({"associate", "permission", "publish"})),
    ("community_campaigns", frozenset({"select", "render", "measure"})),
    ("editorial_articles", frozenset({"ingest", "extract", "publish"})),
    ("moderated_images", frozenset({"download", "classify", "decide"})),
    ("user_appeals", frozenset({"submit", "review", "resolve"})),
    ("mtproto_proxies", frozenset({"probe", "route", "measure"})),
    ("persistent_tasks", frozenset({"schedule", "run", "complete"})),
    ("moderation_rules", frozenset({"load", "match", "act"})),
    ("language_metrics", frozenset({"collect", "aggregate", "map"})),
    ("community_translations", frozenset({"submit", "vote", "approve"})),
    ("personal_consents", frozenset({"verify", "grant", "revoke"})),
    ("telegram_reactions", frozenset({"receive", "classify", "respond"})),
    ("master_panels", frozenset({"fetch", "aggregate", "render"})),
    ("channel_directories", frozenset({"crawl", "verify", "index"})),
    ("external_links", frozenset({"normalize", "inspect", "classify"})),
)


def _distributed_observability(
    feature_id: str,
    resource: str,
    allowed_operations: frozenset[str],
    spans: list[dict[str, Any]],
    actor: dict[str, Any],
) -> dict[str, Any]:
    actor_id = authorize(actor, f"observability:read:{resource}")
    bounded_json(spans, maximum_bytes=524288, reject_secrets=True)
    if len(spans) > 5000:
        raise ValueError("spans supera el límite")
    normalised = []
    span_ids = set()
    for raw in spans:
        if not isinstance(raw, dict):
            raise ValueError("span no válido")
        trace_id = safe_identifier(raw.get("trace_id"), "trace_id", 64)
        span_id = safe_identifier(raw.get("span_id"), "span_id", 64)
        if span_id in span_ids:
            raise ValueError("span_id duplicado")
        span_ids.add(span_id)
        parent_id = raw.get("parent_id")
        if parent_id is not None:
            parent_id = safe_identifier(parent_id, "parent_id", 64)
        node = safe_identifier(raw.get("node"), "node", 128)
        operation = raw.get("operation")
        status = raw.get("status")
        if operation not in allowed_operations or status not in {"ok", "error", "timeout"}:
            raise ValueError("operation/status no válido")
        started = _utc_datetime(raw.get("started_at"), "started_at")
        ended = _utc_datetime(raw.get("ended_at"), "ended_at")
        duration_ms = int((ended - started).total_seconds() * 1000)
        if duration_ms < 0 or duration_ms > 86_400_000:
            raise ValueError("Duración de span no válida")
        attributes = raw.get("attributes", {})
        bounded_json(attributes, maximum_bytes=16384, reject_secrets=True)
        normalised.append({
            "trace_id": trace_id, "span_id": span_id, "parent_id": parent_id,
            "node": node, "operation": operation, "status": status,
            "started_at": started, "ended_at": ended, "duration_ms": duration_ms,
            "attribute_keys": tuple(sorted(attributes)),
        })
    by_trace = defaultdict(list)
    for span in normalised:
        by_trace[span["trace_id"]].append(span)
    traces = []
    for trace_id, rows in sorted(by_trace.items()):
        ids = {row["span_id"] for row in rows}
        orphans = tuple(sorted(row["span_id"] for row in rows if row["parent_id"] and row["parent_id"] not in ids))
        start = min(row["started_at"] for row in rows)
        end = max(row["ended_at"] for row in rows)
        critical = max(rows, key=lambda row: (row["duration_ms"], row["span_id"]))
        traces.append({
            "trace_id": trace_id, "span_count": len(rows),
            "duration_ms": int((end - start).total_seconds() * 1000),
            "error_count": sum(row["status"] != "ok" for row in rows),
            "nodes": tuple(sorted({row["node"] for row in rows})), "orphan_span_ids": orphans,
            "critical_span_id": critical["span_id"], "critical_span_duration_ms": critical["duration_ms"],
        })
    return {
        "feature_id": feature_id, "resource": resource, "observed_by": actor_id,
        "trace_count": len(traces), "span_count": len(normalised), "traces": tuple(traces),
        "contains_raw_attributes": False, "network_export_requested": False,
        "executed": False, "auditable": True,
    }


def _observability_api(index: int) -> Callable[..., dict[str, Any]]:
    resource, operations = _OBS_SPECS[index]

    def operation(spans: list[dict[str, Any]], *, actor: dict[str, Any]) -> dict[str, Any]:
        return _distributed_observability(IDS[index], resource, operations, spans, actor)

    operation.__name__ = f"observe_{resource}_distributed"
    operation.__doc__ = f"Analyse local {resource} traces without exporting telemetry."
    return operation


observe_creator_accounts_distributed = _observability_api(0)
observe_associated_channels_distributed = _observability_api(1)
observe_community_campaigns_distributed = _observability_api(2)
observe_editorial_articles_distributed = _observability_api(3)
observe_moderated_images_distributed = _observability_api(4)
observe_user_appeals_distributed = _observability_api(5)
observe_mtproto_proxies_distributed = _observability_api(6)
observe_persistent_tasks_distributed = _observability_api(7)
observe_moderation_rules_distributed = _observability_api(8)
observe_language_metrics_distributed = _observability_api(9)
observe_community_translations_distributed = _observability_api(10)
observe_personal_consents_distributed = _observability_api(11)
observe_telegram_reactions_distributed = _observability_api(12)
observe_master_panels_distributed = _observability_api(13)
observe_channel_directories_distributed = _observability_api(14)
observe_external_links_distributed = _observability_api(15)


_QUALITY_SPECS = (
    ("administrative_sessions", ("id", "user_id", "state", "started_at")),
    ("community_profiles", ("id", "display_name", "visibility", "language")),
    ("telegram_communities", ("id", "title", "member_count", "bot_permissions")),
    ("house_ads", ("id", "title", "url", "enabled", "approval_status")),
    ("voice_notes", ("id", "duration_seconds", "transcript_status", "consent")),
    ("suspicious_files", ("id", "sha256", "risk", "scan_status")),
    ("captcha_decisions", ("id", "user_id", "decision", "score")),
)


def _public_https(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return False
    if parsed.hostname.casefold() == "localhost":
        return False
    try:
        return not ipaddress.ip_address(parsed.hostname).is_private
    except ValueError:
        return True


def _quality_issues(index: int, record: dict[str, Any]) -> list[str]:
    issues = []
    try:
        safe_identifier(record.get("id"), "record.id")
    except ValueError:
        issues.append("invalid_id")
    if index == 0:
        try: safe_identifier(record.get("user_id"), "user_id")
        except ValueError: issues.append("invalid_user_id")
        if record.get("state") not in {"active", "closed", "revoked"}: issues.append("invalid_state")
        try: _utc_datetime(record.get("started_at"), "started_at")
        except ValueError: issues.append("invalid_started_at")
    elif index == 1:
        if not isinstance(record.get("display_name"), str) or not record["display_name"].strip() or len(record["display_name"]) > 100: issues.append("invalid_display_name")
        if record.get("visibility") not in {"public", "members", "private"}: issues.append("invalid_visibility")
        if not isinstance(record.get("language"), str) or not re.fullmatch(r"[a-z]{2,3}(?:-[A-Z]{2})?", record["language"]): issues.append("invalid_language")
    elif index == 2:
        if not isinstance(record.get("title"), str) or not record["title"].strip() or len(record["title"]) > 128: issues.append("invalid_title")
        if not isinstance(record.get("member_count"), int) or isinstance(record.get("member_count"), bool) or record.get("member_count", -1) < 0: issues.append("invalid_member_count")
        permissions = record.get("bot_permissions")
        if not isinstance(permissions, dict) or not permissions or not all(isinstance(value, bool) for value in permissions.values()): issues.append("invalid_bot_permissions")
    elif index == 3:
        if not isinstance(record.get("title"), str) or not record["title"].strip() or len(record["title"]) > 120: issues.append("invalid_title")
        if not _public_https(record.get("url")): issues.append("unsafe_url")
        if not isinstance(record.get("enabled"), bool): issues.append("invalid_enabled")
        if record.get("approval_status") not in {"pending", "approved", "rejected"}: issues.append("invalid_approval_status")
    elif index == 4:
        duration = record.get("duration_seconds")
        if not isinstance(duration, (int, float)) or isinstance(duration, bool) or not 0 < duration <= 600: issues.append("invalid_duration")
        if record.get("transcript_status") not in {"not_requested", "pending", "completed", "failed"}: issues.append("invalid_transcript_status")
        if not isinstance(record.get("consent"), bool): issues.append("invalid_consent")
    elif index == 5:
        if not isinstance(record.get("sha256"), str) or not re.fullmatch(r"[0-9a-fA-F]{64}", record["sha256"]): issues.append("invalid_sha256")
        if record.get("risk") not in {"low", "medium", "high", "critical"}: issues.append("invalid_risk")
        if record.get("scan_status") not in {"pending", "clean", "suspicious", "malicious", "error"}: issues.append("invalid_scan_status")
    else:
        try: safe_identifier(record.get("user_id"), "user_id")
        except ValueError: issues.append("invalid_user_id")
        if record.get("decision") not in {"pass", "fail", "expired", "appealed"}: issues.append("invalid_decision")
        score = record.get("score")
        if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 1: issues.append("invalid_score")
    return issues


def _quality_control(
    feature_id: str,
    resource: str,
    required_fields: tuple[str, ...],
    index: int,
    records: list[dict[str, Any]],
    actor: dict[str, Any],
    pass_threshold: int,
) -> dict[str, Any]:
    actor_id = authorize(actor, f"quality:review:{resource}")
    bounded_json(records, maximum_bytes=524288, reject_secrets=True)
    if not isinstance(records, list) or len(records) > 10000:
        raise ValueError("records no válido")
    if not isinstance(pass_threshold, int) or isinstance(pass_threshold, bool) or not 50 <= pass_threshold <= 100:
        raise ValueError("pass_threshold no válido")
    seen = set(); results = []
    for position, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError("record no válido")
        missing = tuple(field for field in required_fields if field not in record or record[field] is None)
        issues = list(missing and ("missing_required_fields",) or ())
        issues.extend(_quality_issues(index, record))
        try:
            record_id = safe_identifier(record.get("id"), "record.id")
        except ValueError:
            # Never reflect attacker-controlled identifiers into WebApp output.
            record_id = f"invalid-at-{position}"
        if record_id in seen: issues.append("duplicate_id")
        seen.add(record_id)
        score = max(0, 100 - 20 * len(set(issues)) - 5 * len(missing))
        results.append({"record_id": record_id, "score": score, "issues": tuple(sorted(set(issues))), "missing_fields": missing})
    aggregate = round(sum(row["score"] for row in results) / len(results), 2) if results else 100.0
    return {
        "feature_id": feature_id, "resource": resource, "reviewed_by": actor_id,
        "record_count": len(records), "quality_score": aggregate,
        "pass_threshold": pass_threshold, "passed": aggregate >= pass_threshold,
        "failed_record_ids": tuple(row["record_id"] for row in results if row["score"] < pass_threshold),
        "results": tuple(results), "raw_values_exposed": False,
        "mutation_requested": False, "executed": False, "auditable": True,
    }


def _quality_api(index: int) -> Callable[..., dict[str, Any]]:
    resource, fields = _QUALITY_SPECS[index]

    def operation(records: list[dict[str, Any]], *, actor: dict[str, Any], pass_threshold: int = 90) -> dict[str, Any]:
        return _quality_control(IDS[16 + index], resource, fields, index, records, actor, pass_threshold)

    operation.__name__ = f"review_{resource}_quality"
    operation.__doc__ = f"Score {resource} data quality without changing records."
    return operation


review_administrative_sessions_quality = _quality_api(0)
review_community_profiles_quality = _quality_api(1)
review_telegram_communities_quality = _quality_api(2)
review_house_ads_quality = _quality_api(3)
review_voice_notes_quality = _quality_api(4)
review_suspicious_files_quality = _quality_api(5)
review_captcha_decisions_quality = _quality_api(6)


OBSERVABILITY_APIS = (
    observe_creator_accounts_distributed, observe_associated_channels_distributed,
    observe_community_campaigns_distributed, observe_editorial_articles_distributed,
    observe_moderated_images_distributed, observe_user_appeals_distributed,
    observe_mtproto_proxies_distributed, observe_persistent_tasks_distributed,
    observe_moderation_rules_distributed, observe_language_metrics_distributed,
    observe_community_translations_distributed, observe_personal_consents_distributed,
    observe_telegram_reactions_distributed, observe_master_panels_distributed,
    observe_channel_directories_distributed, observe_external_links_distributed,
)
QUALITY_APIS = (
    review_administrative_sessions_quality, review_community_profiles_quality,
    review_telegram_communities_quality, review_house_ads_quality,
    review_voice_notes_quality, review_suspicious_files_quality,
    review_captcha_decisions_quality,
)
ALL_APIS = OBSERVABILITY_APIS + QUALITY_APIS

assert len(IDS) == len(ALL_APIS) == 23
assert len({operation.__name__ for operation in ALL_APIS}) == 23

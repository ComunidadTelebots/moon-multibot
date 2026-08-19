"""Pure, authorised engines for roadmap quality, sandbox, governance and impact features."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from typing import Any, Callable

from resource_incident_temporal_engines import _utc_datetime
from resource_security_contracts import authorize, bounded_json, safe_identifier


IDS = tuple(f"future-{number}" for number in range(5522, 5700, 3))

QUALITY_RESOURCES = (
    "managed_bots", "recurring_reminders", "security_events", "regional_maps",
    "backups", "ai_learning_data", "rich_commands", "hub_notifications",
    "cookie_policies", "wayback_history",
)
SANDBOX_RESOURCES = (
    "temporary_roles", "managed_groups", "scheduled_messages", "rss_feeds",
    "telegram_videos", "blocklists", "required_subscriptions", "signed_webhooks",
    "quiet_hours", "correlated_incidents", "accessible_preferences",
    "integration_secrets", "contextual_responses", "miniapp_menus", "bot_statistics",
    "advertising_preferences", "processing_queues",
)
GOVERNANCE_RESOURCES = (
    "creator_accounts", "associated_channels", "community_campaigns", "editorial_articles",
    "moderated_images", "user_appeals", "mtproto_proxies", "persistent_tasks",
    "moderation_rules", "language_metrics", "community_translations", "personal_consents",
    "telegram_reactions", "master_panels", "channel_directories", "external_links",
)
IMPACT_RESOURCES = (
    "administrative_sessions", "community_profiles", "telegram_communities", "house_ads",
    "voice_notes", "suspicious_files", "captcha_decisions", "managed_bots",
    "recurring_reminders", "security_events", "regional_maps", "backups",
    "ai_learning_data", "rich_commands", "hub_notifications", "cookie_policies",
    "wayback_history",
)

_QUALITY_REQUIRED = {
    "managed_bots": ("id", "username", "enabled"),
    "recurring_reminders": ("id", "schedule", "enabled"),
    "security_events": ("id", "severity", "occurred_at"),
    "regional_maps": ("id", "language", "user_count"),
    "backups": ("id", "checksum", "created_at"),
    "ai_learning_data": ("id", "consent", "source"),
    "rich_commands": ("id", "command", "parse_mode"),
    "hub_notifications": ("id", "audience", "created_at"),
    "cookie_policies": ("id", "version", "effective_at"),
    "wayback_history": ("id", "url", "captured_at"),
}


def _quality_issues(resource: str, row: dict[str, Any]) -> list[str]:
    issues = []
    if resource == "managed_bots":
        if not isinstance(row.get("username"), str) or not row["username"].lstrip("@").replace("_", "").isalnum(): issues.append("invalid_username")
        if not isinstance(row.get("enabled"), bool): issues.append("invalid_enabled")
    elif resource == "recurring_reminders":
        if not isinstance(row.get("schedule"), str) or len(row["schedule"]) > 100: issues.append("invalid_schedule")
        if not isinstance(row.get("enabled"), bool): issues.append("invalid_enabled")
    elif resource == "security_events":
        if row.get("severity") not in {"low", "medium", "high", "critical"}: issues.append("invalid_severity")
        try: _utc_datetime(row.get("occurred_at"), "occurred_at")
        except ValueError: issues.append("invalid_occurred_at")
    elif resource == "regional_maps":
        if not isinstance(row.get("language"), str) or not 2 <= len(row["language"]) <= 12: issues.append("invalid_language")
        if not isinstance(row.get("user_count"), int) or isinstance(row.get("user_count"), bool) or row.get("user_count", -1) < 0: issues.append("invalid_user_count")
    elif resource == "backups":
        if not isinstance(row.get("checksum"), str) or len(row["checksum"]) != 64: issues.append("invalid_checksum")
        try: _utc_datetime(row.get("created_at"), "created_at")
        except ValueError: issues.append("invalid_created_at")
    elif resource == "ai_learning_data":
        if row.get("consent") is not True: issues.append("missing_consent")
        try: safe_identifier(row.get("source"), "source")
        except ValueError: issues.append("invalid_source")
    elif resource == "rich_commands":
        if not isinstance(row.get("command"), str) or not row["command"].startswith("/"): issues.append("invalid_command")
        if row.get("parse_mode") not in {"HTML", "MarkdownV2", "plain"}: issues.append("invalid_parse_mode")
    elif resource == "hub_notifications":
        if row.get("audience") not in {"master", "admins", "users"}: issues.append("invalid_audience")
        try: _utc_datetime(row.get("created_at"), "created_at")
        except ValueError: issues.append("invalid_created_at")
    elif resource == "cookie_policies":
        try: safe_identifier(row.get("version"), "version")
        except ValueError: issues.append("invalid_version")
        try: _utc_datetime(row.get("effective_at"), "effective_at")
        except ValueError: issues.append("invalid_effective_at")
    else:
        url = row.get("url")
        if not isinstance(url, str) or not url.startswith("https://") or "@" in url.split("/", 3)[2]: issues.append("invalid_url")
        try: _utc_datetime(row.get("captured_at"), "captured_at")
        except ValueError: issues.append("invalid_captured_at")
    return issues


def _review_quality(feature_id: str, resource: str, records: list[dict[str, Any]], actor: dict[str, Any], threshold: int = 90) -> dict[str, Any]:
    actor_id = authorize(actor, f"quality:review:{resource}")
    bounded_json(records, maximum_bytes=524288, reject_secrets=True)
    if not isinstance(records, list) or len(records) > 10000 or not 50 <= threshold <= 100:
        raise ValueError("quality request invalid")
    results = []
    seen = set()
    for position, row in enumerate(records):
        if not isinstance(row, dict): raise ValueError("record invalid")
        try: record_id = safe_identifier(row.get("id"), "id")
        except ValueError: record_id = f"invalid-at-{position}"
        missing = tuple(key for key in _QUALITY_REQUIRED[resource] if row.get(key) is None)
        issues = _quality_issues(resource, row)
        if missing: issues.append("missing_required_fields")
        if record_id in seen: issues.append("duplicate_id")
        seen.add(record_id)
        score = max(0, 100 - 20 * len(set(issues)) - 5 * len(missing))
        results.append({"record_id": record_id, "score": score, "issues": tuple(sorted(set(issues))), "missing_fields": missing})
    aggregate = round(sum(x["score"] for x in results) / len(results), 2) if results else 100.0
    return {"feature_id": feature_id, "resource": resource, "reviewed_by": actor_id, "record_count": len(records), "quality_score": aggregate, "passed": aggregate >= threshold, "results": tuple(results), "raw_values_exposed": False, "mutation_requested": False, "executed": False, "auditable": True}


_SANDBOX_OPERATIONS = {
    resource: frozenset(("validate", "preview", "simulate")) for resource in SANDBOX_RESOURCES
}


def _run_sandbox(feature_id: str, resource: str, request: dict[str, Any], actor: dict[str, Any]) -> dict[str, Any]:
    actor_id = authorize(actor, f"sandbox:run:{resource}")
    bounded_json(request, maximum_bytes=131072, reject_secrets=True)
    if not isinstance(request, dict): raise ValueError("request invalid")
    run_id = safe_identifier(request.get("run_id"), "run_id")
    operation = request.get("operation")
    if operation not in _SANDBOX_OPERATIONS[resource]: raise ValueError("operation not allowed")
    inputs = request.get("inputs", {})
    bounded_json(inputs, maximum_bytes=65536, reject_secrets=True)
    budget = request.get("budget", {})
    if not isinstance(budget, dict): raise ValueError("budget invalid")
    max_steps = budget.get("max_steps", 10)
    max_items = budget.get("max_items", 100)
    timeout_ms = budget.get("timeout_ms", 1000)
    if any(isinstance(v, bool) or not isinstance(v, int) for v in (max_steps, max_items, timeout_ms)) or not (1 <= max_steps <= 100 and 1 <= max_items <= 1000 and 10 <= timeout_ms <= 10000): raise ValueError("budget outside limits")
    input_keys = tuple(sorted(inputs))
    digest = hashlib.sha256(json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"feature_id": feature_id, "resource": resource, "run_id": run_id, "operation": operation, "run_by": actor_id, "input_digest": digest, "input_keys": input_keys, "budget": {"max_steps": max_steps, "max_items": max_items, "timeout_ms": timeout_ms}, "violations": (), "filesystem_access": False, "network_access": False, "process_access": False, "secrets_available": False, "side_effects": False, "executed": False, "auditable": True}


def _governance(feature_id: str, resource: str, proposal: dict[str, Any], votes: list[dict[str, Any]], actor: dict[str, Any]) -> dict[str, Any]:
    actor_id = authorize(actor, f"governance:review:{resource}")
    bounded_json(proposal, maximum_bytes=65536, reject_secrets=True)
    bounded_json(votes, maximum_bytes=262144, reject_secrets=True)
    if not isinstance(proposal, dict) or not isinstance(votes, list) or len(votes) > 5000: raise ValueError("governance request invalid")
    proposal_id = safe_identifier(proposal.get("proposal_id"), "proposal_id")
    proposer_id = safe_identifier(proposal.get("proposer_id"), "proposer_id")
    opens_at = _utc_datetime(proposal.get("opens_at"), "opens_at")
    closes_at = _utc_datetime(proposal.get("closes_at"), "closes_at")
    if closes_at <= opens_at: raise ValueError("invalid voting window")
    quorum = proposal.get("quorum", 1)
    eligible = proposal.get("eligible_voter_ids", [])
    if not isinstance(quorum, int) or isinstance(quorum, bool) or quorum < 1 or quorum > 5000: raise ValueError("invalid quorum")
    if not isinstance(eligible, list) or len(eligible) > 5000: raise ValueError("invalid electorate")
    eligible_ids = {safe_identifier(x, "eligible_voter_id") for x in eligible}
    accepted = {}; rejected = []
    for position, vote in enumerate(votes):
        if not isinstance(vote, dict): raise ValueError("vote invalid")
        voter = safe_identifier(vote.get("voter_id"), "voter_id")
        choice = vote.get("choice")
        if voter not in eligible_ids or voter == proposer_id or choice not in {"approve", "reject", "abstain"} or voter in accepted:
            rejected.append(position); continue
        accepted[voter] = choice
    counts = Counter(accepted.values())
    participating = counts["approve"] + counts["reject"]
    status = "approved" if participating >= quorum and counts["approve"] > counts["reject"] else "rejected" if participating >= quorum else "pending"
    return {"feature_id": feature_id, "resource": resource, "proposal_id": proposal_id, "reviewed_by": actor_id, "status": status, "quorum": quorum, "counts": {k: counts[k] for k in ("approve", "reject", "abstain")}, "accepted_vote_count": len(accepted), "rejected_vote_positions": tuple(rejected), "separation_of_duties": True, "decision_executed": False, "requires_apply_permission": True, "executed": False, "auditable": True}


def _impact(feature_id: str, resource: str, observations: list[dict[str, Any]], actor: dict[str, Any]) -> dict[str, Any]:
    actor_id = authorize(actor, f"impact:read:{resource}")
    bounded_json(observations, maximum_bytes=524288, reject_secrets=True)
    if not isinstance(observations, list) or len(observations) > 10000: raise ValueError("observations invalid")
    grouped: dict[str, dict[str, list[float]]] = {}
    for row in observations:
        if not isinstance(row, dict): raise ValueError("observation invalid")
        metric = safe_identifier(row.get("metric"), "metric")
        period = row.get("period")
        value = row.get("value")
        if period not in {"baseline", "current"} or isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value): raise ValueError("observation fields invalid")
        grouped.setdefault(metric, {"baseline": [], "current": []})[period].append(float(value))
    metrics = []
    for metric, periods in sorted(grouped.items()):
        if not periods["baseline"] or not periods["current"]: continue
        baseline_scale = max(abs(value) for value in periods["baseline"])
        current_scale = max(abs(value) for value in periods["current"])
        baseline = 0.0 if baseline_scale == 0 else baseline_scale * (math.fsum(value / baseline_scale for value in periods["baseline"]) / len(periods["baseline"]))
        current = 0.0 if current_scale == 0 else current_scale * (math.fsum(value / current_scale for value in periods["current"]) / len(periods["current"]))
        change = current - baseline
        percent_value = None if baseline == 0 else change / abs(baseline) * 100
        if not all(math.isfinite(value) for value in (baseline, current, change)) or (percent_value is not None and not math.isfinite(percent_value)): raise ValueError("derived impact metric outside finite limits")
        percent = None if percent_value is None else round(percent_value, 2)
        metrics.append({"metric": metric, "baseline_mean": round(baseline, 4), "current_mean": round(current, 4), "absolute_change": round(change, 4), "percent_change": percent, "sample_size": len(periods["baseline"]) + len(periods["current"]), "direction": "up" if change > 0 else "down" if change < 0 else "flat"})
    return {"feature_id": feature_id, "resource": resource, "analysed_by": actor_id, "observation_count": len(observations), "comparable_metric_count": len(metrics), "metrics": tuple(metrics), "causality_claimed": False, "personal_data_exposed": False, "executed": False, "auditable": True}


def _make_api(index: int, resource: str, family: str) -> Callable[..., dict[str, Any]]:
    if family == "quality":
        def operation(records, *, actor, threshold=90): return _review_quality(IDS[index], resource, records, actor, threshold)
        operation.__name__ = f"review_{resource}_quality"
    elif family == "sandbox":
        def operation(request, *, actor): return _run_sandbox(IDS[index], resource, request, actor)
        operation.__name__ = f"run_{resource}_isolated_sandbox"
    elif family == "governance":
        def operation(proposal, votes, *, actor): return _governance(IDS[index], resource, proposal, votes, actor)
        operation.__name__ = f"review_{resource}_proposal_governance"
    else:
        def operation(observations, *, actor): return _impact(IDS[index], resource, observations, actor)
        operation.__name__ = f"measure_{resource}_impact"
    operation.__doc__ = f"Pure {family} engine for {resource}."
    return operation


QUALITY_APIS = tuple(_make_api(i, resource, "quality") for i, resource in enumerate(QUALITY_RESOURCES))
SANDBOX_APIS = tuple(_make_api(10 + i, resource, "sandbox") for i, resource in enumerate(SANDBOX_RESOURCES))
GOVERNANCE_APIS = tuple(_make_api(27 + i, resource, "governance") for i, resource in enumerate(GOVERNANCE_RESOURCES))
IMPACT_APIS = tuple(_make_api(43 + i, resource, "impact") for i, resource in enumerate(IMPACT_RESOURCES))
ALL_APIS = QUALITY_APIS + SANDBOX_APIS + GOVERNANCE_APIS + IMPACT_APIS
globals().update({api.__name__: api for api in ALL_APIS})

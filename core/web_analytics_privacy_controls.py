"""Verified Web analytics/privacy controls for roadmap future-1177..1196.

The functions are deterministic contracts: they validate input, return an
actionable plan or report, and never mutate the caller's objects.
"""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
from collections import defaultdict, deque


def analytics_continuous_accessibility(snapshots, minimum_score=90):
    if not isinstance(snapshots, list) or not 0 <= minimum_score <= 100:
        raise ValueError("invalid accessibility audit")
    findings = []
    for snapshot in snapshots:
        if not isinstance(snapshot, dict) or not snapshot.get("view_id"):
            raise ValueError("accessibility snapshot requires view_id")
        rules = {
            "label_coverage": snapshot.get("label_coverage", 0),
            "keyboard_coverage": snapshot.get("keyboard_coverage", 0),
            "contrast_score": snapshot.get("contrast_score", 0),
        }
        if any(not isinstance(value, (int, float)) or not 0 <= value <= 100 for value in rules.values()):
            raise ValueError("invalid accessibility score")
        score = round(sum(rules.values()) / len(rules), 2)
        findings.append({"view_id": snapshot["view_id"], "score": score, "passing": score >= minimum_score,
                         "failed_rules": sorted(key for key, value in rules.items() if value < minimum_score)})
    return {"continuous": True, "minimum_score": minimum_score, "findings": findings,
            "passing": all(item["passing"] for item in findings)}


def analytics_external_storage_connector(config, probe):
    if not isinstance(config, dict) or config.get("provider") not in {"s3", "gcs", "azure", "webdav"}:
        raise ValueError("unsupported analytics storage")
    if not str(config.get("bucket", "")).strip() or not isinstance(probe, dict):
        raise ValueError("storage bucket and probe required")
    encryption = config.get("encryption", "none")
    if encryption not in {"none", "provider", "customer_managed"}:
        raise ValueError("invalid storage encryption")
    checks = {name: probe.get(name) is True for name in ("connect", "read", "write")}
    return {"provider": config["provider"], "bucket": config["bucket"], "path": config.get("path", "/"),
            "encryption": encryption, "checks": checks, "healthy": all(checks.values()),
            "credentials_redacted": True, "connected": False}


def analytics_time_band_policies(policies, instant):
    now = _aware(instant)
    if not isinstance(policies, list):
        raise ValueError("invalid analytics policies")
    matched = []
    for policy in policies:
        if not isinstance(policy, dict) or not policy.get("id"):
            raise ValueError("policy id required")
        start, end = policy.get("start_hour"), policy.get("end_hour")
        if not all(isinstance(value, int) and 0 <= value < 24 for value in (start, end)):
            raise ValueError("invalid policy hours")
        weekdays = policy.get("weekdays", list(range(7)))
        if any(not isinstance(day, int) or day not in range(7) for day in weekdays):
            raise ValueError("invalid policy weekdays")
        inside = start <= now.hour < end if start < end else now.hour >= start or now.hour < end
        if now.weekday() in weekdays and inside:
            matched.append({"id": policy["id"], "actions": copy.deepcopy(policy.get("actions", [])),
                            "priority": int(policy.get("priority", 0))})
    matched.sort(key=lambda row: (-row["priority"], str(row["id"])))
    return {"at": _iso(now), "active": matched, "effective": matched[0] if matched else None}


def analytics_sustainable_growth_simulator(baseline, monthly_rate, months, limits):
    if not isinstance(baseline, dict) or not isinstance(months, int) or months < 1 or not 0 <= monthly_rate <= 1:
        raise ValueError("invalid growth simulation")
    required = {"users", "storage_gb", "requests"}
    if set(baseline) != required or not isinstance(limits, dict) or not required <= set(limits):
        raise ValueError("growth metrics or limits missing")
    if any(not isinstance(value, (int, float)) or value < 0 for value in list(baseline.values()) + [limits[k] for k in required]):
        raise ValueError("growth values must be non-negative")
    series, first_breach = [], None
    for month in range(months + 1):
        row = {key: round(value * ((1 + monthly_rate) ** month), 2) for key, value in baseline.items()}
        breached = sorted(key for key in required if row[key] > limits[key])
        series.append({"month": month, "metrics": row, "breached": breached})
        if breached and first_breach is None:
            first_breach = {"month": month, "metrics": breached}
    return {"series": series, "first_breach": first_breach, "sustainable": first_breach is None,
            "writes": 0}


def privacy_dependency_map(graph, roots):
    if not isinstance(graph, dict) or not isinstance(roots, list) or not roots:
        raise ValueError("invalid privacy dependency graph")
    if any(root not in graph for root in roots):
        raise ValueError("unknown dependency root")
    reached, queue = set(), deque(roots)
    while queue:
        node = queue.popleft()
        for child in graph.get(node, []):
            if child not in graph:
                raise ValueError("dangling dependency")
            if child not in reached and child not in roots:
                reached.add(child)
                queue.append(child)
    return {"roots": roots[:], "affected": sorted(reached), "count": len(reached), "applied": False}


def privacy_visual_conditional_rules(rules, facts):
    if not isinstance(rules, list) or not isinstance(facts, dict):
        raise ValueError("invalid privacy visual rules")
    operations = {"eq": lambda a, b: a == b, "gte": lambda a, b: a >= b, "lte": lambda a, b: a <= b,
                  "contains": lambda a, b: b in a}
    matches = []
    for rule in rules:
        operator = rule.get("operator")
        if operator not in operations or not rule.get("id") or rule.get("field") not in facts:
            raise ValueError("unsupported or incomplete visual rule")
        if operations[operator](facts[rule["field"]], rule.get("value")):
            matches.append({"id": rule["id"], "style": rule.get("style", "notice"),
                            "message": str(rule.get("message", ""))})
    return {"evaluated": len(rules), "matches": matches, "render_safe": True}


def privacy_unified_review_inbox(requests, reviewer_scopes):
    if not isinstance(requests, list) or not isinstance(reviewer_scopes, (list, tuple, set)):
        raise ValueError("invalid privacy review inbox")
    scopes = set(reviewer_scopes)
    inbox = []
    for request in requests:
        if request.get("status") != "pending" or request.get("scope") not in scopes:
            continue
        if not request.get("id") or request.get("risk") not in {"low", "medium", "high", "critical"}:
            raise ValueError("invalid review request")
        inbox.append({key: copy.deepcopy(request.get(key)) for key in ("id", "scope", "risk", "created_at", "summary")})
    weight = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    inbox.sort(key=lambda row: (-weight[row["risk"]], str(row.get("created_at", "")), str(row["id"])))
    return {"items": inbox, "total": len(inbox), "scopes": sorted(scopes)}


def privacy_sensitive_change_detection(before, after, sensitive_fields):
    if not isinstance(before, dict) or not isinstance(after, dict) or not isinstance(sensitive_fields, (list, set, tuple)):
        raise ValueError("invalid privacy change detection")
    changed = sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key))
    sensitive = sorted(set(changed) & set(sensitive_fields))
    digest = hashlib.sha256(json.dumps({"before": before, "after": after}, sort_keys=True, default=str).encode()).hexdigest()
    return {"changed": changed, "sensitive": sensitive, "review_required": bool(sensitive),
            "change_digest": digest, "applied": False}


def privacy_automatic_decision_explanation(decision, signals, policy_version):
    if decision not in {"allow", "deny", "review"} or not isinstance(signals, list) or not str(policy_version):
        raise ValueError("invalid privacy decision")
    normalized = []
    for signal in signals:
        if not isinstance(signal, dict) or not signal.get("name") or not isinstance(signal.get("weight"), (int, float)):
            raise ValueError("invalid decision signal")
        normalized.append({"name": signal["name"], "effect": "supports" if signal["weight"] >= 0 else "opposes",
                           "weight": abs(signal["weight"]), "source": signal.get("source", "policy")})
    normalized.sort(key=lambda item: (-item["weight"], item["name"]))
    return {"decision": decision, "policy_version": str(policy_version), "factors": normalized,
            "appealable": decision != "allow", "human_review_available": True}


def privacy_data_quality_panel(records, required_fields, unique_field=None):
    if not isinstance(records, list) or not isinstance(required_fields, (list, tuple, set)) or not required_fields:
        raise ValueError("invalid privacy data quality input")
    issues, seen = [], set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError("privacy record must be an object")
        for field in required_fields:
            if record.get(field) in (None, ""):
                issues.append({"row": index, "field": field, "issue": "missing"})
        if unique_field:
            value = record.get(unique_field)
            if value in seen and value is not None:
                issues.append({"row": index, "field": unique_field, "issue": "duplicate"})
            seen.add(value)
    checks = max(1, len(records) * len(required_fields))
    return {"records": len(records), "issues": issues, "score": max(0, round(100 * (1 - len(issues) / checks), 2)),
            "source_mutated": False}


def privacy_import_preview(rows, mapping, allowed_fields):
    if not isinstance(rows, list) or not isinstance(mapping, dict) or not isinstance(allowed_fields, (list, set, tuple)):
        raise ValueError("invalid privacy import")
    if set(mapping.values()) - set(allowed_fields):
        raise ValueError("mapping contains forbidden target")
    preview, errors = [], []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append({"row": index, "error": "not_object"})
            continue
        transformed = {target: copy.deepcopy(row[source]) for source, target in mapping.items() if source in row}
        missing = sorted(target for target in mapping.values() if target not in transformed)
        if missing:
            errors.append({"row": index, "error": "missing_mapped_fields", "fields": missing})
        preview.append(transformed)
    return {"preview": preview, "errors": errors, "importable": not errors, "imported": False}


def privacy_collaboration_comments(comments, author, message, target, mentions=()):
    if not isinstance(comments, list) or not str(author) or not str(message).strip() or not str(target):
        raise ValueError("invalid privacy comment")
    if any(not str(item) for item in mentions):
        raise ValueError("invalid comment mention")
    result = copy.deepcopy(comments)
    identifier = hashlib.sha256(f"{target}|{author}|{message}|{len(result)}".encode()).hexdigest()[:16]
    result.append({"id": identifier, "author": author, "message": message.strip(), "target": target,
                   "mentions": sorted(set(mentions)), "resolved": False})
    return {"comments": result, "created_id": identifier, "notifications": sorted(set(mentions))}


def privacy_smart_tags(records, taxonomy):
    if not isinstance(records, list) or not isinstance(taxonomy, dict):
        raise ValueError("invalid privacy tagging")
    prepared = {tag: {str(term).lower() for term in terms} for tag, terms in taxonomy.items()}
    tagged = []
    for record in records:
        if not record.get("id"):
            raise ValueError("record id required")
        text = " ".join(str(record.get(key, "")) for key in ("title", "description", "type")).lower()
        tags = sorted(tag for tag, terms in prepared.items() if any(term in text for term in terms))
        tagged.append({"id": record["id"], "suggested_tags": tags, "confirmed": False})
    return {"records": tagged, "taxonomy_version": _digest(taxonomy), "automatic_writes": 0}


def privacy_configurable_activity_summary(events, dimensions, include_counts=True):
    allowed = {"action", "scope", "status", "day"}
    if not isinstance(events, list) or not dimensions or set(dimensions) - allowed:
        raise ValueError("invalid privacy activity summary")
    groups = defaultdict(int)
    for event in events:
        values = []
        for dimension in dimensions:
            value = str(event.get("at", ""))[:10] if dimension == "day" else event.get(dimension, "unknown")
            values.append(value)
        groups[tuple(values)] += 1
    rows = [{**dict(zip(dimensions, key)), **({"count": count} if include_counts else {})}
            for key, count in sorted(groups.items(), key=lambda item: str(item[0]))]
    return {"dimensions": list(dimensions), "rows": rows, "total_events": len(events), "identities_included": False}


def privacy_expiry_alerts(resources, instant, notice_days=(30, 7, 1)):
    now = _aware(instant)
    if not isinstance(resources, list) or any(not isinstance(day, int) or day < 0 for day in notice_days):
        raise ValueError("invalid privacy expiry alerts")
    alerts = []
    for resource in resources:
        if not resource.get("id") or not resource.get("expires_at"):
            raise ValueError("expiring resource incomplete")
        remaining = (_aware(resource["expires_at"]) - now).total_seconds() / 86400
        level = "expired" if remaining < 0 else next((f"due_{day}d" for day in sorted(notice_days) if remaining <= day), None)
        if level:
            alerts.append({"id": resource["id"], "level": level, "days_remaining": max(-1, int(remaining)),
                           "owner": resource.get("owner")})
    return {"alerts": alerts, "generated_at": _iso(now), "delivered": False}


def privacy_reversible_emergency_mode(state, enable, actor, reason, instant):
    if not isinstance(state, dict) or not isinstance(enable, bool) or not str(actor) or len(str(reason).strip()) < 8:
        raise ValueError("invalid privacy emergency transition")
    result = copy.deepcopy(state)
    history = result.setdefault("history", [])
    previous = bool(result.get("enabled", False))
    result.update({"enabled": enable, "changed_by": actor, "changed_at": _iso(_aware(instant))})
    history.append({"from": previous, "to": enable, "actor": actor, "reason": reason.strip(),
                    "at": result["changed_at"], "rollback": {"enabled": previous}})
    return result


def privacy_effective_permission_history(events, subject, resource, instant=None):
    if not isinstance(events, list) or not str(subject) or not str(resource):
        raise ValueError("invalid permission history")
    cutoff = _aware(instant) if instant is not None else None
    relevant = []
    effective = set()
    for event in sorted(events, key=lambda row: str(row.get("at", ""))):
        if event.get("subject") != subject or event.get("resource") != resource:
            continue
        event_time = _aware(event.get("at"))
        if cutoff and event_time > cutoff:
            continue
        if event.get("action") not in {"grant", "revoke"} or not event.get("permission"):
            raise ValueError("invalid permission event")
        effective.discard(event["permission"]) if event["action"] == "revoke" else effective.add(event["permission"])
        relevant.append(copy.deepcopy(event))
    return {"subject": subject, "resource": resource, "effective": sorted(effective), "history": relevant}


def privacy_shared_goals(goals, contributions):
    if not isinstance(goals, list) or not isinstance(contributions, list):
        raise ValueError("invalid shared privacy goals")
    totals = defaultdict(float)
    for contribution in contributions:
        if not contribution.get("goal_id") or not isinstance(contribution.get("amount"), (int, float)) or contribution["amount"] < 0:
            raise ValueError("invalid goal contribution")
        totals[contribution["goal_id"]] += contribution["amount"]
    result = []
    for goal in goals:
        if not goal.get("id") or not isinstance(goal.get("target"), (int, float)) or goal["target"] <= 0:
            raise ValueError("invalid shared goal")
        progress = totals[goal["id"]]
        result.append({"id": goal["id"], "target": goal["target"], "progress": progress,
                       "percentage": round(min(100, 100 * progress / goal["target"]), 2),
                       "completed": progress >= goal["target"]})
    return {"goals": result, "contributors": len({row.get("actor") for row in contributions if row.get("actor")})}


def privacy_configuration_recommender(configuration, observations):
    if not isinstance(configuration, dict) or not isinstance(observations, dict):
        raise ValueError("invalid privacy configuration recommendation")
    recommendations = []
    retention = configuration.get("retention_days")
    if not isinstance(retention, int) or retention > observations.get("required_retention_days", 30):
        recommendations.append({"setting": "retention_days", "value": observations.get("required_retention_days", 30),
                                "reason": "data_minimization", "automatic": False})
    if configuration.get("consent_version") != observations.get("current_consent_version"):
        recommendations.append({"setting": "consent_version", "value": observations.get("current_consent_version"),
                                "reason": "outdated_consent", "automatic": False})
    if configuration.get("audit_enabled") is not True:
        recommendations.append({"setting": "audit_enabled", "value": True, "reason": "accountability", "automatic": False})
    return {"recommendations": recommendations, "configuration_digest": _digest(configuration),
            "applied": False}


def privacy_automatic_configuration_tests(configuration, test_cases):
    if not isinstance(configuration, dict) or not isinstance(test_cases, list):
        raise ValueError("invalid privacy configuration tests")
    operators = {"eq": lambda a, b: a == b, "lte": lambda a, b: a <= b, "gte": lambda a, b: a >= b,
                 "in": lambda a, b: a in b}
    results = []
    for case in test_cases:
        if not case.get("id") or case.get("operator") not in operators or case.get("field") not in configuration:
            raise ValueError("invalid configuration test case")
        try:
            passed = bool(operators[case["operator"]](configuration[case["field"]], case.get("expected")))
        except TypeError as exc:
            raise ValueError("incompatible configuration test values") from exc
        results.append({"id": case["id"], "passed": passed, "field": case["field"]})
    return {"results": results, "passed": all(row["passed"] for row in results), "executed": len(results),
            "writes": 0}


def _aware(value):
    if isinstance(value, str):
        value = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, dt.datetime) or value.tzinfo is None:
        raise ValueError("timezone-aware datetime required")
    return value.astimezone(dt.timezone.utc)


def _iso(value):
    return _aware(value).isoformat().replace("+00:00", "Z")


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()

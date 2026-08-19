"""Concrete offline-mode contracts for Telegram WebApp roadmap items 1822..1841.

The operations are deliberately pure: the Mini App can run them against its local
store and later persist/synchronise their returned state through the protected API.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import re


def _text(value, name, limit=512):
    clean = " ".join(str(value or "").split())
    if not clean or len(clean) > limit:
        raise ValueError(f"invalid {name}")
    return clean


def _items(value, name, limit=500):
    if not isinstance(value, list) or len(value) > limit:
        raise ValueError(f"invalid {name}")
    return value


def _iso(value, name="datetime"):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid {name}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _now(value=None):
    return _iso(value, "now") if value else datetime.now(timezone.utc)


def explain_offline_decision(trace):  # future-1822
    trace = dict(trace or {})
    decision = _text(trace.get("decision"), "decision", 100)
    factors = _items(trace.get("factors", []), "factors", 30)
    normalized = []
    for factor in factors:
        name = _text(factor.get("name"), "factor name", 80)
        weight = float(factor.get("weight", 0))
        if not -1 <= weight <= 1:
            raise ValueError("factor weight out of range")
        normalized.append({"name": name, "weight": weight, "evidence": str(factor.get("evidence") or "")[:240]})
    normalized.sort(key=lambda item: abs(item["weight"]), reverse=True)
    return {"decision": decision, "summary": f"{decision}: {len(normalized)} factores locales", "factors": normalized, "offline": True}


def offline_data_quality(records, required_fields):  # future-1823
    rows = _items(records, "records")
    fields = [_text(field, "required field", 80) for field in _items(required_fields, "required_fields", 30)]
    issues = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            issues.append({"row": index, "issue": "not_an_object"}); continue
        missing = [field for field in fields if row.get(field) in (None, "")]
        if missing:
            issues.append({"row": index, "issue": "missing_fields", "fields": missing})
    valid = len(rows) - len({issue["row"] for issue in issues})
    return {"total": len(rows), "valid": valid, "score": round(valid * 100 / len(rows), 2) if rows else 100.0, "issues": issues}


def preview_offline_import(records, allowed_fields):  # future-1824
    rows = _items(records, "records")
    allowed = {_text(field, "allowed field", 80) for field in _items(allowed_fields, "allowed_fields", 60)}
    if not allowed:
        raise ValueError("allowed_fields required")
    preview, rejected = [], []
    for index, row in enumerate(rows):
        if not isinstance(row, dict): rejected.append({"row": index, "reason": "not_an_object"}); continue
        unknown = sorted(set(row) - allowed)
        if unknown: rejected.append({"row": index, "reason": "unknown_fields", "fields": unknown}); continue
        preview.append(deepcopy(row))
    digest = hashlib.sha256(json.dumps(preview, sort_keys=True, default=str).encode()).hexdigest()
    return {"preview": preview, "accepted": len(preview), "rejected": rejected, "commit_token": digest, "committed": False}


def add_offline_comment(document, actor_id, body, created_at=None):  # future-1825
    state = deepcopy(dict(document or {})); comments = _items(state.setdefault("comments", []), "comments", 999)
    actor = _text(actor_id, "actor_id", 80); content = _text(body, "comment", 1000); stamp = _now(created_at).isoformat()
    comment_id = hashlib.sha256(f"{actor}|{stamp}|{content}".encode()).hexdigest()[:20]
    comment = {"id": comment_id, "actor_id": actor, "body": content, "created_at": stamp, "pending_sync": True}
    comments.append(comment); state["comments"] = comments
    return {"document": state, "comment": comment}


def offline_smart_tags(items, vocabulary):  # future-1826
    vocab = {_text(tag, "tag", 40).casefold() for tag in _items(vocabulary, "vocabulary", 200)}
    result = []
    for item in _items(items, "items"):
        text = f"{item.get('title', '')} {item.get('text', '')}".casefold()
        tags = sorted(tag for tag in vocab if re.search(rf"(?<!\w){re.escape(tag)}(?!\w)", text))
        result.append({"id": _text(item.get("id"), "item id", 100), "tags": tags, "confidence": round(min(1, len(tags) / 3), 2)})
    return {"items": result, "vocabulary_size": len(vocab), "model": "offline-exact-v1"}


def offline_activity_digest(events, categories=None):  # future-1827
    allowed = set(categories or [])
    counts, actors = Counter(), set()
    for event in _items(events, "events", 2000):
        category = _text(event.get("category"), "category", 80)
        if allowed and category not in allowed: continue
        counts[category] += 1
        if event.get("actor_id") is not None: actors.add(str(event["actor_id"]))
    return {"total": sum(counts.values()), "by_category": dict(sorted(counts.items())), "unique_actors": len(actors), "filters": sorted(allowed)}


def offline_expiry_alerts(resources, now=None, horizon_hours=72):  # future-1828
    current = _now(now); horizon = int(horizon_hours)
    if not 1 <= horizon <= 8760: raise ValueError("invalid horizon_hours")
    alerts = []
    for resource in _items(resources, "resources"):
        expires = _iso(resource.get("expires_at"), "expires_at"); hours = (expires-current).total_seconds()/3600
        if hours <= horizon:
            alerts.append({"id": _text(resource.get("id"), "resource id", 100), "expires_at": expires.isoformat(), "hours_remaining": round(hours, 2), "expired": hours <= 0})
    alerts.sort(key=lambda row: row["hours_remaining"])
    return {"alerts": alerts, "horizon_hours": horizon}


def open_offline_emergency(state, reason, actor_id, now=None):  # future-1829
    current = deepcopy(dict(state or {}))
    if current.get("emergency", {}).get("active"): raise ValueError("emergency already active")
    snapshot = deepcopy(current); snapshot.pop("emergency", None)
    token = hashlib.sha256(json.dumps(snapshot, sort_keys=True, default=str).encode()).hexdigest()
    current["emergency"] = {"active": True, "reason": _text(reason, "reason", 300), "actor_id": _text(actor_id, "actor_id", 80), "started_at": _now(now).isoformat(), "restore_token": token}
    return {"state": current, "snapshot": snapshot, "restore_token": token}


def restore_offline_emergency(emergency_result, restore_token):
    result = dict(emergency_result or {})
    if not result.get("state", {}).get("emergency", {}).get("active") or restore_token != result.get("restore_token"):
        raise ValueError("invalid restore token")
    return {"state": deepcopy(result["snapshot"]), "restored": True}


def offline_permission_history(events, user_id):  # future-1830
    target = _text(user_id, "user_id", 80); history = []
    effective = set()
    for event in sorted(_items(events, "events", 2000), key=lambda row: str(row.get("at", ""))):
        if str(event.get("user_id")) != target: continue
        permission = _text(event.get("permission"), "permission", 80); action = event.get("action")
        if action == "grant": effective.add(permission)
        elif action == "revoke": effective.discard(permission)
        else: raise ValueError("invalid permission action")
        history.append({"at": _iso(event.get("at"), "event at").isoformat(), "permission": permission, "action": action, "effective": sorted(effective)})
    return {"user_id": target, "history": history, "effective_permissions": sorted(effective)}


def update_offline_shared_goal(goal, actor_id, delta, note=""):  # future-1831
    state = deepcopy(dict(goal or {})); target = float(state.get("target", 0)); progress = float(state.get("progress", 0)); change = float(delta)
    if target <= 0 or change == 0: raise ValueError("invalid goal update")
    progress = max(0, min(target, progress + change)); state["progress"] = progress
    entry = {"actor_id": _text(actor_id, "actor_id", 80), "delta": change, "note": str(note or "")[:300]}
    state.setdefault("updates", []).append(entry)
    return {"goal": state, "percentage": round(progress * 100 / target, 2), "completed": progress >= target}


def recommend_offline_config(telemetry, current):  # future-1832
    data = dict(telemetry or {}); config = deepcopy(dict(current or {})); recommendations = []
    if int(data.get("failed_syncs", 0)) >= 3 and not config.get("retry_queue"):
        recommendations.append({"key": "retry_queue", "value": True, "reason": "repeated_sync_failures"})
    if int(data.get("storage_percent", 0)) >= 80:
        recommendations.append({"key": "cache_retention_days", "value": 7, "reason": "storage_pressure"})
    if int(data.get("conflicts", 0)) >= 2:
        recommendations.append({"key": "conflict_strategy", "value": "manual", "reason": "repeated_conflicts"})
    return {"recommendations": recommendations, "applied": False, "telemetry_anonymized": True}


def test_offline_config(config):  # future-1833
    cfg = dict(config or {}); checks = {
        "cache_limit": isinstance(cfg.get("cache_limit_mb"), int) and 10 <= cfg["cache_limit_mb"] <= 2048,
        "retry_limit": isinstance(cfg.get("retry_limit"), int) and 0 <= cfg["retry_limit"] <= 20,
        "conflict_strategy": cfg.get("conflict_strategy") in {"manual", "server", "client"},
    }
    return {"valid": all(checks.values()), "checks": checks, "sandboxed": True, "mutated": False}


def update_offline_consent(state, purpose, granted, version, now=None):  # future-1834
    current = deepcopy(dict(state or {})); key = _text(purpose, "purpose", 100); ver = _text(version, "version", 30)
    record = {"purpose": key, "granted": bool(granted), "version": ver, "recorded_at": _now(now).isoformat(), "pending_sync": True}
    current.setdefault("consents", {})[key] = record
    return {"state": current, "record": record}


def offline_task_navigation(tasks, role, completed=None):  # future-1835
    user_role = _text(role, "role", 50); done = {str(item) for item in (completed or [])}; visible = []
    for task in _items(tasks, "tasks", 200):
        roles = {str(item) for item in task.get("roles", [])}
        if roles and user_role not in roles: continue
        task_id = _text(task.get("id"), "task id", 80)
        dependencies = {str(item) for item in task.get("depends_on", [])}
        visible.append({"id": task_id, "title": _text(task.get("title"), "task title", 150), "ready": dependencies <= done, "blocked_by": sorted(dependencies-done)})
    return {"role": user_role, "tasks": visible, "next": next((task["id"] for task in visible if task["ready"] and task["id"] not in done), None)}


def sync_offline_devices(local, remote):  # future-1836
    left, right = dict(local or {}), dict(remote or {}); merged, conflicts = {}, []
    for key in sorted(set(left) | set(right)):
        a, b = left.get(key), right.get(key)
        if a is None: merged[key] = deepcopy(b)
        elif b is None: merged[key] = deepcopy(a)
        elif a.get("version") == b.get("version") and a.get("value") != b.get("value"):
            conflicts.append({"key": key, "local": deepcopy(a), "remote": deepcopy(b)})
        else: merged[key] = deepcopy(a if int(a.get("version", 0)) > int(b.get("version", 0)) else b)
    return {"merged": merged, "conflicts": conflicts, "sync_complete": not conflicts}


def detect_offline_duplicates(records, fields):  # future-1837
    keys = [_text(field, "field", 80) for field in _items(fields, "fields", 20)]; seen, groups = {}, defaultdict(list)
    if not keys: raise ValueError("fields required")
    for index, row in enumerate(_items(records, "records")):
        signature = tuple(str(row.get(field, "")).strip().casefold() for field in keys)
        groups[signature].append(index)
    duplicates = [{"rows": rows, "signature": list(signature)} for signature, rows in groups.items() if len(rows) > 1]
    return {"duplicates": duplicates, "duplicate_rows": sum(len(item["rows"])-1 for item in duplicates), "fields": keys}


def offline_adaptive_quota(usage, base_limit):  # future-1838
    samples = [max(0, float(value)) for value in _items(usage, "usage", 1000)]; base = int(base_limit)
    if base <= 0: raise ValueError("invalid base_limit")
    average = sum(samples)/len(samples) if samples else 0; peak = max(samples, default=0)
    suggested = min(base*2, max(base//2, int(max(average*1.25, peak))))
    return {"base_limit": base, "suggested_limit": suggested, "average_usage": round(average, 2), "peak_usage": peak, "offline_estimate": True}


def offline_community_impact(events):  # future-1839
    totals = Counter(); contributors = set()
    for event in _items(events, "events", 5000):
        metric = _text(event.get("metric"), "metric", 80); value = float(event.get("value", 0))
        totals[metric] += value
        if event.get("actor_id") is not None: contributors.add(str(event["actor_id"]))
    return {"metrics": dict(sorted(totals.items())), "contributors": len(contributors), "event_count": len(events), "privacy": "aggregate_only"}


def review_offline_translation(entry, reviewer_id, decision, suggestion=None):  # future-1840
    state = deepcopy(dict(entry or {})); action = str(decision or "")
    if action not in {"approve", "reject", "suggest"}: raise ValueError("invalid review decision")
    if action == "suggest": state["suggestion"] = _text(suggestion, "suggestion", 2000)
    state["review"] = {"reviewer_id": _text(reviewer_id, "reviewer_id", 80), "decision": action, "pending_sync": True}
    state["status"] = "approved" if action == "approve" else "changes_requested"
    return state


def group_offline_notifications(notifications):  # future-1841
    groups = defaultdict(list)
    for notification in _items(notifications, "notifications", 1000):
        context = _text(notification.get("context"), "context", 100)
        groups[context].append({"id": _text(notification.get("id"), "notification id", 100), "title": _text(notification.get("title"), "title", 200), "read": bool(notification.get("read"))})
    result = []
    for context in sorted(groups):
        rows = groups[context]; result.append({"context": context, "notifications": rows, "unread": sum(not row["read"] for row in rows)})
    return {"groups": result, "total": len(notifications), "unread": sum(group["unread"] for group in result)}

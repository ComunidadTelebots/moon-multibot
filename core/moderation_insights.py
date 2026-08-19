"""Deterministic moderation diagnostics used by the group Hub.

The helpers are deliberately side-effect free: the route owns persistence and
authorization, while this module only reduces already-authorized group state.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone


def build_snapshot(suite_state, warnings=None, bans=None, spam_events=None):
    suite_state = suite_state if isinstance(suite_state, dict) else {}
    config = suite_state.get("config") if isinstance(suite_state.get("config"), dict) else {}
    warnings = warnings if isinstance(warnings, dict) else {}
    bans = bans if isinstance(bans, dict) else {}
    spam_events = spam_events if isinstance(spam_events, list) else []
    pending_reports = sum(1 for row in suite_state.get("reports", [])
                          if isinstance(row, dict) and row.get("status") == "pending")
    pending_consensus = sum(1 for row in suite_state.get("consensus", [])
                            if isinstance(row, dict) and row.get("status") == "pending")
    active_sections = sorted(
        name for name, value in config.items()
        if isinstance(value, dict) and value.get("enabled") is True
    )
    def count(value):
        try:
            return max(0, int(value or 0))
        except (TypeError, ValueError):
            return 0

    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "active_sections": active_sections,
        "warning_users": sum(1 for value in warnings.values() if count(value) > 0),
        "warning_total": sum(count(value) for value in warnings.values()),
        "local_bans": len({str(value) for value in bans.get("users", [])}),
        "spam_events": len(spam_events),
        "pending_reports": pending_reports,
        "pending_consensus": pending_consensus,
        "quarantined_users": len(suite_state.get("quarantine", {})),
        "raid_active": bool((suite_state.get("raid") or {}).get("active")),
    }


def compare_snapshots(previous, current):
    previous = previous if isinstance(previous, dict) else {}
    current = current if isinstance(current, dict) else {}
    numeric = ("warning_users", "warning_total", "local_bans", "spam_events",
               "pending_reports", "pending_consensus", "quarantined_users")
    delta = {key: int(current.get(key, 0)) - int(previous.get(key, 0)) for key in numeric}
    before, after = set(previous.get("active_sections", [])), set(current.get("active_sections", []))
    return {
        "delta": delta,
        "enabled_sections": sorted(after - before),
        "disabled_sections": sorted(before - after),
        "raid_changed": bool(previous) and bool(previous.get("raid_active")) != bool(current.get("raid_active")),
    }


def diagnose(snapshot, comparison=None):
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    delta = (comparison or {}).get("delta", {})
    alerts = []

    def add(code, severity, title, detail):
        alerts.append({"code": code, "severity": severity, "title": title, "detail": detail})

    if snapshot.get("raid_active"):
        add("raid_active", "critical", "Escudo anti-raid activo", "Se ha detectado una entrada coordinada en curso.")
    if int(snapshot.get("pending_reports", 0)) >= 5:
        add("reports_queue", "high", "Reportes acumulados", "Hay cinco o más reportes pendientes de revisión.")
    if int(snapshot.get("pending_consensus", 0)):
        add("consensus_waiting", "medium", "Decisiones esperando votos", "Existen propuestas administrativas sin resolver.")
    if int(delta.get("spam_events", 0)) >= 10:
        add("spam_spike", "high", "Aumento de spam", "Los eventos de spam crecieron en diez o más desde la captura anterior.")
    if int(delta.get("warning_total", 0)) >= 5:
        add("warning_spike", "medium", "Aumento de avisos", "Los avisos crecieron rápidamente desde la captura anterior.")
    if not snapshot.get("active_sections"):
        add("no_protection", "high", "Protecciones desactivadas", "No hay módulos configurables de protección activos.")
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    alerts.sort(key=lambda row: (severity_order.get(row["severity"], 9), row["code"]))
    return {"healthy": not any(row["severity"] in ("critical", "high") for row in alerts),
            "alerts": alerts, "alert_count": len(alerts)}


def signed_export(chat_id, snapshots, secret):
    safe_snapshots = [dict(row) for row in snapshots[-30:] if isinstance(row, dict)]
    payload = {"schema": "moonbot.moderation-history.v1", "chat_id": str(chat_id),
               "exported_at": datetime.now(timezone.utc).isoformat(), "snapshots": safe_snapshots}
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    key = hashlib.sha256((str(secret) + ":moderation-export").encode("utf-8")).digest()
    signature = hmac.new(key, canonical.encode("utf-8"), hashlib.sha256).hexdigest()
    return {"payload": payload, "signature": signature, "algorithm": "HMAC-SHA256"}

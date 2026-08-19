"""One independently-addressable test contract per roadmap feature ID."""

from datetime import datetime, timezone
import unittest

import resource_incident_temporal_engines as engines
from resource_incident_temporal_manifest import MANIFEST


NOW = "2026-07-30T10:00:00Z"
EARLIER = "2026-07-30T08:00:00Z"


def _incident(index):
    return {
        "id": f"incident-{index}",
        "severity": "warning",
        "occurred_at": EARLIER,
        "evaluated_at": NOW,
        "notification_attempts": 4,
        "acknowledged": False,
        "evidence": {"reason": "timeout", "token": "must-not-leak"},
    }


def _escalation_test(index):
    def test(self):
        operation = engines.ESCALATION_APIS[index]
        first = operation(_incident(index))
        second = operation(_incident(index))
        self.assertEqual(first["feature_id"], engines.IDS[index])
        self.assertEqual(first["idempotency_key"], second["idempotency_key"])
        self.assertEqual(first["state"], "escalated")
        self.assertEqual(first["evidence"]["token"], "[REDACTED]")
        self.assertTrue(first["should_notify"])
        self.assertFalse(first["executed"])
        self.assertTrue(first["auditable"])
    return test


def _temporal_event(index, sequence):
    if index == 17:
        entity_field, entity, kinds = "account_id", "account-1", ("login", "role_change")
    elif index == 18:
        entity_field, entity, kinds = "channel_id", "channel-1", ("associate", "permission_change")
    else:
        entity_field, entity, kinds = "campaign_id", "campaign-1", ("publish", "click_spike")
    return {
        "id": f"event-{index}-{sequence}",
        entity_field: entity,
        "kind": kinds[sequence],
        "occurred_at": f"2026-07-30T09:{sequence * 10:02d}:00Z",
        "confidence": 0.8 + sequence / 10,
    }


def _temporal_test(index):
    def test(self):
        operation = engines.TEMPORAL_APIS[index - 17]
        event_a = _temporal_event(index, 0)
        event_b = _temporal_event(index, 1)
        result = operation([event_a, event_a.copy(), event_b], window_minutes=30, min_events=2)
        self.assertEqual(result["feature_id"], engines.IDS[index])
        self.assertEqual(result["input_count"], 3)
        self.assertEqual(result["unique_event_count"], 2)
        self.assertEqual(result["cluster_count"], 1)
        self.assertEqual(result["clusters"][0]["event_ids"], (event_a["id"], event_b["id"]))
        self.assertFalse(result["executed"])
        self.assertTrue(result["auditable"])
    return test


class ResourceIncidentTemporalPerIdTests(unittest.TestCase):
    pass


for _index, _feature_id in enumerate(engines.IDS):
    _factory = _escalation_test if _index < 17 else _temporal_test
    setattr(
        ResourceIncidentTemporalPerIdTests,
        f"test_{_feature_id.replace('-', '_')}",
        _factory(_index),
    )


class ResourceIncidentTemporalInvariantTests(unittest.TestCase):
    def test_manifest_has_complete_contracts(self):
        self.assertEqual(len(MANIFEST), 20)
        self.assertEqual({entry["id"] for entry in MANIFEST}, set(engines.IDS))
        for entry in MANIFEST:
            self.assertEqual(
                set(entry),
                {"id", "title", "capability", "module", "api", "test", "preflight"},
            )

    def test_escalation_rejects_naive_or_future_timestamps(self):
        invalid = _incident(0)
        invalid["occurred_at"] = "2026-07-30T08:00:00"
        with self.assertRaises(ValueError):
            engines.escalate_temporary_roles_incident(invalid)
        invalid = _incident(0)
        invalid["occurred_at"] = "2026-07-31T08:00:00Z"
        with self.assertRaises(ValueError):
            engines.escalate_temporary_roles_incident(invalid)

    def test_acknowledged_incident_does_not_request_notification(self):
        incident = _incident(0)
        incident["acknowledged"] = True
        result = engines.escalate_temporary_roles_incident(incident)
        self.assertEqual(result["state"], "acknowledged")
        self.assertFalse(result["should_notify"])

    def test_temporal_correlation_rejects_wrong_resource_kind(self):
        event = _temporal_event(17, 0)
        event["kind"] = "click_spike"
        with self.assertRaises(ValueError):
            engines.correlate_creator_accounts([event, event])


if __name__ == "__main__":
    unittest.main()

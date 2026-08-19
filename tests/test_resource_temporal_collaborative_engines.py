"""Independently addressable tests for future-4862..future-4919."""

import unittest

import resource_temporal_collaborative_engines as engines
from resource_temporal_collaborative_manifest import MANIFEST


def _temporal_events(index):
    resource, entity_field, kinds = engines._TEMPORAL_SPECS[index]
    entity = f"{resource}-entity"
    first_kind, second_kind = sorted(kinds)[:2]
    first = {
        "id": f"event-{index}-a",
        entity_field: entity,
        "kind": first_kind,
        "occurred_at": "2026-07-30T10:00:00Z",
        "confidence": 0.8,
    }
    second = {
        "id": f"event-{index}-b",
        entity_field: entity,
        "kind": second_kind,
        "occurred_at": "2026-07-30T10:10:00Z",
        "confidence": 1.0,
    }
    return first, second


def _test_temporal(index):
    def test(self):
        first, second = _temporal_events(index)
        result = engines.TEMPORAL_APIS[index]([second, first, first.copy()], 30, 2)
        self.assertEqual(result["feature_id"], engines.IDS[index])
        self.assertEqual(result["unique_event_count"], 2)
        self.assertEqual(result["cluster_count"], 1)
        self.assertEqual(result["clusters"][0]["event_ids"], (first["id"], second["id"]))
        self.assertFalse(result["executed"])
        self.assertTrue(result["auditable"])
    return test


def _proposal(index):
    return {
        "id": f"proposal-{index}",
        "requested_by": "requester",
        "base_version": 3,
        "proposed_version": 4,
        "payload": {"change": "bounded", "secret": "must-not-leak"},
    }


def _reviews(index):
    _, roles, _, _ = engines._REVIEW_SPECS[index]
    first_role, second_role = sorted(roles)[:2]
    return [
        {
            "reviewer_id": "reviewer-a",
            "role": first_role,
            "decision": "approve",
            "comment": "verified",
            "reviewed_version": 4,
            "reviewed_at": "2026-07-30T10:00:00Z",
        },
        {
            "reviewer_id": "reviewer-b",
            "role": second_role,
            "decision": "approve",
            "comment": "verified independently",
            "reviewed_version": 4,
            "reviewed_at": "2026-07-30T10:01:00Z",
        },
    ]


def _test_review(index):
    def test(self):
        operation = engines.REVIEW_APIS[index]
        first = operation(_proposal(index), _reviews(index))
        second = operation(_proposal(index), _reviews(index))
        self.assertEqual(first["feature_id"], engines.IDS[13 + index])
        self.assertEqual(first["state"], "approved")
        self.assertTrue(first["can_apply"])
        self.assertEqual(first["review_key"], second["review_key"])
        self.assertEqual(first["payload"]["secret"], "[REDACTED]")
        self.assertFalse(first["executed"])
        self.assertTrue(first["auditable"])
    return test


class ResourceTemporalCollaborativePerIdTests(unittest.TestCase):
    pass


for _index, _feature_id in enumerate(engines.IDS):
    _factory = _test_temporal if _index < 13 else _test_review
    _factory_index = _index if _index < 13 else _index - 13
    setattr(
        ResourceTemporalCollaborativePerIdTests,
        f"test_{_feature_id.replace('-', '_')}",
        _factory(_factory_index),
    )


class ResourceTemporalCollaborativeInvariantTests(unittest.TestCase):
    def test_manifest_contract_is_complete(self):
        self.assertEqual(len(MANIFEST), 20)
        self.assertEqual({entry["id"] for entry in MANIFEST}, set(engines.IDS))
        for entry in MANIFEST:
            self.assertEqual(
                set(entry),
                {"id", "title", "capability", "module", "api", "test", "preflight"},
            )

    def test_review_rejects_self_review(self):
        review = _reviews(0)[0]
        review["reviewer_id"] = "requester"
        with self.assertRaises(ValueError):
            engines.review_administrative_sessions_collaboratively(_proposal(0), [review])

    def test_review_rejects_stale_version(self):
        review = _reviews(1)[0]
        review["reviewed_version"] = 3
        with self.assertRaises(ValueError):
            engines.review_community_profiles_collaboratively(_proposal(1), [review])

    def test_sensitive_review_rejection_has_veto(self):
        reviews = _reviews(4)
        reviews[0]["decision"] = "reject"
        result = engines.review_voice_notes_collaboratively(_proposal(4), reviews)
        self.assertEqual(result["state"], "rejected")
        self.assertFalse(result["can_apply"])

    def test_temporal_contract_rejects_wrong_kind(self):
        first, second = _temporal_events(0)
        second["kind"] = "captcha_failure"
        with self.assertRaises(ValueError):
            engines.correlate_editorial_articles([first, second])


if __name__ == "__main__":
    unittest.main()

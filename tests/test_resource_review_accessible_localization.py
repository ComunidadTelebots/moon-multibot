"""One independently addressable test for every ID in the 40-feature lot."""

import importlib
import unittest

import resource_collaborative_accessible_engines as combined
import resource_cultural_localization_engines as cultural
from resource_review_accessible_localization_manifest import MANIFEST


def _proposal(index):
    return {
        "id": f"proposal-{index}",
        "requested_by": "requester",
        "base_version": 7,
        "proposed_version": 8,
        "payload": {"change": "reviewed", "secret": "must-not-leak"},
    }


def _reviews(index):
    _, roles, _, _ = combined._REVIEW_SPECS[index]
    selected = sorted(roles)[:2]
    return [
        {
            "reviewer_id": f"reviewer-{position}",
            "role": role,
            "decision": "approve",
            "comment": "verified independently",
            "reviewed_version": 8,
            "reviewed_at": f"2026-07-30T11:0{position}:00Z",
        }
        for position, role in enumerate(selected)
    ]


def _test_review(index):
    def test(self):
        first = combined.REVIEW_APIS[index](_proposal(index), _reviews(index))
        second = combined.REVIEW_APIS[index](_proposal(index), _reviews(index))
        self.assertEqual(first["feature_id"], combined.IDS[index])
        self.assertEqual(first["state"], "approved")
        self.assertEqual(first["review_key"], second["review_key"])
        self.assertEqual(first["payload"]["secret"], "[REDACTED]")
        self.assertTrue(first["can_apply"])
        self.assertFalse(first["executed"])
    return test


def _test_explanation(index):
    def test(self):
        factor = combined._EXPLANATION_SPECS[index][3][0]
        decision = {
            "status": "warning",
            "reason_code": "threshold_exceeded",
            "factors": [{"code": factor, "value": "checked"}],
        }
        result = combined.EXPLANATION_APIS[index](
            decision,
            {"language": "es", "reading_level": "simple", "output_channel": "screen_reader"},
        )
        self.assertEqual(result["feature_id"], combined.IDS[10 + index])
        self.assertEqual(len(result["sections"]), 4)
        self.assertIn("Estado:", result["plain_text"])
        self.assertTrue(result["aria_label"])
        self.assertFalse(result["uses_colour_alone"])
        self.assertTrue(result["deterministic"])
    return test


REUSED_PAYLOADS = (
    {"display_name": "Creador", "bio": "Noticias tecnológicas", "handle": "creator"},
    {"title": "Canal", "username": "CanalOficial", "category": "tecnología"},
    {"name": "Campaña", "budget": 25.5, "currency": "EUR"},
    {"title": "Artículo", "body": "Contenido editorial verificado", "published_at": "2026-07-30T10:00:00Z"},
    {"alt_text": "Imagen informativa", "moderation_labels": ["safe"]},
    {"appeal_id": "appeal-1", "status": "pending", "reason": "Solicita revisión", "decided_at": None},
)


NEW_PAYLOADS = (
    {"host": "proxy.example.org", "port": 443, "latency_ms": 42},
    {"task_id": "task-1", "title": "Revisión", "status": "pending", "due_at": "2026-08-01T10:00:00Z"},
    {"rule_id": "rule-1", "name": "Antispam", "severity": "high", "enabled": True},
    {"language_code": "es", "users": 1200, "percentage": 62.5},
    {"translation_id": "translation-1", "source_locale": "es-ES", "target_locale": "en-US", "text": "Reviewed text", "community_reviewed": True},
    {"subject_id": "user-1", "state": "granted", "scopes": ["analytics", "profile"], "recorded_at": "2026-07-30T10:00:00Z"},
    {"message_id": "message-1", "reaction": "👍", "count": 1500, "observed_at": "2026-07-30T10:00:00Z"},
)


def _test_localization(index):
    def test(self):
        entry = MANIFEST[27 + index]
        module = importlib.import_module(entry["module"].removesuffix(".py"))
        operation = getattr(module, entry["api"])
        payload = REUSED_PAYLOADS[index] if index < 6 else NEW_PAYLOADS[index - 6]
        result = operation(payload, "es-ES")
        if "feature_id" in result:
            self.assertEqual(result["feature_id"], entry["id"])
            self.assertFalse(result["executed"])
            self.assertTrue(result["identifiers_preserved"])
        self.assertEqual(result["locale"], "es-ES")
        self.assertEqual(result["direction"], "ltr")
        self.assertTrue(result["resource"])
    return test


class ResourceReviewAccessibleLocalizationPerIdTests(unittest.TestCase):
    pass


for _index, _entry in enumerate(MANIFEST):
    if _index < 10:
        _test = _test_review(_index)
    elif _index < 27:
        _test = _test_explanation(_index - 10)
    else:
        _test = _test_localization(_index - 27)
    setattr(
        ResourceReviewAccessibleLocalizationPerIdTests,
        f"test_{_entry['id'].replace('-', '_')}",
        _test,
    )


class ResourceReviewAccessibleLocalizationInvariantTests(unittest.TestCase):
    def test_manifest_contract_is_complete(self):
        self.assertEqual(len(MANIFEST), 40)
        for entry in MANIFEST:
            self.assertEqual(
                set(entry),
                {"id", "title", "capability", "module", "api", "test", "preflight"},
            )
            module = importlib.import_module(entry["module"].removesuffix(".py"))
            self.assertTrue(callable(getattr(module, entry["api"])))

    def test_explanation_rejects_cross_resource_factor(self):
        with self.assertRaises(ValueError):
            combined.explain_quiet_hours_accessibly({
                "status": "warning",
                "reason_code": "bad_window",
                "factors": [{"code": "signature", "value": "invalid"}],
            })

    def test_localization_does_not_accept_naive_dates(self):
        payload = dict(NEW_PAYLOADS[1])
        payload["due_at"] = "2026-08-01T10:00:00"
        with self.assertRaises(ValueError):
            cultural.localize_persistent_task(payload, "es-ES")

    def test_localization_preserves_rtl_direction(self):
        result = cultural.localize_telegram_reaction(NEW_PAYLOADS[6], "ar")
        self.assertEqual(result["direction"], "rtl")

    def test_review_rejects_unauthorized_role(self):
        reviews = _reviews(0)
        reviews[0]["role"] = "viewer"
        with self.assertRaises(ValueError):
            combined.review_managed_bots_collaboratively(_proposal(0), reviews)


if __name__ == "__main__":
    unittest.main()

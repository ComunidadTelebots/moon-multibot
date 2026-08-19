import importlib
import math
import socket
import unittest
from unittest import mock

import resource_quality_sandbox_governance_impact_engines as engines
from resource_quality_sandbox_governance_impact_manifest import MANIFEST

MASTER = {"id": "master-1", "roles": ["master"], "scopes": []}
VIEWER = {"id": "viewer-1", "roles": ["viewer"], "scopes": []}


def _valid_quality(resource):
    common = {"id": "record-1"}
    values = {
        "managed_bots": {"username": "@CintiaBot", "enabled": True},
        "recurring_reminders": {"schedule": "daily", "enabled": True},
        "security_events": {"severity": "high", "occurred_at": "2026-07-30T10:00:00Z"},
        "regional_maps": {"language": "es", "user_count": 20},
        "backups": {"checksum": "a" * 64, "created_at": "2026-07-30T10:00:00Z"},
        "ai_learning_data": {"consent": True, "source": "group-1"},
        "rich_commands": {"command": "/help", "parse_mode": "HTML"},
        "hub_notifications": {"audience": "master", "created_at": "2026-07-30T10:00:00Z"},
        "cookie_policies": {"version": "v2", "effective_at": "2026-07-30T10:00:00Z"},
        "wayback_history": {"url": "https://example.org/page", "captured_at": "2026-07-30T10:00:00Z"},
    }
    return {**common, **values[resource]}


class PerFeatureTests(unittest.TestCase):
    pass


def _feature_test(index):
    def test(self):
        api = engines.ALL_APIS[index]
        resource = engines.QUALITY_RESOURCES[index] if index < 10 else engines.SANDBOX_RESOURCES[index - 10] if index < 27 else engines.GOVERNANCE_RESOURCES[index - 27] if index < 43 else engines.IMPACT_RESOURCES[index - 43]
        if index < 10:
            result = api([_valid_quality(resource)], actor=MASTER)
            self.assertEqual(result["quality_score"], 100)
            self.assertFalse(result["raw_values_exposed"])
        elif index < 27:
            result = api({"run_id": "run-1", "operation": "simulate", "inputs": {"item_id": "item-1"}, "budget": {"max_steps": 5, "max_items": 10, "timeout_ms": 500}}, actor=MASTER)
            self.assertFalse(result["network_access"])
            self.assertFalse(result["side_effects"])
        elif index < 43:
            proposal = {"proposal_id": "proposal-1", "proposer_id": "user-1", "opens_at": "2026-07-30T10:00:00Z", "closes_at": "2026-07-31T10:00:00Z", "quorum": 1, "eligible_voter_ids": ["user-1", "user-2"]}
            result = api(proposal, [{"voter_id": "user-2", "choice": "approve"}], actor=MASTER)
            self.assertEqual(result["status"], "approved")
            self.assertFalse(result["decision_executed"])
        else:
            result = api([{"metric": "success_rate", "period": "baseline", "value": 50}, {"metric": "success_rate", "period": "current", "value": 75}], actor=MASTER)
            self.assertEqual(result["metrics"][0]["percent_change"], 50.0)
            self.assertFalse(result["causality_claimed"])
        self.assertEqual(result["feature_id"], engines.IDS[index])
        self.assertFalse(result["executed"])
    return test


for _index, _id in enumerate(engines.IDS):
    setattr(PerFeatureTests, f"test_{_id.replace('-', '_')}", _feature_test(_index))


class SecurityContractTests(unittest.TestCase):
    def test_manifest_exact_and_callable(self):
        self.assertEqual([x["id"] for x in MANIFEST], [f"future-{n}" for n in range(5522, 5700, 3)])
        self.assertEqual(len({x["api"] for x in MANIFEST}), 60)
        self.assertTrue(all(x["roles"][0] == "master" and callable(getattr(importlib.import_module(x["module"][:-3]), x["api"])) for x in MANIFEST))

    def test_every_family_requires_authorization(self):
        with self.assertRaises(PermissionError): engines.QUALITY_APIS[0]([_valid_quality("managed_bots")], actor=VIEWER)
        with self.assertRaises(PermissionError): engines.SANDBOX_APIS[0]({"run_id": "r1", "operation": "simulate", "inputs": {}}, actor=VIEWER)
        with self.assertRaises(PermissionError): engines.GOVERNANCE_APIS[0]({}, [], actor=VIEWER)
        with self.assertRaises(PermissionError): engines.IMPACT_APIS[0]([], actor=VIEWER)

    def test_quality_does_not_reflect_xss_identifier(self):
        row = _valid_quality("managed_bots"); row["id"] = '<img src=x onerror=alert(1)>'
        result = engines.QUALITY_APIS[0]([row], actor=MASTER)
        self.assertEqual(result["results"][0]["record_id"], "invalid-at-0")
        self.assertNotIn("<img", str(result))

    def test_sandbox_rejects_secrets_and_never_touches_system(self):
        with self.assertRaises(ValueError): engines.SANDBOX_APIS[0]({"run_id": "r1", "operation": "simulate", "inputs": {"api_token": "secret"}}, actor=MASTER)
        with mock.patch("socket.create_connection") as network:
            result = engines.SANDBOX_APIS[0]({"run_id": "r1", "operation": "simulate", "inputs": {}}, actor=MASTER)
        network.assert_not_called(); self.assertFalse(result["network_access"])

    def test_governance_rejects_self_vote_duplicates_and_ineligible(self):
        proposal = {"proposal_id": "p1", "proposer_id": "u1", "opens_at": "2026-07-30T10:00:00Z", "closes_at": "2026-07-31T10:00:00Z", "quorum": 2, "eligible_voter_ids": ["u1", "u2"]}
        votes = [{"voter_id": "u1", "choice": "approve"}, {"voter_id": "u2", "choice": "approve"}, {"voter_id": "u2", "choice": "approve"}, {"voter_id": "u3", "choice": "approve"}]
        result = engines.GOVERNANCE_APIS[0](proposal, votes, actor=MASTER)
        self.assertEqual(result["accepted_vote_count"], 1)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(len(result["rejected_vote_positions"]), 3)

    def test_impact_rejects_nonfinite_and_secrets(self):
        with self.assertRaises(ValueError): engines.IMPACT_APIS[0]([{"metric": "x", "period": "current", "value": float("nan")}], actor=MASTER)
        with self.assertRaises(ValueError): engines.IMPACT_APIS[0]([{"metric": "x", "period": "current", "value": 1, "password": "x"}], actor=MASTER)

    def test_impact_never_emits_derived_nonfinite_values(self):
        observations = [{"metric": "x", "period": "baseline", "value": -1e308}, {"metric": "x", "period": "current", "value": 1e308}]
        with self.assertRaises(ValueError): engines.IMPACT_APIS[0](observations, actor=MASTER)
        stable = [{"metric": "x", "period": "baseline", "value": 1e308}, {"metric": "x", "period": "baseline", "value": 1e308}, {"metric": "x", "period": "current", "value": 1e308}]
        self.assertTrue(math.isfinite(engines.IMPACT_APIS[0](stable, actor=MASTER)["metrics"][0]["baseline_mean"]))

    def test_scoped_role_is_supported(self):
        actor = {"id": "admin-1", "roles": ["admin"], "scopes": ["impact:read:administrative_sessions"]}
        self.assertEqual(engines.IMPACT_APIS[0]([], actor=actor)["analysed_by"], "admin-1")


if __name__ == "__main__":
    unittest.main()

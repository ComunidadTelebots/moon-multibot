import ast
import hashlib
import hmac
import importlib
import inspect
import unittest
from datetime import datetime, timezone
from pathlib import Path

import webapp_support_subscription_moderation_operations as operations
from webapp_support_subscription_moderation_operations_manifest import FEATURES


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _case(api):
    if api.endswith("offline_continuity"): return ({"version": 1}, [{"id": "a", "action": "comment"}])
    if api.endswith("adaptive_trust"): return ({"mfa": True},)
    if api.endswith("campaign_plan"): return ({"name": "welcome", "audience": 10, "frequency_per_week": 1},)
    if api.endswith("intent"): return ("leer reglas",)
    if api.endswith("integration"): return ({"url": "https://example.com/hook", "methods": ["GET"], "kind": "events"},)
    if api.endswith("vault"): return ({"id": "v", "encrypted_envelope": "a" * 32, "nonce": "b" * 16},)
    if api.endswith("easy_read"): return ({"name": "Ayuda", "rules": ["Paso uno"]},)
    if api.endswith("sessions"): return ([{"id": "s1", "device": "web", "last_seen": "2026-01-01T00:00:00Z", "moderator": True}], "web")
    if api.endswith("editorial"): return ([{"id": "x", "topics": ["help"], "community_value": 1}], {"topics": ["help"]})
    if api.endswith("budget"): return ([], 10)
    if api.endswith("reputation"): return ([],)
    if api.endswith("localization"): return ({}, "es-ES")
    if api.endswith("communication_preferences"): return ({}, ["web"], {"start": 1, "end": 2})
    if api.endswith("onboarding"): return ({}, [])
    if api.endswith("governance"): return ({}, [], 1)
    if api.endswith("voice_control"): return ("mostrar ayuda", False)
    if api.endswith("federated_bridge"): return ([{"id": "peer", "endpoint": "https://example.com/api", "verified": True}], ["events"])
    if api.endswith("external_event"):
        body, key, at = "{}", "s" * 16, "2026-01-01T00:00:00+00:00"
        domain, kind = ("support", "ticket.updated") if api.startswith("support_") else ("subscription", "subscription.updated")
        signature = hmac.new(key.encode(), f"{domain}:{kind}.{at}.e.{body}".encode(), hashlib.sha256).hexdigest()
        return ({"id": "e", "type": kind, "body": body, "signature": signature, "at": at}, key)
    if api.endswith("digital_twin"): return ({}, [{"action": "add_event", "id": "e"}])
    if api.endswith("incidents"): return ([{"id": "e", "community_id": "c", "at": "2026-01-01T00:00:00Z"}], 30)
    if api.endswith("workflow"): return ({"name": "review", "steps": [{"id": "one", "action": "review"}]},)
    if api.endswith("delegation"): return ({"delegate_id": "u", "role": "community_moderator", "starts_at": "2026-01-01T00:00:00Z", "expires_at": "2026-01-02T00:00:00Z"}, "2026-01-01T12:00:00Z")
    if api.endswith("coordinated_abuse"): return ([{"actor_id": "u1", "target_id": "x", "kind": "spam"}],)
    if api.endswith("copilot"): return ({"facts": ["verified"], "allowed_actions": ["explain"]}, "What happened?")
    if api.endswith("capacity_forecast"): return ([10, 12, 14], 2, 3)
    if api.endswith("batch_plan"): return (["a", "b"], "tag", True)
    if api.endswith("workspace"): return ("team", [{"account_id": "u1", "role": "viewer"}], ["x"])
    if api.endswith("media"): return ([{"id": "m1", "mime": "image/png", "size": 100, "sha256": "a" * 64}],)
    if api.endswith("narrative_report"): return ({"frequency": "weekly", "format": "json"}, [])
    if api.endswith("alert_escalation"): return ([], [])
    raise AssertionError(api)


class WebappSupportSubscriptionModerationTests(unittest.TestCase):
    def test_manifest_exact_roles_callable(self):
        self.assertEqual([item["id"] for item in FEATURES], [f"future-{i}" for i in range(2282, 2342)])
        self.assertEqual(len({item["api"] for item in FEATURES}), 60)
        allowed = {"support_admin", "support_agent", "subscription_admin", "subscription_manager", "accessibility_admin", "accessibility_reviewer", "moderation_admin", "moderator"}
        for item in FEATURES:
            self.assertIn(item["role"], allowed)
            self.assertTrue(callable(getattr(operations, item["api"])))

    def test_all_features_execute_with_safe_samples(self):
        for item in FEATURES:
            with self.subTest(item["id"]):
                result = getattr(operations, item["api"])(*_case(item["api"]))
                self.assertIsNotNone(result)

    def test_plans_do_not_execute_or_persist(self):
        for api in ("subscription_batch_plan", "moderation_batch_plan"):
            result = getattr(operations, api)(["a"], "tag", False)
            self.assertFalse(result.get("executed", False))
            self.assertFalse(result.get("persisted", False))

    def test_no_io_dynamic_execution_or_html_sink(self):
        source = inspect.getsource(operations)
        tree = ast.parse(source)
        forbidden = {"requests", "urllib", "subprocess", "eval", "exec", "system"}
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        self.assertFalse(names & forbidden)
        self.assertNotIn("innerHTML", source)

    def test_external_event_signatures_are_domain_and_type_bound(self):
        event, key = _case("support_external_event")
        self.assertTrue(operations.support_external_event(event, key)["valid"])
        event["type"] = "ticket.resolved"
        self.assertFalse(operations.support_external_event(event, key)["valid"])
        event, key = _case("subscription_external_event")
        self.assertFalse(operations.support_external_event(event, key)["valid"])


def _make_test(feature):
    def test(self):
        result = getattr(operations, feature["api"])(*_case(feature["api"]))
        self.assertIsNotNone(result)
    test.__name__ = feature["test"]
    return test


for _feature in FEATURES:
    setattr(WebappSupportSubscriptionModerationTests, _feature["test"], _make_test(_feature))

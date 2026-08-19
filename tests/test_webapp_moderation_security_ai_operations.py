import ast
import hashlib
import hmac
import inspect
import unittest

import webapp_moderation_security_ai_operations as operations
from webapp_moderation_security_ai_operations_manifest import FEATURES
from tests.test_webapp_support_subscription_moderation_operations import _case


def _signed(context, kind):
    body, secret, at, event_id = "{}", "s" * 16, "2026-01-01T00:00:00+00:00", "evt"
    material = f"{context}.{at}.{event_id}.{body}"
    signature = hmac.new(secret.encode(), material.encode(), hashlib.sha256).hexdigest()
    return {"id": event_id, "type": kind, "body": body, "signature": signature, "at": at}, secret


def args_for(api):
    if api == "moderation_external_event": return _signed("moderation:moderation.alert", "moderation.alert")
    if api == "security_external_event": return _signed("security:security.alert", "security.alert")
    # Existing safe fixtures are suffix based. Correlation has the incidents contract.
    if api == "security_incident_correlation": return _case("security_incidents")
    return _case(api)


class WebappModerationSecurityAiTests(unittest.TestCase):
    def test_manifest_exact_roles_callable(self):
        self.assertEqual([x["id"] for x in FEATURES], [f"future-{i}" for i in range(2342, 2402)])
        self.assertEqual(len({x["api"] for x in FEATURES}), 60)
        allowed = {"moderation_admin", "moderator", "security_admin", "security_reviewer", "ai_admin", "ai_reviewer"}
        for feature in FEATURES:
            self.assertIn(feature["role"], allowed)
            self.assertTrue(callable(getattr(operations, feature["api"])))

    def test_all_features_execute(self):
        for feature in FEATURES:
            with self.subTest(feature["id"]):
                self.assertIsNotNone(getattr(operations, feature["api"])(*args_for(feature["api"])))

    def test_external_event_domains_and_tampering(self):
        event, secret = _signed("moderation:moderation.alert", "moderation.alert")
        self.assertTrue(operations.moderation_external_event(event, secret)["valid"])
        self.assertFalse(operations.security_external_event(event, secret)["valid"])
        event["body"] = '{"tampered":true}'
        self.assertFalse(operations.moderation_external_event(event, secret)["valid"])

    def test_actions_are_preview_only(self):
        for api in ("security_batch_plan", "ai_batch_plan"):
            result = getattr(operations, api)(["x"], "tag", False)
            self.assertFalse(result.get("executed", False))
            self.assertFalse(result.get("persisted", False))

    def test_no_io_dynamic_execution_or_html_sink(self):
        source = inspect.getsource(operations)
        ast.parse(source)
        for token in ("requests.", "urllib.request", "subprocess", "eval(", "exec(", "innerHTML", "os.system"):
            self.assertNotIn(token, source)


def make_test(feature):
    method_name = feature["test"].rsplit(".", 1)[-1]
    def test(self):
        self.assertIsNotNone(getattr(operations, feature["api"])(*args_for(feature["api"])))
    test.__name__ = method_name
    return test


for _feature in FEATURES:
    setattr(WebappModerationSecurityAiTests, _feature["test"].rsplit(".", 1)[-1], make_test(_feature))

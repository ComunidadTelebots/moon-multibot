import ast
import hashlib
import hmac
import inspect
import unittest

import webapp_ai_group_channel_operations as operations
from webapp_ai_group_channel_operations_manifest import FEATURES
from tests.test_webapp_support_subscription_moderation_operations import _case


def signed(context, kind):
    body, secret, at, event_id = "{}", "s" * 16, "2026-01-01T00:00:00+00:00", "evt"
    material = f"{context}.{at}.{event_id}.{body}"
    signature = hmac.new(secret.encode(), material.encode(), hashlib.sha256).hexdigest()
    return {"id": event_id, "type": kind, "body": body, "signature": signature, "at": at}, secret


def args_for(api):
    if api == "ai_external_event": return signed("ai:ai.reviewed", "ai.reviewed")
    if api == "moon_group_external_event": return signed("moon-group:group.updated", "group.updated")
    if api.endswith("incident_correlation"): return _case("community_incidents")
    return _case(api)


class WebappAiGroupChannelTests(unittest.TestCase):
    def test_manifest_exact_roles_callable(self):
        self.assertEqual([x["id"] for x in FEATURES], [f"future-{i}" for i in range(2402, 2462)])
        self.assertEqual(len({x["api"] for x in FEATURES}), 60)
        allowed = {"ai_admin", "ai_reviewer", "group_owner", "group_admin", "channel_owner", "channel_admin"}
        for feature in FEATURES:
            self.assertIn(feature["role"], allowed)
            self.assertTrue(callable(getattr(operations, feature["api"])))

    def test_all_features_execute(self):
        for feature in FEATURES:
            with self.subTest(feature["id"]):
                self.assertIsNotNone(getattr(operations, feature["api"])(*args_for(feature["api"])))

    def test_external_domains_and_tampering(self):
        event, secret = signed("ai:ai.reviewed", "ai.reviewed")
        self.assertTrue(operations.ai_external_event(event, secret)["valid"])
        group_event, group_secret = signed("moon-group:group.updated", "group.updated")
        self.assertTrue(operations.moon_group_external_event(group_event, group_secret)["valid"])
        self.assertFalse(operations.ai_external_event(group_event, group_secret)["valid"])
        group_event["body"] = '{"changed":true}'
        self.assertFalse(operations.moon_group_external_event(group_event, group_secret)["valid"])

    def test_plans_never_execute(self):
        for api in ("moon_group_batch_plan", "moon_channel_batch_plan"):
            result = getattr(operations, api)(["x"], "tag", False)
            self.assertFalse(result.get("executed", False))
            self.assertFalse(result.get("persisted", False))

    def test_no_io_or_dynamic_sinks(self):
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
    setattr(WebappAiGroupChannelTests, _feature["test"].rsplit(".", 1)[-1], make_test(_feature))

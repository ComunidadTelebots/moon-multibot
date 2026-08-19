import ast
import hashlib
import hmac
import importlib
import inspect
import unittest

import webapp_channel_user_automation_operations as operations
from webapp_channel_user_automation_operations_manifest import FEATURES
from tests.test_webapp_support_subscription_moderation_operations import _case


def signed(context, kind):
    body, secret, at, event_id = "{}", "s" * 16, "2026-01-01T00:00:00+00:00", "evt"
    signature = hmac.new(secret.encode(), f"{context}.{at}.{event_id}.{body}".encode(), hashlib.sha256).hexdigest()
    return {"id": event_id, "type": kind, "body": body, "signature": signature, "at": at}, secret


def args_for(api):
    if api == "moon_channel_external_event": return signed("moon-channel:channel.updated", "channel.updated")
    if api == "moon_user_external_event": return signed("moon-user:user.updated", "user.updated")
    if api.endswith("incident_correlation"): return _case("community_incidents")
    return _case(api)


class WebappChannelUserAutomationTests(unittest.TestCase):
    def test_manifest_exact_roles_and_resolvable_tests(self):
        self.assertEqual([x["id"] for x in FEATURES], [f"future-{i}" for i in range(2462, 2522)])
        allowed = {"channel_owner", "channel_admin", "user_admin", "user_reviewer", "automation_owner", "automation_operator"}
        module = importlib.import_module("tests.test_webapp_channel_user_automation_operations")
        case = getattr(module, "WebappChannelUserAutomationTests")
        for feature in FEATURES:
            self.assertIn(feature["role"], allowed)
            self.assertTrue(callable(getattr(operations, feature["api"])))
            self.assertTrue(callable(getattr(case, feature["test"].rsplit(".", 1)[-1])))

    def test_all_features_execute(self):
        for feature in FEATURES:
            with self.subTest(feature["id"]):
                self.assertIsNotNone(getattr(operations, feature["api"])(*args_for(feature["api"])))

    def test_external_domains_tampering_and_type_allowlist(self):
        event, secret = signed("moon-channel:channel.updated", "channel.updated")
        self.assertTrue(operations.moon_channel_external_event(event, secret)["valid"])
        self.assertFalse(operations.moon_user_external_event(event, secret)["valid"])
        event["body"] = '{"changed":true}'
        self.assertFalse(operations.moon_channel_external_event(event, secret)["valid"])
        unknown, key = signed("moon-user:user.deleted", "user.deleted")
        self.assertFalse(operations.moon_user_external_event(unknown, key)["valid"])

    def test_batch_operations_are_preview_only(self):
        for api in ("moon_user_batch_plan", "moon_automation_batch_plan"):
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
    def test(self): self.assertIsNotNone(getattr(operations, feature["api"])(*args_for(feature["api"])))
    test.__name__ = method_name
    return test


for _feature in FEATURES:
    setattr(WebappChannelUserAutomationTests, _feature["test"].rsplit(".", 1)[-1], make_test(_feature))

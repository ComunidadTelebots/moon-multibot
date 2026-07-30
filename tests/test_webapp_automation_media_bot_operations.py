import hashlib
import hmac
import importlib
import inspect
import unittest

import webapp_automation_media_bot_operations as operations
from webapp_automation_media_bot_operations_manifest import FEATURES
from tests.test_webapp_support_subscription_moderation_operations import _case


def signed(context, kind):
    body, secret, at, eid = "{}", "s" * 16, "2026-01-01T00:00:00+00:00", "evt"
    signature = hmac.new(secret.encode(), f"{context}.{at}.{eid}.{body}".encode(), hashlib.sha256).hexdigest()
    return {"id": eid, "type": kind, "body": body, "signature": signature, "at": at}, secret


def args_for(api):
    if api == "moon_automation_external_event": return signed("moon-automation:automation.updated", "automation.updated")
    if api == "moon_media_external_event": return signed("moon-media:media.scanned", "media.scanned")
    if api.endswith("incident_correlation"): return _case("community_incidents")
    if api == "moon_media_library": return _case("community_media")
    return _case(api)


class WebappAutomationMediaBotTests(unittest.TestCase):
    def test_manifest_metadata_roles_and_localizers(self):
        self.assertEqual([x["id"] for x in FEATURES], [f"future-{i}" for i in range(2522, 2582)])
        allowed = {"automation_owner", "automation_operator", "media_admin", "media_reviewer", "bot_owner", "bot_operator"}
        for feature in FEATURES:
            self.assertTrue(feature["title"] and feature["capability"])
            self.assertIn(feature["role"], allowed)
            self.assertTrue(callable(getattr(operations, feature["api"])))
            module_name, class_name, method = feature["test"].rsplit(".", 2)
            cls = getattr(importlib.import_module(module_name), class_name)
            self.assertTrue(callable(getattr(cls, method)))

    def test_domain_specific_behavior(self):
        for feature in FEATURES:
            result = getattr(operations, feature["api"])(*args_for(feature["api"]))
            self.assertIn(result["domain"], {"automation", "media", "managed_bot"})
            self.assertFalse(result["executed"])
            self.assertFalse(result["persisted"])

    def test_signed_events_are_isolated(self):
        event, secret = signed("moon-media:media.scanned", "media.scanned")
        self.assertTrue(operations.moon_media_external_event(event, secret)["valid"])
        self.assertFalse(operations.moon_automation_external_event(event, secret)["valid"])
        event["body"] = '{"changed":true}'
        self.assertFalse(operations.moon_media_external_event(event, secret)["valid"])

    def test_no_io_or_dynamic_sinks(self):
        source = inspect.getsource(operations)
        for token in ("requests.", "urllib.request", "subprocess", "eval(", "exec(", "innerHTML", "os.system"):
            self.assertNotIn(token, source)


def make_test(feature):
    def test(self):
        result = getattr(operations, feature["api"])(*args_for(feature["api"]))
        self.assertEqual(result["domain"], "automation" if feature["api"].startswith("moon_automation_") else "media" if feature["api"].startswith("moon_media_") else "managed_bot")
    return test


for _feature in FEATURES:
    setattr(WebappAutomationMediaBotTests, f"test_future_{_feature['id'].split('-')[1]}", make_test(_feature))


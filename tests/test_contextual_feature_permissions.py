import unittest
from unittest.mock import patch

from core import routes_public


class ChannelStatsStub:
    def get_user_channels(self, user_id):
        return [
            {"chat_id": "-100-admin", "name": "Admin group", "role": "administrator"},
            {"chat_id": "-100-owner", "name": "Owner group", "role": "creator"},
        ]

    def get_all_channels(self):
        return [{"chat_id": "-100-global", "name": "Global"}]


class ContextualFeaturePermissionTests(unittest.TestCase):
    def setUp(self):
        self.original = routes_public._channel_stats
        routes_public._channel_stats = ChannelStatsStub()

    def tearDown(self):
        routes_public._channel_stats = self.original

    def test_role_is_resolved_for_the_selected_group(self):
        user = {"id": 7}
        self.assertEqual("user", routes_public._miniapp_feature_context(user)[0])
        self.assertEqual("group_admin", routes_public._miniapp_feature_context(user, "-100-admin")[0])
        self.assertEqual("group_creator", routes_public._miniapp_feature_context(user, "-100-owner")[0])

    def test_unowned_group_is_denied(self):
        with self.assertRaises(PermissionError):
            routes_public._miniapp_feature_context({"id": 7}, "-100-other")

    def test_master_can_select_registered_global_group(self):
        with patch.object(routes_public, "_is_master", return_value=True):
            role, groups, selected = routes_public._miniapp_feature_context({"id": 1}, "-100-global")
        self.assertEqual("master", role)
        self.assertEqual("-100-global", selected["chat_id"])
        self.assertEqual("master", groups[0]["actor_role"])

    def test_direct_group_identifier_is_overwritten(self):
        item = {"input_schema": {"parameters": [
            {"name": "group_id", "binding": "kwargs", "variadic": False},
            {"name": "title", "binding": "kwargs", "variadic": False},
        ]}}
        payload = routes_public._bind_feature_group_payload(
            item, {"args": [], "kwargs": {"group_id": "-100-attacker", "title": "safe"}}, "-100-admin"
        )
        self.assertEqual("-100-admin", payload["kwargs"]["group_id"])
        self.assertEqual("safe", payload["kwargs"]["title"])

    def test_nested_or_plural_cross_group_references_are_denied(self):
        self.assertTrue(routes_public._payload_uses_only_group({"group_id": "-100-admin"}, "-100-admin"))
        self.assertFalse(routes_public._payload_uses_only_group({"config": {"chat_id": "-100-other"}}, "-100-admin"))
        self.assertFalse(routes_public._payload_uses_only_group({"group_ids": ["-100-admin", "-100-other"]}, "-100-admin"))

    def test_actor_identity_and_roles_cannot_be_forged(self):
        item = {"input_schema": {"parameters": [
            {"name": "actor", "binding": "kwargs", "variadic": False},
            {"name": "actor_id", "binding": "kwargs", "variadic": False},
            {"name": "is_master", "binding": "kwargs", "variadic": False},
        ]}}
        payload = routes_public._bind_feature_actor_payload(item, {"kwargs": {
            "actor": {"id": "attacker", "roles": ["master"], "scopes": ["allowed:scope"]},
            "is_master": True,
        }}, {"id": 7}, "group_admin")
        self.assertEqual({"id": "7", "roles": ["group_admin"], "scopes": ["allowed:scope"]}, payload["kwargs"]["actor"])
        self.assertEqual("7", payload["kwargs"]["actor_id"])
        self.assertFalse(payload["kwargs"]["is_master"])

    def test_hub_sends_only_server_selected_group_context(self):
        source = (routes_public.__file__.replace("core\\routes_public.py", "web\\hub.html"))
        with open(source, encoding="utf-8") as handle:
            html = handle.read()
        self.assertIn('b={...b,group_id:roleFeatureSelectedGroup}', html)
        self.assertIn('data.selected_group_id', html)


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RoleFeatureInterfaceTests(unittest.TestCase):
    def test_public_route_derives_role_from_verified_miniapp_user(self):
        source = (ROOT / "core" / "routes_public.py").read_text(encoding="utf-8")
        segment = source[source.index('@bp.route("/api/public/features"'):source.index('@bp.route("/api/public/notifications"')]
        self.assertIn("_verify_init_data", segment)
        self.assertIn("_miniapp_feature_context(user, body.get(\"group_id\"))", segment)
        self.assertIn("_bind_feature_group_payload", segment)
        self.assertIn("_bind_feature_actor_payload", segment)
        self.assertIn("request.max_content_length = 128 * 1024", segment)
        self.assertIn("list_verified_features(actor_role, release_channel)", segment)
        self.assertIn("_miniapp_release_channel(user)", segment)
        self.assertIn("execute_verified_feature", segment)
        self.assertNotIn('body.get("actor_role")', segment)

    def test_hub_exposes_schema_forms_to_each_effective_role(self):
        source = (ROOT / "web" / "hub.html").read_text(encoding="utf-8")
        self.assertIn('id="userFeatures"', source)
        self.assertIn("async function openRoleFeatures", source)
        self.assertIn("item.input_schema", source)
        self.assertIn('action:"execute"', source)
        self.assertIn("data.actor_role", source)


if __name__ == "__main__":
    unittest.main()

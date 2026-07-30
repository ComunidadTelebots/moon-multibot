import unittest
from pathlib import Path


SOURCE = (Path(__file__).parents[1] / "core" / "routes_public.py").read_text(encoding="utf-8")
SEGMENT = SOURCE[SOURCE.index('@bp.route("/api/internal/features"'):SOURCE.index("def _safe_list")]


class InternalFeatureRoleSecurityTests(unittest.TestCase):
    def test_execution_role_is_derived_from_internal_header_not_body(self):
        self.assertIn('request.headers.get("X-Moon-Actor-Role", "master")', SEGMENT)
        self.assertIn('execute_verified_feature(body.get("feature_id"), payload, effective_role)', SEGMENT)
        self.assertIn('request.headers.get("X-Moon-Actor-Id", "")', SEGMENT)
        self.assertIn('selected["actor_role"] if selected else catalog_role', SEGMENT)
        self.assertNotIn('body.get("actor_role")', SEGMENT)

    def test_actor_role_is_allowlisted(self):
        self.assertIn('{"user", "group_admin", "group_creator", "master"}', SEGMENT)

    def test_internal_authorization_precedes_get_and_post(self):
        self.assertLess(SEGMENT.index("_internal_admin_authorized()"), SEGMENT.index('request.method == "GET"'))


if __name__ == "__main__":
    unittest.main()

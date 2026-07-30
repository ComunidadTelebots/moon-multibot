import unittest
from pathlib import Path


SOURCE = (Path(__file__).parents[1] / "web" / "hub.html").read_text(encoding="utf-8")
SEGMENT = SOURCE[SOURCE.index("const MASTER_CAPABILITY_CENTERS"):SOURCE.index("async function loadMasterOverview")]


class HubCapabilityCentersSecondBlockTests(unittest.TestCase):
    def test_three_new_centers_are_registered(self):
        expected = {
            'id:"ai-center"': "loadMasterAdvancedAiCenter",
            'id:"integrations"': "loadMasterIntegrationsCenter",
            'id:"experience"': "loadMasterExperienceCenter",
        }
        for marker, loader in expected.items():
            self.assertIn(marker, SEGMENT)
            self.assertIn(f"loader:{loader}", SEGMENT)
            self.assertIn(f"async function {loader}()", SEGMENT)

    def test_existing_routes_and_safe_actions_are_used(self):
        for endpoint in ("/api/internal/ai-center", "/api/internal/integrations", "/api/internal/experience"):
            self.assertGreaterEqual(SEGMENT.count(endpoint), 2)
        for action in ('action:"unanswered"', 'action:"config_export"', 'action:"preferences"'):
            self.assertIn(action, SEGMENT)
        for forbidden in ('action:"token_create"', 'action:"config_import"', 'action:"memory_delete"', 'action:"source_delete"'):
            self.assertNotIn(forbidden, SEGMENT)

    def test_back_arrow_returns_to_center_list(self):
        self.assertIn("masterDetailBack.onclick=loadMasterCapabilityCenters", SEGMENT)

    def test_remote_strings_are_escaped(self):
        for expression in (
            'runtime.provider||"local"', 'runtime.model||"sin definir"',
            'item.model||"Modelo"', 'sdk.name||"Moonbot SDK"',
            'item.provider||"Calendario"', 'item.title||item.id||"Aviso"',
        ):
            self.assertIn(f"escHtml({expression})", SEGMENT)

    def test_user_values_are_sent_as_json_not_interpolated_html(self):
        self.assertIn("JSON.stringify({action:\"unanswered\"", SEGMENT)
        self.assertIn("JSON.stringify({action:\"config_export\"", SEGMENT)
        self.assertIn("JSON.stringify({action:\"preferences\"", SEGMENT)

    def test_new_fields_have_accessible_labels(self):
        self.assertIn('label for="centerAiMessages"', SEGMENT)
        self.assertIn('label for="centerIntegrationGroup"', SEGMENT)
        self.assertIn('role="switch"', SEGMENT)
        self.assertIn('aria-checked=', SEGMENT)

    def test_verified_features_use_runtime_input_schema(self):
        self.assertIn("const verifiedPayloadFor", SOURCE)
        self.assertIn("item.input_schema?.parameters", SOURCE)
        self.assertIn("bindVerifiedSchemaFields", SOURCE)
        self.assertIn('aria-required="true"', SOURCE)
        self.assertIn("execute.disabled=!valid", SOURCE)

    def test_role_audiences_are_visible_without_client_side_escalation(self):
        for role in ("user", "group_admin", "group_creator", "master"):
            self.assertIn(f'<option value="{role}">', SOURCE)
        self.assertIn('(item.audience||[]).join', SOURCE)
        self.assertNotIn('actor_role:verifiedFeatureAudience.value', SOURCE)


if __name__ == "__main__":
    unittest.main()

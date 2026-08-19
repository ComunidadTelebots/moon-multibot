import re
import unittest
from pathlib import Path


HUB = Path(__file__).parents[1] / "web" / "hub.html"


class HubCapabilityCentersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HUB.read_text(encoding="utf-8")

    def test_master_entry_and_back_navigation_exist(self):
        self.assertIn('id="masterCapabilityCenters"', self.source)
        self.assertIn('masterDetailBack.onclick=loadMasterCapabilityCenters', self.source)
        self.assertIn('masterDetailBack.onclick=closeMasterPage', self.source)

    def test_existing_endpoints_are_used(self):
        for endpoint in (
            "/api/internal/editorial",
            "/api/internal/automations",
            "/api/internal/operations",
        ):
            self.assertGreaterEqual(self.source.count(endpoint), 2)

    def test_first_collection_has_three_real_loaders(self):
        for loader in (
            "loadMasterEditorialCenter",
            "loadMasterAutomationCenter",
            "loadMasterOperationsCenter",
        ):
            self.assertRegex(self.source, rf"async function {loader}\(\)")
            self.assertIn(f"loader:{loader}", self.source)

    def test_server_content_is_escaped_before_html_render(self):
        sensitive = ("item.name", "item.description", "item.body", "diagnosis.summary")
        for expression in sensitive:
            self.assertRegex(self.source, rf"escHtml\([^\n]*{re.escape(expression)}")

    def test_actions_are_preview_or_diagnosis_only(self):
        self.assertIn('action:"preview"', self.source)
        self.assertIn('action:"simulate"', self.source)
        self.assertIn('action:"diagnose"', self.source)
        for forbidden in ('action:"publish_now"', 'action:"deployment"', 'action:"restore_plan"'):
            segment = self.source[self.source.index("const MASTER_CAPABILITY_CENTERS"):self.source.index("async function loadMasterOverview")]
            self.assertNotIn(forbidden, segment)


if __name__ == "__main__":
    unittest.main()

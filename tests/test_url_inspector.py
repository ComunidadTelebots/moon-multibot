import json
import unittest
from pathlib import Path

from plugins.url_tools import inspect_url

ROOT = Path(__file__).parents[1]
HUB = (ROOT / "web" / "hub.html").read_text(encoding="utf-8")
SECURITY = (ROOT / "core" / "routes_security.py").read_text(encoding="utf-8")


class UrlInspectorTests(unittest.TestCase):
    def test_public_url_is_parsed_without_network(self):
        result = inspect_url("https://example.com/path?a=1#fragment")
        self.assertTrue(result["ok"])
        self.assertEqual(result["inspection"]["host"], "example.com")
        self.assertEqual(result["inspection"]["query_parameters"], 1)
        self.assertNotIn("#fragment", result["inspection"]["normalized"])

    def test_private_and_deceptive_destinations_are_flagged(self):
        private = inspect_url("http://127.0.0.1:8080/admin")
        self.assertFalse(private["inspection"]["safe_to_fetch"])
        self.assertIn("local_or_private_destination", private["inspection"]["signals"])
        deceptive = inspect_url("https://user:pass@xn--exmple-cua.com/")
        self.assertIn("credentials_in_url", deceptive["inspection"]["signals"])
        self.assertIn("punycode_domain", deceptive["inspection"]["signals"])

    def test_invalid_scheme_port_and_length_are_rejected(self):
        self.assertFalse(inspect_url("file:///etc/passwd")["ok"])
        self.assertFalse(inspect_url("https://example.com:bad/")["ok"])
        self.assertFalse(inspect_url("https://example.com/" + "a" * 2100)["ok"])

    def test_master_route_and_existing_hub_components(self):
        self.assertIn('if not _check_jwt(request):', SECURITY)
        self.assertIn('/api/security/url/inspect', SECURITY)
        for marker in ('id="masterUrlInspect"', 'class="casbox"', 'class="rbadge"'):
            self.assertIn(marker, HUB)

    def test_roadmap_has_evidence_for_all_seven_tasks(self):
        roadmap = json.loads((ROOT / "web" / "future-features.json").read_text(encoding="utf-8"))
        self.assertEqual(len(roadmap["tracked_task_audit"]), 7)
        self.assertTrue(all(item["status"] == "implemented" for item in roadmap["tracked_task_audit"]))


if __name__ == "__main__": unittest.main()

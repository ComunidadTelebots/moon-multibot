import unittest
from pathlib import Path

from horizon_completion import HorizonCompletion, FEATURES


ROOT = Path(__file__).parents[1]
ROUTES = (ROOT / "core" / "routes_public.py").read_text(encoding="utf-8")
HUB = (ROOT / "web" / "hub.html").read_text(encoding="utf-8")


class MemoryDB:
    def __init__(self):
        self.data = {}

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value


class TelegramExperienceCenterTests(unittest.TestCase):
    def test_all_ten_telegram_capabilities_execute_and_are_audited(self):
        db = MemoryDB()
        service = HorizonCompletion(db)
        slugs = [slug for slug, (_, category) in FEATURES.items() if category == "telegram"]
        self.assertEqual(len(slugs), 10)
        for slug in slugs:
            self.assertIsInstance(service.execute(slug, {}), dict)
        self.assertEqual([row["feature"] for row in db.get("HORIZON_COMPLETION_AUDIT", [])], slugs)

    def test_route_is_internal_allowlisted_and_size_limited(self):
        segment = ROUTES[ROUTES.index('@bp.route("/api/internal/telegram-experience"'):ROUTES.index("def _safe_list")]
        self.assertIn("_internal_admin_authorized()", segment)
        self.assertIn("slug not in _TELEGRAM_EXPERIENCE_SLUGS", segment)
        self.assertIn("request.content_length > 65536", segment)
        self.assertNotIn('body.get("actor_role")', segment)

    def test_hub_uses_existing_master_panel_and_escapes_catalog(self):
        self.assertIn("loader:loadMasterTelegramExperienceCenter", HUB)
        self.assertIn('masterApi("/api/internal/telegram-experience")', HUB)
        self.assertIn("escHtml(item.title)", HUB)
        self.assertIn("JSON.parse(centerTelegramPayload.value", HUB)
        self.assertIn("masterDetailBack.onclick=loadMasterCapabilityCenters", HUB)


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path
from core.routes_public import _house_ad_metric_context

ROOT = Path(__file__).parents[1]
ROUTES = (ROOT / "core" / "routes_public.py").read_text(encoding="utf-8")
HUB = (ROOT / "web" / "hub.html").read_text(encoding="utf-8")

class HouseAdsDeliveryMetricsTests(unittest.TestCase):
    def test_metric_context_counts_valid_ids_and_rejects_arbitrary_values(self):
        row = {}
        _house_ad_metric_context(row, {"chat_id": "-1001234567890", "bot_id": "209219812"}, "click")
        _house_ad_metric_context(row, {"chat_id": "not-an-id", "bot_id": "secret"}, "impression")
        self.assertEqual(row["clicks_today"], 1)
        self.assertEqual(row["impressions_today"], 1)
        self.assertEqual(row["clicks_by_chat"], {"-1001234567890": 1})
        self.assertEqual(row["clicks_by_bot"], {"209219812": 1})
        self.assertNotIn("impressions_by_chat", row)
        self.assertNotIn("impressions_by_bot", row)

    def test_daily_and_telegram_dimensions_are_persisted(self):
        helper = ROUTES[ROUTES.index("def _house_ad_metric_context"):ROUTES.index("def _official_house_ads")]
        self.assertIn('"clicks_today"', helper)
        self.assertIn('"impressions_today"', helper)
        self.assertIn('f"{metric}s_by_chat"', helper)
        self.assertIn('f"{metric}s_by_bot"', helper)
        self.assertIn('re.fullmatch(pattern, raw)', helper)

    def test_clone_and_reset_do_not_inherit_metrics(self):
        update = ROUTES[ROUTES.index("def _house_ads_update"):ROUTES.index('@bp.route("/api/internal/house-ads"')]
        for field in ("clicks_by_chat", "impressions_by_chat", "clicks_by_bot", "impressions_by_bot", "metrics_day"):
            self.assertGreaterEqual(update.count(f'"{field}"'), 2)

    def test_hub_exposes_context_and_budget_controls(self):
        for field in ("haCategories", "haInclude", "haExclude", "haChannels", "haGroups", "haDailyClicks", "haDailyImpressions"):
            self.assertIn(f'id="{field}"', HUB)
        self.assertIn('content_categories:csvValues("haCategories")', HUB)
        self.assertIn('target_group_ids:csvValues("haGroups")', HUB)

if __name__ == "__main__":
    unittest.main()

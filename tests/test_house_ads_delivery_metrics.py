import json
import unittest
from pathlib import Path
from core.routes_public import _house_ad_metric_context, _house_ads_insights, _house_ads_insights_csv

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

    def test_insights_aggregate_anonymous_dimensions_and_diagnostics(self):
        result = _house_ads_insights([{
            "id": "campaign-1", "title": "Canal", "enabled": True, "approval_status": "approved",
            "url": "https://t.me/example", "clicks": 4, "impressions": 20,
            "clicks_today": 2, "impressions_today": 5, "daily_click_cap": 2,
            "clicks_by_chat": {"-1001234567890": 4, "invalid": 99},
            "impressions_by_chat": {"-1001234567890": 20},
            "clicks_by_bot": {"209219812": 4}, "impressions_by_bot": {"209219812": 20},
        }])
        self.assertEqual(result["totals"]["ctr"], 20.0)
        self.assertEqual(result["top_chats"], [{"id": "-1001234567890", "clicks": 4, "impressions": 20}])
        self.assertIn("daily_click_cap_reached", result["campaigns"][0]["diagnostics"])

    def test_metrics_csv_escapes_titles(self):
        csv = _house_ads_insights_csv({"campaigns": [{"id": "a", "title": 'Canal "uno"', "enabled": True,
            "clicks": 1, "impressions": 2, "ctr": 50, "clicks_today": 1, "impressions_today": 2,
            "diagnostics": []}]})
        self.assertIn('"Canal ""uno"""', csv)

    def test_metrics_csv_neutralizes_spreadsheet_formulas(self):
        csv = _house_ads_insights_csv({"campaigns": [{"id": "a", "title": "=HYPERLINK(1)", "enabled": True}]})
        self.assertIn('"\'=HYPERLINK(1)"', csv)
        self.assertNotIn('\n=HYPERLINK', csv)

    def test_master_hub_has_insights_and_export(self):
        self.assertIn('call({action:"insights"})', HUB)
        self.assertIn('id="haExport"', HUB)
        self.assertIn('call({action:"export_metrics"})', HUB)
        self.assertIn('<div class="statbar"><div class="stat"><div class="v">', HUB)

    def test_roadmap_records_the_completed_block(self):
        roadmap = json.loads((ROOT / "web" / "future-features.json").read_text(encoding="utf-8"))
        release = next(item for item in roadmap["recently_implemented"] if item["version"] == "v18.23.32")
        self.assertEqual(len(release["features"]), 5)

if __name__ == "__main__":
    unittest.main()

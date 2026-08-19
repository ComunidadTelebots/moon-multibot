import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
ROUTES = (ROOT / "core" / "routes_public.py").read_text(encoding="utf-8")
HUB = (ROOT / "web" / "hub.html").read_text(encoding="utf-8")


class HubCommunityCampaignTests(unittest.TestCase):
    def test_audience_is_resolved_server_side(self):
        segment = ROUTES[ROUTES.index('def public_community_campaigns'):ROUTES.index('def _hub_bot')]
        self.assertIn('_verify_init_data', segment)
        self.assertIn('_has_verified_channel_ownership(user)', segment)
        self.assertNotIn('owner_verified = request', segment)

    def test_master_is_not_treated_as_channel_owner(self):
        helper = ROUTES[ROUTES.index('def _has_verified_channel_ownership'):ROUTES.index('def setup')]
        self.assertIn('get_user_channels(user_id)', helper)
        self.assertIn('== "creator"', helper)
        self.assertNotIn('_is_master', helper)

    def test_server_to_server_request_sends_internal_key(self):
        helper = ROUTES[ROUTES.index('def _community_campaigns_for_audience'):ROUTES.index('def _has_verified_channel_ownership')]
        self.assertIn('MOON_ADMIN_API_KEY', helper)
        self.assertIn('X-Moon-Admin-Key', helper)
        self.assertIn('placement=hub&site=hub', helper)
        self.assertNotIn('hub_miniapp', helper)

    def test_internal_user_channels_contract_is_protected(self):
        start = ROUTES.index('@bp.route("/api/internal/get_user_channels")')
        segment = ROUTES[start:ROUTES.index('@bp.route("/api/internal/groups/<cid>"', start)]
        self.assertIn('_internal_admin_authorized()', segment)
        self.assertIn('request.args.get("telegram_id")', segment)
        self.assertIn('_channel_stats.get_user_channels(telegram_id)', segment)
        self.assertIn('"owner_verified"', segment)

    def test_owner_campaign_fails_closed(self):
        self.assertIn('if item_audience == "channel_owner" and not owner_verified', ROUTES)
        self.assertIn('if owner_verified and owner_rows else', ROUTES)
        self.assertNotIn('r_163103382', ROUTES)
        self.assertNotIn('m_163103382', ROUTES)

    def test_hub_uses_catalog_card_and_tracking_url(self):
        self.assertIn('apiPost("/community-campaigns",{initData:tg&&tg.initData})', HUB)
        self.assertIn('const click=ad.click_url||', HUB)
        self.assertIn('instantAd(ads[', HUB)


if __name__ == "__main__":
    unittest.main()

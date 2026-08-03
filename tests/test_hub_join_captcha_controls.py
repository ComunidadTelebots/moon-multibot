import pathlib
import unittest


class HubJoinCaptchaControlsTests(unittest.TestCase):
    def test_global_captcha_shows_per_user_verification_and_twelve_hour_defaults(self):
        hub = pathlib.Path("web/hub.html").read_text(encoding="utf-8")
        routes = pathlib.Path("core/routes_public.py").read_text(encoding="utf-8")
        runtime = pathlib.Path("moon_multibot.py").read_text(encoding="utf-8")
        self.assertIn("user.verified?'✓ Sí':'✕ No'", hub)
        self.assertIn("reverify_interval_hours||12", hub)
        self.assertIn('"TodoSobreAllTech"', routes)
        self.assertIn('"verified": verified', routes)
        self.assertIn('"all_verified": unverified_users == 0', routes)
        self.assertIn('JOIN_GLOBAL_REVERIFY_INTERVAL_HOURS', runtime)
        self.assertIn('global_interval_hours * 3600', runtime)
        self.assertIn('db.set("GLOBAL_CAPTCHA_CAMPAIGN"', runtime)

    def test_local_bulk_controls_remain_bound_after_global_settings_move(self):
        source = pathlib.Path("web/hub.html").read_text(encoding="utf-8")
        start = source.index("async function loadJoinCaptcha()")
        end = source.index("function bindDropdown", start)
        block = source[start:end]
        self.assertIn('document.getElementById("gjoinReverify").onclick', block)
        self.assertIn('document.getElementById("gjoinPreview").onclick', block)
        self.assertIn('const cancelBulk=document.getElementById("gjoinCancel")', block)
        self.assertIn('/group/join/reverify-all', block)
        self.assertIn('/group/join/reverify-control', block)

    def test_global_and_group_captcha_support_joined_channel_recommendations(self):
        hub = pathlib.Path("web/hub.html").read_text(encoding="utf-8")
        routes = pathlib.Path("core/routes_public.py").read_text(encoding="utf-8")
        self.assertIn("suggested_channels", routes)
        self.assertIn("required_channel_suggestions", routes)
        self.assertIn("JOIN_GLOBAL_REQUIRED_CHANNELS", routes)
        self.assertIn("_normalize_required_channels(required)", routes)
        self.assertIn("globalChannelSuggestion", hub)
        self.assertIn("gjoinSuggestion", hub)
        self.assertIn("required_channels:ownChannels", hub)
        self.assertIn("photo_url", routes)
        self.assertIn("_channel_candidate_review", routes)
        self.assertIn("messages_analyzed", hub)
        self.assertIn("join_bot_url", routes)
        self.assertIn("globalChannelSearch", hub)

    def test_global_and_group_recommendations_have_horizontal_banners_and_safe_join_actions(self):
        hub = pathlib.Path("web/hub.html").read_text(encoding="utf-8")
        self.assertIn("required-channel-strip", hub)
        self.assertIn("required-channel-banner", hub)
        self.assertIn('id="globalSelectedChannels"', hub)
        self.assertIn('id="gjoinSelectedChannels"', hub)
        self.assertIn('id="gjoinChannelSearch"', hub)
        self.assertIn("gjoinSuggestionRow", hub)
        self.assertIn("gjoinRemoveChannel", hub)
        self.assertIn("globalRemoveChannel", hub)
        self.assertIn('rel="noopener"', hub)
        self.assertIn("channelAvatar(item)", hub)


if __name__ == "__main__":
    unittest.main()

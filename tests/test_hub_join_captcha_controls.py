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


if __name__ == "__main__":
    unittest.main()

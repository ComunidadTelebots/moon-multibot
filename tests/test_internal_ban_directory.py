import pathlib
import unittest


class InternalBanDirectoryTests(unittest.TestCase):
    def test_directory_uses_registered_moonbot_bans_not_complete_cas_export(self):
        source = (pathlib.Path(__file__).parents[1] / "core" / "routes_public.py").read_text(encoding="utf-8")
        section = source.split('@bp.route("/api/internal/ban-directory")', 1)[1].split('@bp.route("/api/internal/security"', 1)[0]
        self.assertIn("list_ban_records", section)
        self.assertIn("get_all_local_bans", section)
        self.assertIn('cas_sources = {"cas", "cas_feed", "export.csv", "cas_export"}', section)
        self.assertNotIn("cas_export_ids", section)
        self.assertIn("_internal_admin_authorized", section)

    def test_global_captcha_reuses_group_protocol_and_only_targets_pending_users(self):
        source = (pathlib.Path(__file__).parents[1] / "core" / "routes_public.py").read_text(encoding="utf-8")
        self.assertIn('@bp.route("/api/internal/captcha-global", methods=["GET", "POST"])', source)
        self.assertIn('only_pending=True', source)
        self.assertIn('"telegram_mute", "captcha", "cas", "required_channels", "appeal"', source)
        self.assertIn('get("status") != "passed"', source)
        self.assertIn('"percentage": percentage', source)
        self.assertIn('"group_details": group_details', source)
        self.assertIn('in ("group", "supergroup")', source)
        self.assertIn('.startswith("-")', source)
        self.assertIn('exempt.add(str(_master_id))', source)
        self.assertIn('member.get("status") in ("creator", "administrator")', source)
        self.assertIn('"remaining_users": remaining_users', source)


if __name__ == "__main__":
    unittest.main()

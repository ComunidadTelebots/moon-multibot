import unittest

from core.telegram_api import append_community_ad


ADS = [{"id": "community-one", "title": "Comunidad Uno",
        "description": "Canales y grupos de tecnología", "url": "https://t.me/comunidaduno",
        "enabled": True, "approval_status": "approved", "priority": 60}]


class BotCommunityAdsTests(unittest.TestCase):
    def test_informational_group_reply_gets_tracked_ad_and_directory(self):
        value = append_community_ad("## Resultado", "/clima", ADS, "-100123", now=1)
        self.assertIn("Comunidad recomendada", value)
        self.assertIn("placement=bot_reply", value)
        self.assertIn("https://canales.todosobreall.tech/canal/comunidaduno", value)

    def test_sensitive_commands_and_private_chats_never_get_ads(self):
        self.assertEqual("Aviso", append_community_ad("Aviso", "/ban", ADS, "-100123", now=1))
        self.assertEqual("Ayuda", append_community_ad("Ayuda", "/help", ADS, "123", now=1))

    def test_disabled_or_unapproved_ads_are_ignored(self):
        rows = [{**ADS[0], "enabled": False}, {**ADS[0], "approval_status": "pending"}]
        self.assertEqual("Info", append_community_ad("Info", "/info", rows, "-100123", now=1))


if __name__ == "__main__":
    unittest.main()

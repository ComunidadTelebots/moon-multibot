import unittest
import resource_offline_autotest_engines as e

class OfflineAutotestTests(unittest.TestCase):
 def test_thirteen_offline_queues(self):
  funcs=[e.offline_editorial_articles,e.offline_moderated_images,e.offline_user_appeals,e.offline_mtproto_proxies,e.offline_persistent_tasks,e.offline_moderation_rules,e.offline_language_metrics,e.offline_community_translations,e.offline_personal_consents,e.offline_telegram_reactions,e.offline_master_panels,e.offline_channel_directories,e.offline_external_links]
  ops=[{"id":"op1","action":"create","payload":{"id":"x"}}]
  for i,fn in enumerate(funcs):
   with self.subTest(id=e.IDS[i]):
    r=fn(ops); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertTrue(r["offline"]); self.assertFalse(r["applied"])
 def test_seven_safe_autotest_plans(self):
  funcs=[e.autotest_admin_sessions,e.autotest_community_profiles,e.autotest_telegram_communities,e.autotest_house_ads,e.autotest_voice_notes,e.autotest_suspicious_files,e.autotest_captcha_decisions]
  for i,fn in enumerate(funcs,13):
   with self.subTest(id=e.IDS[i]):
    r=fn(["valid","invalid"],["schema","privacy"]); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["case_count"],2); self.assertTrue(r["sandbox_required"]); self.assertFalse(r["executed"]); self.assertTrue(all(not x["mutates_production"] for x in r["cases"]))
 def test_unknown_check_rejected(self):
  with self.assertRaises(ValueError): e.autotest_admin_sessions(["x"],["delete-production"])

if __name__=="__main__": unittest.main()

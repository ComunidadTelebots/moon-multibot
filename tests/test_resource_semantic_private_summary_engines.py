import unittest
import resource_semantic_private_summary_engines as e

class SemanticPrivateSummaryTests(unittest.TestCase):
 def test_three_local_searches(self):
  for i,fn in enumerate((e.search_master_panels,e.search_channel_directories,e.search_external_links)):
   with self.subTest(id=e.IDS[i]):
    r=fn("canal seguro",[{"id":"1","text":"canal seguro telegram"}]); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertTrue(r["local_only"])
 def test_seventeen_private_summaries(self):
  funcs=[e.summarize_admin_sessions,e.summarize_community_profiles,e.summarize_telegram_communities,e.summarize_house_ads,e.summarize_voice_notes,e.summarize_suspicious_files,e.summarize_captcha_decisions,e.summarize_managed_bots,e.summarize_recurring_reminders,e.summarize_security_events,e.summarize_regional_maps,e.summarize_backups,e.summarize_ai_learning_data,e.summarize_rich_commands,e.summarize_hub_notifications,e.summarize_cookie_policies,e.summarize_wayback_history]
  rows=[{"status":"active","token":"TOP-SECRET","email":"private@example.com"},{"status":"active","token":"OTHER"}]
  for i,fn in enumerate(funcs,3):
   with self.subTest(id=e.IDS[i]):
    r=fn(rows); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["record_count"],2); self.assertTrue(r["aggregate_only"]); self.assertFalse(r["raw_records_included"]); self.assertNotIn("TOP-SECRET",str(r)); self.assertNotIn("private@example.com",str(r))
 def test_non_scalar_dimension_is_bucketed(self):
  r=e.summarize_security_events([{"severity":{"secret":"x"}}]); self.assertEqual(r["distributions"]["severity"],(("[OTHER]",1),))

if __name__=="__main__": unittest.main()

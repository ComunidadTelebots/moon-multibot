import unittest
import resource_bulk_recommendation_engines as e

class BulkRecommendationTests(unittest.TestCase):
 def test_three_reversible_bulk_plans(self):
  for i,fn in enumerate((e.bulk_master_panels,e.bulk_channel_directories,e.bulk_external_links)):
   with self.subTest(id=e.IDS[i]):
    r=fn(["x"],"tag","review"); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["rollback"][0]["action"],"untag"); self.assertFalse(r["applied"])
 def test_seventeen_explainable_recommendations(self):
  funcs=[e.recommend_admin_sessions,e.recommend_community_profiles,e.recommend_telegram_communities,e.recommend_house_ads,e.recommend_voice_notes,e.recommend_suspicious_files,e.recommend_captcha_decisions,e.recommend_managed_bots,e.recommend_recurring_reminders,e.recommend_security_events,e.recommend_regional_maps,e.recommend_backups,e.recommend_ai_learning_data,e.recommend_rich_commands,e.recommend_hub_notifications,e.recommend_cookie_policies,e.recommend_wayback_history]
  candidates=[{"id":"b","score":.8,"reasons":["rule b"]},{"id":"a","score":.8,"reasons":["rule a"]},{"id":"c","score":.2,"reasons":["rule c"]}]
  for i,fn in enumerate(funcs,3):
   with self.subTest(id=e.IDS[i]):
    r=fn(candidates,2); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(tuple(x["id"] for x in r["recommendations"]),("a","b")); self.assertTrue(r["explainable"] and r["human_review_required"]); self.assertFalse(r["automatic_action"])
 def test_missing_reasons_rejected(self):
  with self.assertRaises(ValueError): e.recommend_backups([{"id":"x","score":.5,"reasons":[]}])

if __name__=="__main__": unittest.main()

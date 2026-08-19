import unittest
import resource_anonymize_classify_engines as e

class AnonymizeClassifyTests(unittest.TestCase):
 def test_three_verifiable_anonymizers(self):
  for i,fn in enumerate((e.anonymize_master_panels,e.anonymize_channel_directories,e.anonymize_external_links)):
   with self.subTest(id=e.IDS[i]):
    r=fn([{"id":"private","state":"ok"}],["id"],"1234567890123456"); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertNotIn("private",str(r)); self.assertTrue(r["verifiable"])
 def test_seventeen_assisted_classifiers(self):
  funcs=[e.classify_admin_sessions,e.classify_community_profiles,e.classify_telegram_communities,e.classify_house_ads,e.classify_voice_notes,e.classify_suspicious_files,e.classify_captcha_decisions,e.classify_managed_bots,e.classify_recurring_reminders,e.classify_security_events,e.classify_regional_maps,e.classify_backups,e.classify_ai_learning_data,e.classify_rich_commands,e.classify_hub_notifications,e.classify_cookie_policies,e.classify_wayback_history]
  candidates=[{"label":"review","score":.7,"reason":"rule matched"},{"label":"safe","score":.2,"reason":"weak match"}]
  for i,fn in enumerate(funcs,3):
   with self.subTest(id=e.IDS[i]):
    r=fn(candidates,.8); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["suggestion"]["label"],"review"); self.assertTrue(r["low_confidence"] and r["human_review_required"]); self.assertFalse(r["label_applied"])
 def test_bad_score_rejected(self):
  with self.assertRaises(ValueError): e.classify_backups([{"label":"x","score":2,"reason":"bad"}])

if __name__=="__main__": unittest.main()

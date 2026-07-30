import unittest,resource_drift_impact_engines as e
class DriftImpactTests(unittest.TestCase):
 def test_13_resource_drift_contracts(self):
  funcs=[e.drift_editorial_articles,e.drift_moderated_images,e.drift_user_appeals,e.drift_mtproto_proxies,e.drift_persistent_tasks,e.drift_moderation_rules,e.drift_language_metrics,e.drift_community_translations,e.drift_personal_consents,e.drift_telegram_reactions,e.drift_master_panels,e.drift_channel_directories,e.drift_external_links]
  schemas=[("publish_rate","correction_rate","reading_time"),("unsafe_ratio","review_seconds","false_positive_ratio"),("approval_ratio","resolution_hours","reopen_ratio"),("availability_ratio","latency_ms","failure_ratio"),("completion_ratio","overdue_ratio","cycle_hours"),("match_ratio","action_ratio","appeal_ratio"),("detected_ratio","unknown_ratio","confidence"),("coverage_ratio","approval_ratio","edit_ratio"),("grant_ratio","withdraw_ratio","expiry_ratio"),("reaction_rate","unique_ratio","removal_ratio"),("session_minutes","error_ratio","action_rate"),("listing_growth","stale_ratio","click_ratio"),("safe_ratio","redirect_ratio","failure_ratio")]
  for i,fn in enumerate(funcs):
   result=fn({k:1 for k in schemas[i]},{k:2 for k in schemas[i]})
   with self.subTest(id=e.IDS[i]): self.assertEqual(result["feature_id"],e.IDS[i]); self.assertTrue(result["drifted"])
 def test_7_impacts_are_preview_only(self):
  funcs=[e.impact_admin_sessions,e.impact_community_profiles,e.impact_telegram_communities,e.impact_house_ads,e.impact_voice_notes,e.impact_suspicious_files,e.impact_captcha_decisions]
  for i,fn in enumerate(funcs,13):
   result=fn({}, {"concurrency":1,"visible_fields":1,"member_groups":1,"daily_impressions":1,"max_minutes":1,"max_mb":1,"attempts":1})
   with self.subTest(id=e.IDS[i]): self.assertEqual(result["feature_id"],e.IDS[i]); self.assertFalse(result["executed"]); self.assertTrue(result["explainable"])
if __name__=="__main__": unittest.main()

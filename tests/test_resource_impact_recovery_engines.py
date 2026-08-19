import unittest,resource_impact_recovery_engines as e
class ImpactRecoveryTests(unittest.TestCase):
 def test_ten_resource_impacts(self):
  funcs=[e.impact_managed_bots,e.impact_recurring_reminders,e.impact_security_events,e.impact_regional_maps,e.impact_backups,e.impact_ai_learning_data,e.impact_rich_commands,e.impact_hub_notifications,e.impact_cookie_policies,e.impact_wayback_history]
  for i,fn in enumerate(funcs):
   with self.subTest(id=e.IDS[i]): r=fn({},{}); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertFalse(r["executed"]); self.assertGreaterEqual(len(r["effects"]),3)
 def test_ten_selective_recoveries(self):
  cases=[(e.recover_temporary_roles,"role"),(e.recover_managed_groups,"title"),(e.recover_scheduled_messages,"text"),(e.recover_rss_feeds,"url"),(e.recover_telegram_videos,"caption"),(e.recover_blocklists,"enabled"),(e.recover_mandatory_subscriptions,"channels"),(e.recover_signed_webhooks,"url"),(e.recover_quiet_hours,"timezone"),(e.recover_correlated_incidents,"status")]
  for i,(fn,field) in enumerate(cases,10):
   with self.subTest(id=e.IDS[i]): r=fn({field:"new"},{field:"old"},[field]); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertTrue(r["preview"] and r["requires_confirmation"] and not r["applied"]); self.assertEqual(len(r["changes"]),1)
 def test_recovery_rejects_cross_resource_field(self):
  with self.assertRaises(ValueError): e.recover_quiet_hours({}, {"role":"admin"}, ["role"])
if __name__=="__main__": unittest.main()

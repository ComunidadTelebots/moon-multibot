import unittest
import resource_trace_quota_engines as e
class TraceQuotaTests(unittest.TestCase):
 def test_three_traces(self):
  ev=[{"span_id":"r","parent_id":None,"sequence":0,"service":"api","status":"ok"}]
  for i,fn in enumerate((e.trace_master_panels,e.trace_channel_directories,e.trace_external_links)):
   r=fn("t",ev); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertTrue(r["complete"])
 def test_seventeen_quotas(self):
  funcs=[e.quota_admin_sessions,e.quota_community_profiles,e.quota_telegram_communities,e.quota_house_ads,e.quota_voice_notes,e.quota_suspicious_files,e.quota_captcha_decisions,e.quota_managed_bots,e.quota_recurring_reminders,e.quota_security_events,e.quota_regional_maps,e.quota_backups,e.quota_ai_learning_data,e.quota_rich_commands,e.quota_hub_notifications,e.quota_cookie_policies,e.quota_wayback_history]
  for i,fn in enumerate(funcs,3):
   r=fn(100,50,120,.2,80); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["limit"],120); self.assertFalse(r["applied"])
 def test_bounds(self):
  with self.assertRaises(ValueError): e.quota_backups(10,20,30,.5,0)
if __name__=="__main__": unittest.main()

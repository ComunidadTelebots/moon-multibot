import unittest
import resource_approval_signature_engines as e

class ApprovalSignatureTests(unittest.TestCase):
 def test_ten_multilevel_approvals(self):
  funcs=[e.approve_managed_bots,e.approve_recurring_reminders,e.approve_security_events,e.approve_regional_maps,e.approve_backups,e.approve_ai_learning_data,e.approve_rich_commands,e.approve_hub_notifications,e.approve_cookie_policies,e.approve_wayback_history]
  levels=[{"role":"owner","quorum":1}]; votes=[{"actor_id":"u","role":"owner","decision":"approve"}]
  for i,fn in enumerate(funcs):
   with self.subTest(id=e.IDS[i]):
    r=fn(levels,votes); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertTrue(r["execution_authorized"]); self.assertFalse(r["executed"])
 def test_ten_signatures_verify_and_detect_tampering(self):
  funcs=[e.sign_temporary_roles,e.sign_managed_groups,e.sign_scheduled_messages,e.sign_rss_feeds,e.sign_telegram_videos,e.sign_blocklists,e.sign_required_subscriptions,e.sign_signed_webhooks,e.sign_quiet_hours,e.sign_correlated_incidents]; secret="1234567890123456"
  for i,fn in enumerate(funcs,10):
   with self.subTest(id=e.IDS[i]):
    r=fn({"id":"x","state":"ok"},"key-v1",secret); self.assertEqual(r["envelope"]["feature_id"],e.IDS[i]); self.assertTrue(e.verify_signature(r,secret)); self.assertNotIn(secret,str(r)); r["envelope"]["payload"]["state"]="bad"; self.assertFalse(e.verify_signature(r,secret))
 def test_short_secret_rejected(self):
  with self.assertRaises(ValueError): e.sign_temporary_roles({},"key","short")

if __name__=="__main__": unittest.main()

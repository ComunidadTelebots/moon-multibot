import unittest
import resource_diagnostic_history_engines as e

class DiagnosticHistoryTests(unittest.TestCase):
 def test_ten_diagnostics(self):
  funcs=[e.diagnose_managed_bots,e.diagnose_recurring_reminders,e.diagnose_security_events,e.diagnose_regional_maps,e.diagnose_backups,e.diagnose_ai_learning_data,e.diagnose_rich_commands,e.diagnose_hub_notifications,e.diagnose_cookie_policies,e.diagnose_wayback_history]
  for i,fn in enumerate(funcs):
   with self.subTest(id=e.IDS[i]):
    r=fn({}); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertFalse(r["healthy"]); self.assertTrue(r["read_only"])
 def test_ten_historical_comparisons(self):
  funcs=[e.compare_temporary_roles,e.compare_managed_groups,e.compare_scheduled_messages,e.compare_rss_feeds,e.compare_telegram_videos,e.compare_blocklists,e.compare_required_subscriptions,e.compare_signed_webhooks,e.compare_quiet_hours,e.compare_correlated_incidents]
  before=[{"id":"a","state":"old"},{"id":"gone","state":"x"}]; after=[{"id":"a","state":"new"},{"id":"new","state":"x"}]
  for i,fn in enumerate(funcs,10):
   with self.subTest(id=e.IDS[i]):
    r=fn(before,after); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["added"],("new",)); self.assertEqual(r["removed"],("gone",)); self.assertEqual(r["changed"]["a"],("state",)); self.assertEqual(r["change_count"],3)
 def test_duplicate_identity_rejected(self):
  with self.assertRaises(ValueError): e.compare_temporary_roles([{"id":"a"},{"id":"a"}],[])

if __name__=="__main__": unittest.main()

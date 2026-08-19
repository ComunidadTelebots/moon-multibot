import unittest
import resource_autotest_template_engines as e

class AutotestTemplateTests(unittest.TestCase):
 def test_ten_safe_test_plans(self):
  funcs=[e.autotest_managed_bots,e.autotest_recurring_reminders,e.autotest_security_events,e.autotest_regional_maps,e.autotest_backups,e.autotest_ai_learning_data,e.autotest_rich_commands,e.autotest_hub_notifications,e.autotest_cookie_policies,e.autotest_wayback_history]
  for i,fn in enumerate(funcs):
   with self.subTest(id=e.IDS[i]):
    r=fn(["fixture"],["integrity"]); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertFalse(r["executed"]); self.assertTrue(r["sandbox_required"])
 def test_ten_immutable_compositions(self):
  funcs=[e.compose_temporary_roles,e.compose_managed_groups,e.compose_scheduled_messages,e.compose_rss_feeds,e.compose_telegram_videos,e.compose_blocklists,e.compose_required_subscriptions,e.compose_signed_webhooks,e.compose_quiet_hours,e.compose_correlated_incidents]
  layers=[{"enabled":True,"nested":{"a":1}},{"nested":{"b":2}}]
  for i,fn in enumerate(funcs,10):
   with self.subTest(id=e.IDS[i]):
    r=fn(layers); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["template"]["nested"],{"a":1,"b":2}); self.assertTrue(r["immutable"])
  self.assertEqual(layers,[{"enabled":True,"nested":{"a":1}},{"nested":{"b":2}}])
 def test_reserved_key_rejected(self):
  with self.assertRaises(ValueError): e.compose_temporary_roles([{"__class__":"bad"}])

if __name__=="__main__": unittest.main()

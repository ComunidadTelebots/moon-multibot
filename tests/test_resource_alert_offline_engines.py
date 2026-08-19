import unittest
import resource_alert_offline_engines as e

class AlertOfflineTests(unittest.TestCase):
 def test_seventeen_escalable_alerts(self):
  funcs=[e.alert_temporary_roles,e.alert_managed_groups,e.alert_scheduled_messages,e.alert_rss_feeds,e.alert_telegram_videos,e.alert_blocklists,e.alert_required_subscriptions,e.alert_signed_webhooks,e.alert_quiet_hours,e.alert_correlated_incidents,e.alert_accessible_preferences,e.alert_integration_secrets,e.alert_contextual_responses,e.alert_miniapp_menus,e.alert_bot_statistics,e.alert_ad_preferences,e.alert_processing_queues]
  for i,fn in enumerate(funcs):
   with self.subTest(id=e.IDS[i]):
    r=fn("evt","info",8,10); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["severity"],"critical"); self.assertEqual(r["route"],"on_call"); self.assertFalse(r["delivery_requested"])
 def test_three_bounded_offline_queues(self):
  ops=[{"id":"x","action":"update","payload":{"v":1}},{"id":"x","action":"update","payload":{"v":2}}]
  for i,fn in enumerate((e.offline_creator_accounts,e.offline_partner_channels,e.offline_community_campaigns),17):
   with self.subTest(id=e.IDS[i]):
    r=fn(ops); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["queue_count"],1); self.assertEqual(r["deduplicated"],1); self.assertFalse(r["applied"])
 def test_offline_schema_is_strict(self):
  with self.assertRaises(ValueError): e.offline_creator_accounts([{"id":"x","action":"run","payload":{}}])

if __name__=="__main__": unittest.main()

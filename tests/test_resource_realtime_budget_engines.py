import unittest
import resource_realtime_budget_engines as e

class RealtimeBudgetTests(unittest.TestCase):
 def test_seventeen_realtime_snapshots(self):
  funcs=[e.panel_temporary_roles,e.panel_managed_groups,e.panel_scheduled_messages,e.panel_rss_feeds,e.panel_telegram_videos,e.panel_blocklists,e.panel_required_subscriptions,e.panel_signed_webhooks,e.panel_quiet_hours,e.panel_correlated_incidents,e.panel_accessible_preferences,e.panel_integration_secrets,e.panel_contextual_responses,e.panel_miniapp_menus,e.panel_bot_statistics,e.panel_ad_preferences,e.panel_processing_queues]
  for i,fn in enumerate(funcs):
   with self.subTest(id=e.IDS[i]):
    r=fn(5,{"active":3,"errors":0}); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["sequence"],5); self.assertTrue(r["realtime"] and r["snapshot_only"]); self.assertFalse(r["subscribed"])
 def test_three_budget_guardrails(self):
  for i,fn in enumerate((e.budget_creator_accounts,e.budget_partner_channels,e.budget_community_campaigns),17):
   with self.subTest(id=e.IDS[i]):
    ok=fn(100,30,50,"eur"); self.assertEqual(ok["feature_id"],e.IDS[i]); self.assertTrue(ok["allowed"]); self.assertFalse(ok["applied"])
    denied=fn(100,90,20,"EUR"); self.assertEqual(denied["decision"],"deny")
 def test_invalid_metric_rejected(self):
  with self.assertRaises(ValueError): e.panel_temporary_roles(1,{"secret":"text"})

if __name__=="__main__": unittest.main()

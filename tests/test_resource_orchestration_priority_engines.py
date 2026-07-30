import unittest,resource_orchestration_priority_engines as e
class OrchestrationPriorityTests(unittest.TestCase):
 def test_seventeen_orchestrators_plan_without_execution(self):
  cases=[(e.orchestrate_temporary_roles,"role_expiring"),(e.orchestrate_managed_groups,"group_added"),(e.orchestrate_scheduled_messages,"message_due"),(e.orchestrate_rss_feeds,"entry_found"),(e.orchestrate_telegram_videos,"video_received"),(e.orchestrate_blocklists,"list_updated"),(e.orchestrate_mandatory_subscriptions,"member_joined"),(e.orchestrate_signed_webhooks,"delivery_due"),(e.orchestrate_quiet_hours,"quiet_started"),(e.orchestrate_correlated_incidents,"signal_linked"),(e.orchestrate_accessible_preferences,"preference_changed"),(e.orchestrate_integration_secrets,"rotation_due"),(e.orchestrate_contextual_responses,"intent_detected"),(e.orchestrate_miniapp_menus,"role_changed"),(e.orchestrate_bot_statistics,"window_closed"),(e.orchestrate_ad_preferences,"consent_changed"),(e.orchestrate_processing_queues,"task_queued")]
  resources=set()
  for i,(fn,event) in enumerate(cases):
   with self.subTest(id=e.IDS[i]): r=fn({"id":"evt-1","type":event}); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertFalse(r["executed"]); self.assertEqual(len(r["planned_steps"]),2); resources.add(r["resource"])
  self.assertEqual(len(resources),17)
 def test_three_adaptive_priorities_are_explainable(self):
  funcs=[e.prioritize_creator_account,e.prioritize_associated_channel,e.prioritize_community_campaign]
  for i,fn in enumerate(funcs,17):
   with self.subTest(id=e.IDS[i]): r=fn({"risk":50,"pending_reviews":2,"days_inactive":3,"delivery_failures":2,"permission_gaps":1,"stale_hours":5,"hours_to_send":2,"pending_approval":1,"delivery_risk":20}); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertTrue(r["adaptive"]); self.assertFalse(r["automatic_action"]); self.assertGreaterEqual(len(r["components"]),3)
 def test_unknown_event_rejected(self):
  with self.assertRaises(ValueError): e.orchestrate_rss_feeds({"type":"unknown"})
if __name__=="__main__": unittest.main()

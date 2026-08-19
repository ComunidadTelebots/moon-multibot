import unittest
import resource_federation_reconcile_engines as e

class FederationReconcileTests(unittest.TestCase):
 def test_ten_federated_plans(self):
  funcs=[e.federate_managed_bots,e.federate_recurring_reminders,e.federate_security_events,e.federate_regional_maps,e.federate_backups,e.federate_ai_learning_data,e.federate_rich_commands,e.federate_hub_notifications,e.federate_cookie_policies,e.federate_wayback_history]
  change={"node":"n","entity_id":"x","revision":1,"payload":{}}
  for i,fn in enumerate(funcs):
   with self.subTest(id=e.IDS[i]):
    r=fn([change],["n"]); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertTrue(r["ready"]); self.assertFalse(r["applied"])
 def test_ten_reconciliation_plans(self):
  funcs=[e.reconcile_temporary_roles,e.reconcile_managed_groups,e.reconcile_scheduled_messages,e.reconcile_rss_feeds,e.reconcile_telegram_videos,e.reconcile_blocklists,e.reconcile_required_subscriptions,e.reconcile_signed_webhooks,e.reconcile_quiet_hours,e.reconcile_correlated_incidents]
  conflict={"entity_id":"x","candidates":[{"node":"a","revision":1,"payload":{"v":1}},{"node":"b","revision":2,"payload":{"v":2}}]}
  for i,fn in enumerate(funcs,10):
   with self.subTest(id=e.IDS[i]):
    r=fn([conflict],"newest"); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["resolved"][0]["node"],"b"); self.assertTrue(r["ready"] and r["dry_run"]); self.assertFalse(r["applied"])
 def test_tied_newest_remains_unresolved(self):
  c={"entity_id":"x","candidates":[{"node":"a","revision":2,"payload":{}},{"node":"b","revision":2,"payload":{}}]}
  r=e.reconcile_temporary_roles([c],"newest"); self.assertFalse(r["ready"]); self.assertEqual(r["unresolved"],("x",))

if __name__=="__main__": unittest.main()

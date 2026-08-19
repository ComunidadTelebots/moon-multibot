import unittest
import resource_reconcile_anonymize_engines as e

class ReconcileAnonymizeTests(unittest.TestCase):
 def test_seven_reconciliation_plans(self):
  funcs=[e.reconcile_accessible_preferences,e.reconcile_integration_secrets,e.reconcile_contextual_responses,e.reconcile_miniapp_menus,e.reconcile_bot_statistics,e.reconcile_ad_preferences,e.reconcile_processing_queues]
  conflict={"entity_id":"x","candidates":[{"node":"a","revision":1,"payload":{}},{"node":"b","revision":2,"payload":{}}]}
  for i,fn in enumerate(funcs):
   with self.subTest(id=e.IDS[i]):
    r=fn([conflict],"newest"); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertTrue(r["ready"]); self.assertFalse(r["applied"])
 def test_thirteen_verifiable_anonymizers(self):
  funcs=[e.anonymize_creator_accounts,e.anonymize_partner_channels,e.anonymize_community_campaigns,e.anonymize_editorial_articles,e.anonymize_moderated_images,e.anonymize_user_appeals,e.anonymize_mtproto_proxies,e.anonymize_persistent_tasks,e.anonymize_moderation_rules,e.anonymize_language_metrics,e.anonymize_community_translations,e.anonymize_personal_consents,e.anonymize_telegram_reactions]
  secret="1234567890123456"; rows=[{"id":"private-user","email":"secret@example.com","status":"active"}]
  for i,fn in enumerate(funcs,7):
   with self.subTest(id=e.IDS[i]):
    r=fn(rows,["id","email"],secret); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(len(r["proof"]),64); self.assertTrue(r["verifiable"]); self.assertNotIn("private-user",str(r)); self.assertNotIn("secret@example.com",str(r)); self.assertNotIn(secret,str(r))
 def test_short_secret_rejected(self):
  with self.assertRaises(ValueError): e.anonymize_creator_accounts([], ["id"], "short")

if __name__=="__main__": unittest.main()

import unittest
import resource_budget_federation_engines as e

class BudgetFederationTests(unittest.TestCase):
 def test_thirteen_budget_controls(self):
  funcs=[e.budget_editorial_articles,e.budget_moderated_images,e.budget_user_appeals,e.budget_mtproto_proxies,e.budget_persistent_tasks,e.budget_moderation_rules,e.budget_language_metrics,e.budget_community_translations,e.budget_personal_consents,e.budget_telegram_reactions,e.budget_master_panels,e.budget_channel_directories,e.budget_external_links]
  for i,fn in enumerate(funcs):
   with self.subTest(id=e.IDS[i]):
    r=fn(10,8,3,"usd"); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["decision"],"deny"); self.assertFalse(r["applied"])
 def test_seven_federated_dry_runs(self):
  funcs=[e.federate_admin_sessions,e.federate_community_profiles,e.federate_telegram_communities,e.federate_house_ads,e.federate_voice_notes,e.federate_suspicious_files,e.federate_captcha_decisions]
  changes=[{"node":"a","entity_id":"x","revision":1,"payload":{"v":1}},{"node":"b","entity_id":"x","revision":2,"payload":{"v":2}}]
  for i,fn in enumerate(funcs,13):
   with self.subTest(id=e.IDS[i]):
    r=fn(changes,["a","b"]); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["accepted"][0]["revision"],2); self.assertTrue(r["ready"] and r["dry_run"]); self.assertFalse(r["applied"])
 def test_same_revision_conflict_is_explicit(self):
  c=[{"node":"a","entity_id":"x","revision":2,"payload":{"v":1}},{"node":"b","entity_id":"x","revision":2,"payload":{"v":2}}]
  r=e.federate_admin_sessions(c,["a","b"]); self.assertFalse(r["ready"]); self.assertEqual(r["conflicts"][0]["entity_id"],"x")

if __name__=="__main__": unittest.main()

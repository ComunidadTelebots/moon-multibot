import unittest
import resource_history_semantic_engines as e

class HistorySemanticTests(unittest.TestCase):
 def test_seven_comparisons(self):
  funcs=[e.compare_accessible_preferences,e.compare_integration_secrets,e.compare_contextual_responses,e.compare_miniapp_menus,e.compare_bot_statistics,e.compare_ad_preferences,e.compare_processing_queues]
  for i,fn in enumerate(funcs):
   with self.subTest(id=e.IDS[i]):
    r=fn([{"id":"x","v":1}],[{"id":"x","v":2}]); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["changed"],{"x":("v",)}); self.assertTrue(r["read_only"])
 def test_thirteen_local_searches(self):
  funcs=[e.search_creator_accounts,e.search_partner_channels,e.search_community_campaigns,e.search_editorial_articles,e.search_moderated_images,e.search_user_appeals,e.search_mtproto_proxies,e.search_persistent_tasks,e.search_moderation_rules,e.search_language_metrics,e.search_community_translations,e.search_personal_consents,e.search_telegram_reactions]
  docs=[{"id":"b","text":"telegram comunidad tecnologia"},{"id":"a","text":"tecnologia telegram"},{"id":"z","text":"cocina"}]
  for i,fn in enumerate(funcs,7):
   with self.subTest(id=e.IDS[i]):
    r=fn("telegram tecnologia",docs); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["results"][0]["id"],"a"); self.assertEqual(len(r["results"]),2); self.assertTrue(r["local_only"] and r["deterministic"])
 def test_search_rejects_invalid_documents(self):
  with self.assertRaises(ValueError): e.search_creator_accounts("valid",[{"id":"x"}])

if __name__=="__main__": unittest.main()

import unittest
import resource_template_bulk_engines as e

class TemplateBulkTests(unittest.TestCase):
 def test_seven_templates(self):
  funcs=[e.compose_accessible_preferences,e.compose_integration_secrets,e.compose_contextual_responses,e.compose_miniapp_menus,e.compose_bot_statistics,e.compose_ad_preferences,e.compose_processing_queues]
  for i,fn in enumerate(funcs):
   with self.subTest(id=e.IDS[i]):
    r=fn([{"a":1},{"b":2}]); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["template"],{"a":1,"b":2})
 def test_thirteen_reversible_bulk_plans(self):
  funcs=[e.bulk_creator_accounts,e.bulk_partner_channels,e.bulk_community_campaigns,e.bulk_editorial_articles,e.bulk_moderated_images,e.bulk_user_appeals,e.bulk_mtproto_proxies,e.bulk_persistent_tasks,e.bulk_moderation_rules,e.bulk_language_metrics,e.bulk_community_translations,e.bulk_personal_consents,e.bulk_telegram_reactions]
  for i,fn in enumerate(funcs,7):
   with self.subTest(id=e.IDS[i]):
    r=fn(["a","b","a"],"archive"); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["target_count"],2); self.assertEqual(r["rollback"][0]["action"],"restore"); self.assertTrue(r["dry_run"] and r["reversible"]); self.assertFalse(r["applied"])
 def test_irreversible_action_rejected(self):
  with self.assertRaises(ValueError): e.bulk_creator_accounts(["x"],"delete")

if __name__=="__main__": unittest.main()

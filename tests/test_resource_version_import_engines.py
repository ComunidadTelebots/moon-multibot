import unittest,resource_version_import_engines as e
class VersionImportTests(unittest.TestCase):
 def test_seven_semantic_versions(self):
  funcs=[e.version_accessible_preferences,e.version_integration_secrets,e.version_contextual_responses,e.version_miniapp_menus,e.version_bot_statistics,e.version_ad_preferences,e.version_processing_queues]
  for i,fn in enumerate(funcs):
   with self.subTest(id=e.IDS[i]): r=fn("2.3.4","patch",["validated change"]); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["version"],"2.3.5")
 def test_thirteen_transactional_importers(self):
  cases=[(e.import_creator_accounts,{"id":"u1","role":"creator","verified":True}),(e.import_associated_channels,{"chat_id":"c1","title":"Canal","type":"channel"}),(e.import_community_campaigns,{"id":"a1","text":"Texto","status":"draft"}),(e.import_editorial_articles,{"slug":"one","title":"Título","body":"Body"}),(e.import_moderated_images,{"sha256":"a"*64,"verdict":"safe","size":1}),(e.import_user_appeals,{"id":"ap1","user_id":"u1","status":"pending"}),(e.import_mtproto_proxies,{"id":"p1","server":"host","port":443}),(e.import_persistent_tasks,{"id":"t1","owner_id":"u1","title":"Task"}),(e.import_moderation_rules,{"id":"r1","condition":{"links":1},"action":"review"}),(e.import_language_metrics,{"locale":"es","samples":1,"confidence":.9}),(e.import_community_translations,{"key":"hello","locale":"es","value":"Hola"}),(e.import_personal_consents,{"id":"co1","user_id":"u1","purpose":"analytics","granted":True}),(e.import_telegram_reactions,{"id":"re1","message_id":"m1","reaction":"like"})]
  for i,(fn,row) in enumerate(cases,7):
   with self.subTest(id=e.IDS[i]): r=fn([row]); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertTrue(r["valid"] and r["atomic"]); self.assertFalse(r["applied"]); self.assertTrue(r["requires_confirmation"])
 def test_duplicate_rolls_back_entire_plan(self):
  row={"id":"t1","owner_id":"u1","title":"Task"}; r=e.import_persistent_tasks([row,row]); self.assertFalse(r["valid"]); self.assertFalse(r["applied"]); self.assertEqual(len(r["errors"]),1)
if __name__=="__main__": unittest.main()

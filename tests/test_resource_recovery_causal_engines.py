import unittest,resource_recovery_causal_engines as e
class RecoveryCausalTests(unittest.TestCase):
 def test_seven_recovery_contracts(self):
  cases=[(e.recover_accessible_preferences,"font_scale"),(e.recover_integration_secrets,"active_version"),(e.recover_contextual_responses,"confidence"),(e.recover_miniapp_menus,"locale"),(e.recover_bot_statistics,"window"),(e.recover_ad_preferences,"personalized"),(e.recover_processing_queues,"priority")]
  for i,(fn,field) in enumerate(cases):
   with self.subTest(id=e.IDS[i]): r=fn({field:1},{field:2},[field]); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertTrue(r["preview"] and not r["applied"])
 def test_thirteen_causal_audits_have_resource_schema(self):
  schemas=[(e.audit_creator_accounts,{"verification":"yes","role_change":"none","active":1}),(e.audit_associated_channels,{"bot_permission":"full","posting_mode":"auto","delivery_ratio":1}),(e.audit_community_campaigns,{"placement":"top","schedule":"day","click_ratio":1}),(e.audit_editorial_articles,{"category":"tech","reviewed":True,"reading_seconds":1}),(e.audit_moderated_images,{"scanner":"local","threshold":.5,"false_positive":1}),(e.audit_user_appeals,{"reason":"spam","reviewer_role":"admin","approved":1}),(e.audit_mtproto_proxies,{"region":"eu","transport":"tcp","latency_ms":1}),(e.audit_persistent_tasks,{"priority":"high","has_deadline":True,"completion_hours":1}),(e.audit_moderation_rules,{"rule_type":"links","action":"warn","appealed":1}),(e.audit_language_metrics,{"detector":"local","script":"latin","confidence":1}),(e.audit_community_translations,{"locale":"es","review_count":1,"accepted":1}),(e.audit_personal_consents,{"purpose":"analytics","prompt_version":"v1","granted":1}),(e.audit_telegram_reactions,{"reaction":"like","message_type":"text","retained":1})]
  for offset,(fn,row) in enumerate(schemas,7):
   other=dict(row); other[next(iter(row))]="other"; other[list(row)[-1]]=0
   with self.subTest(id=e.IDS[offset]): r=fn([row,other]); self.assertEqual(r["feature_id"],e.IDS[offset]); self.assertFalse(r["causal_claim"]); self.assertGreaterEqual(len(r["causes"]),2)
 def test_wrong_causal_schema_is_rejected(self):
  with self.assertRaises(ValueError): e.audit_creator_accounts([{"active":1},{"active":0}])
if __name__=="__main__": unittest.main()

import unittest,resource_causal_validation_engines as e
class CausalValidationTests(unittest.TestCase):
 def test_three_causal_contracts(self):
  cases=[(e.audit_master_panels,{"role":"admin","session_mode":"web","action_success":1}),(e.audit_channel_directories,{"category":"tech","verified":True,"click_ratio":1}),(e.audit_external_links,{"scheme":"https","scanner_verdict":"safe","opened":1})]
  for i,(fn,row) in enumerate(cases):
   other=dict(row); other[next(iter(row))]="other"; other[list(row)[-1]]=0
   with self.subTest(id=e.IDS[i]): r=fn([row,other]); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertFalse(r["causal_claim"])
 def test_seventeen_continuous_validators_have_unique_resources(self):
  funcs=[e.validate_admin_sessions,e.validate_community_profiles,e.validate_telegram_communities,e.validate_house_ads,e.validate_voice_notes,e.validate_suspicious_files,e.validate_captcha_decisions,e.validate_managed_bots,e.validate_recurring_reminders,e.validate_security_events,e.validate_regional_maps,e.validate_backups,e.validate_ai_learning_data,e.validate_rich_commands,e.validate_hub_notifications,e.validate_cookie_policies,e.validate_wayback_history]
  resources=set()
  for i,fn in enumerate(funcs,3):
   with self.subTest(id=e.IDS[i]): r=fn({}); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertFalse(r["valid"]); self.assertTrue(r["continuous"]); self.assertGreaterEqual(len(r["errors"]),3); resources.add(r["resource"])
  self.assertEqual(len(resources),17)
 def test_valid_session_passes(self): self.assertTrue(e.validate_admin_sessions({"session_id":"session-1","mfa":True,"expires_in":60})["valid"])
if __name__=="__main__": unittest.main()

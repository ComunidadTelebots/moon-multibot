import unittest
import resource_retention_consent_engines as e

class RetentionConsentTests(unittest.TestCase):
 def test_seventeen_retention_contracts(self):
  funcs=[e.retain_temporary_roles,e.retain_managed_groups,e.retain_scheduled_messages,e.retain_rss_feeds,e.retain_telegram_videos,e.retain_blocklists,e.retain_required_subscriptions,e.retain_signed_webhooks,e.retain_quiet_hours,e.retain_correlated_incidents,e.retain_accessible_preferences,e.retain_integration_secrets,e.retain_contextual_responses,e.retain_miniapp_menus,e.retain_bot_statistics,e.retain_ad_preferences,e.retain_processing_queues]
  for i,fn in enumerate(funcs):
   with self.subTest(id=e.IDS[i]):
    active=fn("subject-1",30,"operational",False); self.assertEqual(active["feature_id"],e.IDS[i]); self.assertEqual(active["action"],"retain"); self.assertTrue(active["auditable"])
    revoked=fn("subject-1",30,"operational",True); self.assertEqual(revoked["action"],"purge")
    held=fn("subject-1",30,"legal",True,True); self.assertEqual(held["action"],"retain")
 def test_three_granular_consent_contracts(self):
  for i,fn in enumerate((e.consent_creator_accounts,e.consent_partner_channels,e.consent_community_campaigns),17):
   with self.subTest(id=e.IDS[i]):
    result=fn("subject-1",["read","publish","read"],True,"v1")
    self.assertEqual(result["feature_id"],e.IDS[i]); self.assertEqual(result["scopes"],("publish","read")); self.assertEqual(result["decision"],"allow")
 def test_invalid_inputs_fail_closed(self):
  with self.assertRaises(ValueError): e.retain_temporary_roles("x",0,"reason")
  with self.assertRaises(ValueError): e.consent_creator_accounts("x",["root"],True,"v1")

if __name__=="__main__": unittest.main()

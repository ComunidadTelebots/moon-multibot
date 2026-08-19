import unittest,resource_delegation_version_engines as e
NOW="2026-07-30T10:00:00+00:00"; END="2026-07-31T10:00:00+00:00"
class DelegationVersionTests(unittest.TestCase):
 def test_ten_delegations(self):
  cases=[(e.delegate_managed_bot,"pause"),(e.delegate_recurring_reminder,"edit_schedule"),(e.delegate_security_event,"triage"),(e.delegate_regional_map,"edit_regions"),(e.delegate_backup,"verify"),(e.delegate_ai_learning_data,"review_consent"),(e.delegate_rich_command,"test_render"),(e.delegate_hub_notification,"draft"),(e.delegate_cookie_policy,"edit_draft"),(e.delegate_wayback_history,"lookup")]
  for i,(fn,scope) in enumerate(cases):
   with self.subTest(id=e.IDS[i]): r=fn(grant_id=f"grant-{i}",actor_id="owner",delegate_id="worker",scopes=[scope],expires_at=END,now=NOW); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertTrue(r["revocable"])
 def test_ten_semantic_versions(self):
  funcs=[e.version_temporary_roles,e.version_managed_groups,e.version_scheduled_messages,e.version_rss_feeds,e.version_telegram_videos,e.version_blocklists,e.version_mandatory_subscriptions,e.version_signed_webhooks,e.version_quiet_hours,e.version_correlated_incidents]
  for i,fn in enumerate(funcs,10):
   with self.subTest(id=e.IDS[i]): r=fn("1.2.3","minor",["schema changed"]); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["version"],"1.3.0"); self.assertTrue(r["immutable_release"])
 def test_bad_version_rejected(self):
  with self.assertRaises(ValueError): e.version_rss_feeds("latest","patch",["x"])
if __name__=="__main__": unittest.main()

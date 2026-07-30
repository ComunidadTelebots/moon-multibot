import unittest,resource_priority_delegation_engines as e
NOW="2026-07-30T10:00:00+00:00"; END="2026-07-31T10:00:00+00:00"
class PriorityDelegationTests(unittest.TestCase):
 def test_thirteen_priorities(self):
  funcs=[e.prioritize_editorial_article,e.prioritize_moderated_image,e.prioritize_user_appeal,e.prioritize_mtproto_proxy,e.prioritize_persistent_task,e.prioritize_moderation_rule,e.prioritize_language_metric,e.prioritize_community_translation,e.prioritize_personal_consent,e.prioritize_telegram_reaction,e.prioritize_master_panel,e.prioritize_channel_directory,e.prioritize_external_link]
  for i,fn in enumerate(funcs):
   with self.subTest(id=e.IDS[i]): r=fn({}); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertFalse(r["automatic_action"]); self.assertEqual(len(r["components"]),3)
 def test_seven_delegations_have_distinct_scopes(self):
  cases=[(e.delegate_admin_session,"view"),(e.delegate_community_profile,"review"),(e.delegate_telegram_community,"sync"),(e.delegate_house_ad,"edit_draft"),(e.delegate_voice_note,"request_transcription"),(e.delegate_suspicious_file,"request_scan"),(e.delegate_captcha_decision,"review_appeal")]
  for i,(fn,scope) in enumerate(cases,13):
   with self.subTest(id=e.IDS[i]): r=fn(grant_id=f"grant-{i}",actor_id="owner",delegate_id="worker",scopes=[scope],expires_at=END,now=NOW); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertTrue(r["revocable"] and r["active"])
 def test_delegation_rejects_overlong_grant(self):
  with self.assertRaises(ValueError): e.delegate_admin_session(grant_id="grant-x",actor_id="a",delegate_id="b",scopes=["view"],now=NOW,expires_at="2027-01-01T00:00:00+00:00")
if __name__=="__main__": unittest.main()

import unittest
from datetime import datetime, timezone
import resource_expiry_approval_engines as e

class ExpiryApprovalTests(unittest.TestCase):
 def test_thirteen_expiry_decisions(self):
  funcs=[e.expire_editorial_articles,e.expire_moderated_images,e.expire_user_appeals,e.expire_mtproto_proxies,e.expire_persistent_tasks,e.expire_moderation_rules,e.expire_language_metrics,e.expire_community_translations,e.expire_personal_consents,e.expire_telegram_reactions,e.expire_master_panels,e.expire_channel_directories,e.expire_external_links]
  now=datetime(2026,2,1,tzinfo=timezone.utc)
  for i,fn in enumerate(funcs):
   with self.subTest(id=e.IDS[i]):
    r=fn("2026-01-01T00:00:00Z",0,now); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertTrue(r["expired"]); self.assertFalse(r["applied"])
 def test_seven_multilevel_approvals(self):
  funcs=[e.approve_admin_sessions,e.approve_community_profiles,e.approve_telegram_communities,e.approve_house_ads,e.approve_voice_notes,e.approve_suspicious_files,e.approve_captcha_decisions]
  levels=[{"role":"owner","quorum":1},{"role":"security","quorum":2}]; decisions=[{"actor_id":"o","role":"owner","decision":"approve"},{"actor_id":"s1","role":"security","decision":"approve"},{"actor_id":"s2","role":"security","decision":"approve"}]
  for i,fn in enumerate(funcs,13):
   with self.subTest(id=e.IDS[i]):
    r=fn(levels,decisions); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["status"],"approved"); self.assertTrue(r["execution_authorized"]); self.assertFalse(r["executed"])
 def test_rejection_is_binding(self):
  r=e.approve_admin_sessions([{"role":"owner","quorum":1}],[{"actor_id":"o","role":"owner","decision":"reject"}]); self.assertEqual(r["status"],"rejected"); self.assertFalse(r["execution_authorized"])

if __name__=="__main__": unittest.main()

import unittest
import resource_consent_diagnostic_engines as e

class ConsentDiagnosticTests(unittest.TestCase):
 def test_thirteen_granular_consents(self):
  funcs=[e.consent_editorial_articles,e.consent_moderated_images,e.consent_user_appeals,e.consent_mtproto_proxies,e.consent_persistent_tasks,e.consent_moderation_rules,e.consent_language_metrics,e.consent_community_translations,e.consent_personal_consents,e.consent_telegram_reactions,e.consent_master_panels,e.consent_channel_directories,e.consent_external_links]
  for i,fn in enumerate(funcs):
   with self.subTest(id=e.IDS[i]):
    r=fn("subject",["read","write"],False,"v2"); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["decision"],"deny"); self.assertTrue(r["auditable"])
 def test_seven_autonomous_diagnostics(self):
  funcs=[e.diagnose_admin_sessions,e.diagnose_community_profiles,e.diagnose_telegram_communities,e.diagnose_house_ads,e.diagnose_voice_notes,e.diagnose_suspicious_files,e.diagnose_captcha_decisions]
  for i,fn in enumerate(funcs,13):
   with self.subTest(id=e.IDS[i]):
    degraded=fn({}); self.assertEqual(degraded["feature_id"],e.IDS[i]); self.assertFalse(degraded["healthy"]); self.assertTrue(degraded["read_only"]); self.assertTrue(degraded["missing_checks"])
    healthy=fn({k:True for k in degraded["missing_checks"]}); self.assertTrue(healthy["healthy"])
 def test_diagnostic_rejects_non_mapping(self):
  with self.assertRaises(ValueError): e.diagnose_admin_sessions([])

if __name__=="__main__": unittest.main()

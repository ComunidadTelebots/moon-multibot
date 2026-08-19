import unittest,resource_import_export_engines as e
SECRET="1234567890123456"
class ImportExportTests(unittest.TestCase):
 def test_three_transactional_imports(self):
  cases=[(e.import_master_panels,{"id":"p1","layout":{},"role":"master"}),(e.import_channel_directories,{"chat_id":"c1","title":"Canal","category":"tech"}),(e.import_external_links,{"id":"l1","url":"https://example.com","verdict":"safe"})]
  for i,(fn,row) in enumerate(cases):
   with self.subTest(id=e.IDS[i]): r=fn([row]); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertTrue(r["atomic"] and not r["applied"])
 def test_seventeen_signed_minimized_exports(self):
  funcs=[e.export_admin_sessions,e.export_community_profiles,e.export_telegram_communities,e.export_house_ads,e.export_voice_notes,e.export_suspicious_files,e.export_captcha_decisions,e.export_managed_bots,e.export_recurring_reminders,e.export_security_events,e.export_regional_maps,e.export_backups,e.export_ai_learning_data,e.export_rich_commands,e.export_hub_notifications,e.export_cookie_policies,e.export_wayback_history]
  for i,fn in enumerate(funcs,3):
   with self.subTest(id=e.IDS[i]): r=fn([{"email":"secret","token":"secret","transcript":"secret","requested_by":"secret"}],SECRET); self.assertEqual(r["envelope"]["feature_id"],e.IDS[i]); self.assertTrue(r["signed"]); self.assertEqual(len(r["signature"]),64); self.assertNotIn(SECRET,str(r))
 def test_short_secret_rejected(self):
  with self.assertRaises(ValueError): e.export_backups([],"short")
if __name__=="__main__": unittest.main()

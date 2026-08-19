import unittest
from datetime import datetime, timezone
import resource_duplicate_expiry_engines as e

class DuplicateExpiryTests(unittest.TestCase):
 def test_seventeen_duplicate_detectors(self):
  funcs=[e.duplicates_temporary_roles,e.duplicates_managed_groups,e.duplicates_scheduled_messages,e.duplicates_rss_feeds,e.duplicates_telegram_videos,e.duplicates_blocklists,e.duplicates_required_subscriptions,e.duplicates_signed_webhooks,e.duplicates_quiet_hours,e.duplicates_correlated_incidents,e.duplicates_accessible_preferences,e.duplicates_integration_secrets,e.duplicates_contextual_responses,e.duplicates_miniapp_menus,e.duplicates_bot_statistics,e.duplicates_ad_preferences,e.duplicates_processing_queues]
  rows=[{"id":"a","name":" Same "},{"id":"b","name":"same"},{"id":"c","name":"other"}]
  for i,fn in enumerate(funcs):
   with self.subTest(id=e.IDS[i]):
    r=fn(rows,["name"]); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertEqual(r["duplicate_record_count"],2); self.assertEqual(r["duplicate_groups"][0]["ids"],("a","b")); self.assertNotIn("same",str(r).lower()); self.assertFalse(r["raw_values_included"])
 def test_three_expiry_decisions(self):
  now=datetime(2026,1,10,tzinfo=timezone.utc)
  for i,fn in enumerate((e.expire_creator_accounts,e.expire_partner_channels,e.expire_community_campaigns),17):
   with self.subTest(id=e.IDS[i]):
    r=fn("2026-01-01T00:00:00+00:00",5,now); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertTrue(r["expired"]); self.assertFalse(r["applied"])
 def test_naive_timestamp_rejected(self):
  with self.assertRaises(ValueError): e.expire_creator_accounts("2026-01-01T00:00:00")

if __name__=="__main__": unittest.main()

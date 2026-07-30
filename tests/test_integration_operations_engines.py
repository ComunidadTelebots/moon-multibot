import unittest
import integration_operations_engines as e
from core.feature_runtime import registry,list_features
class IntegrationOperationsTests(unittest.TestCase):
 def test_future_2665(self):
  rows=[{"event_id":"e1","integration_id":"calendar-1","kind":"timeout","occurred_at":"2026-07-30T10:00:00Z"},{"event_id":"e2","integration_id":"calendar-1","kind":"timeout","occurred_at":"2026-07-30T10:01:00Z"}];r=e.correlate_integration_incidents(rows);self.assertEqual(r["incidents"][0]["count"],2);self.assertFalse(r["automatic_action"])
  with self.assertRaises(ValueError):e.correlate_integration_incidents([{"event_id":"e3","integration_id":"calendar-1","kind":"timeout","occurred_at":"2026-07-30T10:00:00"}])
 def test_future_2667(self):
  r=e.delegate_integration_access("g1","owner-1","admin-2",["integration:read"],"2026-07-31T10:00:00Z","2026-07-30T10:00:00Z");self.assertTrue(r["revocable"]);self.assertFalse(r["applied"])
  with self.assertRaises(ValueError):e.delegate_integration_access("g1","same","same",["integration:read"],"2026-07-31T10:00:00Z","2026-07-30T10:00:00Z")
 def test_registry_role_and_schema(self):
  registry.cache_clear();r=registry()
  for fid in e.IDS:
   self.assertEqual(r[fid]["minimum_role"],"group_creator")
  listed={x["id"]:x for x in list_features("group_creator")}
  self.assertTrue(all(fid in listed and listed[fid]["input_schema"]["parameters"] for fid in e.IDS))
  admin_ids={x["id"] for x in list_features("group_admin")}
  self.assertTrue(all(fid not in admin_ids for fid in e.IDS))
if __name__=="__main__":unittest.main()

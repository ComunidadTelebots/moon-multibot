import ast,importlib,socket,unittest
from unittest import mock
import resource_energy_abuse_migration_federation_engines as e
from resource_energy_abuse_migration_federation_manifest import MANIFEST,CHANGELOG_APIS,VERSION_PROPOSAL
MASTER={"id":"master-1","roles":["master"],"scopes":[]}; VIEWER={"id":"viewer-1","roles":["viewer"],"scopes":[]}
class PerFeature(unittest.TestCase):pass
def build(i):
 def test(self):
  api=e.ALL_APIS[i]
  if i<17:r=api([{"workload_id":"work-1","energy_wh":20,"items":10}],actor=MASTER,target_reduction=20);self.assertEqual(r["plans"][0]["target_wh_per_item"],1.6)
  elif i<33:r=api([{"event_id":"ev-1","subject_id":"user-1","occurred_at":"2026-07-30T10:00:00Z"}],{"window_seconds":60,"limit":1,"burst":0},actor=MASTER);self.assertFalse(r["decisions"][0]["limited"])
  elif i<50:r=api([{"id":"item-1","name":"ok"}],{"source_version":"v1","target_version":"v2","required_fields":["name"]},actor=MASTER);self.assertEqual(r["ready_count"],1);self.assertFalse(r["applied"])
  else:r=api({"origin":"node-1","subject_id":"item-1","schema_version":"v1","issued_at":"2026-07-30T10:00:00Z","expires_at":"2026-07-31T10:00:00Z"},{"allowed_origins":["node-1"],"schema_versions":["v1"]},actor=MASTER);self.assertTrue(r["compatible"]);self.assertFalse(r["network_requested"])
  self.assertEqual(r["feature_id"],e.IDS[i]);self.assertFalse(r["executed"])
 return test
for i,fid in enumerate(e.IDS):setattr(PerFeature,f"test_{fid.replace('-','_')}",build(i))
class Security(unittest.TestCase):
 def test_manifest(self):
  self.assertEqual([x["id"] for x in MANIFEST],[f"future-{n}" for n in range(5702,5880,3)]);self.assertEqual(len(set(CHANGELOG_APIS)),60);self.assertEqual(VERSION_PROPOSAL,"v18.23.3");self.assertTrue(all(x["roles"][0]=="master" and callable(getattr(importlib.import_module(x["module"][:-3]),x["api"])) for x in MANIFEST))
 def test_auth_all_families(self):
  calls=[lambda:e.ENERGY_APIS[0]([],actor=VIEWER),lambda:e.ABUSE_APIS[0]([],{},actor=VIEWER),lambda:e.MIGRATION_APIS[0]([],{},actor=VIEWER),lambda:e.FEDERATION_APIS[0]({}, {},actor=VIEWER)]
  for call in calls:
   with self.assertRaises(PermissionError):call()
 def test_secrets_rejected(self):
  with self.assertRaises(ValueError):e.ENERGY_APIS[0]([{"api_token":"x"}],actor=MASTER)
  with self.assertRaises(ValueError):e.FEDERATION_APIS[0]({"token":"x"},{},actor=MASTER)
 def test_abuse_never_bans(self):
  rows=[{"event_id":f"e-{i}","subject_id":"u-1","occurred_at":"2026-07-30T10:00:00Z"} for i in range(3)]
  r=e.ABUSE_APIS[0](rows,{"window_seconds":60,"limit":1,"burst":0},actor=MASTER);self.assertTrue(r["decisions"][0]["limited"]);self.assertFalse(r["automatic_ban"])
 def test_migration_xss_not_reflected(self):
  r=e.MIGRATION_APIS[0]([{"id":"<script>alert(1)</script>"}],{"source_version":"v1","target_version":"v2","required_fields":[]},actor=MASTER);self.assertEqual(r["checks"][0]["record_id"],"invalid-at-0");self.assertNotIn("<script>",str(r))
 def test_federation_no_network(self):
  env={"origin":"node-1","subject_id":"x-1","schema_version":"v1","issued_at":"2026-07-30T10:00:00Z","expires_at":"2026-07-31T10:00:00Z"}
  with mock.patch("socket.create_connection") as n:r=e.FEDERATION_APIS[0](env,{"allowed_origins":[],"schema_versions":[]},actor=MASTER)
  n.assert_not_called();self.assertFalse(r["compatible"])
 def test_energy_nonfinite_rejected(self):
  with self.assertRaises(ValueError):e.ENERGY_APIS[0]([{"workload_id":"x","energy_wh":float('inf'),"items":1}],actor=MASTER)
  with self.assertRaises(ValueError):e.ENERGY_APIS[0]([{"workload_id":"x","energy_wh":1e308,"items":1},{"workload_id":"x","energy_wh":1e308,"items":1}],actor=MASTER)
if __name__=="__main__":unittest.main()

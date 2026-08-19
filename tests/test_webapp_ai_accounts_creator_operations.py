import hashlib
import hmac
import inspect
import unittest

import webapp_ai_accounts_creator_operations as o
from webapp_ai_accounts_creator_operations_manifest import FEATURES


def cases():
 return {
1982:lambda:o.recommend_ai_config({"privacy_incidents":1},{})["recommendations"][0]["key"]=="learning_enabled",
1983:lambda:o.test_ai_config({"confidence_threshold":.8,"safe_fallback":True,"human_review":True,"retention_days":30})["valid"],
1984:lambda:o.update_ai_consent({},"u",["learning"],"1","2026-01-01T00:00:00Z")["record"]["learning_opt_in"],
1985:lambda:o.ai_task_navigation([{"id":"x","title":"X","roles":["ai_reviewer"]}])["next"]=="x",
1986:lambda:o.sync_ai_devices({"model:x":{"version":1,"value":"a"}},{"model:x":{"version":1,"value":"b"}})["model_conflicts"][0]["key"]=="model:x",
1987:lambda:o.detect_ai_duplicates([{"model_id":"m","prompt_hash":"p","input_hash":"i"},{"model_id":"m","prompt_hash":"p","input_hash":"i"}])["duplicate_rows"]==1,
1988:lambda:o.ai_adaptive_quota([10],100,"high")["risk_adjustment"]=="high",
1989:lambda:o.ai_community_impact([{"metric":"helpful","value":2}])["helpful_answers"]==2,
1990:lambda:o.review_ai_translation({},"u","approve")["human_review_required"],
1991:lambda:o.group_ai_notifications([{"id":"n","title":"N","context":"model","requires_review":True}])["review_required"]==1,
1992:lambda:o.plan_ai_migration({"version":1},[{"from":1,"to":2,"reversible":True}])["shadow_evaluation_required"],
1993:lambda:o.record_ai_admin_decision([],"deploy","u","tested","m","2026-01-01T00:00:00Z")["entry"]["model_id"]=="m",
1994:lambda:"confidence" in o.ai_accessibility_timeline([])["ai_controls"],
1995:lambda:o.prepare_ai_storage_transfer([{"name":"m","size":1,"sha256":"a"*64}],"webdav",2)["model_card_included"],
1996:lambda:o.evaluate_ai_time_policy([],30,1,True)["effective_action"]=="disable_auto_actions",
1997:lambda:len(o.simulate_ai_growth([10,11],2,1)["review_capacity"])==2,
1998:lambda:o.map_notification_dependencies([{"id":"a","fallbacks":["b"]},{"id":"b"}])["edges"][0]["to"]=="b",
1999:lambda:o.apply_notification_visual_rules({},[{"id":"r","when":"always","set":{"priority_badge":"x"}}],{})["notification"]["priority_badge"]=="x",
2000:lambda:o.notification_review_inbox([{"id":"n","channel":"web","priority":2}],["web"])["actionable"]==1,
2001:lambda:len(o.correlate_account_incidents([{"id":"a","account_id":"u","at":"2026-01-01T00:00:00Z"},{"id":"b","account_id":"u","at":"2026-01-01T00:05:00Z"}])["incidents"][0]["event_ids"])==2,
2002:lambda:o.build_account_workflow({"name":"W","steps":[{"id":"a","action":"review"}]})["validated"],
2003:lambda:o.delegate_account_role({"delegate_id":"u","role":"editor","starts_at":"2026-01-01T00:00:00Z","expires_at":"2026-01-02T00:00:00Z"},"2026-01-01T12:00:00Z")["active"],
2004:lambda:o.detect_coordinated_account_abuse([{"fingerprint":"x","account_id":"a"},{"fingerprint":"x","account_id":"b"}])["human_review_required"],
2005:lambda:o.account_context_copilot({"status":"ok","password":"secret"},"status")["sensitive_fields_excluded"],
2006:lambda:len(o.forecast_account_capacity([10,11],2)["storage_estimate_mb"])==2,
2007:lambda:o.execute_account_batch_plan(["a","b"],"freeze")["requires_confirmation"],
2008:lambda:o.create_account_workspace("W",[{"account_id":"u","role":"editor"}],["r"])["private"],
2009:lambda:o.index_account_media([{"id":"m","mime":"image/png","size":1,"sha256":"a"*64,"description":"x"}])["count"]==1,
2010:lambda:o.narrate_account_report({"users":2})["metrics"]["users"]==2,
2011:lambda:o.escalate_account_alerts([{"id":"a","score":10}],[{"minimum_score":5,"target":"admin"}])["pending_escalations"]==1,
2012:lambda:not o.account_offline_continuity({},[{"id":"a","action":"update_profile"}])["destructive_actions_allowed"],
2013:lambda:o.evaluate_adaptive_account_trust({"mfa":True})["step_up_required"],
2014:lambda:not o.plan_account_community_campaign({"name":"C","audience":10,"frequency_per_week":2})["launched"],
2015:lambda:o.detect_account_intent("Quiero borrar mi cuenta")["intent"]=="delete",
2016:lambda:not o.test_account_integration({"url":"https://example.com/hook","methods":["POST"]})["network_called"],
2017:lambda:not o.store_account_personal_vault({"id":"v","encrypted_envelope":"a"*32,"nonce":"b"*16})["plaintext_stored"],
2018:lambda:o.format_account_easy_read({"name":"Ana","status":"activa"})["reading_level"]=="easy",
2019:lambda:o.reconcile_account_sessions([{"id":"s","device":"d","last_seen":"2026-01-01T00:00:00Z"}],"d")["current_count"]==1,
2020:lambda:o.curate_account_editorial([{"id":"a","topics":["ai"]}],{"topics":["ai"]})["items"][0]["score"]==1,
2021:lambda:o.budget_account_resources([{"id":"r","cost":3}],5)["remaining"]==2,
2022:lambda:o.score_account_reputation([{"kind":"helpful"}])["score"]==53,
2023:lambda:o.localize_account_culturally({},"ar")["direction"]=="rtl",
2024:lambda:o.update_account_communication_preferences({},["telegram"],{"start":10,"end":20})["communication"]["pending_sync"],
2025:lambda:o.plan_account_onboarding({},["profile"])["next"]=="privacy",
2026:lambda:o.evaluate_account_governance({"threshold":.5,"quorum":.2},[{"account_id":"u","choice":"yes"}],1)["passed"],
2027:lambda:o.parse_accessible_account_voice_control("cerrar sesión")["requires_confirmation"],
2028:lambda:o.plan_account_federated_bridge([{"id":"p","endpoint":"https://example.com","verified":True}],["display_name"])["consent_required"],
2029:lambda:_valid_webhook(),
2030:lambda:not o.simulate_account_digital_twin({},[{"action":"freeze"}])["persisted"],
2031:lambda:o.correlate_creator_incidents([{"id":"a","account_id":"u","campaign_id":"c","at":"2026-01-01T00:00:00Z"}])["campaign_ids"]==["c"],
2032:lambda:o.build_creator_workflow({"name":"W","steps":[]})["publish_requires_review"],
2033:lambda:o.delegate_creator_role({"delegate_id":"u","role":"editor","starts_at":"2026-01-01T00:00:00Z","expires_at":"2026-01-02T00:00:00Z"},"2026-01-01T12:00:00Z")["creator_permissions_limited"],
2034:lambda:not o.detect_coordinated_creator_abuse([{"fingerprint":"x","account_id":"a"}])["campaign_paused"],
2035:lambda:o.creator_context_copilot({},"help")["role"]=="creator",
2036:lambda:len(o.forecast_creator_capacity([10,11],2,1)["editor_load"])==2,
2037:lambda:o.execute_creator_batch_plan(["x"],"archive")["requires_confirmation"],
2038:lambda:o.create_creator_workspace("W",[{"account_id":"u","role":"editor"}],["c"])["content_ids"]==["c"],
2039:lambda:not o.index_creator_media([{"id":"m","mime":"image/png","size":1,"sha256":"a"*64,"rights_confirmed":True}])["rights_missing"],
2040:lambda:o.narrate_creator_report({"reach":2})["creator_summary"],
2041:lambda:not o.escalate_creator_alerts([],[])["sent"],
 }


def _valid_webhook():
 body='{"x":1}'; key="s"*16; event_id="e"; at="2026-01-01T00:00:00+00:00"
 signature=hmac.new(key.encode(),f"{at}.{event_id}.{body}".encode(),hashlib.sha256).hexdigest()
 return o.validate_account_external_event({"id":event_id,"body":body,"signature":signature,"at":at},key,now="2026-01-01T00:01:00Z")["valid"]


class WebappAiAccountsCreatorTests(unittest.TestCase):
 def test_manifest_exact_roles_callable(self):
  self.assertEqual([x["id"] for x in FEATURES],[f"future-{n}" for n in range(1982,2042)])
  self.assertEqual(len({x["api"] for x in FEATURES}),60)
  allowed={"self","member","analyst","translator","ai_reviewer","ai_admin","accessibility_reviewer","notification_admin","notification_reviewer","account_admin","security_reviewer","campaign_manager","creator","creator_admin","creator_owner"}
  for row in FEATURES:
   self.assertIn(row["role"],allowed); self.assertTrue(callable(getattr(o,row["api"]))); self.assertTrue(all(row.get(k) for k in ("id","title","capability","module","api","role","test","preflight")))

 def test_ssrf_private_endpoints_rejected(self):
  for url in ("http://example.com","https://localhost/x","https://127.0.0.1/x","https://10.0.0.1/x","https://[::1]/x","https://user:pass@example.com/x","https://example.com:444/x"):
   with self.subTest(url=url),self.assertRaises(ValueError): o.test_account_integration({"url":url,"methods":["GET"]})
  plan=o.test_account_integration({"url":"https://example.com/hook","methods":["POST"]})
  self.assertTrue(plan["dns_revalidation_required"]); self.assertFalse(plan["redirects_allowed"])

 def test_security_has_no_io_or_html_sink(self):
  source=inspect.getsource(o)
  for forbidden in ("requests.","urllib.request","subprocess","eval(","exec(","innerHTML","os.system"):
   self.assertNotIn(forbidden,source)
  self.assertFalse(o.SECURITY_CONTRACT["network_io"]); self.assertFalse(o.SECURITY_CONTRACT["destructive_side_effects"])

 def test_destructive_plans_do_not_execute(self):
  self.assertFalse(o.execute_account_batch_plan(["u"],"freeze")["executed"]); self.assertFalse(o.execute_creator_batch_plan(["x"],"archive")["executed"])

 def test_weak_webhook_secret_rejected(self):
  with self.assertRaises(ValueError): o.validate_account_external_event({"id":"e","body":"x","signature":"x","at":"2026-01-01T00:00:00Z"},"short")

 def test_webhook_signature_binds_metadata_and_rejects_replay_age(self):
  body="payload"; key="s"*16; at="2026-01-01T00:00:00+00:00"
  signature=hmac.new(key.encode(),f"{at}.event-1.{body}".encode(),hashlib.sha256).hexdigest()
  event={"id":"event-1","body":body,"signature":signature,"at":at}
  self.assertTrue(o.validate_account_external_event(event,key,now="2026-01-01T00:04:00Z")["valid"])
  self.assertFalse(o.validate_account_external_event({**event,"id":"event-2"},key,now="2026-01-01T00:04:00Z")["valid"])
  self.assertFalse(o.validate_account_external_event(event,key,now="2026-01-01T00:06:00Z")["valid"])


def _make(number,case):
 def test(self): self.assertTrue(case())
 test.__name__=f"test_future_{number}"; return test
for number,case in cases().items(): setattr(WebappAiAccountsCreatorTests,f"test_future_{number}",_make(number,case))


if __name__=="__main__": unittest.main()

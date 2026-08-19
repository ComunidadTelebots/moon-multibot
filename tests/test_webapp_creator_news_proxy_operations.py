import hashlib
import hmac
import inspect
import unittest

import webapp_creator_news_proxy_operations as o
from webapp_creator_news_proxy_operations_manifest import FEATURES


def _signed(kind):
 body="{}"; key="s"*16; at="2026-01-01T00:00:00Z"; domain="creator" if kind in {"content.updated","campaign.metric","comment.created"} else "news" if kind in {"feed.updated","article.corrected","source.changed"} else "creator"; signed=f"{domain}:{kind}.2026-01-01T00:00:00+00:00.e.{body}"; sig=hmac.new(key.encode(),signed.encode(),hashlib.sha256).hexdigest(); return {"event":{"id":"e","type":kind,"body":body,"signature":sig,"at":at},"key":key}


CASES={
2042:lambda:not o.creator_offline_continuity({},[{"id":"a","action":"edit_draft"}])["publish_offline"],2043:lambda:not o.evaluate_creator_adaptive_trust({"mfa":True})["publish_allowed"],2044:lambda:o.plan_creator_campaign({"name":"C","audience":10,"frequency_per_week":1})["preview_required"],2045:lambda:o.detect_creator_intent("programar publicación")["intent"]=="schedule",2046:lambda:not o.test_creator_integration({"url":"https://example.com","methods":["GET"],"scopes":["read_content"]})["publish_scope_allowed"],2047:lambda:not o.store_creator_vault({"id":"v","encrypted_envelope":"a"*32,"nonce":"b"*16})["shareable"],2048:lambda:"Programar" in o.format_creator_easy_read({"name":"C","status":"ok"})["creator_actions"],2049:lambda:o.reconcile_creator_sessions([{"id":"s","device":"d","last_seen":"2026-01-01T00:00:00Z","can_publish":True}],"d")["sessions_with_publish"]==["s"],2050:lambda:o.curate_creator_editorial([{"id":"i","topics":["ai"],"source_quality":.5}],{"topics":["ai"]})["items"][0]["needs_fact_check"],2051:lambda:o.budget_creator_resources([{"id":"r","cost":3}],10)["requires_approval"],2052:lambda:o.score_creator_reputation([{"kind":"helpful"}])["reach_not_used"],2053:lambda:o.localize_creator_culturally({},"ar")["content_direction"]=="rtl",2054:lambda:o.update_creator_communication_preferences({},["web"],{"start":1,"end":2})["communication"]["editorial_digest"],2055:lambda:"rights" in o.plan_creator_onboarding({},[])["safety_steps"],2056:lambda:o.evaluate_creator_governance({"creator_benefit":True},[],1)["creator_recusal_required"],2057:lambda:o.parse_creator_voice_control("programar publicación")["requires_confirmation"],2058:lambda:not o.plan_creator_federated_bridge([{"id":"p","endpoint":"https://example.com","verified":True}],["published_content"])["drafts_federated"],2059:lambda:_creator_event(),2060:lambda:not o.simulate_creator_digital_twin({},[{"action":"set_budget","value":2}])["published"],
2061:lambda:o.correlate_news_incidents([{"id":"e","source_id":"s","article_id":"a","at":"2026-01-01T00:00:00Z"}])["affected_articles"]==["a"],2062:lambda:o.build_news_workflow({"name":"N","steps":[{"id":"a","action":"fact_check"}]})["fact_check_required"],2063:lambda:not o.delegate_news_role({"delegate_id":"u","role":"editor","starts_at":"2026-01-01T00:00:00Z","expires_at":"2026-01-02T00:00:00Z"},"2026-01-01T12:00:00Z")["publish_permission_included"],2064:lambda:not o.detect_coordinated_news_abuse([])["articles_removed"],2065:lambda:o.news_context_copilot({},"q")["source_required"],2066:lambda:o.forecast_news_capacity([10,11],1,1)["breaking_news_reserve_percent"]==20,2067:lambda:o.execute_news_batch_plan(["a"],"archive")["requires_confirmation"],2068:lambda:o.create_news_workspace("N",[{"account_id":"u","role":"editor"}],["a"])["source_notes_private"],2069:lambda:not o.index_news_media([{"id":"m","mime":"image/png","size":1,"sha256":"a"*64,"provenance":"camera"}])["provenance_missing"],2070:lambda:"fuentes" in o.narrate_news_report({"published":1})["news_sections"],2071:lambda:o.escalate_news_alerts([{"id":"a","score":1,"breaking":True}],[])["breaking_count"]==1,2072:lambda:not o.news_offline_continuity({},[{"id":"a","action":"fact_check"}])["publish_offline"],2073:lambda:not o.evaluate_news_adaptive_trust({"mfa":True})["publish_allowed"],2074:lambda:o.plan_news_campaign({"name":"N","audience":10,"frequency_per_week":1})["sponsored_disclosure_required"],2075:lambda:o.detect_news_intent("Envío una corrección")["intent"]=="correction",2076:lambda:o.test_news_integration({"url":"https://example.com","methods":["GET"],"format":"rss"})["feed_format"]=="rss",2077:lambda:not o.store_news_vault({"id":"v","encrypted_envelope":"a"*32,"nonce":"b"*16})["plaintext_stored"],2078:lambda:o.format_news_easy_read({"title":"T","summary":"S"})["reading_level"]=="easy",2079:lambda:o.reconcile_news_sessions([{"id":"s","device":"d","role":"editor","last_seen":"2026-01-01T00:00:00Z"}],"d")["editor_sessions"]==1,2080:lambda:o.curate_news_editorial([{"id":"a","topics":["ai"],"source_score":1,"public_interest":1}],{"topics":["ai"]})["human_editor_required"],2081:lambda:o.budget_news_resources([],1)["editorial_decisions_independent"],2082:lambda:o.score_news_reputation([{"kind":"accurate"}])["score"]==54,2083:lambda:o.localize_news_culturally({},"es-ES")["facts_preserved"],2084:lambda:o.update_news_communication_preferences({},["telegram"],{"start":1,"end":2})["communication"]["corrections"],2085:lambda:"rights" in o.plan_news_onboarding({},[])["editorial_steps"],2086:lambda:o.evaluate_news_governance({"conflicts_declared":True},[],1)["conflicts_declared"],2087:lambda:o.parse_news_voice_control("publicar noticia")["requires_confirmation"],2088:lambda:o.plan_news_federated_bridge([{"id":"p","endpoint":"https://example.com","verified":True}],["headline"])["canonical_required"],2089:lambda:_news_event(),2090:lambda:not o.simulate_news_digital_twin({},[{"action":"add_draft","id":"a"}])["published"],
2091:lambda:o.correlate_proxy_incidents([{"id":"e","proxy_id":"p","at":"2026-01-01T00:00:00Z"}])["proxy_ids"]==["p"],2092:lambda:o.build_proxy_workflow({"name":"P","steps":[{"id":"a","action":"probe"}]})["destructive_steps_require_master"],2093:lambda:not o.delegate_proxy_role({"delegate_id":"u","role":"proxy_operator","starts_at":"2026-01-01T00:00:00Z","expires_at":"2026-01-02T00:00:00Z"},"2026-01-01T12:00:00Z")["secret_access"],2094:lambda:not o.detect_coordinated_proxy_abuse([])["auto_blocked"],2095:lambda:not o.proxy_context_copilot({"secret":"x"},"q")["secret_included"],2096:lambda:len(o.forecast_proxy_capacity([10,11],1,1)["connections_per_node"])==1,2097:lambda:o.execute_proxy_batch_plan(["p"],"disable")["requires_master"],2098:lambda:not o.create_proxy_workspace("P",[{"account_id":"u","role":"viewer"}],["p"])["secrets_visible"],2099:lambda:not o.index_proxy_media([{"id":"m","mime":"image/png","size":1,"sha256":"a"*64}])["public"],2100:lambda:o.narrate_proxy_report({"latency":2,"secret":"x"})["secrets_redacted"],2101:lambda:not o.escalate_proxy_alerts([],[])["executed"]}


def _creator_event():
 value=_signed("content.updated"); return o.validate_creator_external_event(value["event"],value["key"])["valid"]
def _news_event():
 value=_signed("feed.updated"); return o.validate_news_external_event(value["event"],value["key"])["valid"]


class WebappCreatorNewsProxyTests(unittest.TestCase):
 def test_manifest_exact_roles_callable(self):
  self.assertEqual([x["id"] for x in FEATURES],[f"future-{n}" for n in range(2042,2102)]); self.assertEqual(len({x["api"] for x in FEATURES}),60)
  allowed={"member","analyst","creator","creator_admin","news_editor","news_admin","proxy_operator","proxy_admin","security_reviewer","campaign_manager"}
  for row in FEATURES: self.assertIn(row["role"],allowed); self.assertTrue(callable(getattr(o,row["api"])))
 def test_no_dynamic_execution_or_network(self):
  source=inspect.getsource(o)
  for forbidden in ("requests.","urllib.request","subprocess","eval(","exec(","innerHTML","os.system"): self.assertNotIn(forbidden,source)
 def test_creator_and_news_events_reject_unknown_types(self):
  value=_signed("unknown"); self.assertFalse(o.validate_creator_external_event(value["event"],value["key"])["valid"]); self.assertFalse(o.validate_news_external_event(value["event"],value["key"])["valid"])
 def test_event_type_is_bound_to_signature(self):
  value=_signed("content.updated")
  self.assertTrue(o.validate_creator_external_event(value["event"],value["key"])["valid"])
  self.assertFalse(o.validate_creator_external_event({**value["event"],"type":"campaign.metric"},value["key"])["valid"])
 def test_proxy_report_redacts_compound_secrets_and_rejects_nan(self):
  result=o.narrate_proxy_report({"latency":2,"access_token":123,"clientSecret":456,"proxy_password":789})
  self.assertEqual(result["metrics"],{"latency":2.0})
  with self.assertRaises(ValueError): o.narrate_proxy_report({"latency":float("nan")})
 def test_destructive_batch_plans_are_not_executed(self):
  self.assertFalse(o.execute_news_batch_plan(["a"],"archive")["executed"]); self.assertFalse(o.execute_proxy_batch_plan(["p"],"disable")["executed"])

def _make(number,case):
 def test(self): self.assertTrue(case())
 test.__name__=f"test_future_{number}"; return test
for number,case in CASES.items(): setattr(WebappCreatorNewsProxyTests,f"test_future_{number}",_make(number,case))

if __name__=="__main__": unittest.main()

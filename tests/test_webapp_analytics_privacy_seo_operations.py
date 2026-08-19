import hashlib,hmac,inspect,unittest
import webapp_analytics_privacy_seo_operations as o
from webapp_analytics_privacy_seo_operations_manifest import FEATURES

def signed(kind):
 body="{}";key="s"*16;at="2026-01-01T00:00:00+00:00";domain="analytics" if kind in {"metric.updated","report.ready","anomaly.detected"} else "privacy";sig=hmac.new(key.encode(),f"{domain}:{kind}.{at}.e.{body}".encode(),hashlib.sha256).hexdigest();return {"event":{"id":"e","type":kind,"body":body,"signature":sig,"at":at},"key":key}
def event_ok(kind,fn):
 v=signed(kind);return fn(v["event"],v["key"])["valid"]

CASES={
2162:lambda:not o.analytics_offline_continuity({},[{"id":"a","action":"save_filter"}])["raw_rows_cached"],2163:lambda:not o.analytics_adaptive_trust({"mfa":True})["raw_export_allowed"],2164:lambda:not o.analytics_campaign({"name":"A","audience":10,"frequency_per_week":1})["personal_tracking"],2165:lambda:o.analytics_intent("comparar periodos")["intent"]=="compare",2166:lambda:not o.analytics_integration({"url":"https://example.com","methods":["GET"],"format":"json-stat"})["raw_identifiers_sent"],2167:lambda:not o.analytics_vault({"id":"v","encrypted_envelope":"a"*32,"nonce":"b"*16})["raw_data_stored"],2168:lambda:o.analytics_easy_read({"metrics":{"users":2}})["reading_level"]=="easy",2169:lambda:o.analytics_sessions([{"id":"s","device":"d","last_seen":"2026-01-01T00:00:00Z","raw_export":True}],"d")["raw_export_sessions"]==1,2170:lambda:o.analytics_editorial([{"id":"d","use_count":2,"aggregate_only":True}],{})["items"][0]["privacy_safe"],2171:lambda:o.analytics_budget([],10)["privacy_reserve_percent"]==10,2172:lambda:o.analytics_reputation([{"kind":"accurate"}])["score"]==53,2173:lambda:o.analytics_localization({},"es-ES")["dimension_ids_unchanged"],2174:lambda:o.analytics_communication_preferences({},["web"],{"start":1,"end":2})["communication"]["raw_data_never_notified"],2175:lambda:"privacy" in o.analytics_onboarding({},[])["analytics_steps"],2176:lambda:not o.analytics_governance({},[],1)["applied"],2177:lambda:o.analytics_voice_control("exportar datos")["requires_confirmation"],2178:lambda:not o.analytics_federated_bridge([{"id":"p","endpoint":"https://example.com","verified":True}],["aggregate"])["raw_rows_federated"],2179:lambda:event_ok("metric.updated",o.analytics_external_event),2180:lambda:not o.analytics_digital_twin({},[{"action":"add_metric","metric":"users"}])["query_executed"],
2181:lambda:not o.webapp_privacy_incidents([{"id":"e","data_subject":"u","category":"access","at":"2026-01-01T00:00:00Z"}])["subject_ids_public"],2182:lambda:o.webapp_privacy_workflow({"name":"P","steps":[{"id":"a","action":"identify"}]})["legal_review_required"],2183:lambda:o.webapp_privacy_delegation({"delegate_id":"u","role":"privacy_officer","starts_at":"2026-01-01T00:00:00Z","expires_at":"2026-01-02T00:00:00Z"},"2026-01-01T12:00:00Z")["data_export_access"],2184:lambda:not o.webapp_privacy_coordinated_abuse([])["requests_denied"],2185:lambda:o.webapp_privacy_copilot({},"q")["personal_data_excluded"],2186:lambda:len(o.webapp_privacy_capacity([10,11],1,1)["request_load"])==1,2187:lambda:o.webapp_privacy_batch_plan(["r"],"erase_preview")["requires_dual_confirmation"],2188:lambda:not o.webapp_privacy_workspace("P",[{"account_id":"u","role":"viewer"}],["r"])["exports_disabled"] is False,2189:lambda:not o.webapp_privacy_media([{"id":"m","mime":"image/png","size":1,"sha256":"a"*64}])["public"],2190:lambda:not o.webapp_privacy_report({"requests":2,"emails":["x"]})["personal_data_included"],2191:lambda:not o.webapp_privacy_alert_escalation([],[])["sent"],2192:lambda:not o.webapp_privacy_offline_continuity({},[{"id":"a","action":"annotate"}])["erasures_offline"],2193:lambda:not o.webapp_privacy_adaptive_trust({"mfa":True})["personal_data_access"],2194:lambda:o.webapp_privacy_campaign({"name":"P","audience":10,"frequency_per_week":1})["tracking_minimized"],2195:lambda:o.webapp_privacy_intent("quiero borrar mis datos")["intent"]=="erase",2196:lambda:not o.webapp_privacy_integration({"url":"https://example.com","methods":["GET"],"purpose":"consent"})["personal_data_sent"],2197:lambda:not o.webapp_privacy_vault({"id":"v","encrypted_envelope":"a"*32,"nonce":"b"*16})["plaintext_stored"],2198:lambda:o.webapp_privacy_easy_read({"purposes":["servicio"]})["withdrawal_visible"],2199:lambda:o.webapp_privacy_sessions([{"id":"s","device":"d","last_seen":"2026-01-01T00:00:00Z","data_access":True}],"d")["data_access_sessions"]==1,2200:lambda:o.webapp_privacy_editorial([{"id":"i","purpose":"service"}],{"purposes":["service"]})["non_compliant"]==0,2201:lambda:o.webapp_privacy_budget([],10)["incident_reserve_percent"]==20,2202:lambda:not o.webapp_privacy_reputation([])["personal_data_used"],2203:lambda:o.webapp_privacy_localization({},"es-ES")["rights_preserved"],2204:lambda:o.webapp_privacy_communication_preferences({},["web"],{"start":1,"end":2})["communication"]["breach_alerts"],2205:lambda:"rights" in o.webapp_privacy_onboarding({},[])["privacy_steps"],2206:lambda:not o.webapp_privacy_governance({},[],1)["policy_changed"],2207:lambda:o.webapp_privacy_voice_control("borrar mis datos")["requires_confirmation"],2208:lambda:not o.webapp_privacy_federated_bridge([{"id":"p","endpoint":"https://example.com","verified":True}],["public_policy"])["personal_data_federated"],2209:lambda:event_ok("consent.changed",o.webapp_privacy_external_event),2210:lambda:not o.webapp_privacy_digital_twin({},[{"action":"request_export"}])["export_created"],
2211:lambda:o.webapp_seo_incidents([{"id":"e","site":"s","url_hash":"h","at":"2026-01-01T00:00:00Z"}])["affected_urls"]==["h"],2212:lambda:o.webapp_seo_workflow({"name":"S","steps":[{"id":"a","action":"crawl"}]})["metadata_publish_requires_review"],2213:lambda:not o.webapp_seo_delegation({"delegate_id":"u","role":"seo_editor","starts_at":"2026-01-01T00:00:00Z","expires_at":"2026-01-02T00:00:00Z"},"2026-01-01T12:00:00Z")["content_publish_access"],2214:lambda:not o.webapp_seo_coordinated_abuse([])["links_removed"],2215:lambda:not o.webapp_seo_copilot({},"q")["metadata_changed"],2216:lambda:len(o.webapp_seo_capacity([10,11],1,1)["audit_load"])==1,2217:lambda:not o.webapp_seo_batch_plan(["u"],"audit")["metadata_changed"],2218:lambda:not o.webapp_seo_workspace("S",[{"account_id":"u","role":"viewer"}],["u"])["publishing_access"],2219:lambda:not o.webapp_seo_media([{"id":"m","mime":"image/png","size":1,"sha256":"a"*64}])["binary_published"],2220:lambda:not o.webapp_seo_report({"pages":2})["rank_guarantee"],2221:lambda:not o.webapp_seo_alert_escalation([],[])["sent"]}

class WebappAnalyticsPrivacySeoTests(unittest.TestCase):
 def test_manifest_exact_roles_callable(self):
  self.assertEqual([x["id"] for x in FEATURES],[f"future-{n}" for n in range(2162,2222)]);self.assertEqual(len({x["api"] for x in FEATURES}),60)
  allowed={"self","member","analyst","campaign_manager","analytics_admin","privacy_officer","security_reviewer","seo_editor","seo_admin"}
  for row in FEATURES:self.assertIn(row["role"],allowed);self.assertTrue(callable(getattr(o,row["api"])))
 def test_no_io_dynamic_execution_or_html_sink(self):
  source=inspect.getsource(o)
  for forbidden in ("requests.","urllib.request","subprocess","eval(","exec(","innerHTML","os.system"):self.assertNotIn(forbidden,source)
 def test_unknown_events_rejected(self):
  v=signed("unknown")
  for fn in (o.analytics_external_event,o.webapp_privacy_external_event):self.assertFalse(fn(v["event"],v["key"])["valid"])
 def test_event_type_is_bound_to_domain_signature(self):
  v=signed("consent.changed");self.assertTrue(o.webapp_privacy_external_event(v["event"],v["key"])["valid"])
  self.assertFalse(o.webapp_privacy_external_event({**v["event"],"type":"breach.detected"},v["key"])["valid"])
 def test_privacy_outputs_do_not_reflect_subjects_or_compound_pii(self):
  result=o.webapp_privacy_incidents([{"id":"e","data_subject":"alice@example.com","category":"access","at":"2026-01-01T00:00:00Z"}])
  self.assertNotIn("alice@example.com",repr(result))
  report=o.webapp_privacy_report({"requests":2,"access_token":123,"user_email":"alice@example.com"})
  self.assertEqual(report["metrics"],{"requests":2.0})
  copilot=o.webapp_privacy_copilot({"requests":{"status":"open","clientSecret":"x","email":"alice@example.com"}},"q")
  self.assertEqual(copilot["facts"],{"requests":{"status":"open"}})
 def test_offline_analytics_drops_raw_rows(self):
  result=o.analytics_offline_continuity({"totals":{"users":2},"raw_rows":[{"email":"a@example.com"}]},[])
  self.assertEqual(result["snapshot"],{"totals":{"users":2}})
 def test_privacy_destructive_actions_are_plans(self):
  self.assertFalse(o.webapp_privacy_batch_plan(["r"],"erase_preview")["executed"]);self.assertFalse(o.webapp_privacy_digital_twin({},[{"action":"request_export"}])["persisted"])

def make(number,case):
 def test(self):self.assertTrue(case())
 test.__name__=f"test_future_{number}";return test
for n,c in CASES.items():setattr(WebappAnalyticsPrivacySeoTests,f"test_future_{n}",make(n,c))
if __name__=="__main__":unittest.main()

import hashlib,hmac,inspect,unittest
import webapp_proxy_dashboard_analytics_operations as o
from webapp_proxy_dashboard_analytics_operations_manifest import FEATURES

def signed(kind):
 body="{}"; key="s"*16; at="2026-01-01T00:00:00+00:00"; domain="proxy" if kind.startswith("proxy.") else "dashboard"; sig=hmac.new(key.encode(),f"{domain}:{kind}.{at}.e.{body}".encode(),hashlib.sha256).hexdigest(); return {"event":{"id":"e","type":kind,"body":body,"signature":sig,"at":at},"key":key}

CASES={
2102:lambda:not o.proxy_offline_continuity({},[{"id":"a","action":"queue_probe"}])["network_changes"],2103:lambda:not o.proxy_adaptive_trust({"mfa":True})["rotate_secret"],2104:lambda:o.proxy_campaign({"name":"P","audience":10,"frequency_per_week":1})["health_filter_required"],2105:lambda:o.proxy_intent("El proxy está lento")["intent"]=="slow",2106:lambda:not o.proxy_integration({"url":"https://example.com","methods":["GET"],"protocol":"health"})["network_called"],2107:lambda:not o.proxy_vault({"id":"v","encrypted_envelope":"a"*32,"nonce":"b"*16})["secret_plaintext"],2108:lambda:o.proxy_easy_read({"name":"P","status":"ok","region":"ES","latency_ms":2})["reading_level"]=="easy",2109:lambda:o.proxy_sessions([{"id":"s","device":"d","last_seen":"2026-01-01T00:00:00Z","secret_access":True}],"d")["sessions_with_secret_access"]==["s"],2110:lambda:o.proxy_editorial([{"id":"p","uptime":.99,"region":"ES"}],{"regions":["ES"]})["items"][0]["healthy"],2111:lambda:o.proxy_budget([],10)["secret_rotation_reserved"]==1,2112:lambda:o.proxy_reputation([{"kind":"healthy_probe"}])["score"]==52,2113:lambda:o.proxy_localization({},"es-ES")["host_unchanged"],2114:lambda:o.proxy_communication_preferences({},["web"],{"start":1,"end":2})["communication"]["outage_alerts"],2115:lambda:"health_check" in o.proxy_onboarding({},[])["proxy_steps"],2116:lambda:not o.proxy_governance({},[],1)["network_change_executed"],2117:lambda:o.proxy_voice_control("desactivar proxy")["requires_confirmation"],2118:lambda:not o.proxy_federated_bridge([{"id":"p","endpoint":"https://example.com","verified":True}],["status"])["secrets_federated"],2119:lambda:event_ok("proxy.healthy",o.proxy_external_event),2120:lambda:not o.proxy_digital_twin({},[{"action":"quarantine"}])["network_changed"],
2121:lambda:o.dashboard_incidents([{"id":"e","component":"api","widget":"health","at":"2026-01-01T00:00:00Z"}])["affected_widgets"]==["health"],2122:lambda:o.dashboard_workflow({"name":"D","steps":[{"id":"a","action":"refresh"}]})["cross_panel_navigation"],2123:lambda:o.dashboard_delegation({"delegate_id":"u","role":"dashboard_viewer","starts_at":"2026-01-01T00:00:00Z","expires_at":"2026-01-02T00:00:00Z"},"2026-01-01T12:00:00Z")["master_panels_hidden"],2124:lambda:not o.dashboard_coordinated_abuse([])["sessions_revoked"],2125:lambda:o.dashboard_copilot({"health":"ok","token":"x"},"q")["secrets_excluded"],2126:lambda:len(o.dashboard_capacity([10,11],1,1)["operator_load"])==1,2127:lambda:not o.dashboard_batch_plan(["a"],"refresh")["executed"],2128:lambda:o.dashboard_workspace("D",[{"account_id":"u","role":"viewer"}],["w"])["master_widgets_filtered"],2129:lambda:not o.dashboard_media([{"id":"m","mime":"image/png","size":1,"sha256":"a"*64}])["public"],2130:lambda:o.dashboard_narrative_report({"frequency":"daily","format":"json"},{"users":2,"tokens":"x"})["secrets_excluded"],2131:lambda:not o.dashboard_alert_escalation([],[])["sent"],2132:lambda:not o.dashboard_offline_continuity({},[{"id":"a","action":"save_filter"}])["admin_actions_allowed"],2133:lambda:not o.dashboard_adaptive_trust({"mfa":True})["master_panels_visible"],2134:lambda:o.dashboard_campaign({"name":"D","audience":10,"frequency_per_week":1})["dashboard_preview"],2135:lambda:o.dashboard_intent("Abrir grupos")["target_panel"]=="groups",2136:lambda:not o.dashboard_integration({"url":"https://example.com","methods":["GET"],"kind":"health"})["credential_value_returned"],2137:lambda:not o.dashboard_vault({"id":"v","encrypted_envelope":"a"*32,"nonce":"b"*16})["visible_in_widgets"],2138:lambda:o.dashboard_easy_read({"users":2})["reading_level"]=="easy",2139:lambda:o.dashboard_sessions([{"id":"s","device":"d","last_seen":"2026-01-01T00:00:00Z","master":True}],"d")["master_sessions"]==1,2140:lambda:o.dashboard_editorial([{"id":"w","priority":1}],{"pinned":["w"]})["widgets"][0]["score"]==101,2141:lambda:o.dashboard_budget([],10)["alerts_reserved_percent"]==10,2142:lambda:not o.dashboard_reputation([])["automatic_access_change"],2143:lambda:o.dashboard_localization({},"ar")["identifiers_unchanged"],2144:lambda:o.dashboard_communication_preferences({},["web"],{"start":1,"end":2})["communication"]["critical_bypass"],2145:lambda:"security" in o.dashboard_onboarding({},[])["dashboard_steps"],2146:lambda:not o.dashboard_governance({},[],1)["applied"],2147:lambda:o.dashboard_voice_control("activar mantenimiento")["requires_confirmation"],2148:lambda:o.dashboard_federated_bridge([{"id":"p","endpoint":"https://example.com","verified":True}],["health"])["read_only"],2149:lambda:event_ok("service.health",o.dashboard_external_event),2150:lambda:not o.dashboard_digital_twin({},[{"action":"hide","widget_id":"w"}])["persisted"],
2151:lambda:o.analytics_incidents([{"id":"e","dataset":"d","query_id":"q","at":"2026-01-01T00:00:00Z"}])["affected_queries"]==["q"],2152:lambda:o.analytics_workflow({"name":"A","steps":[{"id":"a","action":"aggregate"}]})["privacy_check_required"],2153:lambda:not o.analytics_delegation({"delegate_id":"u","role":"analytics_viewer","starts_at":"2026-01-01T00:00:00Z","expires_at":"2026-01-02T00:00:00Z"},"2026-01-01T12:00:00Z")["raw_user_data_access"],2154:lambda:not o.analytics_coordinated_abuse([])["queries_blocked"],2155:lambda:o.analytics_copilot({},"q")["personal_data_excluded"],2156:lambda:len(o.analytics_capacity([10,11],1,1)["query_load"])==1,2157:lambda:not o.analytics_batch_plan(["q"],"export_aggregate")["raw_export"],2158:lambda:not o.analytics_workspace("A",[{"account_id":"u","role":"viewer"}],["d"])["raw_data_shared"],2159:lambda:not o.analytics_media([{"id":"m","mime":"image/png","size":1,"sha256":"a"*64}])["raw_dataset_embedded"],2160:lambda:o.analytics_narrative_report({"frequency":"daily","format":"json"},[{"x":1}])["raw_rows_included"] is False,2161:lambda:not o.analytics_alert_escalation([],[])["sent"]}

def event_ok(kind,fn):
 value=signed(kind); return fn(value["event"],value["key"])["valid"]

class WebappProxyDashboardAnalyticsTests(unittest.TestCase):
 def test_manifest_exact_roles_callable(self):
  self.assertEqual([x["id"] for x in FEATURES],[f"future-{n}" for n in range(2102,2162)]); self.assertEqual(len({x["api"] for x in FEATURES}),60)
  allowed={"self","member","analyst","campaign_manager","proxy_operator","proxy_admin","dashboard_operator","dashboard_admin","analytics_admin","security_reviewer"}
  for row in FEATURES:self.assertIn(row["role"],allowed);self.assertTrue(callable(getattr(o,row["api"])))
 def test_no_dynamic_execution_network_or_html_sink(self):
  source=inspect.getsource(o)
  for forbidden in ("requests.","urllib.request","subprocess","eval(","exec(","innerHTML","os.system"):self.assertNotIn(forbidden,source)
 def test_unknown_events_rejected(self):
  value=signed("unknown")
  for fn in (o.proxy_external_event,o.dashboard_external_event):self.assertFalse(fn(value["event"],value["key"])["valid"])
 def test_event_type_is_bound_to_domain_signature(self):
  value=signed("proxy.healthy");self.assertTrue(o.proxy_external_event(value["event"],value["key"])["valid"])
  self.assertFalse(o.proxy_external_event({**value["event"],"type":"proxy.offline"},value["key"])["valid"])
 def test_dashboard_outputs_redact_compound_and_nested_secrets(self):
  snapshot={"users":2,"access_token":"x","nested":{"clientSecret":"y","status":"ok"},"emails":["a@example.com"]}
  report=o.dashboard_narrative_report({"frequency":"daily","format":"json"},snapshot)
  self.assertEqual(report["snapshot"],{"users":2,"nested":{"status":"ok"}})
  copilot=o.dashboard_copilot({"health":{"status":"ok","refresh_token":"x"}},"q")
  self.assertEqual(copilot["facts"],{"health":{"status":"ok"}})
 def test_destructive_plans_are_simulations(self):
  self.assertFalse(o.proxy_digital_twin({},[{"action":"quarantine"}])["persisted"]);self.assertFalse(o.dashboard_digital_twin({},[{"action":"hide","widget_id":"w"}])["persisted"])

def make(number,case):
 def test(self):self.assertTrue(case())
 test.__name__=f"test_future_{number}";return test
for number,case in CASES.items():setattr(WebappProxyDashboardAnalyticsTests,f"test_future_{number}",make(number,case))

if __name__=="__main__":unittest.main()

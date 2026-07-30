import inspect
import unittest

import webapp_content_security_ai_operations as o
from webapp_content_security_ai_operations_manifest import FEATURES


def _cases():
    return {
1922:lambda:o.recommend_content_config({"stale_articles":1},{})["recommendations"][0]["key"]=="expiry_review",
1923:lambda:o.test_content_config({"max_title_length":100,"require_source":True,"preview_before_publish":True,"summary_length":100})["valid"],
1924:lambda:o.update_content_consent({},"u",["analytics"],"1","2026-01-01T00:00:00Z")["record"]["can_withdraw"],
1925:lambda:o.content_task_navigation([{"id":"x","title":"X","roles":["content_editor"]}])["next"]=="x",
1926:lambda:o.sync_content_devices({"draft:x":{"version":1,"value":"a"}},{"draft:x":{"version":1,"value":"b"}})["draft_conflicts"][0]["key"]=="draft:x",
1927:lambda:len(o.detect_content_duplicates([{"title":"T","source_url":"u","body":"B"},{"title":"T","source_url":"u","body":"B"}])["same_body"])==1,
1928:lambda:o.content_adaptive_quota([10],100,5)["scheduled_reserve"]==10,
1929:lambda:o.content_community_impact([{"metric":"helpful","value":2}])["articles_helpful"]==2,
1930:lambda:o.review_content_translation({"source_language":"es","target_language":"en"},"u","approve")["target_language"]=="en",
1931:lambda:o.group_content_notifications([{"id":"n","title":"N","context":"edit","channel":"web"}])["groups"][0]["channels"]==["web"],
1932:lambda:o.plan_content_migration({"version":1},[{"from":1,"to":2,"reversible":True}])["publish_lock"],
1933:lambda:o.record_content_admin_decision([],"publish","u","ok","c","2026-01-01T00:00:00Z")["entry"]["content_id"]=="c",
1934:lambda:"alt" in o.content_accessibility_timeline([])["required_media_checks"],
1935:lambda:o.prepare_content_storage_transfer([{"name":"a","size":1,"sha256":"a"*64}],"webdav",2)["preserve_canonical_urls"],
1936:lambda:o.evaluate_content_time_policy([{"id":"p","start_minute":0,"end_minute":60,"action":"block_publish"}],30,1,True)["can_publish"],
1937:lambda:len(o.simulate_content_growth([10,11],2,1)["capacity"])==2,
1938:lambda:o.map_security_dependencies([{"id":"a","depends_on":["b"]},{"id":"b"}])["single_points"]==["b"],
1939:lambda:o.apply_security_visual_rules({},[{"id":"r","minimum_risk":"high","set":{"badge":"danger"}}],"high")["panel"]["badge"]=="danger",
1940:lambda:o.security_review_inbox([{"id":"f","scope":"group","severity":"high"}],["group"])["actionable"]==1,
1941:lambda:o.detect_sensitive_security_changes({"auth":1},{"auth":2})["requires_dual_approval"],
1942:lambda:o.explain_security_decision({"decision":"block","finding_id":"f","policy_id":"p","factors":[]})["evidence_redacted"],
1943:lambda:o.security_data_quality([{"id":"f","kind":"scan","severity":"high","observed_at":"now"}])["triage_ready"],
1944:lambda:o.preview_security_import([{"id":"f","kind":"scan","severity":"high","observed_at":"now","evidence_hash":"a"*64}])["commit_allowed"],
1945:lambda:o.add_security_comment({},"u","note","restricted","2026-01-01T00:00:00Z")["comment"]["classification"]=="restricted",
1946:lambda:o.security_smart_tags([{"id":"f","text":"malware"}])["items"][0]["priority"]=="high",
1947:lambda:o.security_activity_digest([{"category":"scan","severity":"high"}])["by_severity"]["high"]==1,
1948:lambda:o.security_expiry_alerts([{"id":"k","expires_at":"2026-01-01T00:00:00Z"}],"2026-01-02T00:00:00Z")["alerts"][0]["action"]=="revoke",
1949:lambda:o.open_security_emergency({},"breach","u","2026-01-01T00:00:00Z")["state"]["sessions_revoked"],
1950:lambda:o.security_permission_history([{"user_id":"u","permission":"token_rotate","action":"grant","at":"2026-01-01T00:00:00Z"}],"u")["privileged"]==["token_rotate"],
1951:lambda:o.update_security_goal({"target":2,"progress":0},"u",1,"C1")["control_id"]=="C1",
1952:lambda:o.recommend_security_config({}, {})["recommendations"][0]["key"]=="mfa_required",
1953:lambda:o.test_security_config({"mfa_required":True,"https_only":True,"token_ttl_seconds":3600,"audit_enabled":True})["valid"],
1954:lambda:o.update_security_consent({},"u","breach_alerts",True,"1","2026-01-01T00:00:00Z")["record"]["granted"],
1955:lambda:o.security_task_navigation([{"id":"x","title":"X","roles":["security_admin"],"privileged":True}])["tasks"][0]["requires_reauthentication"],
1956:lambda:o.sync_security_devices({"auth:x":{"version":1,"value":"a"}},{"auth:x":{"version":1,"value":"b"}})["security_conflicts"][0]["key"]=="auth:x",
1957:lambda:o.detect_security_duplicates([{"kind":"x","evidence_hash":"h","scope":"g"},{"kind":"x","evidence_hash":"h","scope":"g"}])["dedupe_requires_review"],
1958:lambda:o.security_adaptive_quota([10],100,"critical")["threat_level"]=="critical",
1959:lambda:o.security_community_impact([{"metric":"incident_prevented","value":1}])["incidents_prevented"]==1,
1960:lambda:o.review_security_translation({"terms":["warning","action","recovery"],"safe_links":True},"u","approve")["security_terms_complete"],
1961:lambda:o.group_security_notifications([{"id":"n","title":"N","context":"auth","severity":"critical"}])["groups"][0]["ack_required"],
1962:lambda:o.plan_security_migration({"version":1},[{"from":1,"to":2,"reversible":True}])["credential_rotation"],
1963:lambda:o.record_security_admin_decision([],"rotate","u","stale","f","2026-01-01T00:00:00Z")["entry"]["sensitive_values_redacted"],
1964:lambda:"reauth_dialog" in o.security_accessibility_timeline([])["security_controls_checked"],
1965:lambda:o.prepare_security_storage_transfer([{"name":"a","size":1,"sha256":"a"*64}],"nextcloud",2)["envelope_encryption"],
1966:lambda:"contain" in o.evaluate_security_time_policy([],30,1,True)["security_actions_allowed"],
1967:lambda:len(o.simulate_security_growth([10,11],2,1)["coverage"])==2,
1968:lambda:o.map_ai_dependencies([{"id":"a","depends_on":["b"]},{"id":"b"}])["models_without_fallback"]==["a"],
1969:lambda:o.apply_ai_visual_rules({},[{"id":"r","max_confidence":.5,"set":{"review_button":True}}],.4)["panel"]["review_button"],
1970:lambda:o.ai_review_inbox([{"id":"d","domain":"moderation","confidence":.2,"impact":2}],["moderation"])["actionable"]==1,
1971:lambda:o.detect_sensitive_ai_changes({"auto_action":False},{"auto_action":True})["requires_human_approval"],
1972:lambda:o.explain_ai_decision({"decision":"review","model_id":"m","confidence":.8,"factors":[]})["human_override"],
1973:lambda:o.ai_data_quality([{"id":"x","label":"ok","source":"group","consent":True}])["training_ready"],
1974:lambda:not o.preview_ai_import([{"id":"x","text":"t","label":"ok","source":"g","consent":False}])["commit_allowed"],
1975:lambda:o.add_ai_comment({},"u","check","bias","2026-01-01T00:00:00Z")["comment"]["training_use"] is False,
1976:lambda:o.ai_smart_tags([{"id":"x","text":"private malware"}])["items"][0]["escalate"],
1977:lambda:o.ai_activity_digest([{"category":"infer","model_id":"m","outcome":"ok"}],["m"])["by_outcome"]["ok"]==1,
1978:lambda:o.ai_expiry_alerts([{"id":"m","expires_at":"2026-01-01T00:00:00Z"}],"2026-01-02T00:00:00Z")["alerts"][0]["action"]=="disable",
1979:lambda:o.open_ai_emergency({},"unsafe","u","2026-01-01T00:00:00Z")["state"]["learning_paused"],
1980:lambda:o.ai_permission_history([{"user_id":"u","permission":"model_deploy","action":"grant","at":"2026-01-01T00:00:00Z"}],"u")["ai_privileged"]==["model_deploy"],
1981:lambda:o.update_ai_goal({"target":2,"progress":0},"u",1,"precision")["metric"]=="precision",
    }


class WebappContentSecurityAiTests(unittest.TestCase):
    def test_manifest_exact_unique_callable(self):
        self.assertEqual([x["id"] for x in FEATURES],[f"future-{n}" for n in range(1922,1982)])
        self.assertEqual(len({x["api"] for x in FEATURES}),60)
        for row in FEATURES:
            self.assertTrue(all(row.get(k) for k in ("id","title","capability","module","api","test","preflight")))
            self.assertTrue(callable(getattr(o,row["api"])))

    def test_security_no_active_io_or_dynamic_execution(self):
        source=inspect.getsource(o)
        for forbidden in ("requests.","urllib.request","subprocess","eval(","exec(","os.system","innerHTML"):
            self.assertNotIn(forbidden,source)
        self.assertFalse(o.SECURITY_CONTRACT["network_io"])
        self.assertFalse(o.SECURITY_CONTRACT["destructive_side_effects"])
        self.assertEqual(o.SECURITY_CONTRACT["rendering"],"textContent_only")

    def test_storage_rejects_traversal(self):
        for name in ("../secret", "..\\secret", "report.txt:payload", "NUL.txt", "trailing."):
            with self.subTest(name=name), self.assertRaises(ValueError):
                o.prepare_security_storage_transfer([{"name":name,"size":1,"sha256":"a"*64}],"webdav",2)

    def test_destructive_modes_are_reversible_and_not_executed(self):
        opened=o.open_security_emergency({"mode":"normal"},"test","u","2026-01-01T00:00:00Z")
        self.assertTrue(opened["dual_confirmation_required"]); self.assertIn("restore_token",opened); self.assertEqual(opened["snapshot"],{"mode":"normal"})


def _make_test(number,case):
    def test(self): self.assertTrue(case())
    test.__name__=f"test_future_{number}"; return test


for _number,_case in _cases().items(): setattr(WebappContentSecurityAiTests,f"test_future_{_number}",_make_test(_number,_case))


if __name__=="__main__": unittest.main()

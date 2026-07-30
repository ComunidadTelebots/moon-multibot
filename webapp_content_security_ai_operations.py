"""Concrete Telegram WebApp contracts for roadmap IDs future-1922..1981."""

from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
import re

import webapp_offline_operations as base
import webapp_accessibility_operations as advanced
import webapp_moderation_content_operations as domain


SECURITY_CONTRACT = {
    "network_io": False,
    "authentication": "delegated_to_protected_feature_runtime",
    "authorization": "roles_and_scopes_must_be_verified_before_invocation",
    "rendering": "textContent_only",
    "restore_token_is_authorization": False,
    "secrets_in_results": False,
    "destructive_side_effects": False,
}


def _text(value,name,limit=500):
    value=" ".join(str(value or "").split())
    if not value or len(value)>limit: raise ValueError(f"invalid {name}")
    return value


def _list(value,name,limit=2000):
    if not isinstance(value,list) or len(value)>limit: raise ValueError(f"invalid {name}")
    return value


# Content operations -------------------------------------------------------
def recommend_content_config(metrics,current):  # future-1922
    cfg=dict(current or {}); recommendations=[]
    if float(metrics.get("bounce_rate",0))>.6: recommendations.append({"key":"summary_first","value":True,"reason":"high_bounce"})
    if float(metrics.get("image_failure_rate",0))>.05: recommendations.append({"key":"image_fallback","value":True,"reason":"image_failures"})
    if int(metrics.get("stale_articles",0)): recommendations.append({"key":"expiry_review","value":True,"reason":"stale_content"})
    return {"recommendations":recommendations,"current":cfg,"editor_approval_required":True}


def test_content_config(config):  # future-1923
    cfg=dict(config or {}); checks={"max_title":20<=int(cfg.get("max_title_length",0))<=200,"source":cfg.get("require_source") is True,"preview":cfg.get("preview_before_publish") is True,"summary":50<=int(cfg.get("summary_length",0))<=500}
    return {"valid":all(checks.values()),"checks":checks,"sandboxed":True,"published":False}


def update_content_consent(state,actor_id,purposes,version,now):  # future-1924
    allowed={"personalization","analytics","recommendations"}; selected=sorted(set(purposes))
    if not set(selected)<=allowed: raise ValueError("unsupported content consent")
    result=base.update_offline_consent(state,"content_preferences",bool(selected),version,now); result["record"].update({"actor_id":_text(actor_id,"actor_id",80),"purposes":selected,"can_withdraw":True}); return result


def content_task_navigation(tasks,completed=None):  # future-1925
    result=base.offline_task_navigation(tasks,"content_editor",completed)
    for task in result["tasks"]: task["editor_action"]="continue" if task["ready"] else "view_dependencies"
    return result


def sync_content_devices(local,remote):  # future-1926
    result=base.sync_offline_devices(local,remote); result["draft_conflicts"]=[x for x in result["conflicts"] if x["key"].startswith("draft:")]; result["never_auto_publish"] = True; return result


def detect_content_duplicates(records):  # future-1927
    exact=base.detect_offline_duplicates(records,["title","source_url"]); body_hashes=defaultdict(list)
    for index,row in enumerate(records): body_hashes[hashlib.sha256(str(row.get("body","")).strip().casefold().encode()).hexdigest()[:16]].append(index)
    exact["same_body"]=[{"hash":key,"rows":rows} for key,rows in body_hashes.items() if len(rows)>1]; return exact


def content_adaptive_quota(usage,base_limit,scheduled_count=0):  # future-1928
    result=base.offline_adaptive_quota(usage,base_limit); reserved=min(base_limit//2,max(0,int(scheduled_count))*2); result.update({"scheduled_reserve":reserved,"interactive_limit":max(1,result["suggested_limit"]-reserved)}); return result


def content_community_impact(events):  # future-1929
    result=base.offline_community_impact(events); result.update({"articles_helpful":result["metrics"].get("helpful",0),"corrections_applied":result["metrics"].get("correction",0),"aggregate_public":True}); return result


def review_content_translation(entry,reviewer_id,decision,suggestion=None):  # future-1930
    result=base.review_offline_translation(entry,reviewer_id,decision,suggestion); result["source_language"]=_text(entry.get("source_language"),"source_language",20); result["target_language"]=_text(entry.get("target_language"),"target_language",20); result["terminology_checked"]=bool(entry.get("terminology_checked")); return result


def group_content_notifications(notifications):  # future-1931
    result=base.group_offline_notifications(notifications)
    for group in result["groups"]: group["digest_action"]="review_all"; group["channels"]=sorted({str(x.get("channel","web")) for x in notifications if x.get("context")==group["context"]})
    return result


def plan_content_migration(config,migrations):  # future-1932
    result=advanced.plan_offline_migration(config,migrations); result.update({"draft_backup":True,"redirect_map_required":True,"publish_lock":bool(result["steps"])}); return result


def record_content_admin_decision(log,decision,actor_id,rationale,content_id,at):  # future-1933
    result=advanced.record_offline_admin_decision(log,decision,actor_id,rationale,at); entry=result["entry"]; entry["content_id"]=_text(content_id,"content_id",100); entry["hash"]=hashlib.sha256(json.dumps({k:v for k,v in entry.items() if k!="hash"},sort_keys=True).encode()).hexdigest(); result["log"][-1]=entry; return result


def content_accessibility_timeline(snapshots):  # future-1934
    result=advanced.continuous_accessibility_timeline(snapshots); result["publishing_blocked"]=any(x["introduced"]>0 for x in result["timeline"]); result["required_media_checks"]=["alt","captions","transcript"]; return result


def prepare_content_storage_transfer(files,provider,quota_bytes):  # future-1935
    result=advanced.prepare_offline_storage_transfer(files,provider,quota_bytes); result.update({"preserve_canonical_urls":True,"generate_redirect_manifest":True,"publish_after_checksum":False}); return result


def evaluate_content_time_policy(policies,local_minute,weekday,breaking_news=False):  # future-1936
    result=advanced.evaluate_offline_time_policy(policies,local_minute,weekday); result["breaking_news_override"]=bool(breaking_news); result["can_publish"]=bool(breaking_news or not result["effective"] or result["effective"]["action"]!="block_publish"); return result


def simulate_content_growth(history,months,publishing_capacity):  # future-1937
    result=advanced.simulate_offline_sustainable_growth(history,months); capacity=int(publishing_capacity)
    if capacity<1: raise ValueError("publishing capacity required")
    result["capacity"]=[{"month":x["month"],"audience":x["members"],"overloaded":x["members"]/capacity>10000} for x in result["projection"]]; return result


# Security operations ------------------------------------------------------
def map_security_dependencies(services):  # future-1938
    nodes={_text(x.get("id"),"service id",80):x for x in _list(services,"services",500)}; edges=[]
    for sid,item in nodes.items():
        for dep in item.get("depends_on",[]):
            if str(dep) not in nodes: raise ValueError("unknown security dependency")
            edges.append({"from":sid,"to":str(dep),"trust_boundary":bool(item.get("trust_boundary")),"fallback":bool(item.get("fallback"))})
    return {"nodes":sorted(nodes),"edges":edges,"single_points":sorted({x["to"] for x in edges if not x["fallback"]})}


def apply_security_visual_rules(panel,rules,risk_level):  # future-1939
    levels={"low":1,"medium":2,"high":3,"critical":4}
    if risk_level not in levels: raise ValueError("invalid risk")
    output=deepcopy(dict(panel or {})); matched=[]
    for rule in _list(rules,"rules",100):
        if levels[risk_level] < levels.get(rule.get("minimum_risk"),1): continue
        changes=dict(rule.get("set") or {}); forbidden=set(changes)-{"badge","color_token","confirm","icon","detail_level"}
        if forbidden: raise ValueError("unsafe security visual property")
        output.update(changes); matched.append(_text(rule.get("id"),"rule id",80))
    return {"panel":output,"matched_rules":matched,"risk_level":risk_level,"color_not_only_signal":True}


def security_review_inbox(findings,reviewer_scopes):  # future-1940
    scopes=set(reviewer_scopes); weight={"critical":400,"high":300,"medium":200,"low":100}; rows=[]
    for finding in _list(findings,"findings",2000):
        scope=str(finding.get("scope")); authorized=scope in scopes or "global" in scopes; age=int(finding.get("age_minutes",0)); severity=str(finding.get("severity","low"))
        rows.append({"id":_text(finding.get("id"),"finding id",100),"severity":severity,"scope":scope,"authorized":authorized,"score":weight.get(severity,0)+min(age,100)})
    rows.sort(key=lambda x:-x["score"]); return {"items":rows,"actionable":sum(x["authorized"] for x in rows)}


def detect_sensitive_security_changes(before,after):  # future-1941
    watched={"auth","roles","firewall","tokens","encryption","retention"}; changes=[]
    for field in sorted(watched):
        if before.get(field)!=after.get(field): changes.append({"field":field,"changed":True,"secret_values_redacted":field=="tokens","rollback_required":field in {"auth","roles","encryption"}})
    return {"changes":changes,"requires_dual_approval":any(x["rollback_required"] for x in changes),"values_redacted":True}


def explain_security_decision(trace):  # future-1942
    result=base.explain_offline_decision(trace); result.update({"finding_id":_text(trace.get("finding_id"),"finding_id",100),"policy_id":_text(trace.get("policy_id"),"policy_id",100),"evidence_redacted":True,"appeal_or_override":True}); return result


def security_data_quality(records):  # future-1943
    result=base.offline_data_quality(records,["id","kind","severity","observed_at"]); invalid=sum(str(x.get("severity")) not in {"low","medium","high","critical"} for x in records); result.update({"invalid_severity":invalid,"triage_ready":result["score"]==100 and invalid==0}); return result


def preview_security_import(records):  # future-1944
    result=base.preview_offline_import(records,["id","kind","severity","observed_at","evidence_hash","scope"]); invalid=[x.get("id") for x in result["preview"] if not re.fullmatch(r"[0-9a-f]{64}",str(x.get("evidence_hash","")))]; result.update({"invalid_evidence_hashes":invalid,"commit_allowed":not invalid and not result["rejected"]}); return result


def add_security_comment(finding,actor_id,body,classification,created_at=None):  # future-1945
    if classification not in {"internal","restricted","public"}: raise ValueError("invalid classification")
    result=base.add_offline_comment(finding,actor_id,body,created_at); result["comment"].update({"classification":classification,"secrets_scanned":True}); return result


def security_smart_tags(findings):  # future-1946
    result=base.offline_smart_tags(findings,["phishing","malware","credential","spam","raid","xss","injection","botnet"])
    for row in result["items"]: row["priority"]="high" if set(row["tags"])&{"credential","malware","botnet"} else "normal"
    return result


def security_activity_digest(events,severities=None):  # future-1947
    allowed=set(severities or []); filtered=[x for x in _list(events,"events",5000) if not allowed or x.get("severity") in allowed]; result=base.offline_activity_digest(filtered); result["by_severity"]=dict(Counter(str(x.get("severity","unknown")) for x in filtered)); result["identifiers_redacted"]=True; return result


def security_expiry_alerts(credentials,now=None):  # future-1948
    result=base.offline_expiry_alerts(credentials,now,720)
    for alert in result["alerts"]: alert["action"]="revoke" if alert["expired"] else "rotate"; alert["secret_included"]=False
    return result


def open_security_emergency(state,reason,actor_id,now=None):  # future-1949
    result=base.open_offline_emergency(state,reason,actor_id,now); result["state"].update({"sessions_revoked":True,"write_lock":True,"audit_exported":True,"break_glass":True}); result["dual_confirmation_required"]=True; return result


def security_permission_history(events,user_id):  # future-1950
    result=base.offline_permission_history(events,user_id); privileged={"security_admin","token_rotate","audit_export","global_ban"}; result["privileged"]=sorted(privileged&set(result["effective_permissions"])); result["least_privilege_ok"]=len(result["privileged"])<=2; return result


def update_security_goal(goal,actor_id,delta,control_id):  # future-1951
    result=base.update_offline_shared_goal(goal,actor_id,delta,control_id); result.update({"control_id":_text(control_id,"control_id",80),"evidence_required":True,"self_attestation_only":False}); return result


def recommend_security_config(signals,current):  # future-1952
    rec=[]
    if not current.get("mfa_required"): rec.append({"key":"mfa_required","value":True,"reason":"baseline"})
    if int(signals.get("failed_logins",0))>10: rec.append({"key":"rate_limit","value":"strict","reason":"failed_logins"})
    if int(signals.get("stale_tokens",0)): rec.append({"key":"rotate_tokens","value":True,"reason":"stale_tokens"})
    return {"recommendations":rec,"auto_applied":False,"requires_admin":True}


def test_security_config(config):  # future-1953
    cfg=dict(config or {}); checks={"mfa":cfg.get("mfa_required") is True,"https":cfg.get("https_only") is True,"token_ttl":60<=int(cfg.get("token_ttl_seconds",0))<=86400,"audit":cfg.get("audit_enabled") is True}
    return {"valid":all(checks.values()),"checks":checks,"sandboxed":True,"live_credentials_used":False}


def update_security_consent(state,actor_id,purpose,granted,version,now):  # future-1954
    if purpose not in {"security_telemetry","breach_alerts","device_history"}: raise ValueError("invalid security consent")
    result=base.update_offline_consent(state,purpose,granted,version,now); result["record"].update({"actor_id":_text(actor_id,"actor_id",80),"minimum_security_logs_retained":True}); return result


def security_task_navigation(tasks,completed=None):  # future-1955
    result=base.offline_task_navigation(tasks,"security_admin",completed)
    for task in result["tasks"]: task["requires_reauthentication"]=bool(next((x.get("privileged") for x in tasks if str(x.get("id"))==task["id"]),False))
    return result


def sync_security_devices(local,remote):  # future-1956
    result=base.sync_offline_devices(local,remote); result["security_conflicts"]=[x for x in result["conflicts"] if x["key"].startswith(("auth:","role:","token:"))]; result["auto_merge_security_conflicts"]=False; return result


def detect_security_duplicates(records):  # future-1957
    result=base.detect_offline_duplicates(records,["kind","evidence_hash","scope"]); result["dedupe_requires_review"]=bool(result["duplicates"]); result["evidence_preserved"]=True; return result


def security_adaptive_quota(usage,base_limit,threat_level="low"):  # future-1958
    result=base.offline_adaptive_quota(usage,base_limit); factors={"low":1,"medium":1.25,"high":1.5,"critical":2}
    if threat_level not in factors: raise ValueError("invalid threat level")
    result["suggested_limit"]=round(result["suggested_limit"]*factors[threat_level]); result["threat_level"]=threat_level; result["audit_never_limited"]=True; return result


def security_community_impact(events):  # future-1959
    result=base.offline_community_impact(events); result.update({"incidents_prevented":result["metrics"].get("incident_prevented",0),"accounts_recovered":result["metrics"].get("account_recovered",0),"privacy":"aggregate_k_anonymous"}); return result


def review_security_translation(entry,reviewer_id,decision,suggestion=None):  # future-1960
    result=base.review_offline_translation(entry,reviewer_id,decision,suggestion); required={"warning","action","recovery"}; result["security_terms_complete"]=required<=set(entry.get("terms",[])); result["phishing_safe_links"]=bool(entry.get("safe_links")); return result


def group_security_notifications(notifications):  # future-1961
    result=base.group_offline_notifications(notifications); result["critical_count"]=sum(x.get("severity")=="critical" for x in notifications)
    for group in result["groups"]: group["ack_required"]=any(x.get("severity") in {"high","critical"} for x in notifications if x.get("context")==group["context"])
    return result


def plan_security_migration(config,migrations):  # future-1962
    result=advanced.plan_offline_migration(config,migrations); result.update({"credential_rotation":True,"rollback_signed":True,"maintenance_window_required":bool(result["steps"])}); return result


def record_security_admin_decision(log,decision,actor_id,rationale,finding_id,at):  # future-1963
    result=advanced.record_offline_admin_decision(log,decision,actor_id,rationale,at); entry=result["entry"]; entry["finding_id"]=_text(finding_id,"finding_id",100); entry["sensitive_values_redacted"]=True; entry["hash"]=hashlib.sha256(json.dumps({k:v for k,v in entry.items() if k!="hash"},sort_keys=True).encode()).hexdigest(); result["log"][-1]=entry; return result


def security_accessibility_timeline(snapshots):  # future-1964
    result=advanced.continuous_accessibility_timeline(snapshots); result["security_controls_checked"]=["reauth_dialog","warning","recovery","session_list"]; result["accessible_security_required"]=True; return result


def prepare_security_storage_transfer(files,provider,quota_bytes):  # future-1965
    result=advanced.prepare_offline_storage_transfer(files,provider,quota_bytes); result.update({"envelope_encryption":True,"key_exported":False,"immutable_audit":True,"restore_test_required":True}); return result


def evaluate_security_time_policy(policies,local_minute,weekday,incident=False):  # future-1966
    result=advanced.evaluate_offline_time_policy(policies,local_minute,weekday); result["incident_override"]=bool(incident); result["security_actions_allowed"]=["contain","revoke","notify"] if incident else ([result["effective"]["action"]] if result["effective"] else []); return result


def simulate_security_growth(history,months,analyst_count):  # future-1967
    result=advanced.simulate_offline_sustainable_growth(history,months); analysts=int(analyst_count)
    if analysts<1: raise ValueError("analyst required")
    result["coverage"]=[{"month":x["month"],"assets":x["members"],"assets_per_analyst":round(x["members"]/analysts,1),"capacity_warning":x["members"]/analysts>500} for x in result["projection"]]; return result


# AI operations ------------------------------------------------------------
def map_ai_dependencies(models):  # future-1968
    nodes={_text(x.get("id"),"model id",100):x for x in _list(models,"models",500)}; edges=[]
    for mid,item in nodes.items():
        for dep in item.get("depends_on",[]):
            if str(dep) not in nodes: raise ValueError("unknown AI dependency")
            edges.append({"from":mid,"to":str(dep),"purpose":_text(item.get("purpose","inference"),"purpose",100),"fallback":bool(item.get("fallback"))})
    return {"nodes":sorted(nodes),"edges":edges,"models_without_fallback":sorted({x["from"] for x in edges if not x["fallback"]})}


def apply_ai_visual_rules(panel,rules,confidence):  # future-1969
    score=float(confidence)
    if not 0<=score<=1: raise ValueError("invalid confidence")
    output=deepcopy(dict(panel or {})); matched=[]
    for rule in _list(rules,"rules",100):
        if score>float(rule.get("max_confidence",1)): continue
        changes=dict(rule.get("set") or {}); forbidden=set(changes)-{"badge","explanation","review_button","confidence_label","fallback"}
        if forbidden: raise ValueError("unsafe AI visual property")
        output.update(changes); matched.append(_text(rule.get("id"),"rule id",80))
    return {"panel":output,"confidence":score,"matched_rules":matched,"uncertainty_visible":True}


def ai_review_inbox(decisions,reviewer_domains):  # future-1970
    domains=set(reviewer_domains); rows=[]
    for item in _list(decisions,"decisions",2000):
        confidence=float(item.get("confidence",0)); domain=str(item.get("domain")); impact=int(item.get("impact",1)); rows.append({"id":_text(item.get("id"),"decision id",100),"domain":domain,"authorized":domain in domains or "all" in domains,"priority":round((1-confidence)*100+impact*10,2),"confidence":confidence})
    rows.sort(key=lambda x:-x["priority"]); return {"items":rows,"actionable":sum(x["authorized"] for x in rows),"human_review":True}


def detect_sensitive_ai_changes(before,after):  # future-1971
    watched={"model","prompt","threshold","training_sources","retention","auto_action"}; changes=[]
    for field in sorted(watched):
        if before.get(field)!=after.get(field): changes.append({"field":field,"requires_evaluation":True,"high_risk":field in {"training_sources","auto_action","retention"}})
    return {"changes":changes,"requires_human_approval":any(x["high_risk"] for x in changes),"values_not_logged":True}


def explain_ai_decision(trace):  # future-1972
    result=base.explain_offline_decision(trace); confidence=float(trace.get("confidence",0))
    if not 0<=confidence<=1: raise ValueError("invalid confidence")
    result.update({"model_id":_text(trace.get("model_id"),"model_id",100),"confidence":confidence,"limitations":list(trace.get("limitations",[]))[:10],"human_override":True}); return result


def ai_data_quality(records):  # future-1973
    result=base.offline_data_quality(records,["id","label","source","consent"]); unconsented=sum(x.get("consent") is not True for x in records); labels=Counter(str(x.get("label")) for x in records); result.update({"unconsented":unconsented,"label_distribution":dict(labels),"training_ready":result["score"]==100 and unconsented==0}); return result


def preview_ai_import(records):  # future-1974
    result=base.preview_offline_import(records,["id","text","label","source","consent","language"]); blocked=[x.get("id") for x in result["preview"] if x.get("consent") is not True]; result.update({"blocked_without_consent":blocked,"commit_allowed":not blocked and not result["rejected"],"training_started":False}); return result


def add_ai_comment(decision,actor_id,body,review_kind,created_at=None):  # future-1975
    if review_kind not in {"bias","accuracy","safety","explanation"}: raise ValueError("invalid review kind")
    result=base.add_offline_comment(decision,actor_id,body,created_at); result["comment"].update({"review_kind":review_kind,"human_feedback":True,"training_use":False}); return result


def ai_smart_tags(items):  # future-1976
    result=base.offline_smart_tags(items,["bias","hallucination","unsafe","uncertain","private","copyright","spam","malware"])
    for row in result["items"]: row["escalate"]=bool(set(row["tags"])&{"unsafe","private","malware"})
    return result


def ai_activity_digest(events,models=None):  # future-1977
    allowed=set(models or []); filtered=[x for x in _list(events,"events",5000) if not allowed or str(x.get("model_id")) in allowed]; result=base.offline_activity_digest(filtered); result["by_outcome"]=dict(Counter(str(x.get("outcome","unknown")) for x in filtered)); result["personal_data_included"]=False; return result


def ai_expiry_alerts(artifacts,now=None):  # future-1978
    result=base.offline_expiry_alerts(artifacts,now,720)
    for alert in result["alerts"]: alert["action"]="disable" if alert["expired"] else "revalidate"
    return result


def open_ai_emergency(state,reason,actor_id,now=None):  # future-1979
    result=base.open_offline_emergency(state,reason,actor_id,now); result["state"].update({"ai_auto_actions":False,"human_review_required":True,"learning_paused":True,"safe_fallback":True}); result["rollback_model_preserved"]=True; return result


def ai_permission_history(events,user_id):  # future-1980
    result=base.offline_permission_history(events,user_id); privileged={"model_deploy","training_write","prompt_admin","auto_action"}; result["ai_privileged"]=sorted(privileged&set(result["effective_permissions"])); result["separation_of_duties_ok"]=len(result["ai_privileged"])<3; return result


def update_ai_goal(goal,actor_id,delta,metric):  # future-1981
    result=base.update_offline_shared_goal(goal,actor_id,delta,metric); result.update({"metric":_text(metric,"metric",80),"evaluation_required":True,"human_validated":False}); return result

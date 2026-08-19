"""Concrete mobile-moderation and content WebApp contracts (1882..1921)."""

from collections import Counter
from copy import deepcopy
import hashlib
import json

import webapp_offline_operations as base
import webapp_accessibility_operations as advanced


def _text(value, name, limit=500):
    clean=" ".join(str(value or "").split())
    if not clean or len(clean)>limit: raise ValueError(f"invalid {name}")
    return clean


def _list(value,name,limit=1000):
    if not isinstance(value,list) or len(value)>limit: raise ValueError(f"invalid {name}")
    return value


def explain_mobile_moderation_decision(trace):  # future-1882
    result=base.explain_offline_decision(trace); evidence=[_text(x,"evidence",200) for x in trace.get("evidence_ids",[])]
    result.update({"case_id":_text(trace.get("case_id"),"case_id",100),"evidence_ids":evidence,"appeal_available":bool(trace.get("appeal_available",True)),"moderation_context":"mobile"}); return result


def mobile_mod_data_quality(cases):  # future-1883
    result=base.offline_data_quality(cases,["id","subject_id","reason","status"]); dangling=sum(not x.get("evidence_ids") for x in cases)
    result.update({"cases_without_evidence":dangling,"moderation_ready":result["score"]==100 and dangling==0}); return result


def preview_mobile_mod_import(cases):  # future-1884
    allowed=["id","subject_id","reason","status","evidence_ids","created_at","scope"]
    result=base.preview_offline_import(cases,allowed); result["requires_confirmation"]=[x.get("id") for x in result["preview"] if x.get("status") in {"ban","global_ban"}]; return result


def add_mobile_mod_comment(case,actor_id,body,visibility="moderators",created_at=None):  # future-1885
    if visibility not in {"moderators","subject","master"}: raise ValueError("invalid visibility")
    result=base.add_offline_comment(case,actor_id,body,created_at); result["comment"].update({"visibility":visibility,"case_note":True}); return result


def mobile_mod_smart_tags(cases):  # future-1886
    vocabulary=["spam","scam","raid","harassment","malware","impersonation","captcha","cas"]
    result=base.offline_smart_tags(cases,vocabulary)
    for row in result["items"]: row["requires_human_review"]="harassment" in row["tags"] or "impersonation" in row["tags"]
    return result


def mobile_mod_activity_digest(events,actions=None):  # future-1887
    result=base.offline_activity_digest(events,actions); result["by_outcome"]=dict(Counter(str(x.get("outcome","unknown")) for x in events)); result["mobile_cards"]=min(20,result["total"]); return result


def mobile_mod_expiry_alerts(sanctions,now=None):  # future-1888
    result=base.offline_expiry_alerts(sanctions,now,48)
    for alert in result["alerts"]: alert["quick_action"]="restore" if alert["expired"] else "extend"
    return result


def open_mobile_mod_emergency(state,reason,actor_id,now=None):  # future-1889
    result=base.open_offline_emergency(state,reason,actor_id,now); result["state"].update({"slow_mode":True,"new_member_mute":True,"approval_required":True}); result["confirmation_phrase"]="CONFIRMAR EMERGENCIA"; return result


def mobile_mod_permission_history(events,user_id):  # future-1890
    result=base.offline_permission_history(events,user_id); dangerous={"ban","global_ban","delete_messages"}; result["dangerous_permissions"]=sorted(dangerous & set(result["effective_permissions"])); return result


def update_mobile_mod_goal(goal,actor_id,delta,action_type):  # future-1891
    result=base.update_offline_shared_goal(goal,actor_id,delta,action_type); result["action_type"]=_text(action_type,"action_type",80); result["team_visible"]=True; return result


def recommend_mobile_mod_config(telemetry,current):  # future-1892
    result=base.recommend_offline_config(telemetry,current); extra=[]
    if float(telemetry.get("false_positive_rate",0))>.05: extra.append({"key":"auto_action","value":False,"reason":"false_positive_rate"})
    if int(telemetry.get("raid_events",0))>0: extra.append({"key":"raid_shield","value":True,"reason":"raid_detected"})
    result["recommendations"].extend(extra); result["moderation_safe_defaults"]=True; return result


def test_mobile_mod_config(config):  # future-1893
    cfg=dict(config or {}); checks={"appeal":cfg.get("appeal_enabled") is True,"evidence":cfg.get("require_evidence") is True,"timeout":30<=int(cfg.get("default_mute_seconds",0))<=31536000,"confirm_ban":cfg.get("confirm_destructive") is True}
    return {"valid":all(checks.values()),"checks":checks,"sandbox_actions":True,"messages_sent":0}


def update_mobile_mod_consent(state,actor_id,decision,version,now):  # future-1894
    if decision not in {"analytics","assisted_review","none"}: raise ValueError("invalid moderation consent")
    result=base.update_offline_consent(state,"moderation_assistance",decision!="none",version,now); result["record"].update({"actor_id":_text(actor_id,"actor_id",80),"decision":decision,"automated_bans":False}); return result


def mobile_mod_task_navigation(tasks,completed=None):  # future-1895
    result=base.offline_task_navigation(tasks,"mobile_moderator",completed)
    for task in result["tasks"]: task["touch_action"]="open_case"; task["destructive"]=bool(next((x.get("destructive") for x in tasks if str(x.get("id"))==task["id"]),False))
    return result


def sync_mobile_mod_devices(local,remote):  # future-1896
    result=base.sync_offline_devices(local,remote); result["conflict_policy"]="manual_for_sanctions"; result["blocked_keys"]=[x["key"] for x in result["conflicts"] if x["key"].startswith("sanction:")]; return result


def detect_mobile_mod_duplicates(cases):  # future-1897
    result=base.detect_offline_duplicates(cases,["subject_id","reason","scope"]); result["merge_allowed"]=not any("global" in str(x["signature"]) for x in result["duplicates"]); return result


def mobile_mod_adaptive_quota(usage,base_limit,active_raid=False):  # future-1898
    result=base.offline_adaptive_quota(usage,base_limit)
    if active_raid: result["suggested_limit"]=min(base_limit*3,result["suggested_limit"]*2)
    result.update({"active_raid":bool(active_raid),"never_limits_appeals":True}); return result


def mobile_mod_community_impact(events):  # future-1899
    result=base.offline_community_impact(events); result["appeal_overturns"]=result["metrics"].get("appeal_overturned",0); result["prevented_raids"]=result["metrics"].get("raid_prevented",0); result["no_user_ids_exposed"]=True; return result


def review_mobile_mod_translation(entry,reviewer_id,decision,suggestion=None):  # future-1900
    result=base.review_offline_translation(entry,reviewer_id,decision,suggestion); required={"reason","appeal","duration"}; result["moderation_terms_complete"]=required <= set(entry.get("terms",[])); return result


def group_mobile_mod_notifications(notifications):  # future-1901
    result=base.group_offline_notifications(notifications)
    for group in result["groups"]: group["batch_actions"]=["mark_read","assign"] + (["escalate"] if group["unread"] else [])
    result["critical_count"]=sum(x.get("priority")=="critical" for x in notifications); return result


def plan_mobile_mod_migration(config,migrations):  # future-1902
    result=advanced.plan_offline_migration(config,migrations); result.update({"dry_run_required":True,"sanction_backup_required":True,"rollback_window_hours":24}); return result


def record_mobile_mod_admin_decision(log,decision,actor_id,rationale,case_id,at):  # future-1903
    result=advanced.record_offline_admin_decision(log,decision,actor_id,rationale,at); entry=result["entry"]; entry["case_id"]=_text(case_id,"case_id",100); entry["hash"]=hashlib.sha256(json.dumps({k:v for k,v in entry.items() if k!="hash"},sort_keys=True).encode()).hexdigest(); result["log"][-1]=entry; return result


def mobile_mod_accessibility_timeline(snapshots):  # future-1904
    result=advanced.continuous_accessibility_timeline(snapshots); result["mobile_moderation_controls"]=["ban","mute","appeal","evidence"]; result["block_release_on_critical"]=result["current_issues"]>0; return result


def prepare_mobile_mod_storage_transfer(files,provider,quota_bytes):  # future-1905
    result=advanced.prepare_offline_storage_transfer(files,provider,quota_bytes); result.update({"evidence_retention_days":30,"client_side_encryption":True,"export_audit_required":True}); return result


def evaluate_mobile_mod_time_policy(policies,local_minute,weekday,on_call=False):  # future-1906
    result=advanced.evaluate_offline_time_policy(policies,local_minute,weekday); result["on_call_override"]=bool(on_call); result["effective_action"]="notify" if on_call and result["effective"] else (result["effective"] or {}).get("action"); return result


def simulate_mobile_mod_growth(history,months,moderators):  # future-1907
    result=advanced.simulate_offline_sustainable_growth(history,months); count=int(moderators)
    if count<1: raise ValueError("moderator required")
    result["cases_per_moderator"]=[{"month":x["month"],"estimated_members":x["members"],"capacity_warning":x["members"]/count>1000} for x in result["projection"]]; return result


def map_content_dependencies(resources):  # future-1908
    nodes={_text(x.get("id"),"resource id",100):x for x in _list(resources,"resources",500)}; edges=[]
    for rid,item in nodes.items():
        for dependency in item.get("depends_on",[]):
            dep=str(dependency)
            if dep not in nodes: raise ValueError("unknown content dependency")
            edges.append({"from":rid,"to":dep,"blocking":bool(item.get("blocking",True))})
    return {"nodes":sorted(nodes),"edges":edges,"publish_blockers":sorted({x["from"] for x in edges if x["blocking"]})}


def apply_content_visual_rules(content,rules,channel):  # future-1909
    output=deepcopy(dict(content or {})); matched=[]
    for rule in _list(rules,"rules",100):
        channels=set(rule.get("channels",[]))
        if channels and channel not in channels: continue
        changes=dict(rule.get("set") or {}); forbidden=set(changes)-{"layout","theme","badge","summary_length","image_ratio"}
        if forbidden: raise ValueError("unsupported presentation change")
        output.update(changes); matched.append(_text(rule.get("id"),"rule id",80))
    return {"content":output,"channel":_text(channel,"channel",60),"matched_rules":matched,"content_unchanged":not matched}


def content_review_inbox(items,reviewer_topics=None):  # future-1910
    topics=set(reviewer_topics or []); rows=[]
    for item in _list(items,"items",1000):
        item_topics=set(item.get("topics",[])); match=len(topics&item_topics); deadline=int(item.get("minutes_to_deadline",99999)); score=match*1000+max(0,10000-deadline)
        rows.append({"id":_text(item.get("id"),"content id",100),"title":_text(item.get("title"),"title",300),"score":score,"topic_matches":match,"status":str(item.get("status") or "pending")})
    rows.sort(key=lambda x:(-x["score"],x["id"])); return {"items":rows,"pending":sum(x["status"]=="pending" for x in rows)}


def detect_sensitive_content_changes(before,after):  # future-1911
    watched={"title","body","source_url","author","sponsored","age_rating"}; changes=[]
    for field in sorted(watched):
        if before.get(field)!=after.get(field): changes.append({"field":field,"before_hash":hashlib.sha256(str(before.get(field)).encode()).hexdigest()[:12],"after_hash":hashlib.sha256(str(after.get(field)).encode()).hexdigest()[:12],"review_required":field in {"source_url","sponsored","age_rating"}})
    return {"changes":changes,"requires_review":any(x["review_required"] for x in changes),"body_not_logged":True}


def explain_content_decision(trace):  # future-1912
    result=base.explain_offline_decision(trace); result.update({"content_id":_text(trace.get("content_id"),"content_id",100),"policy":_text(trace.get("policy"),"policy",100),"editor_override":True}); return result


def content_data_quality(records):  # future-1913
    result=base.offline_data_quality(records,["id","title","body","source_url"]); invalid_sources=sum(not str(x.get("source_url","")).startswith("https://") for x in records); result.update({"invalid_sources":invalid_sources,"publishable":result["score"]==100 and invalid_sources==0}); return result


def preview_content_import(records):  # future-1914
    result=base.preview_offline_import(records,["id","title","body","source_url","author","topics","published_at"]); result["word_counts"]={str(x.get("id")):len(str(x.get("body","")).split()) for x in result["preview"]}; result["published"]=False; return result


def add_content_comment(document,actor_id,body,anchor,created_at=None):  # future-1915
    result=base.add_offline_comment(document,actor_id,body,created_at); result["comment"].update({"anchor":_text(anchor,"anchor",120),"resolved":False,"editorial":True}); return result


def content_smart_tags(items,taxonomy):  # future-1916
    result=base.offline_smart_tags(items,taxonomy); result["taxonomy_version"]=hashlib.sha256("|".join(sorted(str(x) for x in taxonomy)).encode()).hexdigest()[:12]; return result


def content_activity_digest(events,topics=None):  # future-1917
    filtered=[x for x in _list(events,"events",2000) if not topics or set(x.get("topics",[]))&set(topics)]; result=base.offline_activity_digest(filtered); result["by_topic"]=dict(Counter(topic for x in filtered for topic in x.get("topics",[]))); result["filters"]={"topics":sorted(topics or [])}; return result


def content_expiry_alerts(items,now=None):  # future-1918
    result=base.offline_expiry_alerts(items,now,168)
    by_id={str(x.get("id")):x for x in items}
    for alert in result["alerts"]: alert["action"]="archive" if by_id[alert["id"]].get("evergreen") is not True else "review"
    return result


def open_content_emergency(state,reason,actor_id,now=None):  # future-1919
    result=base.open_offline_emergency(state,reason,actor_id,now); result["state"].update({"publishing_paused":True,"drafts_preserved":True,"public_banner":"Contenido temporalmente en revisión"}); return result


def content_permission_history(events,user_id):  # future-1920
    result=base.offline_permission_history(events,user_id); editorial={"write","review","publish","archive"}; result["editorial_permissions"]=sorted(editorial&set(result["effective_permissions"])); result["can_publish"]="publish" in result["editorial_permissions"]; return result


def update_content_goal(goal,actor_id,delta,content_type):  # future-1921
    result=base.update_offline_shared_goal(goal,actor_id,delta,content_type); result.update({"content_type":_text(content_type,"content_type",80),"editorial_progress":True}); return result

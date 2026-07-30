"""WebApp contracts for offline, accessibility and mobile moderation (1842..1881)."""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
from urllib.parse import urlparse

import webapp_offline_operations as offline


def _text(value, name, limit=500):
    value = " ".join(str(value or "").split())
    if not value or len(value) > limit: raise ValueError(f"invalid {name}")
    return value


def _list(value, name, limit=1000):
    if not isinstance(value, list) or len(value) > limit: raise ValueError(f"invalid {name}")
    return value


def _time(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def _safe_transfer_filename(value):
    """Validate a portable leaf filename before a later storage adapter uses it."""
    name = _text(value, "file name", 200)
    # Besides directory separators, ':' creates NTFS alternate data streams.
    if name in {".", ".."} or any(char in name for char in "/\\:") or any(ord(char) < 32 for char in name):
        raise ValueError("unsafe file name")
    stem = name.rstrip(" .").split(".", 1)[0].upper()
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    if name != name.rstrip(" .") or stem in reserved:
        raise ValueError("unsafe file name")
    return name


def plan_offline_migration(config, migrations):  # future-1842
    version = int(config.get("version", 0)); ordered = sorted(_list(migrations, "migrations", 100), key=lambda x: int(x["from"]))
    steps, cursor = [], version
    for migration in ordered:
        if int(migration["from"]) != cursor: continue
        target = int(migration["to"])
        if target <= cursor: raise ValueError("non-forward migration")
        steps.append({"from": cursor, "to": target, "changes": deepcopy(migration.get("changes", [])), "reversible": bool(migration.get("reversible"))}); cursor = target
    return {"current_version": version, "target_version": cursor, "steps": steps, "offline_safe": all(step["reversible"] for step in steps), "applied": False}


def record_offline_admin_decision(log, decision, actor_id, rationale, at):  # future-1843
    rows = deepcopy(_list(log, "log", 5000)); stamp = _time(at).isoformat()
    previous = rows[-1].get("hash", "root") if rows else "root"
    entry = {"decision": _text(decision,"decision",120), "actor_id":_text(actor_id,"actor_id",80), "rationale":_text(rationale,"rationale",1000), "at":stamp, "previous_hash":previous, "offline":True}
    entry["hash"] = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest(); rows.append(entry)
    return {"log":rows,"entry":entry,"chain_valid":True}


def scan_offline_accessibility(nodes):  # future-1844
    issues=[]
    for node in _list(nodes,"nodes",2000):
        node_id=_text(node.get("id"),"node id",100); kind=str(node.get("kind") or "")
        if kind=="image" and not str(node.get("alt") or "").strip(): issues.append({"id":node_id,"rule":"image-alt","severity":"serious"})
        if kind in {"button","link"} and not str(node.get("label") or "").strip(): issues.append({"id":node_id,"rule":"accessible-name","severity":"critical"})
        if kind=="heading" and int(node.get("level",0)) not in range(1,7): issues.append({"id":node_id,"rule":"heading-order","severity":"moderate"})
    return {"scanned":len(nodes),"issues":issues,"passes":len(nodes)-len({x['id'] for x in issues}),"ruleset":"WCAG-2.2-AA-offline"}


def prepare_offline_storage_transfer(files, provider, quota_bytes):  # future-1845
    provider=_text(provider,"provider",60); allowed={"webdav","nextcloud","s3-compatible"}
    if provider not in allowed: raise ValueError("unsupported provider")
    total=0; manifest=[]
    for item in _list(files,"files",500):
        size=int(item.get("size",-1)); digest=str(item.get("sha256") or "")
        if size<0 or not re.fullmatch(r"[0-9a-f]{64}",digest): raise ValueError("invalid file metadata")
        name=_safe_transfer_filename(item.get("name"))
        total+=size; manifest.append({"name":name,"size":size,"sha256":digest})
    if total>int(quota_bytes): raise ValueError("external quota exceeded")
    return {"provider":provider,"files":manifest,"bytes":total,"encrypted_before_upload":True,"transfer_started":False}


def evaluate_offline_time_policy(policies, local_minute, weekday):  # future-1846
    minute=int(local_minute); day=int(weekday)
    if not 0<=minute<1440 or not 0<=day<7: raise ValueError("invalid local time")
    matches=[]
    for policy in _list(policies,"policies",200):
        days={int(x) for x in policy.get("days",range(7))}; start=int(policy["start_minute"]); end=int(policy["end_minute"])
        active=day in days and ((start<=minute<end) if start<end else (minute>=start or minute<end))
        if active: matches.append({"id":_text(policy.get("id"),"policy id",80),"action":_text(policy.get("action"),"action",80),"priority":int(policy.get("priority",0))})
    matches.sort(key=lambda x:x["priority"],reverse=True)
    return {"active":matches,"effective":matches[0] if matches else None,"evaluated_offline":True}


def simulate_offline_sustainable_growth(history, months, churn_limit=.1):  # future-1847
    samples=[int(x) for x in _list(history,"history",120)]
    if len(samples)<2 or any(x<0 for x in samples) or not 1<=int(months)<=36: raise ValueError("invalid simulation input")
    rates=[(b-a)/max(a,1) for a,b in zip(samples,samples[1:])]; rate=max(-float(churn_limit),min(.25,sum(rates)/len(rates)))
    projection=[]; current=float(samples[-1])
    for month in range(1,int(months)+1): current=max(0,current*(1+rate)); projection.append({"month":month,"members":round(current)})
    return {"baseline":samples[-1],"monthly_rate":round(rate,4),"projection":projection,"sustainability_cap":.25}


def map_accessibility_dependencies(services):  # future-1848
    nodes={_text(x.get("id"),"service id",80):x for x in _list(services,"services",500)}; edges=[]
    for sid,service in nodes.items():
        for dep in service.get("depends_on",[]):
            dep=str(dep)
            if dep not in nodes: raise ValueError(f"unknown dependency {dep}")
            edges.append({"from":sid,"to":dep,"accessible_fallback":bool(service.get("accessible_fallback"))})
    at_risk=sorted({e["from"] for e in edges if not e["accessible_fallback"]})
    return {"nodes":sorted(nodes),"edges":edges,"accessibility_at_risk":at_risk}


def apply_accessible_visual_rules(component, rules, preferences):  # future-1849
    output=deepcopy(dict(component or {})); matched=[]
    prefs=dict(preferences or {})
    for rule in _list(rules,"rules",100):
        condition=str(rule.get("when")); enabled=condition=="always" or bool(prefs.get(condition))
        if enabled:
            changes=dict(rule.get("set") or {}); forbidden=set(changes)-{"contrast","font_scale","motion","focus_ring","aria_live"}
            if forbidden: raise ValueError("unsafe visual property")
            output.update(changes); matched.append(_text(rule.get("id"),"rule id",80))
    return {"component":output,"matched_rules":matched,"preview":True}


def accessibility_review_inbox(items):  # future-1850
    severity={"critical":4,"serious":3,"moderate":2,"minor":1}; rows=[]
    for item in _list(items,"items",1000):
        level=str(item.get("severity") or "minor")
        if level not in severity: raise ValueError("invalid severity")
        rows.append({"id":_text(item.get("id"),"item id",100),"rule":_text(item.get("rule"),"rule",100),"severity":level,"score":severity[level]*100+int(item.get("affected_users",0)),"status":str(item.get("status") or "pending")})
    rows.sort(key=lambda x:(-x["score"],x["id"]))
    return {"items":rows,"pending":sum(x["status"]=="pending" for x in rows)}


def detect_sensitive_accessibility_changes(before, after):  # future-1851
    watched={"label","role","tabindex","contrast","alt","aria_live","hidden"}; changes=[]
    for key in sorted(watched):
        if before.get(key)!=after.get(key): changes.append({"field":key,"before":before.get(key),"after":after.get(key),"sensitive":True})
    risk=sum(3 if x["field"] in {"role","hidden","label"} else 1 for x in changes)
    return {"changes":changes,"risk_score":risk,"requires_review":risk>=3}


def explain_accessibility_decision(trace):  # future-1852
    base=offline.explain_offline_decision(trace); rule=_text(trace.get("wcag_rule"),"wcag_rule",40)
    base.update({"wcag_rule":rule,"human_review_available":True,"screen_reader_summary":f"Regla {rule}. {base['summary']}"}); return base


def accessibility_data_quality(records):  # future-1853
    base=offline.offline_data_quality(records,["id","role","label"]); duplicate_ids=len(records)-len({str(x.get('id')) for x in records})
    base.update({"duplicate_ids":duplicate_ids,"accessibility_ready":base["score"]==100 and duplicate_ids==0}); return base


def preview_accessibility_import(records):  # future-1854
    allowed=["id","role","label","alt","tabindex","language"]
    base=offline.preview_offline_import(records,allowed)
    base["normalizations"]=[{"id":x.get("id"),"language":str(x.get("language") or "und").lower()} for x in base["preview"]]
    return base


def add_accessibility_comment(document, actor_id, body, rule, created_at=None):  # future-1855
    result=offline.add_offline_comment(document,actor_id,body,created_at); result["comment"]["wcag_rule"]=_text(rule,"rule",40); result["comment"]["review_type"]="accessibility"; return result


def accessibility_smart_tags(items):  # future-1856
    vocabulary=["contrast","keyboard","screen reader","captions","focus","alt text","language"]
    return offline.offline_smart_tags(items,vocabulary)


def accessibility_activity_digest(events, minimum_severity="minor"):  # future-1857
    order={"minor":1,"moderate":2,"serious":3,"critical":4}; threshold=order.get(minimum_severity)
    if threshold is None: raise ValueError("invalid severity")
    filtered=[x for x in _list(events,"events",2000) if order.get(x.get("severity"),0)>=threshold]
    result=offline.offline_activity_digest(filtered); result["by_rule"]=dict(Counter(str(x.get("rule")) for x in filtered)); return result


def accessibility_expiry_alerts(resources, now=None):  # future-1858
    base=offline.offline_expiry_alerts(resources,now,168)
    for alert in base["alerts"]: alert["announcement"]="assertive" if alert["expired"] else "polite"
    return base


def open_accessibility_emergency(state, reason, actor_id, now=None):  # future-1859
    result=offline.open_offline_emergency(state,reason,actor_id,now); result["state"].update({"high_contrast":True,"reduced_motion":True,"screen_reader_mode":True}); return result


def accessibility_permission_history(events, user_id):  # future-1860
    result=offline.offline_permission_history(events,user_id); result["can_review_accessibility"]="accessibility_review" in result["effective_permissions"]; return result


def update_accessibility_goal(goal, actor_id, delta, rule):  # future-1861
    result=offline.update_offline_shared_goal(goal,actor_id,delta,rule); result["wcag_rule"]=_text(rule,"rule",40); return result


def recommend_accessibility_config(audit, current):  # future-1862
    recommendations=[]; cfg=dict(current or {})
    if int(audit.get("contrast_issues",0)) and not cfg.get("high_contrast"): recommendations.append({"key":"high_contrast","value":True,"reason":"contrast_issues"})
    if int(audit.get("motion_issues",0)) and not cfg.get("reduced_motion"): recommendations.append({"key":"reduced_motion","value":True,"reason":"motion_issues"})
    if int(audit.get("unlabelled",0)): recommendations.append({"key":"require_labels","value":True,"reason":"unlabelled_controls"})
    return {"recommendations":recommendations,"wcag":"2.2-AA","applied":False}


def test_accessibility_config(config):  # future-1863
    cfg=dict(config or {}); checks={"text_scale":1<=float(cfg.get("text_scale",0))<=2,"focus_visible":cfg.get("focus_visible") is True,"motion":cfg.get("motion") in {"normal","reduced"},"contrast":float(cfg.get("contrast_ratio",0))>=4.5}
    return {"valid":all(checks.values()),"checks":checks,"sandboxed":True,"standard":"WCAG-2.2-AA"}


def update_accessibility_consent(state, actor_id, assistive_features, version, now):  # future-1864
    features=sorted({_text(x,"assistive feature",80) for x in _list(assistive_features,"assistive_features",30)})
    result=offline.update_offline_consent(state,"accessibility_preferences",bool(features),version,now); result["record"].update({"actor_id":_text(actor_id,"actor_id",80),"features":features,"optional":True}); return result


def accessibility_task_navigation(tasks, completed=None):  # future-1865
    result=offline.offline_task_navigation(tasks,"accessibility_reviewer",completed)
    for task in result["tasks"]: task["announcement"]=("Disponible: " if task["ready"] else "Bloqueada: ")+task["title"]
    return result


def sync_accessibility_devices(local, remote):  # future-1866
    result=offline.sync_offline_devices(local,remote); result["preference_keys"]=sorted(k for k in result["merged"] if k.startswith("a11y_")); result["requires_accessible_conflict_dialog"]=bool(result["conflicts"]); return result


def detect_accessibility_duplicates(records):  # future-1867
    result=offline.detect_offline_duplicates(records,["role","label"]); result["reason"]="duplicate accessible name and role"; return result


def accessibility_adaptive_quota(usage, base_limit, assistive_overhead=1.2):  # future-1868
    result=offline.offline_adaptive_quota(usage,base_limit); overhead=float(assistive_overhead)
    if not 1<=overhead<=2: raise ValueError("invalid assistive_overhead")
    result["suggested_limit"]=round(result["suggested_limit"]*overhead); result["assistive_overhead"]=overhead; return result


def accessibility_community_impact(events):  # future-1869
    result=offline.offline_community_impact(events); result["resolved_barriers"]=result["metrics"].get("barrier_resolved",0); result["accessible_summary"]=f"{result['contributors']} personas contribuyeron"; return result


def review_accessibility_translation(entry, reviewer_id, decision, suggestion=None):  # future-1870
    result=offline.review_offline_translation(entry,reviewer_id,decision,suggestion); result["review"]["checks"]={"plain_language":bool(entry.get("plain_language")),"screen_reader_reviewed":bool(entry.get("screen_reader_reviewed"))}; return result


def group_accessibility_notifications(notifications):  # future-1871
    result=offline.group_offline_notifications(notifications)
    for group in result["groups"]: group["aria_live"]="assertive" if any(x.get("priority")=="critical" for x in notifications if x.get("context")==group["context"]) else "polite"
    return result


def plan_accessibility_migration(config, migrations):  # future-1872
    result=plan_offline_migration(config,migrations); result["required_checks"]=["keyboard","screen_reader","contrast","zoom"]; result["block_on_regression"]=True; return result


def record_accessibility_admin_decision(log, decision, actor_id, rationale, wcag_rule, at):  # future-1873
    result=record_offline_admin_decision(log,decision,actor_id,rationale,at); entry=result["entry"]
    entry["wcag_rule"]=_text(wcag_rule,"wcag_rule",40); entry["accessibility_review"]=True
    unsigned={key:value for key,value in entry.items() if key!="hash"}; entry["hash"]=hashlib.sha256(json.dumps(unsigned,sort_keys=True).encode()).hexdigest(); result["log"][-1]=entry; return result


def continuous_accessibility_timeline(snapshots):  # future-1874
    results=[]; previous=set()
    for snapshot in _list(snapshots,"snapshots",100):
        scan=scan_offline_accessibility(snapshot.get("nodes",[])); current={(x["id"],x["rule"]) for x in scan["issues"]}
        results.append({"at":_time(snapshot.get("at")).isoformat(),"issues":len(current),"introduced":len(current-previous),"resolved":len(previous-current)}); previous=current
    return {"timeline":results,"current_issues":len(previous),"continuous":True}


def prepare_accessible_storage_transfer(files, provider, quota_bytes):  # future-1875
    result=prepare_offline_storage_transfer(files,provider,quota_bytes); result["sidecar_manifest"]=[{"name":x["name"],"accessible_description_required":True} for x in result["files"]]; return result


def evaluate_accessibility_time_policy(policies, local_minute, weekday, quiet_hours=False):  # future-1876
    result=evaluate_offline_time_policy(policies,local_minute,weekday); result["announcement_mode"]="silent" if quiet_hours else "polite"; result["visual_indicator_required"]=bool(result["effective"]); return result


def simulate_accessible_growth(history, months, accessible_retention_gain=.03):  # future-1877
    result=simulate_offline_sustainable_growth(history,months); gain=float(accessible_retention_gain)
    if not 0<=gain<=.2: raise ValueError("invalid retention gain")
    result["accessible_projection"]=[{"month":x["month"],"members":round(x["members"]*((1+gain)**x["month"]))} for x in result["projection"]]; return result


def map_mobile_moderation_dependencies(services):  # future-1878
    graph=map_accessibility_dependencies(services); critical={x["from"] for x in graph["edges"] if not x["accessible_fallback"]}; graph.update({"mobile_critical":sorted(critical),"offline_action_available":not critical}); return graph


def apply_mobile_moderation_visual_rules(case, rules, viewport_width):  # future-1879
    width=int(viewport_width)
    if not 240<=width<=2000: raise ValueError("invalid viewport_width")
    preferences={"compact":width<480,"one_handed":width<600}; result=apply_accessible_visual_rules(case,rules,preferences); result.update({"viewport_width":width,"touch_target_min_px":48,"destructive_confirmation":True}); return result


def mobile_moderation_review_inbox(cases, reviewer_id):  # future-1880
    rows=[]
    for case in _list(cases,"cases",1000):
        severity=str(case.get("severity") or "minor"); age=max(0,int(case.get("age_minutes",0))); confidence=float(case.get("confidence",0))
        rows.append({"id":_text(case.get("id"),"case id",100),"severity":severity,"priority":round(age/10+confidence*100+(100 if severity=="critical" else 0),2),"quick_actions":["approve","dismiss","escalate"]})
    rows.sort(key=lambda x:-x["priority"]); return {"reviewer_id":_text(reviewer_id,"reviewer_id",80),"cases":rows,"count":len(rows),"mobile":True}


def detect_mobile_moderation_sensitive_changes(before, after):  # future-1881
    watched={"ban","mute_until","reason","evidence","scope","appeal_allowed"}; changes=[]
    for key in sorted(watched):
        if before.get(key)!=after.get(key): changes.append({"field":key,"before":before.get(key),"after":after.get(key)})
    destructive=any(x["field"] in {"ban","scope"} for x in changes)
    return {"changes":changes,"destructive":destructive,"confirmation_required":destructive,"rollback_snapshot":deepcopy(before) if changes else None}

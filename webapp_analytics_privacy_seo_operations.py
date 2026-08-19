"""Analytics, privacy and SEO WebApp contracts for future-2162..2221."""

from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import re

import webapp_ai_accounts_creator_operations as common
import webapp_proxy_dashboard_analytics_operations as previous


def _text(v,n,limit=500):
    v=" ".join(str(v or "").split())
    if not v or len(v)>limit: raise ValueError(f"invalid {n}")
    return v


def _list(v,n,limit=2000):
    if not isinstance(v,list) or len(v)>limit: raise ValueError(f"invalid {n}")
    return v


def analytics_offline_continuity(snapshot,actions):  # future-2162
    allowed={"save_filter","annotate_chart","queue_aggregate"}; queue=[]
    for x in _list(actions,"actions",500):
        if x.get("action") not in allowed: raise ValueError("unsafe offline analytics action")
        queue.append({"id":_text(x.get("id"),"action id",100),"action":x["action"],"pending_sync":True})
    safe=previous._public_dashboard_data(snapshot)
    if isinstance(safe,dict):
        for key in list(safe):
            if re.sub(r"[^a-z0-9]","",str(key).casefold()) in {"rawrows","records","datasetrows"}: safe.pop(key)
    return {"snapshot":safe,"queue":queue,"raw_rows_cached":False,"writes":0}


def analytics_adaptive_trust(signals):  # future-2163
    r=common.evaluate_adaptive_account_trust(signals); r["aggregate_access"]=True;r["raw_export_allowed"]=r["level"]=="high";r["step_up_for_raw"]=r["level"]!="high";return r


def analytics_campaign(campaign):  # future-2164
    r=common.plan_account_community_campaign(campaign);r.update({"measurement_plan_required":True,"personal_tracking":False,"launched":False});return r


def analytics_intent(message):  # future-2165
    text=_text(message,"message",1000).casefold();ps={"trend":r"tendencia|evoluci[oó]n","compare":r"comparar|frente a","funnel":r"embudo|conversi[oó]n","privacy":r"privacidad|anonim"};scores={k:len(re.findall(p,text)) for k,p in ps.items()};intent=max(scores,key=scores.get) if max(scores.values(),default=0) else "unknown";return {"intent":intent,"scores":scores,"query_executed":False}


def analytics_integration(spec):  # future-2166
    r=common.test_account_integration(spec);fmt=str(spec.get("format","json-stat"))
    if fmt not in {"json-stat","openmetrics","csv-schema"}:raise ValueError("unsupported analytics format")
    r.update({"format":fmt,"raw_identifiers_sent":False});return r


def analytics_vault(record):  # future-2167
    r=common.store_account_personal_vault(record);r.update({"kind":"analytics_query","raw_data_stored":False,"shareable":False});return r


def analytics_easy_read(report):  # future-2168
    title=_text(report.get("title","Resumen analítico"),"title",120);metrics=[f"{_text(k,'metric',80)}: {float(v):g}." for k,v in dict(report.get("metrics",{})).items()][:8];return {"heading":title,"sentences":metrics or ["No hay datos."],"reading_level":"easy","chart_alternative":True}


def analytics_sessions(sessions,current_device):  # future-2169
    r=common.reconcile_account_sessions(sessions,current_device);r["raw_export_sessions"]=sum(x.get("raw_export") is True for x in sessions);r["reauth_for_export"]=True;return r


def analytics_editorial(dashboards,preferences):  # future-2170
    pinned=set(preferences.get("pinned",[]));rows=[{"id":_text(x.get("id"),"dashboard id",100),"score":int(x.get("use_count",0))+(100 if x.get("id") in pinned else 0),"privacy_safe":bool(x.get("aggregate_only",True))} for x in _list(dashboards,"dashboards",500)];rows.sort(key=lambda x:-x["score"]);return {"items":rows,"raw_data_included":False}


def analytics_budget(resources,budget):  # future-2171
    r=common.budget_account_resources(resources,budget);r.update({"query_budget":True,"privacy_reserve_percent":10});return r


def analytics_reputation(events):  # future-2172
    weights={"accurate":3,"reproducible":2,"privacy_violation":-10,"corrected":1};score=max(0,min(100,50+sum(weights.get(str(x.get("kind")),0) for x in events)));return {"score":score,"factors":dict(Counter(str(x.get("kind")) for x in events)),"access_automatic":False}


def analytics_localization(report,locale):  # future-2173
    r=common.localize_account_culturally(report,locale);r.update({"number_format_localized":True,"dimension_ids_unchanged":True});return r


def analytics_communication_preferences(state,channels,quiet_hours):  # future-2174
    r=common.update_account_communication_preferences(state,channels,quiet_hours);r["communication"].update({"anomaly_alerts":True,"scheduled_reports":True,"raw_data_never_notified":True});return r


def analytics_onboarding(profile,completed=None):  # future-2175
    r=common.plan_account_onboarding(profile,completed);r["analytics_steps"]=["metrics","filters","privacy","exports"];return r


def analytics_governance(proposal,votes,eligible_count):  # future-2176
    r=common.evaluate_account_governance(proposal,votes,eligible_count);r.update({"metric_definition_versioned":True,"applied":False});return r


def analytics_voice_control(transcript,confirmed=False):  # future-2177
    text=_text(transcript,"transcript",500).casefold();ps={"read_summary":r"leer resumen","compare":r"comparar periodos","export":r"exportar datos"};action=next((k for k,p in ps.items() if re.search(p,text)),None);return {"action":action,"requires_confirmation":action=="export","confirmed":bool(confirmed and action=="export"),"executed":False}


def analytics_federated_bridge(peers,fields):  # future-2178
    allowed={"aggregate","metric_definition","date_range"};selected=sorted(set(fields))
    if not set(selected)<=allowed:raise ValueError("private analytics federation field")
    r=common.plan_account_federated_bridge(peers,[]);r.update({"fields":selected,"raw_rows_federated":False,"minimum_cohort":10});return r


def analytics_external_event(event,secret,now=None):  # future-2179
    kind=str(event.get("type"));r=common.validate_account_external_event(event,secret,now=now,context=f"analytics:{kind}");r["valid"]=r["valid"] and kind in {"metric.updated","report.ready","anomaly.detected"};r.update({"event_type":kind,"query_executed":False});return r


def analytics_digital_twin(state,actions):  # future-2180
    twin=deepcopy(state);changes=[]
    for x in _list(actions,"actions",100):
        a=str(x.get("action"))
        if a=="set_filter":twin["filter"]=deepcopy(x.get("value"))
        elif a=="add_metric":twin.setdefault("metrics",[]).append(_text(x.get("metric"),"metric",80))
        elif a=="set_range":twin["range"]=_text(x.get("value"),"range",80)
        else:raise ValueError("unsupported analytics twin")
        changes.append(a)
    return {"simulation":twin,"changes":changes,"persisted":False,"query_executed":False}


def webapp_privacy_incidents(events,window_minutes=30):  # future-2181
    mapped=[{**x,"account_id":hashlib.sha256(str(x.get("data_subject","aggregate")).encode()).hexdigest()[:20]} for x in events];r=common.correlate_account_incidents(mapped,window_minutes);r["categories"]=dict(Counter(str(x.get("category")) for x in events));r["subject_ids_public"]=False;return r


def webapp_privacy_workflow(definition):  # future-2182
    r=common.build_account_workflow(definition);allowed={"identify","contain","notify","erase","export","close"}
    if any(x["action"] not in allowed for x in r["steps"]):raise ValueError("unsupported privacy workflow")
    r.update({"legal_review_required":True,"destructive_steps_require_confirmation":True});return r


def webapp_privacy_delegation(delegation,now):  # future-2183
    if delegation.get("role") not in {"privacy_viewer","privacy_officer"}:raise ValueError("invalid privacy delegation")
    r=common.delegate_account_role(delegation,now);r["data_export_access"]=delegation["role"]=="privacy_officer";r["reauth_required"]=True;return r


def webapp_privacy_coordinated_abuse(signals):  # future-2184
    mapped=[{"fingerprint":str(x.get("request_hash")),"account_id":hashlib.sha256(str(x.get("actor_id")).encode()).hexdigest()[:20]} for x in signals];r=common.detect_coordinated_account_abuse(mapped);r.update({"requests_denied":False,"raw_requests_exposed":False});return r


def webapp_privacy_copilot(context,question):  # future-2185
    safe=previous._public_dashboard_data({k:context.get(k) for k in ("policy","retention","consents","requests") if k in context});return {"question":_text(question,"question",500),"facts":safe,"suggestions":["review_consent","inspect_retention","open_request"],"legal_decision":False,"personal_data_excluded":True}


def webapp_privacy_capacity(history,months,officers):  # future-2186
    r=common.forecast_creator_capacity(history,months,officers);r["request_load"]=r.pop("editor_load");return r


def webapp_privacy_batch_plan(request_ids,action,dry_run=True):  # future-2187
    if action not in {"assign","export_preview","erase_preview","notify","close"}:raise ValueError("unsupported privacy batch")
    ids=sorted({_text(x,"request id",100) for x in _list(request_ids,"request_ids",500)});return {"action":action,"targets":ids,"dry_run":bool(dry_run),"requires_dual_confirmation":action=="erase_preview","executed":False}


def webapp_privacy_workspace(name,members,request_ids):  # future-2188
    r=common.create_account_workspace(name,members,request_ids);r["request_ids"]=r.pop("resources");r.update({"private":True,"least_privilege":True,"exports_disabled":True});return r


def webapp_privacy_media(media):  # future-2189
    r=common.index_account_media(media);r.update({"evidence_assets":True,"public":False,"metadata_minimized":True});return r


def webapp_privacy_report(metrics,locale="es"):  # future-2190
    cleaned=previous._public_dashboard_data(metrics);safe={k:v for k,v in cleaned.items() if isinstance(v,(int,float)) and not isinstance(v,bool)};r=common.narrate_account_report(safe,locale);r.update({"privacy_report":True,"personal_data_included":False});return r


def webapp_privacy_alert_escalation(alerts,rules):  # future-2191
    r=common.escalate_account_alerts(alerts,rules);r["breach_count"]=sum(x.get("kind")=="breach" for x in alerts);r.update({"sent":False,"personal_data_in_alert":False});return r


def webapp_privacy_offline_continuity(snapshot,actions):  # future-2192
    allowed={"annotate","assign_local","save_filter"};queue=[]
    for x in _list(actions,"actions",500):
        if x.get("action") not in allowed:raise ValueError("unsafe privacy offline action")
        queue.append({"id":_text(x.get("id"),"action id",100),"action":x["action"],"pending_sync":True})
    return {"snapshot":deepcopy(snapshot),"queue":queue,"exports_offline":False,"erasures_offline":False}


def webapp_privacy_adaptive_trust(signals):  # future-2193
    r=common.evaluate_adaptive_account_trust(signals);r["policy_read"]=True;r["personal_data_access"]=r["level"]=="high";r["step_up_required"]=r["level"]!="high";return r


def webapp_privacy_campaign(campaign):  # future-2194
    r=common.plan_account_community_campaign(campaign);r.update({"consent_segment_required":True,"tracking_minimized":True,"launched":False});return r


def webapp_privacy_intent(message):  # future-2195
    text=_text(message,"message",1000).casefold();ps={"access":r"acceder.*datos|copia.*datos","erase":r"borrar.*datos|eliminar.*cuenta","rectify":r"corregir.*datos","object":r"oponerme|oposici[oó]n"};scores={k:len(re.findall(p,text)) for k,p in ps.items()};intent=max(scores,key=scores.get) if max(scores.values(),default=0) else "unknown";return {"intent":intent,"scores":scores,"request_created":False}


def webapp_privacy_integration(spec):  # future-2196
    r=common.test_account_integration(spec);purpose=str(spec.get("purpose","consent"))
    if purpose not in {"consent","dsar","retention","audit"}:raise ValueError("unsupported privacy integration")
    r.update({"purpose":purpose,"personal_data_sent":False,"network_called":False});return r


def webapp_privacy_vault(record):  # future-2197
    r=common.store_account_personal_vault(record);r.update({"kind":"privacy_evidence","plaintext_stored":False,"exportable_only_after_reauth":True});return r


def webapp_privacy_easy_read(policy):  # future-2198
    title=_text(policy.get("title","Privacidad"),"title",120);purposes=[_text(x,"purpose",180) for x in policy.get("purposes",[])][:8];return {"heading":title,"sentences":[f"Usamos datos para: {x}." for x in purposes] or ["No se indican usos."],"withdrawal_visible":True,"reading_level":"easy"}


def webapp_privacy_sessions(sessions,current_device):  # future-2199
    r=common.reconcile_account_sessions(sessions,current_device);r["data_access_sessions"]=sum(x.get("data_access") is True for x in sessions);r["revoke_all_available"]=True;return r


def webapp_privacy_editorial(items,preferences):  # future-2200
    allowed=set(preferences.get("purposes",[]));rows=[]
    for x in _list(items,"items",1000):rows.append({"id":_text(x.get("id"),"item id",100),"purpose_allowed":x.get("purpose") in allowed,"retention_days":int(x.get("retention_days",0)),"personal_preview":False})
    return {"items":rows,"non_compliant":sum(not x["purpose_allowed"] for x in rows),"auto_delete":False}


def webapp_privacy_budget(resources,budget):  # future-2201
    r=common.budget_account_resources(resources,budget);r.update({"privacy_budget":True,"incident_reserve_percent":20});return r


def webapp_privacy_reputation(events):  # future-2202
    weights={"request_on_time":3,"transparent":2,"late":-3,"breach":-12};score=max(0,min(100,50+sum(weights.get(str(x.get("kind")),0) for x in events)));return {"score":score,"factors":dict(Counter(str(x.get("kind")) for x in events)),"personal_data_used":False,"access_automatic":False}


def webapp_privacy_localization(policy,locale):  # future-2203
    r=common.localize_account_culturally(policy,locale);r.update({"legal_terms_review_required":True,"rights_preserved":True});return r


def webapp_privacy_communication_preferences(state,channels,quiet_hours):  # future-2204
    r=common.update_account_communication_preferences(state,channels,quiet_hours);r["communication"].update({"breach_alerts":True,"request_updates":True,"marketing_separate":True});return r


def webapp_privacy_onboarding(profile,completed=None):  # future-2205
    r=common.plan_account_onboarding(profile,completed);r["privacy_steps"]=["consent","retention","rights","security","contact"];return r


def webapp_privacy_governance(proposal,votes,eligible_count):  # future-2206
    r=common.evaluate_account_governance(proposal,votes,eligible_count);r.update({"dpo_review_required":True,"policy_changed":False});return r


def webapp_privacy_voice_control(transcript,confirmed=False):  # future-2207
    text=_text(transcript,"transcript",500).casefold();ps={"read_policy":r"leer privacidad","download":r"descargar mis datos","erase":r"borrar mis datos"};action=next((k for k,p in ps.items() if re.search(p,text)),None);return {"action":action,"requires_confirmation":action in {"download","erase"},"confirmed":bool(confirmed and action in {"download","erase"}),"executed":False}


def webapp_privacy_federated_bridge(peers,fields):  # future-2208
    allowed={"consent_receipt","public_policy","aggregate_request_metrics"};selected=sorted(set(fields))
    if not set(selected)<=allowed:raise ValueError("personal privacy federation forbidden")
    r=common.plan_account_federated_bridge(peers,[]);r.update({"fields":selected,"personal_data_federated":False,"consent_required":True});return r


def webapp_privacy_external_event(event,secret,now=None):  # future-2209
    kind=str(event.get("type"));r=common.validate_account_external_event(event,secret,now=now,context=f"privacy:{kind}");r["valid"]=r["valid"] and kind in {"consent.changed","request.created","breach.detected"};r.update({"event_type":kind,"request_processed":False});return r


def webapp_privacy_digital_twin(state,actions):  # future-2210
    twin=deepcopy(state);changes=[]
    for x in _list(actions,"actions",100):
        a=str(x.get("action"))
        if a=="set_retention":twin["retention_days"]=max(0,int(x.get("value",0)))
        elif a=="withdraw_consent":twin.setdefault("withdrawn",[]).append(_text(x.get("purpose"),"purpose",100))
        elif a=="request_export":twin["export_pending"]=True
        else:raise ValueError("unsupported privacy twin")
        changes.append(a)
    return {"simulation":twin,"changes":changes,"persisted":False,"erasure_executed":False,"export_created":False}


def webapp_seo_incidents(events,window_minutes=60):  # future-2211
    mapped=[{**x,"account_id":str(x.get("site","web"))} for x in events];r=common.correlate_account_incidents(mapped,window_minutes);r["affected_urls"]=sorted({str(x.get("url_hash")) for x in events if x.get("url_hash")});return r


def webapp_seo_workflow(definition):  # future-2212
    r=common.build_account_workflow(definition);allowed={"crawl","audit","recommend","review","publish_metadata"}
    if any(x["action"] not in allowed for x in r["steps"]):raise ValueError("unsupported SEO workflow")
    r["metadata_publish_requires_review"]=True;return r


def webapp_seo_delegation(delegation,now):  # future-2213
    if delegation.get("role") not in {"seo_viewer","seo_editor"}:raise ValueError("invalid SEO delegation")
    r=common.delegate_account_role(delegation,now);r["content_publish_access"]=False;return r


def webapp_seo_coordinated_abuse(signals):  # future-2214
    mapped=[{"fingerprint":str(x.get("link_pattern")),"account_id":str(x.get("source_domain"))} for x in signals];r=common.detect_coordinated_account_abuse(mapped);r.update({"links_removed":False,"domains_blocked":False});return r


def webapp_seo_copilot(context,question):  # future-2215
    safe={k:context.get(k) for k in ("title","description","canonical","headings","indexable") if k in context};return {"question":_text(question,"question",500),"facts":safe,"recommendations":["review_title","check_canonical","inspect_headings"],"metadata_changed":False}


def webapp_seo_capacity(history,months,editors):  # future-2216
    r=common.forecast_creator_capacity(history,months,editors);r["audit_load"]=r.pop("editor_load");return r


def webapp_seo_batch_plan(url_ids,action,dry_run=True):  # future-2217
    if action not in {"audit","tag","request_index","review_metadata","archive_report"}:raise ValueError("unsupported SEO batch")
    ids=sorted({_text(x,"url id",100) for x in _list(url_ids,"url_ids",1000)});return {"action":action,"targets":ids,"dry_run":bool(dry_run),"metadata_changed":False,"executed":False}


def webapp_seo_workspace(name,members,url_ids):  # future-2218
    r=common.create_account_workspace(name,members,url_ids);r["url_ids"]=r.pop("resources");r["publishing_access"]=False;return r


def webapp_seo_media(media):  # future-2219
    r=common.index_account_media(media);r["alt_audit_assets"]=True;r["binary_published"]=False;return r


def webapp_seo_report(metrics,locale="es"):  # future-2220
    r=common.narrate_account_report(metrics,locale);r.update({"seo_report":True,"rank_guarantee":False,"published":False});return r


def webapp_seo_alert_escalation(alerts,rules):  # future-2221
    r=common.escalate_account_alerts(alerts,rules);r["deindex_count"]=sum(x.get("kind")=="deindexed" for x in alerts);r.update({"sent":False,"metadata_changed":False});return r

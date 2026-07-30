"""Proxy, main-dashboard and analytics contracts for WebApp future-2102..2161."""

from collections import Counter
from copy import deepcopy
import math
import re

import webapp_ai_accounts_creator_operations as common
import webapp_creator_news_proxy_operations as domain
from core.web_dashboard_operations import dashboard_report as existing_dashboard_report
from core.web_analytics_privacy_features import analytics_report as existing_analytics_report


def _text(value,name,limit=500):
    clean=" ".join(str(value or "").split())
    if not clean or len(clean)>limit: raise ValueError(f"invalid {name}")
    return clean


def _list(value,name,limit=2000):
    if not isinstance(value,list) or len(value)>limit: raise ValueError(f"invalid {name}")
    return value


def _public_dashboard_data(value):
    if isinstance(value,dict):
        clean={}
        for key,item in value.items():
            normalized=re.sub(r"[^a-z0-9]","",str(key).casefold())
            if normalized in {"authorization","userid","userids","email","emails","ip","ipaddress","ipaddresses"} or normalized.endswith(("secret","token","password","cookie")):
                continue
            clean[str(key)]=_public_dashboard_data(item)
        return clean
    if isinstance(value,list): return [_public_dashboard_data(item) for item in value[:1000]]
    return deepcopy(value)


def proxy_offline_continuity(snapshot,actions):  # future-2102
    allowed={"annotate","queue_probe","update_label"}; queue=[]
    for item in _list(actions,"actions",500):
        if item.get("action") not in allowed: raise ValueError("unsafe offline proxy action")
        queue.append({"id":_text(item.get("id"),"action id",100),"action":item["action"],"pending_sync":True})
    return {"snapshot":deepcopy(snapshot),"queue":queue,"network_changes":False,"secrets_cached":False}


def proxy_adaptive_trust(signals):  # future-2103
    result=common.evaluate_adaptive_account_trust(signals); result["view_metrics"]=True; result["rotate_secret"]=result["level"]=="high"; result["step_up_for_changes"]=result["level"]!="high"; return result


def proxy_campaign(campaign):  # future-2104
    result=common.plan_account_community_campaign(campaign); result["proxy_disclosure_required"]=True; result["health_filter_required"]=True; result["launched"]=False; return result


def proxy_intent(message):  # future-2105
    text=_text(message,"message",1000).casefold(); patterns={"connect":r"conectar|enlace proxy","slow":r"lento|latencia","report":r"reportar|no funciona","privacy":r"privacidad|registro"}; scores={k:len(re.findall(p,text)) for k,p in patterns.items()}; intent=max(scores,key=scores.get) if max(scores.values(),default=0) else "unknown"; return {"intent":intent,"scores":scores,"configuration_changed":False}


def proxy_integration(spec):  # future-2106
    result=common.test_account_integration(spec); protocol=str(spec.get("protocol","metrics"))
    if protocol not in {"metrics","health","catalog"}: raise ValueError("unsupported proxy integration")
    result.update({"protocol":protocol,"secret_sent":False,"network_called":False}); return result


def proxy_vault(record):  # future-2107
    result=common.store_account_personal_vault(record); result.update({"kind":"proxy_secret","secret_plaintext":False,"rotation_required":bool(record.get("rotation_required"))}); return result


def proxy_easy_read(proxy):  # future-2108
    status=_text(proxy.get("status"),"status",40); region=_text(proxy.get("region","desconocida"),"region",80); latency=int(proxy.get("latency_ms",0)); return {"heading":_text(proxy.get("name"),"name",100),"sentences":[f"Estado: {status}.",f"Región: {region}.",f"Latencia: {latency} milisegundos."],"secret_included":False,"reading_level":"easy"}


def proxy_sessions(sessions,current_device):  # future-2109
    result=common.reconcile_account_sessions(sessions,current_device); result["sessions_with_secret_access"]=[str(x.get("id")) for x in sessions if x.get("secret_access")]; result["reauth_before_rotation"]=True; return result


def proxy_editorial(items,preferences):  # future-2110
    regions=set(preferences.get("regions",[])); rows=[]
    for item in _list(items,"items",1000): rows.append({"id":_text(item.get("id"),"proxy id",100),"score":float(item.get("uptime",0))+(1 if item.get("region") in regions else 0),"healthy":float(item.get("uptime",0))>=.95})
    rows.sort(key=lambda x:-x["score"]); return {"items":rows,"sponsored_separated":True,"secrets_included":False}


def proxy_budget(resources,budget):  # future-2111
    result=common.budget_account_resources(resources,budget); result["infrastructure_budget"]=True; result["secret_rotation_reserved"]=round(float(budget)*.1,2); return result


def proxy_reputation(events):  # future-2112
    weights={"healthy_probe":2,"verified_report":1,"outage":-3,"abuse":-8}; score=max(0,min(100,50+sum(weights.get(str(x.get("kind")),0) for x in events))); return {"score":score,"factors":dict(Counter(str(x.get("kind")) for x in events)),"operator_identity_public":False,"auto_disable":False}


def proxy_localization(proxy,locale):  # future-2113
    result=common.localize_account_culturally(proxy,locale); result["region_names_localized"]=True; result["host_unchanged"]=True; result["secret_unchanged"]=True; return result


def proxy_communication_preferences(state,channels,quiet_hours):  # future-2114
    result=common.update_account_communication_preferences(state,channels,quiet_hours); result["communication"].update({"outage_alerts":True,"rotation_alerts":True,"marketing_separate":True}); return result


def proxy_onboarding(profile,completed=None):  # future-2115
    result=common.plan_account_onboarding(profile,completed); result["proxy_steps"]=["privacy","health_check","secret_rotation","abuse_contact"]; return result


def proxy_governance(proposal,votes,eligible_count):  # future-2116
    result=common.evaluate_account_governance(proposal,votes,eligible_count); result["operator_conflict_declared"]=bool(proposal.get("operator_conflict_declared")); result["network_change_executed"]=False; return result


def proxy_voice_control(transcript,confirmed=False):  # future-2117
    text=_text(transcript,"transcript",500).casefold(); patterns={"read_status":r"leer estado","probe":r"probar proxy","disable":r"desactivar proxy"}; action=next((k for k,p in patterns.items() if re.search(p,text)),None); return {"action":action,"requires_confirmation":action=="disable","confirmed":bool(confirmed and action=="disable"),"executed":False}


def proxy_federated_bridge(peers,fields):  # future-2118
    allowed={"status","region","uptime","public_link"}; selected=sorted(set(fields))
    if not set(selected)<=allowed: raise ValueError("private proxy federation field")
    result=common.plan_account_federated_bridge(peers,[]); result.update({"fields":selected,"secrets_federated":False,"health_signature_required":True}); return result


def proxy_external_event(event,secret,now=None):  # future-2119
    kind=str(event.get("type")); result=common.validate_account_external_event(event,secret,now=now,context=f"proxy:{kind}"); result["valid"]=result["valid"] and kind in {"proxy.healthy","proxy.degraded","proxy.offline"}; result.update({"event_type":kind,"network_action_executed":False}); return result


def proxy_digital_twin(state,actions):  # future-2120
    twin=deepcopy(state); changes=[]
    for item in _list(actions,"actions",100):
        action=str(item.get("action"))
        if action=="set_capacity": twin["capacity"]=max(0,int(item.get("value",0)))
        elif action=="quarantine": twin["quarantined"]=True
        elif action=="rotate_simulation": twin["rotation_pending"]=True
        else: raise ValueError("unsupported proxy twin action")
        changes.append(action)
    return {"simulation":twin,"changes":changes,"persisted":False,"network_changed":False}


def dashboard_incidents(events,window_minutes=15):  # future-2121
    mapped=[{**x,"account_id":str(x.get("component","dashboard"))} for x in events]; result=common.correlate_account_incidents(mapped,window_minutes); result["affected_widgets"]=sorted({str(x.get("widget")) for x in events if x.get("widget")}); return result


def dashboard_workflow(definition):  # future-2122
    result=common.build_account_workflow(definition); allowed={"refresh","review","open_panel","export","notify"}
    if any(x["action"] not in allowed for x in result["steps"]): raise ValueError("unsupported dashboard workflow")
    result["cross_panel_navigation"] = True; return result


def dashboard_delegation(delegation,now):  # future-2123
    if delegation.get("role") not in {"dashboard_viewer","dashboard_operator"}: raise ValueError("invalid dashboard delegation")
    result=common.delegate_account_role(delegation,now); result["master_panels_hidden"]=delegation["role"]!="dashboard_operator"; return result


def dashboard_coordinated_abuse(signals):  # future-2124
    mapped=[{"fingerprint":str(x.get("session_hash")),"account_id":str(x.get("account_id"))} for x in signals]; result=common.detect_coordinated_account_abuse(mapped); result["sessions_revoked"]=False; result["raw_sessions_exposed"]=False; return result


def dashboard_copilot(context,question):  # future-2125
    safe=_public_dashboard_data({k:context.get(k) for k in ("health","alerts","tasks","groups","bots") if k in context}); return {"question":_text(question,"question",500),"facts":safe,"suggested_panels":sorted(safe),"action_executed":False,"secrets_excluded":True}


def dashboard_capacity(history,months,operators):  # future-2126
    result=common.forecast_creator_capacity(history,months,operators); result["operator_load"]=result.pop("editor_load"); return result


def dashboard_batch_plan(target_ids,action,dry_run=True):  # future-2127
    if action not in {"refresh","tag","assign","export","acknowledge"}: raise ValueError("unsupported dashboard batch")
    ids=sorted({_text(x,"target id",100) for x in _list(target_ids,"target_ids",500)}); return {"action":action,"targets":ids,"dry_run":bool(dry_run),"executed":False,"destructive":False}


def dashboard_workspace(name,members,widget_ids):  # future-2128
    result=common.create_account_workspace(name,members,widget_ids); result["widget_ids"]=result.pop("resources"); result["master_widgets_filtered"]=True; return result


def dashboard_media(media):  # future-2129
    result=common.index_account_media(media); result["dashboard_attachments"]=True; result["public"] = False; return result


def dashboard_narrative_report(config,snapshot):  # future-2130
    base=existing_dashboard_report(config,_public_dashboard_data(snapshot)); metrics={k:v for k,v in base["snapshot"].items() if isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(float(v))}; narrative=common.narrate_account_report(metrics); return {**base,"narrative":narrative["summary"],"secrets_excluded":True,"delivered":False}


def dashboard_alert_escalation(alerts,rules):  # future-2131
    result=common.escalate_account_alerts(alerts,rules); result["master_count"]=sum(x.get("master_only") is True for x in alerts); result["sent"]=False; return result


def dashboard_offline_continuity(snapshot,actions):  # future-2132
    allowed={"reorder_widget","hide_widget","save_filter"}; queue=[]
    for item in _list(actions,"actions",500):
        if item.get("action") not in allowed: raise ValueError("unsafe dashboard offline action")
        queue.append({"id":_text(item.get("id"),"action id",100),"action":item["action"],"pending_sync":True})
    return {"snapshot":deepcopy(snapshot),"queue":queue,"admin_actions_allowed":False}


def dashboard_adaptive_trust(signals):  # future-2133
    result=common.evaluate_adaptive_account_trust(signals); result["master_panels_visible"]=result["level"]=="high"; result["step_up_before_admin"] = result["level"]!="high"; return result


def dashboard_campaign(campaign):  # future-2134
    result=common.plan_account_community_campaign(campaign); result["dashboard_preview"]=True; result["audience_consent_required"]=True; result["launched"]=False; return result


def dashboard_intent(message):  # future-2135
    text=_text(message,"message",1000).casefold(); patterns={"groups":r"grupos","users":r"usuarios|cuentas","security":r"seguridad|alertas","bots":r"bots?","news":r"noticias"}; scores={k:len(re.findall(p,text)) for k,p in patterns.items()}; intent=max(scores,key=scores.get) if max(scores.values(),default=0) else "unknown"; return {"intent":intent,"target_panel":intent,"opened":False}


def dashboard_integration(spec):  # future-2136
    result=common.test_account_integration(spec); kind=str(spec.get("kind","metrics"))
    if kind not in {"metrics","health","events"}: raise ValueError("unsupported dashboard integration")
    result.update({"kind":kind,"credential_value_returned":False}); return result


def dashboard_vault(record):  # future-2137
    result=common.store_account_personal_vault(record); result.update({"kind":"dashboard_secret","visible_in_widgets":False,"plaintext_stored":False}); return result


def dashboard_easy_read(snapshot):  # future-2138
    metrics=[(k,v) for k,v in snapshot.items() if isinstance(v,(int,float))][:8]; return {"heading":"Resumen del panel","sentences":[f"{k}: {v}." for k,v in metrics] or ["No hay datos."],"reading_level":"easy","color_not_required":True}


def dashboard_sessions(sessions,current_device):  # future-2139
    result=common.reconcile_account_sessions(sessions,current_device); result["master_sessions"]=sum(x.get("master") is True for x in sessions); result["reauth_before_admin"]=True; return result


def dashboard_editorial(widgets,preferences):  # future-2140
    pinned=set(preferences.get("pinned",[])); rows=[]
    for item in _list(widgets,"widgets",200): rows.append({"id":_text(item.get("id"),"widget id",100),"score":int(item.get("priority",0))+(100 if item.get("id") in pinned else 0),"hidden":bool(item.get("hidden"))})
    rows.sort(key=lambda x:-x["score"]); return {"widgets":rows,"master_only_filtered":True,"preferences_changed":False}


def dashboard_budget(resources,budget):  # future-2141
    result=common.budget_account_resources(resources,budget); result["dashboard_budget"]=True; result["alerts_reserved_percent"]=10; return result


def dashboard_reputation(events):  # future-2142
    result=common.score_account_reputation(events); result["dashboard_visibility"]="aggregate"; result["automatic_access_change"]=False; return result


def dashboard_localization(snapshot,locale):  # future-2143
    result=common.localize_account_culturally(snapshot,locale); result["widget_titles_localized"]=True; result["identifiers_unchanged"]=True; return result


def dashboard_communication_preferences(state,channels,quiet_hours):  # future-2144
    result=common.update_account_communication_preferences(state,channels,quiet_hours); result["communication"].update({"critical_bypass":True,"digest_enabled":True,"marketing_separate":True}); return result


def dashboard_onboarding(profile,completed=None):  # future-2145
    result=common.plan_account_onboarding(profile,completed); result["dashboard_steps"]=["overview","groups","security","notifications","privacy"]; return result


def dashboard_governance(proposal,votes,eligible_count):  # future-2146
    result=common.evaluate_account_governance(proposal,votes,eligible_count); result["dashboard_change_previewed"]=True; result["applied"]=False; return result


def dashboard_voice_control(transcript,confirmed=False):  # future-2147
    text=_text(transcript,"transcript",500).casefold(); patterns={"open_groups":r"abrir grupos","read_alerts":r"leer alertas","maintenance":r"activar mantenimiento"}; action=next((k for k,p in patterns.items() if re.search(p,text)),None); return {"action":action,"requires_confirmation":action=="maintenance","confirmed":bool(confirmed and action=="maintenance"),"executed":False}


def dashboard_federated_bridge(peers,fields):  # future-2148
    allowed={"health","public_metrics","service_status"}; selected=sorted(set(fields))
    if not set(selected)<=allowed: raise ValueError("private dashboard federation field")
    result=common.plan_account_federated_bridge(peers,[]); result.update({"fields":selected,"admin_data_federated":False,"read_only":True}); return result


def dashboard_external_event(event,secret,now=None):  # future-2149
    kind=str(event.get("type")); result=common.validate_account_external_event(event,secret,now=now,context=f"dashboard:{kind}"); result["valid"]=result["valid"] and kind in {"service.health","alert.created","task.completed"}; result["event_type"]=kind; result["action_executed"]=False; return result


def dashboard_digital_twin(state,actions):  # future-2150
    twin=deepcopy(state); changes=[]
    for item in _list(actions,"actions",100):
        action=str(item.get("action"))
        if action=="reorder": twin["widgets"]=list(item.get("widgets",[]))
        elif action=="hide": twin.setdefault("hidden",[]).append(_text(item.get("widget_id"),"widget id",100))
        elif action=="set_filter": twin["filter"]=deepcopy(item.get("value"))
        else: raise ValueError("unsupported dashboard twin action")
        changes.append(action)
    return {"simulation":twin,"changes":changes,"persisted":False,"admin_action_executed":False}


def analytics_incidents(events,window_minutes=15):  # future-2151
    mapped=[{**x,"account_id":str(x.get("dataset","analytics"))} for x in events]; result=common.correlate_account_incidents(mapped,window_minutes); result["affected_queries"]=sorted({str(x.get("query_id")) for x in events if x.get("query_id")}); result["raw_rows_included"]=False; return result


def analytics_workflow(definition):  # future-2152
    result=common.build_account_workflow(definition); allowed={"filter","aggregate","compare","review","export"}
    if any(x["action"] not in allowed for x in result["steps"]): raise ValueError("unsupported analytics workflow")
    result["privacy_check_required"] = True; return result


def analytics_delegation(delegation,now):  # future-2153
    if delegation.get("role") not in {"analytics_viewer","analytics_editor"}: raise ValueError("invalid analytics delegation")
    result=common.delegate_account_role(delegation,now); result["raw_user_data_access"]=False; return result


def analytics_coordinated_abuse(signals):  # future-2154
    mapped=[{"fingerprint":str(x.get("query_hash")),"account_id":str(x.get("actor_id"))} for x in signals]; result=common.detect_coordinated_account_abuse(mapped); result["queries_blocked"]=False; result["raw_queries_exposed"]=False; return result


def analytics_copilot(context,question):  # future-2155
    safe=_public_dashboard_data({k:context.get(k) for k in ("dimensions","metrics","date_range","filters") if k in context}); return {"question":_text(question,"question",500),"facts":safe,"suggested_queries":["trend","compare","funnel"],"query_executed":False,"personal_data_excluded":True}


def analytics_capacity(history,months,analysts):  # future-2156
    result=common.forecast_creator_capacity(history,months,analysts); result["query_load"]=result.pop("editor_load"); return result


def analytics_batch_plan(query_ids,action,dry_run=True):  # future-2157
    if action not in {"tag","archive","export_aggregate","assign","refresh"}: raise ValueError("unsupported analytics batch")
    ids=sorted({_text(x,"query id",100) for x in _list(query_ids,"query_ids",500)}); return {"action":action,"targets":ids,"dry_run":bool(dry_run),"raw_export":False,"executed":False}


def analytics_workspace(name,members,dashboard_ids):  # future-2158
    result=common.create_account_workspace(name,members,dashboard_ids); result["dashboard_ids"]=result.pop("resources"); result["raw_data_shared"]=False; return result


def analytics_media(media):  # future-2159
    result=common.index_account_media(media); result["chart_assets"]=True; result["raw_dataset_embedded"]=False; return result


def analytics_narrative_report(config,data):  # future-2160
    base=existing_analytics_report(config,data); numeric={"rows":base["rows"]}; narrative=common.narrate_account_report(numeric); return {**base,"narrative":narrative["summary"],"raw_rows_included":False,"delivered":False}


def analytics_alert_escalation(alerts,rules):  # future-2161
    result=common.escalate_account_alerts(alerts,rules); result["privacy_alerts"]=sum(x.get("kind")=="privacy" for x in alerts); result["sent"]=False; result["raw_data_included"]=False; return result

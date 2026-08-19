"""Creator, news and proxy WebApp contracts for future-2042..2101."""

from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import hmac
import math
import re

import webapp_ai_accounts_creator_operations as common


def _text(value,name,limit=500):
    clean=" ".join(str(value or "").split())
    if not clean or len(clean)>limit: raise ValueError(f"invalid {name}")
    return clean


def _list(value,name,limit=2000):
    if not isinstance(value,list) or len(value)>limit: raise ValueError(f"invalid {name}")
    return value


# Creator continuation -----------------------------------------------------
def creator_offline_continuity(snapshot,queued_actions):  # future-2042
    allowed={"edit_draft","comment","update_schedule","update_preferences"}; actions=[]
    for item in _list(queued_actions,"queued_actions",500):
        action=str(item.get("action"))
        if action not in allowed: raise ValueError("unsafe offline creator action")
        actions.append({"id":_text(item.get("id"),"action id",100),"action":action,"content_id":str(item.get("content_id","")),"pending_sync":True})
    return {"snapshot":deepcopy(snapshot),"queue":actions,"publish_offline":False,"destructive_actions_allowed":False}


def evaluate_creator_adaptive_trust(signals):  # future-2043
    result=common.evaluate_adaptive_account_trust(signals); result["publish_allowed"]=result["level"]=="high"; result["draft_allowed"]=True; result["step_up_action"]="reauth_before_publish" if not result["publish_allowed"] else None; return result


def plan_creator_campaign(campaign):  # future-2044
    result=common.plan_account_community_campaign(campaign); result["placements"]=sorted({_text(x,"placement",40) for x in campaign.get("placements",["webapp"])}); result["community_only"]=True; result["preview_required"]=True; return result


def detect_creator_intent(message):  # future-2045
    base=common.detect_account_intent(message); text=str(message).casefold(); creator={"publish":"publicar","schedule":"programar","campaign":"campaña","analytics":"estadíst"}; hits={k:bool(re.search(v,text)) for k,v in creator.items()}; selected=next((k for k,v in hits.items() if v),None); return {"intent":selected or base["intent"],"creator_scores":hits,"auto_action":False}


def test_creator_integration(spec):  # future-2046
    result=common.test_account_integration(spec); result["creator_scopes"]=sorted(set(spec.get("scopes",[]))&{"read_content","write_drafts","read_metrics"}); result["publish_scope_allowed"]=False; return result


def store_creator_vault(record):  # future-2047
    result=common.store_account_personal_vault(record); result["kind"]=_text(record.get("kind","draft_secret"),"kind",60); result["shareable"]=False; return result


def format_creator_easy_read(profile):  # future-2048
    result=common.format_account_easy_read(profile); result["sentences"].append("Publicar siempre necesita una revisión."); result["creator_actions"]=["Crear borrador","Revisar","Programar"]; return result


def reconcile_creator_sessions(sessions,current_device):  # future-2049
    result=common.reconcile_account_sessions(sessions,current_device); result["sessions_with_publish"]=[x["id"] for x,item in zip(result["sessions"],sorted(sessions,key=lambda x:str(x.get("last_seen")),reverse=True)) if item.get("can_publish")]; result["mass_revoke_available"]=True; return result


def curate_creator_editorial(items,preferences):  # future-2050
    result=common.curate_account_editorial(items,preferences); by_id={str(x.get("id")):x for x in items}
    for row in result["items"]: row["source_quality"]=float(by_id[row["id"]].get("source_quality",0)); row["needs_fact_check"]=row["source_quality"]<.7
    result["items"].sort(key=lambda x:(x["needs_fact_check"],-x["score"])); return result


def budget_creator_resources(resources,budget):  # future-2051
    result=common.budget_account_resources(resources,budget); result["community_spend_only"]=True; result["requires_approval"]=any(x["cost"]>float(budget)*.25 for x in result["resources"]); return result


def score_creator_reputation(events):  # future-2052
    result=common.score_account_reputation(events); result["creator_factors"]={k:v for k,v in result["factors"].items() if k in {"helpful","verified_report","warning","appeal_upheld"}}; result["reach_not_used"] = True; return result


def localize_creator_culturally(profile,locale):  # future-2053
    result=common.localize_account_culturally(profile,locale); result["content_direction"]=result["direction"]; result["translation_review_required"]=True; return result


def update_creator_communication_preferences(state,channels,quiet_hours):  # future-2054
    result=common.update_account_communication_preferences(state,channels,quiet_hours); result["communication"].update({"campaign_alerts":True,"editorial_digest":True,"audience_marketing_opt_in_required":True}); return result


def plan_creator_onboarding(profile,completed=None):  # future-2055
    result=common.plan_account_onboarding({**profile,"creator":True},completed); result["safety_steps"]=["rights","disclosures","community_rules"]; return result


def evaluate_creator_governance(proposal,votes,eligible_count):  # future-2056
    result=common.evaluate_account_governance(proposal,votes,eligible_count); result["creator_recusal_required"]=bool(proposal.get("creator_benefit")); result["published_after_close"]=False; return result


def parse_creator_voice_control(transcript,confirmed=False):  # future-2057
    text=_text(transcript,"transcript",500).casefold(); patterns={"open_drafts":r"abrir borradores","read_metrics":r"leer m[eé]tricas","schedule":r"programar publicaci[oó]n"}; action=next((k for k,p in patterns.items() if re.search(p,text)),None); return {"action":action,"understood":bool(action),"requires_confirmation":action=="schedule","confirmed":bool(confirmed and action=="schedule"),"executed":False}


def plan_creator_federated_bridge(peers,fields):  # future-2058
    allowed={"display_name","public_profile","published_content","public_metrics"}; selected=sorted(set(fields))
    if not set(selected)<=allowed: raise ValueError("private creator federation field")
    result=common.plan_account_federated_bridge(peers,["display_name"] if "display_name" in selected else []); result["fields"]=selected; result["drafts_federated"]=False; result["rights_metadata_required"]=True; return result


def validate_creator_external_event(event,secret,now=None):  # future-2059
    event_type=str(event.get("type")); allowed={"content.updated","campaign.metric","comment.created"}
    result=common.validate_account_external_event(event,secret,now=now,context=f"creator:{event_type}")
    if event_type not in allowed: result["valid"]=False
    result.update({"event_type":event_type,"creator_action_executed":False}); return result


def simulate_creator_digital_twin(state,actions):  # future-2060
    twin=deepcopy(state); changes=[]
    for action in _list(actions,"actions",100):
        kind=str(action.get("action"))
        if kind=="schedule": twin.setdefault("scheduled",[]).append(_text(action.get("content_id"),"content_id",100))
        elif kind=="set_budget": twin["budget"]=max(0,float(action.get("value",0)))
        elif kind=="pause_campaign": twin.setdefault("paused_campaigns",[]).append(_text(action.get("campaign_id"),"campaign_id",100))
        else: raise ValueError("unsupported creator twin action")
        changes.append(kind)
    return {"simulation":twin,"changes":changes,"persisted":False,"published":False}


# News --------------------------------------------------------------------
def correlate_news_incidents(events,window_minutes=30):  # future-2061
    rows=common.correlate_account_incidents([{**x,"account_id":str(x.get("source_id","unknown"))} for x in events],window_minutes); rows["affected_articles"]=sorted({str(x.get("article_id")) for x in events if x.get("article_id")}); rows["source_incidents"]=True; return rows


def build_news_workflow(definition):  # future-2062
    result=common.build_account_workflow(definition); allowed={"ingest","fact_check","edit","legal_review","publish","archive"}
    if any(x["action"] not in allowed for x in result["steps"]): raise ValueError("unsupported news workflow action")
    result.update({"fact_check_required":True,"publish_requires_approval":True}); return result


def delegate_news_role(delegation,now):  # future-2063
    if delegation.get("role") not in {"reporter","editor","fact_checker"}: raise ValueError("invalid news delegation")
    result=common.delegate_account_role(delegation,now); result["publish_permission_included"]=False; return result


def detect_coordinated_news_abuse(signals):  # future-2064
    normalized=[{"fingerprint":str(x.get("narrative_hash")),"account_id":str(x.get("source_id"))} for x in signals]; result=common.detect_coordinated_account_abuse(normalized); result["coordinated_narratives"]=result.pop("clusters"); result["articles_removed"]=False; return result


def news_context_copilot(context,question):  # future-2065
    safe={k:context.get(k) for k in ("headline","sources","timeline","claims","corrections") if k in context}; return {"question":_text(question,"question",500),"facts":safe,"suggested_checks":["verify_source","compare_claims","review_date"],"answer_published":False,"source_required":True}


def forecast_news_capacity(history,months,editors):  # future-2066
    result=common.forecast_creator_capacity(history,months,editors); result["breaking_news_reserve_percent"]=20; return result


def execute_news_batch_plan(article_ids,action,dry_run=True):  # future-2067
    if action not in {"tag","assign","schedule","archive","mark_for_review"}: raise ValueError("unsupported news batch action")
    ids=sorted({_text(x,"article id",100) for x in _list(article_ids,"article_ids",500)}); return {"action":action,"targets":ids,"dry_run":bool(dry_run),"requires_confirmation":action=="archive","executed":False}


def create_news_workspace(name,members,article_ids):  # future-2068
    result=common.create_account_workspace(name,members,article_ids); result["article_ids"]=result.pop("resources"); result["source_notes_private"]=True; return result


def index_news_media(media):  # future-2069
    result=common.index_account_media(media); result["provenance_missing"]=[row["id"] for row,item in zip(result["items"],media) if not item.get("provenance")]; result["publish_allowed"]=not result["provenance_missing"]; return result


def narrate_news_report(metrics,locale="es"):  # future-2070
    result=common.narrate_account_report(metrics,locale); result["news_sections"]=["publicados","correcciones","fuentes","alcance"]; result["claims_generated"]=False; return result


def escalate_news_alerts(alerts,rules):  # future-2071
    result=common.escalate_account_alerts(alerts,rules); result["breaking_count"]=sum(x.get("breaking") is True for x in alerts); result["auto_publish"]=False; return result


def news_offline_continuity(snapshot,queued_actions):  # future-2072
    allowed={"edit_draft","add_source","comment","fact_check"}; queue=[]
    for item in _list(queued_actions,"queued_actions",500):
        if item.get("action") not in allowed: raise ValueError("unsafe offline news action")
        queue.append({"id":_text(item.get("id"),"action id",100),"action":item["action"],"pending_sync":True})
    return {"snapshot":deepcopy(snapshot),"queue":queue,"publish_offline":False,"source_cache_encrypted":True}


def evaluate_news_adaptive_trust(signals):  # future-2073
    result=common.evaluate_adaptive_account_trust(signals); result["source_submission_allowed"]=result["level"]!="low"; result["publish_allowed"]=result["level"]=="high"; return result


def plan_news_campaign(campaign):  # future-2074
    result=common.plan_account_community_campaign(campaign); result["editorial_independence_notice"]=True; result["sponsored_disclosure_required"]=True; result["launched"]=False; return result


def detect_news_intent(message):  # future-2075
    text=_text(message,"message",2000).casefold(); patterns={"correction":r"correcci[oó]n|errata","tip":r"pista|filtraci[oó]n","source":r"fuente|documento","complaint":r"queja|reclamaci[oó]n"}; scores={k:len(re.findall(p,text)) for k,p in patterns.items()}; intent=max(scores,key=scores.get) if max(scores.values(),default=0) else "unknown"; return {"intent":intent,"scores":scores,"auto_publish":False}


def test_news_integration(spec):  # future-2076
    result=common.test_account_integration(spec); result["feed_format"]=str(spec.get("format","rss"))
    if result["feed_format"] not in {"rss","atom","jsonfeed"}: raise ValueError("unsupported news feed format")
    result["ingested"] = False; return result


def store_news_vault(record):  # future-2077
    result=common.store_account_personal_vault(record); result.update({"source_identity_encrypted":True,"editor_visibility":"need_to_know","plaintext_stored":False}); return result


def format_news_easy_read(article):  # future-2078
    title=_text(article.get("title"),"title",200); summary=_text(article.get("summary"),"summary",1000); facts=[_text(x,"fact",200) for x in article.get("facts",[])][:7]; return {"title":title,"summary":summary,"facts":facts,"reading_level":"easy","source_link_labelled":True}


def reconcile_news_sessions(sessions,current_device):  # future-2079
    result=common.reconcile_account_sessions(sessions,current_device); result["editor_sessions"]=sum(str(x.get("role"))=="editor" for x in sessions); result["publish_sessions_reauth_required"]=True; return result


def curate_news_editorial(items,policy):  # future-2080
    allowed=set(policy.get("topics",[])); rows=[]
    for item in _list(items,"items",1000):
        topics=set(item.get("topics",[])); source=float(item.get("source_score",0)); public_interest=float(item.get("public_interest",0)); rows.append({"id":_text(item.get("id"),"item id",100),"score":round(source*.6+public_interest*.4+(1 if topics&allowed else 0),3),"fact_check_required":source<.8})
    rows.sort(key=lambda x:-x["score"]); return {"items":rows,"human_editor_required":True,"sponsored_separated":True}


def budget_news_resources(resources,budget):  # future-2081
    result=common.budget_account_resources(resources,budget); result["journalism_budget"]=True; result["editorial_decisions_independent"] = True; return result


def score_news_reputation(events):  # future-2082
    weights={"accurate":4,"correction":1,"late_correction":-2,"false":-10,"transparent_source":2}; score=max(0,min(100,50+sum(weights.get(str(x.get("kind")),0) for x in events))); return {"score":score,"factors":dict(Counter(str(x.get("kind")) for x in events)),"reach_not_used":True,"removal_automatic":False}


def localize_news_culturally(article,locale):  # future-2083
    result=common.localize_account_culturally(article,locale); result["headline_review_required"]=True; result["facts_preserved"]=True; result["local_context_labelled"]=True; return result


def update_news_communication_preferences(state,channels,quiet_hours):  # future-2084
    result=common.update_account_communication_preferences(state,channels,quiet_hours); result["communication"].update({"breaking_news":True,"corrections":True,"marketing_separate":True}); return result


def plan_news_onboarding(profile,completed=None):  # future-2085
    result=common.plan_account_onboarding(profile,completed); result["editorial_steps"]=["source_policy","corrections_policy","rights","security"]; return result


def evaluate_news_governance(proposal,votes,eligible_count):  # future-2086
    result=common.evaluate_account_governance(proposal,votes,eligible_count); result["editorial_veto_requires_reason"]=True; result["conflicts_declared"]=bool(proposal.get("conflicts_declared")); return result


def parse_news_voice_control(transcript,confirmed=False):  # future-2087
    text=_text(transcript,"transcript",500).casefold(); patterns={"open_drafts":r"abrir borradores","read_headlines":r"leer titulares","publish":r"publicar noticia"}; action=next((k for k,p in patterns.items() if re.search(p,text)),None); return {"action":action,"requires_confirmation":action=="publish","confirmed":bool(confirmed and action=="publish"),"executed":False}


def plan_news_federated_bridge(peers,fields):  # future-2088
    allowed={"headline","summary","canonical_url","published_at","correction"}; selected=sorted(set(fields))
    if not set(selected)<=allowed: raise ValueError("private news federation field")
    result=common.plan_account_federated_bridge(peers,[]); result.update({"fields":selected,"drafts_federated":False,"canonical_required":True}); return result


def validate_news_external_event(event,secret,now=None):  # future-2089
    event_type=str(event.get("type")); result=common.validate_account_external_event(event,secret,now=now,context=f"news:{event_type}"); result["valid"]=result["valid"] and event_type in {"feed.updated","article.corrected","source.changed"}; result["event_type"]=event_type; result["published"]=False; return result


def simulate_news_digital_twin(state,actions):  # future-2090
    twin=deepcopy(state); changes=[]
    for item in _list(actions,"actions",100):
        action=str(item.get("action"))
        if action=="add_draft": twin.setdefault("drafts",[]).append(_text(item.get("id"),"draft id",100))
        elif action=="schedule": twin.setdefault("scheduled",[]).append(_text(item.get("id"),"article id",100))
        elif action=="correct": twin.setdefault("corrections",[]).append(_text(item.get("id"),"article id",100))
        else: raise ValueError("unsupported news twin action")
        changes.append(action)
    return {"simulation":twin,"changes":changes,"persisted":False,"published":False}


# Proxy operations ---------------------------------------------------------
def correlate_proxy_incidents(events,window_minutes=10):  # future-2091
    mapped=[{**x,"account_id":str(x.get("proxy_id","unknown"))} for x in events]; result=common.correlate_account_incidents(mapped,window_minutes); result["proxy_ids"]=sorted({str(x.get("proxy_id")) for x in events if x.get("proxy_id")}); return result


def build_proxy_workflow(definition):  # future-2092
    result=common.build_account_workflow(definition); allowed={"probe","quarantine","rotate_secret","publish","disable"}
    if any(x["action"] not in allowed for x in result["steps"]): raise ValueError("unsupported proxy workflow")
    result["destructive_steps_require_master"] = True; return result


def delegate_proxy_role(delegation,now):  # future-2093
    if delegation.get("role") not in {"proxy_viewer","proxy_operator"}: raise ValueError("invalid proxy delegation")
    result=common.delegate_account_role(delegation,now); result["secret_access"]=False; return result


def detect_coordinated_proxy_abuse(signals):  # future-2094
    mapped=[{"fingerprint":str(x.get("client_hash")),"account_id":str(x.get("proxy_id"))} for x in signals]; result=common.detect_coordinated_account_abuse(mapped); result["auto_blocked"] = False; result["raw_client_data_exposed"] = False; return result


def proxy_context_copilot(context,question):  # future-2095
    safe={k:context.get(k) for k in ("status","latency","connections","region","last_probe") if k in context}; return {"question":_text(question,"question",500),"facts":safe,"suggestions":["probe","inspect_metrics","review_rotation"],"secret_included":False,"executed":False}


def forecast_proxy_capacity(history,months,nodes):  # future-2096
    result=common.forecast_creator_capacity(history,months,nodes); result["connections_per_node"]=result.pop("editor_load"); return result


def execute_proxy_batch_plan(proxy_ids,action,dry_run=True):  # future-2097
    if action not in {"probe","quarantine","enable","disable","rotate_secret"}: raise ValueError("unsupported proxy batch action")
    ids=sorted({_text(x,"proxy id",100) for x in _list(proxy_ids,"proxy_ids",500)}); return {"action":action,"targets":ids,"dry_run":bool(dry_run),"requires_master":action in {"disable","rotate_secret"},"executed":False}


def create_proxy_workspace(name,members,proxy_ids):  # future-2098
    result=common.create_account_workspace(name,members,proxy_ids); result["proxy_ids"]=result.pop("resources"); result["secrets_visible"]=False; return result


def index_proxy_media(media):  # future-2099
    result=common.index_account_media(media); result["operational_evidence"]=True; result["public"] = False; return result


def narrate_proxy_report(metrics,locale="es"):  # future-2100
    safe={}
    for key,value in dict(metrics or {}).items():
        normalized=re.sub(r"[^a-z0-9]","",str(key).casefold())
        if normalized=="authorization" or normalized.startswith("iplist") or normalized.endswith(("secret","token","password","cookie")): continue
        number=float(value)
        if not math.isfinite(number): raise ValueError("invalid proxy metric")
        safe[key]=number
    result=common.narrate_account_report(safe,locale); result["secrets_redacted"]=True; result["proxy_summary"] = True; return result


def escalate_proxy_alerts(alerts,rules):  # future-2101
    result=common.escalate_account_alerts(alerts,rules); result["master_required"]=any(x.get("action") in {"disable","rotate_secret"} for x in alerts); result["executed"]=False; return result

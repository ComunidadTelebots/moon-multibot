"""SEO, community and support WebApp contracts for future-2222..2281."""

from collections import Counter
from copy import deepcopy
import re

import webapp_ai_accounts_creator_operations as common
from core.web_community_operations import community_report as existing_community_report
from core.web_support_subscription_features import support_report as existing_support_report


def _text(v,n,limit=500):
    v=" ".join(str(v or "").split())
    if not v or len(v)>limit:raise ValueError(f"invalid {n}")
    return v
def _list(v,n,limit=2000):
    if not isinstance(v,list) or len(v)>limit:raise ValueError(f"invalid {n}")
    return v

def webapp_seo_offline_continuity(snapshot,actions):  # future-2222
    allowed={"annotate","queue_audit","save_filter"};q=[]
    for x in _list(actions,"actions",500):
        if x.get("action") not in allowed:raise ValueError("unsafe SEO offline action")
        q.append({"id":_text(x.get("id"),"action id",100),"action":x["action"],"pending_sync":True})
    return {"snapshot":deepcopy(snapshot),"queue":q,"crawl_started":False,"metadata_changed":False}
def webapp_seo_adaptive_trust(signals):  # future-2223
    r=common.evaluate_adaptive_account_trust(signals);r["audit_allowed"]=True;r["metadata_publish_allowed"]=r["level"]=="high";return r
def webapp_seo_campaign(campaign):  # future-2224
    r=common.plan_account_community_campaign(campaign);r.update({"organic_separated":True,"sponsored_disclosure_required":True,"launched":False});return r
def webapp_seo_intent(message):  # future-2225
    t=_text(message,"message",1000).casefold();ps={"audit":r"auditar|seo","index":r"indexar|indexaci[oó]n","metadata":r"t[ií]tulo|descripci[oó]n","links":r"enlaces|backlinks"};s={k:len(re.findall(p,t)) for k,p in ps.items()};return {"intent":max(s,key=s.get) if max(s.values(),default=0) else "unknown","scores":s,"action_executed":False}
def webapp_seo_integration(spec):  # future-2226
    r=common.test_account_integration(spec);kind=str(spec.get("kind","crawler"))
    if kind not in {"crawler","search_console","sitemap"}:raise ValueError("unsupported SEO integration")
    r.update({"kind":kind,"crawl_started":False,"credentials_returned":False});return r
def webapp_seo_vault(record):  # future-2227
    r=common.store_account_personal_vault(record);r.update({"kind":"seo_credential","plaintext_stored":False,"shareable":False});return r
def webapp_seo_easy_read(report):  # future-2228
    issues=[_text(x,"issue",200) for x in report.get("issues",[])][:8];return {"heading":_text(report.get("title","Estado SEO"),"title",120),"sentences":[f"Problema: {x}." for x in issues] or ["No hay problemas."],"reading_level":"easy","technical_details_optional":True}
def webapp_seo_sessions(sessions,current_device):  # future-2229
    r=common.reconcile_account_sessions(sessions,current_device);r["publish_sessions"]=sum(x.get("metadata_publish") is True for x in sessions);r["reauth_before_publish"]=True;return r
def webapp_seo_editorial(items,preferences):  # future-2230
    priorities=set(preferences.get("priority_urls",[]));rows=[{"id":_text(x.get("id"),"url id",100),"score":int(x.get("issues",0))+(100 if x.get("id") in priorities else 0),"recommendation_only":True} for x in _list(items,"items",1000)];rows.sort(key=lambda x:-x["score"]);return {"items":rows,"metadata_changed":False}
def webapp_seo_budget(resources,budget):  # future-2231
    r=common.budget_account_resources(resources,budget);r.update({"crawl_budget":True,"accessibility_reserve_percent":10});return r
def webapp_seo_reputation(events):  # future-2232
    w={"valid_fix":3,"false_claim":-5,"spam_link":-10,"helpful_audit":2};score=max(0,min(100,50+sum(w.get(str(x.get("kind")),0) for x in events)));return {"score":score,"factors":dict(Counter(str(x.get("kind")) for x in events)),"ranking_guaranteed":False}
def webapp_seo_localization(data,locale):  # future-2233
    r=common.localize_account_culturally(data,locale);r.update({"hreflang_review_required":True,"canonical_unchanged":True});return r
def webapp_seo_communication_preferences(state,channels,quiet_hours):  # future-2234
    r=common.update_account_communication_preferences(state,channels,quiet_hours);r["communication"].update({"deindex_alerts":True,"crawl_digest":True,"marketing_separate":True});return r
def webapp_seo_onboarding(profile,completed=None):  # future-2235
    r=common.plan_account_onboarding(profile,completed);r["seo_steps"]=["site","sitemap","canonical","metadata","accessibility"];return r
def webapp_seo_governance(proposal,votes,eligible_count):  # future-2236
    r=common.evaluate_account_governance(proposal,votes,eligible_count);r.update({"metadata_preview_required":True,"applied":False});return r
def webapp_seo_voice_control(transcript,confirmed=False):  # future-2237
    t=_text(transcript,"transcript",500).casefold();ps={"read_audit":r"leer auditor[ií]a","crawl":r"iniciar rastreo","publish_metadata":r"publicar metadatos"};a=next((k for k,p in ps.items() if re.search(p,t)),None);return {"action":a,"requires_confirmation":a in {"crawl","publish_metadata"},"confirmed":bool(confirmed and a in {"crawl","publish_metadata"}),"executed":False}
def webapp_seo_federated_bridge(peers,fields):  # future-2238
    allowed={"canonical","sitemap","public_metadata","audit_summary"};sel=sorted(set(fields))
    if not set(sel)<=allowed:raise ValueError("private SEO federation field")
    r=common.plan_account_federated_bridge(peers,[]);r.update({"fields":sel,"credentials_federated":False,"read_only":True});return r
def webapp_seo_external_event(event,secret):  # future-2239
    kind=str(event.get("type"));r=common.validate_account_external_event(event,secret,context=f"seo:{kind}");r["valid"]=r["valid"] and kind in {"crawl.completed","url.deindexed","metadata.changed"};r.update({"event_type":kind,"metadata_changed":False});return r
def webapp_seo_digital_twin(state,actions):  # future-2240
    twin=deepcopy(state);changes=[]
    for x in _list(actions,"actions",100):
        a=str(x.get("action"))
        if a=="set_title":twin["title"]=_text(x.get("value"),"title",200)
        elif a=="set_description":twin["description"]=_text(x.get("value"),"description",500)
        elif a=="set_canonical":twin["canonical"]=_text(x.get("value"),"canonical",500)
        else:raise ValueError("unsupported SEO twin")
        changes.append(a)
    return {"simulation":twin,"changes":changes,"persisted":False,"published":False}

def community_incidents(events,window_minutes=15):  # future-2241
    mapped=[{**x,"account_id":str(x.get("community_id","community"))} for x in events];r=common.correlate_account_incidents(mapped,window_minutes);r["community_ids"]=sorted({str(x.get("community_id")) for x in events if x.get("community_id")});return r
def community_workflow(definition):  # future-2242
    r=common.build_account_workflow(definition);allowed={"review","invite","announce","moderate","vote"}
    if any(x["action"] not in allowed for x in r["steps"]):raise ValueError("unsupported community workflow")
    r["member_impact_previewed"]=True;return r
def community_delegation(delegation,now):  # future-2243
    if delegation.get("role") not in {"community_viewer","community_moderator"}:raise ValueError("invalid community delegation")
    r=common.delegate_account_role(delegation,now);r["owner_rights_included"]=False;return r
def community_coordinated_abuse(signals):  # future-2244
    mapped=[{"fingerprint":str(x.get("pattern_hash")),"account_id":str(x.get("actor_id"))} for x in signals];r=common.detect_coordinated_account_abuse(mapped);r.update({"members_banned":False,"human_review_required":bool(r["clusters"])});return r
def community_copilot(context,question):  # future-2245
    safe={k:context.get(k) for k in ("rules","events","announcements","proposals","metrics") if k in context};return {"question":_text(question,"question",500),"facts":safe,"suggestions":["review_rules","open_proposals","inspect_events"],"action_executed":False}
def community_capacity(history,months,moderators):  # future-2246
    r=common.forecast_creator_capacity(history,months,moderators);r["moderator_load"]=r.pop("editor_load");return r
def community_batch_plan(target_ids,action,dry_run=True):  # future-2247
    if action not in {"tag","assign","notify","request_review","archive_report"}:raise ValueError("unsupported community batch")
    return {"action":action,"targets":sorted({_text(x,"target id",100) for x in _list(target_ids,"target_ids",500)}),"dry_run":bool(dry_run),"executed":False,"member_action":False}
def community_workspace(name,members,community_ids):  # future-2248
    r=common.create_account_workspace(name,members,community_ids);r["community_ids"]=r.pop("resources");r["member_lists_hidden"]=True;return r
def community_media(media):  # future-2249
    r=common.index_account_media(media);r.update({"community_assets":True,"rights_review_required":True,"public":False});return r
def community_narrative_report(config,events):  # future-2250
    base=existing_community_report(config,events);n=common.narrate_account_report(base["counts"]);return {**base,"narrative":n["summary"],"member_ids_included":False}
def community_alert_escalation(alerts,rules):  # future-2251
    r=common.escalate_account_alerts(alerts,rules);r["safety_count"]=sum(x.get("kind")=="safety" for x in alerts);r.update({"sent":False,"member_ids_included":False});return r
def community_offline_continuity(snapshot,actions):  # future-2252
    allowed={"draft_announcement","comment","save_filter"};q=[]
    for x in _list(actions,"actions",500):
        if x.get("action") not in allowed:raise ValueError("unsafe community offline action")
        q.append({"id":_text(x.get("id"),"action id",100),"action":x["action"],"pending_sync":True})
    return {"snapshot":deepcopy(snapshot),"queue":q,"messages_sent":False,"member_actions":False}
def community_adaptive_trust(signals):  # future-2253
    r=common.evaluate_adaptive_account_trust(signals);r["read_allowed"]=True;r["moderate_allowed"]=r["level"]=="high";return r
def community_campaign_plan(campaign):  # future-2254
    r=common.plan_account_community_campaign(campaign);r.update({"community_consent_filter":True,"cross_post_preview":True,"launched":False});return r
def community_intent(message):  # future-2255
    t=_text(message,"message",1000).casefold();ps={"join":r"unirme|entrar","rules":r"reglas|normas","event":r"evento|actividad","report":r"reportar|denunciar"};s={k:len(re.findall(p,t)) for k,p in ps.items()};return {"intent":max(s,key=s.get) if max(s.values(),default=0) else "unknown","scores":s,"action_executed":False}
def community_integration(spec):  # future-2256
    r=common.test_account_integration(spec);kind=str(spec.get("kind","events"))
    if kind not in {"events","calendar","announcements"}:raise ValueError("unsupported community integration")
    r.update({"kind":kind,"member_ids_sent":False});return r
def community_vault(record):  # future-2257
    r=common.store_account_personal_vault(record);r.update({"kind":"community_secret","member_data_stored":False,"shareable":False});return r
def community_easy_read(data):  # future-2258
    name=_text(data.get("name"),"name",120);rules=[_text(x,"rule",200) for x in data.get("rules",[])][:8];return {"heading":name,"sentences":[f"Regla {i+1}: {x}." for i,x in enumerate(rules)] or ["No hay reglas."],"reading_level":"easy"}
def community_sessions(sessions,current_device):  # future-2259
    r=common.reconcile_account_sessions(sessions,current_device);r["moderator_sessions"]=sum(x.get("moderator") is True for x in sessions);r["reauth_before_moderation"]=True;return r
def community_editorial(items,preferences):  # future-2260
    topics=set(preferences.get("topics",[]));rows=[{"id":_text(x.get("id"),"item id",100),"score":len(set(x.get("topics",[]))&topics)+float(x.get("community_value",0)),"sponsored":bool(x.get("sponsored"))} for x in _list(items,"items",1000)];rows.sort(key=lambda x:(x["sponsored"],-x["score"]));return {"items":rows,"sponsored_separated":True}
def community_budget(resources,budget):  # future-2261
    r=common.budget_account_resources(resources,budget);r.update({"community_budget":True,"safety_reserve_percent":15});return r
def community_reputation(events):  # future-2262
    r=common.score_account_reputation(events);r.update({"community_context":True,"automatic_ban":False,"appeal_available":True});return r
def community_localization(data,locale):  # future-2263
    r=common.localize_account_culturally(data,locale);r.update({"rules_review_required":True,"community_name_unchanged":True});return r
def community_communication_preferences(state,channels,quiet_hours):  # future-2264
    r=common.update_account_communication_preferences(state,channels,quiet_hours);r["communication"].update({"safety_bypass":True,"events_digest":True,"marketing_separate":True});return r
def community_onboarding(profile,completed=None):  # future-2265
    r=common.plan_account_onboarding(profile,completed);r["community_steps"]=["rules","privacy","notifications","events","safety"];return r
def community_governance(proposal,votes,eligible_count):  # future-2266
    r=common.evaluate_account_governance(proposal,votes,eligible_count);r.update({"moderator_override_requires_reason":True,"applied":False});return r
def community_voice_control(transcript,confirmed=False):  # future-2267
    t=_text(transcript,"transcript",500).casefold();ps={"read_rules":r"leer reglas","open_events":r"abrir eventos","announce":r"enviar anuncio"};a=next((k for k,p in ps.items() if re.search(p,t)),None);return {"action":a,"requires_confirmation":a=="announce","confirmed":bool(confirmed and a=="announce"),"executed":False}
def community_federated_bridge(peers,fields):  # future-2268
    allowed={"public_profile","events","public_rules","announcements"};sel=sorted(set(fields))
    if not set(sel)<=allowed:raise ValueError("private community federation field")
    r=common.plan_account_federated_bridge(peers,[]);r.update({"fields":sel,"member_lists_federated":False,"read_only":True});return r
def community_external_event(event,secret):  # future-2269
    kind=str(event.get("type"));r=common.validate_account_external_event(event,secret,context=f"community:{kind}");r["valid"]=r["valid"] and kind in {"community.updated","event.created","proposal.closed"};r.update({"event_type":kind,"action_executed":False});return r
def community_digital_twin(state,actions):  # future-2270
    twin=deepcopy(state);changes=[]
    for x in _list(actions,"actions",100):
        a=str(x.get("action"))
        if a=="add_event":twin.setdefault("events",[]).append(_text(x.get("id"),"event id",100))
        elif a=="draft_announcement":twin.setdefault("drafts",[]).append(_text(x.get("text"),"text",500))
        elif a=="set_rule":twin.setdefault("rules",[]).append(_text(x.get("text"),"rule",300))
        else:raise ValueError("unsupported community twin")
        changes.append(a)
    return {"simulation":twin,"changes":changes,"persisted":False,"messages_sent":False}

def support_incidents(events,window_minutes=30):  # future-2271
    mapped=[{**x,"account_id":str(x.get("requester_hash","support"))} for x in events];r=common.correlate_account_incidents(mapped,window_minutes);r["ticket_ids"]=sorted({str(x.get("ticket_id")) for x in events if x.get("ticket_id")});r["requesters_exposed"]=False;return r
def support_workflow(definition):  # future-2272
    r=common.build_account_workflow(definition);allowed={"triage","assign","respond","escalate","resolve"}
    if any(x["action"] not in allowed for x in r["steps"]):raise ValueError("unsupported support workflow")
    r["response_requires_review"]=True;return r
def support_delegation(delegation,now):  # future-2273
    if delegation.get("role") not in {"support_viewer","support_agent"}:raise ValueError("invalid support delegation")
    r=common.delegate_account_role(delegation,now);r["sensitive_ticket_access"]=False;return r
def support_coordinated_abuse(signals):  # future-2274
    mapped=[{"fingerprint":str(x.get("message_hash")),"account_id":str(x.get("requester_hash"))} for x in signals];r=common.detect_coordinated_account_abuse(mapped);r.update({"tickets_closed":False,"requesters_exposed":False});return r
def support_copilot(context,question):  # future-2275
    safe={k:context.get(k) for k in ("category","status","history_summary","product") if k in context};return {"question":_text(question,"question",500),"facts":safe,"draft_response":None,"sent":False,"personal_data_excluded":True}
def support_capacity_forecast(history,months,agents):  # future-2276
    r=common.forecast_creator_capacity(history,months,agents);r["ticket_load"]=r.pop("editor_load");return r
def support_batch_plan(ticket_ids,action,dry_run=True):  # future-2277
    if action not in {"assign","tag","escalate","resolve_preview","export_aggregate"}:raise ValueError("unsupported support batch")
    return {"action":action,"targets":sorted({_text(x,"ticket id",100) for x in _list(ticket_ids,"ticket_ids",500)}),"dry_run":bool(dry_run),"responses_sent":False,"executed":False}
def support_workspace(name,members,ticket_ids):  # future-2278
    r=common.create_account_workspace(name,members,ticket_ids);r["ticket_ids"]=r.pop("resources");r.update({"requester_data_hidden":True,"private":True});return r
def support_media(media):  # future-2279
    r=common.index_account_media(media);r.update({"ticket_attachments":True,"malware_scan_required":True,"public":False});return r
def support_narrative_report(config,tickets):  # future-2280
    base=existing_support_report(config,tickets);n=common.narrate_account_report({"tickets":base["tickets"],"resolved":base["resolved"]});return {**base,"narrative":n["summary"],"requesters_included":False}
def support_alert_escalation(alerts,rules):  # future-2281
    r=common.escalate_account_alerts(alerts,rules);r["sla_breaches"]=sum(x.get("kind")=="sla_breach" for x in alerts);r.update({"sent":False,"requester_data_included":False});return r

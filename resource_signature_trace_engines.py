"""Cryptographic integrity signatures and end-to-end trace assembly for Moonbot."""
from resource_approval_signature_engines import _sign

IDS=tuple(f"future-{n}" for n in (4682,4685,4688,4691,4694,4697,4700,4703,4706,4709,4712,4715,4718,4721,4724,4727,4730,4733,4736,4739))
def sign_accessible_preferences(p,k,s): return _sign(IDS[0],"accessible_preferences",p,k,s)
def sign_integration_secrets(p,k,s): return _sign(IDS[1],"integration_secrets",p,k,s)
def sign_contextual_responses(p,k,s): return _sign(IDS[2],"contextual_responses",p,k,s)
def sign_miniapp_menus(p,k,s): return _sign(IDS[3],"miniapp_menus",p,k,s)
def sign_bot_statistics(p,k,s): return _sign(IDS[4],"bot_statistics",p,k,s)
def sign_ad_preferences(p,k,s): return _sign(IDS[5],"ad_preferences",p,k,s)
def sign_processing_queues(p,k,s): return _sign(IDS[6],"processing_queues",p,k,s)

def _trace(fid,resource,trace_id,events):
 if not isinstance(trace_id,str) or not trace_id or not isinstance(events,list) or len(events)>10000: raise ValueError("Traza no valida")
 timeline=[]; seen=set()
 for event in events:
  if not isinstance(event,dict) or set(event)!={"span_id","parent_id","sequence","service","status"} or not isinstance(event["span_id"],str) or not event["span_id"] or event["span_id"] in seen or (event["parent_id"] is not None and not isinstance(event["parent_id"],str)) or not isinstance(event["sequence"],int) or event["sequence"]<0 or not isinstance(event["service"],str) or not event["service"] or event["status"] not in ("started","ok","error"): raise ValueError("Evento no valido")
  seen.add(event["span_id"]); timeline.append(dict(event))
 timeline.sort(key=lambda x:(x["sequence"],x["span_id"])); known={x["span_id"] for x in timeline}; orphans=tuple(x["span_id"] for x in timeline if x["parent_id"] is not None and x["parent_id"] not in known)
 sequences={x["sequence"] for x in timeline}; gaps=tuple(x for x in range(max(sequences)+1) if x not in sequences) if sequences else ()
 return {"feature_id":fid,"resource":resource,"trace_id":trace_id,"timeline":tuple(timeline),"orphan_spans":orphans,"sequence_gaps":gaps,"complete":not orphans and not gaps,"end_to_end":True,"read_only":True,"auditable":True}
def _make_trace(i,r): return lambda t,e:_trace(IDS[i],r,t,e)
trace_creator_accounts=_make_trace(7,"creator_accounts"); trace_partner_channels=_make_trace(8,"partner_channels"); trace_community_campaigns=_make_trace(9,"community_campaigns"); trace_editorial_articles=_make_trace(10,"editorial_articles"); trace_moderated_images=_make_trace(11,"moderated_images"); trace_user_appeals=_make_trace(12,"user_appeals"); trace_mtproto_proxies=_make_trace(13,"mtproto_proxies"); trace_persistent_tasks=_make_trace(14,"persistent_tasks"); trace_moderation_rules=_make_trace(15,"moderation_rules"); trace_language_metrics=_make_trace(16,"language_metrics"); trace_community_translations=_make_trace(17,"community_translations"); trace_personal_consents=_make_trace(18,"personal_consents"); trace_telegram_reactions=_make_trace(19,"telegram_reactions")

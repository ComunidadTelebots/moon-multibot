"""Selective recovery and causal audit contracts for twenty Moonbot resources."""
import copy
IDS=tuple(f"future-{n}" for n in (3182,3185,3188,3191,3194,3197,3200,3203,3206,3209,3212,3215,3218,3221,3224,3227,3230,3233,3236,3239))
def _recover(fid,resource,current,snapshot,fields,allowed):
 if not all(isinstance(x,dict) for x in (current,snapshot)) or not isinstance(fields,list): raise ValueError("Recuperación no válida")
 changes=[]
 for field in fields:
  if field not in allowed or field not in snapshot: raise ValueError(f"Campo no recuperable: {field}")
  if current.get(field)!=snapshot[field]: changes.append({"field":field,"before":copy.deepcopy(current.get(field)),"after":copy.deepcopy(snapshot[field])})
 return {"feature_id":fid,"resource":resource,"changes":changes,"preview":True,"applied":False,"requires_confirmation":True}
def recover_accessible_preferences(c,s,f): return _recover(IDS[0],"accessible_preferences",c,s,f,{"font_scale","contrast","reduce_motion","screen_reader"})
def recover_integration_secrets(c,s,f): return _recover(IDS[1],"integration_secrets",c,s,f,{"active_version","rotated_at","scopes","enabled"})
def recover_contextual_responses(c,s,f): return _recover(IDS[2],"contextual_responses",c,s,f,{"enabled","confidence","allowed_intents","review_required"})
def recover_miniapp_menus(c,s,f): return _recover(IDS[3],"miniapp_menus",c,s,f,{"sections","role_visibility","locale","version"})
def recover_bot_statistics(c,s,f): return _recover(IDS[4],"bot_statistics",c,s,f,{"window","counters","labels","retention_days"})
def recover_ad_preferences(c,s,f): return _recover(IDS[5],"ad_preferences",c,s,f,{"personalized","categories","frequency_cap","consent_version"})
def recover_processing_queues(c,s,f): return _recover(IDS[6],"processing_queues",c,s,f,{"priority","paused","concurrency","retry_limit"})
def _causal(fid,resource,events,cause_fields,outcome_field):
 if not isinstance(events,list) or len(events)<2 or len(events)>1000: raise ValueError("Eventos insuficientes")
 normalized=[]
 for event in events:
  if not isinstance(event,dict) or outcome_field not in event or any(x not in event for x in cause_fields): raise ValueError("Evento causal incompleto")
  normalized.append({"causes":{x:event[x] for x in cause_fields},"outcome":event[outcome_field]})
 scores=[]
 for field in cause_fields:
  groups={}
  for row in normalized: groups.setdefault(str(row["causes"][field]),[]).append(float(row["outcome"]))
  means={key:sum(vals)/len(vals) for key,vals in groups.items()}; effect=max(means.values())-min(means.values()) if len(means)>1 else 0
  scores.append({"cause":field,"observed_effect":round(effect,4),"groups":len(means)})
 return {"feature_id":fid,"resource":resource,"observations":len(events),"outcome":outcome_field,"causes":sorted(scores,key=lambda x:-x["observed_effect"]),"causal_claim":False,"explanation":"Asociación observada; requiere revisión para inferir causalidad."}
def audit_creator_accounts(e): return _causal(IDS[7],"creator_accounts",e,("verification","role_change"),"active")
def audit_associated_channels(e): return _causal(IDS[8],"associated_channels",e,("bot_permission","posting_mode"),"delivery_ratio")
def audit_community_campaigns(e): return _causal(IDS[9],"community_campaigns",e,("placement","schedule"),"click_ratio")
def audit_editorial_articles(e): return _causal(IDS[10],"editorial_articles",e,("category","reviewed"),"reading_seconds")
def audit_moderated_images(e): return _causal(IDS[11],"moderated_images",e,("scanner","threshold"),"false_positive")
def audit_user_appeals(e): return _causal(IDS[12],"user_appeals",e,("reason","reviewer_role"),"approved")
def audit_mtproto_proxies(e): return _causal(IDS[13],"mtproto_proxies",e,("region","transport"),"latency_ms")
def audit_persistent_tasks(e): return _causal(IDS[14],"persistent_tasks",e,("priority","has_deadline"),"completion_hours")
def audit_moderation_rules(e): return _causal(IDS[15],"moderation_rules",e,("rule_type","action"),"appealed")
def audit_language_metrics(e): return _causal(IDS[16],"language_metrics",e,("detector","script"),"confidence")
def audit_community_translations(e): return _causal(IDS[17],"community_translations",e,("locale","review_count"),"accepted")
def audit_personal_consents(e): return _causal(IDS[18],"personal_consents",e,("purpose","prompt_version"),"granted")
def audit_telegram_reactions(e): return _causal(IDS[19],"telegram_reactions",e,("reaction","message_type"),"retained")

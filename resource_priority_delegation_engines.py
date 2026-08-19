"""Adaptive priorities and temporary delegation grants for Moonbot resources."""
import datetime as dt, re
IDS=tuple(f"future-{n}" for n in (3362,3365,3368,3371,3374,3377,3380,3383,3386,3389,3392,3395,3398,3401,3404,3407,3410,3413,3416,3419))
def _priority(fid,resource,item,weights):
 if not isinstance(item,dict): raise ValueError("Elemento requerido")
 parts=[]; total=0
 for field,weight in weights.items(): value=float(item.get(field,0)); contribution=value*weight; total+=contribution; parts.append({"field":field,"value":value,"weight":weight,"contribution":round(contribution,3)})
 return {"feature_id":fid,"resource":resource,"priority":round(max(0,min(total,100)),2),"components":parts,"automatic_action":False}
def prioritize_editorial_article(x): return _priority(IDS[0],"editorial_articles",x,{"age_hours":.3,"editorial_risk":.5,"scheduled":-20})
def prioritize_moderated_image(x): return _priority(IDS[1],"moderated_images",x,{"risk_score":.7,"reports":8,"review_age":.2})
def prioritize_user_appeal(x): return _priority(IDS[2],"user_appeals",x,{"wait_hours":.5,"sanction_severity":15,"evidence_count":-1})
def prioritize_mtproto_proxy(x): return _priority(IDS[3],"mtproto_proxies",x,{"failure_ratio":50,"latency_ms":.02,"users":.1})
def prioritize_persistent_task(x): return _priority(IDS[4],"persistent_tasks",x,{"overdue_hours":.4,"business_value":8,"blocked_dependents":5})
def prioritize_moderation_rule(x): return _priority(IDS[5],"moderation_rules",x,{"false_positive_ratio":50,"matches":.1,"appeals":7})
def prioritize_language_metric(x): return _priority(IDS[6],"language_metrics",x,{"unknown_ratio":60,"sample_count":.01,"confidence":-20})
def prioritize_community_translation(x): return _priority(IDS[7],"community_translations",x,{"missing_users":.1,"review_age":.4,"reviewers":-3})
def prioritize_personal_consent(x): return _priority(IDS[8],"personal_consents",x,{"days_to_expiry":-1,"data_sensitivity":15,"scope_count":3})
def prioritize_telegram_reaction(x): return _priority(IDS[9],"telegram_reactions",x,{"reports":10,"velocity":.2,"age_hours":-.1})
def prioritize_master_panel(x): return _priority(IDS[10],"master_panels",x,{"errors":8,"blocked_actions":10,"stale_minutes":.1})
def prioritize_channel_directory(x): return _priority(IDS[11],"channel_directories",x,{"stale_days":1,"reports":9,"subscriber_change":.1})
def prioritize_external_link(x): return _priority(IDS[12],"external_links",x,{"risk_score":.7,"redirects":6,"clicks":.02})
def _delegate(fid,resource,grant_id,actor_id,delegate_id,scopes,allowed,expires_at,now):
 if not re.fullmatch(r"[\w-]{2,80}",str(grant_id)) or actor_id==delegate_id: raise ValueError("Delegación no válida")
 scopes=list(dict.fromkeys(str(x) for x in scopes))
 if not scopes or any(x not in allowed for x in scopes): raise ValueError("Ámbito no permitido")
 start=dt.datetime.fromisoformat(str(now)); end=dt.datetime.fromisoformat(str(expires_at))
 if start.tzinfo is None or end.tzinfo is None or not start<end<=start+dt.timedelta(days=30): raise ValueError("Expiración no válida")
 return {"feature_id":fid,"resource":resource,"id":str(grant_id),"delegated_by":str(actor_id),"delegate_id":str(delegate_id),"scopes":scopes,"starts_at":start.isoformat(),"expires_at":end.isoformat(),"revocable":True,"active":True}
def delegate_admin_session(**x): return _delegate(IDS[13],"admin_sessions",allowed={"view","terminate","require_mfa"},**x)
def delegate_community_profile(**x): return _delegate(IDS[14],"community_profiles",allowed={"view","review","hide_fields"},**x)
def delegate_telegram_community(**x): return _delegate(IDS[15],"telegram_communities",allowed={"view","sync","review_membership"},**x)
def delegate_house_ad(**x): return _delegate(IDS[16],"house_ads",allowed={"view","edit_draft","request_approval"},**x)
def delegate_voice_note(**x): return _delegate(IDS[17],"voice_notes",allowed={"view_metadata","request_transcription","review"},**x)
def delegate_suspicious_file(**x): return _delegate(IDS[18],"suspicious_files",allowed={"view_hash","request_scan","review_verdict"},**x)
def delegate_captcha_decision(**x): return _delegate(IDS[19],"captcha_decisions",allowed={"view","review_appeal","request_evidence"},**x)

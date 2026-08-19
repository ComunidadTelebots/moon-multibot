"""Auditable revocable-retention and granular-consent policies for Moonbot."""
from datetime import datetime, timezone

IDS=tuple(f"future-{n}" for n in (3602,3605,3608,3611,3614,3617,3620,3623,3626,3629,3632,3635,3638,3641,3644,3647,3650,3653,3656,3659))

def _retention(fid,resource,subject_id,days,reason,revoked=False,legal_hold=False):
 if not isinstance(subject_id,str) or not subject_id.strip(): raise ValueError("Sujeto no valido")
 if not isinstance(days,int) or not 1<=days<=3650: raise ValueError("Retencion no valida")
 if not isinstance(reason,str) or not reason.strip() or len(reason)>240: raise ValueError("Motivo no valido")
 effective=bool(not revoked or legal_hold)
 return {"feature_id":fid,"resource":resource,"subject_id":subject_id,"retention_days":days,"reason":reason,"revoked":bool(revoked),"legal_hold":bool(legal_hold),"effective":effective,"action":("retain" if effective else "purge"),"auditable":True}

def retain_temporary_roles(s,d,r,revoked=False,legal_hold=False): return _retention(IDS[0],"temporary_roles",s,d,r,revoked,legal_hold)
def retain_managed_groups(s,d,r,revoked=False,legal_hold=False): return _retention(IDS[1],"managed_groups",s,d,r,revoked,legal_hold)
def retain_scheduled_messages(s,d,r,revoked=False,legal_hold=False): return _retention(IDS[2],"scheduled_messages",s,d,r,revoked,legal_hold)
def retain_rss_feeds(s,d,r,revoked=False,legal_hold=False): return _retention(IDS[3],"rss_feeds",s,d,r,revoked,legal_hold)
def retain_telegram_videos(s,d,r,revoked=False,legal_hold=False): return _retention(IDS[4],"telegram_videos",s,d,r,revoked,legal_hold)
def retain_blocklists(s,d,r,revoked=False,legal_hold=False): return _retention(IDS[5],"blocklists",s,d,r,revoked,legal_hold)
def retain_required_subscriptions(s,d,r,revoked=False,legal_hold=False): return _retention(IDS[6],"required_subscriptions",s,d,r,revoked,legal_hold)
def retain_signed_webhooks(s,d,r,revoked=False,legal_hold=False): return _retention(IDS[7],"signed_webhooks",s,d,r,revoked,legal_hold)
def retain_quiet_hours(s,d,r,revoked=False,legal_hold=False): return _retention(IDS[8],"quiet_hours",s,d,r,revoked,legal_hold)
def retain_correlated_incidents(s,d,r,revoked=False,legal_hold=False): return _retention(IDS[9],"correlated_incidents",s,d,r,revoked,legal_hold)
def retain_accessible_preferences(s,d,r,revoked=False,legal_hold=False): return _retention(IDS[10],"accessible_preferences",s,d,r,revoked,legal_hold)
def retain_integration_secrets(s,d,r,revoked=False,legal_hold=False): return _retention(IDS[11],"integration_secrets",s,d,r,revoked,legal_hold)
def retain_contextual_responses(s,d,r,revoked=False,legal_hold=False): return _retention(IDS[12],"contextual_responses",s,d,r,revoked,legal_hold)
def retain_miniapp_menus(s,d,r,revoked=False,legal_hold=False): return _retention(IDS[13],"miniapp_menus",s,d,r,revoked,legal_hold)
def retain_bot_statistics(s,d,r,revoked=False,legal_hold=False): return _retention(IDS[14],"bot_statistics",s,d,r,revoked,legal_hold)
def retain_ad_preferences(s,d,r,revoked=False,legal_hold=False): return _retention(IDS[15],"ad_preferences",s,d,r,revoked,legal_hold)
def retain_processing_queues(s,d,r,revoked=False,legal_hold=False): return _retention(IDS[16],"processing_queues",s,d,r,revoked,legal_hold)

def _consent(fid,resource,subject_id,scopes,granted,policy_version):
 allowed={"read","write","publish","analytics","moderation","advertising"}
 if not isinstance(subject_id,str) or not subject_id.strip(): raise ValueError("Sujeto no valido")
 if not isinstance(scopes,(list,tuple,set)) or not scopes: raise ValueError("Ambitos no validos")
 normalized=tuple(sorted(set(scopes)))
 if any(not isinstance(x,str) or x not in allowed for x in normalized): raise ValueError("Ambito desconocido")
 if not isinstance(granted,bool) or not isinstance(policy_version,str) or not policy_version.strip(): raise ValueError("Consentimiento no valido")
 return {"feature_id":fid,"resource":resource,"subject_id":subject_id,"scopes":normalized,"granted":granted,"policy_version":policy_version,"decision":("allow" if granted else "deny"),"recorded_at":datetime.now(timezone.utc).isoformat(),"auditable":True}

def consent_creator_accounts(s,scopes,granted,version): return _consent(IDS[17],"creator_accounts",s,scopes,granted,version)
def consent_partner_channels(s,scopes,granted,version): return _consent(IDS[18],"partner_channels",s,scopes,granted,version)
def consent_community_campaigns(s,scopes,granted,version): return _consent(IDS[19],"community_campaigns",s,scopes,granted,version)

"""End-to-end traces and bounded dynamic quota decisions for Moonbot."""
from resource_signature_trace_engines import _trace

IDS=tuple(f"future-{n}" for n in (4742,4745,4748,4751,4754,4757,4760,4763,4766,4769,4772,4775,4778,4781,4784,4787,4790,4793,4796,4799))
def trace_master_panels(t,e): return _trace(IDS[0],"master_panels",t,e)
def trace_channel_directories(t,e): return _trace(IDS[1],"channel_directories",t,e)
def trace_external_links(t,e): return _trace(IDS[2],"external_links",t,e)

def _quota(fid,resource,base,minimum,maximum,load_ratio,used):
 vals=(base,minimum,maximum,used)
 if any(not isinstance(x,int) or isinstance(x,bool) or x<0 for x in vals) or not minimum<=base<=maximum or not isinstance(load_ratio,(int,float)) or isinstance(load_ratio,bool) or not 0<=load_ratio<=2: raise ValueError("Cuota no valida")
 factor=1.25 if load_ratio<.5 else (.75 if load_ratio>1 else 1.0); limit=max(minimum,min(maximum,int(base*factor))); remaining=max(0,limit-used)
 return {"feature_id":fid,"resource":resource,"base":base,"limit":limit,"used":used,"remaining":remaining,"exceeded":used>=limit,"load_ratio":float(load_ratio),"dynamic":True,"applied":False,"auditable":True}
def _make_quota(i,r): return lambda b,n,x,l,u:_quota(IDS[i],r,b,n,x,l,u)
quota_admin_sessions=_make_quota(3,"admin_sessions"); quota_community_profiles=_make_quota(4,"community_profiles"); quota_telegram_communities=_make_quota(5,"telegram_communities"); quota_house_ads=_make_quota(6,"house_ads"); quota_voice_notes=_make_quota(7,"voice_notes"); quota_suspicious_files=_make_quota(8,"suspicious_files"); quota_captcha_decisions=_make_quota(9,"captcha_decisions"); quota_managed_bots=_make_quota(10,"managed_bots"); quota_recurring_reminders=_make_quota(11,"recurring_reminders"); quota_security_events=_make_quota(12,"security_events"); quota_regional_maps=_make_quota(13,"regional_maps"); quota_backups=_make_quota(14,"backups"); quota_ai_learning_data=_make_quota(15,"ai_learning_data"); quota_rich_commands=_make_quota(16,"rich_commands"); quota_hub_notifications=_make_quota(17,"hub_notifications"); quota_cookie_policies=_make_quota(18,"cookie_policies"); quota_wayback_history=_make_quota(19,"wayback_history")

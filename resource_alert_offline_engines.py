"""Escalation decisions and bounded offline queues for Moonbot resources."""
IDS=tuple(f"future-{n}" for n in (3902,3905,3908,3911,3914,3917,3920,3923,3926,3929,3932,3935,3938,3941,3944,3947,3950,3953,3956,3959))

def _alert(fid,resource,event_id,severity,attempts,age_minutes):
 levels=("info","warning","critical")
 if not isinstance(event_id,str) or not event_id.strip() or severity not in levels: raise ValueError("Alerta no valida")
 if not isinstance(attempts,int) or attempts<0 or not isinstance(age_minutes,(int,float)) or age_minutes<0: raise ValueError("Escalado no valido")
 base=levels.index(severity); step=(1 if attempts>=3 or age_minutes>=30 else 0)+(1 if attempts>=8 or age_minutes>=120 else 0)
 final=levels[min(2,base+step)]; route={"info":"log","warning":"operator","critical":"on_call"}[final]
 return {"feature_id":fid,"resource":resource,"event_id":event_id,"original_severity":severity,"severity":final,"route":route,"escalated":final!=severity,"delivery_requested":False,"auditable":True}

def _make_alert(i,resource): return lambda e,s,a,m:_alert(IDS[i],resource,e,s,a,m)
alert_temporary_roles=_make_alert(0,"temporary_roles"); alert_managed_groups=_make_alert(1,"managed_groups"); alert_scheduled_messages=_make_alert(2,"scheduled_messages")
alert_rss_feeds=_make_alert(3,"rss_feeds"); alert_telegram_videos=_make_alert(4,"telegram_videos"); alert_blocklists=_make_alert(5,"blocklists")
alert_required_subscriptions=_make_alert(6,"required_subscriptions"); alert_signed_webhooks=_make_alert(7,"signed_webhooks"); alert_quiet_hours=_make_alert(8,"quiet_hours")
alert_correlated_incidents=_make_alert(9,"correlated_incidents"); alert_accessible_preferences=_make_alert(10,"accessible_preferences"); alert_integration_secrets=_make_alert(11,"integration_secrets")
alert_contextual_responses=_make_alert(12,"contextual_responses"); alert_miniapp_menus=_make_alert(13,"miniapp_menus"); alert_bot_statistics=_make_alert(14,"bot_statistics")
alert_ad_preferences=_make_alert(15,"ad_preferences"); alert_processing_queues=_make_alert(16,"processing_queues")

def _offline(fid,resource,operations,max_items=1000):
 if not isinstance(operations,list) or len(operations)>max_items: raise ValueError("Cola no valida")
 seen=set(); queued=[]
 for op in operations:
  if not isinstance(op,dict) or set(op)!={"id","action","payload"} or not isinstance(op["id"],str) or not op["id"] or op["action"] not in ("create","update","delete") or not isinstance(op["payload"],dict): raise ValueError("Operacion no valida")
  if op["id"] in seen: continue
  seen.add(op["id"]); queued.append({"id":op["id"],"action":op["action"],"payload":op["payload"]})
 return {"feature_id":fid,"resource":resource,"queued":tuple(queued),"queue_count":len(queued),"deduplicated":len(operations)-len(queued),"offline":True,"applied":False,"auditable":True}

def offline_creator_accounts(o,max_items=1000): return _offline(IDS[17],"creator_accounts",o,max_items)
def offline_partner_channels(o,max_items=1000): return _offline(IDS[18],"partner_channels",o,max_items)
def offline_community_campaigns(o,max_items=1000): return _offline(IDS[19],"community_campaigns",o,max_items)

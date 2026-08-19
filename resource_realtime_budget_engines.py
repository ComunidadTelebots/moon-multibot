"""Real-time dashboard snapshots and budget guardrails for Moonbot."""
from datetime import datetime, timezone

IDS=tuple(f"future-{n}" for n in (4202,4205,4208,4211,4214,4217,4220,4223,4226,4229,4232,4235,4238,4241,4244,4247,4250,4253,4256,4259))

def _panel(fid,resource,sequence,metrics):
 if not isinstance(sequence,int) or sequence<0 or not isinstance(metrics,dict) or len(metrics)>50: raise ValueError("Snapshot no valido")
 clean={}
 for key,value in metrics.items():
  if not isinstance(key,str) or not key or len(key)>80 or not isinstance(value,(int,float)) or isinstance(value,bool): raise ValueError("Metrica no valida")
  clean[key]=value
 return {"feature_id":fid,"resource":resource,"sequence":sequence,"metrics":dict(sorted(clean.items())),"generated_at":datetime.now(timezone.utc).isoformat(),"realtime":True,"snapshot_only":True,"subscribed":False,"auditable":True}

def _make_panel(i,r): return lambda s,m:_panel(IDS[i],r,s,m)
panel_temporary_roles=_make_panel(0,"temporary_roles"); panel_managed_groups=_make_panel(1,"managed_groups"); panel_scheduled_messages=_make_panel(2,"scheduled_messages")
panel_rss_feeds=_make_panel(3,"rss_feeds"); panel_telegram_videos=_make_panel(4,"telegram_videos"); panel_blocklists=_make_panel(5,"blocklists")
panel_required_subscriptions=_make_panel(6,"required_subscriptions"); panel_signed_webhooks=_make_panel(7,"signed_webhooks"); panel_quiet_hours=_make_panel(8,"quiet_hours")
panel_correlated_incidents=_make_panel(9,"correlated_incidents"); panel_accessible_preferences=_make_panel(10,"accessible_preferences"); panel_integration_secrets=_make_panel(11,"integration_secrets")
panel_contextual_responses=_make_panel(12,"contextual_responses"); panel_miniapp_menus=_make_panel(13,"miniapp_menus"); panel_bot_statistics=_make_panel(14,"bot_statistics")
panel_ad_preferences=_make_panel(15,"ad_preferences"); panel_processing_queues=_make_panel(16,"processing_queues")

def _budget(fid,resource,budget,spent,requested,currency):
 values=(budget,spent,requested)
 if any(not isinstance(x,(int,float)) or isinstance(x,bool) or x<0 for x in values) or not isinstance(currency,str) or len(currency)!=3 or not currency.isalpha(): raise ValueError("Presupuesto no valido")
 remaining=max(0.0,float(budget)-float(spent)); allowed=float(requested)<=remaining
 return {"feature_id":fid,"resource":resource,"currency":currency.upper(),"budget":round(float(budget),2),"spent":round(float(spent),2),"requested":round(float(requested),2),"remaining":round(remaining,2),"allowed":allowed,"decision":("approve" if allowed else "deny"),"applied":False,"auditable":True}

def budget_creator_accounts(b,s,r,c): return _budget(IDS[17],"creator_accounts",b,s,r,c)
def budget_partner_channels(b,s,r,c): return _budget(IDS[18],"partner_channels",b,s,r,c)
def budget_community_campaigns(b,s,r,c): return _budget(IDS[19],"community_campaigns",b,s,r,c)

"""Federated dry-runs and explicit conflict-reconciliation plans for Moonbot."""
from resource_budget_federation_engines import _federate

IDS=tuple(f"future-{n}" for n in (4322,4325,4328,4331,4334,4337,4340,4343,4346,4349,4352,4355,4358,4361,4364,4367,4370,4373,4376,4379))

def federate_managed_bots(c,n): return _federate(IDS[0],"managed_bots",c,n)
def federate_recurring_reminders(c,n): return _federate(IDS[1],"recurring_reminders",c,n)
def federate_security_events(c,n): return _federate(IDS[2],"security_events",c,n)
def federate_regional_maps(c,n): return _federate(IDS[3],"regional_maps",c,n)
def federate_backups(c,n): return _federate(IDS[4],"backups",c,n)
def federate_ai_learning_data(c,n): return _federate(IDS[5],"ai_learning_data",c,n)
def federate_rich_commands(c,n): return _federate(IDS[6],"rich_commands",c,n)
def federate_hub_notifications(c,n): return _federate(IDS[7],"hub_notifications",c,n)
def federate_cookie_policies(c,n): return _federate(IDS[8],"cookie_policies",c,n)
def federate_wayback_history(c,n): return _federate(IDS[9],"wayback_history",c,n)

def _reconcile(fid,resource,conflicts,strategy,node_priority=(),manual=None):
 if strategy not in ("newest","node_priority","manual") or not isinstance(conflicts,list) or len(conflicts)>5000: raise ValueError("Reconciliacion no valida")
 priority={node:i for i,node in enumerate(node_priority)}
 if strategy=="node_priority" and (not priority or len(priority)!=len(tuple(node_priority))): raise ValueError("Prioridad no valida")
 if strategy=="manual" and not isinstance(manual,dict): raise ValueError("Seleccion manual requerida")
 resolved=[]; unresolved=[]
 for conflict in conflicts:
  if not isinstance(conflict,dict) or set(conflict)!={"entity_id","candidates"} or not isinstance(conflict["candidates"],list) or len(conflict["candidates"])<2: raise ValueError("Conflicto no valido")
  candidates=conflict["candidates"]
  if any(not isinstance(x,dict) or set(x)!={"node","revision","payload"} or not isinstance(x["node"],str) or not isinstance(x["revision"],int) or not isinstance(x["payload"],dict) for x in candidates): raise ValueError("Candidato no valido")
  chosen=None
  if strategy=="newest":
   top=max(x["revision"] for x in candidates); leaders=[x for x in candidates if x["revision"]==top]
   if len(leaders)==1: chosen=leaders[0]
  elif strategy=="node_priority": chosen=min((x for x in candidates if x["node"] in priority),key=lambda x:priority[x["node"]],default=None)
  else:
   node=manual.get(str(conflict["entity_id"])); chosen=next((x for x in candidates if x["node"]==node),None)
  if chosen is None: unresolved.append(str(conflict["entity_id"]))
  else: resolved.append({"entity_id":str(conflict["entity_id"]),"node":chosen["node"],"revision":chosen["revision"],"payload":chosen["payload"]})
 return {"feature_id":fid,"resource":resource,"strategy":strategy,"resolved":tuple(resolved),"unresolved":tuple(unresolved),"ready":not unresolved,"dry_run":True,"applied":False,"auditable":True}

def _make_reconcile(i,r): return lambda c,s,node_priority=(),manual=None:_reconcile(IDS[i],r,c,s,node_priority,manual)
reconcile_temporary_roles=_make_reconcile(10,"temporary_roles"); reconcile_managed_groups=_make_reconcile(11,"managed_groups"); reconcile_scheduled_messages=_make_reconcile(12,"scheduled_messages")
reconcile_rss_feeds=_make_reconcile(13,"rss_feeds"); reconcile_telegram_videos=_make_reconcile(14,"telegram_videos"); reconcile_blocklists=_make_reconcile(15,"blocklists")
reconcile_required_subscriptions=_make_reconcile(16,"required_subscriptions"); reconcile_signed_webhooks=_make_reconcile(17,"signed_webhooks"); reconcile_quiet_hours=_make_reconcile(18,"quiet_hours")
reconcile_correlated_incidents=_make_reconcile(19,"correlated_incidents")

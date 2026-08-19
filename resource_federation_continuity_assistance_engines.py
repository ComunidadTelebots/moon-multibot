"""Final roadmap engines: federation, continuity and contextual assistance."""
from collections import defaultdict
import hashlib,json
from resource_security_contracts import authorize,bounded_json,safe_identifier
from resource_incident_temporal_engines import _utc_datetime
from resource_energy_abuse_migration_federation_engines import _federation
IDS=tuple(f"future-{n}" for n in range(5882,6000,3))
FED=("accessible_preferences","integration_secrets","contextual_responses","miniapp_menus","bot_statistics","advertising_preferences","processing_queues")
CONT=("creator_accounts","associated_channels","community_campaigns","editorial_articles","moderated_images","user_appeals","mtproto_proxies","persistent_tasks","moderation_rules","language_metrics","community_translations","personal_consents","telegram_reactions","master_panels","channel_directories","external_links")
ASSIST=("administrative_sessions","community_profiles","telegram_communities","house_ads","voice_notes","suspicious_files","captcha_decisions","managed_bots","recurring_reminders","security_events","regional_maps","backups","ai_learning_data","rich_commands","hub_notifications","cookie_policies","wayback_history")
def _continuity(fid,res,services,actor,rto_minutes=60,rpo_minutes=15):
 aid=authorize(actor,f"continuity:plan:{res}");bounded_json(services,maximum_bytes=262144,reject_secrets=True)
 if not isinstance(services,list) or len(services)>1000 or any(isinstance(x,bool) or not isinstance(x,int) or x<1 or x>10080 for x in (rto_minutes,rpo_minutes)):raise ValueError("continuity request invalid")
 known=set();rows=[]
 for s in services:
  if not isinstance(s,dict):raise ValueError("service invalid")
  sid=safe_identifier(s.get("service_id"),"service_id"); deps=s.get("dependencies",[])
  if sid in known or not isinstance(deps,list) or len(deps)>100:raise ValueError("service/dependencies invalid")
  known.add(sid);rows.append((sid,tuple(safe_identifier(x,"dependency") for x in deps),bool(s.get("backup_available")),bool(s.get("fallback_available"))))
 missing=tuple(sorted({d for _,ds,_,_ in rows for d in ds if d not in known}));g={x:tuple(d for d in ds if d in known) for x,ds,_,_ in rows}
 indegree={x:len(set(ds)) for x,ds in g.items()};dependents=defaultdict(list)
 for node,deps in g.items():
  for dep in set(deps):dependents[dep].append(node)
 queue=[x for x,n in indegree.items() if n==0];processed=0
 while queue:
  node=queue.pop();processed+=1
  for dependent in dependents[node]:
   indegree[dependent]-=1
   if indegree[dependent]==0:queue.append(dependent)
 cyclic=processed<len(g)
 gaps=tuple(x for x,_,backup,fallback in rows if not backup or not fallback)
 return {"feature_id":fid,"resource":res,"planned_by":aid,"rto_minutes":rto_minutes,"rpo_minutes":rpo_minutes,"service_count":len(rows),"missing_dependencies":missing,"cyclic_dependencies":cyclic,"resilience_gaps":gaps,"ready":not missing and not cyclic and not gaps,"failover_executed":False,"executed":False,"auditable":True}
def _assist(fid,res,context,actor):
 aid=authorize(actor,f"assistance:read:{res}");bounded_json(context,maximum_bytes=65536,reject_secrets=True)
 if not isinstance(context,dict):raise ValueError("context invalid")
 cid=safe_identifier(context.get("context_id"),"context_id");state=context.get("state");severity=context.get("severity","info")
 if state not in {"empty","draft","pending","active","failed","completed","revoked"} or severity not in {"info","warning","critical"}:raise ValueError("state/severity invalid")
 missing=context.get("missing_fields",[])
 if not isinstance(missing,list) or len(missing)>100 or not all(isinstance(x,str) and x.isidentifier() for x in missing):raise ValueError("missing_fields invalid")
 actions=[]
 if missing:actions.append("complete_required_fields")
 if state=="failed":actions.append("review_failure_details")
 if state in {"pending","draft"}:actions.append("review_before_apply")
 if severity=="critical":actions.append("notify_authorised_administrator")
 if not actions:actions.append("no_action_required")
 return {"feature_id":fid,"resource":res,"context_id":cid,"assisted_by":aid,"state":state,"severity":severity,"suggested_action_keys":tuple(actions),"missing_field_names":tuple(sorted(missing)),"generated_text":False,"raw_context_exposed":False,"automatic_action":False,"executed":False,"auditable":True}
def _make(i,r,f):
 if f=="fed":
  def op(envelope,trust,*,actor):return _federation(IDS[i],r,envelope,trust,actor)
  op.__name__=f"verify_{r}_federated_compatibility"
 elif f=="cont":
  def op(services,*,actor,rto_minutes=60,rpo_minutes=15):return _continuity(IDS[i],r,services,actor,rto_minutes,rpo_minutes)
  op.__name__=f"plan_{r}_operational_continuity"
 else:
  def op(context,*,actor):return _assist(IDS[i],r,context,actor)
  op.__name__=f"assist_{r}_contextually"
 return op
FEDERATION_APIS=tuple(_make(i,r,"fed") for i,r in enumerate(FED));CONTINUITY_APIS=tuple(_make(7+i,r,"cont") for i,r in enumerate(CONT));ASSISTANCE_APIS=tuple(_make(23+i,r,"assist") for i,r in enumerate(ASSIST));ALL_APIS=FEDERATION_APIS+CONTINUITY_APIS+ASSISTANCE_APIS;globals().update({x.__name__:x for x in ALL_APIS})

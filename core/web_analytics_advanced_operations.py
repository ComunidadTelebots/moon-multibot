"""Validated analytics contracts for Web future-1157..1176."""
import copy,datetime as dt,hashlib,json
from collections import Counter,defaultdict
def analytics_import_preview(rows):
 if not isinstance(rows,list) or not rows:raise ValueError("invalid import")
 out=[{"row":i+1,"metric":x.get("metric"),"valid":bool(x.get("metric")) and isinstance(x.get("value"),(int,float))} for i,x in enumerate(rows)];return {"preview":out,"valid":sum(x["valid"] for x in out),"committed":False}
def analytics_collaboration_comment(thread,cid,author,text,metric):
 if not isinstance(thread,list) or any(x.get("id")==cid for x in thread) or not str(text).strip() or not metric:raise ValueError("invalid comment")
 return copy.deepcopy(thread)+[{"id":cid,"author":author,"text":text.strip(),"metric":metric,"resolved":False}]
def analytics_smart_tags(dataset,rules):
 if not isinstance(dataset,dict) or not isinstance(rules,dict):raise ValueError("invalid tags")
 return sorted([{"tag":tag,"field":r["field"]} for tag,r in rules.items() if dataset.get(r.get("field"))==r.get("value")],key=lambda x:x["tag"])
def analytics_activity_digest(events,kinds):
 if not isinstance(events,list) or not isinstance(kinds,(list,tuple,set)):raise ValueError("invalid digest")
 chosen=[copy.deepcopy(x) for x in events if x.get("kind") in kinds];return {"events":chosen,"counts":dict(Counter(x["kind"] for x in chosen)),"total":len(chosen)}
def analytics_expiry_alerts(datasets,instant,lead_days=7):
 now=_time(instant);out=[]
 for x in datasets:
  days=(_time(x["expires_at"])-now).days
  if days<=lead_days:out.append({"id":x["id"],"days":days,"state":"expired" if days<0 else "expiring"})
 return sorted(out,key=lambda x:x["days"])
def analytics_emergency_mode(state,actor,reason,enabled,instant):
 if not isinstance(state,dict) or not actor or len(str(reason))<5 or not isinstance(enabled,bool):raise ValueError("invalid emergency")
 result=copy.deepcopy(state);event={"enabled":enabled,"actor":actor,"reason":reason,"at":_iso(instant)};result["safe_mode"]=event;result.setdefault("audit",[]).append(event);return result
def analytics_effective_permissions(role,direct,denied):
 if any(not isinstance(x,(list,tuple,set)) for x in (role,direct,denied)):raise ValueError("invalid permissions")
 return {"effective":sorted((set(role)|set(direct))-set(denied)),"denied":sorted(set(denied)),"default_deny":True}
def analytics_shared_goals(goal,items):
 if goal.get("target",0)<=0 or goal.get("metric") not in {"coverage","accuracy","freshness"}:raise ValueError("invalid goal")
 teams=defaultdict(float)
 for x in items:
  if x.get("value",0)<0:raise ValueError("negative")
  teams[x["team"]]+=x["value"]
 total=sum(teams.values());return {"metric":goal["metric"],"target":goal["target"],"current":total,"percent":min(100,round(total/goal["target"]*100,2)),"teams":dict(teams)}
def analytics_config_recommender(config,signals):
 if not isinstance(config,dict) or not isinstance(signals,dict):raise ValueError("invalid recommendation")
 out=[]
 if signals.get("stale_ratio",0)>.2:out.append({"setting":"refresh_hours","value":6,"reason":"stale_data"})
 if signals.get("query_ms",0)>1000:out.append({"setting":"cache","value":True,"reason":"query_latency"})
 return out
def analytics_config_tests(config):
 if not isinstance(config,dict):raise ValueError("invalid config")
 c={"source":bool(config.get("source")),"retention":isinstance(config.get("retention_days"),int) and config["retention_days"]>0,"privacy":config.get("privacy") in {"aggregate","anonymous"}};return {"passed":all(c.values()),"checks":c,"failures":[k for k,v in c.items() if not v]}
def analytics_consent_center(state,purpose,granted,version,instant):
 if not isinstance(state,dict) or purpose not in {"measurement","profiling","sharing"} or not isinstance(granted,bool) or version<1:raise ValueError("invalid consent")
 result=copy.deepcopy(state);result[purpose]={"granted":granted,"version":version,"at":_iso(instant)};return result
def analytics_task_navigation(tasks,done=()):
 if not isinstance(tasks,list):raise ValueError("invalid tasks")
 done=set(done);ready=[x["id"] for x in tasks if x["id"] not in done and set(x.get("depends_on",[]))<=done];return {"done":sorted(done),"ready":ready,"next":ready[0] if ready else None}
def analytics_device_sync(local,remote):
 if not isinstance(local,dict) or not isinstance(remote,dict):raise ValueError("invalid sync")
 merged={};conflicts=[]
 for k in sorted(set(local)|set(remote)):
  c=[x for x in (local.get(k),remote.get(k)) if x]
  if len(c)==2 and c[0].get("rev")==c[1].get("rev") and c[0].get("value")!=c[1].get("value"):conflicts.append(k)
  merged[k]=copy.deepcopy(max(c,key=lambda x:x.get("rev",0)))
 return {"merged":merged,"conflicts":conflicts}
def analytics_duplicate_detection(rows):
 if not isinstance(rows,list):raise ValueError("invalid rows")
 g=defaultdict(list)
 for x in rows:g[(x.get("metric"),x.get("timestamp"),x.get("dimension"))].append(x.get("id"))
 return [{"key":list(k),"ids":v} for k,v in g.items() if len(v)>1]
def analytics_adaptive_quota(base,used,cost):
 if not isinstance(base,int) or base<1 or used<0 or not 0<=cost<=1:raise ValueError("invalid quota")
 limit=max(1,round(base*(1-.5*cost)));return {"limit":limit,"used":used,"remaining":max(0,limit-used),"limited":used>=limit}
def analytics_community_impact(events):
 w={"open_dataset":5,"shared_report":3,"correction":2}
 if not isinstance(events,list) or any(x.get("type") not in w for x in events):raise ValueError("invalid impact")
 c=Counter()
 for x in events:c[x["type"]]+=x.get("count",1)
 return {"totals":dict(c),"score":sum(c[k]*v for k,v in w.items()),"public_safe":True}
def analytics_reviewable_translation(metric,locale,label,reviewer=None):
 if not metric or len(str(locale))<2 or not str(label).strip():raise ValueError("invalid translation")
 return {"metric":metric,"locale":locale,"label":label.strip(),"status":"approved" if reviewer else "pending_review","reviewer":reviewer}
def analytics_grouped_notifications(items):
 if not isinstance(items,list):raise ValueError("invalid notifications")
 g=defaultdict(list)
 for x in items:
  if not x.get("dataset_id") or not x.get("type"):raise ValueError("missing context")
  g[x["dataset_id"]].append(copy.deepcopy(x))
 return [{"dataset_id":k,"count":len(v),"items":v} for k,v in sorted(g.items())]
def analytics_migration_assistant(source,target):
 if not isinstance(source,int) or target<=source:raise ValueError("invalid migration")
 return {"from":source,"to":target,"steps":[{"version":v,"dry_run":True} for v in range(source+1,target+1)],"executed":False}
def analytics_admin_decision_log(log,did,actor,action,reason,instant):
 if not isinstance(log,list) or any(x.get("id")==did for x in log) or action not in {"publish","restrict","delete","restore"} or len(str(reason))<5:raise ValueError("invalid decision")
 row={"id":did,"actor":actor,"action":action,"reason":reason,"at":_iso(instant),"previous":log[-1]["digest"] if log else ""};row["digest"]=hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest();return copy.deepcopy(log)+[row]
def _time(v):
 if isinstance(v,str):v=dt.datetime.fromisoformat(v.replace("Z","+00:00"))
 if not isinstance(v,dt.datetime) or v.tzinfo is None:raise ValueError("aware datetime required")
 return v.astimezone(dt.timezone.utc)
def _iso(v):return _time(v).isoformat().replace("+00:00","Z")

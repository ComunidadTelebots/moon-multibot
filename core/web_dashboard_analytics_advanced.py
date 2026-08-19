"""Side-effect-free Web dashboard/analytics contracts for future-1137..1156."""
import copy, datetime as dt, hashlib, json
from collections import Counter, defaultdict, deque

def dashboard_consent_center(state,purpose,granted,version,instant):
 if not isinstance(state,dict) or purpose not in {"analytics","personalization","sharing"} or not isinstance(granted,bool) or int(version)<1: raise ValueError("invalid dashboard consent")
 result=copy.deepcopy(state); result[purpose]={"granted":granted,"version":int(version),"at":_iso(instant)}; return result
def dashboard_task_navigation(tasks,done=()):
 if not isinstance(tasks,list): raise ValueError("invalid dashboard tasks")
 completed=set(done); ready=[x["id"] for x in tasks if x.get("id") not in completed and set(x.get("depends_on",[]))<=completed]; return {"completed":sorted(completed),"ready":ready,"next":ready[0] if ready else None}
def dashboard_device_sync(local,remote):
 if not isinstance(local,dict) or not isinstance(remote,dict): raise ValueError("invalid dashboard sync")
 merged={}; conflicts=[]
 for key in sorted(set(local)|set(remote)):
  choices=[x for x in (local.get(key),remote.get(key)) if x]
  if len(choices)==2 and choices[0].get("revision")==choices[1].get("revision") and choices[0].get("value")!=choices[1].get("value"): conflicts.append(key)
  merged[key]=copy.deepcopy(max(choices,key=lambda x:(x.get("revision",0),str(x.get("device","")))))
 return {"merged":merged,"conflicts":conflicts}
def dashboard_duplicate_detection(widgets):
 if not isinstance(widgets,list): raise ValueError("invalid widgets")
 groups=defaultdict(list)
 for row in widgets: groups[(str(row.get("title","")).strip().lower(),row.get("data_source"),row.get("type"))].append(row.get("id"))
 return [{"signature":list(key),"ids":ids} for key,ids in groups.items() if len(ids)>1]
def dashboard_adaptive_quota(base,used,complexity):
 if not isinstance(base,int) or base<1 or not isinstance(used,int) or used<0 or not 0<=complexity<=1: raise ValueError("invalid dashboard quota")
 limit=max(1,round(base*(1-.5*complexity))); return {"limit":limit,"used":used,"remaining":max(0,limit-used),"limited":used>=limit}
def dashboard_community_impact(events):
 weights={"shared_view":2,"public_dataset":5,"feedback":1}
 if not isinstance(events,list) or any(x.get("type") not in weights or x.get("count",0)<0 for x in events): raise ValueError("invalid dashboard impact")
 totals=Counter()
 for row in events: totals[row["type"]]+=row["count"]
 return {"totals":dict(totals),"score":sum(totals[k]*w for k,w in weights.items()),"privacy_safe":True}
def dashboard_reviewable_translation(widget_id,locale,title,reviewer=None):
 if not widget_id or len(str(locale))<2 or not str(title).strip(): raise ValueError("invalid dashboard translation")
 return {"widget_id":widget_id,"locale":locale,"title":str(title).strip(),"status":"approved" if reviewer else "pending_review","reviewer":reviewer}
def dashboard_grouped_notifications(items):
 if not isinstance(items,list): raise ValueError("invalid dashboard notifications")
 groups=defaultdict(list)
 for item in items:
  if not item.get("dashboard_id") or not item.get("type"): raise ValueError("notification missing context")
  groups[item["dashboard_id"]].append(copy.deepcopy(item))
 return [{"dashboard_id":key,"count":len(rows),"types":sorted({x["type"] for x in rows}),"items":rows} for key,rows in sorted(groups.items())]
def dashboard_migration_assistant(source,target):
 if not isinstance(source,int) or not isinstance(target,int) or target<=source: raise ValueError("invalid dashboard migration")
 return {"from":source,"to":target,"steps":[{"version":v,"snapshot":True,"executed":False} for v in range(source+1,target+1)],"rollback_available":True}
def dashboard_admin_decision_log(log,decision_id,actor,action,reason,instant):
 if not isinstance(log,list) or any(x.get("id")==decision_id for x in log) or action not in {"publish","unpublish","transfer","archive"} or len(str(reason).strip())<5: raise ValueError("invalid dashboard decision")
 row={"id":decision_id,"actor":actor,"action":action,"reason":reason,"at":_iso(instant),"previous":log[-1]["digest"] if log else ""}; row["digest"]=hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest(); return copy.deepcopy(log)+[row]
def dashboard_continuous_accessibility(views):
 if not isinstance(views,list): raise ValueError("invalid dashboard views")
 issues=[]
 for view in views:
  if not view.get("heading"): issues.append({"id":view.get("id"),"rule":"heading"})
  if any(not x.get("label") for x in view.get("controls",[])): issues.append({"id":view.get("id"),"rule":"control_label"})
 return {"issues":issues,"score":max(0,100-20*len(issues)),"continuous":True}
def dashboard_external_storage(config,probe):
 if config.get("provider") not in {"s3","gcs","webdav"} or not config.get("path") or not isinstance(probe,dict): raise ValueError("invalid dashboard storage")
 return {"provider":config["provider"],"path":config["path"],"healthy":probe.get("read") is True and probe.get("write") is True,"credentials_redacted":True}
def dashboard_time_policy(start,end,instant):
 if not all(isinstance(x,int) and 0<=x<24 for x in (start,end)): raise ValueError("invalid dashboard window")
 hour=_time(instant).hour; active=start<=hour<end if start<end else hour>=start or hour<end; return {"active":active,"hour":hour,"window":[start,end]}
def dashboard_sustainable_growth(users,rate,months,capacity):
 if users<0 or not 0<=rate<=1 or not isinstance(months,int) or months<0 or capacity<0: raise ValueError("invalid dashboard growth")
 series=[round(users*(1+rate)**i,2) for i in range(months+1)]; return {"users":series,"sustainable":max(series,default=0)<=capacity,"simulated":True}

def analytics_dependency_map(graph,changed):
 if not isinstance(graph,dict) or changed not in graph: raise ValueError("invalid analytics graph")
 seen=set(); queue=deque(graph[changed])
 while queue:
  item=queue.popleft()
  if item in seen: continue
  seen.add(item); queue.extend(graph.get(item,[]))
 return {"metric":changed,"affected":sorted(seen),"recomputed":False}
def analytics_visual_rules(rules,values):
 if not isinstance(rules,list) or not isinstance(values,dict): raise ValueError("invalid analytics rules")
 actions=[]
 for rule in rules:
  if rule.get("operator") not in {"gte","lte"} or rule.get("style") not in {"normal","warning","critical"}: raise ValueError("unsupported analytics rule")
  actual=values.get(rule.get("metric")); matched=actual>=rule.get("threshold") if rule["operator"]=="gte" else actual<=rule.get("threshold")
  if matched: actions.append({"metric":rule["metric"],"style":rule["style"]})
 return {"actions":actions,"evaluated":len(rules)}
def analytics_review_inbox(requests,scopes):
 if not isinstance(requests,list) or not isinstance(scopes,(list,tuple,set)): raise ValueError("invalid analytics review")
 return sorted([copy.deepcopy(x) for x in requests if x.get("status")=="pending" and x.get("scope") in scopes],key=lambda x:(-x.get("risk",0),str(x.get("id"))))
def analytics_sensitive_changes(before,after):
 if not isinstance(before,dict) or not isinstance(after,dict): raise ValueError("invalid analytics changes")
 protected={"formula","source","retention_days","dimensions"}; changed=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k)); sensitive=sorted(set(changed)&protected); return {"changed":changed,"sensitive":sensitive,"review_required":bool(sensitive),"applied":False}
def analytics_decision_explanation(model,signals,decision):
 if not str(model) or not isinstance(signals,dict) or not isinstance(decision,bool): raise ValueError("invalid analytics decision")
 return {"result":"include" if decision else "exclude","model":model,"signals":copy.deepcopy(signals),"human_review":True}
def analytics_data_quality(records):
 if not isinstance(records,list): raise ValueError("invalid analytics records")
 issues=[]
 for index,row in enumerate(records):
  if not row.get("metric"): issues.append({"row":index,"issue":"missing_metric"})
  if not isinstance(row.get("value"),(int,float)): issues.append({"row":index,"issue":"non_numeric_value"})
 return {"score":max(0,100-round(100*len(issues)/max(1,2*len(records)))),"issues":issues,"records":len(records)}
def _time(value):
 if isinstance(value,str): value=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
 if not isinstance(value,dt.datetime) or value.tzinfo is None: raise ValueError("aware datetime required")
 return value.astimezone(dt.timezone.utc)
def _iso(value): return _time(value).isoformat().replace("+00:00","Z")

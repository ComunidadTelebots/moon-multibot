"""Pure Web proxy/dashboard contracts for future-1117..1136."""
import copy, datetime as dt, hashlib
from collections import Counter, defaultdict, deque

def proxy_continuous_accessibility(views):
 if not isinstance(views,list): raise ValueError("invalid proxy views")
 issues=[]
 for view in views:
  if not view.get("label"): issues.append({"id":view.get("id"),"rule":"accessible_name"})
  if view.get("status_color_only") is True: issues.append({"id":view.get("id"),"rule":"color_only_status"})
 return {"issues":issues,"score":max(0,100-15*len(issues)),"continuous":True}
def proxy_external_storage_connector(config,probe):
 if config.get("provider") not in {"s3","gcs","webdav"} or not config.get("path") or not isinstance(probe,dict): raise ValueError("invalid proxy storage")
 return {"provider":config["provider"],"path":config["path"],"readable":probe.get("read") is True,"writable":probe.get("write") is True,"credentials_redacted":True}
def proxy_time_window_policy(policy,instant):
 if not isinstance(policy,dict) or not all(isinstance(policy.get(k),int) and 0<=policy[k]<24 for k in ("start","end")): raise ValueError("invalid proxy window")
 hour=_time(instant).hour; start,end=policy["start"],policy["end"]; active=start<=hour<end if start<end else hour>=start or hour<end
 return {"active":active,"hour_utc":hour,"action":policy.get("action","route") if active else "hold"}
def proxy_sustainable_growth(nodes,monthly_rate,months,max_load):
 if nodes<0 or not 0<=monthly_rate<=1 or not isinstance(months,int) or months<0 or max_load<0: raise ValueError("invalid proxy growth")
 series=[round(nodes*(1+monthly_rate)**i,2) for i in range(months+1)]; return {"nodes":series,"sustainable":max(series,default=0)<=max_load,"simulated":True}

def dashboard_dependency_map(graph,changed):
 if not isinstance(graph,dict) or changed not in graph: raise ValueError("invalid dashboard graph")
 seen=set(); queue=deque(graph[changed])
 while queue:
  item=queue.popleft()
  if item in seen: continue
  seen.add(item); queue.extend(graph.get(item,[]))
 return {"widget":changed,"affected":sorted(seen),"recalculated":False}
def dashboard_visual_rules(rules,metrics):
 if not isinstance(rules,list) or not isinstance(metrics,dict): raise ValueError("invalid dashboard rules")
 actions=[]
 for rule in rules:
  if rule.get("operator") not in {"gte","lte","eq"} or rule.get("style") not in {"info","warning","critical"}: raise ValueError("unsupported dashboard rule")
  value=metrics.get(rule.get("metric")); target=rule.get("value"); matched=value>=target if rule["operator"]=="gte" else value<=target if rule["operator"]=="lte" else value==target
  if matched: actions.append({"widget":rule.get("widget"),"style":rule["style"]})
 return {"actions":actions,"evaluated":len(rules)}
def dashboard_review_inbox(requests,reviewer_scopes):
 if not isinstance(requests,list) or not isinstance(reviewer_scopes,(list,tuple,set)): raise ValueError("invalid dashboard inbox")
 return sorted([copy.deepcopy(x) for x in requests if x.get("state")=="pending" and x.get("scope") in reviewer_scopes],key=lambda x:(-x.get("priority",0),str(x.get("id"))))
def dashboard_sensitive_changes(before,after):
 if not isinstance(before,dict) or not isinstance(after,dict): raise ValueError("invalid dashboard change")
 protected={"visibility","owner","data_source","permissions"}; changed=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k)); sensitive=sorted(set(changed)&protected)
 return {"changed":changed,"sensitive":sensitive,"approval_required":bool(sensitive),"applied":False}
def dashboard_decision_explanation(rule,inputs,visible):
 if not str(rule) or not isinstance(inputs,dict) or not isinstance(visible,bool): raise ValueError("invalid dashboard decision")
 return {"outcome":"visible" if visible else "hidden","rule":rule,"inputs":copy.deepcopy(inputs),"override_available":True}
def dashboard_data_quality(rows,required=("id","value")):
 if not isinstance(rows,list): raise ValueError("invalid dashboard data")
 issues=[]; ids=set()
 for row in rows:
  for field in required:
   if row.get(field) is None: issues.append({"id":row.get("id"),"field":field,"issue":"missing"})
  if row.get("id") in ids: issues.append({"id":row.get("id"),"field":"id","issue":"duplicate"})
  ids.add(row.get("id"))
 return {"score":max(0,100-round(100*len(issues)/max(1,len(rows)*len(required)))),"issues":issues,"rows":len(rows)}
def dashboard_import_preview(widgets):
 if not isinstance(widgets,list) or not widgets: raise ValueError("invalid dashboard import")
 preview=[]; ids=set()
 for i,row in enumerate(widgets):
  issues=[]
  if not row.get("id") or not row.get("type"): issues.append("id_and_type_required")
  if row.get("id") in ids: issues.append("duplicate_id")
  ids.add(row.get("id")); preview.append({"row":i+1,"widget":copy.deepcopy(row),"issues":issues})
 return {"preview":preview,"valid":sum(not x["issues"] for x in preview),"imported":False}
def dashboard_collaboration_comment(thread,comment_id,author,text,widget_id):
 if not isinstance(thread,list) or any(x.get("id")==comment_id for x in thread) or not str(text).strip() or not widget_id: raise ValueError("invalid dashboard comment")
 return copy.deepcopy(thread)+[{"id":comment_id,"author":author,"text":str(text).strip(),"widget_id":widget_id,"resolved":False}]
def dashboard_smart_tags(widget,taxonomy):
 if not isinstance(widget,dict) or not isinstance(taxonomy,dict): raise ValueError("invalid dashboard tags")
 text=(str(widget.get("title",""))+" "+str(widget.get("description",""))).lower(); tags=[]
 for tag,terms in taxonomy.items():
  hits=sorted({str(term).lower() for term in terms if str(term).lower() in text})
  if hits: tags.append({"tag":tag,"evidence":hits,"confidence":round(len(hits)/len(terms),2)})
 return sorted(tags,key=lambda x:(-x["confidence"],x["tag"]))
def dashboard_activity_digest(events,kinds):
 if not isinstance(events,list) or not isinstance(kinds,(list,tuple,set)): raise ValueError("invalid dashboard digest")
 chosen=[copy.deepcopy(x) for x in events if x.get("kind") in kinds]; return {"events":chosen,"counts":dict(Counter(x["kind"] for x in chosen)),"total":len(chosen)}
def dashboard_expiry_alerts(widgets,instant,lead_days=7):
 now=_time(instant); alerts=[]
 for widget in widgets:
  expiry=_time(widget.get("expires_at")); days=(expiry-now).days
  if days<=lead_days: alerts.append({"widget_id":widget["id"],"days":days,"state":"expired" if days<0 else "expiring"})
 return sorted(alerts,key=lambda x:x["days"])
def dashboard_emergency_mode(state,operator,reason,enabled,instant):
 if not isinstance(state,dict) or not operator or len(str(reason).strip())<5 or not isinstance(enabled,bool): raise ValueError("invalid dashboard emergency")
 result=copy.deepcopy(state); event={"enabled":enabled,"operator":operator,"reason":reason,"at":_iso(instant)}; result["safe_mode"]=event; result.setdefault("history",[]).append(copy.deepcopy(event)); return result
def dashboard_effective_permissions(role_grants,direct_grants,direct_denies):
 if any(not isinstance(x,(list,tuple,set)) for x in (role_grants,direct_grants,direct_denies)): raise ValueError("invalid dashboard permissions")
 role,direct,denied=map(set,(role_grants,direct_grants,direct_denies)); effective=(role|direct)-denied
 return {"effective":sorted(effective),"sources":{p:"deny" if p in denied else "direct" if p in direct else "role" for p in sorted(role|direct|denied)}}
def dashboard_shared_goals(goal,contributions):
 if goal.get("metric") not in {"adoption","accuracy","response_time"} or goal.get("target",0)<=0: raise ValueError("invalid dashboard goal")
 teams=defaultdict(float)
 for row in contributions:
  if row.get("value",0)<0: raise ValueError("negative dashboard contribution")
  teams[row["team"]]+=row["value"]
 current=sum(teams.values()); return {"metric":goal["metric"],"current":current,"target":goal["target"],"percent":min(100,round(current/goal["target"]*100,2)),"teams":dict(teams)}
def dashboard_config_recommender(config,usage):
 if not isinstance(config,dict) or not isinstance(usage,dict): raise ValueError("invalid dashboard recommendation")
 rows=[]
 if usage.get("load_ms",0)>1000 and config.get("refresh_seconds",0)<60: rows.append({"setting":"refresh_seconds","value":60,"reason":"load_time","priority":90})
 if usage.get("mobile_share",0)>.5 and not config.get("responsive"): rows.append({"setting":"responsive","value":True,"reason":"mobile_usage","priority":70})
 return rows
def dashboard_config_tests(config):
 if not isinstance(config,dict): raise ValueError("invalid dashboard config")
 checks={"title":bool(config.get("title")),"layout":config.get("layout") in {"grid","list"},"refresh":isinstance(config.get("refresh_seconds"),int) and config["refresh_seconds"]>=10}
 return {"passed":all(checks.values()),"checks":checks,"failures":[k for k,v in checks.items() if not v]}
def _time(value):
 if isinstance(value,str): value=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
 if not isinstance(value,dt.datetime) or value.tzinfo is None: raise ValueError("aware datetime required")
 return value.astimezone(dt.timezone.utc)
def _iso(value): return _time(value).isoformat().replace("+00:00","Z")

"""Resource-scoped contracts for Web catalog future-1077..1096."""
import copy, datetime as dt, hashlib, json
from collections import Counter, defaultdict, deque

def news_consent_center(state,purpose,granted,version,instant):
 if not isinstance(state,dict) or purpose not in {"analytics","personalization","syndication"} or not isinstance(granted,bool) or int(version)<1: raise ValueError("invalid news consent")
 result=copy.deepcopy(state); result[purpose]={"granted":granted,"version":int(version),"at":_iso(instant)}; return result
def news_task_navigation(tasks,done=()):
 if not isinstance(tasks,list): raise ValueError("invalid editorial tasks")
 completed=set(done); ready=[x["id"] for x in tasks if x.get("id") not in completed and set(x.get("depends_on",[]))<=completed]
 return {"done":sorted(completed),"ready":ready,"next":ready[0] if ready else None}
def news_device_sync(left,right):
 if not isinstance(left,dict) or not isinstance(right,dict): raise ValueError("invalid news sync")
 merged={}; conflicts=[]
 for key in sorted(set(left)|set(right)):
  values=[x for x in (left.get(key),right.get(key)) if x]
  if len(values)==2 and values[0].get("rev")==values[1].get("rev") and values[0].get("value")!=values[1].get("value"): conflicts.append(key)
  merged[key]=copy.deepcopy(max(values,key=lambda x:(x.get("rev",0),str(x.get("device","")))))
 return {"merged":merged,"conflicts":conflicts}
def news_duplicate_detection(articles):
 if not isinstance(articles,list): raise ValueError("invalid articles")
 groups=defaultdict(list)
 for row in articles:
  key=(str(row.get("canonical_url","")).strip().lower(),hashlib.sha256(str(row.get("headline","")).strip().lower().encode()).hexdigest())
  groups[key].append(row.get("id"))
 return [{"canonical_url":k[0],"headline_hash":k[1],"ids":v} for k,v in groups.items() if len(v)>1]
def news_adaptive_quota(base,published,trust):
 if not isinstance(base,int) or base<1 or published<0 or not 0<=trust<=1: raise ValueError("invalid news quota")
 limit=max(1,round(base*(.75+trust*.5))); return {"limit":limit,"published":published,"remaining":max(0,limit-published),"requires_review":published>=limit}
def news_community_impact(events):
 weights={"correction":4,"source":2,"local_story":5}
 if not isinstance(events,list) or any(x.get("type") not in weights or x.get("count",0)<0 for x in events): raise ValueError("invalid news impact")
 totals=Counter();
 for row in events: totals[row["type"]]+=row["count"]
 return {"totals":dict(totals),"score":sum(totals[k]*v for k,v in weights.items()),"transparent":True}
def news_reviewable_translation(article_id,locale,text,reviewer=None):
 if not article_id or len(str(locale))<2 or not str(text).strip(): raise ValueError("invalid news translation")
 return {"article_id":article_id,"locale":locale,"text":str(text).strip(),"status":"approved" if reviewer else "review_required","reviewer":reviewer}
def news_grouped_notifications(items):
 if not isinstance(items,list): raise ValueError("invalid news notifications")
 groups=defaultdict(list)
 for item in items:
  if not item.get("story_id") or not item.get("type"): raise ValueError("notification missing context")
  groups[item["story_id"]].append(copy.deepcopy(item))
 return [{"story_id":k,"count":len(v),"types":sorted({x["type"] for x in v}),"items":v} for k,v in sorted(groups.items())]
def news_migration_assistant(schema_version,target):
 if not isinstance(schema_version,int) or target<=schema_version: raise ValueError("invalid news migration")
 return {"from":schema_version,"to":target,"steps":[{"version":v,"backup":True,"executed":False} for v in range(schema_version+1,target+1)],"dry_run":True}
def news_admin_decision_log(log,decision_id,editor,action,reason,instant):
 if not isinstance(log,list) or any(x.get("id")==decision_id for x in log) or action not in {"publish","unpublish","correct","archive"} or len(str(reason).strip())<5: raise ValueError("invalid news decision")
 row={"id":decision_id,"editor":editor,"action":action,"reason":reason,"at":_iso(instant),"previous":log[-1]["digest"] if log else ""}; row["digest"]=hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest(); return copy.deepcopy(log)+[row]
def news_continuous_accessibility(documents):
 if not isinstance(documents,list): raise ValueError("invalid news documents")
 issues=[]
 for doc in documents:
  if not doc.get("headline"): issues.append({"id":doc.get("id"),"rule":"headline"})
  if any(not image.get("alt") for image in doc.get("images",[])): issues.append({"id":doc.get("id"),"rule":"image_alt"})
 return {"issues":issues,"score":max(0,100-20*len(issues)),"scan":"continuous"}
def news_external_storage(config,probe):
 if config.get("provider") not in {"s3","gcs","webdav"} or not config.get("archive") or not isinstance(probe,dict): raise ValueError("invalid news storage")
 return {"provider":config["provider"],"archive":config["archive"],"healthy":probe.get("write_test") is True,"secret_redacted":True}
def news_time_policy(start_hour,end_hour,instant):
 if not all(isinstance(x,int) and 0<=x<24 for x in (start_hour,end_hour)): raise ValueError("invalid publication window")
 hour=_time(instant).hour; permitted=start_hour<=hour<end_hour if start_hour<end_hour else hour>=start_hour or hour<end_hour
 return {"permitted":permitted,"hour":hour,"window":[start_hour,end_hour]}
def news_sustainable_growth(audience,rate,months,editor_capacity):
 if audience<0 or not 0<=rate<=1 or not isinstance(months,int) or months<0 or editor_capacity<0: raise ValueError("invalid newsroom growth")
 series=[round(audience*(1+rate)**i) for i in range(months+1)]; load=[round(x/1000,2) for x in series]
 return {"audience":series,"editor_load":load,"sustainable":max(load,default=0)<=editor_capacity,"simulated":True}

def proxy_dependency_map(graph,changed):
 if not isinstance(graph,dict) or changed not in graph: raise ValueError("invalid proxy dependencies")
 seen=set(); queue=deque(graph[changed])
 while queue:
  item=queue.popleft()
  if item in seen: continue
  seen.add(item); queue.extend(graph.get(item,[]))
 return {"proxy":changed,"affected":sorted(seen),"restart_performed":False}
def proxy_visual_rules(rules,metrics):
 if not isinstance(rules,list) or not isinstance(metrics,dict): raise ValueError("invalid proxy visuals")
 result=[]
 for rule in rules:
  if rule.get("metric") not in metrics or rule.get("style") not in {"warning","critical","healthy"}: raise ValueError("invalid proxy rule")
  if metrics[rule["metric"]]>=rule.get("threshold",0): result.append({"target":rule.get("target","proxy"),"style":rule["style"]})
 return result
def proxy_review_inbox(requests,scopes):
 if not isinstance(requests,list): raise ValueError("invalid proxy reviews")
 return sorted([copy.deepcopy(x) for x in requests if x.get("status")=="pending" and x.get("scope") in scopes],key=lambda x:(-x.get("risk",0),str(x.get("id"))))
def proxy_sensitive_changes(before,after):
 if not isinstance(before,dict) or not isinstance(after,dict): raise ValueError("invalid proxy changes")
 sensitive={"endpoint","credentials_ref","tls_verify","allowed_hosts"}; changed=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k)); flagged=sorted(set(changed)&sensitive)
 return {"changed":changed,"sensitive":flagged,"approval_required":bool(flagged),"applied":False}
def proxy_decision_explanation(policy,signals,allowed):
 if not policy or not isinstance(signals,dict) or not isinstance(allowed,bool): raise ValueError("invalid proxy decision")
 safe={k:v for k,v in signals.items() if k not in {"token","password","secret"}}; return {"decision":"route" if allowed else "block","policy":policy,"signals":safe,"appealable":True}
def proxy_data_quality(proxies):
 if not isinstance(proxies,list): raise ValueError("invalid proxies")
 defects=[]; endpoints=set()
 for item in proxies:
  if not item.get("id") or not str(item.get("endpoint","")).startswith(("http://","https://")): defects.append({"id":item.get("id"),"issue":"invalid_identity_or_endpoint"})
  if item.get("endpoint") in endpoints: defects.append({"id":item.get("id"),"issue":"duplicate_endpoint"})
  endpoints.add(item.get("endpoint"))
 return {"score":max(0,100-round(100*len(defects)/max(1,len(proxies)))),"defects":defects,"records":len(proxies)}

def _time(value):
 if isinstance(value,str): value=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
 if not isinstance(value,dt.datetime) or value.tzinfo is None: raise ValueError("aware datetime required")
 return value.astimezone(dt.timezone.utc)
def _iso(value): return _time(value).isoformat().replace("+00:00","Z")

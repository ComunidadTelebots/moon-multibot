"""Pure contracts for mixed Web creator/news catalog slice future-1057..1076."""
import copy, datetime as dt, hashlib
from collections import Counter, defaultdict, deque

def creator_continuous_accessibility(pages):
 if not isinstance(pages,list): raise ValueError("invalid pages")
 issues=[]
 for page in pages:
  for key in ("title","lang","main_landmark"):
   if not page.get(key): issues.append({"page":page.get("id"),"rule":key,"severity":"high" if key=="main_landmark" else "medium"})
 return {"pages":len(pages),"issues":issues,"score":max(0,100-len(issues)*10),"continuous":True}
def creator_external_storage_connector(config,probe):
 if config.get("provider") not in {"s3","gcs","webdav"} or not str(config.get("bucket","")).strip() or not isinstance(probe,dict): raise ValueError("invalid storage connector")
 return {"provider":config["provider"],"bucket":config["bucket"],"reachable":probe.get("status")==200,"read_only":config.get("mode","read")=="read","credentials_exposed":False}
def creator_time_window_policy(policy,instant):
 hour=_time(instant).hour
 if not isinstance(policy,dict) or not 0<=policy.get("start",-1)<=23 or not 0<=policy.get("end",-1)<=23: raise ValueError("invalid time policy")
 start,end=policy["start"],policy["end"]; allowed=start<=hour<end if start<end else hour>=start or hour<end
 return {"allowed":allowed,"hour_utc":hour,"reason":"inside_window" if allowed else "outside_window"}
def creator_sustainable_growth(current,monthly_rate,months,capacity):
 if any(not isinstance(x,(int,float)) or x<0 for x in (current,monthly_rate,months,capacity)) or monthly_rate>1: raise ValueError("invalid growth simulation")
 values=[round(current*((1+monthly_rate)**i),2) for i in range(int(months)+1)]; return {"series":values,"sustainable":max(values)<=capacity,"capacity":capacity,"applied":False}
def creator_content_dependency_map(graph,changed):
 if not isinstance(graph,dict) or changed not in graph: raise ValueError("invalid dependency graph")
 seen=set(); queue=deque([changed])
 while queue:
  item=queue.popleft()
  for child in graph.get(item,[]):
   if child not in seen: seen.add(child); queue.append(child)
 return {"changed":changed,"affected":sorted(seen),"cycles_safe":changed not in seen,"executed":False}
def creator_conditional_visual_rules(rules,context):
 if not isinstance(rules,list) or not isinstance(context,dict): raise ValueError("invalid visual rules")
 actions=[]
 for rule in rules:
  if rule.get("operator") not in {"eq","gte"} or rule.get("action") not in {"show","hide","highlight"}: raise ValueError("unsupported visual rule")
  actual=context.get(rule.get("field")); matched=actual==rule.get("value") if rule["operator"]=="eq" else isinstance(actual,(int,float)) and actual>=rule.get("value")
  if matched: actions.append({"target":rule.get("target"),"action":rule["action"]})
 return {"actions":actions,"evaluated":len(rules)}
def creator_unified_review_inbox(requests,reviewer_roles):
 if not isinstance(requests,list) or not isinstance(reviewer_roles,(list,tuple,set)): raise ValueError("invalid review inbox")
 visible=[copy.deepcopy(x) for x in requests if x.get("status")=="pending" and x.get("required_role") in reviewer_roles]
 return sorted(visible,key=lambda x:(-int(x.get("priority",0)),str(x.get("id"))))
def creator_scoped_sensitive_changes(before,after,sensitive=("verified","payout","owner")):
 if not isinstance(before,dict) or not isinstance(after,dict): raise ValueError("invalid change documents")
 changed=[k for k in sorted(set(before)|set(after)) if before.get(k)!=after.get(k)]; flagged=[k for k in changed if k in sensitive]
 return {"changed":changed,"sensitive":flagged,"requires_review":bool(flagged),"applied":False}
def creator_automatic_decision_explanation(rule,facts,result):
 if not str(rule) or not isinstance(facts,dict) or not isinstance(result,bool): raise ValueError("invalid decision")
 return {"decision":"allow" if result else "deny","rule":rule,"facts":copy.deepcopy(facts),"human_review_available":True}
def creator_scoped_data_quality(records,required=("id","name")):
 if not isinstance(records,list): raise ValueError("invalid records")
 missing=Counter(); duplicates=[]; seen=set()
 for row in records:
  for field in required:
   if not row.get(field): missing[field]+=1
  if row.get("id") in seen: duplicates.append(row.get("id"))
  seen.add(row.get("id"))
 defects=sum(missing.values())+len(duplicates); denom=max(1,len(records)*len(required)); return {"score":max(0,round(100*(1-defects/denom),2)),"missing":dict(missing),"duplicates":duplicates}

def news_import_preview(rows):
 if not isinstance(rows,list) or not rows: raise ValueError("invalid news import")
 preview=[]
 for i,row in enumerate(rows):
  if not isinstance(row,dict): raise ValueError("invalid news row")
  issues=[] if row.get("headline") and row.get("source_url") else ["headline_and_source_required"]
  preview.append({"row":i+1,"headline":str(row.get("headline","")).strip(),"source_url":row.get("source_url"),"issues":issues})
 return {"preview":preview,"valid":sum(not x["issues"] for x in preview),"published":False}
def news_collaboration_comment(thread,comment_id,author,text,section):
 if not isinstance(thread,list) or any(x.get("id")==comment_id for x in thread) or not str(text).strip() or section not in {"headline","body","sources"}: raise ValueError("invalid editorial comment")
 return copy.deepcopy(thread)+[{"id":comment_id,"author":author,"text":str(text).strip(),"section":section,"resolved":False}]
def news_smart_tags(article,taxonomy):
 if not isinstance(article,dict) or not isinstance(taxonomy,dict): raise ValueError("invalid tagging input")
 content=(str(article.get("headline",""))+" "+str(article.get("body",""))).lower(); rows=[]
 for tag,terms in taxonomy.items():
  hits=sorted({term for term in map(str.lower,terms) if term in content})
  if hits: rows.append({"tag":tag,"confidence":min(1,round(len(hits)/max(1,len(terms)),2)),"evidence":hits})
 return sorted(rows,key=lambda x:(-x["confidence"],x["tag"]))
def news_activity_digest(events,subscriptions):
 if not isinstance(events,list) or not isinstance(subscriptions,(list,tuple,set)): raise ValueError("invalid news digest")
 chosen=[copy.deepcopy(x) for x in events if x.get("desk") in subscriptions]; counts=Counter(x.get("desk") for x in chosen)
 return {"stories":chosen,"by_desk":dict(sorted(counts.items())),"total":len(chosen)}
def news_expiry_alerts(articles,instant,lead_hours=24):
 now=_time(instant); alerts=[]
 for article in articles:
  expiry=_time(article.get("embargo_or_expiry")); hours=(expiry-now).total_seconds()/3600
  if hours<=lead_hours: alerts.append({"id":article["id"],"state":"expired" if hours<0 else "due","hours":round(hours,1)})
 return sorted(alerts,key=lambda x:x["hours"])
def news_emergency_mode(state,editor,reason,enabled,instant):
 if not isinstance(state,dict) or not editor or len(str(reason).strip())<5 or not isinstance(enabled,bool): raise ValueError("invalid newsroom emergency")
 result=copy.deepcopy(state); result["publishing_lock"]={"enabled":enabled,"editor":editor,"reason":reason,"at":_iso(instant)}; result.setdefault("history",[]).append(copy.deepcopy(result["publishing_lock"])); return result
def news_effective_permissions(role,user_grants,user_denies):
 defaults={"reporter":{"draft"},"editor":{"draft","review","publish"},"admin":{"draft","review","publish","delete"}}
 if role not in defaults: raise ValueError("invalid newsroom role")
 effective=(defaults[role]|set(user_grants))-set(user_denies); return {"role":role,"effective":sorted(effective),"denied":sorted(set(user_denies)),"default_deny":True}
def news_shared_goals(goal,contributions):
 if goal.get("metric") not in {"stories","corrections","sources"} or goal.get("target",0)<=0: raise ValueError("invalid editorial goal")
 members=defaultdict(int)
 for item in contributions:
  if item.get("value",0)<0: raise ValueError("negative contribution")
  members[item["author"]]+=item["value"]
 total=sum(members.values()); return {"metric":goal["metric"],"target":goal["target"],"current":total,"complete":total>=goal["target"],"authors":dict(members)}
def news_config_recommender(config,signals):
 if not isinstance(config,dict) or not isinstance(signals,dict): raise ValueError("invalid news configuration")
 rows=[]
 if signals.get("correction_rate",0)>.05 and not config.get("second_review"): rows.append({"setting":"second_review","value":True,"reason":"correction_rate","priority":100})
 if signals.get("breaking_volume",0)>10 and config.get("digest_interval",60)>15: rows.append({"setting":"digest_interval","value":15,"reason":"breaking_volume","priority":70})
 return rows
def news_config_tests(config):
 if not isinstance(config,dict): raise ValueError("invalid news config")
 checks={"desk":bool(config.get("desk")),"workflow":config.get("workflow") in {"single_review","double_review"},"source_minimum":isinstance(config.get("source_minimum"),int) and config["source_minimum"]>=1}
 return {"passed":all(checks.values()),"checks":checks,"failures":[k for k,v in checks.items() if not v]}

def _time(value):
 if isinstance(value,str): value=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
 if not isinstance(value,dt.datetime) or value.tzinfo is None: raise ValueError("aware datetime required")
 return value.astimezone(dt.timezone.utc)
def _iso(value): return _time(value).isoformat().replace("+00:00","Z")

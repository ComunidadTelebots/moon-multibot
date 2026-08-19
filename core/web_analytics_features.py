"""Analytics-specific Web contracts for future-0151..0170."""
import copy, hashlib, hmac, json, statistics
from core.web_creator_features import _iso
def analytics_forecast(series,horizon=1):
 if not isinstance(series,list) or len(series)<3 or any(not isinstance(x,(int,float)) for x in series) or not 1<=horizon<=30:raise ValueError("invalid analytics series")
 slope=(series[-1]-series[0])/(len(series)-1);return {"forecast":[round(series[-1]+slope*i,3) for i in range(1,horizon+1)],"slope":slope,"method":"linear_trend"}
def analytics_guided_setup(config):
 steps=[("source",bool(config.get("source"))),("metric",config.get("metric") in {"users","views","events","conversion"}),("window",config.get("window") in {"hour","day","week","month"})];return {"completed":[k for k,v in steps if v],"next":next((k for k,v in steps if not v),None),"ready":all(v for _,v in steps)}
def analytics_alert(metric,value,baseline,sensitivity=.2):
 if metric not in {"users","views","errors","conversion"} or not all(isinstance(x,(int,float)) for x in (value,baseline,sensitivity)) or baseline<0 or sensitivity<=0:raise ValueError("invalid analytics alert")
 delta=value-baseline;return {"metric":metric,"triggered":abs(delta)>max(1,abs(baseline)*sensitivity),"delta":delta,"relative":None if baseline==0 else delta/baseline}
def analytics_automation(rule,snapshot):
 if rule.get("operator") not in {"gt","lt","eq"} or rule.get("action") not in {"notify","snapshot","open_report"}:raise ValueError("invalid analytics rule")
 val=snapshot.get(rule.get("metric"));target=rule.get("value");matched={"gt":lambda:val>target,"lt":lambda:val<target,"eq":lambda:val==target}[rule["operator"]]()
 return {"matched":matched,"planned":[rule["action"]] if matched else [],"executed":False}
def analytics_compare(current,previous):
 if set(current)!=set(previous) or any(not isinstance(x,(int,float)) for x in [*current.values(),*previous.values()]):raise ValueError("invalid analytics periods")
 return {k:{"delta":current[k]-previous[k],"percent":None if previous[k]==0 else round((current[k]-previous[k])*100/previous[k],2)} for k in sorted(current)}
def analytics_signed_export(dataset,secret):
 if not isinstance(dataset,list) or len(str(secret))<16:raise ValueError("invalid analytics export")
 body=json.dumps(dataset,sort_keys=True,separators=(",",":"));return {"rows":len(dataset),"digest":hashlib.sha256(body.encode()).hexdigest(),"signature":hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest(),"body":body}
def analytics_simulation(query,dataset):
 if query.get("aggregate") not in {"sum","mean","count"} or not isinstance(dataset,list):raise ValueError("invalid analytics simulation")
 vals=[x.get(query.get("field")) for x in dataset if isinstance(x.get(query.get("field")),(int,float))];value=len(vals) if query["aggregate"]=="count" else sum(vals) if query["aggregate"]=="sum" else statistics.mean(vals) if vals else None
 return {"result":value,"matched_rows":len(vals),"saved":False,"effects":[]}
def analytics_version(history,definition,actor,now):
 if not isinstance(definition,dict) or not definition.get("metric"):raise ValueError("invalid metric definition")
 digest=hashlib.sha256(json.dumps(definition,sort_keys=True).encode()).hexdigest()
 if history and history[-1]["digest"]==digest:return copy.deepcopy(history)
 return copy.deepcopy(history)+[{"version":len(history)+1,"definition":copy.deepcopy(definition),"actor":actor,"at":_iso(now),"digest":digest}]
def analytics_search(query,catalog):
 terms=set(str(query).lower().split());rows=[]
 for x in catalog:
  words=set(f'{x.get("name","")} {x.get("description","")} {x.get("dimension","")}'.lower().split());score=len(terms&words)
  if score:rows.append({"metric_id":x["id"],"score":score,"matched":sorted(terms&words)})
 return sorted(rows,key=lambda x:(-x["score"],x["metric_id"]))
def analytics_summary(dataset):
 if not isinstance(dataset,list):raise ValueError("invalid analytics dataset")
 numeric={}
 for row in dataset:
  for k,v in row.items():
   if isinstance(v,(int,float)):numeric.setdefault(k,[]).append(v)
 return {"rows":len(dataset),"metrics":{k:{"sum":sum(v),"mean":statistics.mean(v),"min":min(v),"max":max(v)} for k,v in sorted(numeric.items())},"raw_rows_included":False}
def analytics_permission(policy,actor,dataset,action):
 if action not in {"read","query","export","configure"}:raise ValueError("invalid analytics permission")
 allowed=action in policy.get(actor,{}).get(dataset,[]) if isinstance(policy,dict) else False;return {"allowed":allowed,"dataset":dataset,"reason":"dataset_grant" if allowed else "default_deny"}
def analytics_template(name,dimensions,metrics,filters=None):
 if not str(name).strip() or not isinstance(dimensions,list) or not isinstance(metrics,list) or not metrics or len(metrics)!=len(set(metrics)):raise ValueError("invalid analytics template")
 return {"name":name.strip(),"dimensions":list(dimensions),"metrics":list(metrics),"filters":copy.deepcopy(filters or {}),"reusable":True}
def analytics_bulk_plan(definitions,enabled):
 if not isinstance(enabled,bool) or len({x.get("id") for x in definitions})!=len(definitions):raise ValueError("invalid analytics bulk")
 return {"operations":[{"metric_id":x["id"],"before":bool(x.get("enabled")),"after":enabled} for x in definitions],"undo_available":True,"applied":False}
def analytics_calendar(jobs,timezone):
 if "/" not in str(timezone):raise ValueError("invalid analytics calendar")
 rows=sorted(({"job_id":x["job_id"],"run_at":_iso(x["run_at"]),"report":x["report"]} for x in jobs),key=lambda x:x["run_at"]);return {"timezone":timezone,"jobs":rows,"next_run":rows[0]["run_at"] if rows else None,"executed":False}
def analytics_privacy(dataset,k=3):
 if not isinstance(dataset,list) or not isinstance(k,int) or k<2:raise ValueError("invalid analytics privacy")
 groups={}
 for x in dataset:groups[x.get("segment")]=groups.get(x.get("segment"),0)+1
 return {"segments":{str(key):count for key,count in groups.items() if count>=k},"suppressed":sum(count for count in groups.values() if count<k),"k":k,"identities_included":False}
def analytics_diagnostics(pipeline):
 checks={"source":pipeline.get("source_status")=="up","freshness":pipeline.get("lag_minutes",999)<=60,"schema":pipeline.get("schema_valid") is True,"errors":pipeline.get("error_rate",1)<.05};return {"healthy":all(checks.values()),"checks":checks,"failures":[k for k,v in checks.items() if not v]}
def analytics_recommendations(metrics):
 rows=[]
 if metrics.get("error_rate",0)>.05:rows.append({"action":"inspect_errors","score":100,"because":"high_error_rate"})
 if metrics.get("lag_minutes",0)>60:rows.append({"action":"refresh_pipeline","score":90,"because":"stale_data"})
 return sorted(rows,key=lambda x:-x["score"])
def analytics_approval(request,reviewer,decision,now):
 if request.get("status")!="pending" or request.get("kind") not in {"metric","export","dashboard"} or decision not in {"approved","rejected"} or reviewer==request.get("requested_by"):raise ValueError("invalid analytics approval")
 return {**copy.deepcopy(request),"status":decision,"reviewer":reviewer,"at":_iso(now)}
def analytics_comment(thread,comment):
 if not comment.get("metric_id") or not str(comment.get("text","")).strip() or any(x.get("id")==comment.get("id") for x in thread):raise ValueError("invalid analytics comment")
 return copy.deepcopy(thread)+[{"id":comment["id"],"metric_id":comment["metric_id"],"text":comment["text"].strip(),"resolved":False}]
def analytics_metric(state,event):
 if event.get("type") not in {"query","export","refresh","pipeline_error"} or not event.get("id"):raise ValueError("invalid analytics event")
 out=copy.deepcopy(state or {"seen":[],"counts":{}})
 if event["id"] in out["seen"]:return out
 out["seen"].append(event["id"]);out["counts"][event["type"]]=out["counts"].get(event["type"],0)+1;return out

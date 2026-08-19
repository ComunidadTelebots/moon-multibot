"""WebApp contracts for future-0993..1000 and future-1668..1679."""
from collections import Counter, defaultdict
from datetime import datetime, timezone

def configurable_ai_density(mode="comfortable", columns=1):
 sizes={"compact":36,"comfortable":48,"spacious":60}; return {"mode":mode if mode in sizes else "comfortable","row_height_px":sizes.get(mode,48),"columns":max(1,min(int(columns),4))}
def selective_ai_recovery(snapshot, current, sections):
 result=dict(current); applied=[]
 for key in sections:
  if key in snapshot: result[key]=snapshot[key]; applied.append(key)
 return {"state":result,"sections":applied,"applied":bool(applied)}
def schedule_ai_report(schedule, metrics, recipient):
 return {"schedule":schedule,"metrics":list(dict.fromkeys(metrics)),"recipient":recipient,"status":"scheduled" if schedule and recipient else "draft"}
def sandbox_ai_test(policy, sample):
 denied=[k for k in sample if k not in set(policy.get("allowed_fields",sample))]; return {"valid":not denied,"denied_fields":denied,"executed":False}
def interoperable_ai_connector(records, schema=None):
 schema=schema or {}; normalized=[{schema.get(k,k):v for k,v in r.items()} for r in records]; return {"preview":normalized,"count":len(normalized),"import_applied":False}
def notification_forecast(history, horizon=1):
 values=[float(x) for x in history]; trend=(values[-1]-values[0])/max(1,len(values)-1) if values else 0; base=values[-1] if values else 0; return {"forecast":[round(base+trend*i,2) for i in range(1,max(0,horizon)+1)],"trend":trend}
def guided_notification_setup(config):
 steps=[("channel",bool(config.get("channel"))),("quiet_hours",bool(config.get("quiet_hours"))),("test",bool(config.get("tested")))]; return {"next_step":next((k for k,done in steps if not done),None),"complete":all(done for _,done in steps)}
def adaptive_notification_alert(event, preferences):
 severity=event.get("severity","low"); muted=severity in set(preferences.get("muted_severities",())); return {"notify":not muted,"channel":preferences.get("critical_channel","push") if severity=="critical" else preferences.get("channel","in_app"),"automatic_action":False}
def functional_dependency_map(nodes, edges):
 graph={n:[] for n in nodes}
 for source,target in edges:
  graph.setdefault(source,[]).append(target); graph.setdefault(target,[])
 return {"graph":graph,"roots":[n for n in graph if not any(n in targets for targets in graph.values())]}
def visual_conditional_rules(rules, context):
 matched=[r for r in rules if all(context.get(k)==v for k,v in r.get("when",{}).items())]; return {"matched":matched,"effects":[r.get("effect") for r in matched]}
def unified_review_inbox(items, assignee=None):
 visible=[x for x in items if assignee is None or x.get("assignee")==assignee]; return {"items":sorted(visible,key=lambda x:x.get("priority",0),reverse=True),"pending":sum(x.get("status")!="resolved" for x in visible)}
def detect_sensitive_changes(before, after, sensitive_fields=()):
 changed=[k for k in set(before)|set(after) if before.get(k)!=after.get(k)]; return {"changed":changed,"sensitive":[k for k in changed if k in set(sensitive_fields)],"requires_review":any(k in sensitive_fields for k in changed)}
def explain_automatic_decision(decision, signals):
 ranked=sorted(signals,key=lambda x:abs(x.get("weight",0)),reverse=True); return {"decision":decision,"reasons":[x.get("name") for x in ranked],"weights":[x.get("weight",0) for x in ranked]}
def data_quality_panel(records, required_fields):
 missing=Counter(k for r in records for k in required_fields if r.get(k) in (None,"")); total=max(1,len(records)*max(1,len(required_fields))); return {"records":len(records),"missing":dict(missing),"completeness":1-sum(missing.values())/total}
def preview_import(records, required_fields):
 valid=[]; errors=[]
 for index,row in enumerate(records):
  absent=[k for k in required_fields if row.get(k) in (None,"")]; (errors if absent else valid).append({"index":index,"missing":absent} if absent else row)
 return {"valid":valid,"errors":errors,"applied":False}
def collaborative_comments(comments):
 threads=defaultdict(list)
 for c in comments: threads[c.get("thread","general")].append(c)
 return {"threads":dict(threads),"participants":sorted({c.get("author") for c in comments if c.get("author")})}
def smart_tags(item, vocabulary):
 text=str(item.get("text","")).lower(); tags=[tag for tag in vocabulary if tag.lower() in text]; return {"tags":tags,"suggested":True,"applied":False}
def configurable_activity_summary(events, options):
 selected=set(options.get("types",[])); visible=[e for e in events if not selected or e.get("type") in selected]; return {"total":len(visible),"by_type":dict(Counter(e.get("type","unknown") for e in visible)),"events":visible[:options.get("limit",10)]}
def expiry_alerts(items, now=None, warning_seconds=86400):
 now=datetime.now(timezone.utc).timestamp() if now is None else now; alerts=[x for x in items if x.get("expires_at") is not None and 0<=x["expires_at"]-now<=warning_seconds]; return {"alerts":alerts,"count":len(alerts)}
def reversible_emergency_mode(state, enabled, actor):
 previous=bool(state.get("emergency",False)); updated=dict(state); updated["emergency"]=bool(enabled); return {"state":updated,"audit":{"actor":actor,"before":previous,"after":bool(enabled)},"undo":{"emergency":previous}}

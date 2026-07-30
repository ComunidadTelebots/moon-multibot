"""Web analytics/privacy contracts for future-0171..0190."""
import copy, hashlib, hmac, json, statistics
from urllib.parse import urlparse
from core.web_creator_features import _iso
def analytics_accessibility(config):
 if config.get("table_fallback") is not True or config.get("palette") not in {"standard","colorblind","high_contrast"}:raise ValueError("invalid analytics accessibility")
 return {"palette":config["palette"],"table_fallback":True,"text_labels":True,"animation":not bool(config.get("reduced_motion"))}
def analytics_webhook(url,event,snapshot,secret):
 if event not in {"metric.threshold","report.ready","pipeline.failed"} or urlparse(str(url)).scheme!="https" or len(str(secret))<16:raise ValueError("invalid analytics webhook")
 body=json.dumps(snapshot,sort_keys=True,separators=(",",":"));return {"url":url,"event":event,"body":body,"signature":hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest(),"sent":False}
def analytics_anomaly(points):
 if len(points)<4 or any(not isinstance(x,(int,float)) for x in points):raise ValueError("invalid analytics anomaly series")
 base=points[:-1];median=statistics.median(base);mad=statistics.median(abs(x-median) for x in base);score=abs(points[-1]-median)/max(1,mad)
 return {"anomaly":score>3.5,"median":median,"mad":mad,"robust_score":score}
def analytics_learning(completed,track):
 tracks={"basic":["metrics","filters","charts"],"advanced":["cohorts","funnels","privacy"]}
 if track not in tracks or set(completed)-set(tracks[track]):raise ValueError("invalid analytics learning")
 left=[x for x in tracks[track] if x not in completed];return {"track":track,"next":left[0] if left else None,"completed":not left}
def analytics_language(language,dimensions):
 required={"date","value","total"}
 if language not in {"es","en","ca","ar"} or set(dimensions)!=required:raise ValueError("invalid analytics language")
 return {"language":language,"dimensions":copy.deepcopy(dimensions),"direction":"rtl" if language=="ar" else "ltr","number_locale":language}
def analytics_compact(snapshot,metrics):
 if not metrics or len(metrics)!=len(set(metrics)) or any(k not in snapshot for k in metrics):raise ValueError("invalid analytics compact")
 return {"metrics":{k:snapshot[k] for k in metrics},"density":"compact","raw_data_included":False}
def analytics_recovery(current,snapshot,definitions):
 if not definitions or any(k not in snapshot for k in definitions):raise ValueError("invalid analytics recovery")
 return {"restore":{k:copy.deepcopy(snapshot[k]) for k in definitions},"before":{k:copy.deepcopy(current.get(k)) for k in definitions},"applied":False}
def analytics_report(config,data):
 if config.get("frequency") not in {"daily","weekly","monthly"} or config.get("format") not in {"json","csv"}:raise ValueError("invalid analytics report")
 return {"frequency":config["frequency"],"format":config["format"],"rows":len(data),"digest":hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest(),"delivered":False}
def analytics_sandbox(query,dataset):
 if query.get("operation") not in {"filter","group","aggregate"} or not isinstance(dataset,list):raise ValueError("invalid analytics sandbox")
 return {"operation":query["operation"],"input_rows":len(dataset),"sample":copy.deepcopy(dataset[:10]),"writes":0,"effects":[]}
def analytics_connector(dataset,standard):
 if standard not in {"openmetrics","csv-schema","json-stat"} or not isinstance(dataset,list):raise ValueError("invalid analytics connector")
 return {"standard":standard,"rows":len(dataset),"schema":sorted(set().union(*(x.keys() for x in dataset))) if dataset else [],"credentials_included":False}
def privacy_forecast(records,retention_days,now):
 if not isinstance(records,list) or not isinstance(retention_days,int) or retention_days<1:raise ValueError("invalid retention forecast")
 instant=_parse(now);expired=[x["id"] for x in records if (instant-_parse(x["created_at"])).days>=retention_days]
 return {"expire_count":len(expired),"record_ids":expired,"retention_days":retention_days,"deleted":False}
def privacy_guided_setup(settings):
 steps=[("consent",settings.get("consent_recorded")),("retention",isinstance(settings.get("retention_days"),int)),("export",settings.get("export_enabled") is not None)];return {"next":next((k for k,v in steps if not v),None),"completed":[k for k,v in steps if v],"ready":all(v for _,v in steps)}
def privacy_alert(event,policy):
 if event.get("type") not in {"export","access","deletion","consent_change"} or event["type"] not in policy:raise ValueError("invalid privacy alert")
 triggered=event.get("count",1)>=policy[event["type"]];return {"triggered":triggered,"type":event["type"],"threshold":policy[event["type"]],"contains_pii":False}
def privacy_automation(rule,event):
 if rule.get("trigger") not in {"retention_due","consent_revoked","export_requested"} or rule.get("action") not in {"plan_delete","freeze_processing","prepare_export"}:raise ValueError("invalid privacy automation")
 matched=event.get("type")==rule["trigger"];return {"matched":matched,"plan":[rule["action"]] if matched else [],"executed":False,"requires_confirmation":True}
def privacy_compare(current,previous):
 keys={"stored_records","active_consents","pending_deletions"}
 if set(current)!=keys or set(previous)!=keys:raise ValueError("invalid privacy periods")
 return {k:{"delta":current[k]-previous[k],"current":current[k],"previous":previous[k]} for k in sorted(keys)}
def privacy_signed_export(subject,data,secret):
 if not str(subject) or not isinstance(data,dict) or len(str(secret))<16:raise ValueError("invalid privacy export")
 body=json.dumps({"subject":subject,"data":data},sort_keys=True,separators=(",",":"));return {"subject":subject,"body":body,"digest":hashlib.sha256(body.encode()).hexdigest(),"signature":hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest()}
def privacy_simulation(records,fields):
 if not isinstance(records,list) or not fields:raise ValueError("invalid privacy simulation")
 preview=[{k:("[redacted]" if k in fields else copy.deepcopy(v)) for k,v in x.items()} for x in records];return {"preview":preview,"redacted_fields":sorted(fields),"source_mutated":False,"applied":False}
def privacy_version(history,policy,actor,now):
 if not isinstance(policy,dict) or not isinstance(policy.get("retention_days"),int):raise ValueError("invalid privacy policy")
 digest=hashlib.sha256(json.dumps(policy,sort_keys=True).encode()).hexdigest()
 if history and history[-1]["digest"]==digest:return copy.deepcopy(history)
 return copy.deepcopy(history)+[{"version":len(history)+1,"policy":copy.deepcopy(policy),"actor":actor,"at":_iso(now),"digest":digest}]
def privacy_search(query,records):
 allowed={"consent","retention","export","deletion"}
 if query not in allowed or not isinstance(records,list):raise ValueError("invalid privacy search")
 return [{"id":x["id"],"type":x.get("type"),"status":x.get("status")} for x in records if x.get("type")==query]
def privacy_summary(records):
 if not isinstance(records,list):raise ValueError("invalid privacy records")
 counts={}
 for x in records:counts[x.get("type","unknown")]=counts.get(x.get("type","unknown"),0)+1
 return {"total":len(records),"counts":dict(sorted(counts.items())),"identities_included":False,"method":"exact_event_counts"}
def _parse(v):
 import datetime as dt
 if isinstance(v,str):v=dt.datetime.fromisoformat(v.replace("Z","+00:00"))
 if v.tzinfo is None:raise ValueError("aware datetime required")
 return v

"""Dashboard-specific Web contracts for future-0131..0150."""
import copy, hashlib, hmac, json, statistics
from urllib.parse import urlparse
from core.web_creator_features import _iso
def dashboard_permission(policy,role,widget,action):
 if action not in {"view","configure","export"}:raise ValueError("invalid dashboard action")
 grants=policy.get(role,{}) if isinstance(policy,dict) else {};allowed=action in grants.get(widget,[]);return {"allowed":allowed,"widget":widget,"reason":"widget_grant" if allowed else "default_deny"}
def dashboard_template(name,widgets,columns):
 if not str(name).strip() or not isinstance(widgets,list) or len(widgets)!=len(set(widgets)) or columns not in {1,2,3,4}:raise ValueError("invalid dashboard template")
 return {"name":name.strip(),"widgets":list(widgets),"columns":columns,"reusable":True}
def dashboard_bulk_plan(widgets,visibility):
 if not isinstance(visibility,bool) or len({x.get("id") for x in widgets})!=len(widgets):raise ValueError("invalid dashboard bulk")
 return {"operations":[{"widget":x["id"],"before":bool(x.get("visible")),"after":visibility} for x in widgets],"undo_available":True,"applied":False}
def dashboard_calendar(events,timezone):
 if "/" not in str(timezone):raise ValueError("invalid dashboard calendar")
 rows=sorted(({"id":x["id"],"at":_iso(x["at"]),"kind":x["kind"]} for x in events),key=lambda x:x["at"]);return {"timezone":timezone,"events":rows,"next":rows[0] if rows else None,"actions_executed":False}
def dashboard_privacy(snapshot):
 banned={"user_ids","emails","tokens","ip_addresses"}
 if not isinstance(snapshot,dict):raise ValueError("invalid dashboard snapshot")
 return {"snapshot":{k:copy.deepcopy(v) for k,v in snapshot.items() if k not in banned},"removed":sorted(set(snapshot)&banned),"pii_included":False}
def dashboard_diagnostics(state):
 checks={"api":state.get("api_status")=="up","database":state.get("db_status")=="up","bots":state.get("active_bots",0)>0,"queue":state.get("queue_depth",0)<1000};return {"healthy":all(checks.values()),"checks":checks,"failures":[k for k,v in checks.items() if not v]}
def dashboard_recommendations(state):
 rows=[]
 if state.get("queue_depth",0)>100:rows.append({"action":"review_queue","score":90,"because":"queue_pressure"})
 if state.get("incidents",0)>0:rows.append({"action":"open_incidents","score":100,"because":"active_incidents"})
 return sorted(rows,key=lambda x:-x["score"])
def dashboard_approval(request,reviewer,decision,now):
 if request.get("status")!="pending" or request.get("kind") not in {"layout","widget","export"} or decision not in {"approved","rejected"} or reviewer==request.get("requested_by"):raise ValueError("invalid dashboard approval")
 return {**copy.deepcopy(request),"status":decision,"reviewer":reviewer,"at":_iso(now)}
def dashboard_comment(comments,comment):
 if comment.get("widget_id") is None or not str(comment.get("text","")).strip() or any(x.get("id")==comment.get("id") for x in comments):raise ValueError("invalid dashboard comment")
 return copy.deepcopy(comments)+[{"id":comment["id"],"widget_id":comment["widget_id"],"text":comment["text"].strip(),"resolved":False}]
def dashboard_metric(state,event):
 if event.get("type") not in {"widget_view","refresh","export","error"} or not event.get("id"):raise ValueError("invalid dashboard metric")
 out=copy.deepcopy(state or {"seen":[],"counts":{}})
 if event["id"] in out["seen"]:return out
 out["seen"].append(event["id"]);out["counts"][event["type"]]=out["counts"].get(event["type"],0)+1;return out
def dashboard_accessibility(config):
 if config.get("landmarks") is not True or config.get("contrast") not in {"normal","high"} or config.get("font_scale") not in {1,1.25,1.5,2}:raise ValueError("invalid dashboard accessibility")
 return {"landmarks":True,"contrast":config["contrast"],"font_scale":config["font_scale"],"keyboard_navigation":True}
def dashboard_webhook(url,event,snapshot,secret):
 if event not in {"dashboard.incident","dashboard.health_changed","dashboard.export_ready"} or urlparse(str(url)).scheme!="https" or len(str(secret))<16:raise ValueError("invalid dashboard webhook")
 body=json.dumps(snapshot,sort_keys=True,separators=(",",":"));return {"url":url,"event":event,"signature":hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest(),"body":body,"sent":False}
def dashboard_anomaly(samples):
 if len(samples)<3 or any(not isinstance(x,(int,float)) for x in samples):raise ValueError("invalid dashboard samples")
 baseline=statistics.median(samples[:-1]);deviation=abs(samples[-1]-baseline);return {"anomaly":deviation>max(10,abs(baseline)*2),"baseline":baseline,"latest":samples[-1],"deviation":deviation}
def dashboard_learning(completed,role):
 paths={"viewer":["navigation","filters"],"operator":["alerts","queue","incidents"],"admin":["security","exports","audit"]}
 if role not in paths or set(completed)-set(paths[role]):raise ValueError("invalid dashboard learning")
 left=[x for x in paths[role] if x not in completed];return {"role":role,"next":left[0] if left else None,"certified":not left}
def dashboard_language(language,labels):
 required={"healthy","warning","critical"}
 if language not in {"es","en","ca","ar"} or set(labels)!=required:raise ValueError("invalid dashboard language")
 return {"language":language,"labels":copy.deepcopy(labels),"direction":"rtl" if language=="ar" else "ltr"}
def dashboard_compact(snapshot,metrics):
 allowed={"active_bots","pending_tasks","incidents","users_online"}
 if not isinstance(metrics,list) or not metrics or set(metrics)-allowed:raise ValueError("invalid compact dashboard")
 return {"metrics":{k:snapshot.get(k) for k in metrics},"density":"compact","details_included":False}
def dashboard_recovery(current,snapshot,widgets):
 if not isinstance(widgets,list) or set(widgets)-set(snapshot):raise ValueError("invalid dashboard recovery")
 return {"restore":{k:copy.deepcopy(snapshot[k]) for k in widgets},"before":{k:copy.deepcopy(current.get(k)) for k in widgets},"applied":False}
def dashboard_report(config,snapshot):
 if config.get("frequency") not in {"daily","weekly","monthly"} or config.get("format") not in {"json","csv"}:raise ValueError("invalid dashboard report")
 public={k:v for k,v in snapshot.items() if k not in {"user_ids","tokens"}};return {"frequency":config["frequency"],"format":config["format"],"snapshot":public,"delivered":False}
def dashboard_sandbox(state,operation):
 if operation.get("type") not in {"reorder","hide","show"}:raise ValueError("invalid dashboard sandbox")
 after=copy.deepcopy(state);wid=operation.get("widget_id")
 if operation["type"]=="reorder":after["widgets"]=operation.get("widgets",[])
 else:after.setdefault("visibility",{})[wid]=operation["type"]=="show"
 return {"before":copy.deepcopy(state),"after":after,"effects":[],"saved":False}
def dashboard_connector(snapshot,standard):
 if standard not in {"openmetrics","json-dashboard","activitystreams"}:raise ValueError("invalid dashboard connector")
 public={k:v for k,v in snapshot.items() if isinstance(v,(int,float,bool,str)) and "token" not in k};return {"standard":standard,"resource":"dashboard","data":public,"secrets_included":False}

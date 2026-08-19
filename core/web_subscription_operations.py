"""Subscription-specific Web contracts for future-0311..0330."""
import copy,hashlib,hmac,json,statistics
from urllib.parse import urlparse
from core.web_creator_features import _iso
def subscription_permission(policy,actor,plan,action):
 if action not in {"view","subscribe","manage","refund"}:raise ValueError("invalid subscription action")
 allowed=action in policy.get(actor,{}).get(plan,[]) if isinstance(policy,dict) else False;return {"allowed":allowed,"plan":plan,"reason":"plan_grant" if allowed else "default_deny"}
def subscription_template(name,price_cents,interval,benefits):
 if not str(name).strip() or not isinstance(price_cents,int) or price_cents<0 or interval not in {"monthly","quarterly","yearly"} or not isinstance(benefits,list):raise ValueError("invalid plan template")
 return {"name":name.strip(),"price_cents":price_cents,"interval":interval,"benefits":list(benefits),"reusable":True}
def subscription_bulk_plan(rows,status):
 if status not in {"active","paused","cancelled"} or len({x.get("id") for x in rows})!=len(rows):raise ValueError("invalid subscription bulk")
 return {"operations":[{"id":x["id"],"before":x.get("status"),"after":status} for x in rows],"undo_available":status!="cancelled","requires_confirmation":True,"applied":False}
def subscription_calendar(renewals,timezone):
 if "/" not in str(timezone):raise ValueError("invalid renewal calendar")
 rows=sorted(({"subscription_id":x["subscription_id"],"renew_at":_iso(x["renew_at"])} for x in renewals),key=lambda x:x["renew_at"]);return {"timezone":timezone,"renewals":rows,"next_run":rows[0]["renew_at"] if rows else None,"charged":False}
def subscription_privacy(row):
 if not isinstance(row,dict):raise ValueError("invalid subscription")
 banned={"card_token","email","billing_address","payment_customer_id"};return {"subscription":{k:copy.deepcopy(v) for k,v in row.items() if k not in banned},"removed":sorted(set(row)&banned),"payment_data_included":False}
def subscription_diagnostics(state):
 checks={"payments":state.get("payment_provider")=="up","renewals":state.get("renewal_worker")=="up","webhooks":state.get("webhook_lag_minutes",999)<10,"failures":state.get("failure_rate",1)<.05};return {"healthy":all(checks.values()),"checks":checks,"failures":[k for k,v in checks.items() if not v]}
def subscription_recommendations(row):
 rows=[]
 if row.get("failed_payments",0)>0:rows.append({"action":"update_payment_method","score":100,"because":"payment_failure"})
 if row.get("unused_days",0)>30:rows.append({"action":"offer_pause","score":70,"because":"low_usage"})
 return sorted(rows,key=lambda x:-x["score"])
def subscription_approval(request,reviewer,decision,now):
 if request.get("status")!="pending" or request.get("kind") not in {"refund","discount","plan_change"} or decision not in {"approved","rejected"} or reviewer==request.get("requested_by"):raise ValueError("invalid subscription approval")
 return {**copy.deepcopy(request),"status":decision,"reviewer":reviewer,"at":_iso(now)}
def subscription_comment(thread,comment):
 if not comment.get("subscription_id") or not str(comment.get("text","")).strip() or any(x.get("id")==comment.get("id") for x in thread):raise ValueError("invalid subscription comment")
 return copy.deepcopy(thread)+[{"id":comment["id"],"subscription_id":comment["subscription_id"],"text":comment["text"].strip(),"internal":bool(comment.get("internal")),"resolved":False}]
def subscription_metric(state,event):
 if event.get("type") not in {"started","renewed","cancelled","payment_failed"} or not event.get("id"):raise ValueError("invalid subscription metric")
 out=copy.deepcopy(state or {"seen":[],"counts":{}})
 if event["id"] in out["seen"]:return out
 out["seen"].append(event["id"]);out["counts"][event["type"]]=out["counts"].get(event["type"],0)+1;return out
def subscription_accessibility(config):
 if config.get("price_breakdown") is not True or config.get("renewal_labels") is not True:raise ValueError("invalid subscription accessibility")
 return {"price_breakdown":True,"renewal_labels":True,"keyboard_navigation":True,"color_only_status":False}
def subscription_webhook(url,event,row,secret):
 if event not in {"subscription.started","subscription.renewed","subscription.cancelled"} or urlparse(str(url)).scheme!="https" or len(str(secret))<16:raise ValueError("invalid subscription webhook")
 body=json.dumps({k:row.get(k) for k in ("id","plan","status","renewal_at")},sort_keys=True);return {"event":event,"body":body,"signature":hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest(),"payment_data_included":False,"sent":False}
def subscription_anomaly(values):
 if len(values)<4 or any(not isinstance(x,(int,float)) for x in values):raise ValueError("invalid subscription samples")
 baseline=statistics.median(values[:-1]);return {"anomaly":abs(values[-1]-baseline)>max(5,abs(baseline)*.5),"baseline":baseline,"latest":values[-1]}
def subscription_learning(done,role):
 tracks={"subscriber":["plans","renewal","cancel"],"operator":["payments","refunds","churn"]}
 if role not in tracks or set(done)-set(tracks[role]):raise ValueError("invalid subscription learning")
 left=[x for x in tracks[role] if x not in done];return {"next":left[0] if left else None,"certified":not left}
def subscription_language(language,labels):
 required={"active","paused","cancelled"}
 if language not in {"es","en","ca","ar"} or set(labels)!=required:raise ValueError("invalid subscription language")
 return {"language":language,"labels":copy.deepcopy(labels),"direction":"rtl" if language=="ar" else "ltr"}
def subscription_compact(row,fields):
 allowed={"id","plan","status","renewal_at","price_cents"}
 if not fields or set(fields)-allowed:raise ValueError("invalid compact subscription")
 return {"fields":{k:row.get(k) for k in fields},"payment_data_included":False}
def subscription_recovery(current,snapshot,fields):
 allowed={"plan","status","renewal_at","auto_renew"}
 if not fields or set(fields)-allowed or any(k not in snapshot for k in fields):raise ValueError("invalid subscription recovery")
 return {"restore":{k:copy.deepcopy(snapshot[k]) for k in fields},"before":{k:copy.deepcopy(current.get(k)) for k in fields},"charged":False,"applied":False}
def subscription_report(config,rows):
 if config.get("frequency") not in {"daily","weekly","monthly"} or config.get("format") not in {"json","csv"}:raise ValueError("invalid subscription report")
 return {"frequency":config["frequency"],"subscriptions":len(rows),"active":sum(x.get("status")=="active" for x in rows),"revenue_cents":sum(x.get("revenue_cents",0) for x in rows),"payment_data_included":False,"delivered":False}
def subscription_sandbox(row,operation):
 if operation.get("type") not in {"change_plan","pause","cancel"}:raise ValueError("invalid subscription sandbox")
 after=copy.deepcopy(row);after["plan" if operation["type"]=="change_plan" else "status"]=operation.get("plan") if operation["type"]=="change_plan" else operation["type"]+"d" if operation["type"]=="pause" else "cancelled"
 return {"before":copy.deepcopy(row),"after":after,"charges":0,"effects":[]}
def subscription_connector(rows,standard):
 if standard not in {"stripe-json","portable-subscriptions","billing-csv"}:raise ValueError("invalid subscription connector")
 safe=[{k:x.get(k) for k in ("id","plan","status","renewal_at")} for x in rows];return {"standard":standard,"subscriptions":safe,"payment_data_included":False,"exported":False}

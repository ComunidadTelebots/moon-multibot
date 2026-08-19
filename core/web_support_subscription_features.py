"""Web support/subscription contracts for future-0291..0310."""
import copy,hashlib,hmac,json,statistics
from urllib.parse import urlparse
from core.web_creator_features import _iso
def support_accessibility(c):
 if c.get("plain_language") is not True or c.get("status_labels") is not True:raise ValueError("invalid support accessibility")
 return {"plain_language":True,"status_labels":True,"keyboard_navigation":True,"color_only":False}
def support_webhook(url,event,ticket,secret):
 if event not in {"ticket.created","ticket.escalated","ticket.resolved"} or urlparse(str(url)).scheme!="https" or len(str(secret))<16:raise ValueError("invalid support webhook")
 body=json.dumps({k:ticket.get(k) for k in ("id","category","priority","status")},sort_keys=True);return {"event":event,"body":body,"signature":hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest(),"requester_included":False,"sent":False}
def support_anomaly(waits):
 if len(waits)<4:raise ValueError("invalid wait series")
 baseline=statistics.median(waits[:-1]);return {"anomaly":waits[-1]>max(30,baseline*3),"baseline":baseline,"latest":waits[-1]}
def support_learning(done,role):
 tracks={"agent":["triage","reply","resolve"],"lead":["sla","escalation","quality"]}
 if role not in tracks or set(done)-set(tracks[role]):raise ValueError("invalid support learning")
 left=[x for x in tracks[role] if x not in done];return {"next":left[0] if left else None,"certified":not left}
def support_language(lang,labels):
 req={"open","pending","resolved"}
 if lang not in {"es","en","ca","ar"} or set(labels)!=req:raise ValueError("invalid support language")
 return {"language":lang,"labels":copy.deepcopy(labels),"direction":"rtl" if lang=="ar" else "ltr"}
def support_compact(ticket,fields):
 allowed={"id","subject","category","priority","status","wait_minutes"}
 if not fields or set(fields)-allowed:raise ValueError("invalid compact ticket")
 return {"fields":{k:ticket.get(k) for k in fields},"requester_included":False}
def support_recovery(current,snapshot,fields):
 allowed={"category","priority","status","assignee","tags"}
 if not fields or set(fields)-allowed or any(k not in snapshot for k in fields):raise ValueError("invalid ticket recovery")
 return {"restore":{k:copy.deepcopy(snapshot[k]) for k in fields},"before":{k:copy.deepcopy(current.get(k)) for k in fields},"applied":False}
def support_report(config,tickets):
 if config.get("frequency") not in {"daily","weekly","monthly"} or config.get("format") not in {"json","csv"}:raise ValueError("invalid support report")
 return {"frequency":config["frequency"],"tickets":len(tickets),"resolved":sum(x.get("status")=="resolved" for x in tickets),"requesters_included":False,"delivered":False}
def support_sandbox(ticket,op):
 if op.get("type") not in {"assign","escalate","resolve"}:raise ValueError("invalid support sandbox")
 after=copy.deepcopy(ticket)
 if op["type"]=="assign":after["assignee"]=op.get("assignee")
 else:after["status"]="escalated" if op["type"]=="escalate" else "resolved"
 return {"before":copy.deepcopy(ticket),"after":after,"notifications":0,"effects":[]}
def support_connector(tickets,standard):
 if standard not in {"zendesk-json","freshdesk-csv","portable-tickets"}:raise ValueError("invalid support connector")
 rows=[{k:x.get(k) for k in ("id","subject","category","status")} for x in tickets];return {"standard":standard,"tickets":rows,"requester_data_included":False,"exported":False}
def subscription_forecast(counts):
 if len(counts)<3 or any(not isinstance(x,int) or x<0 for x in counts):raise ValueError("invalid subscription series")
 slope=(counts[-1]-counts[0])/(len(counts)-1);return {"next_active":max(0,round(counts[-1]+slope)),"net_growth":slope}
def subscription_guided(plan):
 checks=[("name",bool(plan.get("name"))),("price",isinstance(plan.get("price_cents"),int) and plan["price_cents"]>=0),("benefits",bool(plan.get("benefits"))),("terms",bool(plan.get("terms_url")))];return {"next":next((k for k,v in checks if not v),None),"completed":[k for k,v in checks if v],"ready":all(v for _,v in checks)}
def subscription_alert(metric,value,policy):
 if metric not in {"churn","failed_payments","renewals","active"} or metric not in policy:raise ValueError("invalid subscription alert")
 bad=value<=policy[metric] if metric in {"renewals","active"} else value>=policy[metric];return {"metric":metric,"triggered":bad,"value":value,"threshold":policy[metric]}
def subscription_automation(rule,event):
 if rule.get("trigger") not in {"payment_failed","renewal_due","cancelled"} or rule.get("action") not in {"notify","retry","offer_help"}:raise ValueError("invalid subscription automation")
 matched=event.get("type")==rule["trigger"];return {"matched":matched,"plan":[rule["action"]] if matched else [],"charged":False}
def subscription_compare(current,previous):
 keys={"active","new","cancelled","revenue_cents"}
 if set(current)!=keys or set(previous)!=keys:raise ValueError("invalid subscription periods")
 return {k:{"delta":current[k]-previous[k]} for k in sorted(keys)}
def subscription_signed_export(rows,secret):
 if len(str(secret))<16:raise ValueError("invalid subscription export")
 safe=[{k:x.get(k) for k in ("id","plan","status","started_at")} for x in rows];body=json.dumps(safe,sort_keys=True);return {"body":body,"signature":hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest(),"payment_data_included":False}
def subscription_simulation(sub,change):
 if change.get("field") not in {"plan","status","renewal_at"}:raise ValueError("invalid subscription simulation")
 after=copy.deepcopy(sub);after[change["field"]]=change.get("value");return {"before":copy.deepcopy(sub),"after":after,"charged":False,"applied":False}
def subscription_version(history,plan,actor,now):
 digest=hashlib.sha256(json.dumps(plan,sort_keys=True).encode()).hexdigest()
 if history and history[-1]["digest"]==digest:return copy.deepcopy(history)
 return copy.deepcopy(history)+[{"version":len(history)+1,"plan":copy.deepcopy(plan),"actor":actor,"at":_iso(now),"digest":digest}]
def subscription_search(query,plans):
 terms=set(str(query).lower().split());rows=[]
 for p in plans:
  words=set(f'{p.get("name","")} {" ".join(p.get("benefits",[]))}'.lower().split());score=len(terms&words)
  if score:rows.append({"plan_id":p["id"],"score":score})
 return sorted(rows,key=lambda x:(-x["score"],x["plan_id"]))
def subscription_summary(rows):
 statuses={}
 for x in rows:statuses[x.get("status","unknown")]=statuses.get(x.get("status","unknown"),0)+1
 return {"subscriptions":len(rows),"statuses":dict(sorted(statuses.items())),"revenue_cents":sum(x.get("revenue_cents",0) for x in rows),"payment_data_included":False}

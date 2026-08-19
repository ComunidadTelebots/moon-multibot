"""Support-specific Web contracts for future-0271..0290."""
import copy, hashlib, hmac, json, statistics
from core.web_creator_features import _iso
def support_forecast(backlog):
 if len(backlog)<3 or any(not isinstance(x,int) or x<0 for x in backlog):raise ValueError("invalid backlog")
 slope=(backlog[-1]-backlog[0])/(len(backlog)-1);return {"next_backlog":max(0,round(backlog[-1]+slope)),"growing":slope>0,"slope":slope}
def support_guided(ticket):
 checks=[("subject",bool(ticket.get("subject"))),("description",len(ticket.get("description",""))>=10),("category",ticket.get("category") in {"account","billing","technical","abuse"}),("contact",bool(ticket.get("contact_hash")))];return {"completed":[k for k,v in checks if v],"next":next((k for k,v in checks if not v),None),"ready":all(v for _,v in checks)}
def support_alert(metric,value,policy):
 if metric not in {"backlog","wait_minutes","breaches","satisfaction"} or metric not in policy:raise ValueError("invalid support alert")
 bad=value<=policy[metric] if metric=="satisfaction" else value>=policy[metric];return {"metric":metric,"triggered":bad,"value":value,"threshold":policy[metric]}
def support_automation(rule,ticket):
 if rule.get("field") not in {"category","priority","status"} or rule.get("action") not in {"assign","escalate","suggest_reply"}:raise ValueError("invalid support automation")
 matched=ticket.get(rule["field"])==rule.get("equals");return {"matched":matched,"plan":[{"action":rule["action"],"target":rule.get("target")}] if matched else [],"executed":False}
def support_compare(current,previous):
 keys={"opened","resolved","median_wait","satisfaction"}
 if set(current)!=keys or set(previous)!=keys:raise ValueError("invalid support periods")
 return {k:{"delta":current[k]-previous[k],"improved":current[k]>=previous[k] if k in {"resolved","satisfaction"} else current[k]<=previous[k]} for k in sorted(keys)}
def support_signed_export(tickets,secret):
 if not isinstance(tickets,list) or len(str(secret))<16:raise ValueError("invalid support export")
 safe=[{k:x.get(k) for k in ("id","category","priority","status","created_at")} for x in tickets];body=json.dumps(safe,sort_keys=True);return {"body":body,"signature":hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest(),"requester_data_included":False}
def support_simulation(ticket,change):
 if change.get("field") not in {"priority","category","assignee","status"}:raise ValueError("invalid support simulation")
 after=copy.deepcopy(ticket);after[change["field"]]=change.get("value");return {"before":copy.deepcopy(ticket),"after":after,"notifications_sent":False,"applied":False}
def support_version(history,ticket,actor,now):
 public={k:ticket.get(k) for k in ("id","category","priority","status","assignee")};digest=hashlib.sha256(json.dumps(public,sort_keys=True).encode()).hexdigest()
 if history and history[-1]["digest"]==digest:return copy.deepcopy(history)
 return copy.deepcopy(history)+[{"version":len(history)+1,"ticket":public,"actor":actor,"at":_iso(now),"digest":digest}]
def support_search(query,tickets):
 terms=set(str(query).lower().split());rows=[]
 for x in tickets:
  words=set(f'{x.get("subject","")} {x.get("category","")} {" ".join(x.get("tags",[]))}'.lower().split());score=len(terms&words)
  if score:rows.append({"ticket_id":x["id"],"score":score,"matched":sorted(terms&words)})
 return sorted(rows,key=lambda x:(-x["score"],x["ticket_id"]))
def support_summary(tickets):
 if not isinstance(tickets,list):raise ValueError("invalid tickets")
 statuses={}
 for x in tickets:statuses[x.get("status","unknown")]=statuses.get(x.get("status","unknown"),0)+1
 waits=[x["wait_minutes"] for x in tickets if isinstance(x.get("wait_minutes"),(int,float))];return {"tickets":len(tickets),"statuses":dict(sorted(statuses.items())),"median_wait":statistics.median(waits) if waits else None,"requester_data_included":False}
def support_permission(policy,actor,queue,action):
 if action not in {"view","reply","assign","close"}:raise ValueError("invalid support permission")
 allowed=action in policy.get(actor,{}).get(queue,[]) if isinstance(policy,dict) else False;return {"allowed":allowed,"queue":queue,"reason":"queue_grant" if allowed else "default_deny"}
def support_template(name,subject,body,variables):
 if not str(name).strip() or not str(subject).strip() or not str(body).strip() or not isinstance(variables,list) or len(variables)!=len(set(variables)):raise ValueError("invalid support template")
 return {"name":name.strip(),"subject":subject,"body":body,"variables":variables,"reusable":True}
def support_bulk_plan(tickets,status):
 if status not in {"open","pending","resolved","closed"} or len({x.get("id") for x in tickets})!=len(tickets):raise ValueError("invalid support bulk")
 return {"operations":[{"id":x["id"],"before":x.get("status"),"after":status} for x in tickets],"undo_available":True,"applied":False}
def support_calendar(shifts,timezone):
 if "/" not in str(timezone):raise ValueError("invalid support calendar")
 rows=sorted(({"agent":x["agent"],"starts_at":_iso(x["starts_at"]),"ends_at":_iso(x["ends_at"])} for x in shifts),key=lambda x:x["starts_at"]);return {"timezone":timezone,"shifts":rows,"next_shift":rows[0] if rows else None,"assignments_sent":False}
def support_privacy(ticket):
 if not isinstance(ticket,dict):raise ValueError("invalid ticket")
 banned={"email","phone","ip","name","auth_token"};return {"ticket":{k:copy.deepcopy(v) for k,v in ticket.items() if k not in banned},"removed":sorted(set(ticket)&banned),"requester_identity_included":False}
def support_diagnostics(state):
 checks={"queue":state.get("queue_online") is True,"sla":state.get("breached",1)==0,"agents":state.get("available_agents",0)>0,"delivery":state.get("delivery_status")=="up"};return {"healthy":all(checks.values()),"checks":checks,"failures":[k for k,v in checks.items() if not v]}
def support_recommendations(ticket):
 rows=[]
 if ticket.get("wait_minutes",0)>60:rows.append({"action":"escalate","score":100,"because":"long_wait"})
 if not ticket.get("category"):rows.append({"action":"classify","score":80,"because":"missing_category"})
 return sorted(rows,key=lambda x:-x["score"])
def support_approval(request,reviewer,decision,now):
 if request.get("status")!="pending" or request.get("kind") not in {"refund","closure","escalation"} or decision not in {"approved","rejected"} or reviewer==request.get("requested_by"):raise ValueError("invalid support approval")
 return {**copy.deepcopy(request),"status":decision,"reviewer":reviewer,"at":_iso(now)}
def support_comment(thread,comment):
 if not comment.get("ticket_id") or not str(comment.get("text","")).strip() or any(x.get("id")==comment.get("id") for x in thread):raise ValueError("invalid support comment")
 return copy.deepcopy(thread)+[{"id":comment["id"],"ticket_id":comment["ticket_id"],"text":comment["text"].strip(),"internal":bool(comment.get("internal")),"resolved":False}]
def support_metric(state,event):
 if event.get("type") not in {"opened","replied","resolved","reopened"} or not event.get("id"):raise ValueError("invalid support metric")
 out=copy.deepcopy(state or {"seen":[],"counts":{}})
 if event["id"] in out["seen"]:return out
 out["seen"].append(event["id"]);out["counts"][event["type"]]=out["counts"].get(event["type"],0)+1;return out

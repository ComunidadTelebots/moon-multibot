"""Security-tail and AI WebApp contracts, future-0953..0972."""
import re
from collections import Counter
def diagnose_security_posture(state):#953
 checks={"mfa":state.get("mfa") is True,"sessions":state.get("unknown_sessions",1)==0,"secrets":state.get("exposed_secrets",1)==0,"audit":state.get("audit_available") is True}
 return {"resource":"security_posture","healthy":all(checks.values()),"checks":checks,"repair_executed":False}
def recommend_security_controls(config,signals):#954
 rows=[]
 if signals.get("unknown_sessions",0):rows.append({"control":"revoke_unknown_sessions","because":"unknown_sessions"})
 if signals.get("failed_logins",0)>=3 and not config.get("mfa"):rows.append({"control":"enable_mfa","because":"failed_logins"})
 return {"resource":"security_controls","recommendations":rows,"applied":False}
def approve_security_exception(exception,decisions):#955
 latest={x["actor"]:x["decision"] for x in decisions};approve=sum(v=="approve" for v in latest.values());reject=any(v=="reject" for v in latest.values());required=2
 return {"resource":"security_exception","exception_id":exception.get("id"),"status":"rejected" if reject else "approved" if approve>=required else "pending","approvals":approve,"required":required}
def security_collaboration(events):#956
 rows=sorted(events,key=lambda x:x["at"]);actors=Counter(str(x.get("actor")) for x in rows)
 return {"resource":"security_collaboration","events":rows,"contributors":dict(actors),"open_handoffs":sum(x.get("type")=="handoff" and not x.get("accepted") for x in rows)}
class SecurityMetrics:#957
 def __init__(self,limit=100):self.limit=limit;self.rows=[]
 def record(self,at,incidents,blocked):
  if incidents<0 or blocked<0 or blocked>incidents:raise ValueError("invalid metrics")
  self.rows.append({"at":at,"incidents":incidents,"blocked":blocked});self.rows=self.rows[-self.limit:];return {"resource":"security_metrics","samples":len(self.rows),"block_rate":blocked/max(1,incidents)}
def accessible_security_notice(event):#958
 severity=str(event.get("severity","unknown"));message=" ".join(str(event.get("message","")).split())
 if not message:raise ValueError("message required")
 return {"resource":"accessible_security_notice","plain_text":f"{severity.upper()}: {message}","aria_live":"assertive" if severity in {"high","critical"} else "polite","color_only":False}
def security_webhook(url,event):#959
 allowed={"incident_opened","session_revoked","policy_changed"}
 if not str(url).startswith("https://") or event.get("type") not in allowed:raise ValueError("invalid webhook")
 return {"resource":"security_event_delivery","url":url,"payload":event,"signature_required":True,"delivered":False}
def detect_security_anomaly(events):#960
 actors=Counter(x.get("actor") for x in events if x.get("type") in {"failed_login","permission_change"});findings=[{"actor":a,"events":n} for a,n in actors.items() if n>=5]
 return {"resource":"security_events","anomalies":findings,"automatic_lock":False}
def security_learning(role,completed):#961
 paths={"member":["sessions","mfa"],"admin":["sessions","mfa","incident_response","audit"]};lessons=paths.get(role,[]);done=set(completed)
 return {"resource":"security_learning","lessons":lessons,"resume":next((x for x in lessons if x not in done),None),"completed":len(done&set(lessons))}
def security_language(language,messages):#962
 code=str(language).lower().replace("_","-").split("-")[0]
 if code not in {"es","en","fr","de","it","pt","ar","tr"}:raise ValueError("unsupported language")
 return {"resource":"security_language","language":code,"direction":"rtl" if code=="ar" else "ltr","missing_messages":[x["id"] for x in messages if code not in x.get("translations",{})]}
def security_density(mode,event_count):#963
 if mode not in {"comfortable","compact"} or event_count<0:raise ValueError("invalid density")
 return {"resource":"security_event_list","mode":mode,"row_height_px":44 if mode=="compact" else 60,"count":event_count,"minimum_target_px":44}
def recover_security_sections(current,snapshot,sections):#964
 safe={"notifications","filters","templates","trusted_devices"};chosen=set(sections)
 if not chosen<=safe:raise ValueError("unsafe section")
 after=dict(current);after.update({k:snapshot[k] for k in chosen if k in snapshot});return {"resource":"security_recovery","preview":after,"restored":sorted(chosen&snapshot.keys()),"applied":False}
def schedule_security_report(hour,metrics,recipient):#965
 if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",hour) or not recipient:raise ValueError("invalid report")
 allowed={"incidents","sessions","permissions","anomalies"}
 if not metrics or not set(metrics)<=allowed:raise ValueError("invalid metrics")
 return {"resource":"security_report","hour":hour,"metrics":list(dict.fromkeys(metrics)),"recipient":recipient,"status":"scheduled"}
def sandbox_security_policy(event,policy):#966
 matched=all(event.get(k)==v for k,v in policy.get("when",{}).items());return {"resource":"security_sandbox","matched":matched,"would_plan":policy.get("then",[]) if matched else [],"executed":False,"automatic_ban":False}
def security_connector(events,version=1):#967
 allowed=("id","type","severity","status","created_at");rows=[{k:x[k] for k in allowed if k in x} for x in events]
 return {"resource":"security_interchange","format":"moon.webapp.security","version":version,"events":rows,"import_applied":False}
def forecast_ai_demand(samples):#968
 vals=[int(x) for x in samples]
 if len(vals)<2 or any(x<0 for x in vals):raise ValueError("samples required")
 rate=(vals[-1]-vals[0])/(len(vals)-1);return {"resource":"ai_request_demand","next_period":max(0,round(vals[-1]+rate)),"trend":"rising" if rate>0 else "falling" if rate<0 else "stable"}
def next_ai_setup_task(config):#969
 checks=("provider","model","privacy_review","limits");pending=[x for x in checks if not config.get(x)]
 return {"resource":"ai_setup","next_task":pending[0] if pending else None,"remaining":len(pending),"ready":not pending}
def adaptive_ai_alert(request,signals):#970
 score=int(signals.get("prompt_injection",False))*5+int(signals.get("sensitive_data",False))*4+int(signals.get("cost_spike",False))*3
 return {"resource":"ai_risk_alert","request_id":request.get("id"),"risk_score":min(10,score),"block_recommended":score>=7,"automatic_block":False}
def ai_automation_plan(event,rules):#971
 matches=[r for r in rules if r.get("enabled") and all(event.get(k)==v for k,v in r.get("when",{}).items())];safe={"notify","queue_review","redact"}
 return {"resource":"ai_automation","matched":[r["id"] for r in matches],"planned":[a for r in matches for a in r.get("then",[]) if a in safe],"executed":False}
def compare_ai_periods(current,previous):#972
 fields={"requests","tokens","errors","reviewed"}
 if not fields<=current.keys() or not fields<=previous.keys():raise ValueError("metrics incomplete")
 return {"resource":"ai_periods","delta":{k:int(current[k])-int(previous[k]) for k in sorted(fields)},"error_rate":current["errors"]/max(1,current["requests"])}

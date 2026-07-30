"""Mobile-moderation tail and content contracts, future-0893..0912."""
import re
from collections import Counter
def diagnose_mobile_moderation(state):#893
 checks={"session":state.get("session_valid") is True,"permissions":state.get("permissions_loaded") is True,"queue":state.get("queue_error") is None,"clock":abs(state.get("clock_skew",999))<60}
 return {"resource":"mobile_moderation_health","healthy":all(checks.values()),"checks":checks,"repair_executed":False}
def recommend_mobile_moderation(config,metrics):#894
 rows=[]
 if metrics.get("queue_age",0)>1800:rows.append({"field":"priority_sort","value":"oldest_first","because":"stale_queue"})
 if metrics.get("reversal_rate",0)>.1:rows.append({"field":"require_second_review","value":True,"because":"reversals"})
 return {"resource":"mobile_moderation_settings","recommendations":rows,"applied":False}
def approve_mobile_appeal(appeal,decisions):#895
 latest={x["actor"]:x["decision"] for x in decisions};approve=sum(v=="approve" for v in latest.values());reject=any(v=="reject" for v in latest.values());required=2 if appeal.get("original_action")=="ban" else 1
 return {"resource":"mobile_appeal","status":"rejected" if reject else "approved" if approve>=required else "pending","approvals":approve,"required":required}
def mobile_moderation_collaboration(events):#896
 rows=sorted(events,key=lambda x:x["at"]);actors=Counter(str(x.get("actor")) for x in rows)
 return {"resource":"mobile_moderation_collaboration","events":rows,"contributors":dict(actors),"pending_handoffs":sum(x.get("type")=="handoff" and not x.get("accepted") for x in rows)}
class MobileModerationMetrics:#897
 def __init__(self,limit=100):self.limit=limit;self.rows=[]
 def record(self,at,pending,resolved):
  if pending<0 or resolved<0:raise ValueError("invalid metrics")
  self.rows.append({"at":at,"pending":pending,"resolved":resolved});self.rows=self.rows[-self.limit:];return {"resource":"mobile_moderation_metrics","latest":self.rows[-1],"samples":len(self.rows)}
def accessible_mobile_case(case):#898
 target=str(case.get("target_name") or "Usuario");reason=" ".join(str(case.get("reason") or "Sin motivo").split());severity=str(case.get("severity","unknown"))
 return {"resource":"accessible_mobile_case","heading":f"Caso de {target}","plain_text":f"Severidad {severity}. {reason}.","aria_live":"assertive" if severity=="critical" else "polite","color_only":False}
def mobile_moderation_webhook(url,event):#899
 allowed={"case_assigned","decision_recorded","appeal_opened"}
 if not str(url).startswith("https://") or event.get("type") not in allowed:raise ValueError("invalid webhook")
 return {"resource":"mobile_moderation_event","url":url,"payload":event,"signature_required":True,"delivered":False}
def detect_mobile_moderation_anomaly(events):#900
 actors=Counter(x.get("actor") for x in events if x.get("action") in {"ban","override"});findings=[{"actor":a,"sensitive_actions":n} for a,n in actors.items() if n>=5]
 return {"resource":"mobile_moderation_events","anomalies":findings,"automatic_revoke":False}
def mobile_moderation_learning(role,completed):#901
 paths={"moderator":["evidence","proportionality","appeals"],"admin":["evidence","proportionality","appeals","oversight"]};lessons=paths.get(role,[]);done=set(completed)
 return {"resource":"mobile_moderation_learning","lessons":lessons,"resume":next((x for x in lessons if x not in done),None),"completed":len(done&set(lessons))}
def mobile_moderation_language(language,reasons):#902
 code=str(language).lower().replace("_","-").split("-")[0]
 if code not in {"es","en","fr","de","it","pt","ar","tr"}:raise ValueError("unsupported language")
 missing=[x["id"] for x in reasons if code not in x.get("translations",{})];return {"resource":"mobile_moderation_language","language":code,"direction":"rtl" if code=="ar" else "ltr","missing_reasons":missing}
def mobile_moderation_density(mode,count):#903
 if mode not in {"comfortable","compact"} or count<0:raise ValueError("invalid density")
 return {"resource":"mobile_case_list","mode":mode,"card_gap_px":8 if mode=="compact" else 16,"count":count,"minimum_target_px":44}
def recover_mobile_moderation(current,snapshot,sections):#904
 safe={"filters","templates","assignments","preferences"};chosen=set(sections)
 if not chosen<=safe:raise ValueError("unsafe section")
 after=dict(current);after.update({k:snapshot[k] for k in chosen if k in snapshot});return {"resource":"mobile_moderation_recovery","preview":after,"restored":sorted(chosen&snapshot.keys()),"applied":False}
def schedule_mobile_moderation_report(hour,metrics,recipient):#905
 if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",hour) or not recipient:raise ValueError("invalid report")
 allowed={"queue","decisions","appeals","reversals"}
 if not metrics or not set(metrics)<=allowed:raise ValueError("invalid metrics")
 return {"resource":"mobile_moderation_report","hour":hour,"metrics":list(dict.fromkeys(metrics)),"recipient":recipient,"status":"scheduled"}
def sandbox_mobile_moderation(case,decision):#906
 if decision not in {"warn","mute","ban","dismiss"}:raise ValueError("invalid decision")
 risks=[] if case.get("evidence_reviewed") else ["missing_evidence_review"];return {"resource":"mobile_moderation_sandbox","case_id":case.get("id"),"decision":decision,"risks":risks,"executed":False}
def mobile_moderation_connector(cases,version=1):#907
 allowed=("id","status","decision","reason_code","created_at");rows=[{k:x[k] for k in allowed if k in x} for x in cases]
 return {"resource":"mobile_moderation_interchange","format":"moon.webapp.mobile-moderation","version":version,"cases":rows,"import_applied":False}
def forecast_content_queue(samples):#908
 values=[int(x) for x in samples]
 if len(values)<2 or any(x<0 for x in values):raise ValueError("samples required")
 rate=(values[-1]-values[0])/(len(values)-1);return {"resource":"content_queue","next_size":max(0,round(values[-1]+rate)),"trend":"growing" if rate>0 else "shrinking" if rate<0 else "stable"}
def next_content_task(item):#909
 steps=[]
 if not item.get("title"):steps.append("add_title")
 if not item.get("accessibility_reviewed"):steps.append("review_accessibility")
 if not item.get("moderation_reviewed"):steps.append("review_moderation")
 return {"resource":"content_workflow","content_id":item.get("id"),"next_task":steps[0] if steps else None,"remaining":len(steps)}
def adaptive_content_alert(item,signals):#910
 score=int(signals.get("reports",0))+int(signals.get("malware",False))*5+int(signals.get("copyright_matches",0))*2
 return {"resource":"content_alert","content_id":item.get("id"),"risk_score":min(10,score),"severity":"critical" if score>=7 else "warning" if score>=3 else "info","automatic_remove":False}
def content_automation_plan(item,rules):#911
 matches=[r for r in rules if r.get("enabled") and all(item.get(k)==v for k,v in r.get("when",{}).items())]
 return {"resource":"content_automation","matched":[r["id"] for r in matches],"planned":[a for r in matches for a in r.get("then",[])],"executed":False,"review_required":True}
def compare_content_periods(current,previous):#912
 fields={"created","published","rejected","archived"}
 if not fields<=current.keys() or not fields<=previous.keys():raise ValueError("metrics incomplete")
 return {"resource":"content_periods","delta":{k:int(current[k])-int(previous[k]) for k in sorted(fields)},"publish_rate":current["published"]/max(1,current["created"])}

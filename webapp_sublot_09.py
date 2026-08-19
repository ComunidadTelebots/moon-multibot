"""Offline-tail and accessibility WebApp contracts, future-0833..0852."""
import re
from collections import Counter
def diagnose_offline_state(state):#833
 checks={"storage":state.get("storage_available") is True,"encrypted":state.get("encrypted") is True,"queue_valid":state.get("invalid_records",0)==0,"clock":state.get("clock_skew_seconds",999)<60}
 return {"resource":"offline_health","healthy":all(checks.values()),"checks":checks,"repair_executed":False}
def recommend_offline_settings(config,metrics):#834
 rows=[]
 if metrics.get("conflict_rate",0)>.1 and config.get("conflict_policy")!="review":rows.append({"field":"conflict_policy","value":"review","because":"conflicts"})
 if metrics.get("storage_percent",0)>80:rows.append({"field":"retention_days","value":7,"because":"storage_pressure"})
 return {"resource":"offline_settings","recommendations":rows,"applied":False}
def approve_offline_conflict(conflict,decisions):#835
 latest={x["actor"]:x["decision"] for x in decisions};valid={"local","remote","merge"};choices=[x for x in latest.values() if x in valid]
 return {"resource":"offline_conflict","conflict_id":conflict["id"],"status":"approved" if len(set(choices))==1 and choices else "pending","resolution":choices[0] if len(set(choices))==1 and choices else None}
def offline_collaboration(events):#836
 rows=sorted(events,key=lambda x:x["at"]);actors=Counter(str(x.get("actor")) for x in rows)
 return {"resource":"offline_collaboration","events":rows,"contributors":dict(actors),"unresolved":sum(x.get("status")=="conflict" for x in rows)}
class OfflineLiveMetrics:#837
 def __init__(self,limit=100):self.limit=limit;self.rows=[]
 def record(self,at,queued,storage_bytes):
  if queued<0 or storage_bytes<0:raise ValueError("invalid metric")
  self.rows.append({"at":at,"queued":queued,"storage_bytes":storage_bytes});self.rows=self.rows[-self.limit:];return {"resource":"offline_live_metrics","latest":self.rows[-1],"samples":len(self.rows)}
def accessible_offline_status(state):#838
 online=state.get("online") is True;queued=max(0,int(state.get("queued",0)));text=f"{'Con conexión' if online else 'Sin conexión'}. {queued} elementos pendientes."
 return {"resource":"accessible_offline_status","plain_text":text,"aria_live":"assertive" if not online and queued else "polite","icon_label":"online" if online else "offline","color_only":False}
def offline_webhook_plan(url,event):#839
 allowed={"sync_completed","conflict_detected","queue_failed"}
 if not str(url).startswith("https://") or event.get("type") not in allowed:raise ValueError("invalid webhook")
 return {"resource":"offline_event","url":url,"payload":event,"signature_required":True,"delivered":False,"queued_while_offline":True}
def detect_offline_anomaly(records):#840
 findings=[]
 duplicates=Counter(x.get("id") for x in records)
 findings.extend({"type":"duplicate_id","id":k,"count":v} for k,v in duplicates.items() if v>1)
 findings.extend({"type":"retry_loop","id":x.get("id"),"retries":x.get("retries")} for x in records if x.get("retries",0)>10)
 return {"resource":"offline_records","anomalies":findings,"automatic_delete":False}
def offline_learning(completed):#841
 lessons=["storage","privacy","sync","conflicts","recovery"];done=set(completed)
 return {"resource":"offline_learning","lessons":lessons,"resume":next((x for x in lessons if x not in done),None),"completed":len(done&set(lessons))}
def offline_language(language,messages):#842
 code=str(language).lower().replace("_","-").split("-")[0]
 if code not in {"es","en","fr","de","it","pt","ar","tr"}:raise ValueError("unsupported language")
 missing=[x["id"] for x in messages if code not in x.get("translations",{})];return {"resource":"offline_language","language":code,"direction":"rtl" if code=="ar" else "ltr","missing_messages":missing}
def offline_density(mode,queue_size):#843
 if mode not in {"comfortable","compact"} or queue_size<0:raise ValueError("invalid density")
 return {"resource":"offline_queue_view","mode":mode,"row_height_px":44 if mode=="compact" else 60,"queue_size":queue_size,"minimum_target_px":44}
def recover_offline_sections(current,snapshot,sections):#844
 safe={"preferences","queue","templates","conflict_policy"};chosen=set(sections)
 if not chosen<=safe:raise ValueError("unsafe section")
 after=dict(current);after.update({k:snapshot[k] for k in chosen if k in snapshot});return {"resource":"offline_recovery","preview":after,"restored":sorted(chosen&snapshot.keys()),"applied":False}
def schedule_offline_report(hour,metrics,recipient):#845
 if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",hour) or not recipient:raise ValueError("invalid report")
 allowed={"queue","conflicts","storage","failures"}
 if not metrics or not set(metrics)<=allowed:raise ValueError("invalid metrics")
 return {"resource":"offline_report","hour":hour,"metrics":list(dict.fromkeys(metrics)),"recipient":recipient,"status":"scheduled"}
def sandbox_offline_sync(records,policy):#846
 results=[]
 for x in records:results.append({"id":x["id"],"decision":"review" if x.get("conflict") and policy=="manual" else "sync"})
 return {"resource":"offline_sync_sandbox","results":results,"executed":False,"committed":False}
def offline_connector(records,version=1):#847
 allowed=("id","type","version","created_at","status");rows=[{k:x[k] for k in allowed if k in x} for x in records]
 return {"resource":"offline_interchange","format":"moon.webapp.offline","version":version,"records":rows,"import_applied":False}
def forecast_accessibility_barriers(audits):#848
 values=[int(x.get("barriers",0)) for x in audits]
 if len(values)<2 or any(x<0 for x in values):raise ValueError("audits required")
 velocity=(values[-1]-values[0])/(len(values)-1);return {"resource":"accessibility_barriers","next_audit":max(0,round(values[-1]+velocity)),"trend":"improving" if velocity<0 else "worsening" if velocity>0 else "stable"}
def next_accessibility_task(audit):#849
 order=("missing_labels","low_contrast","small_targets","motion","complex_language");pending=[x for x in order if audit.get(x,0)>0]
 return {"resource":"accessibility_tasks","next_task":pending[0] if pending else None,"remaining_categories":len(pending),"complete":not pending}
def adaptive_accessibility_alert(issue,user_preferences):#850
 severity=int(issue.get("severity",1));assertive=severity>=3 or issue.get("blocks_navigation")
 modalities=["text"]+( ["sound"] if user_preferences.get("sound") else [])+(["haptic"] if user_preferences.get("haptic") else [])
 return {"resource":"accessibility_alert","aria_live":"assertive" if assertive else "polite","modalities":modalities,"color_only":False}
def accessibility_automation_plan(audit,rules):#851
 planned=[]
 if audit.get("missing_alt",0):planned.append({"action":"request_alt_text","count":audit["missing_alt"]})
 if audit.get("small_targets",0) and rules.get("enforce_targets"):planned.append({"action":"raise_target_minimum","px":44})
 return {"resource":"accessibility_automation","planned_actions":planned,"executed":False,"human_review_required":True}
def compare_accessibility_audits(current,previous):#852
 fields={"missing_labels","contrast_failures","small_targets","motion_failures"}
 if not fields<=current.keys() or not fields<=previous.keys():raise ValueError("audit incomplete")
 delta={k:int(current[k])-int(previous[k]) for k in sorted(fields)};return {"resource":"accessibility_periods","delta":delta,"improved":sum(delta.values())<0}

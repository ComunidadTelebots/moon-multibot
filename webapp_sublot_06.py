"""WebApp alert-tail and quick-action contracts, future-0773..0792."""
import json,re
from collections import Counter
def diagnose_alert_pipeline(checks):#773
 required={"ingest","dedupe","routing","delivery"};failed=sorted(required-set(checks)|{k for k in required if checks.get(k) not in {True,"ok"}})
 return {"resource":"alert_pipeline","healthy":not failed,"failed_stages":failed,"repair_executed":False}
def recommend_alert_tuning(config,metrics):#774
 rows=[]
 if metrics.get("false_positive_rate",0)>.2:rows.append({"field":"threshold","value":min(1,float(config.get("threshold",.5))+.1),"because":"false_positives"})
 if metrics.get("unacknowledged",0)>10:rows.append({"field":"group_notifications","value":True,"because":"unacknowledged"})
 return {"resource":"alert_tuning","recommendations":rows,"applied":False}
def approve_alert_resolution(alert,decisions):#775
 latest={x["actor"]:x["decision"] for x in decisions};approved=sum(v=="resolve" for v in latest.values());rejected=any(v=="keep_open" for v in latest.values());required=2 if alert.get("severity")=="critical" else 1
 return {"resource":"alert_resolution","status":"open" if rejected else "resolved" if approved>=required else "pending","approvals":approved,"required":required}
def alert_collaboration_timeline(events):#776
 rows=sorted(events,key=lambda x:x["at"]);actors=Counter(str(x.get("actor")) for x in rows)
 return {"resource":"alert_collaboration","timeline":rows,"contributors":dict(actors),"latest":rows[-1] if rows else None}
class AlertLiveMetrics:#777
 def __init__(self,limit=120):self.limit=limit;self.rows=[]
 def record(self,at,open_count,oldest_seconds):
  if open_count<0 or oldest_seconds<0:raise ValueError("invalid alert metric")
  self.rows.append({"at":at,"open":open_count,"oldest_seconds":oldest_seconds});self.rows=self.rows[-self.limit:];return {"resource":"alert_live_metrics","latest":self.rows[-1],"samples":len(self.rows)}
def accessible_alert(alert):#778
 severity=str(alert.get("severity","unknown"));message=" ".join(str(alert.get("message","")).split())
 if not message:raise ValueError("message required")
 return {"resource":"accessible_alert","plain_text":f"{severity.upper()}: {message}","aria_live":"assertive" if severity in {"high","critical"} else "polite","icon_label":severity,"color_only":False}
def alert_delivery_webhook(url,alert,delivery_id):#779
 if not str(url).startswith("https://") or not alert.get("id") or not delivery_id:raise ValueError("invalid delivery")
 return {"resource":"alert_delivery","url":url,"delivery_id":str(delivery_id),"payload":{"alert_id":alert["id"],"severity":alert.get("severity")},"signature_required":True,"delivered":False}
def detect_alert_stream_anomaly(events,window):#780
 if window<=0:raise ValueError("window required")
 counts=Counter(x.get("fingerprint") for x in events);findings=[{"fingerprint":k,"count":v} for k,v in counts.items() if k and v>window]
 return {"resource":"alert_stream","anomalies":findings,"automatic_suppression":False}
def alert_learning_path(role,completed):#781
 catalog={"viewer":["read"],"operator":["read","triage","resolve"],"master":["read","triage","resolve","policy"]};lessons=catalog.get(role,[]);done=set(completed)
 return {"resource":"alert_learning","role":role,"lessons":lessons,"resume":next((x for x in lessons if x not in done),None),"completed":len(done&set(lessons))}
def alert_language(language,templates):#782
 code=str(language).lower().replace("_","-").split("-")[0]
 if code not in {"es","en","fr","de","it","pt","ar","tr"}:raise ValueError("unsupported language")
 missing=[x for x in templates if code not in x.get("translations",{})]
 return {"resource":"alert_language","language":code,"direction":"rtl" if code=="ar" else "ltr","missing_template_ids":[x["id"] for x in missing]}
def alert_density(mode,alert_count):#783
 if mode not in {"comfortable","compact"} or alert_count<0:raise ValueError("invalid density")
 return {"resource":"alert_list","mode":mode,"row_height_px":44 if mode=="compact" else 60,"alert_count":alert_count,"minimum_target_px":44}
def recover_alert_configuration(current,snapshot,sections):#784
 safe={"routing","thresholds","templates","notifications"};chosen=set(sections)
 if not chosen<=safe:raise ValueError("unsafe section")
 after=dict(current);after.update({k:snapshot[k] for k in chosen if k in snapshot});return {"resource":"alert_configuration","preview":after,"restored":sorted(chosen&snapshot.keys()),"applied":False}
def schedule_alert_report(hour,severities,recipient):#785
 if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",hour) or not recipient:raise ValueError("invalid report")
 allowed={"low","medium","high","critical"}
 if not severities or not set(severities)<=allowed:raise ValueError("invalid severity")
 return {"resource":"alert_report","hour":hour,"severities":list(dict.fromkeys(severities)),"recipient":recipient,"status":"scheduled"}
def sandbox_alert_policy(policy,sample):#786
 matched=all(sample.get(k)==v for k,v in policy.get("when",{}).items());planned=policy.get("then",[]) if matched else []
 return {"resource":"alert_policy_sandbox","matched":matched,"planned_actions":planned,"executed":False,"committed":False}
def alert_connector(alerts,version=1):#787
 allowed=("id","type","severity","status","created_at");rows=[{k:x[k] for k in allowed if k in x} for x in alerts]
 return {"resource":"alert_interchange","format":"moon.webapp.alerts","version":version,"alerts":rows,"import_applied":False}
def predict_quick_action_usage(samples,action_id):#788
 values=[int(x.get(action_id,0)) for x in samples]
 if len(values)<2 or any(x<0 for x in values):raise ValueError("samples required")
 velocity=(values[-1]-values[0])/(len(values)-1);return {"resource":"quick_action_usage","action_id":action_id,"next_period":max(0,round(values[-1]+velocity)),"method":"usage_velocity"}
def next_quick_action_setup(action):#789
 required=("label","permission","confirmation","result_message");missing=[x for x in required if action.get(x) in {None,""}]
 return {"resource":"quick_action_setup","action_id":action.get("id"),"next_step":f"configure:{missing[0]}" if missing else None,"missing":missing}
def adaptive_quick_action_warning(action,context):#790
 risk=int(action.get("risk",0));risk+=2 if context.get("shared_device") else 0;risk+=2 if context.get("bulk_target_count",0)>10 else 0
 return {"resource":"quick_action_risk","risk_score":min(10,risk),"require_confirmation":risk>=3,"require_reauth":risk>=6}
def quick_action_automation(trigger,actions):#791
 matched=[x for x in actions if x.get("enabled") and x.get("trigger")==trigger.get("type") and x.get("permission_checked")]
 return {"resource":"quick_action_automation","planned":[x["id"] for x in matched],"requires_confirmation":True,"executed":False}
def compare_quick_actions(current,previous):#792
 ids=sorted(set(current)|set(previous));rows=[{"action_id":x,"before":int(previous.get(x,0)),"after":int(current.get(x,0)),"delta":int(current.get(x,0))-int(previous.get(x,0))} for x in ids]
 return {"resource":"quick_action_periods","actions":rows,"total_delta":sum(x["delta"] for x in rows)}

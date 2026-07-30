"""WebApp profile-tail and alert contracts, future-0753..0772."""
import hashlib,hmac,json,re
from collections import Counter
def profile_density(mode,sections):#753
 if mode not in {"comfortable","compact"}:raise ValueError("invalid mode")
 return {"resource":"profile_layout","mode":mode,"section_gap":8 if mode=="compact" else 16,"sections":len(sections),"minimum_target_px":44}
def recover_profile_sections(current,snapshot,sections):#754
 safe={"preferences","visibility","notifications","bio"};chosen=set(sections)
 if not chosen<=safe:raise ValueError("unsafe section")
 after=dict(current);after.update({k:snapshot[k] for k in chosen if k in snapshot});return {"resource":"profile_recovery","preview":after,"restored":sorted(chosen&snapshot.keys()),"applied":False}
def schedule_profile_report(hour,sections,owner_id):#755
 if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",hour) or not owner_id:raise ValueError("invalid report")
 allowed={"security","privacy","activity"}
 if not sections or not set(sections)<=allowed:raise ValueError("invalid sections")
 return {"resource":"profile_report","hour":hour,"sections":list(dict.fromkeys(sections)),"owner_id":str(owner_id),"status":"scheduled"}
def sandbox_profile_changes(profile,changes):#756
 allowed={"display_name","bio","language","visibility"}
 if not set(changes)<=allowed:raise ValueError("unsupported field")
 clone=json.loads(json.dumps(profile));clone.update(changes);return {"resource":"profile_sandbox","result":clone,"original_unchanged":True,"committed":False}
def profile_connector(profile,version=1):#757
 allowed={k:profile[k] for k in ("id","display_name","language","visibility") if k in profile}
 return {"resource":"profile_interchange","format":"moon.webapp.profile","version":int(version),"profile":allowed,"ignored_fields":sorted(set(profile)-set(allowed)),"import_applied":False}
def forecast_alert_volume(daily_counts,horizon=3):#758
 vals=[int(x) for x in daily_counts]
 if len(vals)<2 or any(x<0 for x in vals):raise ValueError("counts required")
 rate=(vals[-1]-vals[0])/(len(vals)-1);return {"resource":"alert_volume","forecast":[max(0,round(vals[-1]+rate*i)) for i in range(1,horizon+1)],"method":"alert_velocity"}
def next_alert_triage_step(alert):#759
 steps=[]
 if not alert.get("classified"):steps.append("classify")
 if alert.get("severity") in {"high","critical"} and not alert.get("assigned_to"):steps.append("assign")
 if not alert.get("acknowledged"):steps.append("acknowledge")
 return {"resource":"alert_triage","alert_id":alert.get("id"),"next_step":steps[0] if steps else None,"remaining":len(steps)}
def adapt_alert_priority(alert,context):#760
 score={"low":1,"medium":2,"high":3,"critical":4}.get(alert.get("severity"),0)
 if context.get("repeat_count",0)>=3:score+=1
 if context.get("affected_users",0)>=100:score+=1
 return {"resource":"adaptive_alert","priority":min(5,score),"escalate":score>=4,"signals":{"repeat":context.get("repeat_count",0),"affected":context.get("affected_users",0)}}
def alert_automation_plan(alert,rules):#761
 matched=[r for r in rules if r.get("enabled") and all(alert.get(k)==v for k,v in r.get("when",{}).items())]
 return {"resource":"alert_automation","matched_rules":[r["id"] for r in matched],"planned_actions":[a for r in matched for a in r.get("then",[])],"executed":False}
def compare_alert_periods(current,previous):#762
 fields={"opened","resolved","escalated","false_positive"}
 if not fields<=current.keys() or not fields<=previous.keys():raise ValueError("metrics incomplete")
 return {"resource":"alert_periods","delta":{k:int(current[k])-int(previous[k]) for k in sorted(fields)},"resolution_rate":current["resolved"]/max(1,current["opened"])}
def sign_alert_export(alerts,key):#763
 if not isinstance(key,bytes) or len(key)<32:raise ValueError("key required")
 clean=[{k:x[k] for k in ("id","type","severity","status") if k in x} for x in alerts];body=json.dumps(clean,sort_keys=True,separators=(",",":"))
 return {"resource":"alert_export","alerts":clean,"signature":hmac.new(key,body.encode(),hashlib.sha256).hexdigest(),"algorithm":"HMAC-SHA256"}
def simulate_alert_rule(sample,rule):#764
 matched=all(sample.get(k)==v for k,v in rule.get("when",{}).items());return {"resource":"alert_rule_simulation","matched":matched,"would_plan":rule.get("then",[]) if matched else [],"executed":False}
class AlertHistory:#765
 def __init__(self):self.rows=[]
 def append(self,alert):
  state={k:alert.get(k) for k in ("id","severity","status","assigned_to")};digest=hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()
  if self.rows and self.rows[-1]["digest"]==digest:return {**self.rows[-1],"changed":False}
  row={"version":len(self.rows)+1,"state":state,"digest":digest};self.rows.append(row);return {**row,"changed":True}
def search_alerts(query,alerts):#766
 terms=set(re.findall(r"\w+",str(query).casefold()));rows=[]
 for a in alerts:
  words=set(re.findall(r"\w+",f"{a.get('type','')} {a.get('message','')} {a.get('severity','')}".casefold()));rows.append({"alert_id":a["id"],"score":len(terms&words)/max(1,len(terms))})
 return sorted(rows,key=lambda x:(-x["score"],str(x["alert_id"])))
def explain_alert_summary(alerts):#767
 severity=Counter(x.get("severity","unknown") for x in alerts);status=Counter(x.get("status","unknown") for x in alerts)
 return {"resource":"alert_summary","severity":dict(severity),"status":dict(status),"text":f"{len(alerts)} alertas; "+", ".join(f"{k}: {v}" for k,v in sorted(severity.items())),"source_count":len(alerts)}
def authorize_alert_action(role,alert,action):#768
 grants={"viewer":{"view"},"operator":{"view","acknowledge","assign"},"master":{"view","acknowledge","assign","resolve","delete"}}
 allowed=action in grants.get(role,set()) and (alert.get("severity")!="critical" or role=="master" or action=="view")
 return {"resource":"alert_permission","allowed":bool(allowed),"role":role,"action":action,"default_deny":True}
class AlertTemplates:#769
 def __init__(self):self.rows={}
 def save(self,name,template):
  allowed={"severity","message","routing","labels"}
  if not name or not set(template)<=allowed:raise ValueError("invalid template")
  self.rows[name]=json.loads(json.dumps(template));return {"name":name,"fields":sorted(template)}
 def instantiate(self,name,overrides=None):
  value=json.loads(json.dumps(self.rows[name]));value.update(overrides or {});return value
def plan_alert_batch(alerts,action):#770
 if action not in {"acknowledge","assign","archive"}:raise ValueError("unsafe action")
 before={str(x["id"]):x.get("status") for x in alerts};after={k:("acknowledged" if action=="acknowledge" else action+"d") for k in before}
 return {"resource":"alert_batch","action":action,"before":before,"after":after,"undo":before,"applied":False}
def alert_calendar(alerts,timezone):#771
 if not re.fullmatch(r"UTC|[A-Za-z_]+/[A-Za-z_]+",timezone):raise ValueError("timezone required")
 rows=sorted(({"id":x["id"],"at":x["due_at"],"severity":x.get("severity")} for x in alerts if x.get("due_at")),key=lambda x:x["at"])
 return {"resource":"alert_calendar","timezone":timezone,"events":rows,"unscheduled":len(alerts)-len(rows)}
def private_alert_view(alert):#772
 secret={"ip","email","phone","token","session_id"};data={k:("[redacted]" if k in secret else v) for k,v in alert.items()}
 return {"resource":"private_alert","data":data,"redacted_fields":sorted(set(alert)&secret),"privacy_mode":"reinforced"}

"""Content-tail and security WebApp contracts, future-0933..0952."""
import hashlib,hmac,json,re
from collections import Counter
def content_density(mode,count):#933
 if mode not in {"comfortable","compact"} or count<0:raise ValueError("invalid density")
 return {"resource":"content_list","mode":mode,"card_gap_px":8 if mode=="compact" else 16,"count":count,"minimum_target_px":44}
def recover_content(current,snapshot,sections):#934
 safe={"drafts","templates","tags","preferences"};chosen=set(sections)
 if not chosen<=safe:raise ValueError("unsafe section")
 after=dict(current);after.update({k:snapshot[k] for k in chosen if k in snapshot});return {"resource":"content_recovery","preview":after,"restored":sorted(chosen&snapshot.keys()),"applied":False}
def schedule_content_report(hour,metrics,recipient):#935
 if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",hour) or not recipient:raise ValueError("invalid report")
 allowed={"published","drafts","accessibility","moderation"}
 if not metrics or not set(metrics)<=allowed:raise ValueError("invalid metrics")
 return {"resource":"content_report","hour":hour,"metrics":list(dict.fromkeys(metrics)),"recipient":recipient,"status":"scheduled"}
def sandbox_content_transform(item,changes):#936
 allowed={"title","summary","tags","visibility"}
 if not set(changes)<=allowed:raise ValueError("unsupported field")
 clone=json.loads(json.dumps(item));clone.update(changes);return {"resource":"content_sandbox","result":clone,"published":False,"committed":False}
def content_connector(items,version=1):#937
 allowed=("id","title","type","status","version","tags");rows=[{k:x[k] for k in allowed if k in x} for x in items]
 return {"resource":"content_interchange","format":"moon.webapp.content","version":version,"items":rows,"import_applied":False}
def forecast_security_incidents(samples):#938
 vals=[int(x) for x in samples]
 if len(vals)<2 or any(x<0 for x in vals):raise ValueError("samples required")
 rate=(vals[-1]-vals[0])/(len(vals)-1);return {"resource":"security_incidents","next_period":max(0,round(vals[-1]+rate)),"trend":"rising" if rate>0 else "falling" if rate<0 else "stable"}
def next_security_task(posture):#939
 checks=("mfa","session_review","recovery_codes","audit_log");pending=[x for x in checks if not posture.get(x)]
 return {"resource":"security_setup","next_task":pending[0] if pending else None,"remaining":len(pending),"complete":not pending}
def adaptive_security_alert(event,context):#940
 score=int(event.get("risk",0));score+=3 if context.get("unknown_device") else 0;score+=2 if context.get("impossible_travel") else 0
 return {"resource":"security_alert","risk_score":min(10,score),"severity":"critical" if score>=7 else "warning" if score>=3 else "info","require_reauth":score>=5}
def security_automation_plan(event,rules):#941
 matches=[r for r in rules if r.get("enabled") and all(event.get(k)==v for k,v in r.get("when",{}).items())]
 safe_actions={"notify","revoke_session","require_reauth"};planned=[a for r in matches for a in r.get("then",[]) if a in safe_actions]
 return {"resource":"security_automation","matched":[r["id"] for r in matches],"planned":planned,"executed":False,"destructive_excluded":True}
def compare_security_periods(current,previous):#942
 fields={"incidents","blocked","false_positive","sessions_revoked"}
 if not fields<=current.keys() or not fields<=previous.keys():raise ValueError("metrics incomplete")
 return {"resource":"security_periods","delta":{k:int(current[k])-int(previous[k]) for k in sorted(fields)},"block_rate":current["blocked"]/max(1,current["incidents"])}
def sign_security_export(events,key):#943
 if not isinstance(key,bytes) or len(key)<32:raise ValueError("key required")
 rows=[{k:x[k] for k in ("id","type","severity","status","created_at") if k in x} for x in events];body=json.dumps(rows,sort_keys=True,separators=(",",":"))
 return {"resource":"security_export","events":rows,"signature":hmac.new(key,body.encode(),hashlib.sha256).hexdigest(),"algorithm":"HMAC-SHA256"}
def simulate_security_policy(event,policy):#944
 matched=all(event.get(k)==v for k,v in policy.get("when",{}).items());actions=policy.get("then",[]) if matched else []
 return {"resource":"security_policy_simulation","matched":matched,"would_plan":actions,"executed":False,"automatic_ban":False}
class SecurityHistory:#945
 def __init__(self):self.rows=[]
 def append(self,event):
  state={k:event.get(k) for k in ("id","type","severity","status")};digest=hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()
  if self.rows and self.rows[-1]["digest"]==digest:return {**self.rows[-1],"changed":False}
  row={"version":len(self.rows)+1,"state":state,"digest":digest};self.rows.append(row);return {**row,"changed":True}
def search_security_events(query,events):#946
 terms=set(re.findall(r"\w+",str(query).casefold()));rows=[]
 for x in events:
  words=set(re.findall(r"\w+",f"{x.get('type','')} {x.get('summary','')} {x.get('severity','')}".casefold()));rows.append({"event_id":x["id"],"score":len(terms&words)/max(1,len(terms))})
 return sorted(rows,key=lambda x:(-x["score"],str(x["event_id"])))
def explain_security_summary(events):#947
 severity=Counter(x.get("severity","unknown") for x in events);types=Counter(x.get("type","unknown") for x in events)
 return {"resource":"security_summary","severity":dict(severity),"types":dict(types),"text":f"{len(events)} eventos de seguridad","source_count":len(events)}
def authorize_security_action(role,event,action):#948
 grants={"viewer":{"view"},"operator":{"view","notify","revoke_session"},"master":{"view","notify","revoke_session","change_policy","dismiss"}}
 allowed=action in grants.get(role,set()) and (event.get("critical") is not True or role=="master" or action=="view")
 return {"resource":"security_permission","allowed":bool(allowed),"action":action,"default_deny":True}
class SecurityTemplates:#949
 def __init__(self):self.rows={}
 def save(self,name,template):
  allowed={"severity","conditions","notifications","reauth"}
  if not name or not set(template)<=allowed:raise ValueError("invalid template")
  self.rows[name]=json.loads(json.dumps(template));return {"name":name,"fields":sorted(template)}
 def preview(self,name,current):
  after=dict(current);after.update(self.rows[name]);return {"before":current,"after":after,"applied":False}
def plan_security_batch(events,operation):#950
 if operation not in {"acknowledge","assign","archive"}:raise ValueError("unsafe operation")
 before={str(x["id"]):x.get("status") for x in events};return {"resource":"security_batch","operation":operation,"event_ids":sorted(before),"undo":before,"executed":False}
def security_calendar(events,timezone):#951
 if not re.fullmatch(r"UTC|[A-Za-z_]+/[A-Za-z_]+",timezone):raise ValueError("timezone required")
 rows=sorted(({"id":x["id"],"at":x["review_at"]} for x in events if x.get("review_at")),key=lambda x:x["at"]);return {"resource":"security_calendar","timezone":timezone,"reviews":rows,"unscheduled":len(events)-len(rows)}
def private_security_event(event):#952
 secret={"ip","email","token","session_id","device_fingerprint"};data={k:("[redacted]" if k in secret else v) for k,v in event.items()}
 return {"resource":"private_security_event","data":data,"redacted_fields":sorted(set(event)&secret),"persistent_plaintext":False}

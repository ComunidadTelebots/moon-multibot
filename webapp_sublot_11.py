"""Accessibility-tail and mobile-moderation contracts, future-0873..0892."""
import hashlib,hmac,json,re
from collections import Counter
def accessibility_density(mode,issue_count):#873
 if mode not in {"comfortable","compact"} or issue_count<0:raise ValueError("invalid density")
 return {"resource":"accessibility_issue_list","mode":mode,"row_height_px":44 if mode=="compact" else 60,"issues":issue_count,"minimum_target_px":44}
def recover_accessibility_settings(current,snapshot,sections):#874
 safe={"text","contrast","motion","labels"};chosen=set(sections)
 if not chosen<=safe:raise ValueError("unsafe section")
 after=dict(current);after.update({k:snapshot[k] for k in chosen if k in snapshot});return {"resource":"accessibility_recovery","preview":after,"restored":sorted(chosen&snapshot.keys()),"applied":False}
def schedule_accessibility_report(hour,standards,recipient):#875
 if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",hour) or not standards or not recipient:raise ValueError("invalid report")
 return {"resource":"accessibility_report","hour":hour,"standards":sorted(set(standards)),"recipient":recipient,"status":"scheduled"}
def sandbox_accessibility_fix(issue,fix):#876
 allowed={"label","target_size","contrast","motion"}
 if fix.get("type") not in allowed:raise ValueError("unsupported fix")
 return {"resource":"accessibility_fix_sandbox","issue_id":issue.get("id"),"before":issue,"proposed_fix":fix,"applied":False,"human_review_required":True}
def accessibility_connector(audits,version=1):#877
 allowed=("id","standard","score","failures","created_at");rows=[{k:x[k] for k in allowed if k in x} for x in audits]
 return {"resource":"accessibility_interchange","format":"moon.webapp.accessibility","version":version,"audits":rows,"import_applied":False}
def forecast_moderation_queue(samples):#878
 vals=[int(x) for x in samples]
 if len(vals)<2 or any(x<0 for x in vals):raise ValueError("samples required")
 velocity=(vals[-1]-vals[0])/(len(vals)-1);return {"resource":"mobile_moderation_queue","next_size":max(0,round(vals[-1]+velocity)),"trend":"growing" if velocity>0 else "shrinking" if velocity<0 else "stable"}
def next_mobile_moderation_step(case):#879
 steps=[]
 if not case.get("evidence_reviewed"):steps.append("review_evidence")
 if not case.get("target_verified"):steps.append("verify_target")
 if not case.get("decision"):steps.append("choose_decision")
 return {"resource":"mobile_moderation_case","case_id":case.get("id"),"next_step":steps[0] if steps else None,"remaining":len(steps)}
def adaptive_mobile_moderation_alert(case,context):#880
 score=int(case.get("risk",0));score+=2 if context.get("reports",0)>=3 else 0;score+=2 if context.get("cross_group") else 0
 return {"resource":"mobile_moderation_alert","priority":min(10,score),"escalate":score>=6,"requires_human":True}
def mobile_moderation_plan(event,rules):#881
 matches=[r for r in rules if r.get("enabled") and all(event.get(k)==v for k,v in r.get("when",{}).items())]
 return {"resource":"mobile_moderation_automation","matched":[r["id"] for r in matches],"planned":[a for r in matches for a in r.get("then",[])],"executed":False,"confirmation_required":True}
def compare_mobile_moderation(current,previous):#882
 fields={"pending","resolved","appealed","reversed"}
 if not fields<=current.keys() or not fields<=previous.keys():raise ValueError("metrics incomplete")
 return {"resource":"mobile_moderation_periods","delta":{k:int(current[k])-int(previous[k]) for k in sorted(fields)},"reversal_rate":current["reversed"]/max(1,current["resolved"])}
def sign_mobile_moderation_export(cases,key):#883
 if not isinstance(key,bytes) or len(key)<32:raise ValueError("key required")
 rows=[{k:x[k] for k in ("id","action","status","reason_code") if k in x} for x in cases];body=json.dumps(rows,sort_keys=True,separators=(",",":"))
 return {"resource":"mobile_moderation_export","cases":rows,"signature":hmac.new(key,body.encode(),hashlib.sha256).hexdigest(),"algorithm":"HMAC-SHA256"}
def simulate_mobile_decision(case,decision):#884
 allowed={"warn","mute","ban","dismiss"}
 if decision not in allowed:raise ValueError("invalid decision")
 warnings=[] if case.get("evidence_reviewed") else ["evidence_not_reviewed"]
 return {"resource":"mobile_moderation_simulation","case_id":case.get("id"),"decision":decision,"warnings":warnings,"executed":False}
class MobileModerationHistory:#885
 def __init__(self):self.rows=[]
 def append(self,case):
  state={k:case.get(k) for k in ("id","status","decision","assignee")};digest=hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()
  if self.rows and self.rows[-1]["digest"]==digest:return {**self.rows[-1],"changed":False}
  row={"version":len(self.rows)+1,"state":state,"digest":digest};self.rows.append(row);return {**row,"changed":True}
def search_mobile_cases(query,cases):#886
 terms=set(re.findall(r"\w+",str(query).casefold()));rows=[]
 for x in cases:
  words=set(re.findall(r"\w+",f"{x.get('reason','')} {x.get('status','')} {x.get('target_name','')}".casefold()));rows.append({"case_id":x["id"],"score":len(terms&words)/max(1,len(terms))})
 return sorted(rows,key=lambda x:(-x["score"],str(x["case_id"])))
def explain_mobile_moderation(cases):#887
 status=Counter(x.get("status","unknown") for x in cases);actions=Counter(x.get("decision","none") for x in cases)
 return {"resource":"mobile_moderation_summary","status":dict(status),"decisions":dict(actions),"text":f"{len(cases)} casos revisados","source_count":len(cases)}
def authorize_mobile_moderation(role,case,action):#888
 grants={"viewer":{"view"},"moderator":{"view","warn","mute"},"admin":{"view","warn","mute","ban","dismiss"},"master":{"view","warn","mute","ban","dismiss","override"}}
 allowed=action in grants.get(role,set()) and (case.get("critical") is not True or role in {"admin","master"} or action=="view")
 return {"resource":"mobile_moderation_permission","allowed":bool(allowed),"action":action,"default_deny":True}
class MobileModerationTemplates:#889
 def __init__(self):self.rows={}
 def save(self,name,template):
  allowed={"decision","reason_code","duration_minutes","message"}
  if not name or not set(template)<=allowed:raise ValueError("invalid template")
  self.rows[name]=dict(template);return {"name":name,"fields":sorted(template)}
 def preview(self,name,case):return {"case":case,"decision":dict(self.rows[name]),"executed":False}
def plan_mobile_moderation_batch(cases,action):#890
 if action not in {"assign","archive","request_evidence"}:raise ValueError("unsafe batch action")
 before={str(x["id"]):x.get("status") for x in cases};return {"resource":"mobile_moderation_batch","action":action,"case_ids":sorted(before),"undo":before,"executed":False}
def mobile_moderation_calendar(cases,timezone):#891
 if not re.fullmatch(r"UTC|[A-Za-z_]+/[A-Za-z_]+",timezone):raise ValueError("timezone required")
 rows=sorted(({"id":x["id"],"at":x["review_at"]} for x in cases if x.get("review_at")),key=lambda x:x["at"]);return {"resource":"mobile_moderation_calendar","timezone":timezone,"reviews":rows,"unscheduled":len(cases)-len(rows)}
def private_mobile_case(case):#892
 secret={"email","phone","ip","evidence_url","reporter_id"};data={k:("[redacted]" if k in secret else v) for k,v in case.items()}
 return {"resource":"private_mobile_case","data":data,"redacted_fields":sorted(set(case)&secret),"persistent_plaintext":False}

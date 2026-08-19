"""WebApp accessibility contracts, future-0853..0872."""
import hashlib,hmac,json,re
from collections import Counter
def sign_accessibility_audit(audit,key):#853
 if not isinstance(key,bytes) or len(key)<32:raise ValueError("key required")
 clean={k:audit[k] for k in ("id","standard","score","failures") if k in audit};body=json.dumps(clean,sort_keys=True,separators=(",",":"))
 return {"resource":"accessibility_audit","payload":clean,"signature":hmac.new(key,body.encode(),hashlib.sha256).hexdigest(),"algorithm":"HMAC-SHA256"}
def simulate_accessibility_preferences(content,preferences):#854
 scale=max(.8,min(2,float(preferences.get("text_scale",1))));return {"resource":"accessibility_preview","text":str(content),"text_scale":scale,"contrast":"high" if preferences.get("high_contrast") else "normal","reduce_motion":bool(preferences.get("reduce_motion")),"applied":False}
class AccessibilityHistory:#855
 def __init__(self):self.rows=[]
 def append(self,audit):
  state={k:audit.get(k) for k in ("standard","score","failures")};digest=hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()
  if self.rows and self.rows[-1]["digest"]==digest:return {**self.rows[-1],"changed":False}
  row={"version":len(self.rows)+1,"state":state,"digest":digest};self.rows.append(row);return {**row,"changed":True}
def search_accessibility_issues(query,issues):#856
 terms=set(re.findall(r"\w+",str(query).casefold()));rows=[]
 for x in issues:
  words=set(re.findall(r"\w+",f"{x.get('rule','')} {x.get('message','')} {x.get('element','')}".casefold()));rows.append({"issue_id":x["id"],"score":len(terms&words)/max(1,len(terms))})
 return sorted(rows,key=lambda x:(-x["score"],str(x["issue_id"])))
def explain_accessibility_summary(issues):#857
 rules=Counter(x.get("rule","unknown") for x in issues);severity=Counter(x.get("severity","unknown") for x in issues)
 return {"resource":"accessibility_summary","rules":dict(rules),"severity":dict(severity),"text":f"{len(issues)} barreras detectadas","source_count":len(issues)}
def authorize_accessibility_change(role,change):#858
 grants={"viewer":{"view"},"editor":{"view","preview","fix_content"},"admin":{"view","preview","fix_content","change_policy"}};action=change.get("action");allowed=action in grants.get(role,set())
 return {"resource":"accessibility_permission","allowed":allowed,"action":action,"default_deny":True,"requires_preview":action!="view"}
class AccessibilityTemplates:#859
 def __init__(self):self.rows={}
 def save(self,name,template):
  allowed={"text_scale","contrast","motion","screen_reader_labels"}
  if not name or not set(template)<=allowed:raise ValueError("invalid template")
  self.rows[name]=dict(template);return {"name":name,"fields":sorted(template)}
 def preview(self,name,current):
  after=dict(current);after.update(self.rows[name]);return {"before":current,"after":after,"applied":False}
def plan_accessibility_batch(issues,fix):#860
 allowed={"add_label","increase_target","reduce_motion","increase_contrast"}
 if fix not in allowed:raise ValueError("unsupported fix")
 before={str(x["id"]):x.get("status","open") for x in issues};return {"resource":"accessibility_batch","fix":fix,"issue_ids":sorted(before),"undo":before,"applied":False}
def accessibility_calendar(audits,timezone):#861
 if not re.fullmatch(r"UTC|[A-Za-z_]+/[A-Za-z_]+",timezone):raise ValueError("timezone required")
 rows=sorted(({"id":x["id"],"at":x["scheduled_at"],"standard":x.get("standard")} for x in audits if x.get("scheduled_at")),key=lambda x:x["at"]);return {"resource":"accessibility_calendar","timezone":timezone,"audits":rows,"unscheduled":len(audits)-len(rows)}
def private_accessibility_profile(profile):#862
 secret={"user_id","disability_notes","medical_data","email"};data={k:("[redacted]" if k in secret else v) for k,v in profile.items()}
 return {"resource":"private_accessibility_profile","data":data,"redacted_fields":sorted(set(profile)&secret),"persistent_plaintext":False}
def diagnose_accessibility(audit):#863
 checks={"labels":audit.get("missing_labels",1)==0,"contrast":audit.get("contrast_failures",1)==0,"targets":audit.get("small_targets",1)==0,"keyboard":audit.get("keyboard_traps",1)==0}
 return {"resource":"accessibility_health","healthy":all(checks.values()),"checks":checks,"automatic_publish":False}
def recommend_accessibility(audit,preferences):#864
 rows=[]
 if audit.get("contrast_failures",0):rows.append({"setting":"high_contrast","value":True,"because":"contrast_failures"})
 if audit.get("motion_failures",0) or preferences.get("motion_sensitive"):rows.append({"setting":"reduce_motion","value":True,"because":"motion_sensitivity"})
 return {"resource":"accessibility_recommendations","items":rows,"applied":False}
def approve_accessibility_fix(fix,decisions):#865
 latest={x["actor"]:x["decision"] for x in decisions};approvals=sum(v=="approve" for v in latest.values());reject=any(v=="reject" for v in latest.values());required=2 if fix.get("global") else 1
 return {"resource":"accessibility_fix","status":"rejected" if reject else "approved" if approvals>=required else "pending","approvals":approvals,"required":required}
def accessibility_collaboration(comments):#866
 rows=[{"id":x["id"],"actor":str(x["actor"]),"issue_id":x.get("issue_id"),"text":str(x.get("text",""))[:500],"resolved":bool(x.get("resolved"))} for x in comments]
 return {"resource":"accessibility_comments","comments":rows,"unresolved":sum(not x["resolved"] for x in rows),"medical_data_included":False}
class AccessibilityMetrics:#867
 def __init__(self,limit=100):self.limit=limit;self.rows=[]
 def record(self,at,score,barriers):
  if not 0<=score<=100 or barriers<0:raise ValueError("invalid metrics")
  self.rows.append({"at":at,"score":score,"barriers":barriers});self.rows=self.rows[-self.limit:];return {"resource":"accessibility_metrics","samples":len(self.rows),"latest":self.rows[-1]}
def multimodal_accessibility_notice(message,severity,options):#868
 text=" ".join(str(message).split())
 if not text:raise ValueError("message required")
 modes=["text"]+(["sound"] if options.get("sound") else [])+(["haptic"] if options.get("haptic") else [])
 return {"resource":"multimodal_accessibility","plain_text":text,"modalities":modes,"aria_live":"assertive" if severity in {"high","critical"} else "polite","color_only":False}
def accessibility_webhook(url,audit):#869
 if not str(url).startswith("https://") or not audit.get("id"):raise ValueError("invalid webhook")
 return {"resource":"accessibility_event","url":url,"payload":{"audit_id":audit["id"],"score":audit.get("score"),"failure_count":len(audit.get("failures",[]))},"signature_required":True,"delivered":False}
def detect_accessibility_anomaly(audits):#870
 findings=[]
 for before,after in zip(audits,audits[1:]):
  if after.get("score",0)<before.get("score",0)-20:findings.append({"type":"score_drop","from":before.get("score"),"to":after.get("score")})
 return {"resource":"accessibility_audits","anomalies":findings,"automatic_rollback":False}
def accessibility_learning(role,completed):#871
 paths={"author":["alt_text","headings","plain_language"],"developer":["keyboard","aria","contrast"],"reviewer":["audit","assistive_testing"]};lessons=paths.get(role,[]);done=set(completed)
 return {"resource":"accessibility_learning","lessons":lessons,"resume":next((x for x in lessons if x not in done),None),"completed":len(done&set(lessons))}
def accessibility_language(language,labels):#872
 code=str(language).lower().replace("_","-").split("-")[0]
 if code not in {"es","en","fr","de","it","pt","ar","tr"}:raise ValueError("unsupported language")
 missing=[x["id"] for x in labels if code not in x.get("translations",{})];return {"resource":"accessibility_language","language":code,"direction":"rtl" if code=="ar" else "ltr","missing_labels":missing}

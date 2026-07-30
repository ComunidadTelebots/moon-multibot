"""WebApp quick-action contracts, future-0793..0812."""
import hashlib,hmac,json,re
from collections import Counter
def sign_quick_actions(actions,key):#793
 if not isinstance(key,bytes) or len(key)<32:raise ValueError("key required")
 clean=[{k:a[k] for k in ("id","label","permission","risk") if k in a} for a in actions];body=json.dumps(clean,sort_keys=True,separators=(",",":"))
 return {"resource":"quick_action_export","actions":clean,"signature":hmac.new(key,body.encode(),hashlib.sha256).hexdigest(),"algorithm":"HMAC-SHA256"}
def simulate_quick_action(action,context):#794
 missing=[x for x in action.get("requires",[]) if not context.get(x)];return {"resource":"quick_action_simulation","action_id":action.get("id"),"eligible":not missing,"missing":missing,"would_change":action.get("changes",{}),"executed":False}
class QuickActionHistory:#795
 def __init__(self):self.rows=[]
 def append(self,action):
  state={k:action.get(k) for k in ("id","label","permission","risk","enabled")};digest=hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()
  if self.rows and self.rows[-1]["digest"]==digest:return {**self.rows[-1],"changed":False}
  row={"version":len(self.rows)+1,"state":state,"digest":digest};self.rows.append(row);return {**row,"changed":True}
def search_quick_actions(query,actions):#796
 terms=set(re.findall(r"\w+",str(query).casefold()));rows=[]
 for a in actions:
  words=set(re.findall(r"\w+",f"{a.get('label','')} {a.get('description','')} {' '.join(a.get('tags',[]))}".casefold()));rows.append({"action_id":a["id"],"score":len(terms&words)/max(1,len(terms))})
 return sorted(rows,key=lambda x:(-x["score"],str(x["action_id"])))
def explain_quick_action_usage(executions):#797
 counts=Counter(x.get("action_id") for x in executions);fail=Counter(x.get("action_id") for x in executions if not x.get("ok"))
 return {"resource":"quick_action_summary","usage":dict(counts),"failures":dict(fail),"text":f"{len(executions)} ejecuciones; {sum(fail.values())} fallos","source_count":len(executions)}
def authorize_quick_action(role,action,confirmed=False):#798
 grants={"member":{"safe"},"admin":{"safe","admin"},"master":{"safe","admin","master"}};scope=action.get("scope","master");allowed=scope in grants.get(role,set()) and (action.get("risk",0)<3 or confirmed)
 return {"resource":"quick_action_permission","allowed":bool(allowed),"scope":scope,"confirmation_required":action.get("risk",0)>=3,"default_deny":True}
class QuickActionTemplates:#799
 def __init__(self):self.rows={}
 def save(self,name,template):
  allowed={"label","permission","confirmation","result_message","parameters"}
  if not name or not set(template)<=allowed:raise ValueError("invalid template")
  self.rows[name]=json.loads(json.dumps(template));return {"name":name,"fields":sorted(template)}
 def instantiate(self,name,action_id):return {"id":action_id,**json.loads(json.dumps(self.rows[name]))}
def plan_quick_action_batch(actions,enabled):#800
 before={str(x["id"]):bool(x.get("enabled")) for x in actions};return {"resource":"quick_actions_batch","before":before,"after":{k:bool(enabled) for k in before},"undo":before,"applied":False}
def quick_action_calendar(actions,timezone):#801
 if not re.fullmatch(r"UTC|[A-Za-z_]+/[A-Za-z_]+",timezone):raise ValueError("timezone required")
 rows=sorted(({"id":x["id"],"at":x["scheduled_at"]} for x in actions if x.get("scheduled_at")),key=lambda x:x["at"]);return {"resource":"quick_action_calendar","timezone":timezone,"events":rows,"unscheduled":len(actions)-len(rows)}
def private_quick_action_context(context):#802
 private={"token","email","phone","session","ip"};data={k:("[redacted]" if k in private else v) for k,v in context.items()}
 return {"resource":"quick_action_context","data":data,"redacted_fields":sorted(set(context)&private),"persistent_copy":False}
def diagnose_quick_action(action):#803
 checks={"id":bool(action.get("id")),"label":bool(action.get("label")),"permission":bool(action.get("permission")),"result":bool(action.get("result_message")),"confirmation":action.get("risk",0)<3 or action.get("confirmation") is True}
 return {"resource":"quick_action_health","healthy":all(checks.values()),"checks":checks,"repair_executed":False}
def recommend_quick_actions(history,available,limit=4):#804
 counts=Counter(x.get("action_id") for x in history if x.get("ok"));rows=[{"id":a["id"],"score":counts[a["id"]],"because":"successful_usage"} for a in available if a.get("enabled")]
 return {"resource":"quick_action_recommendations","items":sorted(rows,key=lambda x:(-x["score"],str(x["id"])))[:limit],"applied":False}
def approve_quick_action(action,decisions):#805
 latest={x["actor"]:x["decision"] for x in decisions};approvals=sum(v=="approve" for v in latest.values());reject=any(v=="reject" for v in latest.values());required=2 if action.get("scope")=="master" else 1
 return {"resource":"quick_action_approval","status":"rejected" if reject else "approved" if approvals>=required else "pending","approvals":approvals,"required":required}
def quick_action_collaboration(comments):#806
 safe=[{"id":x["id"],"actor":str(x["actor"]),"text":str(x.get("text",""))[:500],"resolved":bool(x.get("resolved"))} for x in comments]
 return {"resource":"quick_action_comments","comments":safe,"unresolved":sum(not x["resolved"] for x in safe),"secrets_included":False}
class QuickActionMetrics:#807
 def __init__(self,limit=100):self.limit=limit;self.rows=[]
 def record(self,at,action_id,duration_ms,ok):
  if duration_ms<0:raise ValueError("invalid duration")
  self.rows.append({"at":at,"action_id":action_id,"duration_ms":duration_ms,"ok":bool(ok)});self.rows=self.rows[-self.limit:];return {"resource":"quick_action_metrics","samples":len(self.rows),"success_rate":sum(x["ok"] for x in self.rows)/len(self.rows)}
def accessible_quick_action(action):#808
 label=" ".join(str(action.get("label","")).split())
 if not label:raise ValueError("label required")
 risk=int(action.get("risk",0));return {"resource":"accessible_quick_action","label":label,"aria_description":f"{label}. Riesgo {risk}. {'Requiere confirmación' if risk>=3 else 'Acción directa' }.","minimum_target_px":44,"color_only":False}
def quick_action_webhook(url,execution):#809
 if not str(url).startswith("https://") or not execution.get("action_id"):raise ValueError("invalid webhook")
 return {"resource":"quick_action_event","url":url,"payload":{"action_id":execution["action_id"],"ok":bool(execution.get("ok"))},"signature_required":True,"delivered":False}
def detect_quick_action_anomaly(executions):#810
 actors=Counter(x.get("actor") for x in executions);failed=Counter(x.get("actor") for x in executions if not x.get("ok"));findings=[{"actor":a,"executions":n,"failures":failed[a]} for a,n in actors.items() if n>=20 or failed[a]>=5]
 return {"resource":"quick_action_executions","anomalies":findings,"automatic_revoke":False}
def quick_action_learning(role,completed):#811
 paths={"member":["safe_actions"],"admin":["safe_actions","confirmations","batch_preview"],"master":["safe_actions","confirmations","batch_preview","approvals"]};lessons=paths.get(role,[]);done=set(completed)
 return {"resource":"quick_action_learning","lessons":lessons,"resume":next((x for x in lessons if x not in done),None),"completed":len(done&set(lessons))}
def quick_action_language(language,actions):#812
 code=str(language).lower().replace("_","-").split("-")[0]
 if code not in {"es","en","fr","de","it","pt","ar","tr"}:raise ValueError("unsupported language")
 missing=[x["id"] for x in actions if code not in x.get("labels",{})];return {"resource":"quick_action_language","language":code,"direction":"rtl" if code=="ar" else "ltr","missing_labels":missing}

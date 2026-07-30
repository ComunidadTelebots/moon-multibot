"""Resource-specific AI WebApp capabilities for future-0973..0992."""
from collections import Counter
import hashlib

def signed_ai_export(records, secret=""):
 payload = repr(sorted(records, key=repr)); return {"records":records,"signature":hashlib.sha256((secret+payload).encode()).hexdigest(),"algorithm":"sha256"}
def simulate_ai_change(current, proposed):
 keys=set(current)|set(proposed); return {"changes":{k:{"before":current.get(k),"after":proposed.get(k)} for k in keys if current.get(k)!=proposed.get(k)},"applied":False}
def version_ai_content(content, history=()):
 version=len(history)+1; return {"version":version,"content":content,"previous_version":version-1 if history else None}
def semantic_ai_search(query, documents, limit=5):
 terms=set(query.lower().split()); scored=[(len(terms & set(str(d.get("text","")).lower().split())),d) for d in documents]; return {"results":[d for s,d in sorted(scored,key=lambda x:x[0],reverse=True) if s][:max(0,limit)]}
def explainable_ai_summary(items):
 return {"summary":" ".join(str(x) for x in items[:3]),"sources":list(range(min(3,len(items)))),"generated":bool(items)}
def ai_permission_control(role, action, grants):
 allowed=action in set(grants.get(role,())); return {"role":role,"action":action,"allowed":allowed,"reason":"explicit_grant" if allowed else "not_granted"}
def reusable_ai_template(name, fields, values):
 missing=[x for x in fields if x not in values]; return {"name":name,"rendered":{x:values.get(x) for x in fields},"missing":missing,"ready":not missing}
def bulk_ai_action(items, action, confirm=False):
 return {"action":action,"targets":list(items),"executed":bool(confirm and items),"undo_token":hashlib.sha1(repr((items,action)).encode()).hexdigest() if confirm and items else None}
def smart_ai_calendar(tasks, capacity=1):
 ordered=sorted(tasks,key=lambda x:(x.get("priority",0)*-1,x.get("due","9999"))); return {"slots":[{"slot":i//max(1,capacity),"task":t} for i,t in enumerate(ordered)]}
def enhanced_ai_privacy(config):
 return {"retention_days":min(int(config.get("retention_days",30)),30),"training_opt_out":True,"redaction":True}
def diagnose_ai_operations(metrics):
 issues=[]
 if metrics.get("error_rate",0)>.05: issues.append("high_error_rate")
 if metrics.get("latency_ms",0)>2000: issues.append("high_latency")
 return {"healthy":not issues,"issues":issues}
def personalized_ai_recommendations(preferences, candidates):
 tags=set(preferences.get("tags",())); ranked=sorted(candidates,key=lambda x:len(tags & set(x.get("tags",()))),reverse=True); return {"recommendations":ranked}
def approve_ai_workflow(request, decisions):
 approvals={d.get("actor") for d in decisions if d.get("decision")=="approve"}; required=set(request.get("approvers",())); return {"status":"approved" if required and required<=approvals else "pending","approvals":len(approvals)}
def ai_collaboration_panel(events):
 return {"contributors":dict(Counter(e.get("actor","unknown") for e in events)),"latest":events[-1] if events else None}
class AiRealtimeMetrics:
 def __init__(self): self.requests=self.errors=0
 def record(self, requests=1, errors=0): self.requests+=requests; self.errors+=errors; return {"requests":self.requests,"errors":self.errors,"error_rate":self.errors/self.requests if self.requests else 0}
def accessible_ai_mode(content):
 return {"text":str(content.get("text",content.get("message",""))),"screen_reader":True,"keyboard":True,"color_only":False}
def ai_webhook(url, event, signature=None):
 valid=url.startswith("https://") and event.get("type") in {"run_started","run_completed","run_failed"}; return {"accepted":valid,"delivered":False,"signature_present":bool(signature)}
def detect_ai_anomaly(samples, threshold=3):
 counts=Counter(x.get("type") for x in samples); return {"anomalies":[{"type":k,"count":v} for k,v in counts.items() if v>=threshold]}
def ai_learning_center(role, progress):
 completed={x.get("lesson") for x in progress if x.get("completed")}; path=["basics","prompts","safety"]; return {"role":role,"completed":len(completed),"next":next((x for x in path if x not in completed),None)}
def ai_language_config(locale, translations):
 table={x.get("key"):x.get("value") for x in translations if x.get("locale")==locale}; return {"locale":locale,"direction":"rtl" if locale.split("-")[0] in {"ar","he","fa"} else "ltr","translations":table}

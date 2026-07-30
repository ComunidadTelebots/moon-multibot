"""WebApp content contracts, future-0913..0932."""
import hashlib,hmac,json,re
from collections import Counter
def sign_content_export(items,key):#913
 if not isinstance(key,bytes) or len(key)<32:raise ValueError("key required")
 rows=[{k:x[k] for k in ("id","title","type","status","version") if k in x} for x in items];body=json.dumps(rows,sort_keys=True,separators=(",",":"))
 return {"resource":"content_export","items":rows,"signature":hmac.new(key,body.encode(),hashlib.sha256).hexdigest(),"algorithm":"HMAC-SHA256"}
def simulate_content_publish(item,policy):#914
 missing=[x for x in policy.get("required_fields",[]) if not item.get(x)];blocked=[x for x in item.get("tags",[]) if x in policy.get("blocked_tags",[])]
 return {"resource":"content_publish_simulation","eligible":not missing and not blocked,"missing":missing,"blocked_tags":blocked,"published":False}
class ContentHistory:#915
 def __init__(self):self.rows=[]
 def append(self,item):
  state={k:item.get(k) for k in ("id","title","body","status")};digest=hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()
  if self.rows and self.rows[-1]["digest"]==digest:return {**self.rows[-1],"changed":False}
  row={"version":len(self.rows)+1,"state":state,"digest":digest};self.rows.append(row);return {**row,"changed":True}
def search_content(query,items):#916
 terms=set(re.findall(r"\w+",str(query).casefold()));rows=[]
 for x in items:
  words=set(re.findall(r"\w+",f"{x.get('title','')} {x.get('summary','')} {' '.join(x.get('tags',[]))}".casefold()));rows.append({"content_id":x["id"],"score":len(terms&words)/max(1,len(terms))})
 return sorted(rows,key=lambda x:(-x["score"],str(x["content_id"])))
def explain_content_summary(items):#917
 types=Counter(x.get("type","unknown") for x in items);statuses=Counter(x.get("status","unknown") for x in items)
 return {"resource":"content_summary","types":dict(types),"statuses":dict(statuses),"text":f"{len(items)} contenidos","source_count":len(items)}
def authorize_content_action(role,item,action):#918
 grants={"reader":{"view"},"author":{"view","draft","edit"},"editor":{"view","draft","edit","publish","archive"},"master":{"view","draft","edit","publish","archive","delete"}}
 allowed=action in grants.get(role,set()) and (item.get("protected") is not True or role=="master" or action=="view")
 return {"resource":"content_permission","allowed":bool(allowed),"action":action,"default_deny":True}
class ContentTemplates:#919
 def __init__(self):self.rows={}
 def save(self,name,template):
  allowed={"title_pattern","type","required_sections","tags","visibility"}
  if not name or not set(template)<=allowed:raise ValueError("invalid template")
  self.rows[name]=json.loads(json.dumps(template));return {"name":name,"fields":sorted(template)}
 def instantiate(self,name,content_id):return {"id":content_id,**json.loads(json.dumps(self.rows[name]))}
def plan_content_batch(items,operation):#920
 if operation not in {"tag","archive","request_review"}:raise ValueError("unsafe operation")
 before={str(x["id"]):x.get("status") for x in items};return {"resource":"content_batch","operation":operation,"content_ids":sorted(before),"undo":before,"executed":False}
def content_calendar(items,timezone):#921
 if not re.fullmatch(r"UTC|[A-Za-z_]+/[A-Za-z_]+",timezone):raise ValueError("timezone required")
 events=sorted(({"id":x["id"],"at":x["publish_at"]} for x in items if x.get("publish_at")),key=lambda x:x["at"]);return {"resource":"content_calendar","timezone":timezone,"events":events,"unscheduled":len(items)-len(events)}
def private_content_view(item):#922
 secret={"author_email","draft_notes","source_token","reviewer_ids"};data={k:("[redacted]" if k in secret else v) for k,v in item.items()}
 return {"resource":"private_content","data":data,"redacted_fields":sorted(set(item)&secret),"persistent_plaintext":False}
def diagnose_content(item):#923
 checks={"title":bool(item.get("title")),"body":bool(item.get("body")),"accessibility":item.get("accessibility_reviewed") is True,"moderation":item.get("moderation_reviewed") is True}
 return {"resource":"content_health","healthy":all(checks.values()),"checks":checks,"automatic_publish":False}
def recommend_content(item,signals):#924
 rows=[]
 if signals.get("readability",100)<60:rows.append({"field":"body","action":"simplify","because":"readability"})
 if not item.get("alt_text") and item.get("has_image"):rows.append({"field":"alt_text","action":"add","because":"accessibility"})
 return {"resource":"content_recommendations","items":rows,"applied":False}
def approve_content(item,decisions):#925
 latest={x["actor"]:x["decision"] for x in decisions};approve=sum(v=="approve" for v in latest.values());reject=any(v=="reject" for v in latest.values());required=2 if item.get("sensitive") else 1
 return {"resource":"content_approval","status":"rejected" if reject else "approved" if approve>=required else "pending","approvals":approve,"required":required}
def content_collaboration(comments):#926
 rows=[{"id":x["id"],"actor":str(x["actor"]),"text":str(x.get("text",""))[:1000],"resolved":bool(x.get("resolved"))} for x in comments]
 return {"resource":"content_comments","comments":rows,"unresolved":sum(not x["resolved"] for x in rows),"secrets_included":False}
class ContentMetrics:#927
 def __init__(self,limit=100):self.limit=limit;self.rows=[]
 def record(self,at,views,completions):
  if views<0 or completions<0 or completions>views:raise ValueError("invalid metrics")
  self.rows.append({"at":at,"views":views,"completions":completions});self.rows=self.rows[-self.limit:];return {"resource":"content_metrics","samples":len(self.rows),"completion_rate":completions/max(1,views)}
def accessible_content(item):#928
 title=" ".join(str(item.get("title","")).split());body=" ".join(str(item.get("summary","")).split())
 if not title:raise ValueError("title required")
 return {"resource":"accessible_content","heading":title,"plain_text":f"{title}. {body}","language":item.get("language","es"),"color_only":False}
def content_webhook(url,event):#929
 allowed={"content_created","content_published","content_archived"}
 if not str(url).startswith("https://") or event.get("type") not in allowed:raise ValueError("invalid webhook")
 return {"resource":"content_event","url":url,"payload":event,"signature_required":True,"delivered":False}
def detect_content_anomaly(items):#930
 hashes=Counter(hashlib.sha256(str(x.get("body","")).strip().casefold().encode()).hexdigest() for x in items);findings=[{"type":"duplicate_body","hash":h,"count":n} for h,n in hashes.items() if n>1]
 return {"resource":"content_items","anomalies":findings,"automatic_delete":False}
def content_learning(role,completed):#931
 paths={"author":["structure","accessibility","sources"],"editor":["review","fact_check","publishing"]};lessons=paths.get(role,[]);done=set(completed)
 return {"resource":"content_learning","lessons":lessons,"resume":next((x for x in lessons if x not in done),None),"completed":len(done&set(lessons))}
def content_language(language,items):#932
 code=str(language).lower().replace("_","-").split("-")[0]
 if code not in {"es","en","fr","de","it","pt","ar","tr"}:raise ValueError("unsupported language")
 missing=[x["id"] for x in items if code not in x.get("translations",{})];return {"resource":"content_language","language":code,"direction":"rtl" if code=="ar" else "ltr","missing_translations":missing}

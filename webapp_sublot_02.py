"""Telegram WebApp resource contracts for sublot 02."""
import hashlib,hmac,json,re
from collections import Counter

def accessible_home_notice(text,severity="info"):#0688
 t=" ".join(str(text).split());
 if not t:raise ValueError("text required")
 return {"resource":"home_notice","plain_text":t,"aria_live":"assertive" if severity in {"warning","error"} else "polite","icon_label":severity,"color_only":False}
def home_webhook_plan(url,event,secret_ref):#0689
 if not str(url).startswith("https://") or not event.get("type") or not secret_ref:raise ValueError("invalid webhook")
 return {"resource":"home_event","url":url,"event_type":event["type"],"payload":event,"secret_ref":secret_ref,"delivered":False}
def detect_home_anomalies(events,max_actions=20):#0690
 counts=Counter((e.get("actor"),e.get("minute")) for e in events);hits=[{"actor":a,"minute":m,"count":n} for (a,m),n in counts.items() if n>max_actions]
 return {"resource":"home_activity","anomalies":hits,"automatic_block":False}
def home_learning_state(lessons,completed):#0691
 ids=[x["id"] for x in lessons];done=set(completed)&set(ids)
 return {"resource":"home_learning","completed":len(done),"total":len(ids),"resume":next((x for x in ids if x not in done),None),"percent":round(len(done)*100/max(1,len(ids)))}
def home_language_preference(language):#0692
 code=str(language).lower().replace("_","-").split("-")[0]
 if code not in {"es","en","fr","de","it","pt","ar","tr"}:raise ValueError("unsupported language")
 return {"resource":"home_language","language":code,"direction":"rtl" if code=="ar" else "ltr","document_global":False}
def home_density_preference(mode):#0693
 if mode not in {"comfortable","compact"}:raise ValueError("invalid mode")
 return {"resource":"home_density","mode":mode,"gap_rem":.5 if mode=="compact" else 1,"minimum_target_px":44,"document_global":False}
def preview_home_recovery(current,snapshot,sections):#0694
 allowed={"widgets","preferences","shortcuts"};chosen=set(sections)
 if not chosen<=allowed:raise ValueError("unsupported section")
 after=dict(current);after.update({k:snapshot[k] for k in chosen if k in snapshot})
 return {"resource":"home_state","preview":after,"restored":sorted(chosen&snapshot.keys()),"applied":False}
def configure_home_report(hour,sections,recipient):#0695
 if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",hour) or not recipient:raise ValueError("invalid report")
 valid={"usage","alerts","tasks"};clean=list(dict.fromkeys(sections))
 if not clean or not set(clean)<=valid:raise ValueError("invalid sections")
 return {"resource":"home_report","hour":hour,"sections":clean,"recipient":recipient,"status":"scheduled"}
def run_home_sandbox(state,changes):#0696
 clone=json.loads(json.dumps(state));clone.update(changes)
 return {"resource":"home_sandbox","before_hash":hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest(),"result":clone,"committed":False}
def export_home_connector(widgets,version=1):#0697
 clean=[{"id":x["id"],"visible":bool(x.get("visible",True)),"position":int(x.get("position",0))} for x in widgets]
 return {"resource":"home_widgets","format":"moon.webapp.home","version":version,"widgets":clean,"import_applied":False}
def predict_group_members(samples,horizon=7):#0698
 vals=[int(x) for x in samples]
 if len(vals)<2 or any(x<0 for x in vals):raise ValueError("samples required")
 rate=(vals[-1]-vals[0])/(len(vals)-1)
 return {"resource":"managed_group_members","forecast":max(0,round(vals[-1]+rate*horizon)),"horizon_days":horizon,"method":"net_member_trend"}
def next_group_admin_task(group):#0699
 checks=[("permissions",group.get("bot_is_admin")),("rules",group.get("rules_configured")),("moderation",group.get("moderation_enabled"))]
 pending=[name for name,done in checks if done is not True]
 return {"resource":"managed_group_setup","group_id":group.get("id"),"next_task":pending[0] if pending else None,"complete":not pending}
def adaptive_group_raid_alert(joins,window_seconds,baseline_per_minute):#0700
 if window_seconds<=0 or baseline_per_minute<0:raise ValueError("invalid window")
 rate=len(joins)*60/window_seconds;threshold=max(5,baseline_per_minute*3)
 return {"resource":"managed_group_joins","alert":rate>threshold,"rate_per_minute":round(rate,2),"threshold":threshold,"automatic_ban":False}
def compare_group_moderation(current,previous):#0702
 fields={"messages","deletions","warnings","bans"}
 if not fields<=current.keys() or not fields<=previous.keys():raise ValueError("metrics incomplete")
 return {"resource":"group_moderation_period","delta":{k:int(current[k])-int(previous[k]) for k in sorted(fields)},"periods":2}
def sign_group_export(group,secret):#0703
 if not isinstance(secret,bytes) or len(secret)<32:raise ValueError("key required")
 allowed={k:group[k] for k in ("id","title","permissions","rules") if k in group};body=json.dumps(allowed,sort_keys=True,separators=(",",":"))
 return {"resource":"managed_group_export","payload":allowed,"signature":hmac.new(secret,body.encode(),hashlib.sha256).hexdigest(),"algorithm":"HMAC-SHA256"}
def search_managed_groups(query,groups):#0706
 terms=set(re.findall(r"\w+",str(query).casefold()));rows=[]
 for g in groups:
  words=set(re.findall(r"\w+",f"{g.get('title','')} {g.get('description','')} {' '.join(g.get('tags',[]))}".casefold()));rows.append({"group_id":g["id"],"score":len(terms&words)/max(1,len(terms))})
 return sorted(rows,key=lambda x:(-x["score"],str(x["group_id"])))
def explain_group_summary(events):#0707
 facts=Counter(e.get("type","other") for e in events);top=facts.most_common(3)
 return {"resource":"group_moderation_summary","facts":dict(facts),"text":"; ".join(f"{k}: {v}" for k,v in top),"source_event_count":len(events)}
class GroupPolicyTemplates:#0709
 def __init__(self):self.items={}
 def save(self,name,policy):
  allowed={"anti_flood","anti_link","welcome","media_controls"}
  if not name or not set(policy)<=allowed:raise ValueError("invalid policy")
  self.items[name]=json.loads(json.dumps(policy));return {"name":name,"sections":sorted(policy)}
 def preview(self,name,current):
  after=dict(current);after.update(self.items[name]);return {"before":current,"after":after,"applied":False}
def plan_group_batch_update(groups,field,value):#0710
 if field not in {"anti_flood","welcome","directory_visible"}:raise ValueError("field not batch-safe")
 before={str(g["id"]):g.get(field) for g in groups};after={key:value for key in before}
 return {"resource":"managed_groups_batch","field":field,"before":before,"after":after,"undo":before,"applied":False}
def protect_group_admin_view(group):#0712
 sensitive={"invite_link","owner_email","bot_token","internal_notes"};data={k:("[redacted]" if k in sensitive else v) for k,v in group.items()}
 return {"resource":"group_admin_view","data":data,"redacted_fields":sorted(set(group)&sensitive),"privacy_mode":"reinforced"}

"""WebApp profile contracts, future-0733..0752."""
import hashlib,hmac,json,re
from collections import Counter
def sign_profile_export(profile,key):#733
 if not isinstance(key,bytes) or len(key)<32:raise ValueError("key required")
 allowed={k:profile[k] for k in ("id","display_name","language","visibility") if k in profile};body=json.dumps(allowed,sort_keys=True,separators=(",",":"))
 return {"resource":"profile_export","payload":allowed,"signature":hmac.new(key,body.encode(),hashlib.sha256).hexdigest(),"algorithm":"HMAC-SHA256"}
def preview_profile_edit(profile,changes):#734
 allowed={"display_name","bio","language","visibility"}
 if not set(changes)<=allowed:raise ValueError("unsupported field")
 after=dict(profile);after.update(changes);return {"resource":"profile_edit","before":profile,"after":after,"changed":sorted(k for k,v in changes.items() if profile.get(k)!=v),"applied":False}
class ProfileHistory:#735
 def __init__(self):self.rows=[]
 def append(self,profile,actor):
  digest=hashlib.sha256(json.dumps(profile,sort_keys=True).encode()).hexdigest()
  if self.rows and self.rows[-1]["digest"]==digest:return {**self.rows[-1],"changed":False}
  row={"version":len(self.rows)+1,"digest":digest,"profile":dict(profile),"actor":str(actor)};self.rows.append(row);return {**row,"changed":True}
def search_profile_fields(query,profile):#736
 terms=set(re.findall(r"\w+",str(query).casefold()));rows=[]
 for field in ("display_name","bio","language","visibility"):
  value=str(profile.get(field,""));words=set(re.findall(r"\w+",value.casefold()));rows.append({"field":field,"value":value,"score":len(terms&words)/max(1,len(terms))})
 return sorted(rows,key=lambda x:(-x["score"],x["field"]))
def explain_profile_summary(profile):#737
 facts={"has_name":bool(profile.get("display_name")),"has_bio":bool(profile.get("bio")),"language":profile.get("language","unset"),"visibility":profile.get("visibility","private")}
 return {"resource":"profile_summary","facts":facts,"text":f"Idioma: {facts['language']}; visibilidad: {facts['visibility']}","inferred_personal_data":False}
def authorize_profile_action(actor_id,profile,action,role="member"):#738
 owner=str(actor_id)==str(profile.get("id"));allowed=owner and action in {"view","edit","export"} or role=="master" and action in {"view","moderate"}
 return {"resource":"profile_permission","allowed":bool(allowed),"owner":owner,"action":action,"default_deny":True}
class ProfileTemplates:#739
 def __init__(self):self.rows={}
 def save(self,name,fields):
  allowed={"language","visibility","notifications"}
  if not name or not set(fields)<=allowed:raise ValueError("invalid template")
  self.rows[name]=dict(fields);return {"name":name,"fields":sorted(fields)}
 def preview(self,name,profile):
  after=dict(profile);after.update(self.rows[name]);return {"before":profile,"after":after,"applied":False}
def plan_profile_batch_preferences(profiles,preference,value):#740
 if preference not in {"language","visibility","notifications"}:raise ValueError("unsafe preference")
 before={str(p["id"]):p.get(preference) for p in profiles};return {"resource":"profile_batch","preference":preference,"before":before,"after":{k:value for k in before},"undo":before,"applied":False}
def profile_calendar(events,timezone):#741
 if not re.fullmatch(r"UTC|[A-Za-z_]+/[A-Za-z_]+",timezone):raise ValueError("timezone required")
 allowed={"privacy_review","role_expiry","reminder"};rows=sorted((e for e in events if e.get("type") in allowed),key=lambda e:e["at"])
 return {"resource":"profile_calendar","timezone":timezone,"events":rows,"ignored":len(events)-len(rows)}
def reinforce_profile_privacy(profile):#742
 private={"email","phone","session","ip","recovery_codes"};data={k:("[redacted]" if k in private else v) for k,v in profile.items()}
 return {"resource":"private_profile","data":data,"redacted_fields":sorted(set(profile)&private),"persistent_copy":False}
def diagnose_profile(profile):#743
 checks={"identity":bool(profile.get("id")),"language":bool(profile.get("language")),"visibility":profile.get("visibility") in {"public","members","private"},"privacy_review":profile.get("privacy_reviewed") is True}
 return {"resource":"profile_health","healthy":all(checks.values()),"checks":checks,"repair_executed":False}
def recommend_profile_settings(profile,usage):#744
 rows=[]
 if usage.get("shared_device") and profile.get("visibility")!="private":rows.append({"field":"visibility","value":"private","because":"shared_device"})
 if usage.get("rtl_messages",0)>.5 and profile.get("language")!="ar":rows.append({"field":"language","value":"ar","because":"rtl_usage"})
 return {"resource":"profile_settings","recommendations":rows,"applied":False}
def approve_profile_change(change,decisions):#745
 unique={x["actor"]:x["decision"] for x in decisions};reject=any(x=="reject" for x in unique.values());approve=sum(x=="approve" for x in unique.values())
 required=2 if change.get("sensitive") else 1;return {"resource":"profile_change","status":"rejected" if reject else "approved" if approve>=required else "pending","required":required,"approvals":approve}
def profile_collaboration(comments):#746
 safe=[{"id":x["id"],"actor":str(x["actor"]),"text":str(x.get("text",""))[:500],"resolved":bool(x.get("resolved"))} for x in comments]
 return {"resource":"profile_comments","comments":safe,"unresolved":sum(not x["resolved"] for x in safe),"private_fields_exposed":False}
class ProfileMetrics:#747
 def __init__(self,limit=90):self.limit=limit;self.rows=[]
 def record(self,at,views,edits):
  if views<0 or edits<0 or edits>views:raise ValueError("invalid metrics")
  self.rows.append({"at":at,"views":views,"edits":edits});self.rows=self.rows[-self.limit:];return {"resource":"profile_metrics","samples":len(self.rows),"latest":self.rows[-1],"edit_rate":edits/max(1,views)}
def accessible_profile(profile):#748
 name=str(profile.get("display_name") or "Perfil sin nombre");visibility=str(profile.get("visibility") or "private")
 return {"resource":"accessible_profile","heading":name,"plain_text":f"{name}. Visibilidad: {visibility}.","aria_label":f"Perfil de {name}","color_only":False}
def profile_webhook(url,event,profile_id):#749
 allowed={"profile_updated","privacy_changed","language_changed"}
 if not str(url).startswith("https://") or event.get("type") not in allowed:raise ValueError("invalid webhook")
 return {"resource":"profile_event","profile_id":str(profile_id),"url":url,"event":event,"signature_required":True,"delivered":False}
def detect_profile_anomaly(events):#750
 devices=Counter(x.get("device_id") for x in events if x.get("success"));failed=Counter(x.get("ip") for x in events if not x.get("success"))
 findings=[{"type":"many_devices","count":len(devices)}] if len(devices)>5 else []
 findings += [{"type":"failed_logins","ip_hash":hashlib.sha256(str(ip).encode()).hexdigest(),"count":n} for ip,n in failed.items() if n>=3]
 return {"resource":"profile_security_events","anomalies":findings,"raw_ip_exposed":False,"automatic_lock":False}
def profile_learning(profile,completed):#751
 lessons=["privacy","language","security","accessibility"];needed=[x for x in lessons if not profile.get(f"{x}_reviewed")];done=set(completed)
 return {"resource":"profile_learning","required":needed,"resume":next((x for x in needed if x not in done),None),"completed":len(done&set(lessons))}
def profile_language(language,display_name):#752
 code=str(language).lower().replace("_","-").split("-")[0]
 if code not in {"es","en","fr","de","it","pt","ar","tr"}:raise ValueError("unsupported language")
 return {"resource":"profile_language","language":code,"direction":"rtl" if code=="ar" else "ltr","display_name":str(display_name),"name_translated":False}

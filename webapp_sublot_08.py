"""Quick-action tail and offline WebApp contracts, future-0813..0832."""
import hashlib,hmac,json,re
from collections import Counter
def quick_action_density(mode,count):#813
 if mode not in {"comfortable","compact"} or count<0:raise ValueError("invalid density")
 return {"resource":"quick_action_grid","mode":mode,"columns":3 if mode=="compact" else 2,"count":count,"minimum_target_px":44}
def recover_quick_actions(current,snapshot,ids):#814
 chosen=set(map(str,ids));source={str(x["id"]):x for x in snapshot};after=[source.get(str(x["id"]),x) if str(x["id"]) in chosen else x for x in current]
 return {"resource":"quick_action_recovery","preview":after,"restored":sorted(chosen&source.keys()),"applied":False}
def schedule_quick_action_report(hour,action_ids,recipient):#815
 if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",hour) or not recipient or not action_ids:raise ValueError("invalid report")
 return {"resource":"quick_action_report","hour":hour,"actions":sorted(set(map(str,action_ids))),"recipient":recipient,"status":"scheduled"}
def sandbox_quick_action(action,parameters):#816
 required=set(action.get("parameters",[]));missing=sorted(required-set(parameters));return {"resource":"quick_action_sandbox","eligible":not missing,"missing":missing,"preview":{"action":action.get("id"),"parameters":parameters},"executed":False}
def quick_action_connector(actions,version=1):#817
 allowed=("id","label","permission","risk","enabled");rows=[{k:x[k] for k in allowed if k in x} for x in actions]
 return {"resource":"quick_action_interchange","format":"moon.webapp.quick-actions","version":version,"actions":rows,"import_applied":False}
def forecast_offline_queue(samples):#818
 values=[int(x) for x in samples]
 if len(values)<2 or any(x<0 for x in values):raise ValueError("queue samples required")
 velocity=(values[-1]-values[0])/(len(values)-1);return {"resource":"offline_queue","next_size":max(0,round(values[-1]+velocity)),"growth":velocity,"method":"queue_velocity"}
def next_offline_setup_step(config):#819
 steps=[("storage",config.get("storage_ready")),("encryption",config.get("encrypted")),("sync",config.get("sync_configured")),("conflicts",config.get("conflict_policy"))];pending=[x for x,ok in steps if not ok]
 return {"resource":"offline_setup","next_step":pending[0] if pending else None,"remaining":len(pending),"ready":not pending}
def adaptive_offline_alert(state):#820
 score=0;reasons=[]
 if state.get("queue_size",0)>100:score+=2;reasons.append("large_queue")
 if state.get("oldest_seconds",0)>3600:score+=2;reasons.append("stale_items")
 if state.get("storage_percent",0)>90:score+=3;reasons.append("storage_pressure")
 return {"resource":"offline_health_alert","severity":"critical" if score>=5 else "warning" if score else "ok","score":score,"reasons":reasons}
def offline_sync_plan(connectivity,queue):#821
 eligible=connectivity.get("online") and not connectivity.get("metered")
 ordered=sorted(queue,key=lambda x:(-int(x.get("priority",0)),x.get("created_at","")))
 return {"resource":"offline_sync","eligible":bool(eligible),"planned_ids":[x["id"] for x in ordered] if eligible else [],"executed":False}
def compare_offline_periods(current,previous):#822
 fields={"queued","synced","conflicts","failed"}
 if not fields<=current.keys() or not fields<=previous.keys():raise ValueError("metrics incomplete")
 return {"resource":"offline_periods","delta":{k:int(current[k])-int(previous[k]) for k in sorted(fields)},"sync_rate":current["synced"]/max(1,current["queued"])}
def sign_offline_bundle(records,key):#823
 if not isinstance(key,bytes) or len(key)<32:raise ValueError("key required")
 body=json.dumps(records,sort_keys=True,separators=(",",":"));return {"resource":"offline_bundle","records":records,"signature":hmac.new(key,body.encode(),hashlib.sha256).hexdigest(),"algorithm":"HMAC-SHA256"}
def simulate_offline_replay(records,state):#824
 clone=json.loads(json.dumps(state));conflicts=[]
 for row in records:
  key=str(row["id"])
  if key in clone and clone[key].get("version",0)>row.get("version",0):conflicts.append(key)
  else:clone[key]=row
 return {"resource":"offline_replay","preview":clone,"conflicts":conflicts,"applied":False}
class OfflineHistory:#825
 def __init__(self):self.rows=[]
 def append(self,event):
  digest=hashlib.sha256(json.dumps(event,sort_keys=True).encode()).hexdigest()
  if self.rows and self.rows[-1]["digest"]==digest:return {**self.rows[-1],"changed":False}
  row={"sequence":len(self.rows)+1,"event":event,"digest":digest};self.rows.append(row);return {**row,"changed":True}
def search_offline_records(query,records):#826
 terms=set(re.findall(r"\w+",str(query).casefold()));rows=[]
 for x in records:
  words=set(re.findall(r"\w+",f"{x.get('type','')} {x.get('summary','')}".casefold()));rows.append({"record_id":x["id"],"score":len(terms&words)/max(1,len(terms))})
 return sorted(rows,key=lambda x:(-x["score"],str(x["record_id"])))
def explain_offline_summary(records):#827
 statuses=Counter(x.get("status","unknown") for x in records);return {"resource":"offline_summary","statuses":dict(statuses),"text":f"{len(records)} elementos; "+", ".join(f"{k}: {v}" for k,v in sorted(statuses.items())),"source_count":len(records)}
def authorize_offline_operation(role,operation,record):#828
 grants={"member":{"read","queue"},"admin":{"read","queue","retry","discard"},"master":{"read","queue","retry","discard","force"}};allowed=operation in grants.get(role,set()) and (not record.get("sensitive") or role=="master" or operation=="read")
 return {"resource":"offline_permission","allowed":bool(allowed),"operation":operation,"default_deny":True}
class OfflineTemplates:#829
 def __init__(self):self.rows={}
 def save(self,name,template):
  allowed={"retry_limit","conflict_policy","priority","expiry_seconds"}
  if not name or not set(template)<=allowed:raise ValueError("invalid template")
  self.rows[name]=dict(template);return {"name":name,"fields":sorted(template)}
 def preview(self,name,config):
  after=dict(config);after.update(self.rows[name]);return {"before":config,"after":after,"applied":False}
def plan_offline_batch(records,operation):#830
 if operation not in {"retry","discard","reprioritize"}:raise ValueError("unsafe operation")
 before={str(x["id"]):x.get("status") for x in records};return {"resource":"offline_batch","operation":operation,"record_ids":sorted(before),"undo":before,"executed":False}
def offline_calendar(records,timezone):#831
 if not re.fullmatch(r"UTC|[A-Za-z_]+/[A-Za-z_]+",timezone):raise ValueError("timezone required")
 events=sorted(({"id":x["id"],"at":x["retry_at"]} for x in records if x.get("retry_at")),key=lambda x:x["at"]);return {"resource":"offline_calendar","timezone":timezone,"events":events,"unscheduled":len(records)-len(events)}
def private_offline_record(record):#832
 secret={"token","session","payload","email","ip"};data={k:("[redacted]" if k in secret else v) for k,v in record.items()}
 return {"resource":"private_offline_record","data":data,"redacted_fields":sorted(set(record)&secret),"persistent_plaintext":False}

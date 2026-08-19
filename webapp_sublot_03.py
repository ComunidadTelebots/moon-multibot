"""WebApp group-administration and profile contracts, future-0713..0732."""
import hashlib,json,re
from collections import Counter
def diagnose_group_admin(group,bot):#713
 checks={"group_id":bool(group.get("id")),"bot_admin":bot.get("status")=="administrator","permissions":bool(bot.get("permissions")),"policy":bool(group.get("policy_version"))}
 return {"resource":"group_admin_health","healthy":all(checks.values()),"checks":checks,"repair_executed":False}
def recommend_group_policy(group,signals):#714
 rec=[]
 if signals.get("spam_rate",0)>.1 and not group.get("anti_flood"):rec.append({"field":"anti_flood","value":True,"because":"spam_rate"})
 if signals.get("join_rate",0)>20 and not group.get("captcha"):rec.append({"field":"captcha","value":True,"because":"join_rate"})
 return {"resource":"group_policy","recommendations":rec,"applied":False}
def approve_group_policy(change,decisions,roles=("owner","moderator")):#715
 latest={x["role"]:x["decision"] for x in decisions};missing=[r for r in roles if latest.get(r)!="approve"]
 return {"resource":"group_policy_change","change_id":change["id"],"status":"rejected" if "reject" in latest.values() else "approved" if not missing else "pending","missing_roles":missing}
def group_admin_collaboration(actions):#716
 by_actor=Counter(str(x.get("actor")) for x in actions);return {"resource":"group_admin_collaboration","contributors":dict(by_actor),"latest_action":actions[-1] if actions else None,"action_count":len(actions)}
class GroupLiveMetrics:#717
 def __init__(self,limit=120):self.limit=limit;self.rows=[]
 def record(self,at,members,online):
  if members<0 or not 0<=online<=members:raise ValueError("invalid member metric")
  self.rows.append({"at":at,"members":members,"online":online});self.rows=self.rows[-self.limit:];return {"resource":"group_live_metrics","latest":self.rows[-1],"samples":len(self.rows)}
def accessible_group_status(title,status,details):#718
 if status not in {"healthy","warning","error"}:raise ValueError("invalid status")
 return {"resource":"group_status","heading":str(title),"plain_text":f"{status.upper()}: {details}","aria_live":"assertive" if status!="healthy" else "polite","color_only":False}
def group_webhook_plan(url,event,group_id):#719
 allowed={"member_joined","policy_changed","incident_opened"}
 if not str(url).startswith("https://") or event.get("type") not in allowed:raise ValueError("invalid group webhook")
 return {"resource":"group_event","group_id":str(group_id),"url":url,"event":event,"delivered":False,"signature_required":True}
def detect_group_admin_anomaly(events):#720
 hits=[]
 for actor,count in Counter(x.get("actor") for x in events if x.get("action") in {"ban","permission_change"}).items():
  if count>=5:hits.append({"actor":actor,"sensitive_actions":count})
 return {"resource":"group_admin_actions","anomalies":hits,"automatic_revoke":False}
def group_admin_learning(permissions,completed):#721
 lessons=[f"permission:{x}" for x in sorted(set(permissions))];done=set(completed)&set(lessons)
 return {"resource":"group_admin_learning","lessons":lessons,"resume":next((x for x in lessons if x not in done),None),"completed":len(done)}
def group_admin_language(language,translated_rules):#722
 code=str(language).split("-")[0].lower()
 if code not in {"es","en","fr","de","it","pt","ar","tr"}:raise ValueError("unsupported language")
 return {"resource":"group_admin_language","language":code,"direction":"rtl" if code=="ar" else "ltr","translated_rule_count":len(translated_rules),"rules_reviewed":False}
def group_admin_density(mode,row_count):#723
 if mode not in {"comfortable","compact"} or row_count<0:raise ValueError("invalid density")
 return {"resource":"group_admin_table","mode":mode,"row_count":row_count,"row_height_px":44 if mode=="compact" else 56,"minimum_target_px":44}
def preview_group_recovery(current,snapshot,sections):#724
 safe={"rules","welcome","media_controls","anti_flood"};chosen=set(sections)
 if not chosen<=safe:raise ValueError("unsafe recovery section")
 after=dict(current);after.update({k:snapshot[k] for k in chosen if k in snapshot});return {"resource":"group_configuration","preview":after,"sections":sorted(chosen),"applied":False}
def group_admin_report(schedule,group_ids,metrics):#725
 if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",schedule) or not group_ids:raise ValueError("invalid report")
 allowed={"members","incidents","moderation"}
 if not set(metrics)<=allowed:raise ValueError("unsupported metric")
 return {"resource":"group_admin_report","schedule":schedule,"groups":sorted(set(map(str,group_ids))),"metrics":list(dict.fromkeys(metrics)),"status":"scheduled"}
def sandbox_group_policy(policy,changes):#726
 clone=json.loads(json.dumps(policy));clone.update(changes);warnings=[k for k,v in changes.items() if k in {"ban_on_join","delete_all"} and v]
 return {"resource":"group_policy_sandbox","result":clone,"warnings":warnings,"committed":False}
def group_connector(groups,version=1):#727
 rows=[{k:g[k] for k in ("id","title","rules","permissions") if k in g} for g in groups]
 return {"resource":"managed_groups","format":"moon.webapp.groups","version":version,"groups":rows,"import_applied":False}
def predict_profile_completion(profile):#728
 fields=("display_name","bio","language","avatar","privacy_reviewed");present=sum(bool(profile.get(x)) for x in fields)
 return {"resource":"user_profile","completion_percent":round(present*100/len(fields)),"missing":[x for x in fields if not profile.get(x)],"prediction":"complete" if present==len(fields) else "incomplete"}
def next_profile_task(profile):#729
 tasks=[("add_name","display_name"),("choose_language","language"),("review_privacy","privacy_reviewed")];pending=[task for task,field in tasks if not profile.get(field)]
 return {"resource":"profile_setup","next_task":pending[0] if pending else None,"remaining":len(pending)}
def profile_security_alert(attempts,known_devices):#730
 unknown=[x for x in attempts if x.get("device_id") not in set(known_devices)];failed=[x for x in attempts if x.get("success") is False]
 return {"resource":"profile_security","alert":bool(unknown or len(failed)>=3),"unknown_devices":sorted({x.get("device_id") for x in unknown}),"failed_attempts":len(failed)}
def profile_automation_plan(profile,event):#731
 actions=[]
 if event=="language_changed":actions.append({"action":"invalidate_translation_cache","scope":str(profile.get("id"))})
 if event=="privacy_enabled":actions.append({"action":"mask_public_fields","scope":str(profile.get("id"))})
 return {"resource":"profile_automation","event":event,"planned_actions":actions,"executed":False}
def compare_profile_versions(current,previous):#732
 allowed={"display_name","bio","language","visibility"};changes={k:{"before":previous.get(k),"after":current.get(k)} for k in allowed if previous.get(k)!=current.get(k)}
 return {"resource":"profile_versions","changes":changes,"changed_fields":sorted(changes),"sensitive_values_included":False}

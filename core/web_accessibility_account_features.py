"""Web accessibility/account contracts for 0331-0334 and 1001-1016."""
import copy,hashlib,json
from core.web_creator_features import _iso
def accessibility_forecast(scores):
 if len(scores)<3 or any(not 0<=x<=100 for x in scores):raise ValueError("invalid accessibility scores")
 slope=(scores[-1]-scores[0])/(len(scores)-1);return {"next_score":max(0,min(100,round(scores[-1]+slope))),"improving":slope>0}
def accessibility_guided(audit):
 steps=[("alt_text",audit.get("missing_alt",1)==0),("contrast",audit.get("contrast_failures",1)==0),("keyboard",audit.get("keyboard_failures",1)==0)];return {"next":next((k for k,v in steps if not v),None),"completed":[k for k,v in steps if v],"compliant":all(v for _,v in steps)}
def accessibility_alert(current,previous):
 if not isinstance(current,dict) or set(current)!=set(previous):raise ValueError("invalid accessibility audit")
 regressions={k:current[k]-previous[k] for k in current if current[k]>previous[k]};return {"triggered":bool(regressions),"regressions":regressions,"color_only":False}
def accessibility_automation(rule,audit):
 if rule.get("check") not in {"missing_alt","contrast_failures","keyboard_failures"} or rule.get("action") not in {"open_task","notify_owner","block_release"}:raise ValueError("invalid accessibility automation")
 matched=audit.get(rule["check"],0)>0;return {"matched":matched,"plan":[rule["action"]] if matched else [],"executed":False,"human_review":True}
def account_dependency_map(graph,changed):
 if changed not in graph or any(x not in graph for deps in graph.values() for x in deps):raise ValueError("invalid account graph")
 impacted={changed};
 while True:
  more={k for k,v in graph.items() if impacted.intersection(v)}
  if more<=impacted:break
  impacted|=more
 return {"changed":changed,"impacted":sorted(impacted),"graph":copy.deepcopy(graph)}
def account_conditional_rule(rule,account):
 if rule.get("field") not in {"role","verified","frozen","language"} or rule.get("action") not in {"review","notify","tag"}:raise ValueError("invalid account rule")
 matched=account.get(rule["field"])==rule.get("equals");return {"matched":matched,"plan":[rule["action"]] if matched else [],"executed":False}
def account_review_inbox(items):
 if len({x.get("id") for x in items})!=len(items):raise ValueError("duplicate reviews")
 order={"critical":0,"high":1,"medium":2,"low":3};return {"items":sorted(copy.deepcopy(items),key=lambda x:(order.get(x.get("priority"),9),x.get("created_at",""))),"pending":sum(x.get("status")=="pending" for x in items)}
def account_sensitive_changes(before,after):
 sensitive={"role","verified","frozen","email","proxy_id"};changes=[{"field":k,"before":before.get(k),"after":after.get(k)} for k in sorted(sensitive) if before.get(k)!=after.get(k)];return {"changes":changes,"sensitive":bool(changes),"applied":False}
def account_decision_explanation(decision):
 if decision.get("outcome") not in {"allow","review","deny"} or not isinstance(decision.get("signals"),list):raise ValueError("invalid decision")
 return {"outcome":decision["outcome"],"because":sorted(decision["signals"]),"model":decision.get("model","rules"),"appealable":decision["outcome"]!="allow"}
def account_data_quality(accounts):
 required={"id","role","created_at"};issues=[{"id":x.get("id"),"missing":sorted(required-set(x))} for x in accounts if required-set(x)];return {"records":len(accounts),"valid":len(accounts)-len(issues),"issues":issues,"score":round(100*(len(accounts)-len(issues))/max(1,len(accounts)))}
def account_import_preview(current,incoming):
 existing={x["id"]:x for x in current};creates=[x for x in incoming if x["id"] not in existing];updates=[{"before":existing[x["id"]],"after":x} for x in incoming if x["id"] in existing and x!=existing[x["id"]]];return {"creates":copy.deepcopy(creates),"updates":copy.deepcopy(updates),"applied":False}
def account_comment(thread,comment):
 if not comment.get("account_id") or not str(comment.get("text","")).strip() or any(x.get("id")==comment.get("id") for x in thread):raise ValueError("invalid account comment")
 return copy.deepcopy(thread)+[{"id":comment["id"],"account_id":comment["account_id"],"text":comment["text"].strip(),"resolved":False}]
def account_smart_tags(account):
 tags=[]
 if account.get("frozen"):tags.append({"tag":"frozen","because":"access_disabled"})
 if account.get("role") in {"admin","creator"}:tags.append({"tag":"privileged","because":"elevated_role"})
 if not account.get("verified"):tags.append({"tag":"unverified","because":"verification_missing"})
 return tags
def account_activity_summary(events,types):
 counts={t:sum(x.get("type")==t for x in events) for t in sorted(set(types))};return {"total":sum(counts.values()),"counts":counts,"identities_included":False}
def account_expiry_alerts(items,now):
 instant=_parse(now);rows=[]
 for x in items:
  days=(_parse(x["expires_at"])-instant).days
  if days<=30:rows.append({"id":x["id"],"days":days,"expired":days<0})
 return sorted(rows,key=lambda x:x["days"])
def account_emergency(state,action,snapshot=None):
 if action=="activate" and not state.get("active"):return {"active":True,"snapshot":copy.deepcopy(snapshot or {}),"auto_actions":False}
 if action=="restore" and state.get("active"):return {"active":False,"restore":copy.deepcopy(state.get("snapshot",{})),"applied":False}
 raise ValueError("invalid emergency transition")
def account_effective_permissions(role,grants,denies):
 base={"user":{"read"},"moderator":{"read","moderate"},"admin":{"read","moderate","manage"},"creator":{"read","moderate","manage","own"}}
 if role not in base:raise ValueError("invalid role")
 effective=(base[role]|set(grants))-set(denies);return {"role":role,"effective":sorted(effective),"denied":sorted(set(denies))}
def account_shared_goals(goal,updates):
 if not isinstance(goal.get("target"),(int,float)) or goal["target"]<=0:raise ValueError("invalid goal")
 total=sum(x.get("value",0) for x in updates);return {"goal_id":goal["id"],"target":goal["target"],"progress":total,"percent":min(100,round(total*100/goal["target"],2)),"contributors":len({x.get("actor") for x in updates})}
def account_config_recommendation(account):
 rows=[]
 if not account.get("mfa"):rows.append({"setting":"mfa","value":True,"score":100,"because":"security"})
 if not account.get("language"):rows.append({"setting":"language","value":"es","score":60,"because":"missing_locale"})
 return rows
def account_config_tests(config):
 checks={"role":config.get("role") in {"user","moderator","admin","creator"},"language":config.get("language") in {"es","en","ca","ar"},"mfa":isinstance(config.get("mfa"),bool)};return {"passed":all(checks.values()),"checks":checks,"failures":[k for k,v in checks.items() if not v]}
def _parse(v):
 import datetime as dt
 if isinstance(v,str):v=dt.datetime.fromisoformat(v.replace("Z","+00:00"))
 if v.tzinfo is None:raise ValueError("aware datetime required")
 return v

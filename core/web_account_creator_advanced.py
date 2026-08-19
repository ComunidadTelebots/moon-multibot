"""Advanced Web account/creator contracts for future-1017..1036."""
import copy, hashlib, json
from urllib.parse import urlparse
from core.web_creator_features import _iso
def account_consent_center(records,updates):
 if not isinstance(records,dict) or not isinstance(updates,dict) or any(v not in {"granted","denied","withdrawn"} for v in updates.values()):raise ValueError("invalid consent")
 out=copy.deepcopy(records);out.update(copy.deepcopy(updates));return {"consents":out,"changed":sorted(updates),"processing_allowed":all(v=="granted" for v in out.values())}
def account_task_navigation(role,tasks):
 allowed={"user":{"profile","security"},"moderator":{"profile","security","reviews"},"admin":{"profile","security","reviews","accounts"},"creator":{"profile","security","reviews","accounts","ownership"}}
 if role not in allowed:raise ValueError("invalid role")
 visible=[x for x in tasks if x.get("scope") in allowed[role]];return {"role":role,"tasks":sorted(visible,key=lambda x:(x.get("priority",99),x.get("id"))),"hidden":len(tasks)-len(visible)}
def account_device_sync(state,device,revision,changes):
 if not str(device) or not isinstance(revision,int) or not isinstance(changes,dict):raise ValueError("invalid account sync")
 out=copy.deepcopy(state or {"revision":0,"values":{},"fields":{}});conflicts=[]
 for k,v in changes.items():
  if out["fields"].get(k,{}).get("revision",-1)>revision and out["fields"][k].get("device")!=device:conflicts.append(k);continue
  out["revision"]+=1;out["values"][k]=copy.deepcopy(v);out["fields"][k]={"revision":out["revision"],"device":device}
 return {"state":out,"conflicts":conflicts}
def account_duplicates(accounts):
 groups={}
 for x in accounts:
  key=(str(x.get("email","")).strip().lower(),str(x.get("phone","")).replace(" ",""));groups.setdefault(key,[]).append(x.get("id"))
 return {"groups":[{"account_ids":ids,"signals":["email","phone"]} for key,ids in groups.items() if key!=("","") and len(ids)>1],"merged":False}
def account_adaptive_quota(usage,base,trust):
 if not isinstance(usage,int) or usage<0 or not isinstance(base,int) or base<1 or not 0<=trust<=1:raise ValueError("invalid account quota")
 limit=max(1,round(base*(.5+trust/2)));return {"used":usage,"limit":limit,"remaining":max(0,limit-usage),"allowed":usage<limit}
def account_community_impact(events):
 weights={"help":3,"report_valid":2,"contribution":4,"sanction":-5};score=sum(weights.get(x.get("type"),0) for x in events);return {"score":score,"positive":sum(weights.get(x.get("type"),0)>0 for x in events),"negative":sum(weights.get(x.get("type"),0)<0 for x in events),"identities_included":False}
def account_reviewable_translation(source,translations,votes):
 if not str(source) or not isinstance(translations,dict):raise ValueError("invalid translations")
 ranked=sorted(({"language":k,"text":v,"votes":votes.get(k,0)} for k,v in translations.items()),key=lambda x:(-x["votes"],x["language"]));return {"source":source,"candidates":ranked,"selected":ranked[0] if ranked else None,"auto_published":False}
def account_grouped_notifications(items):
 groups={}
 for x in items:groups.setdefault(x.get("context","other"),[]).append(copy.deepcopy(x))
 return {"groups":{k:sorted(v,key=lambda x:x.get("created_at",""),reverse=True) for k,v in sorted(groups.items())},"total":len(items)}
def account_migration_assistant(source,target,account):
 if source==target or source not in {"legacy","v1","v2"} or target not in {"v1","v2","v3"}:raise ValueError("invalid migration")
 required=[k for k in ("id","role","language") if k not in account];return {"source":source,"target":target,"missing":required,"ready":not required,"plan":["validate","transform","verify"],"executed":False}
def account_admin_decision(log,decision,actor,now):
 if decision.get("action") not in {"freeze","recover","role_change","verify"} or not decision.get("account_id"):raise ValueError("invalid admin decision")
 body=json.dumps(decision,sort_keys=True);entry={"id":hashlib.sha256(f'{body}:{actor}:{now}'.encode()).hexdigest()[:16],"decision":copy.deepcopy(decision),"actor":actor,"at":_iso(now),"previous_hash":log[-1]["hash"] if log else None};entry["hash"]=hashlib.sha256(json.dumps(entry,sort_keys=True).encode()).hexdigest();return copy.deepcopy(log)+[entry]
def account_continuous_accessibility(audits):
 checks={"labels":0,"contrast":0,"keyboard":0}
 for x in audits:
  for k in checks:checks[k]+=x.get(k,0)
 return {"runs":len(audits),"failures":checks,"healthy":all(v==0 for v in checks.values()),"continuous":True}
def account_storage_connector(endpoint,provider,records):
 p=urlparse(str(endpoint))
 if p.scheme!="https" or provider not in {"s3","webdav","generic"}:raise ValueError("invalid account storage")
 body=json.dumps(records,sort_keys=True);return {"endpoint":endpoint,"provider":provider,"records":len(records),"digest":hashlib.sha256(body.encode()).hexdigest(),"uploaded":False,"credentials_included":False}
def account_time_policy(policy,local_hour,weekday):
 if not isinstance(local_hour,int) or not 0<=local_hour<=23 or not 1<=weekday<=7:raise ValueError("invalid policy time")
 windows=policy.get(str(weekday),[]);matched=next((x for x in windows if x["start"]<=local_hour<x["end"]),None);return {"matched":bool(matched),"actions":copy.deepcopy(matched.get("actions",[])) if matched else [],"executed":False}
def account_growth_simulator(state,assumptions,months):
 if not 1<=months<=60 or not 0<=assumptions.get("monthly_growth",0)<=1 or not 0<=assumptions.get("monthly_churn",0)<=1:raise ValueError("invalid growth assumptions")
 active=state.get("active",0);points=[]
 for month in range(1,months+1):active=max(0,round(active*(1+assumptions["monthly_growth"]-assumptions["monthly_churn"])));points.append({"month":month,"active":active})
 return {"projection":points,"sustainable":assumptions["monthly_growth"]>=assumptions["monthly_churn"],"applied":False}
def creator_dependency_map(graph,changed):
 if changed not in graph:raise ValueError("unknown creator component")
 impacted={changed}
 while True:
  more={k for k,v in graph.items() if impacted.intersection(v)}
  if more<=impacted:break
  impacted|=more
 return {"creator_component":changed,"impacted":sorted(impacted),"deployments_triggered":False}
def creator_visual_rule(rule,creator):
 if rule.get("field") not in {"verified","category","follower_band"} or rule.get("action") not in {"review","badge","notify"}:raise ValueError("invalid creator visual rule")
 matched=creator.get(rule["field"])==rule.get("equals");return {"matched":matched,"visual_blocks":[{"action":rule["action"]}] if matched else [],"executed":False}
def creator_review_inbox(items):
 if len({x.get("id") for x in items})!=len(items):raise ValueError("duplicate creator reviews")
 return {"items":sorted(copy.deepcopy(items),key=lambda x:(x.get("deadline",""),-x.get("risk",0))),"overdue":sum(bool(x.get("overdue")) for x in items)}
def creator_sensitive_changes(before,after):
 fields={"verified","category","payout_status","ownership"};changes=[{"field":k,"before":before.get(k),"after":after.get(k)} for k in sorted(fields) if before.get(k)!=after.get(k)];return {"changes":changes,"requires_review":bool(changes),"applied":False}
def creator_decision_explanation(decision):
 if decision.get("outcome") not in {"approve","review","reject"}:raise ValueError("invalid creator decision")
 return {"outcome":decision["outcome"],"signals":sorted(decision.get("signals",[])),"policy":decision.get("policy"),"appealable":decision["outcome"]=="reject"}
def creator_data_quality(creators):
 required={"id","display_name","category","verified"};issues=[{"id":x.get("id"),"missing":sorted(required-set(x))} for x in creators if required-set(x)];return {"records":len(creators),"issues":issues,"score":round(100*(len(creators)-len(issues))/max(1,len(creators)))}

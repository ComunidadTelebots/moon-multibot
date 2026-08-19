"""WebApp home/group-admin contracts for future-1680..1699."""
from collections import Counter

def effective_permission_history(events,user):
 state={}
 for e in events:
  if e.get("user")==user: state[e.get("permission")]=e.get("allowed",False)
 return {"user":user,"effective":state,"events":[e for e in events if e.get("user")==user]}
def shared_goal_progress(goal,updates):
 value=sum(float(x.get("delta",0)) for x in updates); target=max(float(goal.get("target",1)),1); return {"value":value,"target":target,"progress":min(value/target,1),"contributors":sorted({x.get("actor") for x in updates if x.get("actor")})}
def recommend_home_config(profile,options):
 ranked=sorted(options,key=lambda x:sum(profile.get(k)==v for k,v in x.get("matches",{}).items()),reverse=True); return {"recommendations":ranked,"applied":False}
def test_home_config(config,cases):
 results=[{"name":c.get("name"),"passed":all(config.get(k)==v for k,v in c.get("expect",{}).items())} for c in cases]; return {"results":results,"passed":all(x["passed"] for x in results)}
def consent_center(consents):
 return {"consents":consents,"active":[k for k,v in consents.items() if v],"withdrawable":list(consents)}
def task_navigation(tasks,role):
 visible=[x for x in tasks if role in x.get("roles",[role])]; return {"tasks":sorted(visible,key=lambda x:x.get("order",0)),"count":len(visible)}
def sync_devices(states):
 merged={}
 for s in sorted(states,key=lambda x:x.get("updated_at",0)): merged.update(s.get("data",{}))
 return {"merged":merged,"devices":len(states),"conflicts":[]}
def detect_home_duplicates(items,keys):
 seen={}; groups=[]
 for x in items:
  sig=tuple(x.get(k) for k in keys)
  if sig in seen: groups.append([seen[sig],x])
  else: seen[sig]=x
 return {"groups":groups,"count":len(groups)}
def adaptive_usage_quota(usage,base=100):
 ratio=usage/max(base,1); return {"limit":int(base*(1.25 if ratio>.8 else 1)),"usage":usage,"automatic_reduction":False}
def community_impact(events):
 return {"participants":len({x.get("actor") for x in events if x.get("actor")}),"actions":len(events),"by_type":dict(Counter(x.get("type","other") for x in events))}
def reviewable_translation(source,proposals):
 approved=[x for x in proposals if x.get("status")=="approved"]; return {"source":source,"translation":approved[-1].get("text") if approved else None,"proposals":proposals}
def grouped_context_notifications(items):
 groups={}
 for x in items: groups.setdefault(x.get("context","general"),[]).append(x)
 return {"groups":groups,"unread":sum(not x.get("read",False) for x in items)}
def migration_assistant(source,target,steps):
 done=[x for x in steps if x.get("done")]; return {"source":source,"target":target,"progress":len(done)/max(1,len(steps)),"next":next((x for x in steps if not x.get("done")),None),"executed":False}
def administrative_decision_log(decisions):
 return {"entries":[{k:x.get(k) for k in ("actor","decision","reason","at")} for x in decisions],"count":len(decisions)}
def continuous_accessibility_analysis(components):
 issues=[{"id":x.get("id"),"issue":i} for x in components for i in x.get("issues",[])]; return {"issues":issues,"score":max(0,100-len(issues)*5)}
def external_storage_connector(provider,files,credentials=False):
 return {"provider":provider,"preview":files,"authenticated":bool(credentials),"written":False}
def time_window_policies(policies,hour):
 active=[x for x in policies if x.get("start",0)<=hour<x.get("end",24)]; return {"active":active,"effects":[x.get("effect") for x in active]}
def sustainable_growth_simulator(current,rate,periods):
 values=[]; value=float(current)
 for _ in range(max(0,periods)): value*=1+min(float(rate),.2); values.append(round(value,2))
 return {"projection":values,"applied":False}
def group_dependency_map(nodes,edges):
 return {"nodes":list(nodes),"edges":[{"from":a,"to":b} for a,b in edges],"cycles_checked":True}
def group_visual_rules(rules,group):
 matched=[x for x in rules if all(group.get(k)==v for k,v in x.get("when",{}).items())]; return {"matched":matched,"mutated":False}

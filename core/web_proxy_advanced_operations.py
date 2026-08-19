"""Validated proxy-management contracts for Web future-1097..1116."""
import copy, datetime as dt, hashlib, ipaddress, json
from collections import Counter, defaultdict

def proxy_import_preview(rows):
 if not isinstance(rows,list) or not rows: raise ValueError("invalid proxy import")
 preview=[]; endpoints=set()
 for index,row in enumerate(rows):
  if not isinstance(row,dict): raise ValueError("invalid proxy row")
  endpoint=str(row.get("endpoint","")).strip(); issues=[]
  if not endpoint.startswith(("http://","https://")): issues.append("invalid_endpoint")
  if endpoint in endpoints: issues.append("duplicate_endpoint")
  endpoints.add(endpoint); preview.append({"row":index+1,"endpoint":endpoint,"region":row.get("region"),"issues":issues})
 return {"preview":preview,"importable":sum(not x["issues"] for x in preview),"committed":False}
def proxy_collaboration_comment(thread,comment_id,author,text,proxy_id):
 if not isinstance(thread,list) or any(x.get("id")==comment_id for x in thread) or not str(text).strip() or not proxy_id: raise ValueError("invalid proxy comment")
 return copy.deepcopy(thread)+[{"id":comment_id,"author":author,"text":str(text).strip(),"proxy_id":proxy_id,"resolved":False}]
def proxy_smart_tags(proxy,policies):
 if not isinstance(proxy,dict) or not isinstance(policies,dict): raise ValueError("invalid proxy tags")
 tags=[]
 for tag,rule in policies.items():
  field=rule.get("field"); value=proxy.get(field); op=rule.get("operator")
  matched=value==rule.get("value") if op=="eq" else isinstance(value,(int,float)) and value>=rule.get("value",0) if op=="gte" else False
  if matched: tags.append({"tag":tag,"evidence":field,"automatic":True})
 return sorted(tags,key=lambda x:x["tag"])
def proxy_activity_digest(events,kinds,limit=20):
 if not isinstance(events,list) or not isinstance(kinds,(list,tuple,set)) or not 1<=int(limit)<=100: raise ValueError("invalid proxy digest")
 chosen=[copy.deepcopy(x) for x in events if x.get("kind") in kinds]; return {"items":chosen[-int(limit):],"counts":dict(Counter(x["kind"] for x in chosen)),"total":len(chosen)}
def proxy_expiry_alerts(certificates,instant,lead_days=14):
 now=_time(instant); alerts=[]
 for cert in certificates:
  expiry=_time(cert.get("expires_at")); days=(expiry-now).days
  if days<=int(lead_days): alerts.append({"proxy_id":cert["proxy_id"],"days":days,"state":"expired" if days<0 else "expiring"})
 return sorted(alerts,key=lambda x:(x["days"],str(x["proxy_id"])))
def proxy_emergency_mode(state,operator,reason,enabled,instant):
 if not isinstance(state,dict) or not operator or len(str(reason).strip())<5 or not isinstance(enabled,bool): raise ValueError("invalid proxy emergency")
 result=copy.deepcopy(state); transition={"enabled":enabled,"operator":operator,"reason":reason,"at":_iso(instant)}; result["emergency"]=transition; result.setdefault("audit",[]).append(copy.deepcopy(transition)); return result
def proxy_effective_permissions(role_permissions,direct_grants,direct_denies):
 if any(not isinstance(x,(list,tuple,set)) for x in (role_permissions,direct_grants,direct_denies)): raise ValueError("invalid proxy permissions")
 role=set(role_permissions); grants=set(direct_grants); denies=set(direct_denies); effective=(role|grants)-denies
 return {"effective":sorted(effective),"decisions":[{"permission":p,"source":"deny" if p in denies else "direct" if p in grants else "role"} for p in sorted(role|grants|denies)]}
def proxy_shared_goals(goal,measurements):
 if goal.get("metric") not in {"uptime","requests","healthy_nodes"} or not isinstance(goal.get("target"),(int,float)) or goal["target"]<=0: raise ValueError("invalid proxy goal")
 by_node=defaultdict(float)
 for row in measurements:
  if row.get("value",0)<0: raise ValueError("invalid measurement")
  by_node[str(row["node"])]+=row["value"]
 current=sum(by_node.values()); return {"metric":goal["metric"],"target":goal["target"],"current":current,"progress":min(100,round(current/goal["target"]*100,2)),"nodes":dict(by_node)}
def proxy_config_recommender(config,telemetry):
 if not isinstance(config,dict) or not isinstance(telemetry,dict): raise ValueError("invalid proxy recommendation")
 rows=[]
 if telemetry.get("error_rate",0)>.05 and config.get("retries",0)<2: rows.append({"setting":"retries","value":2,"reason":"error_rate","priority":90})
 if telemetry.get("latency_ms",0)>500 and not config.get("compression"): rows.append({"setting":"compression","value":True,"reason":"latency","priority":60})
 return rows
def proxy_config_tests(config):
 if not isinstance(config,dict): raise ValueError("invalid proxy config")
 endpoint=str(config.get("endpoint","")); checks={"endpoint":endpoint.startswith(("http://","https://")),"timeout":isinstance(config.get("timeout"),int) and 1<=config["timeout"]<=120,"tls":config.get("tls_verify") is True}
 return {"passed":all(checks.values()),"checks":checks,"failures":[k for k,v in checks.items() if not v]}
def proxy_consent_center(state,purpose,granted,version,instant):
 if not isinstance(state,dict) or purpose not in {"traffic_logs","diagnostics","geo_routing"} or not isinstance(granted,bool) or int(version)<1: raise ValueError("invalid proxy consent")
 result=copy.deepcopy(state); result[purpose]={"granted":granted,"version":int(version),"at":_iso(instant)}; return result
def proxy_task_navigation(tasks,completed=()):
 if not isinstance(tasks,list): raise ValueError("invalid proxy tasks")
 done=set(completed); ready=[x["id"] for x in tasks if x.get("id") not in done and set(x.get("depends_on",[]))<=done]
 return {"completed":sorted(done),"ready":ready,"next":ready[0] if ready else None}
def proxy_device_sync(local,remote):
 if not isinstance(local,dict) or not isinstance(remote,dict): raise ValueError("invalid proxy sync")
 merged={}; conflicts=[]
 for key in sorted(set(local)|set(remote)):
  candidates=[x for x in (local.get(key),remote.get(key)) if x]
  if len(candidates)==2 and candidates[0].get("revision")==candidates[1].get("revision") and candidates[0].get("value")!=candidates[1].get("value"): conflicts.append(key)
  merged[key]=copy.deepcopy(max(candidates,key=lambda x:(x.get("revision",0),str(x.get("device","")))))
 return {"merged":merged,"conflicts":conflicts}
def proxy_duplicate_detection(proxies):
 if not isinstance(proxies,list): raise ValueError("invalid proxies")
 groups=defaultdict(list)
 for row in proxies:
  endpoint=str(row.get("endpoint","")).lower().rstrip("/"); groups[(endpoint,row.get("credentials_ref"))].append(row.get("id"))
 return [{"endpoint":key[0],"credentials_ref":key[1],"ids":ids} for key,ids in groups.items() if len(ids)>1]
def proxy_adaptive_quota(base,requests,health_score):
 if not isinstance(base,int) or base<1 or not isinstance(requests,int) or requests<0 or not 0<=health_score<=1: raise ValueError("invalid proxy quota")
 limit=max(1,round(base*(.5+health_score))); return {"limit":limit,"requests":requests,"remaining":max(0,limit-requests),"throttled":requests>=limit}
def proxy_community_impact(events):
 weights={"shared_node":5,"incident_report":3,"documentation":2}
 if not isinstance(events,list) or any(x.get("type") not in weights or x.get("count",0)<0 for x in events): raise ValueError("invalid proxy impact")
 totals=Counter()
 for row in events: totals[row["type"]]+=row["count"]
 return {"totals":dict(totals),"score":sum(totals[k]*w for k,w in weights.items()),"public_safe":True}
def proxy_reviewable_translation(proxy_id,locale,label,reviewer=None):
 if not proxy_id or len(str(locale))<2 or not str(label).strip(): raise ValueError("invalid proxy translation")
 return {"proxy_id":proxy_id,"locale":locale,"label":str(label).strip(),"status":"approved" if reviewer else "pending_review","reviewer":reviewer}
def proxy_grouped_notifications(items):
 if not isinstance(items,list): raise ValueError("invalid proxy notifications")
 groups=defaultdict(list)
 for item in items:
  if not item.get("proxy_id") or item.get("severity") not in {"info","warning","critical"}: raise ValueError("invalid notification")
  groups[item["proxy_id"]].append(copy.deepcopy(item))
 return [{"proxy_id":key,"count":len(rows),"highest":max((x["severity"] for x in rows),key={"info":0,"warning":1,"critical":2}.get),"items":rows} for key,rows in sorted(groups.items())]
def proxy_migration_assistant(source_version,target_version):
 if not isinstance(source_version,int) or not isinstance(target_version,int) or target_version<=source_version: raise ValueError("invalid proxy migration")
 return {"from":source_version,"to":target_version,"steps":[{"version":v,"validate_connectivity":True,"executed":False} for v in range(source_version+1,target_version+1)],"rollback_plan":True}
def proxy_admin_decision_log(log,decision_id,operator,action,reason,instant):
 if not isinstance(log,list) or any(x.get("id")==decision_id for x in log) or action not in {"enable","disable","rotate","quarantine"} or len(str(reason).strip())<5: raise ValueError("invalid proxy decision")
 row={"id":decision_id,"operator":operator,"action":action,"reason":str(reason).strip(),"at":_iso(instant),"previous":log[-1]["digest"] if log else ""}; row["digest"]=hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest(); return copy.deepcopy(log)+[row]
def _time(value):
 if isinstance(value,str): value=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
 if not isinstance(value,dt.datetime) or value.tzinfo is None: raise ValueError("aware datetime required")
 return value.astimezone(dt.timezone.utc)
def _iso(value): return _time(value).isoformat().replace("+00:00","Z")

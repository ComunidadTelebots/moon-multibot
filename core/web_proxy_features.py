"""Proxy-specific Web contracts for future-0091..0110."""
import copy, hashlib, hmac, json, statistics
from urllib.parse import urlparse
from core.web_creator_features import _iso
def proxy_forecast(latencies):
 if not isinstance(latencies,list) or len(latencies)<3 or any(not isinstance(x,(int,float)) or x<0 for x in latencies):raise ValueError("invalid latency series")
 slope=(latencies[-1]-latencies[0])/(len(latencies)-1);return {"next_latency_ms":max(0,round(latencies[-1]+slope,2)),"degrading":slope>0,"slope":slope}
def proxy_guided_setup(proxy):
 checks=[("endpoint",bool(proxy.get("host") and proxy.get("port"))), ("credentials",bool(proxy.get("secret_ref"))), ("healthcheck",bool(proxy.get("healthcheck_url")))];return {"completed":[k for k,v in checks if v],"next":next((k for k,v in checks if not v),None),"ready":all(v for _,v in checks)}
def proxy_adaptive_alert(latency,baseline,failures):
 if any(not isinstance(x,(int,float)) or x<0 for x in (latency,baseline,failures)):raise ValueError("invalid proxy signal")
 threshold=max(100,baseline*1.5);return {"triggered":latency>threshold or failures>=3,"latency_threshold":threshold,"reasons":[x for x,v in (("latency",latency>threshold),("failures",failures>=3)) if v]}
def proxy_automation(rule,proxy):
 if rule.get("trigger") not in {"offline","latency_above","region"} or rule.get("action") not in {"rotate","disable","review"}:raise ValueError("invalid proxy rule")
 val=not proxy.get("online") if rule["trigger"]=="offline" else proxy.get("latency_ms",0)>rule.get("value",0) if rule["trigger"]=="latency_above" else proxy.get("region")==rule.get("value");return {"matched":val,"plan":[rule["action"]] if val else [],"executed":False}
def proxy_temporal_compare(now,previous):
 keys={"latency_ms","uptime_percent","failures"}
 if set(now)!=keys or set(previous)!=keys:raise ValueError("invalid proxy periods")
 return {k:{"current":now[k],"previous":previous[k],"delta":now[k]-previous[k],"improved":now[k]>=previous[k] if k=="uptime_percent" else now[k]<=previous[k]} for k in sorted(keys)}
def proxy_signed_export(proxies,secret):
 if not isinstance(proxies,list) or len(str(secret))<16:raise ValueError("invalid proxy export")
 public=[{k:x.get(k) for k in ("id","region","status","latency_ms")} for x in proxies];body=json.dumps(public,sort_keys=True,separators=(",",":"));return {"body":body,"signature":hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest(),"credentials_included":False}
def proxy_simulation(proxy,change):
 if change.get("field") not in {"region","enabled","rotation_weight"}:raise ValueError("invalid proxy simulation")
 after=copy.deepcopy(proxy);after[change["field"]]=change.get("value");return {"before":copy.deepcopy(proxy),"after":after,"connectivity_tested":False,"applied":False}
def proxy_version(history,config,actor,now):
 safe={k:config.get(k) for k in ("id","host","port","region","enabled")};digest=hashlib.sha256(json.dumps(safe,sort_keys=True).encode()).hexdigest()
 if history and history[-1]["digest"]==digest:return copy.deepcopy(history)
 return copy.deepcopy(history)+[{"version":len(history)+1,"config":safe,"digest":digest,"actor":actor,"at":_iso(now)}]
def proxy_semantic_search(query,proxies):
 terms=set(str(query).lower().split());rows=[]
 for x in proxies:
  words=set(f'{x.get("region","")} {x.get("provider","")} {x.get("status","")}'.lower().split());score=len(terms&words)
  if score:rows.append({"id":x["id"],"score":score,"matched":sorted(terms&words)})
 return sorted(rows,key=lambda x:(-x["score"],x["id"]))
def proxy_summary(proxies):
 if not isinstance(proxies,list):raise ValueError("invalid proxies")
 online=sum(bool(x.get("online")) for x in proxies);lat=[x["latency_ms"] for x in proxies if isinstance(x.get("latency_ms"),(int,float))]
 return {"total":len(proxies),"online":online,"offline":len(proxies)-online,"median_latency_ms":statistics.median(lat) if lat else None,"hosts_included":False}
def proxy_permission(policy,actor,action,proxy_id):
 if action not in {"view","assign","rotate","delete"}:raise ValueError("invalid proxy action")
 grants=policy.get(actor,{}) if isinstance(policy,dict) else {};allowed=action in grants.get(proxy_id,[]) or action in grants.get("*",[]);return {"allowed":allowed,"scope":proxy_id,"reason":"scoped_grant" if allowed else "default_deny"}
def proxy_template(template,values):
 required={"region","provider","port"}
 if set(values)!=required or not isinstance(values["port"],int) or not 1<=values["port"]<=65535:raise ValueError("invalid proxy template")
 return {"config":{"region":values["region"],"provider":values["provider"],"port":values["port"]},"template":template,"secret_required":True}
def proxy_bulk_plan(proxies,enabled):
 if not isinstance(enabled,bool) or len({x.get("id") for x in proxies})!=len(proxies):raise ValueError("invalid proxy bulk")
 return {"operations":[{"id":x["id"],"before":bool(x.get("enabled")),"after":enabled} for x in proxies],"undo_available":True,"applied":False}
def proxy_calendar(rotations,timezone):
 if "/" not in str(timezone):raise ValueError("invalid rotation calendar")
 rows=sorted(({"proxy_id":x["proxy_id"],"rotate_at":_iso(x["rotate_at"])} for x in rotations),key=lambda x:x["rotate_at"]);return {"timezone":timezone,"rotations":rows,"next_run":rows[0]["rotate_at"] if rows else None,"automatic":False}
def proxy_privacy(proxy):
 if not isinstance(proxy,dict):raise ValueError("invalid proxy")
 return {k:("[redacted]" if k in {"host","username","password","secret_ref"} else copy.deepcopy(v)) for k,v in proxy.items()}
def proxy_diagnostics(proxy):
 checks={"id":bool(proxy.get("id")),"port":isinstance(proxy.get("port"),int) and 1<=proxy["port"]<=65535,"protocol":proxy.get("protocol") in {"mtproto","socks5","https"},"latency":isinstance(proxy.get("latency_ms"),(int,float)) and proxy["latency_ms"]>=0};return {"healthy":all(checks.values()),"checks":checks,"failures":[k for k,v in checks.items() if not v]}
def proxy_recommendations(proxy,metrics):
 rows=[]
 if metrics.get("latency_ms",0)>500:rows.append({"action":"change_region","score":90,"because":"high_latency"})
 if metrics.get("failures",0)>=3:rows.append({"action":"rotate_credentials","score":100,"because":"repeated_failures"})
 return sorted(rows,key=lambda x:-x["score"])
def proxy_approval(request,reviewer,decision,now):
 if request.get("status")!="pending" or decision not in {"approved","rejected"} or reviewer==request.get("requested_by"):raise ValueError("invalid proxy approval")
 return {**copy.deepcopy(request),"status":decision,"reviewer":reviewer,"reviewed_at":_iso(now)}
def proxy_comment(thread,comment):
 if comment.get("kind") not in {"incident","maintenance","performance"} or not str(comment.get("text","")).strip() or any(x.get("id")==comment.get("id") for x in thread):raise ValueError("invalid proxy comment")
 return copy.deepcopy(thread)+[{"id":comment["id"],"kind":comment["kind"],"text":comment["text"].strip(),"resolved":False}]
def proxy_metric(state,event):
 if event.get("type") not in {"request","failure","rotation","healthcheck"} or not event.get("id"):raise ValueError("invalid proxy metric")
 out=copy.deepcopy(state or {"seen":[],"counts":{}})
 if event["id"] in out["seen"]:return out
 out["seen"].append(event["id"]);out["counts"][event["type"]]=out["counts"].get(event["type"],0)+1;return out

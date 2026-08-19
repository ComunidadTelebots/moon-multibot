"""Web proxy/dashboard contracts for future-0111..0130."""
import copy, hashlib, hmac, json, statistics
from urllib.parse import urlparse
from core.web_creator_features import _iso
def proxy_accessibility(config):
 if config.get("status_labels") is not True or config.get("contrast") not in {"normal","high"}:raise ValueError("invalid proxy accessibility")
 return {"contrast":config["contrast"],"status_labels":True,"latency_text":True,"color_only":False}
def proxy_webhook(url,event,proxy,secret):
 if event not in {"proxy.online","proxy.offline","proxy.rotated"} or urlparse(str(url)).scheme!="https" or len(str(secret))<16:raise ValueError("invalid proxy webhook")
 body=json.dumps({k:proxy.get(k) for k in ("id","region","status")},sort_keys=True,separators=(",",":"));return {"url":url,"event":event,"body":body,"signature":hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest(),"sent":False}
def proxy_anomaly(samples):
 if not isinstance(samples,list) or len(samples)<3:raise ValueError("invalid proxy samples")
 baseline=statistics.median(x["latency_ms"] for x in samples[:-1]);latest=samples[-1];return {"proxy_id":latest["proxy_id"],"anomaly":latest["latency_ms"]>max(200,baseline*3),"baseline":baseline,"latest":latest["latency_ms"]}
def proxy_learning(completed,protocol):
 paths={"mtproto":["secret","tls","rotation"],"socks5":["auth","dns","rotation"]}
 if protocol not in paths or set(completed)-set(paths[protocol]):raise ValueError("invalid proxy learning")
 left=[x for x in paths[protocol] if x not in completed];return {"protocol":protocol,"next":left[0] if left else None,"completed":not left}
def proxy_language(language,labels):
 required={"online","offline","degraded"}
 if language not in {"es","en","ca"} or set(labels)!=required or any(not str(v).strip() for v in labels.values()):raise ValueError("invalid proxy language")
 return {"language":language,"labels":copy.deepcopy(labels),"fallback":"es" if language!="es" else None}
def proxy_compact(proxy,fields):
 allowed={"id","region","status","latency_ms","provider"}
 if not isinstance(fields,list) or not fields or set(fields)-allowed:raise ValueError("invalid proxy compact fields")
 return {"fields":{k:copy.deepcopy(proxy.get(k)) for k in fields},"credentials_included":False,"density":"compact"}
def proxy_recovery(current,snapshot,fields):
 allowed={"region","enabled","rotation_weight","provider"}
 if not fields or set(fields)-allowed or any(k not in snapshot for k in fields):raise ValueError("invalid proxy recovery")
 return {"proxy_id":current.get("id"),"restore":{k:snapshot[k] for k in fields},"before":{k:current.get(k) for k in fields},"applied":False}
def proxy_report(config,proxies):
 if config.get("frequency") not in {"hourly","daily","weekly"} or config.get("format") not in {"json","csv"}:raise ValueError("invalid proxy report")
 return {"frequency":config["frequency"],"format":config["format"],"total":len(proxies),"online":sum(bool(x.get("online")) for x in proxies),"hostnames_included":False,"delivered":False}
def proxy_sandbox(proxy,operation):
 if operation.get("type") not in {"rotate","disable","change_region"}:raise ValueError("invalid proxy sandbox")
 after=copy.deepcopy(proxy)
 if operation["type"]=="disable":after["enabled"]=False
 elif operation["type"]=="change_region":after["region"]=operation.get("region")
 else:after["rotation_pending"]=True
 return {"before":copy.deepcopy(proxy),"after":after,"network_calls":0,"effects":[]}
def proxy_connector(proxy,standard):
 if standard not in {"proxy-config-v1","clash","mtproto-link"} or not proxy.get("id"):raise ValueError("invalid proxy connector")
 return {"standard":standard,"resource":{"id":proxy["id"],"region":proxy.get("region"),"protocol":proxy.get("protocol")},"secret_reference_required":True,"secret_included":False}
def dashboard_forecast(metrics):
 required={"active_users","pending_tasks","incidents"}
 if set(metrics)!=required or any(not isinstance(v,list) or len(v)<2 for v in metrics.values()):raise ValueError("invalid dashboard history")
 return {k:max(0,round(v[-1]+(v[-1]-v[0])/(len(v)-1),2)) for k,v in metrics.items()}
def dashboard_guided(state):
 steps=[("security",state.get("mfa_enabled")),("bots",state.get("active_bots",0)>0),("alerts",state.get("alerts_configured"))];return {"next":next((k for k,v in steps if not v),None),"completed":[k for k,v in steps if v],"ready":all(v for _,v in steps)}
def dashboard_alert(metric,value,policy):
 if metric not in {"incidents","queue_depth","error_rate"} or not isinstance(value,(int,float)) or metric not in policy:raise ValueError("invalid dashboard alert")
 return {"metric":metric,"triggered":value>=policy[metric],"value":value,"threshold":policy[metric],"severity":"critical" if value>=policy[metric]*2 else "warning"}
def dashboard_automation(rule,snapshot):
 if rule.get("metric") not in {"incidents","queue_depth","offline_bots"} or rule.get("action") not in {"notify","open_incident","pause_queue"}:raise ValueError("invalid dashboard automation")
 matched=snapshot.get(rule["metric"],0)>=rule.get("at_least",1);return {"matched":matched,"planned":[rule["action"]] if matched else [],"executed":False}
def dashboard_compare(current,previous):
 if set(current)!=set(previous) or any(not isinstance(v,(int,float)) for v in [*current.values(),*previous.values()]):raise ValueError("invalid dashboard comparison")
 return {"metrics":{k:{"delta":current[k]-previous[k]} for k in sorted(current)},"periods_comparable":True}
def dashboard_signed(snapshot,secret):
 if not isinstance(snapshot,dict) or len(str(secret))<16:raise ValueError("invalid dashboard signature")
 body=json.dumps(snapshot,sort_keys=True,separators=(",",":"));return {"digest":hashlib.sha256(body.encode()).hexdigest(),"signature":hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest(),"body":body}
def dashboard_simulation(state,widgets):
 allowed={"security","bots","queue","analytics","alerts"}
 if not isinstance(widgets,list) or len(widgets)!=len(set(widgets)) or set(widgets)-allowed:raise ValueError("invalid dashboard simulation")
 return {"before":copy.deepcopy(state.get("widgets",[])),"after":list(widgets),"layout_saved":False,"effects":[]}
def dashboard_version(history,layout,actor,now):
 if not isinstance(layout,list) or len(layout)!=len(set(layout)):raise ValueError("invalid dashboard layout")
 digest=hashlib.sha256(json.dumps(layout).encode()).hexdigest()
 if history and history[-1]["digest"]==digest:return copy.deepcopy(history)
 return copy.deepcopy(history)+[{"version":len(history)+1,"layout":list(layout),"actor":actor,"at":_iso(now),"digest":digest}]
def dashboard_search(query,widgets):
 terms=set(str(query).lower().split());rows=[]
 for w in widgets:
  words=set(f'{w.get("title","")} {w.get("description","")}'.lower().split());score=len(terms&words)
  if score:rows.append({"widget_id":w["id"],"score":score})
 return sorted(rows,key=lambda x:(-x["score"],x["widget_id"]))
def dashboard_summary(snapshot):
 required={"active_bots","pending_tasks","incidents","users_online"}
 if not isinstance(snapshot,dict) or not required<=set(snapshot):raise ValueError("invalid dashboard snapshot")
 return {"headline":f'{snapshot["active_bots"]} bots · {snapshot["incidents"]} incidents',"metrics":{k:snapshot[k] for k in sorted(required)},"method":"exact_snapshot","pii_included":False}

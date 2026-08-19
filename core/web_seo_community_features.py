"""Web SEO/community contracts for future-0231..0250."""
import copy,hashlib,hmac,json,statistics
from urllib.parse import urlparse
from core.web_creator_features import _iso
def seo_accessibility(c):
 if c.get("headings") is not True or c.get("alt_text") is not True:raise ValueError("invalid accessible SEO")
 return {"headings":True,"alt_text":True,"link_labels":True,"screen_reader_metadata":True}
def seo_webhook(url,event,page,secret):
 if event not in {"seo.audit_failed","seo.rank_changed","seo.indexed"} or urlparse(str(url)).scheme!="https" or len(str(secret))<16:raise ValueError("invalid SEO webhook")
 body=json.dumps({k:page.get(k) for k in ("url","rank","indexable")},sort_keys=True);return {"event":event,"body":body,"signature":hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest(),"sent":False}
def seo_anomaly(ranks):
 if len(ranks)<4:raise ValueError("invalid ranks")
 base=statistics.median(ranks[:-1]);return {"anomaly":abs(ranks[-1]-base)>10,"baseline_rank":base,"latest_rank":ranks[-1]}
def seo_learning(done,track):
 tracks={"editor":["titles","links","schema"],"technical":["crawl","index","performance"]}
 if track not in tracks or set(done)-set(tracks[track]):raise ValueError("invalid SEO learning")
 left=[x for x in tracks[track] if x not in done];return {"next":left[0] if left else None,"certified":not left}
def seo_language(lang,keywords):
 if lang not in {"es","en","ca"} or not isinstance(keywords,list) or not keywords:raise ValueError("invalid SEO language")
 return {"language":lang,"keywords":sorted(set(keywords)),"hreflang":lang,"fallback":"es" if lang!="es" else None}
def seo_compact(page,fields):
 allowed={"url","title","rank","indexable","score"}
 if not fields or set(fields)-allowed:raise ValueError("invalid compact SEO")
 return {"fields":{k:page.get(k) for k in fields},"content_included":False}
def seo_recovery(current,snapshot,fields):
 allowed={"title","description","canonical","indexable"}
 if not fields or set(fields)-allowed or any(k not in snapshot for k in fields):raise ValueError("invalid SEO recovery")
 return {"restore":{k:snapshot[k] for k in fields},"before":{k:current.get(k) for k in fields},"applied":False}
def seo_report(config,pages):
 if config.get("frequency") not in {"weekly","monthly"} or config.get("format") not in {"json","csv"}:raise ValueError("invalid SEO report")
 return {"frequency":config["frequency"],"pages":len(pages),"issues":sum(not x.get("healthy",False) for x in pages),"delivered":False}
def seo_sandbox(page,change):
 if change.get("field") not in {"title","description","canonical","indexable"}:raise ValueError("invalid SEO sandbox")
 after=copy.deepcopy(page);after[change["field"]]=change.get("value");return {"before":copy.deepcopy(page),"after":after,"reindexed":False,"effects":[]}
def seo_connector(pages,standard):
 if standard not in {"sitemap","indexnow","search-console"}:raise ValueError("invalid SEO connector")
 return {"standard":standard,"urls":[x["url"] for x in pages],"credentials_included":False,"submitted":False}
def community_forecast(series):
 if len(series)<3 or any(not isinstance(x,int) or x<0 for x in series):raise ValueError("invalid member series")
 slope=(series[-1]-series[0])/(len(series)-1);return {"next_members":max(0,round(series[-1]+slope)),"growth":slope,"method":"member_trend"}
def community_guided(state):
 steps=[("identity",bool(state.get("name"))),("rules",bool(state.get("rules"))),("moderators",state.get("moderators",0)>0)];return {"next":next((k for k,v in steps if not v),None),"completed":[k for k,v in steps if v],"ready":all(v for _,v in steps)}
def community_alert(metric,value,policy):
 if metric not in {"reports","departures","engagement","growth"} or metric not in policy:raise ValueError("invalid community alert")
 bad=value>=policy[metric] if metric in {"reports","departures"} else value<=policy[metric];return {"metric":metric,"triggered":bad,"value":value,"threshold":policy[metric]}
def community_automation(rule,event):
 if rule.get("trigger") not in {"member_joined","report_created","milestone"} or rule.get("action") not in {"welcome","notify_mods","celebrate"}:raise ValueError("invalid community automation")
 matched=event.get("type")==rule["trigger"];return {"matched":matched,"plan":[rule["action"]] if matched else [],"executed":False}
def community_compare(current,previous):
 keys={"members","active","reports","posts"}
 if set(current)!=keys or set(previous)!=keys:raise ValueError("invalid community periods")
 return {k:{"delta":current[k]-previous[k]} for k in sorted(keys)}
def community_signed_export(community,secret):
 if not community.get("id") or len(str(secret))<16:raise ValueError("invalid community export")
 public={k:community.get(k) for k in ("id","name","member_count","rules")};body=json.dumps(public,sort_keys=True);return {"body":body,"signature":hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest(),"member_ids_included":False}
def community_simulation(state,operation):
 if operation.get("type") not in {"rename","change_rules","set_visibility"}:raise ValueError("invalid community simulation")
 after=copy.deepcopy(state);after[{"rename":"name","change_rules":"rules","set_visibility":"visibility"}[operation["type"]]]=operation.get("value");return {"before":copy.deepcopy(state),"after":after,"applied":False}
def community_version(history,config,actor,now):
 digest=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
 if history and history[-1]["digest"]==digest:return copy.deepcopy(history)
 return copy.deepcopy(history)+[{"version":len(history)+1,"config":copy.deepcopy(config),"actor":actor,"at":_iso(now),"digest":digest}]
def community_search(query,communities):
 terms=set(str(query).lower().split());rows=[]
 for c in communities:
  words=set(f'{c.get("name","")} {c.get("description","")} {" ".join(c.get("topics",[]))}'.lower().split());score=len(terms&words)
  if score:rows.append({"id":c["id"],"score":score})
 return sorted(rows,key=lambda x:(-x["score"],x["id"]))
def community_summary(communities):
 if not isinstance(communities,list):raise ValueError("invalid communities")
 return {"communities":len(communities),"members":sum(x.get("member_count",0) for x in communities),"active":sum(x.get("active",False) for x in communities),"member_ids_included":False}

"""SEO-specific Web contracts for future-0211..0230."""
import copy, hashlib, hmac, json, re, statistics
from core.web_creator_features import _iso
def seo_forecast(ranks):
 if len(ranks)<3 or any(not isinstance(x,int) or x<1 for x in ranks):raise ValueError("invalid rankings")
 slope=(ranks[-1]-ranks[0])/(len(ranks)-1);return {"next_rank":max(1,round(ranks[-1]+slope)),"improving":slope<0,"slope":slope}
def seo_guided_setup(page):
 checks=[("title",0<len(page.get("title",""))<=60),("description",50<=len(page.get("description",""))<=160),("canonical",str(page.get("canonical","" )).startswith("https://")),("indexable",page.get("indexable") is True)];return {"completed":[k for k,v in checks if v],"next":next((k for k,v in checks if not v),None),"ready":all(v for _,v in checks)}
def seo_alert(metric,value,threshold):
 if metric not in {"rank","organic_clicks","crawl_errors","ctr"} or not isinstance(value,(int,float)) or not isinstance(threshold,(int,float)):raise ValueError("invalid seo alert")
 bad=value>threshold if metric in {"rank","crawl_errors"} else value<threshold;return {"metric":metric,"triggered":bad,"value":value,"threshold":threshold}
def seo_automation(rule,page):
 if rule.get("trigger") not in {"missing_title","missing_canonical","noindex"} or rule.get("action") not in {"queue_fix","notify_editor","open_audit"}:raise ValueError("invalid seo automation")
 matched={"missing_title":not page.get("title"),"missing_canonical":not page.get("canonical"),"noindex":not page.get("indexable",True)}[rule["trigger"]];return {"matched":matched,"plan":[rule["action"]] if matched else [],"executed":False}
def seo_compare(current,previous):
 keys={"organic_clicks","impressions","average_rank","indexed_pages"}
 if set(current)!=keys or set(previous)!=keys:raise ValueError("invalid seo periods")
 return {k:{"delta":current[k]-previous[k],"improved":current[k]<=previous[k] if k=="average_rank" else current[k]>=previous[k]} for k in sorted(keys)}
def seo_signed_export(rows,secret):
 if not isinstance(rows,list) or len(str(secret))<16:raise ValueError("invalid seo export")
 body=json.dumps(rows,sort_keys=True,separators=(",",":"));return {"rows":len(rows),"digest":hashlib.sha256(body.encode()).hexdigest(),"signature":hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest(),"body":body}
def seo_simulation(page,changes):
 allowed={"title","description","canonical","indexable"}
 if set(changes)-allowed:raise ValueError("invalid seo simulation")
 after={**copy.deepcopy(page),**copy.deepcopy(changes)};return {"before":copy.deepcopy(page),"after":after,"score_before":_score(page),"score_after":_score(after),"saved":False}
def seo_version(history,metadata,actor,now):
 if not isinstance(metadata,dict) or not metadata.get("url"):raise ValueError("invalid seo metadata")
 digest=hashlib.sha256(json.dumps(metadata,sort_keys=True).encode()).hexdigest()
 if history and history[-1]["digest"]==digest:return copy.deepcopy(history)
 return copy.deepcopy(history)+[{"version":len(history)+1,"metadata":copy.deepcopy(metadata),"actor":actor,"at":_iso(now),"digest":digest}]
def seo_search(query,pages):
 terms=set(str(query).lower().split());rows=[]
 for p in pages:
  words=set(f'{p.get("title","")} {p.get("description","")} {" ".join(p.get("keywords",[]))}'.lower().split());score=len(terms&words)
  if score:rows.append({"url":p["url"],"score":score,"matched":sorted(terms&words)})
 return sorted(rows,key=lambda x:(-x["score"],x["url"]))
def seo_summary(pages):
 if not isinstance(pages,list):raise ValueError("invalid seo pages")
 scores=[_score(x) for x in pages];return {"pages":len(pages),"average_score":statistics.mean(scores) if scores else None,"indexable":sum(x.get("indexable") is True for x in pages),"page_content_included":False}
def seo_permission(policy,actor,site,action):
 if action not in {"audit","edit_metadata","submit_index","export"}:raise ValueError("invalid seo permission")
 allowed=action in policy.get(actor,{}).get(site,[]) if isinstance(policy,dict) else False;return {"allowed":allowed,"site":site,"reason":"site_grant" if allowed else "default_deny"}
def seo_template(name,title_pattern,description_pattern):
 if not str(name).strip() or "{title}" not in title_pattern or not description_pattern:raise ValueError("invalid seo template")
 return {"name":name.strip(),"title_pattern":title_pattern,"description_pattern":description_pattern,"reusable":True}
def seo_bulk_plan(pages,changes):
 if set(changes)-{"indexable","canonical_host"} or len({x.get("url") for x in pages})!=len(pages):raise ValueError("invalid seo bulk")
 return {"operations":[{"url":x["url"],"changes":copy.deepcopy(changes)} for x in pages],"undo_available":True,"applied":False}
def seo_calendar(audits,timezone):
 if "/" not in str(timezone):raise ValueError("invalid seo calendar")
 rows=sorted(({"site":x["site"],"at":_iso(x["at"])} for x in audits),key=lambda x:x["at"]);return {"timezone":timezone,"audits":rows,"next_run":rows[0]["at"] if rows else None,"executed":False}
def seo_privacy(page):
 if not isinstance(page,dict):raise ValueError("invalid seo page")
 return {"metadata":{k:v for k,v in page.items() if k not in {"author_email","editor_ip","token"}},"pii_included":False}
def seo_diagnostics(page):
 checks={"title":0<len(page.get("title",""))<=60,"description":50<=len(page.get("description",""))<=160,"canonical":str(page.get("canonical","")).startswith("https://"),"status":page.get("status_code")==200};return {"healthy":all(checks.values()),"checks":checks,"failures":[k for k,v in checks.items() if not v]}
def seo_recommendations(page):
 rows=[]
 if len(page.get("title",""))>60:rows.append({"action":"shorten_title","score":90,"because":"title_length"})
 if not page.get("canonical"):rows.append({"action":"add_canonical","score":100,"because":"missing_canonical"})
 return sorted(rows,key=lambda x:-x["score"])
def seo_approval(request,reviewer,decision,now):
 if request.get("status")!="pending" or request.get("kind") not in {"metadata","redirect","indexing"} or decision not in {"approved","rejected"} or reviewer==request.get("requested_by"):raise ValueError("invalid seo approval")
 return {**copy.deepcopy(request),"status":decision,"reviewer":reviewer,"at":_iso(now)}
def seo_comment(thread,comment):
 if not comment.get("url") or not str(comment.get("text","")).strip() or any(x.get("id")==comment.get("id") for x in thread):raise ValueError("invalid seo comment")
 return copy.deepcopy(thread)+[{"id":comment["id"],"url":comment["url"],"text":comment["text"].strip(),"resolved":False}]
def seo_metric(state,event):
 if event.get("type") not in {"crawl","click","impression","index"} or not event.get("id"):raise ValueError("invalid seo metric")
 out=copy.deepcopy(state or {"seen":[],"counts":{}})
 if event["id"] in out["seen"]:return out
 out["seen"].append(event["id"]);out["counts"][event["type"]]=out["counts"].get(event["type"],0)+1;return out
def _score(p):return 25*sum((0<len(p.get("title",""))<=60,50<=len(p.get("description",""))<=160,bool(p.get("canonical")),p.get("indexable") is True))

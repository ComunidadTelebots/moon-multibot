"""News-specific Web contracts for future-0071..0090."""
import copy, hashlib, hmac, json, re, statistics
from urllib.parse import urlparse
from core.web_creator_features import _iso

def news_permission(policy,editor,operation,article_status):
 if operation not in {"edit","review","publish","archive"} or article_status not in {"draft","review","published","archived"}: raise ValueError("invalid editorial permission")
 grants=policy.get(editor,[]) if isinstance(policy,dict) else []; allowed=operation in grants and not (operation=="edit" and article_status=="archived")
 return {"allowed":allowed,"editor":editor,"operation":operation,"reason":"grant" if allowed else "editorial_default_deny"}
def news_template(template,values):
 required={"title","summary","source_url"}; p=urlparse(str(values.get("source_url","")))
 if set(values)!=required or p.scheme!="https" or set(re.findall(r"\{(\w+)\}",template))!=required: raise ValueError("invalid article template")
 return {"article":template.format(**values),"source_host":p.hostname,"draft":True}
def news_bulk_plan(articles,transition):
 allowed={"draft":"review","review":"published","published":"archived"}
 if not isinstance(articles,list) or len({x.get("id") for x in articles})!=len(articles): raise ValueError("invalid article batch")
 ops=[]
 for x in articles:
  if allowed.get(x.get("status"))!=transition: raise ValueError("invalid editorial transition")
  ops.append({"id":x["id"],"from":x["status"],"to":transition})
 return {"operations":ops,"undo":{"transition":{ "review":"draft","published":"review","archived":"published"}[transition]},"applied":False}
def news_calendar(items,timezone):
 if "/" not in str(timezone) or not isinstance(items,list): raise ValueError("invalid editorial calendar")
 rows=sorted(({"article_id":x["article_id"],"publish_at":_iso(x["publish_at"]),"slot":x.get("slot","standard")} for x in items),key=lambda x:x["publish_at"])
 if len({x["publish_at"] for x in rows})!=len(rows): raise ValueError("publication slot collision")
 return {"timezone":timezone,"items":rows,"next_run":rows[0]["publish_at"] if rows else None,"publishes_automatically":False}
def news_privacy(article):
 if not isinstance(article,dict): raise ValueError("invalid article")
 banned={"author_email","editor_ip","source_token","internal_notes"}; public={k:copy.deepcopy(v) for k,v in article.items() if k not in banned}
 return {"public":public,"removed":sorted(set(article)&banned),"pii_included":False}
def news_diagnostics(article):
 if not isinstance(article,dict): raise ValueError("invalid article")
 checks={"title":bool(article.get("title")),"slug":bool(re.fullmatch(r"[a-z0-9-]+",str(article.get("slug","")))),"sources":len(article.get("sources",[]))>=1,"summary":len(str(article.get("summary","")))>=20}
 return {"publishable":all(checks.values()),"checks":checks,"blocking":[k for k,v in checks.items() if not v]}
def news_recommendations(article,metrics):
 if not isinstance(article,dict) or not isinstance(metrics,dict): raise ValueError("invalid news recommendation")
 rows=[]
 if len(article.get("sources",[]))<2: rows.append({"action":"add_source","score":90,"because":"single_source"})
 if metrics.get("read_completion",1)<.4: rows.append({"action":"shorten_intro","score":70,"because":"low_completion"})
 return sorted(rows,key=lambda x:-x["score"])
def news_approval(request,reviewer,decision,now):
 if request.get("status")!="review" or decision not in {"publish","changes_requested"} or reviewer==request.get("author_id"): raise ValueError("invalid editorial approval")
 return {**copy.deepcopy(request),"status":"published" if decision=="publish" else "draft","decision":decision,"reviewer":reviewer,"at":_iso(now)}
def news_comment(thread,comment):
 if not isinstance(thread,list) or not isinstance(comment,dict) or not str(comment.get("text","")).strip() or comment.get("anchor") not in {"title","summary","body","sources"} or any(x.get("id")==comment.get("id") for x in thread): raise ValueError("invalid editorial comment")
 return copy.deepcopy(thread)+[{"id":comment["id"],"anchor":comment["anchor"],"text":comment["text"].strip(),"author":comment.get("author"),"resolved":False}]
def news_metric(state,event):
 if event.get("type") not in {"view","share","completion","source_click"} or not str(event.get("id","")) or not isinstance(event.get("value",1),(int,float)): raise ValueError("invalid news metric")
 out=copy.deepcopy(state or {"seen":[],"totals":{}})
 if event["id"] in out.setdefault("seen",[]): return out
 out["seen"].append(event["id"]); out.setdefault("totals",{})[event["type"]]=out["totals"].get(event["type"],0)+event.get("value",1); return out
def news_accessibility(config):
 if config.get("reading_level") not in {"plain","standard","expert"} or config.get("image_alt_required") is not True: raise ValueError("invalid news accessibility")
 return {"reading_level":config["reading_level"],"image_alt_required":True,"captions_required":bool(config.get("captions_required",True)),"color_independent":True}
def news_webhook(url,event,article,secret):
 if event not in {"article.created","article.reviewed","article.published"} or urlparse(str(url)).scheme!="https" or len(str(secret))<16: raise ValueError("invalid news webhook")
 payload={k:article.get(k) for k in ("id","slug","status")}; body=json.dumps(payload,sort_keys=True,separators=(",",":")); return {"event":event,"url":url,"body":body,"signature":hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest(),"sent":False}
def news_anomaly(hourly_views):
 if not isinstance(hourly_views,list) or len(hourly_views)<3 or any(not isinstance(x,(int,float)) or x<0 for x in hourly_views): raise ValueError("invalid view series")
 baseline=statistics.median(hourly_views[:-1]); ratio=None if baseline==0 else hourly_views[-1]/baseline
 return {"anomaly":ratio is not None and (ratio>3 or ratio<.2),"baseline":baseline,"latest":hourly_views[-1],"ratio":ratio}
def news_learning(completed,role):
 tracks={"writer":["sources","style","seo"],"editor":["review","fact_check","publish"]}
 if role not in tracks or not isinstance(completed,list) or set(completed)-set(tracks[role]): raise ValueError("invalid editorial learning")
 left=[x for x in tracks[role] if x not in completed]; return {"role":role,"completed":len(set(completed)),"next":left[0] if left else None,"certified":not left}
def news_language(language,translations):
 if language not in {"es","en","ca"} or not isinstance(translations,dict) or language not in translations: raise ValueError("invalid article language")
 return {"primary":language,"available":sorted(k for k,v in translations.items() if str(v).strip()),"fallback":"es" if language!="es" else None,"rtl":False}
def news_compact(article,mode):
 fields={"headline":["title","category","published_at"],"editorial":["title","status","sources","editor"]}
 if mode not in fields or not isinstance(article,dict): raise ValueError("invalid news compact mode")
 return {"mode":mode,"fields":{k:copy.deepcopy(article.get(k)) for k in fields[mode]},"body_included":False}
def news_recovery(current,version,fields):
 allowed={"title","summary","body","category","status"}
 if not isinstance(current,dict) or not isinstance(version,dict) or not fields or set(fields)-allowed or any(k not in version for k in fields): raise ValueError("invalid article recovery")
 return {"article_id":current.get("id"),"restore":{k:copy.deepcopy(version[k]) for k in fields},"current":{k:copy.deepcopy(current.get(k)) for k in fields},"applied":False}
def news_report(config,metrics):
 if config.get("frequency") not in {"daily","weekly"} or config.get("format") not in {"json","csv"} or not isinstance(metrics,dict): raise ValueError("invalid news report")
 return {"schedule":{"frequency":config["frequency"],"timezone":config.get("timezone","Europe/Madrid")},"format":config["format"],"metrics":dict(sorted(metrics.items())),"delivered":False}
def news_sandbox(article,operation):
 if operation.get("type") not in {"change_title","change_category","submit_review"} or not isinstance(article,dict): raise ValueError("invalid news sandbox")
 after=copy.deepcopy(article)
 if operation["type"]=="submit_review": after["status"]="review"
 else: after[{"change_title":"title","change_category":"category"}[operation["type"]]]=operation.get("value")
 return {"before":copy.deepcopy(article),"after":after,"warnings":["publication_not_executed"],"effects":[]}
def news_connector(article,standard):
 if standard not in {"json-feed","rss","activitystreams"} or not article.get("id") or not article.get("title"): raise ValueError("invalid news connector")
 return {"standard":standard,"type":"article","document":{k:article.get(k) for k in ("id","title","summary","url","published_at")},"credentials_included":False}

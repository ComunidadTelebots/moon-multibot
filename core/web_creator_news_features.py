"""Distinct Web contracts for future-0051..0070."""
import copy, hashlib, hmac, json, math, re, statistics
from urllib.parse import urlparse
from core.web_creator_features import creator_forecast, creator_guided_assistant, creator_semantic_search, creator_version_append, _iso

def creator_accessibility(preferences):
 if not isinstance(preferences,dict) or preferences.get("font_scale") not in {1,1.25,1.5,2} or preferences.get("contrast") not in {"normal","high"}: raise ValueError("invalid accessibility")
 return {"font_scale":preferences["font_scale"],"contrast":preferences["contrast"],"reduced_motion":bool(preferences.get("reduced_motion")),"non_color_labels":True}
def creator_webhook_plan(url,events,secret,payload):
 p=urlparse(str(url)); allowed={"creator.created","creator.updated","creator.suspended"}
 if p.scheme!="https" or not p.hostname or not isinstance(events,list) or not events or set(events)-allowed or len(str(secret))<16: raise ValueError("invalid creator webhook")
 body=json.dumps(payload,sort_keys=True,separators=(",",":")); return {"url":url,"events":sorted(set(events)),"body":body,"signature":hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest(),"sent":False}
def creator_anomaly(events):
 if not isinstance(events,list): raise ValueError("invalid anomaly events")
 values=[x.get("value") for x in events]
 if any(not isinstance(x,(int,float)) for x in values): raise ValueError("invalid anomaly value")
 baseline=statistics.median(values); deviations=[abs(x-baseline) for x in values]; threshold=max(10,baseline*2)
 return {"anomalies":[events[i]["id"] for i,d in enumerate(deviations) if d>threshold],"baseline":baseline,"threshold":threshold}
def creator_learning_progress(completed,catalog):
 if not isinstance(completed,list) or not isinstance(catalog,list) or len(set(completed))!=len(completed) or set(completed)-set(catalog): raise ValueError("invalid learning progress")
 remaining=[x for x in catalog if x not in completed]; return {"completed":len(completed),"total":len(catalog),"percent":round(100*len(completed)/max(1,len(catalog))),"next":remaining[0] if remaining else None}
def creator_language_config(language,fallback="es"):
 supported={"es":"ltr","en":"ltr","ca":"ltr","ar":"rtl"}
 if language not in supported or fallback not in supported: raise ValueError("unsupported language")
 return {"language":language,"fallback":fallback,"direction":supported[language],"persistable":True}
def creator_compact_view(fields,hidden):
 if not isinstance(fields,list) or not isinstance(hidden,list) or len(fields)!=len(set(fields)) or set(hidden)-set(fields): raise ValueError("invalid compact view")
 visible=[x for x in fields if x not in hidden]; return {"visible":visible,"hidden":list(hidden),"density":"compact","empty":not visible}
def creator_recovery_plan(current,snapshot,selected):
 allowed={"display_name","category","notifications","language"}
 if not isinstance(current,dict) or not isinstance(snapshot,dict) or not isinstance(selected,list) or set(selected)-allowed or any(k not in snapshot for k in selected): raise ValueError("invalid recovery")
 return {"restore":{k:copy.deepcopy(snapshot[k]) for k in selected},"before":{k:copy.deepcopy(current.get(k)) for k in selected},"applied":False}
def creator_report_schedule(schedule):
 if schedule.get("frequency") not in {"daily","weekly","monthly"} or not re.fullmatch(r"[0-2]\d:[0-5]\d",str(schedule.get("time",""))) or "/" not in str(schedule.get("timezone","")): raise ValueError("invalid report schedule")
 if schedule.get("format") not in {"json","csv"}: raise ValueError("invalid report format")
 return {"frequency":schedule["frequency"],"time":schedule["time"],"timezone":schedule["timezone"],"format":schedule["format"],"enabled":schedule.get("enabled",True),"automatic_delivery":False}
def creator_sandbox(creator,operation):
 if not isinstance(creator,dict) or operation.get("type") not in {"change_category","toggle_verified","set_language"}: raise ValueError("invalid creator sandbox")
 after=copy.deepcopy(creator); field={"change_category":"category","toggle_verified":"verified","set_language":"language"}[operation["type"]]; after[field]=operation.get("value")
 return {"before":copy.deepcopy(creator),"after":after,"field":field,"risks":["visibility_change"] if field=="verified" else [],"effects":[]}
def creator_connector_export(creator,standard):
 if standard not in {"activitystreams","json-feed","portable-profile"} or not isinstance(creator,dict) or not creator.get("id"): raise ValueError("invalid creator connector")
 public={k:creator[k] for k in ("id","display_name","category") if k in creator}; return {"standard":standard,"resource_type":"creator","data":public,"secrets_included":False}
def news_forecast(series):
 result=creator_forecast(series); return {**result,"metric":"publication_demand","confidence":round(min(.95,.5+len(series)/20),2)}
def news_guided_assistant(article):
 mapped={"name":article.get("title"),"mfa":bool(article.get("sources")),"payout_configured":bool(article.get("summary"))}; base=creator_guided_assistant(mapped)
 labels={"identity":"title","security":"sources","payout":"summary"}; return {"completed":[labels[x] for x in base["completed"]],"next":labels.get(base["next"]),"publishable":base["done"]}
def news_adaptive_alert(article,now):
 if article.get("status") not in {"draft","review","published"}: raise ValueError("invalid article status")
 age=(_parse(now)-_parse(article.get("updated_at"))).total_seconds()/3600; limit=24 if article["status"]=="draft" else 6
 return {"triggered":age>limit,"reason":"stale_article" if age>limit else None,"age_hours":round(age,2),"threshold_hours":limit}
def news_automation(rule,article):
 if rule.get("trigger") not in {"category","status","source_count"} or rule.get("action") not in {"queue_review","add_label","notify_editor"}: raise ValueError("invalid news automation")
 value=len(article.get("sources",[])) if rule["trigger"]=="source_count" else article.get(rule["trigger"]); matched=value==rule.get("equals")
 return {"matched":matched,"plan":[rule["action"]] if matched else [],"published":False}
def news_temporal_compare(current,previous):
 required={"views","shares","articles"}
 if set(current)!=required or set(previous)!=required or any(not isinstance(x,(int,float)) or x<0 for x in [*current.values(),*previous.values()]): raise ValueError("invalid news periods")
 return {k:{"delta":current[k]-previous[k],"rate":None if previous[k]==0 else round(current[k]/previous[k]-1,4)} for k in sorted(required)}
def news_signed_export(articles,secret):
 if not isinstance(articles,list) or any(set(x)-{"id","title","slug","status"} for x in articles) or len(str(secret))<16: raise ValueError("invalid news export")
 body=json.dumps(articles,ensure_ascii=False,sort_keys=True,separators=(",",":")); return {"sha256":hashlib.sha256(body.encode()).hexdigest(),"signature":hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest(),"body":body}
def news_simulation(article,changes):
 allowed={"title","summary","category","status"}
 if not isinstance(article,dict) or set(changes)-allowed or changes.get("status",article.get("status")) not in {"draft","review","published"}: raise ValueError("invalid news simulation")
 after={**copy.deepcopy(article),**copy.deepcopy(changes)}; return {"before":copy.deepcopy(article),"after":after,"changed":sorted(k for k in changes if article.get(k)!=changes[k]),"saved":False}
def news_version_append(history,article,editor,now):
 if not article.get("id") or not article.get("title"): raise ValueError("invalid article version")
 return creator_version_append(history,{k:article.get(k) for k in ("id","title","summary","status")},editor,now)
def news_semantic_search(query,articles,limit=5):
 docs=[{"id":x["id"],"text":f'{x.get("title","")} {x.get("summary","")}'} for x in articles]; return creator_semantic_search(query,docs,limit)
def news_explainable_summary(articles):
 if not isinstance(articles,list): raise ValueError("invalid articles")
 status={}; categories={}
 for x in articles: status[x.get("status","unknown")]=status.get(x.get("status","unknown"),0)+1; categories[x.get("category","other")]=categories.get(x.get("category","other"),0)+1
 return {"total":len(articles),"by_status":dict(sorted(status.items())),"by_category":dict(sorted(categories.items())),"method":"exact_counts","article_bodies_included":False}
def _parse(value):
 import datetime as dt
 if isinstance(value,str): value=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
 if value.tzinfo is None: raise ValueError("aware datetime required")
 return value

"""Pure, persistable contracts for Web creator features future-0031..0050."""
import copy, datetime as dt, hashlib, hmac, json, math, re

def creator_forecast(samples):
    if not isinstance(samples,list) or len(samples)<2 or any(not isinstance(x,(int,float)) or x<0 for x in samples): raise ValueError("invalid samples")
    slope=(samples[-1]-samples[0])/(len(samples)-1); return {"next":max(0,round(samples[-1]+slope,2)),"trend":"up" if slope>0 else "down" if slope<0 else "flat","explanation":{"slope":slope,"points":len(samples)}}
def creator_guided_assistant(profile):
    if not isinstance(profile,dict): raise ValueError("invalid profile")
    checks=[("identity",bool(profile.get("name"))), ("security",bool(profile.get("mfa"))), ("payout",bool(profile.get("payout_configured")))]
    return {"completed":[x for x,ok in checks if ok],"next":next((x for x,ok in checks if not ok),None),"done":all(ok for _,ok in checks)}
def creator_adaptive_alert(metric, value, baseline):
    if metric not in {"followers","engagement","reports"} or not all(isinstance(x,(int,float)) and x>=0 for x in (value,baseline)): raise ValueError("invalid alert metric")
    delta=value-baseline; threshold=max(1,baseline*.2); return {"metric":metric,"triggered":abs(delta)>=threshold,"direction":"increase" if delta>0 else "decrease" if delta<0 else "stable","delta":delta,"threshold":threshold}
def creator_automation(rule,event):
    if not isinstance(rule,dict) or rule.get("field") not in {"status","category","verified"} or rule.get("action") not in {"notify","request_review","tag"}: raise ValueError("invalid automation")
    matched=event.get(rule["field"])==rule.get("equals"); return {"matched":matched,"planned_actions":[{"type":rule["action"]}] if matched else [],"executed":False}
def creator_temporal_compare(current,previous):
    if not isinstance(current,dict) or set(current)!=set(previous) or any(not isinstance(v,(int,float)) for v in current.values()): raise ValueError("incomparable periods")
    return {k:{"current":current[k],"previous":previous[k],"delta":current[k]-previous[k]} for k in sorted(current)}
def creator_signed_export(records,secret):
    if not isinstance(records,list) or not isinstance(secret,str) or len(secret)<16: raise ValueError("invalid signed export")
    body=json.dumps(records,sort_keys=True,separators=(",",":")); return {"body":body,"signature":hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest(),"algorithm":"hmac-sha256"}
def creator_change_simulation(creator,changes):
    allowed={"display_name","category","notifications"}
    if not isinstance(creator,dict) or not isinstance(changes,dict) or set(changes)-allowed: raise ValueError("invalid simulation")
    after=copy.deepcopy(creator); after.update(copy.deepcopy(changes)); return {"before":copy.deepcopy(creator),"after":after,"diff":sorted(k for k in changes if creator.get(k)!=changes[k]),"applied":False}
def creator_version_append(history,document,actor,now):
    if not isinstance(history,list) or not isinstance(document,dict) or not str(actor): raise ValueError("invalid version")
    digest=hashlib.sha256(json.dumps(document,sort_keys=True).encode()).hexdigest()
    if history and history[-1].get("digest")==digest:return copy.deepcopy(history)
    return copy.deepcopy(history)+[{"version":len(history)+1,"document":copy.deepcopy(document),"actor":str(actor),"at":_iso(now),"digest":digest}]
def creator_semantic_search(query,documents,limit=5):
    terms=set(_tokens(query));
    if not terms or not isinstance(documents,list): raise ValueError("invalid semantic query")
    rows=[]
    for d in documents:
        words=set(_tokens(d.get("text",""))); score=len(terms&words)/math.sqrt(len(terms)*max(1,len(words)))
        if score: rows.append({"id":d["id"],"score":round(score,6),"matched":sorted(terms&words)})
    return sorted(rows,key=lambda x:(-x["score"],str(x["id"])))[:max(1,min(int(limit),20))]
def creator_explainable_summary(events):
    if not isinstance(events,list): raise ValueError("invalid events")
    counts={};
    for e in events: counts[str(e.get("type","unknown"))]=counts.get(str(e.get("type","unknown")),0)+1
    return {"total":len(events),"counts":dict(sorted(counts.items())),"explanation":"Agrupado por tipo; no incluye identidades."}
def creator_permission_check(policy,actor,action):
    if not isinstance(policy,dict) or not str(actor) or not str(action): raise ValueError("invalid permission request")
    grants=policy.get(actor,[]); allowed=action in grants; return {"allowed":allowed,"reason":"explicit_grant" if allowed else "default_deny"}
def creator_template_render(template,values):
    fields=set(re.findall(r"\{([a-z_]+)\}",str(template)))
    if fields!=set(values) or any(not isinstance(v,(str,int,float,bool)) for v in values.values()): raise ValueError("template fields mismatch")
    return {"rendered":str(template).format(**values),"fields":sorted(fields)}
def creator_bulk_plan(creators,changes):
    if not isinstance(creators,list) or len({x.get("id") for x in creators})!=len(creators) or not isinstance(changes,dict): raise ValueError("invalid bulk plan")
    return {"operations":[{"id":x["id"],"before":{k:x.get(k) for k in changes},"after":copy.deepcopy(changes)} for x in creators],"undo_available":True,"applied":False}
def creator_calendar(reviews,timezone):
    if not isinstance(reviews,list) or "/" not in str(timezone): raise ValueError("invalid calendar")
    rows=sorted(({"id":x["id"],"at":_iso(x["at"]),"priority":x.get("priority","medium")} for x in reviews),key=lambda x:x["at"])
    return {"timezone":timezone,"items":rows,"next_run":rows[0]["at"] if rows else None,"automatic_effects":False}
def creator_privacy_view(profile):
    if not isinstance(profile,dict): raise ValueError("invalid private profile")
    sensitive={"email","phone","token","secret","payout_account"}; return {k:("[redacted]" if k in sensitive else copy.deepcopy(v)) for k,v in profile.items()}
def creator_diagnostics(state):
    if not isinstance(state,dict): raise ValueError("invalid diagnostic state")
    checks={"identity":bool(state.get("id")),"mfa":state.get("mfa") is True,"profile":bool(state.get("display_name")),"payout":state.get("payout_status") in {"ready","not_required"}}
    return {"healthy":all(checks.values()),"checks":checks,"failures":[k for k,v in checks.items() if not v]}
def creator_recommendations(profile,signals):
    if not isinstance(profile,dict) or not isinstance(signals,dict): raise ValueError("invalid recommendation input")
    rows=[]
    if not profile.get("mfa"): rows.append({"action":"enable_mfa","score":100,"because":"mfa_disabled"})
    if signals.get("engagement",0)<.2: rows.append({"action":"review_content_plan","score":70,"because":"low_engagement"})
    return sorted(rows,key=lambda x:-x["score"])
def creator_approval_transition(request,reviewer,decision,now):
    if request.get("status")!="pending" or reviewer==request.get("requested_by") or decision not in {"approved","rejected"}: raise ValueError("invalid approval")
    return {**copy.deepcopy(request),"status":decision,"reviewed_by":reviewer,"reviewed_at":_iso(now)}
def creator_comment_append(thread,comment_id,author,text,now):
    if not isinstance(thread,list) or any(x.get("id")==comment_id for x in thread) or not str(text).strip() or len(str(text))>1000: raise ValueError("invalid comment")
    return copy.deepcopy(thread)+[{"id":comment_id,"author":str(author),"text":str(text).strip(),"at":_iso(now),"resolved":False}]
def creator_metric_ingest(state,event):
    if not isinstance(state,dict) or event.get("type") not in {"view","follow","publish","report"} or not str(event.get("id","")): raise ValueError("invalid metric event")
    result=copy.deepcopy(state or {"seen":[],"counts":{}})
    if event["id"] in result.setdefault("seen",[]): return result
    result["seen"].append(event["id"]); counts=result.setdefault("counts",{}); counts[event["type"]]=counts.get(event["type"],0)+1; return result
def _tokens(value): return re.findall(r"[a-z0-9áéíóúñ]+",str(value).lower())
def _iso(value):
    if isinstance(value,str): value=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
    if not isinstance(value,dt.datetime) or value.tzinfo is None: raise ValueError("aware datetime required")
    return value.astimezone(dt.timezone.utc).isoformat().replace("+00:00","Z")

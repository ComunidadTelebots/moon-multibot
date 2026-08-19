"""Validated, side-effect-free Web creator operations for future-1037..1056."""
import copy
import datetime as dt
import hashlib
import json
from collections import Counter, defaultdict

def creator_import_preview(rows, required=("id", "name")):
    if not isinstance(rows, list) or not rows or any(not isinstance(x, dict) for x in rows): raise ValueError("invalid import rows")
    seen=set(); preview=[]; errors=[]
    for index,row in enumerate(rows):
        missing=[key for key in required if not str(row.get(key,"")).strip()]
        duplicate=row.get("id") in seen
        if row.get("id") is not None: seen.add(row["id"])
        issues=(["missing:"+key for key in missing]+(["duplicate:id"] if duplicate else []))
        preview.append({"row":index+1,"normalized":{k:str(v).strip() for k,v in row.items()},"issues":issues})
        errors.extend({"row":index+1,"code":issue} for issue in issues)
    return {"preview":preview,"errors":errors,"importable":not errors,"committed":False}

def creator_collaboration_comment(comments, comment_id, author, text, mentions=()):
    if not isinstance(comments,list) or not comment_id or any(x.get("id")==comment_id for x in comments) or not str(text).strip(): raise ValueError("invalid collaboration comment")
    if not isinstance(mentions,(list,tuple)) or any(not str(x).strip() for x in mentions): raise ValueError("invalid mentions")
    return copy.deepcopy(comments)+[{"id":str(comment_id),"author":str(author),"text":str(text).strip(),"mentions":sorted(set(map(str,mentions))),"resolved":False}]

def creator_smart_tags(content, vocabulary):
    if not str(content).strip() or not isinstance(vocabulary,dict): raise ValueError("invalid smart tag input")
    words=set(str(content).lower().split()); matches=[]
    for tag,keywords in vocabulary.items():
        score=len(words & {str(x).lower() for x in keywords})
        if score: matches.append({"tag":str(tag),"score":score,"evidence":sorted(words & set(map(str.lower,keywords)))})
    return sorted(matches,key=lambda x:(-x["score"],x["tag"]))

def creator_activity_digest(events, enabled_types, limit=10):
    if not isinstance(events,list) or not isinstance(enabled_types,(list,tuple,set)) or not 1<=int(limit)<=50: raise ValueError("invalid activity digest")
    selected=[copy.deepcopy(x) for x in events if x.get("type") in enabled_types]
    return {"items":selected[-int(limit):],"counts":dict(Counter(x["type"] for x in selected)),"omitted":len(events)-len(selected)}

def creator_expiry_alerts(resources, now, warning_days=7):
    now=_time(now); warning=dt.timedelta(days=int(warning_days)); result=[]
    for item in resources:
        expiry=_time(item.get("expires_at")); remaining=expiry-now
        if remaining<=warning: result.append({"id":item["id"],"status":"expired" if remaining.total_seconds()<0 else "expiring","days":max(-1,remaining.days)})
    return sorted(result,key=lambda x:(x["days"],str(x["id"])))

def creator_emergency_mode(state, actor, reason, enabled, now):
    if not isinstance(state,dict) or not str(actor) or len(str(reason).strip())<5 or not isinstance(enabled,bool): raise ValueError("invalid emergency transition")
    result=copy.deepcopy(state); result["emergency"]={"enabled":enabled,"actor":str(actor),"reason":str(reason).strip(),"at":_iso(now)}
    result.setdefault("audit",[]).append(copy.deepcopy(result["emergency"])); return result

def creator_effective_permissions(role_grants, user_grants, user_denies):
    if any(not isinstance(x,(list,tuple,set)) for x in (role_grants,user_grants,user_denies)): raise ValueError("invalid permissions")
    allowed=(set(role_grants)|set(user_grants))-set(user_denies)
    universe=set(role_grants)|set(user_grants)|set(user_denies)
    return {"effective":sorted(allowed),"history":[{"permission":p,"decision":"deny" if p in user_denies else "grant","source":"user" if p in set(user_grants)|set(user_denies) else "role"} for p in sorted(universe)]}

def creator_shared_goals(goal, contributions):
    target=goal.get("target");
    if not isinstance(target,(int,float)) or target<=0 or not isinstance(contributions,list) or any(x.get("amount",0)<0 for x in contributions): raise ValueError("invalid shared goal")
    by_member=defaultdict(float)
    for row in contributions: by_member[str(row["member"])]+=row["amount"]
    total=sum(by_member.values()); return {"id":goal.get("id"),"target":target,"current":total,"percent":min(100,round(total/target*100,2)),"members":dict(sorted(by_member.items()))}

def creator_config_recommender(config, usage):
    if not isinstance(config,dict) or not isinstance(usage,dict): raise ValueError("invalid recommendation context")
    rows=[]
    if usage.get("failed_logins",0)>=3 and not config.get("mfa"): rows.append({"setting":"mfa","value":True,"priority":100,"reason":"failed_logins"})
    if usage.get("weekly_posts",0)>20 and config.get("digest")!="daily": rows.append({"setting":"digest","value":"daily","priority":60,"reason":"high_activity"})
    return rows

def creator_config_tests(config):
    if not isinstance(config,dict): raise ValueError("invalid configuration")
    checks={"identity":bool(config.get("creator_id")),"visibility":config.get("visibility") in {"public","private","unlisted"},"notifications":isinstance(config.get("notifications"),bool)}
    return {"passed":all(checks.values()),"checks":checks,"failures":[k for k,v in checks.items() if not v]}

def creator_consent_center(consents, purpose, granted, version, now):
    if not isinstance(consents,dict) or not str(purpose) or not isinstance(granted,bool) or int(version)<1: raise ValueError("invalid consent")
    result=copy.deepcopy(consents); result[str(purpose)]={"granted":granted,"version":int(version),"at":_iso(now)}; return result

def creator_task_navigation(tasks, completed=()):
    if not isinstance(tasks,list) or any("id" not in x or "depends_on" not in x for x in tasks): raise ValueError("invalid tasks")
    done=set(completed); available=[x for x in tasks if x["id"] not in done and set(x["depends_on"])<=done]
    return {"completed":sorted(done),"available":[x["id"] for x in available],"next":available[0]["id"] if available else None}

def creator_device_sync(local, remote):
    if not isinstance(local,dict) or not isinstance(remote,dict): raise ValueError("invalid sync state")
    merged={}; conflicts=[]
    for key in sorted(set(local)|set(remote)):
        left=local.get(key); right=remote.get(key)
        if left and right and left.get("value")!=right.get("value") and left.get("updated_at")==right.get("updated_at"): conflicts.append(key); merged[key]=copy.deepcopy(left)
        else: merged[key]=copy.deepcopy(max((x for x in (left,right) if x),key=lambda x:x.get("updated_at","")))
    return {"merged":merged,"conflicts":conflicts}

def creator_duplicate_detection(records, fields):
    if not isinstance(records,list) or not fields: raise ValueError("invalid duplicate detection")
    groups=defaultdict(list)
    for row in records: groups[tuple(str(row.get(k,"")).strip().lower() for k in fields)].append(row.get("id"))
    return [{"key":list(k),"ids":ids} for k,ids in groups.items() if len(ids)>1]

def creator_adaptive_quota(base, usage, trust_score):
    if not isinstance(base,int) or base<1 or not isinstance(usage,int) or usage<0 or not isinstance(trust_score,(int,float)) or not 0<=trust_score<=1: raise ValueError("invalid quota input")
    limit=max(1,round(base*(.5+trust_score))); return {"limit":limit,"used":usage,"remaining":max(0,limit-usage),"throttled":usage>=limit}

def creator_community_impact(events):
    if not isinstance(events,list) or any(x.get("kind") not in {"answer","resource","mentoring"} or x.get("value",0)<0 for x in events): raise ValueError("invalid impact events")
    totals=Counter();
    for row in events: totals[row["kind"]]+=row["value"]
    weights={"answer":1,"resource":3,"mentoring":5}; return {"totals":dict(totals),"score":sum(totals[k]*weights[k] for k in weights),"events":len(events)}

def creator_reviewable_translation(source, locale, translation, reviewer=None):
    if not str(source).strip() or len(str(locale))<2 or not str(translation).strip(): raise ValueError("invalid translation")
    return {"source_hash":hashlib.sha256(str(source).encode()).hexdigest(),"locale":locale,"translation":translation,"status":"approved" if reviewer else "pending_review","reviewer":reviewer}

def creator_grouped_notifications(notifications):
    if not isinstance(notifications,list): raise ValueError("invalid notifications")
    grouped=defaultdict(list)
    for row in notifications:
        if not row.get("context") or not row.get("id"): raise ValueError("notification context required")
        grouped[row["context"]].append(copy.deepcopy(row))
    return [{"context":key,"count":len(grouped[key]),"items":grouped[key]} for key in sorted(grouped)]

def creator_migration_assistant(source, target_version):
    if not isinstance(source,dict) or int(source.get("version",0))<1 or int(target_version)<=source["version"]: raise ValueError("invalid migration")
    steps=[{"from":v,"to":v+1,"status":"pending"} for v in range(source["version"],int(target_version))]
    return {"source_version":source["version"],"target_version":int(target_version),"steps":steps,"executed":False,"backup_required":True}

def creator_admin_decision_log(log, decision_id, actor, action, rationale, now):
    if not isinstance(log,list) or any(x.get("id")==decision_id for x in log) or action not in {"approve","reject","suspend","restore"} or len(str(rationale).strip())<5: raise ValueError("invalid administrative decision")
    previous=log[-1].get("digest","") if log else ""; payload={"id":decision_id,"actor":actor,"action":action,"rationale":str(rationale).strip(),"at":_iso(now),"previous":previous}
    payload["digest"]=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest(); return copy.deepcopy(log)+[payload]

def _time(value):
    if isinstance(value,str): value=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
    if not isinstance(value,dt.datetime) or value.tzinfo is None: raise ValueError("aware datetime required")
    return value.astimezone(dt.timezone.utc)
def _iso(value): return _time(value).isoformat().replace("+00:00","Z")

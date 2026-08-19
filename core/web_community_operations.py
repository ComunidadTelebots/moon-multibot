"""Community-specific Web contracts for future-0251..0270."""
import copy, hashlib, hmac, json, statistics
from urllib.parse import urlparse
from core.web_creator_features import _iso
def community_permission(policy,actor,community,action):
 if action not in {"view","post","moderate","configure"}:raise ValueError("invalid community action")
 allowed=action in policy.get(actor,{}).get(community,[]) if isinstance(policy,dict) else False;return {"allowed":allowed,"community":community,"reason":"community_grant" if allowed else "default_deny"}
def community_template(name,rules,roles):
 if not str(name).strip() or not isinstance(rules,list) or not rules or not isinstance(roles,list) or len(roles)!=len(set(roles)):raise ValueError("invalid community template")
 return {"name":name.strip(),"rules":copy.deepcopy(rules),"roles":list(roles),"reusable":True}
def community_bulk_plan(communities,visibility):
 if visibility not in {"public","private","invite_only"} or len({x.get("id") for x in communities})!=len(communities):raise ValueError("invalid community bulk")
 return {"operations":[{"id":x["id"],"before":x.get("visibility"),"after":visibility} for x in communities],"undo_available":True,"applied":False}
def community_calendar(events,timezone):
 if "/" not in str(timezone):raise ValueError("invalid community calendar")
 rows=sorted(({"id":x["id"],"starts_at":_iso(x["starts_at"]),"kind":x["kind"]} for x in events),key=lambda x:x["starts_at"]);return {"timezone":timezone,"events":rows,"next":rows[0] if rows else None,"messages_sent":False}
def community_privacy(community):
 if not isinstance(community,dict):raise ValueError("invalid community")
 banned={"member_ids","invite_tokens","moderator_emails"};return {"public":{k:copy.deepcopy(v) for k,v in community.items() if k not in banned},"removed":sorted(set(community)&banned),"member_identity_included":False}
def community_diagnostics(state):
 checks={"owner":bool(state.get("owner_id")),"moderators":state.get("moderator_count",0)>0,"rules":bool(state.get("rules")),"bot":state.get("bot_status")=="active"};return {"healthy":all(checks.values()),"checks":checks,"failures":[k for k,v in checks.items() if not v]}
def community_recommendations(state):
 rows=[]
 if state.get("reports",0)>5:rows.append({"action":"review_moderation","score":100,"because":"report_volume"})
 if state.get("engagement",1)<.2:rows.append({"action":"schedule_activity","score":70,"because":"low_engagement"})
 return sorted(rows,key=lambda x:-x["score"])
def community_approval(request,reviewer,decision,now):
 if request.get("status")!="pending" or request.get("kind") not in {"role","rule","event"} or decision not in {"approved","rejected"} or reviewer==request.get("requested_by"):raise ValueError("invalid community approval")
 return {**copy.deepcopy(request),"status":decision,"reviewer":reviewer,"at":_iso(now)}
def community_comment(thread,comment):
 if not comment.get("community_id") or not str(comment.get("text","")).strip() or any(x.get("id")==comment.get("id") for x in thread):raise ValueError("invalid community comment")
 return copy.deepcopy(thread)+[{"id":comment["id"],"community_id":comment["community_id"],"text":comment["text"].strip(),"resolved":False}]
def community_metric(state,event):
 if event.get("type") not in {"join","leave","post","report"} or not event.get("id"):raise ValueError("invalid community metric")
 out=copy.deepcopy(state or {"seen":[],"counts":{}})
 if event["id"] in out["seen"]:return out
 out["seen"].append(event["id"]);out["counts"][event["type"]]=out["counts"].get(event["type"],0)+1;return out
def community_accessibility(config):
 if config.get("descriptive_labels") is not True or config.get("contrast") not in {"normal","high"}:raise ValueError("invalid community accessibility")
 return {"descriptive_labels":True,"contrast":config["contrast"],"keyboard_navigation":True,"color_only_status":False}
def community_webhook(url,event,community,secret):
 if event not in {"community.created","community.member_count_changed","community.archived"} or urlparse(str(url)).scheme!="https" or len(str(secret))<16:raise ValueError("invalid community webhook")
 body=json.dumps({k:community.get(k) for k in ("id","name","member_count","status")},sort_keys=True);return {"url":url,"event":event,"body":body,"signature":hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest(),"member_ids_included":False,"sent":False}
def community_anomaly(samples):
 if len(samples)<4 or any(not isinstance(x,(int,float)) for x in samples):raise ValueError("invalid community samples")
 baseline=statistics.median(samples[:-1]);return {"anomaly":abs(samples[-1]-baseline)>max(5,baseline*.5),"baseline":baseline,"latest":samples[-1]}
def community_learning(completed,role):
 tracks={"member":["rules","safety","participation"],"moderator":["reports","appeals","incidents"]}
 if role not in tracks or set(completed)-set(tracks[role]):raise ValueError("invalid community learning")
 left=[x for x in tracks[role] if x not in completed];return {"role":role,"next":left[0] if left else None,"certified":not left}
def community_language(language,labels):
 required={"join","leave","report"}
 if language not in {"es","en","ca","ar"} or set(labels)!=required:raise ValueError("invalid community language")
 return {"language":language,"labels":copy.deepcopy(labels),"direction":"rtl" if language=="ar" else "ltr"}
def community_compact(community,fields):
 allowed={"id","name","member_count","status","topics"}
 if not fields or set(fields)-allowed:raise ValueError("invalid compact community")
 return {"fields":{k:copy.deepcopy(community.get(k)) for k in fields},"member_ids_included":False,"density":"compact"}
def community_recovery(current,snapshot,fields):
 allowed={"name","description","rules","visibility","topics"}
 if not fields or set(fields)-allowed or any(k not in snapshot for k in fields):raise ValueError("invalid community recovery")
 return {"restore":{k:copy.deepcopy(snapshot[k]) for k in fields},"before":{k:copy.deepcopy(current.get(k)) for k in fields},"applied":False}
def community_report(config,events):
 if config.get("frequency") not in {"daily","weekly","monthly"} or config.get("format") not in {"json","csv"}:raise ValueError("invalid community report")
 counts={}
 for x in events:counts[x.get("type","unknown")]=counts.get(x.get("type","unknown"),0)+1
 return {"frequency":config["frequency"],"format":config["format"],"counts":counts,"member_ids_included":False,"delivered":False}
def community_sandbox(state,operation):
 if operation.get("type") not in {"change_rules","change_visibility","rename"}:raise ValueError("invalid community sandbox")
 field={"change_rules":"rules","change_visibility":"visibility","rename":"name"}[operation["type"]];after=copy.deepcopy(state);after[field]=operation.get("value");return {"before":copy.deepcopy(state),"after":after,"effects":[],"saved":False}
def community_connector(community,standard):
 if standard not in {"activitystreams","matrix-space","portable-community"} or not community.get("id"):raise ValueError("invalid community connector")
 public={k:community.get(k) for k in ("id","name","description","topics","member_count")};return {"standard":standard,"resource":public,"member_ids_included":False,"exported":False}

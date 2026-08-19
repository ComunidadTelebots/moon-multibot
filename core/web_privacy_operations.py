"""Privacy-specific Web contracts for future-0191..0210."""
import copy, hashlib, hmac, json
from urllib.parse import urlparse
from core.web_creator_features import _iso
def privacy_permission(policy,actor,subject,action):
 if action not in {"inspect","export","correct","delete"}:raise ValueError("invalid privacy action")
 grants=policy.get(actor,{}) if isinstance(policy,dict) else {};allowed=action in grants.get(subject,[]);return {"allowed":allowed,"subject":subject,"reason":"subject_grant" if allowed else "privacy_default_deny"}
def privacy_template(name,retention_days,fields):
 if not str(name).strip() or not isinstance(retention_days,int) or not 1<=retention_days<=3650 or not isinstance(fields,list) or len(fields)!=len(set(fields)):raise ValueError("invalid privacy template")
 return {"name":name.strip(),"retention_days":retention_days,"fields":list(fields),"reusable":True,"default_collect":False}
def privacy_bulk_plan(records,action):
 if action not in {"anonymize","delete","restrict"} or len({x.get("id") for x in records})!=len(records):raise ValueError("invalid privacy bulk")
 return {"operations":[{"id":x["id"],"action":action,"previous_status":x.get("status")} for x in records],"requires_confirmation":True,"undo_available":action!="delete","applied":False}
def privacy_calendar(items,timezone):
 if "/" not in str(timezone):raise ValueError("invalid privacy calendar")
 rows=sorted(({"id":x["id"],"review_at":_iso(x["review_at"]),"kind":x["kind"]} for x in items),key=lambda x:x["review_at"]);return {"timezone":timezone,"reviews":rows,"next_run":rows[0]["review_at"] if rows else None,"automatic_deletion":False}
def privacy_mode(record,enabled):
 if not isinstance(record,dict) or not isinstance(enabled,bool):raise ValueError("invalid privacy mode")
 return {"record_id":record.get("id"),"enabled":enabled,"masked_fields":[k for k in record if k in {"email","phone","ip","location"}],"source_changed":False}
def privacy_diagnostics(state):
 checks={"consent":state.get("consent_coverage",0)>=.99,"retention":state.get("overdue_records",1)==0,"encryption":state.get("encrypted") is True,"exports":state.get("unsigned_exports",1)==0};return {"healthy":all(checks.values()),"checks":checks,"failures":[k for k,v in checks.items() if not v]}
def privacy_recommendations(state):
 rows=[]
 if state.get("overdue_records",0):rows.append({"action":"review_retention","score":100,"because":"overdue_records"})
 if state.get("consent_coverage",1)<.99:rows.append({"action":"repair_consent","score":90,"because":"consent_gap"})
 return sorted(rows,key=lambda x:-x["score"])
def privacy_approval(request,reviewer,decision,now):
 if request.get("status")!="pending" or request.get("kind") not in {"export","deletion","policy"} or decision not in {"approved","rejected"} or reviewer==request.get("requested_by"):raise ValueError("invalid privacy approval")
 return {**copy.deepcopy(request),"status":decision,"reviewer":reviewer,"at":_iso(now)}
def privacy_comment(thread,comment):
 if comment.get("subject_hash") is None or not str(comment.get("text","")).strip() or any(x.get("id")==comment.get("id") for x in thread):raise ValueError("invalid privacy comment")
 return copy.deepcopy(thread)+[{"id":comment["id"],"subject_hash":comment["subject_hash"],"text":comment["text"].strip(),"resolved":False,"pii":False}]
def privacy_metric(state,event):
 if event.get("type") not in {"consent","export","deletion","access"} or not event.get("id"):raise ValueError("invalid privacy metric")
 out=copy.deepcopy(state or {"seen":[],"counts":{}})
 if event["id"] in out["seen"]:return out
 out["seen"].append(event["id"]);out["counts"][event["type"]]=out["counts"].get(event["type"],0)+1;return out
def privacy_accessibility(config):
 if config.get("plain_language") is not True or config.get("consent_labels") is not True:raise ValueError("invalid privacy accessibility")
 return {"plain_language":True,"consent_labels":True,"keyboard_navigation":True,"legal_jargon_required":False}
def privacy_webhook(url,event,payload,secret):
 if event not in {"privacy.export_ready","privacy.deletion_completed","privacy.consent_changed"} or urlparse(str(url)).scheme!="https" or len(str(secret))<16:raise ValueError("invalid privacy webhook")
 safe={k:v for k,v in payload.items() if k not in {"email","phone","name","ip"}};body=json.dumps(safe,sort_keys=True,separators=(",",":"));return {"url":url,"event":event,"body":body,"signature":hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest(),"pii_included":False,"sent":False}
def privacy_anomaly(events):
 if not isinstance(events,list):raise ValueError("invalid privacy events")
 counts={}
 for x in events:counts[x.get("actor_hash")]=counts.get(x.get("actor_hash"),0)+1
 flagged=sorted(k for k,v in counts.items() if v>=5);return {"flagged_actor_hashes":flagged,"threshold":5,"raw_identities_included":False}
def privacy_learning(completed,role):
 tracks={"user":["consent","export","delete"],"operator":["retention","breach","audit"]}
 if role not in tracks or set(completed)-set(tracks[role]):raise ValueError("invalid privacy learning")
 left=[x for x in tracks[role] if x not in completed];return {"role":role,"next":left[0] if left else None,"certified":not left}
def privacy_language(language,notices):
 required={"consent","retention","deletion"}
 if language not in {"es","en","ca","ar"} or set(notices)!=required:raise ValueError("invalid privacy language")
 return {"language":language,"notices":copy.deepcopy(notices),"direction":"rtl" if language=="ar" else "ltr"}
def privacy_compact(record,fields):
 allowed={"type","status","created_at","retention_until"}
 if not fields or set(fields)-allowed:raise ValueError("invalid privacy compact")
 return {"fields":{k:record.get(k) for k in fields},"identity_included":False,"density":"compact"}
def privacy_recovery(current,snapshot,fields):
 allowed={"consent","retention_until","processing_restricted"}
 if not fields or set(fields)-allowed or any(k not in snapshot for k in fields):raise ValueError("invalid privacy recovery")
 return {"restore":{k:copy.deepcopy(snapshot[k]) for k in fields},"before":{k:copy.deepcopy(current.get(k)) for k in fields},"applied":False,"deletions_reversible":False}
def privacy_report(config,events):
 if config.get("frequency") not in {"monthly","quarterly"} or config.get("format") not in {"json","csv"}:raise ValueError("invalid privacy report")
 counts={}
 for x in events:counts[x.get("type","unknown")]=counts.get(x.get("type","unknown"),0)+1
 return {"frequency":config["frequency"],"format":config["format"],"counts":counts,"identities_included":False,"delivered":False}
def privacy_sandbox(policy,records):
 if not isinstance(policy,dict) or not isinstance(records,list):raise ValueError("invalid privacy sandbox")
 overdue=sum(bool(x.get("retention_due")) for x in records);return {"policy":copy.deepcopy(policy),"records_evaluated":len(records),"would_delete":overdue,"deletions":0,"effects":[]}
def privacy_connector(records,standard):
 if standard not in {"gdpr-portability","json-ld","csv-redacted"}:raise ValueError("invalid privacy connector")
 safe=[{k:v for k,v in x.items() if k not in {"token","password","internal_secret"}} for x in records];return {"standard":standard,"records":safe,"secrets_included":False,"exported":False}

"""Authorised pure planners for energy, abuse, migration and federation roadmap features."""
from __future__ import annotations
from collections import defaultdict, deque
from datetime import timedelta
import hashlib, json, math
from typing import Any, Callable
from resource_incident_temporal_engines import _utc_datetime
from resource_security_contracts import authorize, bounded_json, safe_identifier

IDS=tuple(f"future-{n}" for n in range(5702,5880,3))
ENERGY=("temporary_roles","managed_groups","scheduled_messages","rss_feeds","telegram_videos","blocklists","required_subscriptions","signed_webhooks","quiet_hours","correlated_incidents","accessible_preferences","integration_secrets","contextual_responses","miniapp_menus","bot_statistics","advertising_preferences","processing_queues")
ABUSE=("creator_accounts","associated_channels","community_campaigns","editorial_articles","moderated_images","user_appeals","mtproto_proxies","persistent_tasks","moderation_rules","language_metrics","community_translations","personal_consents","telegram_reactions","master_panels","channel_directories","external_links")
MIGRATION=("administrative_sessions","community_profiles","telegram_communities","house_ads","voice_notes","suspicious_files","captcha_decisions","managed_bots","recurring_reminders","security_events","regional_maps","backups","ai_learning_data","rich_commands","hub_notifications","cookie_policies","wayback_history")
FEDERATION=("temporary_roles","managed_groups","scheduled_messages","rss_feeds","telegram_videos","blocklists","required_subscriptions","signed_webhooks","quiet_hours","correlated_incidents")

def _energy(fid,resource,samples,actor,target_reduction=10.0):
    aid=authorize(actor,f"energy:plan:{resource}"); bounded_json(samples,maximum_bytes=524288,reject_secrets=True)
    if not isinstance(samples,list) or len(samples)>10000 or isinstance(target_reduction,bool) or not isinstance(target_reduction,(int,float)) or not 0<=target_reduction<=90: raise ValueError("energy request invalid")
    groups=defaultdict(list)
    for row in samples:
        if not isinstance(row,dict): raise ValueError("sample invalid")
        workload=safe_identifier(row.get("workload_id"),"workload_id"); energy=row.get("energy_wh"); items=row.get("items")
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (energy,items)) or energy<0 or items<=0: raise ValueError("sample values invalid")
        groups[workload].append((float(energy),float(items)))
    plans=[]
    for workload,rows in sorted(groups.items()):
        total_e=sum(x for x,_ in rows); total_i=sum(x for _,x in rows); intensity=total_e/total_i
        if not all(math.isfinite(value) for value in (total_e,total_i,intensity)): raise ValueError("derived energy metric outside finite limits")
        plans.append({"workload_id":workload,"samples":len(rows),"energy_wh":round(total_e,6),"items":round(total_i,4),"wh_per_item":round(intensity,8),"target_wh_per_item":round(intensity*(1-target_reduction/100),8),"actions":("batch_requests","coalesce_wakeups","prefer_cached_reads")})
    return {"feature_id":fid,"resource":resource,"planned_by":aid,"target_reduction_percent":target_reduction,"plans":tuple(plans),"measurement_only":True,"hardware_control":False,"executed":False,"auditable":True}

def _abuse(fid,resource,events,policy,actor):
    aid=authorize(actor,f"abuse:evaluate:{resource}"); bounded_json(events,maximum_bytes=524288,reject_secrets=True); bounded_json(policy,reject_secrets=True)
    if not isinstance(events,list) or len(events)>20000 or not isinstance(policy,dict): raise ValueError("abuse request invalid")
    window=int(policy.get("window_seconds",60)); limit=int(policy.get("limit",10)); burst=int(policy.get("burst",3))
    if not(1<=window<=86400 and 1<=limit<=10000 and 0<=burst<=limit): raise ValueError("policy invalid")
    by_subject=defaultdict(list)
    for e in events:
        if not isinstance(e,dict): raise ValueError("event invalid")
        sid=safe_identifier(e.get("subject_id"),"subject_id"); eid=safe_identifier(e.get("event_id"),"event_id"); at=_utc_datetime(e.get("occurred_at"),"occurred_at"); by_subject[sid].append((at,eid))
    decisions=[]
    for sid,rows in sorted(by_subject.items()):
        rows.sort(); queue=deque(); peak=0
        for at,_ in rows:
            while queue and (at-queue[0]).total_seconds()>=window: queue.popleft()
            queue.append(at); peak=max(peak,len(queue))
        allowed=limit+burst
        decisions.append({"subject_id":sid,"event_count":len(rows),"peak_in_window":peak,"limited":peak>allowed,"retry_after_seconds":window if peak>allowed else 0})
    return {"feature_id":fid,"resource":resource,"evaluated_by":aid,"policy":{"window_seconds":window,"limit":limit,"burst":burst},"decisions":tuple(decisions),"automatic_ban":False,"mutation_requested":False,"executed":False,"auditable":True}

def _migration(fid,resource,records,plan,actor):
    aid=authorize(actor,f"migration:plan:{resource}"); bounded_json(records,maximum_bytes=524288,reject_secrets=True); bounded_json(plan,reject_secrets=True)
    if not isinstance(records,list) or len(records)>10000 or not isinstance(plan,dict): raise ValueError("migration request invalid")
    source=safe_identifier(plan.get("source_version"),"source_version"); target=safe_identifier(plan.get("target_version"),"target_version")
    if source==target: raise ValueError("versions must differ")
    required=plan.get("required_fields",[])
    if not isinstance(required,list) or len(required)>100 or not all(isinstance(x,str) and x.isidentifier() for x in required): raise ValueError("required_fields invalid")
    checks=[]
    for pos,row in enumerate(records):
        if not isinstance(row,dict): raise ValueError("record invalid")
        try: rid=safe_identifier(row.get("id"),"id")
        except ValueError: rid=f"invalid-at-{pos}"
        missing=tuple(x for x in required if row.get(x) is None); checks.append({"record_id":rid,"ready":not missing,"missing_fields":missing})
    digest=hashlib.sha256(json.dumps(records,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    return {"feature_id":fid,"resource":resource,"planned_by":aid,"source_version":source,"target_version":target,"record_count":len(records),"ready_count":sum(x["ready"] for x in checks),"checks":tuple(checks),"source_digest":digest,"backup_required":True,"rollback_required":True,"requires_approval":True,"applied":False,"executed":False,"auditable":True}

def _federation(fid,resource,envelope,trust,actor):
    aid=authorize(actor,f"federation:verify:{resource}"); bounded_json(envelope,maximum_bytes=131072,reject_secrets=True); bounded_json(trust,reject_secrets=True)
    if not isinstance(envelope,dict) or not isinstance(trust,dict): raise ValueError("federation request invalid")
    origin=safe_identifier(envelope.get("origin"),"origin"); subject=safe_identifier(envelope.get("subject_id"),"subject_id"); schema=safe_identifier(envelope.get("schema_version"),"schema_version")
    issued=_utc_datetime(envelope.get("issued_at"),"issued_at"); expires=_utc_datetime(envelope.get("expires_at"),"expires_at")
    if expires<=issued or expires-issued>timedelta(days=7): raise ValueError("envelope lifetime invalid")
    allowed=trust.get("allowed_origins",[]); schemas=trust.get("schema_versions",[])
    if not isinstance(allowed,list) or not isinstance(schemas,list): raise ValueError("trust invalid")
    allowed={safe_identifier(x,"allowed_origin") for x in allowed}; schemas={safe_identifier(x,"schema_version") for x in schemas}
    compatible=origin in allowed and schema in schemas
    return {"feature_id":fid,"resource":resource,"verified_by":aid,"origin":origin,"subject_id":subject,"schema_version":schema,"compatible":compatible,"reason":None if compatible else "untrusted_origin_or_schema","payload_exposed":False,"trust_extended":False,"network_requested":False,"executed":False,"auditable":True}

def _make(i,r,f):
    if f=="energy":
        def op(samples,*,actor,target_reduction=10.0): return _energy(IDS[i],r,samples,actor,target_reduction)
        op.__name__=f"optimize_{r}_energy"
    elif f=="abuse":
        def op(events,policy,*,actor): return _abuse(IDS[i],r,events,policy,actor)
        op.__name__=f"limit_{r}_abuse"
    elif f=="migration":
        def op(records,plan,*,actor): return _migration(IDS[i],r,records,plan,actor)
        op.__name__=f"plan_{r}_guided_migration"
    else:
        def op(envelope,trust,*,actor): return _federation(IDS[i],r,envelope,trust,actor)
        op.__name__=f"verify_{r}_federated_compatibility"
    return op
ENERGY_APIS=tuple(_make(i,r,"energy") for i,r in enumerate(ENERGY))
ABUSE_APIS=tuple(_make(17+i,r,"abuse") for i,r in enumerate(ABUSE))
MIGRATION_APIS=tuple(_make(33+i,r,"migration") for i,r in enumerate(MIGRATION))
FEDERATION_APIS=tuple(_make(50+i,r,"federation") for i,r in enumerate(FEDERATION))
ALL_APIS=ENERGY_APIS+ABUSE_APIS+MIGRATION_APIS+FEDERATION_APIS
globals().update({x.__name__:x for x in ALL_APIS})

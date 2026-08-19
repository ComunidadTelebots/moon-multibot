"""Auditable integration operations missing from the generated Moonbot matrix."""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timezone
from resource_security_contracts import bounded_json, safe_identifier

IDS=("future-2665","future-2667")
def _at(value):
    if not isinstance(value,str):raise ValueError("timestamp required")
    try:
        parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:raise ValueError("timezone required")
        return parsed.astimezone(timezone.utc)
    except ValueError as exc:raise ValueError("invalid timestamp") from exc

def correlate_integration_incidents(events:list[dict],window_seconds:int=300)->dict:
    bounded_json(events,maximum_bytes=262144,reject_secrets=True)
    if not isinstance(events,list) or len(events)>5000 or isinstance(window_seconds,bool) or not 1<=window_seconds<=86400:raise ValueError("invalid correlation request")
    groups=defaultdict(list);seen=set()
    for row in events:
        eid=safe_identifier(row.get("event_id"),"event_id");integration=safe_identifier(row.get("integration_id"),"integration_id");kind=safe_identifier(row.get("kind"),"kind");at=_at(row.get("occurred_at"))
        if eid in seen:continue
        seen.add(eid);groups[(integration,kind)].append((at,eid))
    incidents=[]
    for (integration,kind),rows in sorted(groups.items()):
        rows.sort();bucket=[]
        for at,eid in rows:
            if bucket and (at-bucket[-1][0]).total_seconds()>window_seconds:
                incidents.append((integration,kind,bucket));bucket=[]
            bucket.append((at,eid))
        if bucket:incidents.append((integration,kind,bucket))
    return {"feature_id":IDS[0],"incidents":tuple({"integration_id":i,"kind":k,"event_ids":tuple(x[1] for x in b),"count":len(b),"requires_review":len(b)>1} for i,k,b in incidents),"raw_payload_exposed":False,"automatic_action":False,"executed":False,"auditable":True}

def delegate_integration_access(grant_id:str,owner_id:str,delegate_id:str,scopes:list[str],expires_at:str,now:str)->dict:
    grant=safe_identifier(grant_id,"grant_id");owner=safe_identifier(owner_id,"owner_id");delegate=safe_identifier(delegate_id,"delegate_id")
    if owner==delegate:raise ValueError("self delegation forbidden")
    bounded_json(scopes,reject_secrets=True);allowed={"integration:read","integration:test","integration:configure"}
    if not isinstance(scopes,list) or not scopes or len(scopes)!=len(set(scopes)) or set(scopes)-allowed:raise ValueError("invalid scopes")
    expiry,current=_at(expires_at),_at(now)
    if not current<expiry or (expiry-current).total_seconds()>604800:raise ValueError("invalid expiry")
    return {"feature_id":IDS[1],"grant_id":grant,"owner_id":owner,"delegate_id":delegate,"scopes":tuple(sorted(scopes)),"expires_at":expiry.isoformat().replace("+00:00","Z"),"requires_owner_approval":"integration:configure" in scopes,"revocable":True,"active":True,"applied":False,"executed":False,"auditable":True}

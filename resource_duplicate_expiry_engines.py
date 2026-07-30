"""Privacy-minimized duplicate detection and automatic-expiry decisions for Moonbot."""
import hashlib, json
from datetime import datetime, timezone

IDS=tuple(f"future-{n}" for n in (4502,4505,4508,4511,4514,4517,4520,4523,4526,4529,4532,4535,4538,4541,4544,4547,4550,4553,4556,4559))

def _duplicates(fid,resource,records,match_fields):
 if not isinstance(records,list) or len(records)>50000 or not isinstance(match_fields,(list,tuple,set)) or not match_fields or any(not isinstance(x,str) or not x for x in match_fields): raise ValueError("Deteccion no valida")
 fields=tuple(sorted(set(match_fields))); buckets={}
 for record in records:
  if not isinstance(record,dict) or not isinstance(record.get("id"),(str,int)): raise ValueError("Registro no valido")
  values=[]
  for field in fields:
   value=record.get(field); values.append(value.strip().casefold() if isinstance(value,str) else value)
  canonical=json.dumps(values,sort_keys=True,separators=(",",":"),ensure_ascii=False,default=str).encode(); fingerprint=hashlib.sha256(canonical).hexdigest()
  buckets.setdefault(fingerprint,[]).append(str(record["id"]))
 groups=tuple({"fingerprint":fp,"ids":tuple(sorted(ids)),"count":len(ids)} for fp,ids in sorted(buckets.items()) if len(ids)>1)
 return {"feature_id":fid,"resource":resource,"match_fields":fields,"duplicate_groups":groups,"duplicate_record_count":sum(x["count"] for x in groups),"raw_values_included":False,"read_only":True,"auditable":True}

def _make_dup(i,r): return lambda rows,fields:_duplicates(IDS[i],r,rows,fields)
duplicates_temporary_roles=_make_dup(0,"temporary_roles"); duplicates_managed_groups=_make_dup(1,"managed_groups"); duplicates_scheduled_messages=_make_dup(2,"scheduled_messages")
duplicates_rss_feeds=_make_dup(3,"rss_feeds"); duplicates_telegram_videos=_make_dup(4,"telegram_videos"); duplicates_blocklists=_make_dup(5,"blocklists")
duplicates_required_subscriptions=_make_dup(6,"required_subscriptions"); duplicates_signed_webhooks=_make_dup(7,"signed_webhooks"); duplicates_quiet_hours=_make_dup(8,"quiet_hours")
duplicates_correlated_incidents=_make_dup(9,"correlated_incidents"); duplicates_accessible_preferences=_make_dup(10,"accessible_preferences"); duplicates_integration_secrets=_make_dup(11,"integration_secrets")
duplicates_contextual_responses=_make_dup(12,"contextual_responses"); duplicates_miniapp_menus=_make_dup(13,"miniapp_menus"); duplicates_bot_statistics=_make_dup(14,"bot_statistics")
duplicates_ad_preferences=_make_dup(15,"ad_preferences"); duplicates_processing_queues=_make_dup(16,"processing_queues")

def _expiry(fid,resource,expires_at,grace_days=0,now=None):
 if not isinstance(expires_at,str) or not isinstance(grace_days,int) or not 0<=grace_days<=365: raise ValueError("Caducidad no valida")
 try: expiry=datetime.fromisoformat(expires_at.replace("Z","+00:00"))
 except ValueError as exc: raise ValueError("Fecha no valida") from exc
 if expiry.tzinfo is None: raise ValueError("Zona horaria requerida")
 current=now or datetime.now(timezone.utc)
 if not isinstance(current,datetime) or current.tzinfo is None: raise ValueError("Ahora no valido")
 age=(current-expiry).total_seconds()/86400; expired=age>=grace_days
 return {"feature_id":fid,"resource":resource,"expires_at":expiry.isoformat(),"grace_days":grace_days,"expired":expired,"action":("expire" if expired else "keep"),"applied":False,"auditable":True}

def expire_creator_accounts(x,g=0,now=None): return _expiry(IDS[17],"creator_accounts",x,g,now)
def expire_partner_channels(x,g=0,now=None): return _expiry(IDS[18],"partner_channels",x,g,now)
def expire_community_campaigns(x,g=0,now=None): return _expiry(IDS[19],"community_campaigns",x,g,now)

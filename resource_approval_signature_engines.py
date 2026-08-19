"""Multilevel approvals and cryptographic integrity signatures for Moonbot."""
import hashlib, hmac, json
from resource_expiry_approval_engines import _approve

IDS=tuple(f"future-{n}" for n in (4622,4625,4628,4631,4634,4637,4640,4643,4646,4649,4652,4655,4658,4661,4664,4667,4670,4673,4676,4679))

def approve_managed_bots(l,d): return _approve(IDS[0],"managed_bots",l,d)
def approve_recurring_reminders(l,d): return _approve(IDS[1],"recurring_reminders",l,d)
def approve_security_events(l,d): return _approve(IDS[2],"security_events",l,d)
def approve_regional_maps(l,d): return _approve(IDS[3],"regional_maps",l,d)
def approve_backups(l,d): return _approve(IDS[4],"backups",l,d)
def approve_ai_learning_data(l,d): return _approve(IDS[5],"ai_learning_data",l,d)
def approve_rich_commands(l,d): return _approve(IDS[6],"rich_commands",l,d)
def approve_hub_notifications(l,d): return _approve(IDS[7],"hub_notifications",l,d)
def approve_cookie_policies(l,d): return _approve(IDS[8],"cookie_policies",l,d)
def approve_wayback_history(l,d): return _approve(IDS[9],"wayback_history",l,d)

def _canonical(envelope): return json.dumps(envelope,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def _sign(fid,resource,payload,key_id,secret):
 if not isinstance(payload,dict) or not isinstance(key_id,str) or not key_id.strip() or len(key_id)>120 or not isinstance(secret,str) or len(secret)<16: raise ValueError("Firma no valida")
 envelope={"feature_id":fid,"resource":resource,"payload":payload,"key_id":key_id,"algorithm":"HMAC-SHA256"}
 signature=hmac.new(secret.encode(),_canonical(envelope),hashlib.sha256).hexdigest()
 return {"envelope":envelope,"signature":signature,"signed":True,"secret_included":False,"auditable":True}
def verify_signature(result,secret):
 if not isinstance(result,dict) or not isinstance(secret,str): return False
 try: expected=hmac.new(secret.encode(),_canonical(result["envelope"]),hashlib.sha256).hexdigest(); return hmac.compare_digest(expected,result["signature"])
 except (KeyError,TypeError,ValueError): return False

def _make_sign(i,r): return lambda p,k,s:_sign(IDS[i],r,p,k,s)
sign_temporary_roles=_make_sign(10,"temporary_roles"); sign_managed_groups=_make_sign(11,"managed_groups"); sign_scheduled_messages=_make_sign(12,"scheduled_messages")
sign_rss_feeds=_make_sign(13,"rss_feeds"); sign_telegram_videos=_make_sign(14,"telegram_videos"); sign_blocklists=_make_sign(15,"blocklists")
sign_required_subscriptions=_make_sign(16,"required_subscriptions"); sign_signed_webhooks=_make_sign(17,"signed_webhooks"); sign_quiet_hours=_make_sign(18,"quiet_hours"); sign_correlated_incidents=_make_sign(19,"correlated_incidents")

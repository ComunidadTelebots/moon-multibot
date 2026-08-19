"""Conflict reconciliation and verifiable field anonymization for Moonbot."""
import hashlib, hmac, json
from resource_federation_reconcile_engines import _reconcile

IDS=tuple(f"future-{n}" for n in (4382,4385,4388,4391,4394,4397,4400,4403,4406,4409,4412,4415,4418,4421,4424,4427,4430,4433,4436,4439))

def reconcile_accessible_preferences(c,s,node_priority=(),manual=None): return _reconcile(IDS[0],"accessible_preferences",c,s,node_priority,manual)
def reconcile_integration_secrets(c,s,node_priority=(),manual=None): return _reconcile(IDS[1],"integration_secrets",c,s,node_priority,manual)
def reconcile_contextual_responses(c,s,node_priority=(),manual=None): return _reconcile(IDS[2],"contextual_responses",c,s,node_priority,manual)
def reconcile_miniapp_menus(c,s,node_priority=(),manual=None): return _reconcile(IDS[3],"miniapp_menus",c,s,node_priority,manual)
def reconcile_bot_statistics(c,s,node_priority=(),manual=None): return _reconcile(IDS[4],"bot_statistics",c,s,node_priority,manual)
def reconcile_ad_preferences(c,s,node_priority=(),manual=None): return _reconcile(IDS[5],"ad_preferences",c,s,node_priority,manual)
def reconcile_processing_queues(c,s,node_priority=(),manual=None): return _reconcile(IDS[6],"processing_queues",c,s,node_priority,manual)

def _anonymize(fid,resource,records,identifier_fields,secret):
 if not isinstance(records,list) or len(records)>10000 or not isinstance(identifier_fields,(list,tuple,set)) or not identifier_fields or any(not isinstance(x,str) or not x for x in identifier_fields) or not isinstance(secret,str) or len(secret)<16: raise ValueError("Anonimizacion no valida")
 fields=tuple(sorted(set(identifier_fields))); output=[]
 for record in records:
  if not isinstance(record,dict): raise ValueError("Registro no valido")
  row={k:v for k,v in record.items() if k not in fields}
  for field in fields:
   if field in record:
    raw=json.dumps(record[field],sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    row[field+"_anonymous_id"]=hmac.new(secret.encode(),(resource+":"+field+":").encode()+raw,hashlib.sha256).hexdigest()
  output.append(row)
 canonical=json.dumps(output,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
 proof=hmac.new(secret.encode(),b"proof:"+canonical,hashlib.sha256).hexdigest()
 return {"feature_id":fid,"resource":resource,"records":tuple(output),"record_count":len(output),"removed_fields":fields,"proof":proof,"algorithm":"HMAC-SHA256","secret_included":False,"verifiable":True,"auditable":True}

def _make_anon(i,r): return lambda rows,fields,secret:_anonymize(IDS[i],r,rows,fields,secret)
anonymize_creator_accounts=_make_anon(7,"creator_accounts"); anonymize_partner_channels=_make_anon(8,"partner_channels"); anonymize_community_campaigns=_make_anon(9,"community_campaigns")
anonymize_editorial_articles=_make_anon(10,"editorial_articles"); anonymize_moderated_images=_make_anon(11,"moderated_images"); anonymize_user_appeals=_make_anon(12,"user_appeals")
anonymize_mtproto_proxies=_make_anon(13,"mtproto_proxies"); anonymize_persistent_tasks=_make_anon(14,"persistent_tasks"); anonymize_moderation_rules=_make_anon(15,"moderation_rules")
anonymize_language_metrics=_make_anon(16,"language_metrics"); anonymize_community_translations=_make_anon(17,"community_translations"); anonymize_personal_consents=_make_anon(18,"personal_consents")
anonymize_telegram_reactions=_make_anon(19,"telegram_reactions")

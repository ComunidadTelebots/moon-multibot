"""Composable templates and reversible bulk-action plans for Moonbot."""
from resource_autotest_template_engines import _compose

IDS=tuple(f"future-{n}" for n in (4082,4085,4088,4091,4094,4097,4100,4103,4106,4109,4112,4115,4118,4121,4124,4127,4130,4133,4136,4139))

def compose_accessible_preferences(x): return _compose(IDS[0],"accessible_preferences",x)
def compose_integration_secrets(x): return _compose(IDS[1],"integration_secrets",x)
def compose_contextual_responses(x): return _compose(IDS[2],"contextual_responses",x)
def compose_miniapp_menus(x): return _compose(IDS[3],"miniapp_menus",x)
def compose_bot_statistics(x): return _compose(IDS[4],"bot_statistics",x)
def compose_ad_preferences(x): return _compose(IDS[5],"ad_preferences",x)
def compose_processing_queues(x): return _compose(IDS[6],"processing_queues",x)

def _bulk(fid,resource,target_ids,action,value=None):
 inverse={"enable":"disable","disable":"enable","tag":"untag","untag":"tag","archive":"restore","restore":"archive"}
 if action not in inverse: raise ValueError("Accion no reversible")
 if not isinstance(target_ids,(list,tuple)) or not 1<=len(target_ids)<=5000 or any(not isinstance(x,(str,int)) or not str(x) for x in target_ids): raise ValueError("Objetivos no validos")
 targets=tuple(dict.fromkeys(str(x) for x in target_ids))
 if action in ("tag","untag") and (not isinstance(value,str) or not value.strip() or len(value)>80): raise ValueError("Etiqueta no valida")
 operations=tuple({"target_id":x,"action":action,"value":value} for x in targets)
 rollback=tuple({"target_id":x,"action":inverse[action],"value":value} for x in reversed(targets))
 return {"feature_id":fid,"resource":resource,"operations":operations,"rollback":rollback,"target_count":len(targets),"deduplicated":len(target_ids)-len(targets),"reversible":True,"dry_run":True,"applied":False,"auditable":True}

def bulk_creator_accounts(t,a,v=None): return _bulk(IDS[7],"creator_accounts",t,a,v)
def bulk_partner_channels(t,a,v=None): return _bulk(IDS[8],"partner_channels",t,a,v)
def bulk_community_campaigns(t,a,v=None): return _bulk(IDS[9],"community_campaigns",t,a,v)
def bulk_editorial_articles(t,a,v=None): return _bulk(IDS[10],"editorial_articles",t,a,v)
def bulk_moderated_images(t,a,v=None): return _bulk(IDS[11],"moderated_images",t,a,v)
def bulk_user_appeals(t,a,v=None): return _bulk(IDS[12],"user_appeals",t,a,v)
def bulk_mtproto_proxies(t,a,v=None): return _bulk(IDS[13],"mtproto_proxies",t,a,v)
def bulk_persistent_tasks(t,a,v=None): return _bulk(IDS[14],"persistent_tasks",t,a,v)
def bulk_moderation_rules(t,a,v=None): return _bulk(IDS[15],"moderation_rules",t,a,v)
def bulk_language_metrics(t,a,v=None): return _bulk(IDS[16],"language_metrics",t,a,v)
def bulk_community_translations(t,a,v=None): return _bulk(IDS[17],"community_translations",t,a,v)
def bulk_personal_consents(t,a,v=None): return _bulk(IDS[18],"personal_consents",t,a,v)
def bulk_telegram_reactions(t,a,v=None): return _bulk(IDS[19],"telegram_reactions",t,a,v)

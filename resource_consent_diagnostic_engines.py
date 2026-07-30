"""Granular consent and autonomous diagnostic contracts for Moonbot resources."""
from resource_retention_consent_engines import _consent

IDS=tuple(f"future-{n}" for n in (3662,3665,3668,3671,3674,3677,3680,3683,3686,3689,3692,3695,3698,3701,3704,3707,3710,3713,3716,3719))

def consent_editorial_articles(s,x,g,v): return _consent(IDS[0],"editorial_articles",s,x,g,v)
def consent_moderated_images(s,x,g,v): return _consent(IDS[1],"moderated_images",s,x,g,v)
def consent_user_appeals(s,x,g,v): return _consent(IDS[2],"user_appeals",s,x,g,v)
def consent_mtproto_proxies(s,x,g,v): return _consent(IDS[3],"mtproto_proxies",s,x,g,v)
def consent_persistent_tasks(s,x,g,v): return _consent(IDS[4],"persistent_tasks",s,x,g,v)
def consent_moderation_rules(s,x,g,v): return _consent(IDS[5],"moderation_rules",s,x,g,v)
def consent_language_metrics(s,x,g,v): return _consent(IDS[6],"language_metrics",s,x,g,v)
def consent_community_translations(s,x,g,v): return _consent(IDS[7],"community_translations",s,x,g,v)
def consent_personal_consents(s,x,g,v): return _consent(IDS[8],"personal_consents",s,x,g,v)
def consent_telegram_reactions(s,x,g,v): return _consent(IDS[9],"telegram_reactions",s,x,g,v)
def consent_master_panels(s,x,g,v): return _consent(IDS[10],"master_panels",s,x,g,v)
def consent_channel_directories(s,x,g,v): return _consent(IDS[11],"channel_directories",s,x,g,v)
def consent_external_links(s,x,g,v): return _consent(IDS[12],"external_links",s,x,g,v)

def _diagnose(fid,resource,observations,required):
 if not isinstance(observations,dict): raise ValueError("Observaciones no validas")
 missing=tuple(sorted(k for k in required if k not in observations))
 failures=tuple(sorted(k for k in required if k in observations and observations[k] is not True))
 healthy=not missing and not failures
 return {"feature_id":fid,"resource":resource,"healthy":healthy,"status":("healthy" if healthy else "degraded"),"missing_checks":missing,"failed_checks":failures,"checked":tuple(sorted(set(required)&set(observations))),"autonomous":True,"read_only":True,"auditable":True}

def diagnose_admin_sessions(o): return _diagnose(IDS[13],"admin_sessions",o,("expiry_valid","mfa_enforced","revocation_reachable"))
def diagnose_community_profiles(o): return _diagnose(IDS[14],"community_profiles",o,("schema_valid","privacy_valid","owner_reachable"))
def diagnose_telegram_communities(o): return _diagnose(IDS[15],"telegram_communities",o,("bot_member","permissions_valid","chat_reachable"))
def diagnose_house_ads(o): return _diagnose(IDS[16],"house_ads",o,("creative_valid","target_valid","budget_valid"))
def diagnose_voice_notes(o): return _diagnose(IDS[17],"voice_notes",o,("codec_supported","duration_valid","file_reachable"))
def diagnose_suspicious_files(o): return _diagnose(IDS[18],"suspicious_files",o,("hash_present","scanner_reachable","quarantine_ready"))
def diagnose_captcha_decisions(o): return _diagnose(IDS[19],"captcha_decisions",o,("evidence_present","policy_versioned","appeal_available"))

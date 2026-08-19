"""Bounded offline queues and safe automatic-test plans for Moonbot resources."""
from resource_alert_offline_engines import _offline

IDS=tuple(f"future-{n}" for n in (3962,3965,3968,3971,3974,3977,3980,3983,3986,3989,3992,3995,3998,4001,4004,4007,4010,4013,4016,4019))

def offline_editorial_articles(o,max_items=1000): return _offline(IDS[0],"editorial_articles",o,max_items)
def offline_moderated_images(o,max_items=1000): return _offline(IDS[1],"moderated_images",o,max_items)
def offline_user_appeals(o,max_items=1000): return _offline(IDS[2],"user_appeals",o,max_items)
def offline_mtproto_proxies(o,max_items=1000): return _offline(IDS[3],"mtproto_proxies",o,max_items)
def offline_persistent_tasks(o,max_items=1000): return _offline(IDS[4],"persistent_tasks",o,max_items)
def offline_moderation_rules(o,max_items=1000): return _offline(IDS[5],"moderation_rules",o,max_items)
def offline_language_metrics(o,max_items=1000): return _offline(IDS[6],"language_metrics",o,max_items)
def offline_community_translations(o,max_items=1000): return _offline(IDS[7],"community_translations",o,max_items)
def offline_personal_consents(o,max_items=1000): return _offline(IDS[8],"personal_consents",o,max_items)
def offline_telegram_reactions(o,max_items=1000): return _offline(IDS[9],"telegram_reactions",o,max_items)
def offline_master_panels(o,max_items=1000): return _offline(IDS[10],"master_panels",o,max_items)
def offline_channel_directories(o,max_items=1000): return _offline(IDS[11],"channel_directories",o,max_items)
def offline_external_links(o,max_items=1000): return _offline(IDS[12],"external_links",o,max_items)

def _autotest(fid,resource,fixtures,checks):
 allowed={"schema","permissions","privacy","integrity","availability","idempotency"}
 if not isinstance(fixtures,(list,tuple)) or not fixtures or any(not isinstance(x,str) or not x for x in fixtures): raise ValueError("Fixtures no validas")
 if not isinstance(checks,(list,tuple,set)) or not checks: raise ValueError("Checks no validos")
 normalized=tuple(sorted(set(checks)))
 if any(x not in allowed for x in normalized): raise ValueError("Check desconocido")
 cases=tuple({"fixture":f,"checks":normalized,"sandboxed":True,"mutates_production":False} for f in fixtures)
 return {"feature_id":fid,"resource":resource,"cases":cases,"case_count":len(cases),"automatic":True,"sandbox_required":True,"executed":False,"auditable":True}

def autotest_admin_sessions(f,c): return _autotest(IDS[13],"admin_sessions",f,c)
def autotest_community_profiles(f,c): return _autotest(IDS[14],"community_profiles",f,c)
def autotest_telegram_communities(f,c): return _autotest(IDS[15],"telegram_communities",f,c)
def autotest_house_ads(f,c): return _autotest(IDS[16],"house_ads",f,c)
def autotest_voice_notes(f,c): return _autotest(IDS[17],"voice_notes",f,c)
def autotest_suspicious_files(f,c): return _autotest(IDS[18],"suspicious_files",f,c)
def autotest_captcha_decisions(f,c): return _autotest(IDS[19],"captcha_decisions",f,c)

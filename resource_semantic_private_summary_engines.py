"""Local searches and privacy-preserving aggregate summaries for Moonbot."""
from collections import Counter
from resource_history_semantic_engines import _search

IDS=tuple(f"future-{n}" for n in (3842,3845,3848,3851,3854,3857,3860,3863,3866,3869,3872,3875,3878,3881,3884,3887,3890,3893,3896,3899))

def search_master_panels(q,d,limit=10): return _search(IDS[0],"master_panels",q,d,limit)
def search_channel_directories(q,d,limit=10): return _search(IDS[1],"channel_directories",q,d,limit)
def search_external_links(q,d,limit=10): return _search(IDS[2],"external_links",q,d,limit)

def _summary(fid,resource,rows,dimensions=()):
 if not isinstance(rows,list) or len(rows)>100000: raise ValueError("Datos no validos")
 counts={d:Counter() for d in dimensions}; missing={d:0 for d in dimensions}
 for row in rows:
  if not isinstance(row,dict): raise ValueError("Registro no valido")
  for d in dimensions:
   value=row.get(d)
   if value is None: missing[d]+=1
   elif isinstance(value,(str,int,bool)) and len(str(value))<=80: counts[d][str(value)]+=1
   else: counts[d]["[OTHER]"]+=1
 distributions={d:tuple(sorted(c.items(),key=lambda x:(-x[1],x[0]))[:20]) for d,c in counts.items()}
 return {"feature_id":fid,"resource":resource,"record_count":len(rows),"distributions":distributions,"missing":missing,"private":True,"aggregate_only":True,"raw_records_included":False,"auditable":True}

def summarize_admin_sessions(r): return _summary(IDS[3],"admin_sessions",r,("mfa","status"))
def summarize_community_profiles(r): return _summary(IDS[4],"community_profiles",r,("visibility","locale"))
def summarize_telegram_communities(r): return _summary(IDS[5],"telegram_communities",r,("status","type"))
def summarize_house_ads(r): return _summary(IDS[6],"house_ads",r,("status","target"))
def summarize_voice_notes(r): return _summary(IDS[7],"voice_notes",r,("language","codec"))
def summarize_suspicious_files(r): return _summary(IDS[8],"suspicious_files",r,("verdict","mime_type"))
def summarize_captcha_decisions(r): return _summary(IDS[9],"captcha_decisions",r,("decision","policy_version"))
def summarize_managed_bots(r): return _summary(IDS[10],"managed_bots",r,("status","mode"))
def summarize_recurring_reminders(r): return _summary(IDS[11],"recurring_reminders",r,("timezone","status"))
def summarize_security_events(r): return _summary(IDS[12],"security_events",r,("severity","category"))
def summarize_regional_maps(r): return _summary(IDS[13],"regional_maps",r,("region","privacy_level"))
def summarize_backups(r): return _summary(IDS[14],"backups",r,("verified","status"))
def summarize_ai_learning_data(r): return _summary(IDS[15],"ai_learning_data",r,("consented","language"))
def summarize_rich_commands(r): return _summary(IDS[16],"rich_commands",r,("format","status"))
def summarize_hub_notifications(r): return _summary(IDS[17],"hub_notifications",r,("priority","status"))
def summarize_cookie_policies(r): return _summary(IDS[18],"cookie_policies",r,("version","status"))
def summarize_wayback_history(r): return _summary(IDS[19],"wayback_history",r,("available","status"))

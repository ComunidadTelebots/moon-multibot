"""Historical comparisons and local semantic-like search for Moonbot resources."""
import re, unicodedata
from resource_diagnostic_history_engines import _compare

IDS=tuple(f"future-{n}" for n in (3782,3785,3788,3791,3794,3797,3800,3803,3806,3809,3812,3815,3818,3821,3824,3827,3830,3833,3836,3839))

def compare_accessible_preferences(a,b): return _compare(IDS[0],"accessible_preferences",a,b)
def compare_integration_secrets(a,b): return _compare(IDS[1],"integration_secrets",a,b)
def compare_contextual_responses(a,b): return _compare(IDS[2],"contextual_responses",a,b)
def compare_miniapp_menus(a,b): return _compare(IDS[3],"miniapp_menus",a,b)
def compare_bot_statistics(a,b): return _compare(IDS[4],"bot_statistics",a,b)
def compare_ad_preferences(a,b): return _compare(IDS[5],"ad_preferences",a,b)
def compare_processing_queues(a,b): return _compare(IDS[6],"processing_queues",a,b)

def _tokens(value):
 normalized=unicodedata.normalize("NFKC",value).casefold()
 return set(re.findall(r"[\w-]{2,}",normalized,flags=re.UNICODE))

def _search(fid,resource,query,documents,limit=10):
 if not isinstance(query,str) or not query.strip() or len(query)>500: raise ValueError("Consulta no valida")
 if not isinstance(documents,list) or not isinstance(limit,int) or not 1<=limit<=100: raise ValueError("Busqueda no valida")
 q=_tokens(query); scored=[]
 for doc in documents:
  if not isinstance(doc,dict) or not isinstance(doc.get("id"),(str,int)) or not isinstance(doc.get("text"),str): raise ValueError("Documento no valido")
  t=_tokens(doc["text"]); score=len(q&t)/len(q|t) if q|t else 0.0
  if score: scored.append({"id":str(doc["id"]),"score":round(score,6),"matched_terms":tuple(sorted(q&t))})
 scored.sort(key=lambda x:(-x["score"],x["id"]))
 return {"feature_id":fid,"resource":resource,"query_terms":tuple(sorted(q)),"results":tuple(scored[:limit]),"local_only":True,"deterministic":True,"auditable":True}

def search_creator_accounts(q,d,limit=10): return _search(IDS[7],"creator_accounts",q,d,limit)
def search_partner_channels(q,d,limit=10): return _search(IDS[8],"partner_channels",q,d,limit)
def search_community_campaigns(q,d,limit=10): return _search(IDS[9],"community_campaigns",q,d,limit)
def search_editorial_articles(q,d,limit=10): return _search(IDS[10],"editorial_articles",q,d,limit)
def search_moderated_images(q,d,limit=10): return _search(IDS[11],"moderated_images",q,d,limit)
def search_user_appeals(q,d,limit=10): return _search(IDS[12],"user_appeals",q,d,limit)
def search_mtproto_proxies(q,d,limit=10): return _search(IDS[13],"mtproto_proxies",q,d,limit)
def search_persistent_tasks(q,d,limit=10): return _search(IDS[14],"persistent_tasks",q,d,limit)
def search_moderation_rules(q,d,limit=10): return _search(IDS[15],"moderation_rules",q,d,limit)
def search_language_metrics(q,d,limit=10): return _search(IDS[16],"language_metrics",q,d,limit)
def search_community_translations(q,d,limit=10): return _search(IDS[17],"community_translations",q,d,limit)
def search_personal_consents(q,d,limit=10): return _search(IDS[18],"personal_consents",q,d,limit)
def search_telegram_reactions(q,d,limit=10): return _search(IDS[19],"telegram_reactions",q,d,limit)

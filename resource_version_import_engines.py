"""Semantic versions and transactional import plans for Moonbot resources."""
import copy
from resource_delegation_version_engines import _version
IDS=tuple(f"future-{n}" for n in (3482,3485,3488,3491,3494,3497,3500,3503,3506,3509,3512,3515,3518,3521,3524,3527,3530,3533,3536,3539))
def version_accessible_preferences(v,k,c): return _version(IDS[0],"accessible_preferences",v,k,c)
def version_integration_secrets(v,k,c): return _version(IDS[1],"integration_secrets",v,k,c)
def version_contextual_responses(v,k,c): return _version(IDS[2],"contextual_responses",v,k,c)
def version_miniapp_menus(v,k,c): return _version(IDS[3],"miniapp_menus",v,k,c)
def version_bot_statistics(v,k,c): return _version(IDS[4],"bot_statistics",v,k,c)
def version_ad_preferences(v,k,c): return _version(IDS[5],"ad_preferences",v,k,c)
def version_processing_queues(v,k,c): return _version(IDS[6],"processing_queues",v,k,c)
def _import(fid,resource,rows,required,unique,validators):
 if not isinstance(rows,list) or not rows or len(rows)>1000: raise ValueError("Lote no válido")
 staged=[]; errors=[]; seen=set()
 for index,source in enumerate(rows):
  if not isinstance(source,dict): errors.append({"index":index,"field":"row","error":"object_required"}); continue
  missing=[field for field in required if field not in source]
  if missing: errors.append({"index":index,"field":missing[0],"error":"required"}); continue
  key=str(source[unique])
  if not key or key in seen: errors.append({"index":index,"field":unique,"error":"duplicate_or_empty"}); continue
  invalid=next((field for field,check in validators.items() if not check(source.get(field))),None)
  if invalid: errors.append({"index":index,"field":invalid,"error":"invalid"}); continue
  seen.add(key); staged.append(copy.deepcopy(source))
 return {"feature_id":fid,"resource":resource,"received":len(rows),"staged":staged,"errors":errors,"valid":not errors,"atomic":True,"applied":False,"requires_confirmation":True}
def import_creator_accounts(r): return _import(IDS[7],"creator_accounts",r,{"id","role","verified"},"id",{"role":lambda x:x in ("user","admin","creator"),"verified":lambda x:isinstance(x,bool)})
def import_associated_channels(r): return _import(IDS[8],"associated_channels",r,{"chat_id","title","type"},"chat_id",{"type":lambda x:x in ("channel","group","supergroup"),"title":lambda x:isinstance(x,str) and 0<len(x)<=200})
def import_community_campaigns(r): return _import(IDS[9],"community_campaigns",r,{"id","text","status"},"id",{"text":lambda x:isinstance(x,str) and 0<len(x)<=3500,"status":lambda x:x in ("draft","pending","approved")})
def import_editorial_articles(r): return _import(IDS[10],"editorial_articles",r,{"slug","title","body"},"slug",{"title":lambda x:isinstance(x,str) and 0<len(x)<=300,"body":lambda x:isinstance(x,str) and len(x)<=50000})
def import_moderated_images(r): return _import(IDS[11],"moderated_images",r,{"sha256","verdict","size"},"sha256",{"sha256":lambda x:isinstance(x,str) and len(x)==64,"verdict":lambda x:x in ("safe","unsafe","pending"),"size":lambda x:isinstance(x,int) and 0<x<=200*1024*1024})
def import_user_appeals(r): return _import(IDS[12],"user_appeals",r,{"id","user_id","status"},"id",{"status":lambda x:x in ("pending","approved","rejected"),"user_id":lambda x:bool(str(x))})
def import_mtproto_proxies(r): return _import(IDS[13],"mtproto_proxies",r,{"id","server","port"},"id",{"server":lambda x:isinstance(x,str) and bool(x),"port":lambda x:isinstance(x,int) and 1<=x<=65535})
def import_persistent_tasks(r): return _import(IDS[14],"persistent_tasks",r,{"id","owner_id","title"},"id",{"owner_id":lambda x:bool(str(x)),"title":lambda x:isinstance(x,str) and 0<len(x)<=300})
def import_moderation_rules(r): return _import(IDS[15],"moderation_rules",r,{"id","condition","action"},"id",{"condition":lambda x:isinstance(x,dict) and bool(x),"action":lambda x:x in ("observe","warn","delete","review")})
def import_language_metrics(r): return _import(IDS[16],"language_metrics",r,{"locale","samples","confidence"},"locale",{"samples":lambda x:isinstance(x,int) and x>=0,"confidence":lambda x:isinstance(x,(int,float)) and 0<=x<=1})
def import_community_translations(r): return _import(IDS[17],"community_translations",r,{"key","locale","value"},"key",{"locale":lambda x:isinstance(x,str) and 2<=len(x)<=15,"value":lambda x:isinstance(x,str) and len(x)<=10000})
def import_personal_consents(r): return _import(IDS[18],"personal_consents",r,{"id","user_id","purpose","granted"},"id",{"purpose":lambda x:x in ("analytics","ai_learning","notifications","ads"),"granted":lambda x:isinstance(x,bool)})
def import_telegram_reactions(r): return _import(IDS[19],"telegram_reactions",r,{"id","message_id","reaction"},"id",{"message_id":lambda x:bool(str(x)),"reaction":lambda x:isinstance(x,str) and 0<len(x)<=32})

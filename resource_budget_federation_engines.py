"""Budget guardrails and dry-run federated synchronization for Moonbot."""
from resource_realtime_budget_engines import _budget

IDS=tuple(f"future-{n}" for n in (4262,4265,4268,4271,4274,4277,4280,4283,4286,4289,4292,4295,4298,4301,4304,4307,4310,4313,4316,4319))

def budget_editorial_articles(b,s,r,c): return _budget(IDS[0],"editorial_articles",b,s,r,c)
def budget_moderated_images(b,s,r,c): return _budget(IDS[1],"moderated_images",b,s,r,c)
def budget_user_appeals(b,s,r,c): return _budget(IDS[2],"user_appeals",b,s,r,c)
def budget_mtproto_proxies(b,s,r,c): return _budget(IDS[3],"mtproto_proxies",b,s,r,c)
def budget_persistent_tasks(b,s,r,c): return _budget(IDS[4],"persistent_tasks",b,s,r,c)
def budget_moderation_rules(b,s,r,c): return _budget(IDS[5],"moderation_rules",b,s,r,c)
def budget_language_metrics(b,s,r,c): return _budget(IDS[6],"language_metrics",b,s,r,c)
def budget_community_translations(b,s,r,c): return _budget(IDS[7],"community_translations",b,s,r,c)
def budget_personal_consents(b,s,r,c): return _budget(IDS[8],"personal_consents",b,s,r,c)
def budget_telegram_reactions(b,s,r,c): return _budget(IDS[9],"telegram_reactions",b,s,r,c)
def budget_master_panels(b,s,r,c): return _budget(IDS[10],"master_panels",b,s,r,c)
def budget_channel_directories(b,s,r,c): return _budget(IDS[11],"channel_directories",b,s,r,c)
def budget_external_links(b,s,r,c): return _budget(IDS[12],"external_links",b,s,r,c)

def _federate(fid,resource,changes,trusted_nodes):
 if not isinstance(trusted_nodes,(list,tuple,set)) or not trusted_nodes or any(not isinstance(x,str) or not x for x in trusted_nodes): raise ValueError("Nodos no validos")
 trust=set(trusted_nodes)
 if not isinstance(changes,list) or len(changes)>10000: raise ValueError("Cambios no validos")
 grouped={}; rejected=[]
 for change in changes:
  if not isinstance(change,dict) or set(change)!={"node","entity_id","revision","payload"} or change["node"] not in trust or not isinstance(change["entity_id"],(str,int)) or not isinstance(change["revision"],int) or change["revision"]<0 or not isinstance(change["payload"],dict):
   rejected.append(change.get("entity_id") if isinstance(change,dict) else None); continue
  grouped.setdefault(str(change["entity_id"]),[]).append(change)
 accepted=[]; conflicts=[]
 for entity_id,versions in sorted(grouped.items()):
  top=max(x["revision"] for x in versions); leaders=[x for x in versions if x["revision"]==top]
  canonical={repr(sorted(x["payload"].items())) for x in leaders}
  if len(canonical)>1: conflicts.append({"entity_id":entity_id,"revision":top,"nodes":tuple(sorted(x["node"] for x in leaders))})
  else: accepted.append({"entity_id":entity_id,"revision":top,"source_node":sorted(x["node"] for x in leaders)[0],"payload":leaders[0]["payload"]})
 return {"feature_id":fid,"resource":resource,"accepted":tuple(accepted),"conflicts":tuple(conflicts),"rejected":tuple(str(x) for x in rejected),"ready":not conflicts and not rejected,"federated":True,"dry_run":True,"applied":False,"auditable":True}

def federate_admin_sessions(c,n): return _federate(IDS[13],"admin_sessions",c,n)
def federate_community_profiles(c,n): return _federate(IDS[14],"community_profiles",c,n)
def federate_telegram_communities(c,n): return _federate(IDS[15],"telegram_communities",c,n)
def federate_house_ads(c,n): return _federate(IDS[16],"house_ads",c,n)
def federate_voice_notes(c,n): return _federate(IDS[17],"voice_notes",c,n)
def federate_suspicious_files(c,n): return _federate(IDS[18],"suspicious_files",c,n)
def federate_captcha_decisions(c,n): return _federate(IDS[19],"captcha_decisions",c,n)

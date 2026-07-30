"""Automatic-expiry decisions and multilevel approval evaluation for Moonbot."""
from resource_duplicate_expiry_engines import _expiry

IDS=tuple(f"future-{n}" for n in (4562,4565,4568,4571,4574,4577,4580,4583,4586,4589,4592,4595,4598,4601,4604,4607,4610,4613,4616,4619))

def expire_editorial_articles(x,g=0,now=None): return _expiry(IDS[0],"editorial_articles",x,g,now)
def expire_moderated_images(x,g=0,now=None): return _expiry(IDS[1],"moderated_images",x,g,now)
def expire_user_appeals(x,g=0,now=None): return _expiry(IDS[2],"user_appeals",x,g,now)
def expire_mtproto_proxies(x,g=0,now=None): return _expiry(IDS[3],"mtproto_proxies",x,g,now)
def expire_persistent_tasks(x,g=0,now=None): return _expiry(IDS[4],"persistent_tasks",x,g,now)
def expire_moderation_rules(x,g=0,now=None): return _expiry(IDS[5],"moderation_rules",x,g,now)
def expire_language_metrics(x,g=0,now=None): return _expiry(IDS[6],"language_metrics",x,g,now)
def expire_community_translations(x,g=0,now=None): return _expiry(IDS[7],"community_translations",x,g,now)
def expire_personal_consents(x,g=0,now=None): return _expiry(IDS[8],"personal_consents",x,g,now)
def expire_telegram_reactions(x,g=0,now=None): return _expiry(IDS[9],"telegram_reactions",x,g,now)
def expire_master_panels(x,g=0,now=None): return _expiry(IDS[10],"master_panels",x,g,now)
def expire_channel_directories(x,g=0,now=None): return _expiry(IDS[11],"channel_directories",x,g,now)
def expire_external_links(x,g=0,now=None): return _expiry(IDS[12],"external_links",x,g,now)

def _approve(fid,resource,levels,decisions):
 if not isinstance(levels,list) or not levels or len(levels)>10 or not isinstance(decisions,list): raise ValueError("Aprobacion no valida")
 roles=[]; quorum={}
 for level in levels:
  if not isinstance(level,dict) or set(level)!={"role","quorum"} or not isinstance(level["role"],str) or not level["role"] or level["role"] in quorum or not isinstance(level["quorum"],int) or not 1<=level["quorum"]<=20: raise ValueError("Nivel no valido")
  roles.append(level["role"]); quorum[level["role"]]=level["quorum"]
 votes={role:{} for role in roles}
 for decision in decisions:
  if not isinstance(decision,dict) or set(decision)!={"actor_id","role","decision"} or decision["role"] not in votes or not isinstance(decision["actor_id"],str) or not decision["actor_id"] or decision["decision"] not in ("approve","reject"): raise ValueError("Decision no valida")
  votes[decision["role"]][decision["actor_id"]]=decision["decision"]
 rejected=any("reject" in actor_votes.values() for actor_votes in votes.values())
 completed=tuple(role for role in roles if sum(v=="approve" for v in votes[role].values())>=quorum[role])
 status="rejected" if rejected else ("approved" if len(completed)==len(roles) else "pending")
 return {"feature_id":fid,"resource":resource,"status":status,"completed_levels":completed,"pending_levels":tuple(x for x in roles if x not in completed),"multilevel":True,"execution_authorized":status=="approved","executed":False,"auditable":True}

def _make_approval(i,r): return lambda l,d:_approve(IDS[i],r,l,d)
approve_admin_sessions=_make_approval(13,"admin_sessions"); approve_community_profiles=_make_approval(14,"community_profiles"); approve_telegram_communities=_make_approval(15,"telegram_communities")
approve_house_ads=_make_approval(16,"house_ads"); approve_voice_notes=_make_approval(17,"voice_notes"); approve_suspicious_files=_make_approval(18,"suspicious_files"); approve_captcha_decisions=_make_approval(19,"captcha_decisions")

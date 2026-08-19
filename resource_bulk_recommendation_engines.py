"""Reversible bulk plans and explainable recommendations for Moonbot."""
from resource_template_bulk_engines import _bulk

IDS=tuple(f"future-{n}" for n in (4142,4145,4148,4151,4154,4157,4160,4163,4166,4169,4172,4175,4178,4181,4184,4187,4190,4193,4196,4199))

def bulk_master_panels(t,a,v=None): return _bulk(IDS[0],"master_panels",t,a,v)
def bulk_channel_directories(t,a,v=None): return _bulk(IDS[1],"channel_directories",t,a,v)
def bulk_external_links(t,a,v=None): return _bulk(IDS[2],"external_links",t,a,v)

def _recommend(fid,resource,candidates,limit=5):
 if not isinstance(candidates,list) or not isinstance(limit,int) or not 1<=limit<=50: raise ValueError("Candidatos no validos")
 ranked=[]
 for item in candidates:
  if not isinstance(item,dict) or set(item)!={"id","score","reasons"}: raise ValueError("Candidato no valido")
  if not isinstance(item["id"],(str,int)) or not isinstance(item["score"],(int,float)) or isinstance(item["score"],bool) or not 0<=item["score"]<=1: raise ValueError("Puntuacion no valida")
  if not isinstance(item["reasons"],(list,tuple)) or not item["reasons"] or any(not isinstance(x,str) or not x.strip() or len(x)>240 for x in item["reasons"]): raise ValueError("Explicacion no valida")
  ranked.append({"id":str(item["id"]),"score":round(float(item["score"]),6),"reasons":tuple(item["reasons"])})
 ranked.sort(key=lambda x:(-x["score"],x["id"]))
 return {"feature_id":fid,"resource":resource,"recommendations":tuple(ranked[:limit]),"explainable":True,"automatic_action":False,"human_review_required":True,"auditable":True}

def _make_rec(i,resource): return lambda c,limit=5:_recommend(IDS[i],resource,c,limit)
recommend_admin_sessions=_make_rec(3,"admin_sessions"); recommend_community_profiles=_make_rec(4,"community_profiles"); recommend_telegram_communities=_make_rec(5,"telegram_communities")
recommend_house_ads=_make_rec(6,"house_ads"); recommend_voice_notes=_make_rec(7,"voice_notes"); recommend_suspicious_files=_make_rec(8,"suspicious_files")
recommend_captcha_decisions=_make_rec(9,"captcha_decisions"); recommend_managed_bots=_make_rec(10,"managed_bots"); recommend_recurring_reminders=_make_rec(11,"recurring_reminders")
recommend_security_events=_make_rec(12,"security_events"); recommend_regional_maps=_make_rec(13,"regional_maps"); recommend_backups=_make_rec(14,"backups")
recommend_ai_learning_data=_make_rec(15,"ai_learning_data"); recommend_rich_commands=_make_rec(16,"rich_commands"); recommend_hub_notifications=_make_rec(17,"hub_notifications")
recommend_cookie_policies=_make_rec(18,"cookie_policies"); recommend_wayback_history=_make_rec(19,"wayback_history")

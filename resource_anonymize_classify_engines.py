"""Verifiable anonymization and human-reviewed assisted classification for Moonbot."""
from resource_reconcile_anonymize_engines import _anonymize

IDS=tuple(f"future-{n}" for n in (4442,4445,4448,4451,4454,4457,4460,4463,4466,4469,4472,4475,4478,4481,4484,4487,4490,4493,4496,4499))

def anonymize_master_panels(r,f,s): return _anonymize(IDS[0],"master_panels",r,f,s)
def anonymize_channel_directories(r,f,s): return _anonymize(IDS[1],"channel_directories",r,f,s)
def anonymize_external_links(r,f,s): return _anonymize(IDS[2],"external_links",r,f,s)

def _classify(fid,resource,candidates,review_threshold=.8):
 if not isinstance(candidates,list) or not candidates or not isinstance(review_threshold,(int,float)) or isinstance(review_threshold,bool) or not 0<=review_threshold<=1: raise ValueError("Clasificacion no valida")
 normalized=[]
 for item in candidates:
  if not isinstance(item,dict) or set(item)!={"label","score","reason"} or not isinstance(item["label"],str) or not item["label"].strip() or len(item["label"])>80 or not isinstance(item["score"],(int,float)) or isinstance(item["score"],bool) or not 0<=item["score"]<=1 or not isinstance(item["reason"],str) or not item["reason"].strip() or len(item["reason"])>240: raise ValueError("Candidato no valido")
  normalized.append({"label":item["label"],"score":round(float(item["score"]),6),"reason":item["reason"]})
 normalized.sort(key=lambda x:(-x["score"],x["label"])); best=normalized[0]
 return {"feature_id":fid,"resource":resource,"suggestion":best,"alternatives":tuple(normalized[1:]),"review_threshold":float(review_threshold),"low_confidence":best["score"]<review_threshold,"assisted":True,"human_review_required":True,"label_applied":False,"auditable":True}

def _make_classify(i,r): return lambda c,review_threshold=.8:_classify(IDS[i],r,c,review_threshold)
classify_admin_sessions=_make_classify(3,"admin_sessions"); classify_community_profiles=_make_classify(4,"community_profiles"); classify_telegram_communities=_make_classify(5,"telegram_communities")
classify_house_ads=_make_classify(6,"house_ads"); classify_voice_notes=_make_classify(7,"voice_notes"); classify_suspicious_files=_make_classify(8,"suspicious_files")
classify_captcha_decisions=_make_classify(9,"captcha_decisions"); classify_managed_bots=_make_classify(10,"managed_bots"); classify_recurring_reminders=_make_classify(11,"recurring_reminders")
classify_security_events=_make_classify(12,"security_events"); classify_regional_maps=_make_classify(13,"regional_maps"); classify_backups=_make_classify(14,"backups")
classify_ai_learning_data=_make_classify(15,"ai_learning_data"); classify_rich_commands=_make_classify(16,"rich_commands"); classify_hub_notifications=_make_classify(17,"hub_notifications")
classify_cookie_policies=_make_classify(18,"cookie_policies"); classify_wayback_history=_make_classify(19,"wayback_history")

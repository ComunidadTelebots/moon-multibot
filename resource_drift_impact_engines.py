"""Resource-specific drift and impact contracts for Moonbot sublot 2."""
from resource_forecast_engines import _drift
IDS=tuple(f"future-{n}" for n in (3062,3065,3068,3071,3074,3077,3080,3083,3086,3089,3092,3095,3098,3101,3104,3107,3110,3113,3116,3119))
def _tag(result,fid,resource): result.update(feature_id=fid,resource=resource); return result
def drift_editorial_articles(a,b,threshold=.2): return _tag(_drift(a,b,("publish_rate","correction_rate","reading_time"),threshold),IDS[0],"editorial_articles")
def drift_moderated_images(a,b,threshold=.2): return _tag(_drift(a,b,("unsafe_ratio","review_seconds","false_positive_ratio"),threshold),IDS[1],"moderated_images")
def drift_user_appeals(a,b,threshold=.2): return _tag(_drift(a,b,("approval_ratio","resolution_hours","reopen_ratio"),threshold),IDS[2],"user_appeals")
def drift_mtproto_proxies(a,b,threshold=.2): return _tag(_drift(a,b,("availability_ratio","latency_ms","failure_ratio"),threshold),IDS[3],"mtproto_proxies")
def drift_persistent_tasks(a,b,threshold=.2): return _tag(_drift(a,b,("completion_ratio","overdue_ratio","cycle_hours"),threshold),IDS[4],"persistent_tasks")
def drift_moderation_rules(a,b,threshold=.2): return _tag(_drift(a,b,("match_ratio","action_ratio","appeal_ratio"),threshold),IDS[5],"moderation_rules")
def drift_language_metrics(a,b,threshold=.2): return _tag(_drift(a,b,("detected_ratio","unknown_ratio","confidence"),threshold),IDS[6],"language_metrics")
def drift_community_translations(a,b,threshold=.2): return _tag(_drift(a,b,("coverage_ratio","approval_ratio","edit_ratio"),threshold),IDS[7],"community_translations")
def drift_personal_consents(a,b,threshold=.2): return _tag(_drift(a,b,("grant_ratio","withdraw_ratio","expiry_ratio"),threshold),IDS[8],"personal_consents")
def drift_telegram_reactions(a,b,threshold=.2): return _tag(_drift(a,b,("reaction_rate","unique_ratio","removal_ratio"),threshold),IDS[9],"telegram_reactions")
def drift_master_panels(a,b,threshold=.2): return _tag(_drift(a,b,("session_minutes","error_ratio","action_rate"),threshold),IDS[10],"master_panels")
def drift_channel_directories(a,b,threshold=.2): return _tag(_drift(a,b,("listing_growth","stale_ratio","click_ratio"),threshold),IDS[11],"channel_directories")
def drift_external_links(a,b,threshold=.2): return _tag(_drift(a,b,("safe_ratio","redirect_ratio","failure_ratio"),threshold),IDS[12],"external_links")
def _impact(fid,resource,before,change,weights):
 if not isinstance(before,dict) or not isinstance(change,dict): raise ValueError("Escenario requerido")
 effects={key:round(float(change.get(key,0))*weight,3) for key,weight in weights.items()}
 return {"feature_id":fid,"resource":resource,"baseline":{k:float(before.get(k,0)) for k in weights},"effects":effects,"risk":round(sum(abs(x) for x in effects.values()),3),"executed":False,"explainable":True}
def impact_admin_sessions(b,c): return _impact(IDS[13],"admin_sessions",b,c,{"concurrency":1.2,"timeout_minutes":.4,"mfa_ratio":-1})
def impact_community_profiles(b,c): return _impact(IDS[14],"community_profiles",b,c,{"visible_fields":.5,"completion_ratio":-1,"report_ratio":2})
def impact_telegram_communities(b,c): return _impact(IDS[15],"telegram_communities",b,c,{"member_groups":.8,"admin_load":1.5,"join_rate":.4})
def impact_house_ads(b,c): return _impact(IDS[16],"house_ads",b,c,{"daily_impressions":.01,"frequency":1.3,"opt_out_ratio":2})
def impact_voice_notes(b,c): return _impact(IDS[17],"voice_notes",b,c,{"max_minutes":.7,"transcription_ratio":1.1,"retention_days":.2})
def impact_suspicious_files(b,c): return _impact(IDS[18],"suspicious_files",b,c,{"max_mb":.3,"scan_ratio":-1.2,"quarantine_hours":.5})
def impact_captcha_decisions(b,c): return _impact(IDS[19],"captcha_decisions",b,c,{"attempts":.8,"timeout_seconds":.1,"appeal_ratio":1.4})

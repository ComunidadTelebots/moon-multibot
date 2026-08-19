"""Resource-specific impact simulation and selective recovery plans for Moonbot."""
import copy
IDS=tuple(f"future-{n}" for n in (3122,3125,3128,3131,3134,3137,3140,3143,3146,3149,3152,3155,3158,3161,3164,3167,3170,3173,3176,3179))
def _impact(fid,resource,baseline,changes,weights):
 if not isinstance(baseline,dict) or not isinstance(changes,dict): raise ValueError("Escenario no válido")
 effects={k:round(float(changes.get(k,0))*w,3) for k,w in weights.items()}; return {"feature_id":fid,"resource":resource,"baseline":{k:float(baseline.get(k,0)) for k in weights},"effects":effects,"risk":round(sum(abs(v) for v in effects.values()),3),"executed":False}
def impact_managed_bots(b,c): return _impact(IDS[0],"managed_bots",b,c,{"instances":1.2,"error_budget":-2,"restart_minutes":.5})
def impact_recurring_reminders(b,c): return _impact(IDS[1],"recurring_reminders",b,c,{"frequency":1,"recipients":.2,"quiet_deferrals":.8})
def impact_security_events(b,c): return _impact(IDS[2],"security_events",b,c,{"retention_days":.1,"alert_threshold":-1.5,"reviewers":-.5})
def impact_regional_maps(b,c): return _impact(IDS[3],"regional_maps",b,c,{"regions":.4,"precision":1.2,"privacy_radius":-.8})
def impact_backups(b,c): return _impact(IDS[4],"backups",b,c,{"retention_days":.2,"frequency":1,"verification":-1})
def impact_ai_learning_data(b,c): return _impact(IDS[5],"ai_learning_data",b,c,{"samples":.001,"retention_days":.2,"consent_ratio":-2})
def impact_rich_commands(b,c): return _impact(IDS[6],"rich_commands",b,c,{"max_length":.001,"entities":.3,"fallback_ratio":1.2})
def impact_hub_notifications(b,c): return _impact(IDS[7],"hub_notifications",b,c,{"daily_limit":.2,"priority_threshold":-1,"recipients":.1})
def impact_cookie_policies(b,c): return _impact(IDS[8],"cookie_policies",b,c,{"expiry_days":.1,"optional_categories":.5,"consent_ratio":-1})
def impact_wayback_history(b,c): return _impact(IDS[9],"wayback_history",b,c,{"history_limit":.01,"timeout_seconds":.5,"retention_days":.1})
def _recover(fid,resource,current,snapshot,fields,allowed):
 if not isinstance(current,dict) or not isinstance(snapshot,dict) or not isinstance(fields,list): raise ValueError("Recuperación no válida")
 selected=[]
 for field in fields:
  if field not in allowed or field not in snapshot: raise ValueError(f"Campo no recuperable: {field}")
  if current.get(field)!=snapshot[field]: selected.append({"field":field,"before":copy.deepcopy(current.get(field)),"after":copy.deepcopy(snapshot[field])})
 return {"feature_id":fid,"resource":resource,"changes":selected,"preview":True,"requires_confirmation":True,"applied":False}
def recover_temporary_roles(c,s,f): return _recover(IDS[10],"temporary_roles",c,s,f,{"role","expires_at","scope"})
def recover_managed_groups(c,s,f): return _recover(IDS[11],"managed_groups",c,s,f,{"title","config","bot_ids"})
def recover_scheduled_messages(c,s,f): return _recover(IDS[12],"scheduled_messages",c,s,f,{"text","send_at","targets","status"})
def recover_rss_feeds(c,s,f): return _recover(IDS[13],"rss_feeds",c,s,f,{"url","filters","template","enabled"})
def recover_telegram_videos(c,s,f): return _recover(IDS[14],"telegram_videos",c,s,f,{"caption","metadata","status"})
def recover_blocklists(c,s,f): return _recover(IDS[15],"blocklists",c,s,f,{"enabled","entries","source"})
def recover_mandatory_subscriptions(c,s,f): return _recover(IDS[16],"mandatory_subscriptions",c,s,f,{"channels","enabled","grace_minutes"})
def recover_signed_webhooks(c,s,f): return _recover(IDS[17],"signed_webhooks",c,s,f,{"url","events","enabled","secret_version"})
def recover_quiet_hours(c,s,f): return _recover(IDS[18],"quiet_hours",c,s,f,{"timezone","start","end","exceptions","enabled"})
def recover_correlated_incidents(c,s,f): return _recover(IDS[19],"correlated_incidents",c,s,f,{"status","links","assignee","severity"})

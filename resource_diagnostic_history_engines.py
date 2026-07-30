"""Read-only diagnostics and historical comparisons for Moonbot resources."""
from resource_consent_diagnostic_engines import _diagnose

IDS=tuple(f"future-{n}" for n in (3722,3725,3728,3731,3734,3737,3740,3743,3746,3749,3752,3755,3758,3761,3764,3767,3770,3773,3776,3779))

def diagnose_managed_bots(o): return _diagnose(IDS[0],"managed_bots",o,("token_valid","owner_reachable","updates_flowing"))
def diagnose_recurring_reminders(o): return _diagnose(IDS[1],"recurring_reminders",o,("rrule_valid","timezone_valid","scheduler_reachable"))
def diagnose_security_events(o): return _diagnose(IDS[2],"security_events",o,("schema_valid","severity_valid","sink_reachable"))
def diagnose_regional_maps(o): return _diagnose(IDS[3],"regional_maps",o,("geometry_valid","privacy_radius_valid","tiles_reachable"))
def diagnose_backups(o): return _diagnose(IDS[4],"backups",o,("checksum_valid","restore_tested","storage_reachable"))
def diagnose_ai_learning_data(o): return _diagnose(IDS[5],"ai_learning_data",o,("consent_valid","schema_valid","provenance_present"))
def diagnose_rich_commands(o): return _diagnose(IDS[6],"rich_commands",o,("syntax_valid","payload_valid","handler_reachable"))
def diagnose_hub_notifications(o): return _diagnose(IDS[7],"hub_notifications",o,("recipient_valid","channel_reachable","delivery_tracked"))
def diagnose_cookie_policies(o): return _diagnose(IDS[8],"cookie_policies",o,("version_present","categories_valid","expiry_valid"))
def diagnose_wayback_history(o): return _diagnose(IDS[9],"wayback_history",o,("url_valid","snapshot_reachable","timestamp_valid"))

def _compare(fid,resource,before,after,identity="id"):
 if not isinstance(before,list) or not isinstance(after,list): raise ValueError("Historial no valido")
 def index(rows):
  out={}
  for row in rows:
   if not isinstance(row,dict) or identity not in row or not isinstance(row[identity],(str,int)): raise ValueError("Registro no valido")
   key=str(row[identity])
   if key in out: raise ValueError("Identidad duplicada")
   out[key]=row
  return out
 old,new=index(before),index(after); keys=sorted(set(old)|set(new))
 added=tuple(k for k in keys if k not in old); removed=tuple(k for k in keys if k not in new)
 changed={k:tuple(sorted(f for f in set(old[k])|set(new[k]) if f!=identity and old[k].get(f)!=new[k].get(f))) for k in keys if k in old and k in new}
 changed={k:v for k,v in changed.items() if v}
 return {"feature_id":fid,"resource":resource,"added":added,"removed":removed,"changed":changed,"change_count":len(added)+len(removed)+len(changed),"read_only":True,"auditable":True}

def compare_temporary_roles(a,b): return _compare(IDS[10],"temporary_roles",a,b)
def compare_managed_groups(a,b): return _compare(IDS[11],"managed_groups",a,b)
def compare_scheduled_messages(a,b): return _compare(IDS[12],"scheduled_messages",a,b)
def compare_rss_feeds(a,b): return _compare(IDS[13],"rss_feeds",a,b)
def compare_telegram_videos(a,b): return _compare(IDS[14],"telegram_videos",a,b)
def compare_blocklists(a,b): return _compare(IDS[15],"blocklists",a,b)
def compare_required_subscriptions(a,b): return _compare(IDS[16],"required_subscriptions",a,b)
def compare_signed_webhooks(a,b): return _compare(IDS[17],"signed_webhooks",a,b)
def compare_quiet_hours(a,b): return _compare(IDS[18],"quiet_hours",a,b)
def compare_correlated_incidents(a,b): return _compare(IDS[19],"correlated_incidents",a,b)

"""Safe automatic-test plans and immutable template composition for Moonbot."""
from copy import deepcopy
from resource_offline_autotest_engines import _autotest

IDS=tuple(f"future-{n}" for n in (4022,4025,4028,4031,4034,4037,4040,4043,4046,4049,4052,4055,4058,4061,4064,4067,4070,4073,4076,4079))

def autotest_managed_bots(f,c): return _autotest(IDS[0],"managed_bots",f,c)
def autotest_recurring_reminders(f,c): return _autotest(IDS[1],"recurring_reminders",f,c)
def autotest_security_events(f,c): return _autotest(IDS[2],"security_events",f,c)
def autotest_regional_maps(f,c): return _autotest(IDS[3],"regional_maps",f,c)
def autotest_backups(f,c): return _autotest(IDS[4],"backups",f,c)
def autotest_ai_learning_data(f,c): return _autotest(IDS[5],"ai_learning_data",f,c)
def autotest_rich_commands(f,c): return _autotest(IDS[6],"rich_commands",f,c)
def autotest_hub_notifications(f,c): return _autotest(IDS[7],"hub_notifications",f,c)
def autotest_cookie_policies(f,c): return _autotest(IDS[8],"cookie_policies",f,c)
def autotest_wayback_history(f,c): return _autotest(IDS[9],"wayback_history",f,c)

def _compose(fid,resource,layers):
 if not isinstance(layers,list) or not 1<=len(layers)<=50: raise ValueError("Capas no validas")
 reserved={"__class__","__dict__","__bases__","__proto__"}
 def merge(left,right,depth=0):
  if depth>10: raise ValueError("Plantilla demasiado profunda")
  if not isinstance(right,dict): raise ValueError("Capa no valida")
  out=deepcopy(left)
  for key,value in right.items():
   if not isinstance(key,str) or key in reserved: raise ValueError("Clave reservada")
   if isinstance(value,dict): out[key]=merge(out.get(key,{}) if isinstance(out.get(key),dict) else {},value,depth+1)
   elif isinstance(value,(str,int,float,bool,list,tuple,type(None))): out[key]=deepcopy(value)
   else: raise ValueError("Valor no valido")
  return out
 result={}
 for layer in layers: result=merge(result,layer)
 return {"feature_id":fid,"resource":resource,"template":result,"layer_count":len(layers),"immutable":True,"composable":True,"auditable":True}

def compose_temporary_roles(x): return _compose(IDS[10],"temporary_roles",x)
def compose_managed_groups(x): return _compose(IDS[11],"managed_groups",x)
def compose_scheduled_messages(x): return _compose(IDS[12],"scheduled_messages",x)
def compose_rss_feeds(x): return _compose(IDS[13],"rss_feeds",x)
def compose_telegram_videos(x): return _compose(IDS[14],"telegram_videos",x)
def compose_blocklists(x): return _compose(IDS[15],"blocklists",x)
def compose_required_subscriptions(x): return _compose(IDS[16],"required_subscriptions",x)
def compose_signed_webhooks(x): return _compose(IDS[17],"signed_webhooks",x)
def compose_quiet_hours(x): return _compose(IDS[18],"quiet_hours",x)
def compose_correlated_incidents(x): return _compose(IDS[19],"correlated_incidents",x)

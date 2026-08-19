"""Transactional imports and signed, minimized exports for Moonbot resources."""
import hashlib,hmac,json
from resource_version_import_engines import _import
IDS=tuple(f"future-{n}" for n in (3542,3545,3548,3551,3554,3557,3560,3563,3566,3569,3572,3575,3578,3581,3584,3587,3590,3593,3596,3599))
def import_master_panels(r): return _import(IDS[0],"master_panels",r,{"id","layout","role"},"id",{"layout":lambda x:isinstance(x,dict),"role":lambda x:x in ("admin","master")})
def import_channel_directories(r): return _import(IDS[1],"channel_directories",r,{"chat_id","title","category"},"chat_id",{"title":lambda x:isinstance(x,str) and 0<len(x)<=200,"category":lambda x:isinstance(x,str) and len(x)<=80})
def import_external_links(r): return _import(IDS[2],"external_links",r,{"id","url","verdict"},"id",{"url":lambda x:isinstance(x,str) and x.startswith(("http://","https://")),"verdict":lambda x:x in ("safe","unsafe","unknown")})
def _export(fid,resource,rows,fields,secret,redacted=()):
 if not isinstance(rows,list) or len(rows)>5000 or len(str(secret))<16: raise ValueError("Exportación no válida")
 payload=[]
 for row in rows:
  if not isinstance(row,dict): raise ValueError("Registro no válido")
  payload.append({field:("[REDACTED]" if field in redacted and row.get(field) is not None else row.get(field)) for field in fields})
 envelope={"feature_id":fid,"resource":resource,"records":payload,"count":len(payload),"algorithm":"HMAC-SHA256"}
 canonical=json.dumps(envelope,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode(); signature=hmac.new(str(secret).encode(),canonical,hashlib.sha256).hexdigest()
 return {"envelope":envelope,"signature":signature,"signed":True,"secret_included":False}
def export_admin_sessions(r,s): return _export(IDS[3],"admin_sessions",r,("id","actor_id","created_at","expires_at","mfa"),s)
def export_community_profiles(r,s): return _export(IDS[4],"community_profiles",r,("id","visibility","locale","email"),s,("email",))
def export_telegram_communities(r,s): return _export(IDS[5],"telegram_communities",r,("id","title","chat_ids","admin_count"),s)
def export_house_ads(r,s): return _export(IDS[6],"house_ads",r,("id","target","status","impressions","clicks"),s)
def export_voice_notes(r,s): return _export(IDS[7],"voice_notes",r,("id","duration","language","transcript"),s,("transcript",))
def export_suspicious_files(r,s): return _export(IDS[8],"suspicious_files",r,("sha256","size","verdict","source_path"),s,("source_path",))
def export_captcha_decisions(r,s): return _export(IDS[9],"captcha_decisions",r,("id","user_id","decision","evidence_count"),s,("user_id",))
def export_managed_bots(r,s): return _export(IDS[10],"managed_bots",r,("id","username","status","token"),s,("token",))
def export_recurring_reminders(r,s): return _export(IDS[11],"recurring_reminders",r,("id","rrule","timezone","recipient"),s,("recipient",))
def export_security_events(r,s): return _export(IDS[12],"security_events",r,("id","severity","occurred_at","evidence"),s,("evidence",))
def export_regional_maps(r,s): return _export(IDS[13],"regional_maps",r,("id","regions","privacy_radius_km","raw_coordinates"),s,("raw_coordinates",))
def export_backups(r,s): return _export(IDS[14],"backups",r,("id","checksum","verified","storage_secret"),s,("storage_secret",))
def export_ai_learning_data(r,s): return _export(IDS[15],"ai_learning_data",r,("id","sample_count","consented","raw_samples"),s,("raw_samples",))
def export_rich_commands(r,s): return _export(IDS[16],"rich_commands",r,("command","format","length","body"),s,("body",))
def export_hub_notifications(r,s): return _export(IDS[17],"hub_notifications",r,("id","priority","status","recipient"),s,("recipient",))
def export_cookie_policies(r,s): return _export(IDS[18],"cookie_policies",r,("version","categories","expiry_days","published_at"),s)
def export_wayback_history(r,s): return _export(IDS[19],"wayback_history",r,("url","snapshot_timestamp","available","requested_by"),s,("requested_by",))

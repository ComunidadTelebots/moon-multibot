import requests
import json
from moon_multibot import add_web_log

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin: WebArchive (Compatibilidad con Wayback Machine)
    Comandos:
    /wayback <url> : Recupera la última instantánea de la URL.
    /archive <url> : Guarda la URL actual en WebArchive.
    """
    t_lower = text.lower()
    
    settings = bot.db.get("GLOBAL_SETTINGS", {})
    if not settings.get("webarchive_enabled", True):
        return False
        
    if t_lower.startswith("/wayback "):
        url = text[9:].strip()
        if not url.startswith("http"):
            url = "http://" + url
            
        bot.send_msg(cid, f"⏳ Buscando instantáneas para: `{url}`...")
        
        try:
            r = requests.get(f"https://archive.org/wayback/available?url={url}", timeout=10)
            data = r.json()
            
            if data.get("archived_snapshots") and "closest" in data["archived_snapshots"]:
                closest = data["archived_snapshots"]["closest"]
                timestamp = closest["timestamp"]
                formatted_time = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}"
                snapshot_url = closest["url"]
                
                bot.send_msg(cid, f"🏛️ **WebArchive (Wayback Machine)**\n\n✅ Se encontró una versión del **{formatted_time}**:\n👉 [Ver Instantánea]({snapshot_url})", parse_mode="Markdown")
            else:
                bot.send_msg(cid, "❌ No se encontraron registros en el archivo para esta URL.")
                
            add_web_log("INFO", f"WebArchive consultado por {uid}")
            
        except Exception as e:
            bot.send_msg(cid, f"⚠️ Error contactando con Archive.org: {e}")
            
        return True
        
    if t_lower.startswith("/archive "):
        url = text[9:].strip()
        if not url.startswith("http"):
            url = "http://" + url
            
        save_url = f"https://web.archive.org/save/{url}"
        bot.send_msg(cid, f"💾 **Guardar en WebArchive**\n\nPara forzar el guardado de esta página ahora mismo, haz clic en el siguiente enlace:\n👉 [Guardar Instantánea]({save_url})", parse_mode="Markdown")
        return True

    return False

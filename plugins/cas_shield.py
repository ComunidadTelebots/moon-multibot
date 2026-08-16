from moon_multibot import add_web_log
import urllib.request
import json

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin de Escudo CAS (Combot Anti-Spam)
    Comprueba a los nuevos usuarios en la base de datos global de Combot.
    """
    # En un entorno real, esto se engancharía a "new_chat_members".
    # Dado que estamos usando parseo de texto por el momento, haremos la comprobación
    # on-the-fly para el usuario que hable (lo cual gasta un request, idealmente cacheado).
    
    # Comprobar si CAS está activado en los ajustes globales
    settings = bot.db.get("GLOBAL_SETTINGS", {})
    if not settings.get("cas_protection", False):
        return False
        
    # Verificar si el usuario ya fue cacheado como "limpio" en esta sesión/memoria
    # para no saturar la API en cada mensaje.
    cas_cache = bot.db.get("CAS_CACHE", {})
    user_id_str = str(uid)
    
    if user_id_str in cas_cache:
        # Ya comprobado, es limpio o fue baneado
        return False
        
    # Consultar API de CAS
    try:
        url = f"https://api.cas.chat/check?user_id={uid}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            
        if data.get("ok") and data.get("result"):
            # El usuario es un spammer conocido en Combot!
            bot.api_call("banChatMember", {"chat_id": cid, "user_id": uid})
            bot.send_msg(cid, f"🛡️ **CAS Shield Activado**\nEl usuario @{uid} ha sido expulsado inmediatamente porque figura en la base de datos global de spammers de Combot Anti-Spam.")
            add_web_log("WARNING", f"Usuario {uid} bloqueado por CAS en {cid}")
            return True # Detener procesamiento de este mensaje
            
        # Si llega aquí, está limpio
        cas_cache[user_id_str] = "clean"
        bot.db.set("CAS_CACHE", cas_cache)
            
    except Exception as e:
        # Fallo de conexión o timeout con CAS, permitir acceso por defecto
        pass

    return False

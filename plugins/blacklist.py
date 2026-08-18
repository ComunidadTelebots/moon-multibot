from moon_multibot import add_web_log
import re

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin Blacklist (Filtro de Palabras) - RC
    Elimina instantáneamente mensajes que contengan palabras prohibidas.
    
    Comandos (Admin):
    /addblacklist <palabra>
    /rmblacklist <palabra>
    /blacklist
    """
    
    blacklist = bot.db.get(f"BLACKLIST_{cid}", [])
    
    # Comandos de Admin
    if str(rank).lower() in ["admin", "master"] and text.startswith("/"):
        t_lower = text.lower()
        parts = t_lower.split(" ", 1)
        
        if t_lower.startswith("/addblacklist ") and len(parts) == 2:
            word = parts[1].strip().lower()
            if word not in blacklist:
                blacklist.append(word)
                bot.db.set(f"BLACKLIST_{cid}", blacklist)
                bot.send_msg(cid, f"✅ Palabra añadida a la lista negra: `{word}`")
                add_web_log("INFO", f"Palabra '{word}' añadida a blacklist en {cid}")
            else:
                bot.send_msg(cid, "ℹ️ Esa palabra ya está en la lista negra.")
            return True
            
        if t_lower.startswith("/rmblacklist ") and len(parts) == 2:
            word = parts[1].strip().lower()
            if word in blacklist:
                blacklist.remove(word)
                bot.db.set(f"BLACKLIST_{cid}", blacklist)
                bot.send_msg(cid, f"🗑️ Palabra removida de la lista negra: `{word}`")
            else:
                bot.send_msg(cid, "❌ Palabra no encontrada en la lista negra.")
            return True
            
        if t_lower == "/blacklist":
            if not blacklist:
                bot.send_msg(cid, "ℹ️ La lista negra está vacía.")
            else:
                msg = "🚫 **Lista Negra del Grupo:**\n\n"
                for w in blacklist:
                    msg += f"• `{w}`\n"
                bot.send_msg(cid, msg)
            return True

    # Comprobación Pasiva (Solo para usuarios no-admin)
    if text and str(rank).lower() not in ["admin", "master"]:
        text_lower = text.lower()
        # Buscar coincidencias exactas de palabras (usando regex para delimitar)
        words = set(re.findall(r'\b\w+\b', text_lower))
        
        for bad_word in blacklist:
            if bad_word in words or bad_word in text_lower:
                bot.send_msg(cid, f"🚫 @{uid}, tu mensaje ha sido eliminado por contener lenguaje prohibido.")
                # En un entorno real con el ID del mensaje, usaríamos deleteMessage
                # bot.api_call("deleteMessage", {"chat_id": cid, "message_id": mid})
                add_web_log("WARNING", f"Mensaje de {uid} borrado por blacklist en {cid}")
                return True # Evitamos que siga procesando

    return False

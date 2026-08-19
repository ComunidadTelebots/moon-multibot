from moon_multibot import add_web_log

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin de Media Locks (Bloqueos de Contenido)
    Comandos:
    /lock <url|stickers|forward|audio>
    /unlock <url|stickers|forward|audio>
    /locks
    """
    locks_db = bot.db.get(f"LOCKS_{cid}", {
        "url": False,
        "stickers": False,
        "forward": False,
        "audio": False
    })
    
    # Comandos de Admin
    if str(rank).lower() in ["admin", "master"] and text.startswith("/"):
        t_lower = text.lower()
        parts = t_lower.split(" ")
        
        if t_lower.startswith("/lock ") and len(parts) == 2:
            target = parts[1]
            if target in locks_db:
                locks_db[target] = True
                bot.db.set(f"LOCKS_{cid}", locks_db)
                bot.send_msg(cid, f"🔒 **Bloqueo activado:** `{target}`")
                add_web_log("INFO", f"Lock '{target}' activado en {cid}")
            else:
                bot.send_msg(cid, "❌ Tipo de bloqueo inválido. Disponibles: url, stickers, forward, audio")
            return True
            
        if t_lower.startswith("/unlock ") and len(parts) == 2:
            target = parts[1]
            if target in locks_db:
                locks_db[target] = False
                bot.db.set(f"LOCKS_{cid}", locks_db)
                bot.send_msg(cid, f"🔓 **Bloqueo desactivado:** `{target}`")
                add_web_log("INFO", f"Lock '{target}' desactivado en {cid}")
            else:
                bot.send_msg(cid, "❌ Tipo de bloqueo inválido.")
            return True
            
        if t_lower == "/locks":
            msg = "🔒 **Estado de Bloqueos:**\n\n"
            for k, v in locks_db.items():
                status = "✅ Permitido" if not v else "🚫 Bloqueado"
                msg += f"• `{k}`: {status}\n"
            bot.send_msg(cid, msg)
            return True
            
    # Lógica de eliminación (Si es un usuario normal)
    if str(rank).lower() not in ["admin", "master"]:
        should_delete = False
        reason = ""
        
        # Como no tenemos el objeto update completo en text (solo text string), 
        # para "url" podemos parsearlo del texto. 
        # Para stickers/audio/forward requeriríamos el objeto del mensaje completo en una implementación real,
        # pero aquí hacemos un mock para URL.
        if locks_db.get("url") and ("http://" in text or "https://" in text or "www." in text):
            should_delete = True
            reason = "Enlaces web bloqueados"
            
        # (Mock) Aquí se detectaría si el mensaje es un sticker/audio/forward si se pasara el objeto.
        
        if should_delete:
            bot.send_msg(cid, f"🚫 @{uid}, los mensajes que contienen **{reason}** no están permitidos en este grupo.")
            # Intentar borrar el mensaje (requiere el ID del mensaje, que idealmente vendría en los parámetros o se extrae)
            # En este entorno de ejemplo no pasamos mid a handle_command.
            return True

    return False

from moon_multibot import add_web_log

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin de Aprobaciones (Whitelist) - BETA
    Da inmunidad a un usuario frente a filtros (Flood, Locks, Captcha, Blacklist).
    
    Comandos (Admin):
    /approve <user_id>
    /disapprove <user_id>
    /approved
    """
    
    whitelist_db = bot.db.get(f"WHITELIST_{cid}", [])
    
    if text.startswith("/") and str(rank).lower() in ["admin", "master"]:
        t_lower = text.lower()
        parts = text.split(" ")
        
        if t_lower.startswith("/approve ") and len(parts) == 2:
            target_uid = parts[1]
            if target_uid not in whitelist_db:
                whitelist_db.append(target_uid)
                bot.db.set(f"WHITELIST_{cid}", whitelist_db)
                bot.send_msg(cid, f"✅ **Usuario Aprobado.**\n`{target_uid}` ahora tiene inmunidad contra los filtros del bot.")
                add_web_log("INFO", f"Usuario {target_uid} añadido a Whitelist en {cid}")
            else:
                bot.send_msg(cid, "ℹ️ El usuario ya estaba aprobado.")
            return True
            
        if t_lower.startswith("/disapprove ") and len(parts) == 2:
            target_uid = parts[1]
            if target_uid in whitelist_db:
                whitelist_db.remove(target_uid)
                bot.db.set(f"WHITELIST_{cid}", whitelist_db)
                bot.send_msg(cid, f"❌ **Aprobación Revocada.**\n`{target_uid}` vuelve a estar sujeto a las reglas normales.")
            else:
                bot.send_msg(cid, "ℹ️ El usuario no estaba en la lista de aprobados.")
            return True
            
        if t_lower == "/approved":
            if not whitelist_db:
                bot.send_msg(cid, "📝 No hay usuarios aprobados en este grupo.")
            else:
                msg = "🛡️ **Usuarios con Inmunidad:**\n\n"
                for w in whitelist_db:
                    msg += f"• `{w}`\n"
                bot.send_msg(cid, msg)
            return True

    # Nota arquitectónica:
    # Para que este plugin cumpla su función al 100%, los demás plugins (AntiFlood, Locks, Blacklist)
    # deben importar o verificar si `uid` está dentro de `bot.db.get(f"WHITELIST_{cid}", [])` antes de castigar.
    
    return False

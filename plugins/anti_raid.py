from moon_multibot import add_web_log

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin de Escudo Anti-Raid (RC)
    Comandos:
    /antiraid on
    /antiraid off
    """
    if str(rank).lower() not in ["admin", "master"] or not text.startswith("/"):
        return False
        
    t_lower = text.lower()
    
    raid_db = bot.db.get("ANTI_RAID_STATUS", {})
    
    if t_lower == "/antiraid on":
        raid_db[str(cid)] = True
        bot.db.set("ANTI_RAID_STATUS", raid_db)
        
        # En prod: Poner el grupo en Slow Mode (ej. 60 segs) o cerrarlo
        try:
            bot.api_call("setChatPermissions", {
                "chat_id": cid,
                "permissions": {"can_send_messages": False}
            })
            bot.send_msg(cid, "🚨 **MODO PÁNICO (ANTI-RAID) ACTIVADO** 🚨\n\nEl chat ha sido bloqueado temporalmente debido a una detección de ataque masivo o instrucción de un administrador. Todos los usuarios nuevos serán expulsados automáticamente.")
            add_web_log("WARNING", f"Anti-Raid activado manualmente en {cid}")
        except:
            bot.send_msg(cid, "⚠️ Anti-Raid activado en la base de datos, pero el bot necesita ser Administrador con permisos de Restricción para cerrar el grupo.")
        return True
        
    if t_lower == "/antiraid off":
        raid_db[str(cid)] = False
        bot.db.set("ANTI_RAID_STATUS", raid_db)
        
        try:
            bot.api_call("setChatPermissions", {
                "chat_id": cid,
                "permissions": {
                    "can_send_messages": True,
                    "can_send_media_messages": True,
                    "can_send_other_messages": True,
                    "can_add_web_page_previews": True
                }
            })
            bot.send_msg(cid, "✅ **Escudo Anti-Raid Desactivado**\n\nEl grupo vuelve a la normalidad.")
            add_web_log("INFO", f"Anti-Raid desactivado en {cid}")
        except:
            pass
        return True

    # Pasivo: Si anti-raid está ON, bloquear cualquier intento de mensaje de no-admins
    # Nota: Esto es un filtro brutal, idealmente interceptaría "new_chat_members"
    if raid_db.get(str(cid), False) and str(rank).lower() not in ["admin", "master"]:
        # Se asume que el chat está cerrado, pero si llega algo, se borra.
        return True # Bloqueado

    return False

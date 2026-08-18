from moon_multibot import add_web_log
from datetime import datetime, time

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin de Modo Nocturno (Night Mode) - ALFA
    Cierra el chat automáticamente durante la noche para evitar spam cuando no hay admins.
    
    Comandos:
    /nightmode <on/off>
    /setnight <hora_inicio> <hora_fin> (ej: /setnight 23:00 08:00)
    """
    
    # Comandos de configuración
    if str(rank).lower() in ["admin", "master"] and text.startswith("/"):
        t_lower = text.lower()
        parts = t_lower.split()
        
        settings = bot.db.get(f"NIGHTMODE_{cid}", {"enabled": False, "start": "23:00", "end": "08:00", "is_locked": False})
        
        if t_lower.startswith("/nightmode "):
            if len(parts) > 1:
                state = parts[1]
                if state == "on":
                    settings["enabled"] = True
                    bot.send_msg(cid, f"🌙 Modo nocturno activado. El grupo se silenciará entre las {settings['start']} y las {settings['end']}.")
                else:
                    settings["enabled"] = False
                    # Desbloquear si estaba bloqueado
                    if settings["is_locked"]:
                        _unlock_group(bot, cid)
                        settings["is_locked"] = False
                    bot.send_msg(cid, "☀️ Modo nocturno desactivado.")
                
                bot.db.set(f"NIGHTMODE_{cid}", settings)
                add_web_log("INFO", f"NightMode configurado a {settings['enabled']} en {cid}")
            return True
            
        if t_lower.startswith("/setnight "):
            if len(parts) == 3:
                settings["start"] = parts[1]
                settings["end"] = parts[2]
                bot.db.set(f"NIGHTMODE_{cid}", settings)
                bot.send_msg(cid, f"✅ Horario nocturno actualizado: {settings['start']} a {settings['end']}")
            else:
                bot.send_msg(cid, "❌ Uso: `/setnight HH:MM HH:MM` (ej: `/setnight 23:00 08:00`)")
            return True

    # Comprobación pasiva (Se ejecuta en cada mensaje si está activado)
    # Nota: Idealmente, esto se ejecutaría en un background worker (cron), 
    # pero como aproximación ALFA lo comprobamos on-message.
    settings = bot.db.get(f"NIGHTMODE_{cid}", {"enabled": False, "start": "23:00", "end": "08:00", "is_locked": False})
    
    if settings["enabled"]:
        now = datetime.now().time()
        start_time = datetime.strptime(settings["start"], "%H:%M").time()
        end_time = datetime.strptime(settings["end"], "%H:%M").time()
        
        is_night = False
        if start_time < end_time:
            is_night = start_time <= now <= end_time
        else: # Pasa por la medianoche
            is_night = now >= start_time or now <= end_time
            
        # Transiciones de estado
        if is_night and not settings["is_locked"]:
            _lock_group(bot, cid)
            settings["is_locked"] = True
            bot.db.set(f"NIGHTMODE_{cid}", settings)
            bot.send_msg(cid, "🌙 **Modo Nocturno Automático:** El grupo ha sido cerrado. ¡A dormir!")
            
        elif not is_night and settings["is_locked"]:
            _unlock_group(bot, cid)
            settings["is_locked"] = False
            bot.db.set(f"NIGHTMODE_{cid}", settings)
            bot.send_msg(cid, "☀️ **Buenos días:** El grupo ha sido reabierto automáticamente.")
            
        # Si es de noche y habla un usuario normal, borrar su mensaje.
        if is_night and str(rank).lower() not in ["admin", "master"]:
            # (El borrado requeriría el ID del mensaje)
            bot.send_msg(cid, f"🤫 @{uid}, el grupo está en Modo Nocturno. Por favor, vuelve mañana.")
            return True

    return False

def _lock_group(bot, cid):
    try:
        bot.api_call("setChatPermissions", {
            "chat_id": cid,
            "permissions": {"can_send_messages": False}
        })
    except:
        pass

def _unlock_group(bot, cid):
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
    except:
        pass

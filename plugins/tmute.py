from moon_multibot import add_web_log
import time
import threading

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin de Muteo Temporal (TMute) - ESTABLE
    Comandos:
    /mute <user_id>
    /unmute <user_id>
    /tmute <user_id> <horas>h
    """
    if str(rank).lower() not in ["admin", "master"] or not text.startswith("/"):
        return False
        
    t_lower = text.lower()
    parts = text.split()
    
    if t_lower.startswith("/mute "):
        if len(parts) >= 2:
            target_uid = parts[1]
            try:
                bot.api_call("restrictChatMember", {
                    "chat_id": cid,
                    "user_id": target_uid,
                    "permissions": {"can_send_messages": False}
                })
                bot.send_msg(cid, f"🔇 Usuario `{target_uid}` ha sido silenciado permanentemente.")
                add_web_log("INFO", f"Usuario {target_uid} silenciado en {cid}")
            except Exception as e:
                bot.send_msg(cid, f"❌ Error: {str(e)}")
        return True
        
    if t_lower.startswith("/unmute "):
        if len(parts) >= 2:
            target_uid = parts[1]
            try:
                bot.api_call("restrictChatMember", {
                    "chat_id": cid,
                    "user_id": target_uid,
                    "permissions": {
                        "can_send_messages": True,
                        "can_send_media_messages": True,
                        "can_send_other_messages": True,
                        "can_add_web_page_previews": True
                    }
                })
                bot.send_msg(cid, f"🔊 Usuario `{target_uid}` ya puede hablar de nuevo.")
                add_web_log("INFO", f"Usuario {target_uid} des-silenciado en {cid}")
            except Exception as e:
                bot.send_msg(cid, f"❌ Error: {str(e)}")
        return True
        
    if t_lower.startswith("/tmute "):
        if len(parts) >= 3:
            target_uid = parts[1]
            duration_str = parts[2]
            
            # Parsear duración básica (solo horas para simplificar)
            hours = 1
            if duration_str.endswith("h"):
                try:
                    hours = int(duration_str[:-1])
                except:
                    pass
            
            try:
                bot.api_call("restrictChatMember", {
                    "chat_id": cid,
                    "user_id": target_uid,
                    "permissions": {"can_send_messages": False}
                })
                bot.send_msg(cid, f"🔇 Usuario `{target_uid}` silenciado por {hours} hora(s).")
                
                # Lanzar thread para desmutear (En prod usaríamos TaskQueue o cron de DB)
                def unmute_later():
                    time.sleep(hours * 3600)
                    try:
                        bot.api_call("restrictChatMember", {
                            "chat_id": cid,
                            "user_id": target_uid,
                            "permissions": {
                                "can_send_messages": True,
                                "can_send_media_messages": True,
                                "can_send_other_messages": True,
                                "can_add_web_page_previews": True
                            }
                        })
                        bot.send_msg(cid, f"🔊 El castigo temporal ha terminado. `{target_uid}` ya puede hablar.")
                    except:
                        pass
                
                threading.Thread(target=unmute_later, daemon=True).start()
                add_web_log("INFO", f"Usuario {target_uid} tmuted ({hours}h) en {cid}")
            except Exception as e:
                bot.send_msg(cid, f"❌ Error: {str(e)}")
        return True

    return False

from moon_multibot import add_web_log
import random

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin Captcha
    Obliga a los nuevos usuarios a resolver un captcha matemático básico para poder hablar.
    """
    # En un bot real, esto se activaría al detectar un "new_chat_members" event.
    # Dado que el framework actual parsea texto plano, simularemos el comando /forcecaptcha para pruebas.
    
    t_lower = text.lower()
    
    if t_lower.startswith("/forcecaptcha ") and str(rank).lower() in ["admin", "master"]:
        parts = t_lower.split(" ")
        if len(parts) == 2:
            target_uid = parts[1]
            n1 = random.randint(1, 10)
            n2 = random.randint(1, 10)
            answer = n1 + n2
            
            # Guardar el captcha en la DB
            bot.db.set(f"CAPTCHA_{cid}_{target_uid}", answer)
            
            # Restringir usuario
            try:
                bot.api_call("restrictChatMember", {
                    "chat_id": cid,
                    "user_id": target_uid,
                    "permissions": {"can_send_messages": False}
                })
            except:
                pass
                
            bot.send_msg(cid, f"🤖 @{target_uid}, por favor verifica que eres humano resolviendo esto:\n\n**¿Cuánto es {n1} + {n2}?**\n\nResponde con el número para desbloquearte.")
        return True
        
    # Verificar si el usuario actual tiene un captcha pendiente
    expected_answer = bot.db.get(f"CAPTCHA_{cid}_{uid}")
    if expected_answer is not None:
        if text.strip() == str(expected_answer):
            # Resolver captcha
            bot.db.set(f"CAPTCHA_{cid}_{uid}", None)
            try:
                bot.api_call("restrictChatMember", {
                    "chat_id": cid,
                    "user_id": uid,
                    "permissions": {
                        "can_send_messages": True,
                        "can_send_media_messages": True,
                        "can_send_other_messages": True,
                        "can_add_web_page_previews": True
                    }
                })
                bot.send_msg(cid, f"✅ @{uid} ha verificado que es humano. ¡Bienvenido!")
                add_web_log("INFO", f"Usuario {uid} superó el captcha en {cid}")
            except:
                bot.send_msg(cid, "Error al restaurar permisos, un admin debe desbloquearte manualmente.")
        else:
            bot.send_msg(cid, f"❌ Respuesta incorrecta. Inténtalo de nuevo.")
        return True

    return False

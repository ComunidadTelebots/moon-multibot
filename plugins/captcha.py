from moon_multibot import add_web_log
import random
import json

def handle_command(bot, cid, uid, text, rank):
    t_lower = text.lower()
    
    # Force Captcha Command
    if t_lower.startswith("/forcecaptcha ") and str(rank).lower() in ["admin", "master"]:
        target_uid = text.split(" ")[1]
        settings = bot.db.get("GLOBAL_SETTINGS", {})
        fsub_channels = settings.get("fsub_channels", ["@todosobealltech"])
        
        bot.db.set(f"CAPTCHA_{cid}_{target_uid}", {"type": "fsub", "passed": False})
        
        # Restrict user
        try:
            bot.api_call("restrictChatMember", {"chat_id": cid, "user_id": target_uid, "permissions": {"can_send_messages": False}})
        except:
            pass
            
        # Generar teclado inline para unirse a los canales
        kb = []
        for ch in fsub_channels:
            url = f"https://t.me/{ch.replace('@', '')}"
            kb.append([{"text": f"🔗 Unirse a {ch}", "url": url}])
            
        kb.append([{"text": "✅ Ya me he unido", "callback_data": f"checkfsub_{target_uid}"}])
        
        bot.api_call("sendMessage", {
            "chat_id": cid,
            "text": f"🤖 @{target_uid}, para poder hablar en este grupo es **OBLIGATORIO** suscribirse a los siguientes canales globales:",
            "reply_markup": json.dumps({"inline_keyboard": kb})
        })
        return True
        
    # Validacion al hablar
    captcha_data = bot.db.get(f"CAPTCHA_{cid}_{uid}")
    if captcha_data and not captcha_data.get("passed"):
        bot.send_msg(cid, f"🚫 @{uid}, no puedes hablar hasta que completes el proceso de verificación arriba.")
        return True # Intercept and delete ideally

    return False

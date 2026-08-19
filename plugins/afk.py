from moon_multibot import add_web_log
import re

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin AFK (Away From Keyboard) - ESTABLE
    Los usuarios pueden marcarse como ausentes. Si son mencionados, el bot avisa.
    Si vuelven a hablar, se quita el estado AFK.
    
    Comandos:
    /afk [motivo]
    """
    
    afk_db = bot.db.get("GLOBAL_AFK", {})
    user_id = str(uid)
    
    # 1. Si el usuario escribe /afk
    if text.lower().startswith("/afk"):
        reason = text[4:].strip() or "Sin motivo"
        afk_db[user_id] = reason
        bot.db.set("GLOBAL_AFK", afk_db)
        bot.send_msg(cid, f"💤 @{uid} se ha puesto **AFK**.\nMotivo: _{reason}_")
        add_web_log("INFO", f"Usuario {uid} está AFK ({reason})")
        return True

    # 2. Si el usuario AFK vuelve a hablar, quitarle el AFK
    if user_id in afk_db and not text.lower().startswith("/afk"):
        del afk_db[user_id]
        bot.db.set("GLOBAL_AFK", afk_db)
        bot.send_msg(cid, f"👋 @{uid} ya no está AFK. ¡Bienvenido de vuelta!")
        # Seguimos procesando el mensaje por si hay triggers o warns

    # 3. Si se menciona a alguien que está AFK (por @alias o por ID si pudieramos extraerlo)
    # Como el texto plano a veces no resuelve el UID desde el alias, vamos a iterar 
    # por las menciones de alias si existieran en una base de datos local. 
    # Pero como forma básica, revisamos si el user_id o el alias (si lo tuvieramos) está en el mensaje.
    # Dado que solo tenemos el uid en la DB, asumimos que podríamos buscar si un ID numérico está en el texto 
    # o de alguna manera. En un bot real tendríamos el objeto "entities" de Telegram.
    
    # Como aproximación para el ecosistema actual, vamos a iterar la lista de AFK
    # y si el string del UID está explícitamente en el texto, avisamos.
    for afk_uid, reason in afk_db.items():
        if afk_uid != user_id and afk_uid in text:
            bot.send_msg(cid, f"😴 El usuario que mencionaste está AFK.\nMotivo: _{reason}_")
            return False # No bloqueamos, permitimos que otros plugins actuen

    return False

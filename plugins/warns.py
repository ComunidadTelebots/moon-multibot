from moon_multibot import add_web_log

WARN_LIMIT = 3

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin de Advertencias (Warns)
    Comandos:
    /warn <user_id o respondiendo> [motivo]
    /unwarn <user_id o respondiendo>
    /warns <user_id o respondiendo>
    """
    if str(rank).lower() not in ["admin", "master"]:
        # Solo procesar comandos si es admin
        if text.startswith("/warn ") or text.startswith("/unwarn ") or text.startswith("/warns "):
            bot.send_msg(cid, "❌ Este comando es exclusivo para administradores.")
            return True
        return False
        
    t_lower = text.lower()
    
    # Ayuda para parsear objetivo (simplificado)
    # En un sistema real extraeríamos el reply_to_message o el ID del texto.
    parts = text.split(" ", 2)
    
    if t_lower.startswith("/warn "):
        if len(parts) < 2:
            bot.send_msg(cid, "❌ Uso: `/warn <user_id> [motivo]`")
            return True
            
        target_uid = parts[1]
        reason = parts[2] if len(parts) > 2 else "Sin motivo"
        
        warns_db = bot.db.get(f"WARNS_{cid}_{target_uid}", {"count": 0, "reasons": []})
        warns_db["count"] += 1
        warns_db["reasons"].append(reason)
        bot.db.set(f"WARNS_{cid}_{target_uid}", warns_db)
        
        count = warns_db["count"]
        msg = f"⚠️ Usuario `{target_uid}` ha recibido una advertencia ({count}/{WARN_LIMIT}).\n📝 Motivo: {reason}"
        
        if count >= WARN_LIMIT:
            msg += "\n\n⛔ **Límite de advertencias alcanzado. Aplicando sanción (Ban).**"
            try:
                bot.api_call("banChatMember", {"chat_id": cid, "user_id": target_uid})
                add_web_log("WARNING", f"Usuario {target_uid} baneado por superar límite de warns en {cid}")
            except Exception as e:
                msg += f"\n❌ Error al banear: {str(e)}"
        
        bot.send_msg(cid, msg)
        return True
        
    if t_lower.startswith("/unwarn "):
        if len(parts) < 2:
            bot.send_msg(cid, "❌ Uso: `/unwarn <user_id>`")
            return True
            
        target_uid = parts[1]
        warns_db = bot.db.get(f"WARNS_{cid}_{target_uid}", {"count": 0, "reasons": []})
        
        if warns_db["count"] > 0:
            warns_db["count"] -= 1
            if warns_db["reasons"]:
                warns_db["reasons"].pop()
            bot.db.set(f"WARNS_{cid}_{target_uid}", warns_db)
            bot.send_msg(cid, f"✅ Se ha removido una advertencia al usuario `{target_uid}`. Tiene ({warns_db['count']}/{WARN_LIMIT}).")
        else:
            bot.send_msg(cid, f"ℹ️ El usuario `{target_uid}` no tiene advertencias.")
        return True
        
    if t_lower.startswith("/warns "):
        if len(parts) < 2:
            bot.send_msg(cid, "❌ Uso: `/warns <user_id>`")
            return True
            
        target_uid = parts[1]
        warns_db = bot.db.get(f"WARNS_{cid}_{target_uid}", {"count": 0, "reasons": []})
        
        msg = f"📋 **Advertencias de `{target_uid}`: {warns_db['count']}/{WARN_LIMIT}**\n\n"
        for i, reason in enumerate(warns_db["reasons"]):
            msg += f"• Warn {i+1}: {reason}\n"
            
        if warns_db["count"] == 0:
            msg += "✨ Historial limpio."
            
        bot.send_msg(cid, msg)
        return True

    return False

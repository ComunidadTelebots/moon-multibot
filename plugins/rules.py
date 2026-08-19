from moon_multibot import add_web_log

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin de Reglas del Grupo - ESTABLE
    
    Comandos:
    /rules
    /setrules <texto largo>
    /clearrules
    """
    
    t_lower = text.lower()
    
    if t_lower.startswith("/setrules ") and str(rank).lower() in ["admin", "master"]:
        rules_text = text[10:].strip()
        bot.db.set(f"RULES_{cid}", rules_text)
        bot.send_msg(cid, "✅ **Las normas del grupo han sido guardadas.**\nLos usuarios pueden leerlas usando `/rules`.")
        add_web_log("INFO", f"Reglas actualizadas en el chat {cid}")
        return True
        
    if t_lower == "/clearrules" and str(rank).lower() in ["admin", "master"]:
        bot.db.set(f"RULES_{cid}", None)
        bot.send_msg(cid, "🗑️ Las normas del grupo han sido eliminadas.")
        return True
        
    if t_lower == "/rules":
        rules_text = bot.db.get(f"RULES_{cid}")
        if not rules_text:
            bot.send_msg(cid, "ℹ️ Los administradores aún no han establecido normas para este grupo.")
        else:
            bot.send_msg(cid, f"📜 **Normas del Grupo:**\n\n{rules_text}\n\n_Por favor, respeta las reglas para mantener una buena convivencia._")
        return True

    return False

from moon_multibot import add_web_log

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin Lector RSS (BETA)
    Comandos (Admin):
    /addrss <url>
    /rmrss <url>
    /rsslist
    
    Nota: La publicación periódica se manejaría idealmente en un worker en el core.
    Aquí dejamos configurados los comandos de gestión.
    """
    
    if str(rank).lower() not in ["admin", "master"] or not text.startswith("/"):
        return False
        
    t_lower = text.lower()
    parts = text.split(" ")
    
    rss_db = bot.db.get(f"RSS_{cid}", [])
    
    if t_lower.startswith("/addrss ") and len(parts) == 2:
        url = parts[1].strip()
        if url not in rss_db:
            rss_db.append(url)
            bot.db.set(f"RSS_{cid}", rss_db)
            bot.send_msg(cid, f"📰 **Fuente RSS añadida:**\n`{url}`\n\nEl bot publicará automáticamente las nuevas entradas aquí.")
            add_web_log("INFO", f"Fuente RSS {url} añadida a {cid}")
        else:
            bot.send_msg(cid, "ℹ️ Esa fuente RSS ya estaba registrada.")
        return True
        
    if t_lower.startswith("/rmrss ") and len(parts) == 2:
        url = parts[1].strip()
        if url in rss_db:
            rss_db.remove(url)
            bot.db.set(f"RSS_{cid}", rss_db)
            bot.send_msg(cid, f"🗑️ **Fuente RSS eliminada:**\n`{url}`")
        else:
            bot.send_msg(cid, "❌ Fuente RSS no encontrada.")
        return True
        
    if t_lower == "/rsslist":
        if not rss_db:
            bot.send_msg(cid, "📭 No hay fuentes RSS configuradas en este grupo.")
        else:
            msg = "📡 **Fuentes RSS Activas:**\n\n"
            for url in rss_db:
                msg += f"• `{url}`\n"
            bot.send_msg(cid, msg)
        return True

    return False

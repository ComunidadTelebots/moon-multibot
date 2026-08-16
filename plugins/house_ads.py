from moon_multibot import add_web_log

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin de Anuncios Mutuos (House Ads) - ESTABLE
    Configura mensajes promocionales que se publicarán en el grupo y se auto-destruirán en 24h.
    
    Comandos (Admin):
    /addpromo <id> - <texto del anuncio>
    /rmpromo <id>
    /promolist
    """
    
    if str(rank).lower() not in ["admin", "master"] or not text.startswith("/"):
        return False
        
    t_lower = text.lower()
    parts = text.split(" ", 1)
    
    promos_db = bot.db.get(f"PROMOS_{cid}", {})
    
    if t_lower.startswith("/addpromo ") and len(parts) == 2:
        promo_data = parts[1].split("-", 1)
        if len(promo_data) == 2:
            promo_id = promo_data[0].strip().lower()
            promo_text = promo_data[1].strip()
            
            promos_db[promo_id] = promo_text
            bot.db.set(f"PROMOS_{cid}", promos_db)
            bot.send_msg(cid, f"🤝 **Anuncio Mutuo Añadido:** `{promo_id}`\n\nEl sistema lo publicará de forma programada y lo eliminará tras 24 horas.")
            add_web_log("INFO", f"Anuncio mutuo '{promo_id}' configurado en {cid}")
        else:
            bot.send_msg(cid, "❌ Uso: `/addpromo <id> - <texto del anuncio>`")
        return True
        
    if t_lower.startswith("/rmpromo ") and len(parts) == 2:
        promo_id = parts[1].strip().lower()
        if promo_id in promos_db:
            del promos_db[promo_id]
            bot.db.set(f"PROMOS_{cid}", promos_db)
            bot.send_msg(cid, f"🗑️ **Anuncio Mutuo Eliminado:** `{promo_id}`")
        else:
            bot.send_msg(cid, "❌ ID de anuncio no encontrado.")
        return True
        
    if t_lower == "/promolist":
        if not promos_db:
            bot.send_msg(cid, "📭 No hay anuncios mutuos configurados en este grupo.")
        else:
            msg = "🤝 **Anuncios Mutuos Activos:**\n\n"
            for pid, text in promos_db.items():
                msg += f"• `{pid}`: {text[:30]}...\n"
            bot.send_msg(cid, msg)
        return True

    return False

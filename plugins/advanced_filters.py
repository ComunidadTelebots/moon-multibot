import json
from moon_multibot import add_web_log

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin de Filtros Avanzados (BETA)
    Permite configurar filtros con botones Inline y Markdown avanzado.
    
    Comandos (Admin):
    /filter <palabra> - <texto>
    /filterbtn <palabra> - <texto_boton> - <url_boton>
    /delfilter <palabra>
    """
    
    if text.startswith("/") and str(rank).lower() in ["admin", "master"]:
        t_lower = text.lower()
        filters = bot.db.get(f"ADVFILTERS_{cid}", {})
        
        if t_lower.startswith("/filter "):
            parts = text[8:].split("-", 1)
            if len(parts) == 2:
                keyword = parts[0].strip().lower()
                response = parts[1].strip()
                
                filters[keyword] = {"type": "text", "text": response}
                bot.db.set(f"ADVFILTERS_{cid}", filters)
                bot.send_msg(cid, f"✅ Filtro avanzado añadido: `{keyword}`")
            return True
            
        if t_lower.startswith("/filterbtn "):
            parts = text[11:].split("-", 2)
            if len(parts) == 3:
                keyword = parts[0].strip().lower()
                btn_text = parts[1].strip()
                btn_url = parts[2].strip()
                
                filters[keyword] = {
                    "type": "button", 
                    "text": "Haz clic en el botón abajo:", 
                    "btn_text": btn_text,
                    "btn_url": btn_url
                }
                bot.db.set(f"ADVFILTERS_{cid}", filters)
                bot.send_msg(cid, f"✅ Filtro con botón añadido: `{keyword}`")
            return True
            
        if t_lower.startswith("/delfilter "):
            keyword = t_lower[11:].strip()
            if keyword in filters:
                del filters[keyword]
                bot.db.set(f"ADVFILTERS_{cid}", filters)
                bot.send_msg(cid, f"🗑️ Filtro eliminado: `{keyword}`")
            else:
                bot.send_msg(cid, "❌ Filtro no encontrado.")
            return True

    # Evaluación pasiva
    if text and not text.startswith("/"):
        filters = bot.db.get(f"ADVFILTERS_{cid}", {})
        text_lower = text.lower()
        
        for keyword, data in filters.items():
            if keyword in text_lower:
                if data["type"] == "text":
                    # Usar formato Markdown
                    bot.send_msg(cid, data["text"])
                elif data["type"] == "button":
                    # Botón Inline
                    keyboard = {
                        "inline_keyboard": [
                            [{"text": data["btn_text"], "url": data["btn_url"]}]
                        ]
                    }
                    try:
                        bot.api_call("sendMessage", {
                            "chat_id": cid,
                            "text": data["text"],
                            "reply_markup": json.dumps(keyboard)
                        })
                    except Exception as e:
                        bot.send_msg(cid, data["text"] + f"\n\n[🔗 {data['btn_text']}]({data['btn_url']})")
                return False # Permitir a otros procesar

    return False

from moon_multibot import add_web_log

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin Traductor Integrado (RC)
    Permite traducir mensajes. Idealmente usaría una API externa (DeepL/Google),
    o si estamos integrados con la IA Híbrida (ia_nativa), podemos pedirle a la IA
    que lo traduzca.
    
    Comandos:
    /tr <idioma> [texto]
    Si se usa como respuesta (reply), traduce el mensaje original.
    """
    t_lower = text.lower()
    
    if t_lower.startswith("/tr"):
        parts = text.split(" ", 2)
        lang = "es" # Español por defecto
        content_to_translate = ""
        
        if len(parts) >= 2:
            if len(parts[1]) == 2: # Ej: /tr en texto...
                lang = parts[1].lower()
                content_to_translate = parts[2] if len(parts) > 2 else ""
            else:
                content_to_translate = text[4:]
                
        # En un escenario real con el objeto de update, si no hay content_to_translate,
        # sacaríamos el texto del reply_to_message.
        
        if not content_to_translate:
            bot.send_msg(cid, "ℹ️ Usa `/tr [idioma] <texto>` o responde a un mensaje con `/tr [idioma]`.")
            return True
            
        bot.send_msg(cid, f"🌍 **Traducción ({lang}):**\n_(En Producción, este módulo enviará '{content_to_translate}' a la IA Nativa para traducir al idioma '{lang}')_")
        add_web_log("INFO", f"Comando /tr usado en {cid} a idioma {lang}")
        return True

    return False

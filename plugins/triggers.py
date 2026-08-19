import re
from moon_multibot import add_web_log

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin de Auto-Respuestas (Triggers)
    Detecta palabras clave en el mensaje y responde con un texto predefinido.
    Solo funciona si el plugin está activado y el trigger coincide.
    
    Comandos de Admin:
    /addtrigger <palabra> - <respuesta> : Añade un nuevo trigger
    /deltrigger <palabra> : Elimina un trigger
    /listtriggers : Lista todos los triggers configurados
    """
    
    # 1. Comandos de administración de triggers
    if text.startswith("/addtrigger ") and rank in ["master", "admin"]:
        parts = text[12:].split("-", 1)
        if len(parts) == 2:
            keyword = parts[0].strip().lower()
            response = parts[1].strip()
            
            # Guardar en DB
            triggers = bot.db.get(f"TRIGGERS_{cid}", {})
            triggers[keyword] = response
            bot.db.set(f"TRIGGERS_{cid}", triggers)
            
            bot.send_msg(cid, f"✅ Trigger añadido: `{keyword}` -> `{response}`")
            add_web_log("SUCCESS", f"Trigger '{keyword}' añadido en el chat {cid}")
        else:
            bot.send_msg(cid, "❌ Uso: `/addtrigger palabra - respuesta`")
        return True
        
    if text.startswith("/deltrigger ") and rank in ["master", "admin"]:
        keyword = text[12:].strip().lower()
        triggers = bot.db.get(f"TRIGGERS_{cid}", {})
        
        if keyword in triggers:
            del triggers[keyword]
            bot.db.set(f"TRIGGERS_{cid}", triggers)
            bot.send_msg(cid, f"🗑️ Trigger eliminado: `{keyword}`")
        else:
            bot.send_msg(cid, "❌ Trigger no encontrado.")
        return True
        
    if text == "/listtriggers" and rank in ["master", "admin"]:
        triggers = bot.db.get(f"TRIGGERS_{cid}", {})
        if not triggers:
            bot.send_msg(cid, "ℹ️ No hay triggers configurados en este chat.")
        else:
            msg = "📋 **Lista de Triggers:**\n\n"
            for k, v in triggers.items():
                msg += f"• `{k}` -> {v}\n"
            bot.send_msg(cid, msg)
        return True
        
    # 2. Evaluación de Triggers en mensajes normales
    if text and not text.startswith("/"):
        triggers = bot.db.get(f"TRIGGERS_{cid}", {})
        if triggers:
            text_lower = text.lower()
            # Búsqueda de palabra exacta
            words = set(re.findall(r'\b\w+\b', text_lower))
            for keyword, response in triggers.items():
                if keyword in words or keyword in text_lower:
                    # Enviar respuesta del trigger
                    bot.send_msg(cid, response)
                    # No retornamos True para permitir que otros plugins (ej. exp) sigan procesando
                    return False
                    
    return False

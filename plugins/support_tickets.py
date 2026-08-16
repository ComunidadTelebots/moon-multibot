from moon_multibot import add_web_log
import os

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin de Soporte
    Permite a los usuarios abrir un ticket de soporte enviando un mensaje privado al bot.
    El bot reenvía el mensaje al Master.
    
    Comandos:
    /ticket <mensaje> : Abre un ticket de soporte
    /replyticket <user_id> <mensaje> : Responde a un ticket (Solo Master)
    """
    
    MASTER_ID = os.getenv("MASTER_ID")
    
    # 1. Comando del usuario para abrir ticket
    if text.startswith("/ticket "):
        msg = text[8:].strip()
        if not msg:
            bot.send_msg(cid, "❌ Por favor, describe tu problema: `/ticket <mensaje>`")
            return True
            
        # Confirmar al usuario
        bot.send_msg(cid, "✅ Tu ticket ha sido enviado al equipo de soporte. Te responderemos por aquí lo antes posible.")
        
        # Enviar al Master
        if MASTER_ID:
            ticket_msg = f"🎫 **NUEVO TICKET DE SOPORTE** 🎫\n\n"
            ticket_msg += f"👤 **Usuario ID:** `{uid}`\n"
            ticket_msg += f"📝 **Mensaje:**\n{msg}\n\n"
            ticket_msg += f"💡 *Para responder usa:* `/replyticket {uid} tu mensaje`"
            bot.send_msg(MASTER_ID, ticket_msg)
            add_web_log("INFO", f"Nuevo ticket creado por usuario {uid}")
            
        return True
        
    # 2. Comando del Master para responder
    if text.startswith("/replyticket ") and rank == "master":
        parts = text[13:].strip().split(" ", 1)
        if len(parts) == 2:
            target_uid = parts[0].strip()
            reply_msg = parts[1].strip()
            
            # Enviar respuesta al usuario
            try:
                bot.send_msg(target_uid, f"👨‍💻 **Respuesta de Soporte:**\n\n{reply_msg}")
                bot.send_msg(cid, f"✅ Respuesta enviada al usuario `{target_uid}`")
                add_web_log("SUCCESS", f"Respuesta de ticket enviada al usuario {target_uid}")
            except Exception as e:
                bot.send_msg(cid, f"❌ Error al enviar mensaje: El usuario no ha iniciado el bot en privado o ha bloqueado al bot.")
        else:
            bot.send_msg(cid, "❌ Uso: `/replyticket <user_id> <mensaje>`")
            
        return True
        
    return False

import json
from moon_multibot import add_web_log

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin Constructor de Botones Inline (BETA)
    Comando: /buttonpost [Texto] | [Boton1 -> URL] | [Boton2 -> URL]
    """
    
    if str(rank).lower() not in ["admin", "master"] or not text.startswith("/"):
        return False
        
    t_lower = text.lower()
    
    if t_lower.startswith("/buttonpost "):
        raw = text[12:].strip()
        parts = raw.split("|")
        
        if len(parts) < 2:
            bot.send_msg(cid, "❌ Uso correcto: `/buttonpost Mensaje | Texto Boton -> https://...`")
            return True
            
        main_text = parts[0].strip()
        buttons_raw = parts[1:]
        
        keyboard = []
        
        for b in buttons_raw:
            if "->" in b:
                b_parts = b.split("->", 1)
                btn_text = b_parts[0].strip()
                btn_url = b_parts[1].strip()
                
                # Cada botón en una fila nueva
                keyboard.append([{"text": btn_text, "url": btn_url}])
                
        if not keyboard:
            bot.send_msg(cid, "❌ Ningún botón válido detectado. Formato: `Texto -> URL`")
            return True
            
        try:
            bot.api_call("sendMessage", {
                "chat_id": cid,
                "text": main_text,
                "reply_markup": json.dumps({"inline_keyboard": keyboard})
            })
            add_web_log("SUCCESS", f"Post con botones enviado a {cid}")
        except Exception as e:
            bot.send_msg(cid, f"❌ Error enviando mensaje con botones: {e}")
            
        return True

    return False

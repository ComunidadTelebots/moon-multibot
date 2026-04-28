import json
import os
from datetime import datetime

def handle_command(bot, cid, uid, text, rank):
    t_lower = text.lower()
    
    if t_lower == "/backup_db":
        if rank not in ["admin", "master"]:
            bot.send_msg(cid, "❌ Solo administradores pueden hacer backup.")
            return True
        
        try:
            # Exportar DB a JSON
            db_data = {}
            for key in ["IA_BRAIN", "CHAT_HISTORY", "GLOBAL_SETTINGS", "U_FILE", "CHANNELS"]:
                db_data[key] = bot.db.get(key, {})
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_{timestamp}.json"
            with open(f"data/{filename}", "w", encoding="utf-8") as f:
                json.dump(db_data, f, ensure_ascii=False, indent=2)
            
            bot.send_msg(cid, f"💾 **Backup Creado**: {filename}")
        except Exception as e:
            bot.send_msg(cid, f"❌ Error en backup: {str(e)}")
        
        return True
    
    elif t_lower.startswith("/restore_db"):
        if rank != "master":
            bot.send_msg(cid, "❌ Solo el master puede restaurar.")
            return True
        
        filename = text[12:].strip()
        if not filename:
            bot.send_msg(cid, "Uso: /restore_db <filename.json>")
            return True
        
        try:
            with open(f"data/{filename}", "r", encoding="utf-8") as f:
                db_data = json.load(f)
            
            for key, value in db_data.items():
                bot.db.set(key, value)
            
            bot.send_msg(cid, f"🔄 **Restauración Completada**: {filename}")
        except Exception as e:
            bot.send_msg(cid, f"❌ Error en restauración: {str(e)}")
        
        return True
    
    return False
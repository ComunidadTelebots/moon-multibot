from moon_multibot import add_web_log
import re

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin Filtro de Caracteres (ALFA)
    Detecta texto en cirílico, árabe o "Zalgo" corrupto, común en bots.
    """
    
    settings = bot.db.get("GLOBAL_SETTINGS", {})
    if not settings.get("char_filter_enabled", False):
        return False
        
    if str(rank).lower() in ["admin", "master"]:
        return False # Ignorar admins
        
    # Regex para Cirílico y Árabe
    cyrillic_pattern = re.compile(r'[\u0400-\u04FF\u0500-\u052F]')
    arabic_pattern = re.compile(r'[\u0600-\u06FF]')
    
    # Simple Zalgo detection (muchos diacríticos combinados)
    zalgo_pattern = re.compile(r'[\u0300-\u036F]{3,}')
    
    detected = False
    reason = ""
    
    if cyrillic_pattern.search(text):
        detected = True
        reason = "Cirílico"
    elif arabic_pattern.search(text):
        detected = True
        reason = "Árabe"
    elif zalgo_pattern.search(text):
        detected = True
        reason = "Zalgo/Corrupto"
        
    if detected:
        # En prod: borrar mensaje original y advertir o banear
        bot.send_msg(cid, f"🚫 **Filtro de Caracteres**\nEl mensaje del usuario `{uid}` ha sido bloqueado por contener texto detectado como: {reason}.")
        add_web_log("INFO", f"Mensaje bloqueado en {cid} por filtro de caracteres ({reason})")
        return True # Interceptado

    return False

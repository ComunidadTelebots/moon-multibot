import requests
import json
from moon_multibot import add_web_log

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin: Búsqueda Inteligente (Smart Search)
    Comandos:
    /search <query> : Busca un resumen en Wikipedia.
    /buscar <query> : Alias de search.
    """
    t_lower = text.lower()
    
    settings = bot.db.get("GLOBAL_SETTINGS", {})
    if not settings.get("smart_search_enabled", True):
        return False
        
    if t_lower.startswith("/search ") or t_lower.startswith("/buscar "):
        query = text.split(" ", 1)[1].strip()
        if not query:
            bot.send_msg(cid, "❌ Por favor, indica qué quieres buscar. Ejemplo: `/search Inteligencia Artificial`", parse_mode="Markdown")
            return True
            
        bot.send_msg(cid, f"🔍 Buscando información sobre: *{query}*...")
        
        try:
            # Buscar en Wikipedia en español usando la API
            url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(query)}"
            r = requests.get(url, headers={'User-Agent': 'MoonMultibot/16.0'}, timeout=10)
            
            if r.status_code == 200:
                data = r.json()
                title = data.get("title", query)
                extract = data.get("extract", "No hay resumen disponible.")
                page_url = data.get("content_urls", {}).get("desktop", {}).get("page", f"https://es.wikipedia.org/wiki/{query}")
                
                msg = f"📚 **Búsqueda: {title}**\n\n{extract}\n\n🔗 [Leer más en Wikipedia]({page_url})"
                bot.send_msg(cid, msg, parse_mode="Markdown", disable_web_page_preview=False)
            else:
                # Si no encuentra coincidencia exacta, usar la API de búsqueda abierta
                search_url = f"https://es.wikipedia.org/w/api.php?action=query&list=search&srsearch={requests.utils.quote(query)}&utf8=&format=json"
                r2 = requests.get(search_url, timeout=10)
                data2 = r2.json()
                
                if data2.get("query", {}).get("search"):
                    results = data2["query"]["search"]
                    top_result = results[0]["title"]
                    bot.send_msg(cid, f"⚠️ No encontré un artículo exacto, pero encontré:\n👉 **{top_result}**\nIntenta con: `/search {top_result}`", parse_mode="Markdown")
                else:
                    bot.send_msg(cid, f"❌ No se encontró ninguna información sobre *{query}*.", parse_mode="Markdown")
                    
            add_web_log("INFO", f"Búsqueda Inteligente ejecutada por {uid}: {query}")
            
        except Exception as e:
            bot.send_msg(cid, f"⚠️ Error en la búsqueda inteligente: {e}")
            
        return True

    return False

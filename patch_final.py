import re

with open("moon_multibot.py", "r", encoding="utf-8") as f:
    content = f.read()

# Buscamos el inicio del primer bloque "patch_bot_instances"
start_str = "def patch_bot_instances():"
idx = content.find(start_str)

if idx != -1:
    # Truncamos todo a partir de ahí
    content = content[:idx]

# Ahora añadimos la versión definitiva
patch = """def patch_bot_instances():
    for bot in active_bots:
        if getattr(bot, "_patched_for_router", False): continue
        bot._patched_for_router = True
        
        if not hasattr(bot, "router_queue"):
            bot.router_queue = queue.Queue()
            
        original_api_call = bot.api_call
        def patched_api_call(method, payload=None, files=None, timeout=None, silent=False):
            # En Sub-Bots, interceptamos getUpdates...
            if MOON_ENV != "stable" and method == "getUpdates":
                try:
                    update = bot.router_queue.get(timeout=10)
                    return {"ok": True, "result": [update]}
                except queue.Empty:
                    return {"ok": True, "result": []}
                    
            # En Sub-Bots, las demás llamadas a la API se envían al Stable
            if MOON_ENV != "stable" and method != "getUpdates":
                url = f"http://moonbot:5000/api/internal/tg/{method}"
                kwargs = {"headers": {"X-Bot-Token": bot.token}}
                if files:
                    kwargs["data"] = payload
                    kwargs["files"] = files
                else:
                    kwargs["json"] = payload
                try:
                    res = requests.post(url, timeout=timeout or 15, **kwargs)
                    return res.json()
                except Exception as e:
                    return {"ok": False, "description": str(e)}
            
            # En Stable, comportamiento normal, pero procesando reenvíos a sub-bots
            res = original_api_call(method, payload, files, timeout, silent)
            if MOON_ENV == "stable" and method == "getUpdates" and res.get("ok"):
                for item in res.get("result", []):
                    msg = item.get("message") or item.get("callback_query", {}).get("message")
                    if msg:
                        uid = msg.get("from", {}).get("id")
                        try:
                            from core.db import get_db
                            with get_db() as db_con:
                                row = db_con.execute("SELECT release_channels FROM users WHERE uid = ?", (uid,)).fetchone()
                                if row and row[0]:
                                    channels = [c.strip().lower() for c in row[0].split(",")]
                                    for target in ["alfa", "beta", "rc", "prealfa"]:
                                        if target in channels:
                                            try:
                                                requests.post(f"http://moonbot-{target}:5000/api/internal_update", json={"bot_token": bot.token, "update": item}, timeout=2)
                                            except: pass
                        except: pass
            return res
        bot.api_call = patched_api_call

def check_bots():
    if "active_bots" in globals() and active_bots:
        patch_bot_instances()
    threading.Timer(5.0, check_bots).start()
check_bots()
"""

content += patch

with open("moon_multibot.py", "w", encoding="utf-8") as f:
    f.write(content)

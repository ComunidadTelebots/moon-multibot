import re

with open("moon_multibot.py", "r", encoding="utf-8") as f:
    bot = f.read()

# We need to replace the entire patch_bot_instances block.
old_patch = """def patch_bot_instances():
    print(f"[DEBUG] Ejecutando patch_bot_instances. Bots activos: {len(active_bots)}", flush=True)
    for bot in active_bots:
        print(f"[DEBUG] Parcheando bot {bot.bot_username}. Ya parcheado: {getattr(bot, '_patched_for_router', False)}", flush=True)
        if getattr(bot, "_patched_for_router", False): continue

        bot._patched_for_router = True
        
        import queue
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
                    
            # En Sub-Bots, las dem\u00e1s llamadas a la API se env\u00edan al Stable
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
            
            # En Stable, comportamiento normal, pero procesando reenv\u00edos a sub-bots
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
        bot.api_call = patched_api_call"""

new_patch = """def patch_bot_instances():
    print(f"[DEBUG] Ejecutando patch_bot_instances. Bots activos: {len(active_bots)}", flush=True)
    for bot in active_bots:
        print(f"[DEBUG] Parcheando bot {bot.bot_username}. Ya parcheado: {getattr(bot, '_patched_for_router', False)}", flush=True)
        if getattr(bot, "_patched_for_router", False): continue

        bot._patched_for_router = True
        
        import queue
        if not hasattr(bot, "router_queue"):
            bot.router_queue = queue.Queue()
            
        original_api_call = bot.api_call
        def patched_api_call(m, p=None, silent=False):
            # En Sub-Bots, interceptamos getUpdates...
            if MOON_ENV != "stable" and m == "getUpdates":
                try:
                    update = bot.router_queue.get(timeout=10)
                    return {"ok": True, "result": [update]}
                except queue.Empty:
                    return {"ok": True, "result": []}
                    
            # En Sub-Bots, las dem\u00e1s llamadas a la API (JSON) se env\u00edan al Stable
            if MOON_ENV != "stable" and m != "getUpdates":
                url = f"http://moonbot:5000/api/internal/tg/{m}"
                kwargs = {"headers": {"X-Bot-Token": bot.token}}
                kwargs["json"] = p
                try:
                    res = requests.post(url, timeout=15, **kwargs)
                    return res.json()
                except Exception as e:
                    return {"ok": False, "description": str(e)}
            
            # En Stable, comportamiento normal, pero procesando reenv\u00edos a sub-bots
            res = original_api_call(m, p, silent)
            if MOON_ENV == "stable" and m == "getUpdates" and res.get("ok"):
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
        bot.api_call = patched_api_call"""

# Fallback: using regex to dynamically replace patched_api_call block
match = re.search(r'def patched_api_call\(method, payload=None, files=None, timeout=None, silent=False\):.*?bot\.api_call = patched_api_call', bot, re.DOTALL)
if match:
    bot = bot.replace(match.group(0), new_patch.split('original_api_call = bot.api_call\n')[1])
    with open("moon_multibot.py", "w", encoding="utf-8") as f:
        f.write(bot)
    print("Patch applied via Regex!")
elif old_patch in bot:
    bot = bot.replace(old_patch, new_patch)
    with open("moon_multibot.py", "w", encoding="utf-8") as f:
        f.write(bot)
    print("Patch applied via exact match!")
else:
    print("Could not find the patch block!")

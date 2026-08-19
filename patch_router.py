import re

with open("moon_multibot.py", "r", encoding="utf-8") as f:
    bot = f.read()

old_func = """        def patched_api_call(method, payload=None, files=None, timeout=None, silent=False):
            # En Sub-Bots, interceptamos getUpdates...
            if MOON_ENV != "stable" and method == "getUpdates":
                try:
                    update = bot.router_queue.get(timeout=10)
                    return {"ok": True, "result": [update]}
                except queue.Empty:
                    return {"ok": True, "result": []}
            
            # Llamada real para otros m\u00e9todos
            res = original_api_call(method, payload, files, timeout, silent)
            
            # Master Bot encola updates para el resto
            if MOON_ENV == "stable" and method == "getUpdates" and res.get("ok"):
                for item in res.get("result", []):
                    # Redirigir v\u00eda HTTP / internal
                    msg = item.get("message", item.get("edited_message", item.get("channel_post")))
                    if msg:
                        text = msg.get("text", msg.get("caption", ""))
                        if text:
                            text = text.lower()
                            targets = []
                            if any(w in text for w in ["ai", "ia", "bot"]): targets.append("ia")
                            if "spam" in text or "ban" in text: targets.append("moderation")
                            if "stats" in text: targets.append("stats")
                            for target in targets:
                                try:
                                    requests.post(f"http://moonbot-{target}:5000/api/internal_update", json={"bot_token": bot.token, "update": item}, timeout=2)
                                except: pass
                        except: pass
            return res"""

new_func = """        def patched_api_call(m, p=None, silent=False):
            # En Sub-Bots, interceptamos getUpdates...
            if MOON_ENV != "stable" and m == "getUpdates":
                try:
                    update = bot.router_queue.get(timeout=10)
                    return {"ok": True, "result": [update]}
                except queue.Empty:
                    return {"ok": True, "result": []}
            
            # Llamada real para otros m\u00e9todos
            res = original_api_call(m, p, silent)
            
            # Master Bot encola updates para el resto
            if MOON_ENV == "stable" and m == "getUpdates" and res.get("ok"):
                for item in res.get("result", []):
                    # Redirigir v\u00eda HTTP / internal
                    msg = item.get("message", item.get("edited_message", item.get("channel_post")))
                    if msg:
                        text = msg.get("text", msg.get("caption", ""))
                        if text:
                            text = text.lower()
                            targets = []
                            if any(w in text for w in ["ai", "ia", "bot"]): targets.append("ia")
                            if "spam" in text or "ban" in text: targets.append("moderation")
                            if "stats" in text: targets.append("stats")
                            for target in targets:
                                try:
                                    requests.post(f"http://moonbot-{target}:5000/api/internal_update", json={"bot_token": bot.token, "update": item}, timeout=2)
                                except: pass
            return res"""

if "patched_api_call(method, payload=None" in bot:
    bot = bot.replace(old_func, new_func)
    # Also there's a stray `except: pass` in the original source string without a try block, wait, the original source has it.
    with open("moon_multibot.py", "w", encoding="utf-8") as f:
        f.write(bot)
    print("Router loop crash patched successfully.")
else:
    print("Could not find patched_api_call")

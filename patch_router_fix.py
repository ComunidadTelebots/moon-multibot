with open("moon_multibot.py", "r", encoding="utf-8") as f:
    content = f.read()

idx = content.find("# === INICIO ROUTER PATCH ===")
if idx != -1:
    content = content[:idx]

router_patch = """# === INICIO ROUTER PATCH ===
import os
import requests
import threading
import time
import queue
from flask import request

MOON_ENV = os.getenv("MOON_ENV", "stable")
tg_out_queue = queue.Queue()

# Endpoint para que el Stable reciba llamadas salientes de Alfa/Beta y las encuele
@app.route("/api/internal/tg/<path:method>", methods=["POST"])
def internal_tg_proxy(method):
    if MOON_ENV != "stable": return "Not Stable", 400
    token = request.headers.get("X-Bot-Token")
    url = f"https://api.telegram.org/bot{token}/{method}"
    kwargs = {}
    if request.is_json: kwargs["json"] = request.json
    elif request.form: 
        kwargs["data"] = request.form.to_dict()
        if request.files:
            kwargs["files"] = {k: (v.filename, v.stream.read(), v.mimetype) for k, v in request.files.items()}
    tg_out_queue.put({"url": url, "kwargs": kwargs})
    return {"ok": True, "description": "Encolado en StableRouter"}

# Worker para llamadas salientes en el Stable
def tg_rate_limiter_worker():
    while True:
        try:
            task = tg_out_queue.get()
            requests.post(task["url"], timeout=10, **task["kwargs"])
            time.sleep(0.04)
        except Exception as e:
            pass

if MOON_ENV == "stable":
    threading.Thread(target=tg_rate_limiter_worker, daemon=True).start()

# Endpoint para que Alfa/Beta reciban updates del Stable
@app.route("/api/internal_update", methods=["POST"])
def internal_update():
    data = request.json
    if not data: return "OK", 200
    token = data.get("bot_token")
    item = data.get("update")
    for b in active_bots.values():
        if b.token == token:
            if not hasattr(b, "router_queue"):
                b.router_queue = queue.Queue()
            b.router_queue.put(item)
            break
    return "OK", 200

# Interceptores (Parche Dinámico)
def patch_bot_instances():
    for bot in active_bots.values():
        if getattr(bot, "_patched_for_router", False): continue
        bot._patched_for_router = True
        
        if not hasattr(bot, "router_queue"):
            bot.router_queue = queue.Queue()
            
        original_api_call = bot.api_call
        def patched_api_call(method, payload=None, files=None, timeout=None, silent=False):
            # En Sub-Bots, interceptamos getUpdates para que se quede esperando a que el Stable le envíe mensajes por HTTP
            if MOON_ENV != "stable" and method == "getUpdates":
                try:
                    update = bot.router_queue.get(timeout=10)
                    return {"ok": True, "result": [update]}
                except queue.Empty:
                    return {"ok": True, "result": []}
                    
            # En Sub-Bots, las demás llamadas a la API de Telegram se envían al Stable
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
            
            # En Stable, comportamiento normal
            return original_api_call(method, payload, files, timeout, silent)
        bot.api_call = patched_api_call

def check_bots():
    if "active_bots" in globals() and active_bots:
        patch_bot_instances()
    threading.Timer(5.0, check_bots).start()
check_bots()

# === FIN ROUTER PATCH ===
"""
content += router_patch

with open("moon_multibot.py", "w", encoding="utf-8") as f:
    f.write(content)

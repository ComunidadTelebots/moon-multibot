import re

with open("moon_multibot.py", "r", encoding="utf-8") as f:
    content = f.read()

patch_code = """def patch_bot_instances():
    print(f"[DEBUG] Ejecutando patch_bot_instances. Bots activos: {len(active_bots)}", flush=True)
    for bot in active_bots:
        print(f"[DEBUG] Parcheando bot {bot.bot_username}. Ya parcheado: {getattr(bot, '_patched_for_router', False)}", flush=True)
        if getattr(bot, "_patched_for_router", False): continue
"""

content = content.replace("""def patch_bot_instances():
    for bot in active_bots:
        if getattr(bot, "_patched_for_router", False): continue""", patch_code)

with open("moon_multibot.py", "w", encoding="utf-8") as f:
    f.write(content)

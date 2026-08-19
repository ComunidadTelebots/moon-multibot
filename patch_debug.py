with open("moon_multibot.py", "r", encoding="utf-8") as f:
    content = f.read()

debug_patch = """
        def patched_api_call(method, payload=None, files=None, timeout=None, silent=False):
            print(f"[DEBUG API CALL] ENV={MOON_ENV} method={method} payload={payload}", flush=True)
            # En Sub-Bots, interceptamos getUpdates...
"""

import re
content = re.sub(r'        def patched_api_call\(method, payload=None, files=None, timeout=None, silent=False\):\n            # En Sub-Bots, interceptamos getUpdates', debug_patch.strip("\n"), content)

with open("moon_multibot.py", "w", encoding="utf-8") as f:
    f.write(content)

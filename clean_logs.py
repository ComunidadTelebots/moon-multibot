import re

with open("moon_multibot.py", "r", encoding="utf-8") as f:
    bot = f.read()

# Delete noisy logs
noisy_logs = [
    r'if random.random\(\) < 0\.1:\s*add_web_log\("DEBUG", "Esperando nuevos mensajes de Telegram..."\)',
    r'add_web_log\("DEBUG", f"Nuevo mensaje detectado:.*?\"\)',
    r'add_web_log\("DEBUG", f"Deteccion de ID:.*?\"\)',
    r'add_web_log\("DEBUG", f"Procesando mensaje de.*?\"\)',
    r'add_web_log\("DEBUG", f"Webhook configurado para.*?\"\)'
]

for pattern in noisy_logs:
    bot = re.sub(pattern, '', bot)

with open("moon_multibot.py", "w", encoding="utf-8") as f:
    f.write(bot)

print("Noisy logs removed.")

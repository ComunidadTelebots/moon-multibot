import codecs
import re

with codecs.open("CHANGELOG.md", "r", "utf-8") as f:
    changelog = f.read()

# We want to append to the v18.26.15.16-alpha section.
# We can find the start of the next section `## [v` or the end of the current section.
# Since it's the top section, we can just insert before the first double line break after the bullet points, 
# or just look for the end of the "Correcci\u00f3n de Codificaci\u00f3n" line.

new_bullets = """
**Optimizaciones de Backend y Estabilidad (Silent Fixes)**
* **Crash Crítico del Router Resuelto:** Reparado un desajuste de argumentos (`patched_api_call` recibía 6 argumentos en vez de 4) que causaba el colapso silencioso del bucle de eventos cada 5 segundos.
* **Rotación de Logs (Prevención de Desbordamiento):** Implementado un sistema nativo para `data/bot.log` que archiva el historial automáticamente al alcanzar los 5MB, previniendo el consumo infinito de disco.
* **Limpieza de Verbose Debugging:** Eliminados los rastros excesivos de logging en el bucle principal ("Esperando nuevos mensajes", "Detección de ID") que saturaban la interfaz del dashboard y la memoria.
* **Purga de BOM UTF-8:** Eliminado un carácter invisible (`\\ufeff`) en la cabecera del archivo masivo `core/routes_public.py` que comprometía la compatibilidad del intérprete en entornos Linux/Docker."""

# Find the insertion point: right after the UTF-16/Encoding bullet.
insertion_marker = "(UTF-16)."
if insertion_marker in changelog:
    changelog = changelog.replace(insertion_marker, insertion_marker + "\n" + new_bullets)
else:
    # Fallback, just insert after the section header
    changelog = changelog.replace("## [v18.26.15.16-alpha] - 2026-08-19 (Fusión Arquitectónica de Interfaces)", 
                                  "## [v18.26.15.16-alpha] - 2026-08-19 (Fusión Arquitectónica y Estabilidad)\n" + new_bullets + "\n")

with codecs.open("CHANGELOG.md", "w", "utf-8") as f:
    f.write(changelog)

print("Changelog updated")

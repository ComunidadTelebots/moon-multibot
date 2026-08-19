import codecs

with codecs.open("CHANGELOG.md", "r", "utf-8") as f:
    changelog = f.read()

# First, remove it from the bottom
bad_block = """
**Arquitectura Multi-Canal (Micro-Repositorios)**
* **Enrutamiento por Base de Datos Restaurado:** Se reescribi\u00f3 el interceptor del router (`patched_api_call`) para restaurar la l\u00f3gica perdida en commits anteriores. Ahora el Master (stable) vuelve a consultar nativamente `SELECT release_channels FROM users` y redirige los eventos de Telegram a las instancias correspondientes (`alpha`, `beta`, `rc`) de forma transparente.
* **Aislamiento de Manifiestos:** Se escanearon y etiquetaron autom\u00e1ticamente **103 archivos de manifiesto** (`*manifest.py`) inyectando la propiedad `"release_channel": "alpha"`. Esto sella las fronteras del control de acceso y prepara el c\u00f3digo base para su divisi\u00f3n f\u00edsica en micro-repositorios sin p\u00e9rdida de compatibilidad.
"""
changelog = changelog.replace(bad_block, "")

# Now inject it into the proper place under v18.26.15.16-alpha
# We look for the "Purga de BOM UTF-8" line which is the last bullet of that section.
marker = "entornos Linux/Docker."
if marker in changelog:
    changelog = changelog.replace(marker, marker + "\n" + bad_block)

with codecs.open("CHANGELOG.md", "w", "utf-8") as f:
    f.write(changelog)

print("Changelog fixed and properly positioned.")

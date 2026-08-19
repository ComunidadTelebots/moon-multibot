import codecs

with codecs.open("CHANGELOG.md", "r", "utf-8") as f:
    changelog = f.read()

new_bullets = """
**Arquitectura Multi-Canal (Micro-Repositorios)**
* **Enrutamiento por Base de Datos Restaurado:** Se reescribió el interceptor del router (`patched_api_call`) para restaurar la lógica perdida en commits anteriores. Ahora el Master (stable) vuelve a consultar nativamente `SELECT release_channels FROM users` y redirige los eventos de Telegram a las instancias correspondientes (`alpha`, `beta`, `rc`) de forma transparente.
* **Aislamiento de Manifiestos:** Se escanearon y etiquetaron automáticamente **103 archivos de manifiesto** (`*manifest.py`) inyectando la propiedad `"release_channel": "alpha"`. Esto sella las fronteras del control de acceso y prepara el código base para su división física en micro-repositorios sin pérdida de compatibilidad.
"""

# Insert before "## [v18.25.15.15-alpha]"
insertion_point = "\n\n## [v18.25.15.15-alpha]"
if insertion_point in changelog:
    changelog = changelog.replace(insertion_point, "\n" + new_bullets + insertion_point)
else:
    # Append if something goes wrong
    changelog += new_bullets

with codecs.open("CHANGELOG.md", "w", "utf-8") as f:
    f.write(changelog)

print("Changelog updated.")

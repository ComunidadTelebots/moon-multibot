import os
import re

with open("CHANGELOG.md", "r", encoding="utf-8") as f:
    content = f.read()

build_section = """## [v18.25.15.15-alpha] - 2026-08-19 (Registro Diario de Builds)

**Build 15** (`b741135`): Desplazamiento del parche del router por encima del bucle infinito de Waitress para garantizar su ejecución.
**Build 14** (`f74bcf8`): Implementación de la herramienta de Ping directamente accesible desde el panel de administración.
**Build 13** (`f3d0100`): Resolución de error de sangría (indentation) y bloque try/except roto durante parcheo automatizado.
**Build 12** (`c06f15d`): Importación de la librería `queue` en el interceptor para prevenir un crash silencioso en el hilo del timer.
**Build 11** (`51f7eab`): Inyección de logs de diagnóstico profundos para auditar la correcta aplicación de los interceptores web.
**Build 10** (`6614582`): Unificación y limpieza arquitectónica de parches duplicados del router que causaban colisiones de concurrencia.
**Build 9** (`8eb5657`): Corrección del `AttributeError` originado al tratar `active_bots` como lista en lugar de diccionario.
**Build 8** (`6789416`): Eliminación crítica de carácter BOM (Byte Order Mark) UTF-8 invisible en la línea 2 que bloqueaba intérpretes.
**Build 7** (`16a1699`): Inclusión de importación faltante (`wraps` de `functools`) necesaria para los decoradores del router.
**Build 6** (`eeaf848`): Aumento de verbosidad con logs de debug avanzados en la función `api_call` hacia Telegram.
**Build 5** (`cf0c885`): Desactivación estratégica de réplicas en el bot estable para eliminar colisiones `409 Conflict` en la API de Telegram.
**Build 4** (`7f007e4`): Inclusión de un fallback robusto en el auto-escalador para calcular `system_cpu_usage` frente a discrepancias de la API de Docker.
**Build 3** (`7bd65d5`): Eliminación de errores de configuración en el sistema de réplicas asociado al motor de Ollama.
**Build 2** (`4a91a8f`): Implementación nuclear del Auto-escalador, colas de Webhooks y correcciones masivas en el Central Router.
**Build 1** (`ac9708a`): Reparación de la autenticación de testers y forzado del establecimiento de la cookie `hub_session` adaptada a subdominios cruzados.

"""

content = re.sub(
    r"## \[v18\.25\.15\.17-alpha\].*?(?=\*\*18 de Agosto de 2026\*\*|\Z)", 
    build_section, 
    content, 
    flags=re.DOTALL
)

with open("CHANGELOG.md", "w", encoding="utf-8", newline="\n") as f:
    f.write(content)


import os

with open("CHANGELOG.md", "r", encoding="utf-8") as f:
    content = f.read()

new_section = """## [v18.25.15-alpha] - 2026-08-19
### Feature - Arquitectura y Optimizaciones Multi-Entorno

**19 de Agosto de 2026**
- **Auto-escalador Docker (Autoscaler)**: Sistema automático de escalado de réplicas en función de la carga de CPU, integrando un fallback robusto en la API de Docker y eliminación de conflictos en réplicas de Ollama.
- **Gestión de Recursos y Conflictos**: Desactivación inteligente de réplicas de contenedores en bots estables para evitar errores `409 Conflict` en Telegram API.
- **Estabilización de Enrutador Central**: Resolución de colisiones por hilos concurrentes, unificación de parches duplicados en Waitress e implementación segura de interceptores con colas.
- **Seguridad y Panel de Administración**: Nueva herramienta de ping desde el dashboard, reparación del sistema de autenticación de testers (cookie `hub_session` para subdominios).
- **Compatibilidad Linux**: Corrección crítica de bugs de codificación (caracteres BOM invisibles, UTF-8 en `moon_multibot.py`).

**18 de Agosto de 2026**
- **Arquitectura Docker Multi-Entorno**: Soporte nativo en `docker-compose` para entornos (alfa, beta, rc, estable) aislando puertos y redes (Traefik ext), con regeneración segura de YAML sin perfiles conflictivos.
- **Central Webhook Router**: Nuevo enrutador central de webhooks con limitador de tasa global (Rate Limiter) y suspensión dinámica de hilos secundarios en entornos no estables.
- **UI del Hub**: Insignias visuales (badges) dinámicas que muestran el estado y versión actual (Alfa/Beta/RC/Estable) con selector y limitación por `release channel`.

"""

# Reemplazar la seccion anterior que no tenia fechas
import re
content = re.sub(
    r"## \[v18\.25\.15-alpha\].*?(?=\n## |\Z)", 
    new_section, 
    content, 
    flags=re.DOTALL
)

with open("CHANGELOG.md", "w", encoding="utf-8", newline="\n") as f:
    f.write(content)


import os

with open("CHANGELOG.md", "r", encoding="utf-8") as f:
    content = f.read()

new_section = """## [v18.25.15-alpha] - 2026-08-19
### Feature - Arquitectura y Optimizaciones Multi-Entorno
- **Arquitectura Docker Multi-Entorno**: Soporte nativo en `docker-compose` para entornos (alfa, beta, rc, estable) aislando puertos y dominios, con limpieza de caracteres BOM/UTF-8 para evitar bloqueos en Linux.
- **Central Webhook Router**: Nuevo enrutador central de webhooks con interceptores, limitador de tasa global (Rate Limiter) y colas seguras que resuelve colisiones entre instancias.
- **Auto-escalador Docker (Autoscaler)**: Sistema automático de escalado de réplicas en función de la carga de CPU, integrando un fallback robusto en la API de Docker.
- **Gestión de Recursos y Conflictos**: Desactivación inteligente de réplicas de contenedores en bots estables para evitar errores `409 Conflict` en Telegram API, y suspensión de hilos secundarios (ollama, etc.) en entornos experimentales.
- **Seguridad y Panel de Administración**: Nueva herramienta de ping desde el dashboard, reparación del sistema de autenticación de testers (cookie `hub_session` para subdominios), y protección de excepciones en hilos asíncronos.
- **UI del Hub**: Insignias visuales (badges) dinámicas que muestran el estado y versión actual (Alfa/Beta/RC/Estable) con un selector interactivo.

"""

# Insert after "# Changelog - Moon Multibot"
lines = content.split('\n')
if len(lines) > 0 and "Changelog" in lines[0]:
    content = lines[0] + '\n\n' + new_section + '\n'.join(lines[1:]).lstrip()

with open("CHANGELOG.md", "w", encoding="utf-8", newline="\n") as f:
    f.write(content)


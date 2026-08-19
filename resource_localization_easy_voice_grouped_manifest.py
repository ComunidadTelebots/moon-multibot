"""Complete manifest for Moonbot future-5042..future-5159."""

from resource_localization_easy_reading_engines import ALL_APIS as FIRST_APIS
from resource_localization_easy_reading_engines import IDS as FIRST_IDS
from resource_voice_grouped_notification_engines import ALL_APIS as SECOND_APIS
from resource_voice_grouped_notification_engines import IDS as SECOND_IDS


TITLES = (
    "Localización cultural de paneles del master en Moonbot",
    "Localización cultural de directorios de canales en Moonbot",
    "Localización cultural de enlaces externos en Moonbot",
    "Lectura fácil para sesiones administrativas en Moonbot",
    "Lectura fácil para perfiles comunitarios en Moonbot",
    "Lectura fácil para comunidades Telegram en Moonbot",
    "Lectura fácil para anuncios propios en Moonbot",
    "Lectura fácil para notas de voz en Moonbot",
    "Lectura fácil para archivos sospechosos en Moonbot",
    "Lectura fácil para decisiones de captcha en Moonbot",
    "Lectura fácil para bots administrados en Moonbot",
    "Lectura fácil para recordatorios recurrentes en Moonbot",
    "Lectura fácil para eventos de seguridad en Moonbot",
    "Lectura fácil para mapas regionales en Moonbot",
    "Lectura fácil para copias de seguridad en Moonbot",
    "Lectura fácil para datos de aprendizaje IA en Moonbot",
    "Lectura fácil para comandos enriquecidos en Moonbot",
    "Lectura fácil para notificaciones del Hub en Moonbot",
    "Lectura fácil para políticas de cookies en Moonbot",
    "Lectura fácil para historial Wayback en Moonbot",
    "Navegación por voz de roles temporales en Moonbot",
    "Navegación por voz de grupos administrados en Moonbot",
    "Navegación por voz de mensajes programados en Moonbot",
    "Navegación por voz de feeds RSS en Moonbot",
    "Navegación por voz de vídeos de Telegram en Moonbot",
    "Navegación por voz de listas de bloqueo en Moonbot",
    "Navegación por voz de suscripciones obligatorias en Moonbot",
    "Navegación por voz de webhooks firmados en Moonbot",
    "Navegación por voz de horarios silenciosos en Moonbot",
    "Navegación por voz de incidentes correlacionados en Moonbot",
    "Navegación por voz de preferencias accesibles en Moonbot",
    "Navegación por voz de secretos de integración en Moonbot",
    "Navegación por voz de respuestas contextuales en Moonbot",
    "Navegación por voz de menús de la MiniApp en Moonbot",
    "Navegación por voz de estadísticas por bot en Moonbot",
    "Navegación por voz de preferencias publicitarias en Moonbot",
    "Navegación por voz de colas de procesamiento en Moonbot",
    "Notificación agrupada de cuentas creadoras en Moonbot",
    "Notificación agrupada de canales asociados en Moonbot",
    "Notificación agrupada de campañas comunitarias en Moonbot",
)

IDS = FIRST_IDS + SECOND_IDS
APIS = FIRST_APIS + SECOND_APIS
CAPABILITIES = tuple(title.removesuffix(" en Moonbot") for title in TITLES)
PREFLIGHT = (
    "No existe localización cultural tipada de este recurso; universal_i18n solo traduce cadenas."
    if index < 3 else
    "easy_read genérico solo separa frases; falta estructura por recurso, glosario, límites e identificadores preservados."
    if index < 20 else
    "voice_navigation genérico reconoce cuatro rutas; falta gramática cerrada por recurso, objetivo y confirmación segura."
    if index < 37 else
    "Las agrupaciones existentes son de panel web; falta deduplicación Moonbot por entidad, tipo y ventana temporal."
    for index in range(40)
)
MODULES = (
    ("resource_localization_easy_reading_engines.py",) * 20
    + ("resource_voice_grouped_notification_engines.py",) * 20
)

MANIFEST = tuple(
    {"release_channel": "beta", "id": feature_id,
        "title": title,
        "capability": capability,
        "module": module,
        "api": operation.__name__,
        "test": f"tests/test_resource_localization_easy_voice_grouped.py::test_{feature_id.replace('-', '_')}",
        "preflight": preflight,
    }
    for feature_id, title, capability, module, operation, preflight in zip(
        IDS, TITLES, CAPABILITIES, MODULES, APIS, PREFLIGHT
    )
)

assert len(MANIFEST) == 40
assert len({entry["id"] for entry in MANIFEST}) == 40
assert len({entry["title"] for entry in MANIFEST}) == 40
assert len({entry["capability"] for entry in MANIFEST}) == 40
assert len({entry["api"] for entry in MANIFEST}) == 40

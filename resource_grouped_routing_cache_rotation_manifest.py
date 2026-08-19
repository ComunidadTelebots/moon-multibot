"""Complete 60-entry manifest for Moonbot future-5162..future-5339."""

from resource_cache_rotation_engines import ALL_APIS as CACHE_ROTATION_APIS
from resource_cache_rotation_engines import IDS as CACHE_ROTATION_IDS
from resource_grouped_routing_engines import ALL_APIS as GROUP_ROUTE_APIS
from resource_grouped_routing_engines import IDS as GROUP_ROUTE_IDS


GROUP_LABELS = (
    "artículos editoriales", "imágenes moderadas", "apelaciones de usuarios",
    "proxies MTProto", "tareas persistentes", "reglas de moderación",
    "métricas lingüísticas", "traducciones comunitarias", "consentimientos personales",
    "reacciones Telegram", "paneles del master", "directorios de canales", "enlaces externos",
)
ROUTE_LABELS = (
    "sesiones administrativas", "perfiles comunitarios", "comunidades Telegram",
    "anuncios propios", "notas de voz", "archivos sospechosos", "decisiones de captcha",
    "bots administrados", "recordatorios recurrentes", "eventos de seguridad",
    "mapas regionales", "copias de seguridad", "datos de aprendizaje IA",
    "comandos enriquecidos", "notificaciones del Hub", "políticas de cookies",
    "historial Wayback",
)
CACHE_LABELS = (
    "roles temporales", "grupos administrados", "mensajes programados", "feeds RSS",
    "vídeos de Telegram", "listas de bloqueo", "suscripciones obligatorias",
    "webhooks firmados", "horarios silenciosos", "incidentes correlacionados",
    "preferencias accesibles", "secretos de integración", "respuestas contextuales",
    "menús de la MiniApp", "estadísticas por bot", "preferencias publicitarias",
    "colas de procesamiento",
)
ROTATION_LABELS = (
    "cuentas creadoras", "canales asociados", "campañas comunitarias",
    "artículos editoriales", "imágenes moderadas", "apelaciones de usuarios",
    "proxies MTProto", "tareas persistentes", "reglas de moderación",
    "métricas lingüísticas", "traducciones comunitarias", "consentimientos personales",
    "reacciones Telegram",
)

TITLES = tuple(
    [f"Notificación agrupada de {label} en Moonbot" for label in GROUP_LABELS]
    + [f"Enrutamiento inteligente de {label} en Moonbot" for label in ROUTE_LABELS]
    + [f"Caché reconciliable de {label} en Moonbot" for label in CACHE_LABELS]
    + [f"Rotación segura de {label} en Moonbot" for label in ROTATION_LABELS]
)
CAPABILITIES = tuple(title.removesuffix(" en Moonbot") for title in TITLES)
IDS = GROUP_ROUTE_IDS + CACHE_ROTATION_IDS
APIS = GROUP_ROUTE_APIS + CACHE_ROTATION_APIS
MODULES = (
    ("resource_grouped_routing_engines.py",) * 30
    + ("resource_cache_rotation_engines.py",) * 30
)


def _preflight(index, feature_id, api):
    if index < 13:
        nearest = "group_notifications cubre otros recursos; no existe esta entidad/tipos/ID"
    elif index < 30:
        nearest = "no existe router con skill, clearance, región, capacidad y autorización"
    elif index < 47:
        nearest = "reconcile existente no implementa caché con etag/version/conflicto/TTL"
    else:
        nearest = "rotaciones existentes no ofrecen fases, health gate, gracia y rollback para este recurso"
    return f"repo_scan_before:{feature_id}/{api}: ID, API y capacidad exactos ausentes; {nearest}."


def _roles(index, operation):
    resource = operation.__name__.removeprefix("group_").removesuffix("_notifications")
    if index < 13:
        scope = f"notifications:group:{resource}"
    elif index < 30:
        resource = operation.__name__.removeprefix("route_").removesuffix("_intelligently")
        scope = f"route:plan:{resource}"
    elif index < 47:
        resource = operation.__name__.removeprefix("reconcile_").removesuffix("_cache")
        scope = f"cache:reconcile:{resource}"
    else:
        resource = operation.__name__.removeprefix("plan_safe_").removesuffix("_rotation")
        scope = f"rotation:plan:{resource}"
    return ("master", f"scope:{scope}")


MANIFEST = tuple(
    {"release_channel": "prealfa", "id": feature_id,
        "title": title,
        "capability": capability,
        "module": module,
        "api": operation.__name__,
        "test": f"tests/test_resource_grouped_routing_cache_rotation.py::test_{feature_id.replace('-', '_')}",
        "preflight": _preflight(index, feature_id, operation.__name__),
        "roles": _roles(index, operation),
    }
    for index, (feature_id, title, capability, module, operation) in enumerate(
        zip(IDS, TITLES, CAPABILITIES, MODULES, APIS)
    )
)

assert len(MANIFEST) == 60
assert len({entry["id"] for entry in MANIFEST}) == 60
assert len({entry["title"] for entry in MANIFEST}) == 60
assert len({entry["capability"] for entry in MANIFEST}) == 60
assert len({entry["api"] for entry in MANIFEST}) == 60

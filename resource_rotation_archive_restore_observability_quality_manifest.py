"""Complete 60-entry manifest for Moonbot future-5342..future-5519."""

from resource_observability_quality_engines import ALL_APIS as OBS_QUALITY_APIS
from resource_observability_quality_engines import IDS as OBS_QUALITY_IDS
from resource_rotation_archive_restore_engines import ALL_APIS as ROT_ARCHIVE_RESTORE_APIS
from resource_rotation_archive_restore_engines import IDS as ROT_ARCHIVE_RESTORE_IDS


ROTATION_LABELS = ("paneles del master", "directorios de canales", "enlaces externos")
ARCHIVE_LABELS = (
    "sesiones administrativas", "perfiles comunitarios", "comunidades Telegram",
    "anuncios propios", "notas de voz", "archivos sospechosos", "decisiones de captcha",
    "bots administrados", "recordatorios recurrentes", "eventos de seguridad",
    "mapas regionales", "copias de seguridad", "datos de aprendizaje IA",
    "comandos enriquecidos", "notificaciones del Hub", "políticas de cookies", "historial Wayback",
)
RESTORE_LABELS = (
    "roles temporales", "grupos administrados", "mensajes programados", "feeds RSS",
    "vídeos de Telegram", "listas de bloqueo", "suscripciones obligatorias",
    "webhooks firmados", "horarios silenciosos", "incidentes correlacionados",
    "preferencias accesibles", "secretos de integración", "respuestas contextuales",
    "menús de la MiniApp", "estadísticas por bot", "preferencias publicitarias", "colas de procesamiento",
)
OBS_LABELS = (
    "cuentas creadoras", "canales asociados", "campañas comunitarias", "artículos editoriales",
    "imágenes moderadas", "apelaciones de usuarios", "proxies MTProto", "tareas persistentes",
    "reglas de moderación", "métricas lingüísticas", "traducciones comunitarias",
    "consentimientos personales", "reacciones Telegram", "paneles del master",
    "directorios de canales", "enlaces externos",
)
QUALITY_LABELS = (
    "sesiones administrativas", "perfiles comunitarios", "comunidades Telegram",
    "anuncios propios", "notas de voz", "archivos sospechosos", "decisiones de captcha",
)

TITLES = tuple(
    [f"Rotación segura de {label} en Moonbot" for label in ROTATION_LABELS]
    + [f"Archivado programado de {label} en Moonbot" for label in ARCHIVE_LABELS]
    + [f"Restauración por punto temporal de {label} en Moonbot" for label in RESTORE_LABELS]
    + [f"Observabilidad distribuida de {label} en Moonbot" for label in OBS_LABELS]
    + [f"Control de calidad para {label} en Moonbot" for label in QUALITY_LABELS]
)
CAPABILITIES = tuple(title.removesuffix(" en Moonbot") for title in TITLES)
IDS = ROT_ARCHIVE_RESTORE_IDS + OBS_QUALITY_IDS
APIS = ROT_ARCHIVE_RESTORE_APIS + OBS_QUALITY_APIS
MODULES = (
    ("resource_rotation_archive_restore_engines.py",) * 37
    + ("resource_observability_quality_engines.py",) * 23
)


def _family(index):
    if index < 3: return "rotation:plan"
    if index < 20: return "archive:plan"
    if index < 37: return "restore:plan"
    if index < 53: return "observability:read"
    return "quality:review"


def _preflight(index, feature_id, api):
    nearest = (
        "rotación previa cubre otros recursos; falta este artefacto"
        if index < 3 else
        "no hay selector de archivo con corte, legal hold, lotes, retención y checksum"
        if index < 20 else
        "recovery existente no selecciona snapshot por intervalo/checksum con control optimista"
        if index < 37 else
        "métricas existentes no validan un grafo local de spans ni evitan exportar atributos"
        if index < 53 else
        "data-quality de paneles no valida este esquema ni produce resultados por registro"
    )
    return f"repo_scan_before:{feature_id}/{api}: ID, API y capacidad ausentes; {nearest}."


def _roles(index, operation):
    family = _family(index)
    name = operation.__name__
    for prefix, suffix in (
        ("plan_safe_", "_rotation"), ("plan_", "_scheduled_archive"),
        ("plan_", "_point_in_time_restore"), ("observe_", "_distributed"),
        ("review_", "_quality"),
    ):
        if name.startswith(prefix) and name.endswith(suffix):
            resource = name[len(prefix):-len(suffix)]
            break
    return ("master", f"scope:{family}:{resource}")


MANIFEST = tuple(
    {"release_channel": "prealfa", "id": feature_id, "title": title, "capability": capability,
        "module": module, "api": operation.__name__,
        "test": f"tests/test_resource_rotation_archive_restore_observability_quality.py::test_{feature_id.replace('-', '_')}",
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

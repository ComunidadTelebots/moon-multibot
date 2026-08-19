"""Verified manifest for the Moonbot future-4862..future-4919 lot."""

from resource_temporal_collaborative_engines import ALL_APIS, IDS


TITLES = (
    "Correlación temporal de artículos editoriales en Moonbot",
    "Correlación temporal de imágenes moderadas en Moonbot",
    "Correlación temporal de apelaciones de usuarios en Moonbot",
    "Correlación temporal de proxies MTProto en Moonbot",
    "Correlación temporal de tareas persistentes en Moonbot",
    "Correlación temporal de reglas de moderación en Moonbot",
    "Correlación temporal de métricas lingüísticas en Moonbot",
    "Correlación temporal de traducciones comunitarias en Moonbot",
    "Correlación temporal de consentimientos personales en Moonbot",
    "Correlación temporal de reacciones Telegram en Moonbot",
    "Correlación temporal de paneles del master en Moonbot",
    "Correlación temporal de directorios de canales en Moonbot",
    "Correlación temporal de enlaces externos en Moonbot",
    "Revisión colaborativa de sesiones administrativas en Moonbot",
    "Revisión colaborativa de perfiles comunitarios en Moonbot",
    "Revisión colaborativa de comunidades Telegram en Moonbot",
    "Revisión colaborativa de anuncios propios en Moonbot",
    "Revisión colaborativa de notas de voz en Moonbot",
    "Revisión colaborativa de archivos sospechosos en Moonbot",
    "Revisión colaborativa de decisiones de captcha en Moonbot",
)

CAPABILITIES = tuple(title.removesuffix(" en Moonbot") for title in TITLES)
PREFLIGHT_TEMPORAL = (
    "IncidentCorrelator solo agrupa incidentes y el lote anterior cubre otros recursos; no existe "
    "correlación temporal tipada, deduplicada y acotada para este dominio."
)
PREFLIGHT_REVIEW = (
    "Existen aprobaciones/comentarios genéricos, pero no revisión ligada a versión con quórum, veto, "
    "separación solicitante-revisor, última decisión por revisor y huella estable."
)

MANIFEST = tuple(
    {"release_channel": "prealfa", "id": feature_id,
        "title": title,
        "capability": capability,
        "module": "resource_temporal_collaborative_engines.py",
        "api": operation.__name__,
        "test": f"tests/test_resource_temporal_collaborative_engines.py::test_{feature_id.replace('-', '_')}",
        "preflight": PREFLIGHT_TEMPORAL if index < 13 else PREFLIGHT_REVIEW,
    }
    for index, (feature_id, title, capability, operation) in enumerate(
        zip(IDS, TITLES, CAPABILITIES, ALL_APIS)
    )
)

assert len(MANIFEST) == 20
assert len({entry["id"] for entry in MANIFEST}) == 20
assert len({entry["title"] for entry in MANIFEST}) == 20
assert len({entry["capability"] for entry in MANIFEST}) == 20
assert len({entry["api"] for entry in MANIFEST}) == 20

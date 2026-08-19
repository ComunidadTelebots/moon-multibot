"""Verified manifest for future-4802 through future-4859 (Moonbot product)."""

from resource_incident_temporal_engines import ALL_APIS, IDS


TITLES = (
    "Escalado de incidentes en roles temporales en Moonbot",
    "Escalado de incidentes en grupos administrados en Moonbot",
    "Escalado de incidentes en mensajes programados en Moonbot",
    "Escalado de incidentes en feeds RSS en Moonbot",
    "Escalado de incidentes en vídeos de Telegram en Moonbot",
    "Escalado de incidentes en listas de bloqueo en Moonbot",
    "Escalado de incidentes en suscripciones obligatorias en Moonbot",
    "Escalado de incidentes en webhooks firmados en Moonbot",
    "Escalado de incidentes en horarios silenciosos en Moonbot",
    "Escalado de incidentes en incidentes correlacionados en Moonbot",
    "Escalado de incidentes en preferencias accesibles en Moonbot",
    "Escalado de incidentes en secretos de integración en Moonbot",
    "Escalado de incidentes en respuestas contextuales en Moonbot",
    "Escalado de incidentes en menús de la MiniApp en Moonbot",
    "Escalado de incidentes en estadísticas por bot en Moonbot",
    "Escalado de incidentes en preferencias publicitarias en Moonbot",
    "Escalado de incidentes en colas de procesamiento en Moonbot",
    "Correlación temporal de cuentas creadoras en Moonbot",
    "Correlación temporal de canales asociados en Moonbot",
    "Correlación temporal de campañas comunitarias en Moonbot",
)

CAPABILITIES = tuple(title.removesuffix(" en Moonbot") for title in TITLES)
PREFLIGHT_ESCALATION = (
    "Existe alert_* en resource_alert_offline_engines, pero solo eleva severidad por edad/reintentos; "
    "no implementa SLA de acuse, cadena de responsables, estado, huella idempotente ni evidencia redactada."
)
PREFLIGHT_CORRELATION = (
    "No se encontró correlación temporal por entidad con ventana, deduplicación, tipos admitidos y evidencia ordenada."
)

MANIFEST = tuple(
    {"release_channel": "alpha", "id": feature_id,
        "title": title,
        "capability": capability,
        "module": "resource_incident_temporal_engines.py",
        "api": operation.__name__,
        "test": f"tests/test_resource_incident_temporal_engines.py::test_{feature_id.replace('-', '_')}",
        "preflight": PREFLIGHT_ESCALATION if index < 17 else PREFLIGHT_CORRELATION,
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

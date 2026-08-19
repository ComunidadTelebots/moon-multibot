"""Manifest for the 60 Moonbot features future-5522..future-5699."""

from resource_quality_sandbox_governance_impact_engines import (
    ALL_APIS, GOVERNANCE_RESOURCES, IDS, IMPACT_RESOURCES, QUALITY_RESOURCES,
    SANDBOX_RESOURCES,
)

LABELS = {
    "managed_bots": "bots administrados", "recurring_reminders": "recordatorios recurrentes",
    "security_events": "eventos de seguridad", "regional_maps": "mapas regionales",
    "backups": "copias de seguridad", "ai_learning_data": "datos de aprendizaje IA",
    "rich_commands": "comandos enriquecidos", "hub_notifications": "notificaciones del Hub",
    "cookie_policies": "políticas de cookies", "wayback_history": "historial Wayback",
    "temporary_roles": "roles temporales", "managed_groups": "grupos administrados",
    "scheduled_messages": "mensajes programados", "rss_feeds": "feeds RSS",
    "telegram_videos": "vídeos de Telegram", "blocklists": "listas de bloqueo",
    "required_subscriptions": "suscripciones obligatorias", "signed_webhooks": "webhooks firmados",
    "quiet_hours": "horarios silenciosos", "correlated_incidents": "incidentes correlacionados",
    "accessible_preferences": "preferencias accesibles", "integration_secrets": "secretos de integración",
    "contextual_responses": "respuestas contextuales", "miniapp_menus": "menús de la MiniApp",
    "bot_statistics": "estadísticas por bot", "advertising_preferences": "preferencias publicitarias",
    "processing_queues": "colas de procesamiento", "creator_accounts": "cuentas creadoras",
    "associated_channels": "canales asociados", "community_campaigns": "campañas comunitarias",
    "editorial_articles": "artículos editoriales", "moderated_images": "imágenes moderadas",
    "user_appeals": "apelaciones de usuarios", "mtproto_proxies": "proxies MTProto",
    "persistent_tasks": "tareas persistentes", "moderation_rules": "reglas de moderación",
    "language_metrics": "métricas lingüísticas", "community_translations": "traducciones comunitarias",
    "personal_consents": "consentimientos personales", "telegram_reactions": "reacciones Telegram",
    "master_panels": "paneles del master", "channel_directories": "directorios de canales",
    "external_links": "enlaces externos", "administrative_sessions": "sesiones administrativas",
    "community_profiles": "perfiles comunitarios", "telegram_communities": "comunidades Telegram",
    "house_ads": "anuncios propios", "voice_notes": "notas de voz",
    "suspicious_files": "archivos sospechosos", "captcha_decisions": "decisiones de captcha",
}

RESOURCES = QUALITY_RESOURCES + SANDBOX_RESOURCES + GOVERNANCE_RESOURCES + IMPACT_RESOURCES


def _family(index):
    if index < 10: return "quality", "Control de calidad para", "quality:review"
    if index < 27: return "sandbox", "Sandbox aislado de", "sandbox:run"
    if index < 43: return "governance", "Gobernanza mediante propuestas de", "governance:review"
    return "impact", "Métricas de impacto para", "impact:read"


def _preflight(feature_id, api, family):
    distinction = {
        "quality": "los validadores existentes no cubren el esquema de este recurso",
        "sandbox": "los previews existentes no aíslan presupuesto, red, disco, procesos y secretos",
        "governance": "el voto genérico no tipa este recurso ni fuerza quórum y separación de funciones",
        "impact": "las estadísticas existentes no comparan baseline/current sin afirmar causalidad",
    }[family]
    return f"repo_scan_before:{feature_id}/{api}: ID, API y capacidad exacta ausentes; {distinction}."


MANIFEST = tuple(
    {"release_channel": "rc", "id": feature_id,
        "title": f"{prefix} {LABELS[resource]} en Moonbot",
        "capability": f"{prefix} {LABELS[resource]}",
        "module": "resource_quality_sandbox_governance_impact_engines.py",
        "api": api.__name__,
        "test": f"tests/test_resource_quality_sandbox_governance_impact.py::test_{feature_id.replace('-', '_')}",
        "preflight": _preflight(feature_id, api.__name__, family),
        "roles": ("master", f"{scope}:{resource}"),
    }
    for index, (feature_id, resource, api) in enumerate(zip(IDS, RESOURCES, ALL_APIS))
    for family, prefix, scope in (_family(index),)
)


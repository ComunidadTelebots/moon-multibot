"""Collaborative review and deterministic accessible explanation contracts."""

from __future__ import annotations

from typing import Any, Callable

from resource_temporal_collaborative_engines import _review_collaboratively


IDS = tuple(
    f"future-{number}"
    for number in (
        4922, 4925, 4928, 4931, 4934, 4937, 4940, 4943, 4946, 4949,
        4952, 4955, 4958, 4961, 4964, 4967, 4970, 4973, 4976, 4979,
        4982, 4985, 4988, 4991, 4994, 4997, 5000,
    )
)


_REVIEW_SPECS = (
    ("managed_bots", frozenset({"bot_operator", "security_admin", "master"}), 2, True),
    ("recurring_reminders", frozenset({"automation_owner", "privacy_admin", "master"}), 2, False),
    ("security_events", frozenset({"incident_owner", "security_admin", "master"}), 2, True),
    ("regional_maps", frozenset({"privacy_admin", "accessibility_admin", "master"}), 2, True),
    ("backups", frozenset({"backup_operator", "security_admin", "master"}), 2, True),
    ("ai_learning_data", frozenset({"ai_reviewer", "privacy_admin", "master"}), 2, True),
    ("rich_commands", frozenset({"command_editor", "accessibility_admin", "master"}), 2, False),
    ("hub_notifications", frozenset({"support", "privacy_admin", "master"}), 2, False),
    ("cookie_policies", frozenset({"privacy_admin", "legal_reviewer", "master"}), 2, True),
    ("wayback_history", frozenset({"archivist", "privacy_admin", "master"}), 2, False),
)


def _review_api(index: int) -> Callable[..., dict[str, Any]]:
    resource, roles, quorum, veto = _REVIEW_SPECS[index]

    def operation(
        proposal: dict[str, Any],
        reviews: list[dict[str, Any]],
        *,
        quorum_override: int | None = None,
    ) -> dict[str, Any]:
        return _review_collaboratively(
            IDS[index], resource, proposal, reviews, roles, quorum, veto, quorum_override
        )

    operation.__name__ = f"review_{resource}_collaboratively"
    operation.__doc__ = f"Resolve a version-bound collaborative review for {resource}."
    return operation


review_managed_bots_collaboratively = _review_api(0)
review_recurring_reminders_collaboratively = _review_api(1)
review_security_events_collaboratively = _review_api(2)
review_regional_maps_collaboratively = _review_api(3)
review_backups_collaboratively = _review_api(4)
review_ai_learning_data_collaboratively = _review_api(5)
review_rich_commands_collaboratively = _review_api(6)
review_hub_notifications_collaboratively = _review_api(7)
review_cookie_policies_collaboratively = _review_api(8)
review_wayback_history_collaboratively = _review_api(9)


_COPY = {
    "es": {
        "status": "Estado",
        "reason": "Motivo",
        "factors": "Factores considerados",
        "next": "Qué puedes hacer",
        "unknown": "No se proporcionó un motivo reconocible.",
        "states": {
            "active": "Activo", "inactive": "Inactivo", "pending": "Pendiente",
            "approved": "Aprobado", "rejected": "Rechazado", "blocked": "Bloqueado",
            "warning": "Requiere atención", "completed": "Completado",
        },
    },
    "en": {
        "status": "Status",
        "reason": "Reason",
        "factors": "Factors considered",
        "next": "What you can do",
        "unknown": "No recognised reason was provided.",
        "states": {
            "active": "Active", "inactive": "Inactive", "pending": "Pending",
            "approved": "Approved", "rejected": "Rejected", "blocked": "Blocked",
            "warning": "Needs attention", "completed": "Completed",
        },
    },
}


_EXPLANATION_SPECS = (
    ("temporary_roles", "roles temporales", "temporary roles", ("expiry", "scope", "permission"), "Revisa el alcance y la caducidad.", "Review scope and expiry."),
    ("managed_groups", "grupos administrados", "managed groups", ("permission", "bot_state", "membership"), "Comprueba los permisos del bot en el grupo.", "Check the bot permissions in the group."),
    ("scheduled_messages", "mensajes programados", "scheduled messages", ("schedule", "target", "delivery"), "Revisa la hora, el destino y el estado de entrega.", "Review time, target and delivery status."),
    ("rss_feeds", "feeds RSS", "RSS feeds", ("source", "filter", "fetch"), "Verifica la fuente y vuelve a probar el feed.", "Verify the source and test the feed again."),
    ("telegram_videos", "vídeos de Telegram", "Telegram videos", ("format", "duration", "moderation"), "Comprueba el formato y el resultado de moderación.", "Check format and moderation result."),
    ("blocklists", "listas de bloqueo", "blocklists", ("source", "match", "scope"), "Revisa la fuente, la coincidencia y el alcance.", "Review source, match and scope."),
    ("required_subscriptions", "suscripciones obligatorias", "required subscriptions", ("membership", "channel", "exception"), "Comprueba la membresía y las excepciones configuradas.", "Check membership and configured exceptions."),
    ("signed_webhooks", "webhooks firmados", "signed webhooks", ("signature", "timestamp", "delivery"), "Verifica la firma sin compartir el secreto.", "Verify the signature without sharing the secret."),
    ("quiet_hours", "horarios silenciosos", "quiet hours", ("timezone", "window", "exception"), "Comprueba la zona horaria, la franja y sus excepciones.", "Check timezone, window and exceptions."),
    ("correlated_incidents", "incidentes correlacionados", "correlated incidents", ("signal", "window", "severity"), "Revisa las señales vinculadas y su ventana temporal.", "Review linked signals and their time window."),
    ("accessible_preferences", "preferencias accesibles", "accessible preferences", ("channel", "reading_level", "language"), "Ajusta el canal, idioma o nivel de lectura.", "Adjust channel, language or reading level."),
    ("integration_secrets", "secretos de integración", "integration secrets", ("rotation", "expiry", "access"), "Rota el secreto y revisa quién puede usarlo.", "Rotate the secret and review who can use it."),
    ("contextual_responses", "respuestas contextuales", "contextual responses", ("intent", "confidence", "safety"), "Revisa la intención detectada y el filtro de seguridad.", "Review detected intent and safety filter."),
    ("miniapp_menus", "menús de la MiniApp", "MiniApp menus", ("role", "visibility", "navigation"), "Comprueba el rol, la visibilidad y la ruta de navegación.", "Check role, visibility and navigation path."),
    ("bot_statistics", "estadísticas por bot", "per-bot statistics", ("source", "period", "availability"), "Comprueba la fuente y el periodo de las métricas.", "Check metric source and period."),
    ("advertising_preferences", "preferencias publicitarias", "advertising preferences", ("consent", "placement", "frequency"), "Revisa consentimiento, ubicación y frecuencia.", "Review consent, placement and frequency."),
    ("processing_queues", "colas de procesamiento", "processing queues", ("priority", "capacity", "retry"), "Revisa prioridad, capacidad y reintentos.", "Review priority, capacity and retries."),
)


def _accessible_explanation(
    feature_id: str,
    resource: str,
    label_es: str,
    label_en: str,
    allowed_factors: tuple[str, ...],
    next_es: str,
    next_en: str,
    decision: dict[str, Any],
    preferences: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(decision, dict):
        raise ValueError("decision debe ser un objeto")
    prefs = dict(preferences or {})
    language = prefs.get("language", "es")
    if language not in _COPY:
        raise ValueError("language debe ser es o en")
    reading_level = prefs.get("reading_level", "simple")
    if reading_level not in {"simple", "standard"}:
        raise ValueError("reading_level no válido")
    output_channel = prefs.get("output_channel", "text")
    if output_channel not in {"text", "screen_reader", "both"}:
        raise ValueError("output_channel no válido")
    status = decision.get("status")
    if status not in _COPY[language]["states"]:
        raise ValueError("status no reconocido")
    reason_code = decision.get("reason_code")
    if not isinstance(reason_code, str) or not reason_code or len(reason_code) > 80:
        raise ValueError("reason_code no válido")
    raw_factors = decision.get("factors", [])
    if not isinstance(raw_factors, list) or len(raw_factors) > 20:
        raise ValueError("factors debe ser una lista acotada")
    factors = []
    for factor in raw_factors:
        if not isinstance(factor, dict) or set(factor) != {"code", "value"}:
            raise ValueError("factor no válido")
        code = factor["code"]
        if code not in allowed_factors:
            raise ValueError(f"factor no admitido para {resource}")
        value = factor["value"]
        if not isinstance(value, (str, int, float, bool)) or len(str(value)) > 200:
            raise ValueError("valor de factor no válido")
        factors.append({"code": code, "value": value})
    copy = _COPY[language]
    resource_label = label_es if language == "es" else label_en
    next_step = next_es if language == "es" else next_en
    status_label = copy["states"][status]
    reason_text = reason_code.replace("_", " ").strip().capitalize() or copy["unknown"]
    factor_text = "; ".join(f"{item['code'].replace('_', ' ')}: {item['value']}" for item in factors)
    sections = (
        {"heading": copy["status"], "text": status_label},
        {"heading": copy["reason"], "text": reason_text},
        {"heading": copy["factors"], "text": factor_text or copy["unknown"]},
        {"heading": copy["next"], "text": next_step},
    )
    plain_text = "\n".join(f"{section['heading']}: {section['text']}" for section in sections)
    return {
        "feature_id": feature_id,
        "resource": resource,
        "resource_label": resource_label,
        "language": language,
        "reading_level": reading_level,
        "output_channel": output_channel,
        "status": status,
        "reason_code": reason_code,
        "sections": sections,
        "plain_text": plain_text,
        "aria_label": f"{resource_label}: {status_label}",
        "uses_colour_alone": False,
        "deterministic": True,
        "executed": False,
    }


def _explanation_api(index: int) -> Callable[..., dict[str, Any]]:
    resource, label_es, label_en, factors, next_es, next_en = _EXPLANATION_SPECS[index]

    def operation(decision: dict[str, Any], preferences: dict[str, Any] | None = None) -> dict[str, Any]:
        return _accessible_explanation(
            IDS[10 + index], resource, label_es, label_en, factors, next_es, next_en,
            decision, preferences,
        )

    operation.__name__ = f"explain_{resource}_accessibly"
    operation.__doc__ = f"Create a deterministic accessible explanation for {resource}."
    return operation


explain_temporary_roles_accessibly = _explanation_api(0)
explain_managed_groups_accessibly = _explanation_api(1)
explain_scheduled_messages_accessibly = _explanation_api(2)
explain_rss_feeds_accessibly = _explanation_api(3)
explain_telegram_videos_accessibly = _explanation_api(4)
explain_blocklists_accessibly = _explanation_api(5)
explain_required_subscriptions_accessibly = _explanation_api(6)
explain_signed_webhooks_accessibly = _explanation_api(7)
explain_quiet_hours_accessibly = _explanation_api(8)
explain_correlated_incidents_accessibly = _explanation_api(9)
explain_accessible_preferences_accessibly = _explanation_api(10)
explain_integration_secrets_accessibly = _explanation_api(11)
explain_contextual_responses_accessibly = _explanation_api(12)
explain_miniapp_menus_accessibly = _explanation_api(13)
explain_bot_statistics_accessibly = _explanation_api(14)
explain_advertising_preferences_accessibly = _explanation_api(15)
explain_processing_queues_accessibly = _explanation_api(16)


REVIEW_APIS = (
    review_managed_bots_collaboratively,
    review_recurring_reminders_collaboratively,
    review_security_events_collaboratively,
    review_regional_maps_collaboratively,
    review_backups_collaboratively,
    review_ai_learning_data_collaboratively,
    review_rich_commands_collaboratively,
    review_hub_notifications_collaboratively,
    review_cookie_policies_collaboratively,
    review_wayback_history_collaboratively,
)

EXPLANATION_APIS = (
    explain_temporary_roles_accessibly,
    explain_managed_groups_accessibly,
    explain_scheduled_messages_accessibly,
    explain_rss_feeds_accessibly,
    explain_telegram_videos_accessibly,
    explain_blocklists_accessibly,
    explain_required_subscriptions_accessibly,
    explain_signed_webhooks_accessibly,
    explain_quiet_hours_accessibly,
    explain_correlated_incidents_accessibly,
    explain_accessible_preferences_accessibly,
    explain_integration_secrets_accessibly,
    explain_contextual_responses_accessibly,
    explain_miniapp_menus_accessibly,
    explain_bot_statistics_accessibly,
    explain_advertising_preferences_accessibly,
    explain_processing_queues_accessibly,
)

ALL_APIS = REVIEW_APIS + EXPLANATION_APIS

assert len(IDS) == len(ALL_APIS) == 27
assert len({operation.__name__ for operation in ALL_APIS}) == 27

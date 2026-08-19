"""Roadmap manifest for the application services in future-2282..2341."""

MODULE = "webapp_support_subscription_moderation_operations"

_SUPPORT = [
    "support_offline_continuity", "support_adaptive_trust", "support_campaign_plan",
    "support_intent", "support_integration", "support_vault", "support_easy_read",
    "support_sessions", "support_editorial", "support_budget", "support_reputation",
    "support_localization", "support_communication_preferences", "support_onboarding",
    "support_governance", "support_voice_control", "support_federated_bridge",
    "support_external_event", "support_digital_twin",
]
_SUBSCRIPTION = [
    "subscription_incidents", "subscription_workflow", "subscription_delegation",
    "subscription_coordinated_abuse", "subscription_copilot",
    "subscription_capacity_forecast", "subscription_batch_plan",
    "subscription_workspace", "subscription_media", "subscription_narrative_report",
    "subscription_alert_escalation", "subscription_offline_continuity",
    "subscription_adaptive_trust", "subscription_campaign_plan", "subscription_intent",
    "subscription_integration", "subscription_vault", "subscription_easy_read",
    "subscription_sessions", "subscription_editorial", "subscription_budget",
    "subscription_reputation", "subscription_localization",
    "subscription_communication_preferences", "subscription_onboarding",
    "subscription_governance", "subscription_voice_control",
    "subscription_federated_bridge", "subscription_external_event",
    "subscription_digital_twin",
]
_ACCESSIBILITY = [
    "accessibility_incidents", "accessibility_workflow", "accessibility_delegation",
    "accessibility_coordinated_abuse",
]
_MODERATION = [
    "moderation_incidents", "moderation_workflow", "moderation_delegation",
    "moderation_coordinated_abuse", "moderation_copilot",
    "moderation_capacity_forecast", "moderation_batch_plan",
]
_APIS = _SUPPORT + _SUBSCRIPTION + _ACCESSIBILITY + _MODERATION


def _role(api):
    if api.startswith("support_"):
        return "support_admin" if any(word in api for word in ("workflow", "delegation", "batch", "governance", "integration")) else "support_agent"
    if api.startswith("subscription_"):
        return "subscription_admin" if any(word in api for word in ("workflow", "delegation", "batch", "governance", "integration")) else "subscription_manager"
    if api.startswith("accessibility_"):
        return "accessibility_admin" if "workflow" in api or "delegation" in api else "accessibility_reviewer"
    return "moderation_admin" if any(word in api for word in ("workflow", "delegation", "batch")) else "moderator"


FEATURES = tuple(
    {"release_channel": "alpha", "id": f"future-{2282 + index}",
        "api": api,
        "module": MODULE,
        "role": _role(api),
        "status": "implemented",
        "preflight": "api_and_id_absent_from_head",
        "test": f"tests.test_webapp_support_subscription_moderation_operations.WebappSupportSubscriptionModerationTests.test_future_{2282 + index}",
    }
    for index, api in enumerate(_APIS)
)

assert len(FEATURES) == 60
assert len({item["api"] for item in FEATURES}) == 60

"""Manifest for future-2402..2461."""

MODULE = "webapp_ai_group_channel_operations"
_TAIL = [
    "workspace", "media", "narrative_report", "alert_escalation",
    "offline_continuity", "adaptive_trust", "campaign_plan", "intent",
    "integration", "vault", "easy_read", "sessions", "editorial", "budget",
    "reputation", "localization", "communication_preferences", "onboarding",
    "governance", "voice_control", "federated_bridge", "external_event",
    "digital_twin",
]
_FULL = [
    "incident_correlation", "workflow", "delegation", "coordinated_abuse",
    "copilot", "capacity_forecast", "batch_plan",
] + _TAIL
_SMALL = [
    "incident_correlation", "workflow", "delegation", "coordinated_abuse",
    "copilot", "capacity_forecast", "batch_plan",
]
_APIS = [f"ai_{x}" for x in _TAIL] + [f"moon_group_{x}" for x in _FULL] + [f"moon_channel_{x}" for x in _SMALL]


def _role(api):
    if api.startswith("ai_"):
        return "ai_admin" if any(x in api for x in ("integration", "governance", "workspace")) else "ai_reviewer"
    if api.startswith("moon_group_"):
        return "group_owner" if any(x in api for x in ("workflow", "delegation", "batch", "integration", "governance")) else "group_admin"
    return "channel_owner" if any(x in api for x in ("workflow", "delegation", "batch")) else "channel_admin"


FEATURES = tuple({
    "id": f"future-{2402 + index}", "api": api, "module": MODULE,
    "role": _role(api), "status": "implemented",
    "preflight": "api_and_id_absent_from_head", "test": f"tests.test_webapp_ai_group_channel_operations.WebappAiGroupChannelTests.test_future_{2402 + index}",
} for index, api in enumerate(_APIS))

assert len(FEATURES) == 60 and len({x["api"] for x in FEATURES}) == 60

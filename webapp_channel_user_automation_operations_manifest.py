"""Manifest for future-2462..2521."""

MODULE = "webapp_channel_user_automation_operations"
_TAIL = [
    "workspace", "media", "narrative_report", "alert_escalation",
    "offline_continuity", "adaptive_trust", "campaign_plan", "intent",
    "integration", "vault", "easy_read", "sessions", "editorial", "budget",
    "reputation", "localization", "communication_preferences", "onboarding",
    "governance", "voice_control", "federated_bridge", "external_event",
    "digital_twin",
]
_HEAD = ["incident_correlation", "workflow", "delegation", "coordinated_abuse", "copilot", "capacity_forecast", "batch_plan"]
_APIS = [f"moon_channel_{x}" for x in _TAIL] + [f"moon_user_{x}" for x in _HEAD + _TAIL] + [f"moon_automation_{x}" for x in _HEAD]


def _role(api):
    if api.startswith("moon_channel_"):
        return "channel_owner" if any(x in api for x in ("workspace", "integration", "governance")) else "channel_admin"
    if api.startswith("moon_user_"):
        return "user_admin" if any(x in api for x in ("workflow", "delegation", "batch", "integration", "governance")) else "user_reviewer"
    return "automation_owner" if any(x in api for x in ("workflow", "delegation", "batch")) else "automation_operator"


def _capability(api):
    prefixes = (("moon_channel_", "canales"), ("moon_user_", "usuarios"), ("moon_automation_", "automatizaciones"))
    prefix, area = next((prefix, area) for prefix, area in prefixes if api.startswith(prefix))
    operation = api.removeprefix(prefix).replace("_", " ")
    return f"{operation.capitalize()} para {area}"


FEATURES = tuple({"release_channel": "alpha", "id": f"future-{2462 + index}", "api": api, "module": MODULE,
    "title": _capability(api), "capability": _capability(api),
    "role": _role(api), "status": "implemented",
    "preflight": "api_and_id_absent_from_head",
    "test": f"tests.test_webapp_channel_user_automation_operations.WebappChannelUserAutomationTests.test_future_{2462 + index}",
} for index, api in enumerate(_APIS))

assert len(FEATURES) == 60 and len({x["api"] for x in FEATURES}) == 60

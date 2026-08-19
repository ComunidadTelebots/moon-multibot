"""Manifest for future-2522..2581 with user-facing metadata."""

MODULE = "webapp_automation_media_bot_operations"
TEST_CLASS = "tests.test_webapp_automation_media_bot_operations.WebappAutomationMediaBotTests"
_TAIL = ["workspace", "media", "narrative_report", "alert_escalation", "offline_continuity", "adaptive_trust", "campaign_plan", "intent", "integration", "vault", "easy_read", "sessions", "editorial", "budget", "reputation", "localization", "communication_preferences", "onboarding", "governance", "voice_control", "federated_bridge", "external_event", "digital_twin"]
_HEAD = ["incident_correlation", "workflow", "delegation", "coordinated_abuse", "copilot", "capacity_forecast", "batch_plan"]
_MEDIA_TAIL = ["workspace", "library"] + _TAIL[2:]
_APIS = [f"moon_automation_{x}" for x in _TAIL] + [f"moon_media_{x}" for x in _HEAD + _MEDIA_TAIL] + [f"managed_bot_{x}" for x in _HEAD]


def _domain(api):
    if api.startswith("moon_automation_"): return "automatizaciones"
    if api.startswith("moon_media_"): return "multimedia"
    return "bots administrados"


def _role(api):
    domain = _domain(api)
    privileged = any(x in api for x in ("workflow", "delegation", "batch", "integration", "governance"))
    return {"automatizaciones": "automation_owner" if privileged else "automation_operator", "multimedia": "media_admin" if privileged else "media_reviewer", "bots administrados": "bot_owner" if privileged else "bot_operator"}[domain]


def _capability(api):
    operation = api.split("_", 2)[-1]
    return f"{operation.replace('_', ' ')} para {_domain(api)} con vista previa segura y sin efectos directos"


FEATURES = tuple({"release_channel": "beta", "id": f"future-{2522 + index}", "api": api, "module": MODULE,
    "title": f"{_capability(api).capitalize()} en Moonbot",
    "capability": _capability(api), "role": _role(api), "status": "implemented",
    "preflight": "id_api_and_behavior_absent_from_head",
    "test": f"{TEST_CLASS}.test_future_{2522 + index}",
} for index, api in enumerate(_APIS))

assert len(FEATURES) == 60 and len({x["api"] for x in FEATURES}) == 60


"""Clasificación y autorización por alcance del registro de funciones."""

from __future__ import annotations


ROLES = ("user", "group_admin", "group_creator", "master")

MASTER_TERMS = (
    "global", "system", "backup", "secret", "incident", "creator_account",
    "account_creator", "admin_", "analytics", "audit", "security_event",
)
CREATOR_TERMS = (
    "config", "integration", "webhook", "subscription", "campaign", "rss",
    "feed", "role", "permission", "quota", "policy", "migration", "storage",
    "growth", "community", "managed_group", "associated_channel",
)
ADMIN_TERMS = (
    "moderation", "review", "captcha", "block", "alert", "message", "content",
    "schedule", "member", "user", "tag", "goal", "quality", "emergency",
    "decision", "expiry", "duplicate",
)
USER_TERMS = (
    "accessib", "localiz", "preference", "translation", "consent", "offline",
    "notification", "summary", "help", "personal", "navigation", "explain",
)


def _searchable(item):
    return " ".join(str(item.get(key) or "") for key in (
        "api", "module", "title", "capability", "context", "product"
    )).lower()


def classify_feature(item):
    explicit = str(item.get("minimum_role") or "").strip().lower()
    if explicit:
        if explicit not in ROLES:
            raise ValueError(f"Rol mínimo no válido: {explicit}")
        defaults = {"user": ("personal", "low"), "group_admin": ("group_operation", "moderate"),
                    "group_creator": ("group_configuration", "elevated"), "master": ("platform", "high")}
        scope, risk = defaults[explicit]
        index = ROLES.index(explicit)
        return {"minimum_role": explicit, "audience": list(ROLES[index:]),
                "scope": item.get("scope") or scope, "risk": item.get("risk") or risk}
    text = _searchable(item)
    if any(term in text for term in MASTER_TERMS):
        minimum_role, scope, risk = "master", "platform", "high"
    elif any(term in text for term in CREATOR_TERMS):
        minimum_role, scope, risk = "group_creator", "group_configuration", "elevated"
    elif any(term in text for term in ADMIN_TERMS):
        minimum_role, scope, risk = "group_admin", "group_operation", "moderate"
    elif any(term in text for term in USER_TERMS):
        minimum_role, scope, risk = "user", "personal", "low"
    else:
        minimum_role, scope, risk = "group_admin", "group_operation", "moderate"
    index = ROLES.index(minimum_role)
    return {
        "minimum_role": minimum_role,
        "audience": list(ROLES[index:]),
        "scope": scope,
        "risk": risk,
    }


def can_access_feature(item, actor_role):
    role = str(actor_role or "").strip().lower()
    if role not in ROLES:
        return False
    minimum = item.get("minimum_role") or classify_feature(item)["minimum_role"]
    return ROLES.index(role) >= ROLES.index(minimum)

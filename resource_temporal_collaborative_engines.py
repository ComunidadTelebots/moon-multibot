"""Resource-aware temporal correlation and collaborative review contracts."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Callable

from resource_incident_temporal_engines import _correlate_temporal, _redact, _utc_datetime


IDS = tuple(
    f"future-{number}"
    for number in (
        4862, 4865, 4868, 4871, 4874, 4877, 4880, 4883, 4886, 4889,
        4892, 4895, 4898, 4901, 4904, 4907, 4910, 4913, 4916, 4919,
    )
)


_TEMPORAL_SPECS = (
    ("editorial_articles", "article_id", frozenset({"draft", "publish", "update", "source_change", "archive"})),
    ("moderated_images", "media_hash", frozenset({"detect", "review", "quarantine", "release", "appeal"})),
    ("user_appeals", "appeal_id", frozenset({"submit", "evidence", "review", "escalate", "resolve"})),
    ("mtproto_proxies", "proxy_id", frozenset({"health_down", "health_up", "rotation", "traffic_spike", "config_change"})),
    ("persistent_tasks", "task_id", frozenset({"create", "defer", "run", "fail", "complete"})),
    ("moderation_rules", "rule_id", frozenset({"create", "change", "match", "disable", "enable"})),
    ("language_metrics", "language_code", frozenset({"sample", "anomaly", "baseline_change", "map_change"})),
    ("community_translations", "translation_id", frozenset({"submit", "edit", "vote", "approve", "reject"})),
    ("personal_consents", "subject_id", frozenset({"grant", "revoke", "expire", "scope_change"})),
    ("telegram_reactions", "message_id", frozenset({"reaction_add", "reaction_remove", "reaction_spike", "moderation"})),
    ("master_panels", "panel_id", frozenset({"open", "action", "error", "config_change"})),
    ("channel_directories", "directory_id", frozenset({"add", "remove", "update", "verification"})),
    ("external_links", "normalized_url", frozenset({"observed", "redirect_changed", "reputation_change", "blocked", "unblocked"})),
)


def _temporal_api(index: int) -> Callable[[list[dict[str, Any]], int, int], dict[str, Any]]:
    resource, entity_field, kinds = _TEMPORAL_SPECS[index]

    def operation(
        events: list[dict[str, Any]],
        window_minutes: int = 60,
        min_events: int = 2,
    ) -> dict[str, Any]:
        return _correlate_temporal(
            IDS[index], resource, events, entity_field, kinds, window_minutes, min_events
        )

    operation.__name__ = f"correlate_{resource}"
    operation.__doc__ = f"Correlate ordered {resource} events inside a bounded window."
    return operation


correlate_editorial_articles = _temporal_api(0)
correlate_moderated_images = _temporal_api(1)
correlate_user_appeals = _temporal_api(2)
correlate_mtproto_proxies = _temporal_api(3)
correlate_persistent_tasks = _temporal_api(4)
correlate_moderation_rules = _temporal_api(5)
correlate_language_metrics = _temporal_api(6)
correlate_community_translations = _temporal_api(7)
correlate_personal_consents = _temporal_api(8)
correlate_telegram_reactions = _temporal_api(9)
correlate_master_panels = _temporal_api(10)
correlate_channel_directories = _temporal_api(11)
correlate_external_links = _temporal_api(12)


_REVIEW_SPECS = (
    ("administrative_sessions", frozenset({"security_admin", "master"}), 2, True),
    ("community_profiles", frozenset({"community_admin", "privacy_admin", "master"}), 2, False),
    ("telegram_communities", frozenset({"community_admin", "group_owner", "master"}), 2, False),
    ("house_ads", frozenset({"campaign_manager", "privacy_admin", "master"}), 2, False),
    ("voice_notes", frozenset({"media_moderator", "privacy_admin", "master"}), 2, True),
    ("suspicious_files", frozenset({"security_admin", "malware_analyst", "master"}), 2, True),
    ("captcha_decisions", frozenset({"group_admin", "security_admin", "master"}), 2, True),
)


def _review_collaboratively(
    feature_id: str,
    resource: str,
    proposal: dict[str, Any],
    reviews: list[dict[str, Any]],
    allowed_roles: frozenset[str],
    default_quorum: int,
    rejection_veto: bool,
    quorum: int | None,
) -> dict[str, Any]:
    if not isinstance(proposal, dict):
        raise ValueError("proposal debe ser un objeto")
    proposal_id = proposal.get("id")
    requester_id = proposal.get("requested_by")
    base_version = proposal.get("base_version")
    proposed_version = proposal.get("proposed_version")
    payload = proposal.get("payload")
    if not isinstance(proposal_id, str) or not proposal_id.strip() or len(proposal_id) > 128:
        raise ValueError("id de propuesta no válido")
    if not isinstance(requester_id, str) or not requester_id.strip() or len(requester_id) > 128:
        raise ValueError("requested_by no válido")
    if not isinstance(base_version, int) or isinstance(base_version, bool) or base_version < 0:
        raise ValueError("base_version no válida")
    if not isinstance(proposed_version, int) or isinstance(proposed_version, bool) or proposed_version != base_version + 1:
        raise ValueError("proposed_version debe suceder a base_version")
    if not isinstance(payload, dict) or len(payload) > 100:
        raise ValueError("payload debe ser un objeto acotado")
    if not isinstance(reviews, list) or len(reviews) > 50:
        raise ValueError("reviews debe ser una lista acotada")
    required_quorum = default_quorum if quorum is None else quorum
    if not isinstance(required_quorum, int) or isinstance(required_quorum, bool) or not 1 <= required_quorum <= 10:
        raise ValueError("quorum debe estar entre 1 y 10")

    latest_by_reviewer: dict[str, dict[str, Any]] = {}
    for review in reviews:
        if not isinstance(review, dict):
            raise ValueError("review no válida")
        reviewer_id = review.get("reviewer_id")
        role = review.get("role")
        decision = review.get("decision")
        comment = review.get("comment", "")
        reviewed_version = review.get("reviewed_version")
        reviewed_at = _utc_datetime(review.get("reviewed_at"), "reviewed_at")
        if not isinstance(reviewer_id, str) or not reviewer_id.strip() or len(reviewer_id) > 128:
            raise ValueError("reviewer_id no válido")
        if reviewer_id == requester_id:
            raise ValueError("El solicitante no puede revisar su propuesta")
        if role not in allowed_roles:
            raise ValueError("Rol de revisor no autorizado")
        if decision not in {"approve", "reject", "request_changes"}:
            raise ValueError("decision no válida")
        if not isinstance(comment, str) or len(comment) > 2000:
            raise ValueError("comment no válido")
        if reviewed_version != proposed_version:
            raise ValueError("La revisión pertenece a otra versión")
        normalised = {
            "reviewer_id": reviewer_id,
            "role": role,
            "decision": decision,
            "comment": comment,
            "reviewed_version": reviewed_version,
            "reviewed_at": reviewed_at,
        }
        previous = latest_by_reviewer.get(reviewer_id)
        if previous is None or reviewed_at > previous["reviewed_at"]:
            latest_by_reviewer[reviewer_id] = normalised

    effective = sorted(latest_by_reviewer.values(), key=lambda row: (row["reviewed_at"], row["reviewer_id"]))
    approvals = sum(row["decision"] == "approve" for row in effective)
    rejections = sum(row["decision"] == "reject" for row in effective)
    change_requests = sum(row["decision"] == "request_changes" for row in effective)
    if rejections and rejection_veto:
        state = "rejected"
    elif change_requests:
        state = "changes_requested"
    elif approvals >= required_quorum:
        state = "approved"
    else:
        state = "pending"
    canonical = {
        "resource": resource,
        "proposal_id": proposal_id,
        "proposed_version": proposed_version,
        "reviewers": [(row["reviewer_id"], row["decision"]) for row in effective],
    }
    review_key = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "feature_id": feature_id,
        "resource": resource,
        "proposal_id": proposal_id,
        "base_version": base_version,
        "proposed_version": proposed_version,
        "state": state,
        "quorum": required_quorum,
        "approvals": approvals,
        "rejections": rejections,
        "change_requests": change_requests,
        "remaining_approvals": max(0, required_quorum - approvals),
        "reviewer_ids": tuple(row["reviewer_id"] for row in effective),
        "review_key": review_key,
        "payload": _redact(payload),
        "can_apply": state == "approved",
        "executed": False,
        "auditable": True,
    }


def _review_api(index: int) -> Callable[..., dict[str, Any]]:
    resource, roles, quorum, veto = _REVIEW_SPECS[index]

    def operation(
        proposal: dict[str, Any],
        reviews: list[dict[str, Any]],
        *,
        quorum_override: int | None = None,
    ) -> dict[str, Any]:
        return _review_collaboratively(
            IDS[13 + index], resource, proposal, reviews, roles, quorum, veto, quorum_override
        )

    operation.__name__ = f"review_{resource}_collaboratively"
    operation.__doc__ = f"Resolve a version-bound collaborative review for {resource}."
    return operation


review_administrative_sessions_collaboratively = _review_api(0)
review_community_profiles_collaboratively = _review_api(1)
review_telegram_communities_collaboratively = _review_api(2)
review_house_ads_collaboratively = _review_api(3)
review_voice_notes_collaboratively = _review_api(4)
review_suspicious_files_collaboratively = _review_api(5)
review_captcha_decisions_collaboratively = _review_api(6)


TEMPORAL_APIS = (
    correlate_editorial_articles,
    correlate_moderated_images,
    correlate_user_appeals,
    correlate_mtproto_proxies,
    correlate_persistent_tasks,
    correlate_moderation_rules,
    correlate_language_metrics,
    correlate_community_translations,
    correlate_personal_consents,
    correlate_telegram_reactions,
    correlate_master_panels,
    correlate_channel_directories,
    correlate_external_links,
)

REVIEW_APIS = (
    review_administrative_sessions_collaboratively,
    review_community_profiles_collaboratively,
    review_telegram_communities_collaboratively,
    review_house_ads_collaboratively,
    review_voice_notes_collaboratively,
    review_suspicious_files_collaboratively,
    review_captcha_decisions_collaboratively,
)

ALL_APIS = TEMPORAL_APIS + REVIEW_APIS

assert len(IDS) == len(ALL_APIS) == 20
assert len({operation.__name__ for operation in ALL_APIS}) == 20

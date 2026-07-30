"""Registro seguro de capacidades verificadas del roadmap.

Solo carga manifiestos incluidos explícitamente. Nunca acepta nombres de módulo o
función proporcionados por el cliente, evitando convertir el endpoint en un
ejecutor arbitrario de Python.
"""

from __future__ import annotations

import importlib
import inspect
from functools import lru_cache
from core.feature_access import can_access_feature, classify_feature


MANIFEST_MODULES = (
    "resource_forecast_manifest",
    "resource_drift_impact_manifest",
    "resource_impact_recovery_manifest",
    "resource_recovery_causal_manifest",
    "resource_causal_validation_manifest",
    "resource_orchestration_priority_manifest",
    "resource_priority_delegation_manifest",
    "resource_delegation_version_manifest",
    "resource_version_import_manifest",
    "resource_import_export_manifest",
    "resource_retention_consent_manifest",
    "resource_consent_diagnostic_manifest",
    "resource_diagnostic_history_manifest",
    "resource_history_semantic_manifest",
    "resource_semantic_private_summary_manifest",
    "resource_alert_offline_manifest",
    "resource_offline_autotest_manifest",
    "resource_autotest_template_manifest",
    "resource_template_bulk_manifest",
    "resource_bulk_recommendation_manifest",
    "resource_realtime_budget_manifest",
    "resource_budget_federation_manifest",
    "resource_federation_reconcile_manifest",
    "resource_reconcile_anonymize_manifest",
    "resource_anonymize_classify_manifest",
    "resource_duplicate_expiry_manifest",
    "resource_expiry_approval_manifest",
    "resource_approval_signature_manifest",
    "resource_signature_trace_manifest",
    "resource_trace_quota_manifest",
    "resource_incident_temporal_manifest",
    "resource_temporal_collaborative_manifest",
    "resource_review_accessible_localization_manifest",
    "resource_localization_easy_voice_grouped_manifest",
    "resource_grouped_routing_cache_rotation_manifest",
    "resource_rotation_archive_restore_observability_quality_manifest",
    "resource_quality_sandbox_governance_impact_manifest",
    "resource_energy_abuse_migration_federation_manifest",
    "core.web_creator_features_manifest",
    "core.web_creator_news_manifest",
    "core.web_news_operations_manifest",
    "core.web_proxy_features_manifest",
    "core.web_proxy_dashboard_manifest",
    "core.web_dashboard_operations_manifest",
    "core.web_analytics_features_manifest",
    "core.web_analytics_privacy_manifest",
    "core.web_privacy_operations_manifest",
    "core.web_seo_features_manifest",
    "core.web_seo_community_manifest",
    "core.web_community_operations_manifest",
    "core.web_support_features_manifest",
    "core.web_support_subscription_manifest",
    "core.web_subscription_operations_manifest",
    "core.web_accessibility_account_manifest",
    "core.web_account_creator_advanced_manifest",
    "core.web_creator_advanced_operations_manifest",
    "core.web_creator_news_advanced_manifest",
    "core.web_news_proxy_operations_manifest",
    "core.web_proxy_advanced_operations_manifest",
    "core.web_proxy_dashboard_operations_manifest",
    "core.web_dashboard_analytics_advanced_manifest",
    "core.web_analytics_advanced_operations_manifest",
    "core.web_analytics_privacy_controls_manifest",
    "webapp_offline_operations_manifest",
    "webapp_accessibility_operations_manifest",
    "webapp_moderation_content_operations_manifest",
    "webapp_content_security_ai_operations_manifest",
    "webapp_ai_accounts_creator_operations_manifest",
    "webapp_creator_news_proxy_operations_manifest",
    "webapp_proxy_dashboard_analytics_operations_manifest",
    "webapp_analytics_privacy_seo_operations_manifest",
    "webapp_seo_community_support_operations_manifest",
    "webapp_support_subscription_moderation_operations_manifest",
    "webapp_moderation_security_ai_operations_manifest",
    "webapp_future_0668_0687_manifest",
    "webapp_sublot_02_manifest",
    "webapp_sublot_03_manifest",
    "webapp_sublot_04_manifest",
    "webapp_sublot_05_manifest",
    "webapp_sublot_06_manifest",
    "webapp_sublot_07_manifest",
    "webapp_sublot_08_manifest",
    "webapp_sublot_09_manifest",
    "webapp_sublot_10_manifest",
    "webapp_sublot_11_manifest",
    "webapp_sublot_12_manifest",
    "webapp_sublot_13_manifest",
    "webapp_sublot_14_manifest",
    "webapp_sublot_15_manifest",
    "webapp_sublot_16_manifest",
    "webapp_sublot_17_manifest",
    "webapp_sublot_18_manifest",
    "webapp_sublot_19_manifest",
    "webapp_sublot_20_manifest",
    "webapp_sublot_21_manifest",
    "webapp_sublot_22_manifest",
    "webapp_sublot_23_manifest",
    "webapp_sublot_24_manifest",
)


def _entries(module):
    return getattr(module, "MANIFEST", None) or getattr(module, "FEATURES", None) or ()


@lru_cache(maxsize=1)
def registry():
    result = {}
    for manifest_name in MANIFEST_MODULES:
        manifest = importlib.import_module(manifest_name)
        for raw in _entries(manifest):
            item = dict(raw)
            feature_id = str(item.get("id", ""))
            api_name = str(item.get("api", ""))
            module_name = str(item.get("module") or manifest_name.removesuffix("_manifest")).removesuffix(".py").replace("/", ".")
            if not feature_id or not api_name or not module_name:
                raise RuntimeError(f"Manifiesto incompleto en {manifest_name}")
            if feature_id in result:
                raise RuntimeError(f"ID de función duplicado: {feature_id}")
            target = getattr(importlib.import_module(module_name), api_name, None)
            if not callable(target):
                raise RuntimeError(f"API no invocable: {module_name}.{api_name}")
            item.update({"module": module_name, "api": api_name, "callable": target})
            item.update(classify_feature(item))
            result[feature_id] = item
    return result


def list_features(actor_role=None):
    items = registry().values()
    if actor_role is not None:
        items = (item for item in items if can_access_feature(item, actor_role))
    return [{key: value for key, value in item.items() if key != "callable"} for item in items]


def execute(feature_id, payload, actor_role="master"):
    item = registry().get(str(feature_id))
    if item is None:
        raise KeyError("Función no registrada")
    if not can_access_feature(item, actor_role):
        raise PermissionError("El rol no puede ejecutar esta función")
    if not isinstance(payload, dict):
        raise ValueError("El payload debe ser un objeto")
    args = payload.get("args", [])
    kwargs = payload.get("kwargs", {})
    if not isinstance(args, list) or not isinstance(kwargs, dict):
        raise ValueError("args debe ser una lista y kwargs un objeto")
    target = item["callable"]
    inspect.signature(target).bind(*args, **kwargs)
    result = target(*args, **kwargs)
    if inspect.isawaitable(result):
        raise ValueError("Las capacidades asíncronas requieren un worker dedicado")
    return result

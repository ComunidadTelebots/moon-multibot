"""Registro seguro de capacidades verificadas del roadmap.

Solo carga manifiestos incluidos explícitamente. Nunca acepta nombres de módulo o
función proporcionados por el cliente, evitando convertir el endpoint en un
ejecutor arbitrario de Python.
"""

from __future__ import annotations

import importlib
import inspect
from functools import lru_cache


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
            module_name = str(item.get("module", "")).removesuffix(".py").replace("/", ".")
            if not feature_id or not api_name or not module_name:
                raise RuntimeError(f"Manifiesto incompleto en {manifest_name}")
            if feature_id in result:
                raise RuntimeError(f"ID de función duplicado: {feature_id}")
            target = getattr(importlib.import_module(module_name), api_name, None)
            if not callable(target):
                raise RuntimeError(f"API no invocable: {module_name}.{api_name}")
            item.update({"module": module_name, "api": api_name, "callable": target})
            result[feature_id] = item
    return result


def list_features():
    return [{key: value for key, value in item.items() if key != "callable"}
            for item in registry().values()]


def execute(feature_id, payload):
    item = registry().get(str(feature_id))
    if item is None:
        raise KeyError("Función no registrada")
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

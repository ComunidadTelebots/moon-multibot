"""Versioned evidence manifest for WebApp roadmap items future-1822..1841."""

_ROWS = [
    (1822, "Explicación de decisiones automáticas para modo offline", "Explicación de decisiones automáticas", "explain_offline_decision"),
    (1823, "Panel de calidad de datos para modo offline", "Panel de calidad de datos", "offline_data_quality"),
    (1824, "Importación con vista previa para modo offline", "Importación con vista previa", "preview_offline_import"),
    (1825, "Colaboración mediante comentarios para modo offline", "Colaboración mediante comentarios", "add_offline_comment"),
    (1826, "Etiquetas inteligentes para modo offline", "Etiquetas inteligentes", "offline_smart_tags"),
    (1827, "Resumen de actividad configurable para modo offline", "Resumen de actividad configurable", "offline_activity_digest"),
    (1828, "Alertas de caducidad para modo offline", "Alertas de caducidad", "offline_expiry_alerts"),
    (1829, "Modo de emergencia reversible para modo offline", "Modo de emergencia reversible", "open_offline_emergency"),
    (1830, "Historial de permisos efectivo para modo offline", "Historial de permisos efectivo", "offline_permission_history"),
    (1831, "Objetivos y progreso compartidos para modo offline", "Objetivos y progreso compartidos", "update_offline_shared_goal"),
    (1832, "Recomendador de configuración para modo offline", "Recomendador de configuración", "recommend_offline_config"),
    (1833, "Pruebas automáticas de configuración para modo offline", "Pruebas automáticas de configuración", "test_offline_config"),
    (1834, "Centro de consentimiento para modo offline", "Centro de consentimiento", "update_offline_consent"),
    (1835, "Navegación simplificada por tareas para modo offline", "Navegación simplificada por tareas", "offline_task_navigation"),
    (1836, "Sincronización entre dispositivos para modo offline", "Sincronización entre dispositivos", "sync_offline_devices"),
    (1837, "Detección de duplicados para modo offline", "Detección de duplicados", "detect_offline_duplicates"),
    (1838, "Cuotas adaptativas por uso para modo offline", "Cuotas adaptativas por uso", "offline_adaptive_quota"),
    (1839, "Panel de impacto comunitario para modo offline", "Panel de impacto comunitario", "offline_community_impact"),
    (1840, "Traducción revisable por la comunidad para modo offline", "Traducción revisable por la comunidad", "review_offline_translation"),
    (1841, "Notificaciones agrupadas por contexto para modo offline", "Notificaciones agrupadas por contexto", "group_offline_notifications"),
]

FEATURES = [
    {"release_channel": "prealfa", "id": f"future-{number}", "title": title, "capability": capability,
        "module": "webapp_offline_operations", "api": api,
        "test": f"tests.test_webapp_offline_operations.WebappOfflineOperationTests.test_future_{number}",
        "preflight": f"catalog:future-{number}:definition_only; runtime_symbol:{api}:absent",
    }
    for number, title, capability, api in _ROWS
]

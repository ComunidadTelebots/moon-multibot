"""Verified integration-operation capabilities exposed by the safe registry."""

MANIFEST = (
    {"release_channel": "beta", "id": "future-2665",
        "title": "Centro de incidencias correlacionadas para integraciones en Moonbot",
        "capability": "Centro de incidencias correlacionadas para integraciones",
        "module": "integration_operations_engines.py",
        "api": "correlate_integration_incidents",
        "minimum_role": "group_creator",
        "release_channel": "beta",
        "test": "tests/test_integration_operations_engines.py::test_future_2665",
        "preflight": "No existe correlación específica por integration_id, tipo, ventana y deduplicación; el escalado de secretos no es equivalente.",
    },
    {"release_channel": "beta", "id": "future-2667",
        "title": "Delegación temporal de funciones para integraciones en Moonbot",
        "capability": "Delegación temporal de funciones para integraciones",
        "module": "integration_operations_engines.py",
        "api": "delegate_integration_access",
        "minimum_role": "group_creator",
        "release_channel": "beta",
        "test": "tests/test_integration_operations_engines.py::test_future_2667",
        "preflight": "No existe delegación acotada de scopes integration:* con caducidad, revocación y separación owner/delegate.",
    },
)

"""Small defensive validators shared only by pure roadmap resource engines."""

from __future__ import annotations

import json
import math
import re
from typing import Any


_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.@-]{0,255}\Z")
_SENSITIVE = {"secret", "token", "password", "authorization", "cookie", "api_key", "signature", "payload_raw"}


def is_sensitive_key(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = re.sub(r"[^a-z0-9]", "", value.casefold())
    return normalized in {"authorization", "apikey", "signature", "payloadraw"} or normalized.endswith(
        ("secret", "token", "password", "cookie")
    )


def redact_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): "[REDACTED]" if is_sensitive_key(key) else redact_sensitive(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    return value


def safe_identifier(value: Any, field: str, maximum: int = 128) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum or not _SAFE_ID.fullmatch(value):
        raise ValueError(f"{field} no válido")
    if ".." in value or "/" in value or "\\" in value:
        raise ValueError(f"{field} contiene traversal")
    stem = value.rstrip(" .").split(".", 1)[0].upper()
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    if value != value.rstrip(" .") or stem in reserved:
        raise ValueError(f"{field} no válido")
    return value


def authorize(actor: dict[str, Any], permission: str) -> str:
    if not isinstance(actor, dict):
        raise PermissionError("actor es obligatorio")
    actor_id = safe_identifier(actor.get("id"), "actor.id")
    roles = actor.get("roles", [])
    scopes = actor.get("scopes", [])
    if not isinstance(roles, list) or len(roles) > 20 or not all(isinstance(role, str) and len(role) <= 80 for role in roles):
        raise PermissionError("roles no válidos")
    if not isinstance(scopes, list) or len(scopes) > 100 or not all(isinstance(scope, str) and len(scope) <= 160 for scope in scopes):
        raise PermissionError("scopes no válidos")
    if "master" not in roles and permission not in scopes:
        raise PermissionError(f"Falta permiso: {permission}")
    return actor_id


def bounded_json(value: Any, *, maximum_bytes: int = 65536, reject_secrets: bool = False) -> None:
    nodes = 0

    def visit(current: Any, depth: int) -> None:
        nonlocal nodes
        nodes += 1
        if nodes > 5000 or depth > 12:
            raise ValueError("Estructura demasiado compleja")
        if current is None or isinstance(current, (str, int, float, bool)):
            if isinstance(current, float) and not math.isfinite(current):
                raise ValueError("Número no finito")
            if isinstance(current, str) and (len(current) > maximum_bytes or any(ord(char) < 9 for char in current)):
                raise ValueError("Texto no válido")
            return
        if isinstance(current, list):
            if len(current) > 1000:
                raise ValueError("Lista demasiado grande")
            for item in current:
                visit(item, depth + 1)
            return
        if isinstance(current, dict):
            if len(current) > 200:
                raise ValueError("Objeto demasiado grande")
            for key, item in current.items():
                if not isinstance(key, str) or len(key) > 128:
                    raise ValueError("Clave no válida")
                if reject_secrets and is_sensitive_key(key):
                    raise ValueError(f"El campo secreto {key} no se puede almacenar")
                visit(item, depth + 1)
            return
        raise ValueError("Tipo no serializable")

    visit(value, 0)
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > maximum_bytes:
        raise ValueError("Payload demasiado grande")

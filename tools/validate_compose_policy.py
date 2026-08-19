"""Valida Compose renderizado sin mostrar secretos ni valores de entorno."""

import argparse
import json
import re
import sys


PROXY_SERVICES = ("mtproxy-1", "mtproxy-2", "mtproxy-3")
FORBIDDEN_MOUNTS = ("/", "/etc", "/proc", "/sys", "/dev", "/root", "/var/run")


def fail(message):
    raise ValueError(message)


def environment_map(service):
    environment = service.get("environment") or {}
    if isinstance(environment, dict):
        return {str(key): "" if value is None else str(value) for key, value in environment.items()}
    result = {}
    for item in environment:
        key, _, value = str(item).partition("=")
        result[key] = value
    return result


def validate_service_scope(name, service):
    if service.get("privileged"):
        fail(f"{name}: privileged no está permitido")
    if service.get("network_mode") == "host" or service.get("pid") == "host":
        fail(f"{name}: host network/PID no está permitido")
    for field in ("cap_add", "devices", "device_cgroup_rules"):
        if service.get(field):
            fail(f"{name}: {field} no está permitido")
    for volume in service.get("volumes") or []:
        source = volume.get("source") if isinstance(volume, dict) else str(volume).split(":", 1)[0]
        if not source:
            continue
        normalized = str(source).rstrip("/") or "/"
        if any(normalized == root or normalized.startswith(root.rstrip("/") + "/") for root in FORBIDDEN_MOUNTS):
            fail(f"{name}: montaje sensible no permitido")


def proxy_secret(service):
    env = environment_map(service)
    values = [value.strip() for key, value in env.items() if "SECRET" in key.upper() and value.strip()]
    if len(values) != 1:
        fail("cada MTProxy debe declarar exactamente un secret")
    value = values[0]
    if len(value) < 32 or len(value) > 512 or not re.fullmatch(r"[A-Za-z0-9_+=:/.-]+", value):
        fail("secret MTProxy con formato o longitud no válidos")
    return value


def proxy_port(service):
    published = []
    for port in service.get("ports") or []:
        value = port.get("published") if isinstance(port, dict) else str(port).split(":", 1)[0]
        if value not in (None, ""):
            published.append(value)
    if not published:
        env = environment_map(service)
        published = [value for key, value in env.items() if "PORT" in key.upper() and str(value).isdigit()]
    if len(published) != 1:
        fail("cada MTProxy debe publicar exactamente un puerto")
    if not published:
        fail("falta un puerto publicado para MTProxy")
    try:
        port = int(published[0])
    except (TypeError, ValueError):
        fail("puerto MTProxy no numérico")
    if not 1 <= port <= 65535:
        fail("puerto MTProxy fuera de rango")
    return port


def validate(document, kind):
    services = document.get("services") or {}
    for name, service in services.items():
        validate_service_scope(name, service or {})
    if kind == "moonbot":
        if "moonbot" not in services:
            fail("falta el servicio moonbot")
        return
    unexpected = sorted(name for name in services if name.startswith("mtproxy-") and name not in PROXY_SERVICES)
    missing = sorted(set(PROXY_SERVICES) - set(services))
    if missing or unexpected:
        fail("se requieren exactamente mtproxy-1, mtproxy-2 y mtproxy-3")
    secrets = [proxy_secret(services[name]) for name in PROXY_SERVICES]
    ports = [proxy_port(services[name]) for name in PROXY_SERVICES]
    for name in PROXY_SERVICES:
        if services[name].get("build"):
            fail(f"{name}: build local no está permitido para proxies")
        image = str(services[name].get("image") or "")
        if not re.search(r"@sha256:[a-fA-F0-9]{64}$", image):
            fail(f"{name}: la imagen debe estar fijada por digest sha256")
    if len(set(secrets)) != 3:
        fail("los tres secrets MTProxy deben ser diferentes")
    if len(set(ports)) != 3:
        fail("los tres puertos MTProxy deben ser diferentes")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("moonbot", "proxies"), required=True)
    args = parser.parse_args()
    try:
        document = json.load(sys.stdin)
        validate(document, args.kind)
    except (ValueError, json.JSONDecodeError) as error:
        print(f"política Compose rechazada: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

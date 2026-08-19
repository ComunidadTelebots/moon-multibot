import ipaddress
import re
from urllib.parse import parse_qsl, urlparse


_URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)


def inspect_url(value):
    """Inspección estructural offline: nunca conecta con el destino."""
    raw = str(value or "").strip()
    if len(raw) > 2048:
        return {"ok": False, "error": "URL demasiado larga"}
    try:
        parsed = urlparse(raw)
        port = parsed.port
    except ValueError:
        return {"ok": False, "error": "puerto no válido"}
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return {"ok": False, "error": "URL HTTP/HTTPS no válida"}
    host = parsed.hostname.lower().rstrip(".")
    try:
        address = ipaddress.ip_address(host)
        ip_literal, private = True, not address.is_global
    except ValueError:
        ip_literal = False
        private = host == "localhost" or host.endswith((".local", ".internal", ".localhost"))
    signals = []
    if parsed.username or parsed.password: signals.append("credentials_in_url")
    if host.startswith("xn--") or ".xn--" in host: signals.append("punycode_domain")
    if ip_literal: signals.append("ip_literal")
    if private: signals.append("local_or_private_destination")
    if port and port not in {80, 443}: signals.append("non_standard_port")
    if len(raw) > 500: signals.append("very_long_url")
    return {"ok": True, "inspection": {"scheme": parsed.scheme, "host": host[:253], "port": port,
        "path": (parsed.path or "/")[:500], "query_parameters": len(parse_qsl(parsed.query, keep_blank_values=True)),
        "fragment": bool(parsed.fragment), "signals": signals, "safe_to_fetch": not private,
        "normalized": parsed._replace(fragment="").geturl()[:2048]}}


def handle_command(bot, cid, uid, text, rank):
    t = text.strip()
    low = t.lower()

    if low.startswith("/extracturls"):
        body = t[len("/extracturls"):].strip()
        if not body:
            bot.send_msg(cid, "Uso: /extracturls <texto>")
            return True
        urls = _URL_RE.findall(body)
        if not urls:
            bot.send_msg(cid, "No encontre URLs.")
            return True
        bot.send_msg(cid, "URLs encontradas:\n" + "\n".join(urls[:30]))
        return True

    if low.startswith("/domain"):
        body = t[len("/domain"):].strip()
        if not body:
            bot.send_msg(cid, "Uso: /domain <url>")
            return True
        result = inspect_url(body)
        if not result.get("ok"):
            bot.send_msg(cid, f"URL inválida: {result.get('error')}")
            return True
        info = result["inspection"]
        signals = ", ".join(info["signals"]) or "sin señales estructurales"
        bot.send_msg(cid, f"Dominio: `{info['host']}`\nEsquema: {info['scheme']}\nSeñales: {signals}")
        return True

    return False

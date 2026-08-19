"""Comandos informativos recuperados del bot clásico TeleBots.

Todas las consultas usan fuentes públicas, límites cortos y una caché local para no
saturar servicios externos ni ralentizar el bucle principal del bot.
"""

import datetime
import html
import random
import re
import time
from urllib.parse import quote, quote_plus
from zoneinfo import ZoneInfo

import requests


USER_AGENT = "MoonMultibot/18 (+https://todosobreall.tech)"
TIMEOUT = 8
_CACHE = {}


def _plain(value, limit=700):
    value = html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    return re.sub(r"\s+", " ", value).strip()[:limit]


def _query(text, command):
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        raise ValueError(f"Uso: /{command} <consulta>")
    return parts[1].strip()[:180]


def _json(url, params=None, ttl=300):
    key = (url, tuple(sorted((params or {}).items())))
    now = time.time()
    cached = _CACHE.get(key)
    if cached and now - cached[0] < ttl:
        return cached[1]
    response = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    _CACHE[key] = (now, payload)
    return payload


def _geocode(place):
    data = _json("https://geocoding-api.open-meteo.com/v1/search", {
        "name": place, "count": 1, "language": "es", "format": "json",
    }, ttl=86400)
    rows = data.get("results") or []
    if not rows:
        raise ValueError("No encontré ese lugar.")
    return rows[0]


def _weather(place):
    geo = _geocode(place)
    data = _json("https://api.open-meteo.com/v1/forecast", {
        "latitude": geo["latitude"], "longitude": geo["longitude"],
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
        "timezone": "auto",
    }, ttl=600)
    current = data.get("current") or {}
    name = ", ".join(filter(None, [geo.get("name"), geo.get("admin1"), geo.get("country")]))
    return (
        f"Tiempo en {name}\n"
        f"Temperatura: {current.get('temperature_2m', '?')} °C "
        f"(sensación {current.get('apparent_temperature', '?')} °C)\n"
        f"Humedad: {current.get('relative_humidity_2m', '?')} % · "
        f"Viento: {current.get('wind_speed_10m', '?')} km/h · "
        f"Precipitación: {current.get('precipitation', '?')} mm\n"
        f"Código meteorológico WMO: {current.get('weather_code', '?')}"
    )


def _wiki(query, dictionary=False):
    host = "es.wiktionary.org" if dictionary else "es.wikipedia.org"
    data = _json(f"https://{host}/w/api.php", {
        "action": "query", "list": "search", "srsearch": query,
        "srlimit": 3, "utf8": 1, "format": "json",
    }, ttl=3600)
    rows = (data.get("query") or {}).get("search") or []
    if not rows:
        return "No encontré resultados."
    label = "Wikcionario" if dictionary else "Wikipedia"
    lines = [f"Resultados en {label}:"]
    for row in rows:
        title = _plain(row.get("title"), 100)
        snippet = _plain(row.get("snippet"), 220)
        lines.append(f"• {title}: {snippet}\nhttps://{host}/wiki/{quote(title.replace(' ', '_'))}")
    return "\n".join(lines)


def _earthquakes(argument):
    minimum = 4.5
    if argument:
        try:
            minimum = max(0.0, min(10.0, float(argument.replace(",", "."))))
        except ValueError:
            raise ValueError("Uso: /terremoto [magnitud mínima]. Ejemplo: /terremoto 5")
    data = _json("https://earthquake.usgs.gov/fdsnws/event/1/query", {
        "format": "geojson", "limit": 5, "orderby": "time", "minmagnitude": minimum,
    }, ttl=300)
    features = data.get("features") or []
    if not features:
        return f"No hay terremotos recientes de magnitud {minimum} o superior."
    lines = [f"Últimos terremotos (M ≥ {minimum}):"]
    for item in features:
        props = item.get("properties") or {}
        stamp = datetime.datetime.fromtimestamp((props.get("time") or 0) / 1000, datetime.timezone.utc)
        lines.append(f"• M{props.get('mag', '?')} · {_plain(props.get('place'), 120)} · {stamp:%d/%m %H:%M} UTC\n{props.get('url', '')}")
    return "\n".join(lines)


def _stack(query):
    data = _json("https://api.stackexchange.com/2.3/search/advanced", {
        "site": "stackoverflow", "order": "desc", "sort": "relevance",
        "pagesize": 3, "q": query,
    }, ttl=1800)
    rows = data.get("items") or []
    if not rows:
        return "No encontré preguntas relacionadas en Stack Overflow."
    lines = ["Resultados en Stack Overflow:"]
    for row in rows:
        lines.append(f"• {_plain(row.get('title'), 180)}\n{row.get('link', '')}")
    return "\n".join(lines)


def handle_command(bot, cid, uid, text, rank):
    parts = text.strip().split(maxsplit=1)
    cmd = parts[0].lower() if parts else ""
    argument = parts[1].strip() if len(parts) > 1 else ""
    if cmd not in {"/clima", "/hora", "/mapa", "/terremoto", "/wiki", "/diccionario", "/stack", "/google", "/rae", "/sera"}:
        return False
    try:
        if cmd == "/clima":
            answer = _weather(_query(text, "clima"))
        elif cmd == "/hora":
            geo = _geocode(_query(text, "hora"))
            timezone = geo.get("timezone") or "UTC"
            current = datetime.datetime.now(ZoneInfo(timezone))
            answer = f"Hora en {geo.get('name')}, {geo.get('country')}: {current:%H:%M:%S · %d/%m/%Y}\nZona: {timezone}"
        elif cmd == "/mapa":
            place = _query(text, "mapa")
            geo = _geocode(place)
            answer = f"{geo.get('name')}, {geo.get('country')}\nhttps://www.openstreetmap.org/?mlat={geo['latitude']}&mlon={geo['longitude']}#map=12/{geo['latitude']}/{geo['longitude']}"
        elif cmd == "/terremoto":
            answer = _earthquakes(argument)
        elif cmd == "/wiki":
            answer = _wiki(_query(text, "wiki"))
        elif cmd == "/diccionario":
            answer = _wiki(_query(text, "diccionario"), dictionary=True)
        elif cmd == "/stack":
            answer = _stack(_query(text, "stack"))
        elif cmd == "/google":
            query = _query(text, "google")
            answer = f"Búsqueda preparada:\nhttps://www.google.com/search?q={quote_plus(query)}"
        elif cmd == "/rae":
            word = _query(text, "rae")
            answer = f"Consulta oficial en el DLE de la RAE:\nhttps://dle.rae.es/{quote(word)}"
        else:
            if not argument:
                raise ValueError("Uso: /sera <pregunta>")
            answer = random.choice(("Sí.", "No.", "Es posible.", "Aún no está claro.", "Todo apunta a que sí.", "Mejor vuelve a preguntarlo más tarde."))
        bot.send_msg(cid, answer, parse_mode=None)
    except (requests.RequestException, KeyError):
        bot.send_msg(cid, "La fuente externa no responde ahora. Inténtalo de nuevo en unos minutos.", parse_mode=None)
    except ValueError as exc:
        bot.send_msg(cid, str(exc), parse_mode=None)
    except Exception:
        bot.send_msg(cid, "No pude completar la consulta en este momento.", parse_mode=None)
    return True

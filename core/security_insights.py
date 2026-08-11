"""Explainable, offline insights over Moonbot's existing threat history."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
import hashlib


_INTENTS = {
    "malware": {"malware", "virus", "troyano", "malicious", "amenaza", "infectado"},
    "phishing": {"phishing", "suplantacion", "credenciales", "fraude", "login"},
    "image": {"imagen", "image", "foto", "vision", "ocr"},
    "url": {"url", "enlace", "link", "dominio", "domain"},
    "file": {"archivo", "file", "documento", "hash"},
}


def _tokens(value):
    normalized = unicodedata.normalize("NFKD", str(value or "").casefold())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return set(re.findall(r"[a-z0-9._-]{2,}", normalized))


def _document(row):
    fields = [row.get("source"), row.get("kind"), row.get("risk"), row.get("filename"), row.get("value")]
    fields.extend(row.get("signals", []) if isinstance(row.get("signals"), list) else [])
    return _tokens(" ".join(str(value or "")[:500] for value in fields))


def _number(value):
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def search_history(rows, query, limit=50):
    rows = [row for row in rows if isinstance(row, dict)]
    terms = _tokens(query)
    expanded = set(terms)
    for intent, synonyms in _INTENTS.items():
        if terms & synonyms or intent in terms:
            expanded.update(synonyms)
    if not expanded:
        return list(reversed(rows[-limit:]))
    ranked = []
    for index, row in enumerate(rows):
        document = _document(row)
        exact = len(terms & document)
        related = len((expanded - terms) & document)
        score = exact * 4 + related
        if score:
            ranked.append((score, index, {**row, "match_score": score,
                                          "matched_terms": sorted(expanded & document)[:10]}))
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [item[2] for item in ranked[:max(1, min(int(limit), 100))]]


def summarize_history(rows):
    rows = [row for row in rows if isinstance(row, dict)][-300:]
    risks = Counter(str(row.get("risk") or "unknown") for row in rows)
    sources = Counter(str(row.get("source") or "unknown") for row in rows)
    kinds = Counter(str(row.get("kind") or "unknown") for row in rows)
    signals = Counter(str(signal) for row in rows for signal in
                      (row.get("signals", []) if isinstance(row.get("signals"), list) else []))
    suspicious = sum(row.get("risk") in ("high", "medium") or _number(row.get("malicious")) > 0
                     for row in rows)
    return {
        "total": len(rows), "suspicious": suspicious,
        "clean": max(0, len(rows) - suspicious),
        "by_risk": dict(risks), "by_source": dict(sources), "by_kind": dict(kinds),
        "top_signals": [{"signal": key, "count": count} for key, count in signals.most_common(8)],
        "explanation": "Conteo determinista de los últimos 300 análisis; no usa mensajes ni perfiles de usuarios.",
    }


def detect_anomalies(rows, window=25):
    rows = [row for row in rows if isinstance(row, dict)]
    window = max(5, min(int(window), 100))
    if len(rows) < window * 2:
        return {"ready": False, "anomalies": [], "reason": f"Se requieren {window * 2} análisis para comparar ventanas."}
    baseline, recent = rows[-window * 2:-window], rows[-window:]

    def risky(batch):
        return sum(row.get("risk") in ("high", "medium") or _number(row.get("malicious")) > 0 for row in batch)

    base_risky, recent_risky = risky(baseline), risky(recent)
    anomalies = []
    threshold = max(3, base_risky * 2)
    if recent_risky >= threshold and recent_risky > base_risky:
        anomalies.append({"code": "risk_spike", "severity": "high", "baseline": base_risky,
                          "current": recent_risky, "detail": "La ventana reciente duplica el volumen de análisis sospechosos."})
    base_sources, recent_sources = Counter(str(row.get("source") or "unknown") for row in baseline), Counter(str(row.get("source") or "unknown") for row in recent)
    for source, count in recent_sources.items():
        if count >= 5 and count >= max(3, base_sources.get(source, 0) * 3):
            anomalies.append({"code": "source_spike", "severity": "medium", "source": source,
                              "baseline": base_sources.get(source, 0), "current": count,
                              "detail": "Una fuente creció al menos tres veces frente a la ventana anterior."})
    return {"ready": True, "window": window, "anomalies": anomalies,
            "baseline_suspicious": base_risky, "recent_suspicious": recent_risky}


def build_alerts(rows, anomaly_report, minimum_severity="medium", acknowledged=None):
    acknowledged = {str(value) for value in (acknowledged or [])}
    levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    minimum = minimum_severity if minimum_severity in levels else "medium"
    candidates = []
    for anomaly in (anomaly_report or {}).get("anomalies", []):
        candidates.append({"kind": "anomaly", "severity": anomaly.get("severity", "medium"),
                           "title": "Anomalía en análisis de seguridad", "detail": anomaly.get("detail", ""),
                           "context": {key: anomaly.get(key) for key in ("code", "source", "baseline", "current") if anomaly.get(key) is not None}})
    recent_high = [row for row in rows[-50:] if isinstance(row, dict) and
                   (row.get("risk") == "high" or _number(row.get("malicious")) > 0)]
    if recent_high:
        candidates.append({"kind": "high_risk", "severity": "high", "title": "Análisis de riesgo alto",
                           "detail": f"Hay {len(recent_high)} análisis recientes con riesgo alto.",
                           "context": {"count": len(recent_high)}})
    alerts = []
    for item in candidates:
        if levels.get(item["severity"], 0) < levels[minimum]:
            continue
        identity = "|".join((item["kind"], item["severity"], item["detail"], repr(sorted(item["context"].items()))))
        alert_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
        alerts.append({**item, "id": alert_id, "acknowledged": alert_id in acknowledged})
    return alerts


def redact_results(rows, enabled=True):
    if not enabled:
        return [dict(row) for row in rows]
    redacted = []
    for row in rows:
        safe = dict(row)
        identity = str(safe.get("value") or safe.get("filename") or safe.get("kind") or "analysis")
        safe["fingerprint"] = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]
        safe.pop("value", None)
        safe.pop("filename", None)
        safe["redacted"] = True
        redacted.append(safe)
    return redacted

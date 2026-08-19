"""Análisis visual local y explicable para revisión administrativa."""

import hashlib
import math
import os
import re
from PIL import Image, ImageStat, UnidentifiedImageError

try:
    import pytesseract
except ImportError:  # La imagen puede funcionar sin OCR.
    pytesseract = None


URL_RE = re.compile(r"(?:https?://|www\.|t\.me/)[^\s]+", re.I)
SCAM_TERMS = (
    "inversión garantizada", "ganancia garantizada", "duplica tu dinero",
    "premio", "urgente", "paga ahora", "wallet", "seed phrase", "frase semilla",
)
BRANDS = ("telegram", "paypal", "binance", "banco", "meta", "google", "microsoft")


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _entropy(image):
    histogram = image.convert("L").histogram()
    total = sum(histogram) or 1
    return round(-sum((n / total) * math.log2(n / total) for n in histogram if n), 2)


def _skin_ratio(image):
    sample = image.convert("RGB")
    sample.thumbnail((320, 320))
    pixels = list(sample.getdata())
    if not pixels:
        return 0.0
    matches = sum(
        1 for red, green, blue in pixels
        if red > 95 and green > 40 and blue > 20
        and max(red, green, blue) - min(red, green, blue) > 15
        and abs(red - green) > 15 and red > green and red > blue
    )
    return round(matches / len(pixels), 3)


def analyze_image(path, options=None):
    options = options or {}
    try:
        with Image.open(path) as original:
            original.verify()
        with Image.open(path) as original:
            source_format = original.format or "unknown"
            image = original.copy()
            width, height = image.size
            if width * height > 40_000_000:
                return {"ok": False, "error": "La imagen supera el límite de 40 megapíxeles"}
            rgb = image.convert("RGB")
            stat = ImageStat.Stat(rgb.resize((1, 1)))
            average = [round(value) for value in stat.mean]
            entropy = _entropy(rgb)
            skin_ratio = _skin_ratio(rgb) if options.get("sensitive", True) else 0
            text = ""
            ocr_available = bool(pytesseract)
            if options.get("ocr", True) and pytesseract:
                try:
                    ocr_image = rgb.copy()
                    ocr_image.thumbnail((1800, 1800))
                    text = pytesseract.image_to_string(
                        ocr_image, lang="spa+eng", config="--psm 6", timeout=15
                    ).strip()[:5000]
                except Exception:
                    ocr_available = False
            lower = text.lower()
            urls = list(dict.fromkeys(URL_RE.findall(text)))[:20]
            scams = [term for term in SCAM_TERMS if term in lower]
            brands = [brand for brand in BRANDS if brand in lower]
            signals = []
            score = 0
            if urls:
                score += min(30, 10 + len(urls) * 5)
                signals.append({"type": "link", "label": f"{len(urls)} enlace(s) en la imagen", "weight": 20})
            if scams:
                score += min(45, len(scams) * 20)
                signals.append({"type": "scam_text", "label": "Texto de estafa: " + ", ".join(scams[:3]), "weight": 40})
            if options.get("impersonation", True) and brands and (urls or scams):
                score += 25
                signals.append({"type": "impersonation", "label": "Posible suplantación: " + ", ".join(brands[:3]), "weight": 25})
            # Es una señal débil: nunca causa una decisión automática por sí sola.
            if options.get("sensitive", True) and skin_ratio >= 0.55:
                score += 15
                signals.append({"type": "sensitive_review", "label": "Revisión sensible recomendada", "weight": 15, "review_only": True})
            score = min(100, score)
            risk = "high" if score >= 70 else "medium" if score >= 35 else "low" if score else "clean"
            return {
                "ok": True, "filename": os.path.basename(path), "sha256": _sha256(path),
                "format": source_format, "width": width, "height": height,
                "mode": image.mode, "bytes": os.path.getsize(path), "entropy": entropy,
                "average_rgb": average, "ocr_text": text, "ocr_available": ocr_available,
                "urls": urls, "brands": brands, "skin_ratio": skin_ratio,
                "score": score, "risk": risk, "signals": signals,
                "review_required": score >= 35,
                "automatic_action": False,
                "explanation": "Las señales visuales requieren revisión humana; no generan un ban automático.",
            }
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        return {"ok": False, "error": f"Imagen no válida: {error}"}

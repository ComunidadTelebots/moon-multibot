"""Resource-specific cultural localization contracts for future-5001..5020."""

import datetime
import re


LOCALES = {
    "es-ES": {"language": "es", "direction": "ltr", "date": "%d/%m/%Y", "decimal": ",", "thousands": "."},
    "en-US": {"language": "en", "direction": "ltr", "date": "%m/%d/%Y", "decimal": ".", "thousands": ","},
    "fr-FR": {"language": "fr", "direction": "ltr", "date": "%d/%m/%Y", "decimal": ",", "thousands": " "},
    "ar": {"language": "ar", "direction": "rtl", "date": "%Y/%m/%d", "decimal": "٫", "thousands": "٬"},
}


def _context(locale):
    code = str(locale or "").replace("_", "-")
    if code not in LOCALES:
        raise ValueError("unsupported locale")
    return {"locale": code, **LOCALES[code]}


def _text(value, field, maximum=500):
    clean = " ".join(str(value or "").split())
    if not clean or len(clean) > maximum:
        raise ValueError(f"invalid {field}")
    return clean


def _date(value, locale):
    parsed = datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.strftime(LOCALES[locale]["date"])


def _number(value, locale, decimals=0):
    raw = f"{float(value):,.{decimals}f}"
    profile = LOCALES[locale]
    return raw.replace(",", "\0").replace(".", profile["decimal"]).replace("\0", profile["thousands"])


def localize_admin_session(data, locale):  # future-5001
    ctx = _context(locale); session = _text(data.get("session_id"), "session_id", 128); started = _date(data.get("started_at"), ctx["locale"])
    timezone = _text(data.get("timezone"), "timezone", 64)
    return {**ctx, "resource": "admin_session", "session_id": session, "started_date": started, "timezone": timezone, "status": "localized"}


def localize_temporary_role(data, locale):  # future-5002
    ctx = _context(locale); role = _text(data.get("role"), "role", 80); expires = _date(data.get("expires_at"), ctx["locale"])
    if role.casefold() not in {"moderator", "reviewer", "editor", "admin"}: raise ValueError("unsupported temporary role")
    return {**ctx, "resource": "temporary_role", "role_label": role, "expires_date": expires, "temporary": True}


def localize_creator_account(data, locale):  # future-5003
    ctx = _context(locale); name = _text(data.get("display_name"), "display_name", 100); bio = str(data.get("bio") or "").strip()[:500]
    return {**ctx, "resource": "creator_account", "display_name": name, "bio": bio, "handle_preserved": str(data.get("handle") or ""), "status": "localized"}


def localize_community_profile(data, locale):  # future-5004
    ctx = _context(locale); name = _text(data.get("name"), "name", 100); visibility = str(data.get("visibility"))
    if visibility not in {"public", "members", "private"}: raise ValueError("invalid visibility")
    return {**ctx, "resource": "community_profile", "name": name, "visibility": visibility, "region_label": _text(data.get("region"), "region", 80)}


def localize_managed_group(data, locale):  # future-5005
    ctx = _context(locale); title = _text(data.get("title"), "title", 128); rules = [_text(x, "rule", 300) for x in data.get("rules", [])]
    if not rules: raise ValueError("at least one group rule required")
    return {**ctx, "resource": "managed_group", "title": title, "rules": rules[:20], "rule_count": len(rules[:20])}


def localize_associated_channel(data, locale):  # future-5006
    ctx = _context(locale); title = _text(data.get("title"), "title", 128); username = str(data.get("username") or "").lstrip("@")
    if not re.fullmatch(r"[A-Za-z0-9_]{5,32}", username): raise ValueError("invalid channel username")
    return {**ctx, "resource": "associated_channel", "title": title, "username": username, "category_label": _text(data.get("category"), "category", 60)}


def localize_telegram_community(data, locale):  # future-5007
    ctx = _context(locale); title = _text(data.get("title"), "title", 128); members = int(data.get("member_count", -1))
    if members < 0: raise ValueError("invalid member_count")
    return {**ctx, "resource": "telegram_community", "title": title, "member_count": members, "member_count_display": _number(members, ctx["locale"]), "welcome": _text(data.get("welcome"), "welcome", 500)}


def localize_scheduled_message(data, locale):  # future-5008
    ctx = _context(locale); content = _text(data.get("content"), "content", 4096); send_date = _date(data.get("send_at"), ctx["locale"])
    return {**ctx, "resource": "scheduled_message", "content": content, "send_date": send_date, "schedule_preserved": str(data.get("send_at")), "status": "scheduled"}


def localize_community_campaign(data, locale):  # future-5009
    ctx = _context(locale); name = _text(data.get("name"), "name", 120); budget = float(data.get("budget", -1)); currency = str(data.get("currency", "")).upper()
    if budget < 0 or not re.fullmatch(r"[A-Z]{3}", currency): raise ValueError("invalid campaign budget")
    return {**ctx, "resource": "community_campaign", "name": name, "budget": budget, "budget_display": f"{_number(budget, ctx['locale'], 2)} {currency}", "currency": currency}


def localize_house_ad(data, locale):  # future-5010
    ctx = _context(locale); title = _text(data.get("title"), "title", 120); cta = _text(data.get("cta"), "cta", 40)
    if data.get("sponsored_disclosure") is not True: raise ValueError("ad disclosure required")
    return {**ctx, "resource": "house_ad", "title": title, "cta": cta, "disclosure": "publicidad" if ctx["language"] == "es" else "sponsored", "status": "localized"}


def localize_rss_feed(data, locale):  # future-5011
    ctx = _context(locale); title = _text(data.get("title"), "title", 150); url = str(data.get("url") or "")
    if not url.startswith("https://"): raise ValueError("https feed required")
    return {**ctx, "resource": "rss_feed", "title": title, "url": url, "categories": sorted({_text(x, "category", 50) for x in data.get("categories", [])})}


def localize_editorial_article(data, locale):  # future-5012
    ctx = _context(locale); title = _text(data.get("title"), "title", 200); body = _text(data.get("body"), "body", 20000)
    return {**ctx, "resource": "editorial_article", "title": title, "body": body, "published_date": _date(data.get("published_at"), ctx["locale"]), "word_count": len(body.split())}


def localize_voice_note(data, locale):  # future-5013
    ctx = _context(locale); transcript = _text(data.get("transcript"), "transcript", 10000); duration = float(data.get("duration", 0))
    if duration <= 0 or duration > 600: raise ValueError("invalid voice duration")
    return {**ctx, "resource": "voice_note", "transcript": transcript, "duration_seconds": duration, "caption_direction": ctx["direction"], "audio_modified": False}


def localize_telegram_video(data, locale):  # future-5014
    ctx = _context(locale); title = _text(data.get("title"), "title", 200); captions = _text(data.get("captions"), "captions", 20000)
    duration = int(data.get("duration", 0))
    if duration <= 0: raise ValueError("invalid video duration")
    return {**ctx, "resource": "telegram_video", "title": title, "captions": captions, "duration_seconds": duration, "captions_available": True}


def localize_moderated_image(data, locale):  # future-5015
    ctx = _context(locale); alt = _text(data.get("alt_text"), "alt_text", 1000); labels = sorted({_text(x, "label", 80) for x in data.get("moderation_labels", [])})
    if not labels: raise ValueError("moderation labels required")
    return {**ctx, "resource": "moderated_image", "alt_text": alt, "moderation_labels": labels, "image_modified": False}


def localize_suspicious_file(data, locale):  # future-5016
    ctx = _context(locale); filename = _text(data.get("filename"), "filename", 255); risk = str(data.get("risk"))
    if risk not in {"low", "medium", "high", "critical"}: raise ValueError("invalid risk")
    return {**ctx, "resource": "suspicious_file", "filename": filename, "risk": risk, "reason": _text(data.get("reason"), "reason", 500), "safe_to_open": False}


def localize_blocklist(data, locale):  # future-5017
    ctx = _context(locale); name = _text(data.get("name"), "name", 80); scope = str(data.get("scope"))
    if scope not in {"global", "group"}: raise ValueError("invalid blocklist scope")
    count = int(data.get("entry_count", -1))
    if count < 0: raise ValueError("invalid entry_count")
    return {**ctx, "resource": "blocklist", "name": name, "scope": scope, "entry_count": count, "entry_count_display": _number(count, ctx["locale"])}


def localize_user_appeal(data, locale):  # future-5018
    ctx = _context(locale); appeal_id = _text(data.get("appeal_id"), "appeal_id", 128); status = str(data.get("status"))
    if status not in {"pending", "approved", "rejected"}: raise ValueError("invalid appeal status")
    return {**ctx, "resource": "user_appeal", "appeal_id": appeal_id, "status": status, "reason": _text(data.get("reason"), "reason", 2000), "decision_date": _date(data["decided_at"], ctx["locale"]) if data.get("decided_at") else None}


def localize_captcha_decision(data, locale):  # future-5019
    ctx = _context(locale); decision = str(data.get("decision"))
    if decision not in {"pass", "fail", "expired"}: raise ValueError("invalid captcha decision")
    score = float(data.get("score", -1))
    if not 0 <= score <= 1: raise ValueError("invalid captcha score")
    return {**ctx, "resource": "captcha_decision", "decision": decision, "score_percent": _number(score * 100, ctx["locale"], 1) + "%", "explanation": _text(data.get("explanation"), "explanation", 500)}


def localize_required_subscription(data, locale):  # future-5020
    ctx = _context(locale); channel = str(data.get("channel_username") or "").lstrip("@")
    if not re.fullmatch(r"[A-Za-z0-9_]{5,32}", channel): raise ValueError("invalid channel username")
    return {**ctx, "resource": "required_subscription", "channel_username": channel, "requirement": _text(data.get("requirement"), "requirement", 500), "mandatory": data.get("mandatory") is True, "status": "localized"}

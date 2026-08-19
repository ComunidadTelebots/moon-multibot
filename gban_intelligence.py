"""Motor local, explicable y adaptable para propuestas comunitarias de GBAN."""

import datetime
import re


class GbanIntelligenceEngine:
    PROFILE_KEY = "GBAN_REPORTER_PROFILES"
    METRICS_KEY = "GBAN_INTELLIGENCE_METRICS"
    MODEL_VERSION = "moon_gban_intelligence_v2"

    def __init__(self, db):
        self.db = db

    @staticmethod
    def _when(value):
        try:
            return datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
        except (TypeError, ValueError):
            return datetime.datetime.min

    def reporter_profile(self, reporter_id):
        profiles = self.db.get(self.PROFILE_KEY, {})
        profiles = profiles if isinstance(profiles, dict) else {}
        raw = profiles.get(str(reporter_id), {})
        approved = max(0, int(raw.get("approved", 0) or 0))
        rejected = max(0, int(raw.get("rejected", 0) or 0))
        # Prior bayesiano moderado: no premia en exceso a un reportante nuevo.
        reliability = round((approved + 2) / (approved + rejected + 4), 3)
        return {"approved": approved, "rejected": rejected, "reliability": reliability,
                "samples": approved + rejected}

    @staticmethod
    def evidence_quality(values):
        rows = [str(value).strip()[:500] for value in (values or []) if str(value).strip()]
        kinds = set()
        for value in rows:
            low = value.lower()
            if re.search(r"(?:mensaje|message)[\s:#-]*\d+", low):
                kinds.add("telegram_message")
            if re.search(r"https?://", low):
                kinds.add("url")
            if re.search(r"\b[a-f0-9]{32,64}\b", low):
                kinds.add("content_hash")
            if any(token in low for token in ("captura", "screenshot", "archivo", "video", "foto")):
                kinds.add("media_reference")
        quality = min(1.0, len(rows) * 0.15 + len(kinds) * 0.2)
        return {"count": len(rows), "kinds": sorted(kinds), "quality": round(quality, 2)}

    def assess(self, report, reports, spam_result=None, cas_result=None, context=None):
        now = datetime.datetime.now()
        uid = str(report.get("user_id", "")).strip()
        cutoff = now - datetime.timedelta(days=30)
        related = [row for row in reports if isinstance(row, dict)
                   and str(row.get("user_id", "")).strip() == uid
                   and self._when(row.get("created_at")) >= cutoff
                   and row.get("status", "pending") in ("pending", "approved")]
        groups = sorted({str(row.get("chat_id", "")).strip() for row in related if str(row.get("chat_id", "")).strip()})
        reporters = sorted({str(row.get("reported_by", "")).strip() for row in related if str(row.get("reported_by", "")).strip()})
        profiles = [self.reporter_profile(value) for value in reporters]
        reporter_reliability = round(sum(row["reliability"] for row in profiles) / len(profiles), 3) if profiles else 0.5
        evidence = self.evidence_quality(report.get("evidence", []))
        spam_result = spam_result if isinstance(spam_result, dict) else {}
        spam_score = max(0, min(int(spam_result.get("score", 0) or 0), 100))
        cas_banned = bool(isinstance(cas_result, dict) and cas_result.get("ok") and cas_result.get("banned"))
        context = context if isinstance(context, dict) else {}

        score, signals = 8, [{"signal": "authenticated_admin_report", "points": 8}]
        evidence_points = round(evidence["quality"] * 22)
        if evidence_points:
            score += evidence_points
            signals.append({"signal": "evidence_quality", "points": evidence_points, **evidence})
        spam_points = round(spam_score * 0.45)
        if spam_points:
            score += spam_points
            signals.append({"signal": "behavioral_spam", "points": spam_points, "score": spam_score,
                            "reasons": spam_result.get("reasons", [])})
        if len(groups) >= 2 and len(reporters) >= 2:
            consensus_points = min(55, (len(groups) - 1) * 20 + (len(reporters) - 1) * 8)
            score += consensus_points
            signals.append({"signal": "independent_consensus", "points": consensus_points,
                            "groups": groups, "reporters": len(reporters)})
        trust_adjustment = round((reporter_reliability - 0.5) * 30)
        if trust_adjustment:
            score += trust_adjustment
            signals.append({"signal": "reporter_reliability", "points": trust_adjustment,
                            "reliability": reporter_reliability})
        rejected = sum(1 for row in reports if isinstance(row, dict) and str(row.get("user_id")) == uid
                       and row.get("status") == "rejected" and self._when(row.get("updated_at")) >= cutoff)
        if rejected:
            deduction = min(30, rejected * 12)
            score -= deduction
            signals.append({"signal": "previous_rejections", "points": -deduction, "count": rejected})
        if cas_banned:
            score = 100
            signals.append({"signal": "cas_confirmed", "points": 100})

        local_ban_groups = sorted({str(value) for value in context.get("local_ban_groups", []) if str(value)})
        captcha_fail_groups = sorted({str(value) for value in context.get("captcha_fail_groups", []) if str(value)})
        warning_count = max(0, int(context.get("warning_count", 0) or 0))
        spam_events = max(0, int(context.get("spam_events", 0) or 0))
        ham_events = max(0, int(context.get("ham_events", 0) or 0))
        if local_ban_groups:
            points = min(28, len(local_ban_groups) * 10)
            score += points
            signals.append({"signal": "local_ban_recurrence", "points": points, "groups": local_ban_groups})
        if captcha_fail_groups:
            points = min(18, len(captcha_fail_groups) * 6)
            score += points
            signals.append({"signal": "captcha_failures", "points": points, "groups": captcha_fail_groups})
        if warning_count:
            points = min(15, warning_count * 3)
            score += points
            signals.append({"signal": "moderation_warnings", "points": points, "count": warning_count})
        if spam_events:
            points = min(22, spam_events * 5)
            score += points
            signals.append({"signal": "historical_spam_events", "points": points, "count": spam_events})
        if ham_events:
            deduction = min(25, ham_events * 7)
            score -= deduction
            signals.append({"signal": "verified_legitimate_history", "points": -deduction, "count": ham_events})

        score = max(0, min(score, 100))
        independent_consensus = len(groups) >= 3 and len(reporters) >= 2 and reporter_reliability >= 0.5
        strong_behavior = spam_score >= 90 and evidence["quality"] >= 0.45
        persistent_behavior = len(local_ban_groups) >= 2 and (spam_events >= 2 or warning_count >= 3) and score >= 80
        automatic = bool(cas_banned or (independent_consensus and score >= 70) or strong_behavior or persistent_behavior)
        confidence = min(0.99, 0.35 + evidence["quality"] * 0.2 + min(len(groups), 3) * 0.1
                         + min(len(reporters), 3) * 0.08 + (0.2 if cas_banned else 0))
        return {
            "score": score, "confidence": round(confidence, 2),
            "level": "critical" if score >= 90 else "high" if score >= 70 else "medium" if score >= 40 else "low",
            "signals": signals, "groups": groups, "reporters": reporters,
            "reporter_reliability": reporter_reliability, "evidence": evidence,
            "behavior_context": {"local_ban_groups": local_ban_groups, "captcha_fail_groups": captcha_fail_groups,
                                 "warning_count": warning_count, "spam_events": spam_events, "ham_events": ham_events},
            "automatic_eligible": automatic,
            "recommendation": "temporary_global_ban" if automatic else "master_review" if score >= 40 else "observe",
            "analyzed_at": now.isoformat(), "engine": self.MODEL_VERSION,
        }

    def learn_resolution(self, report, decision):
        reporter = str(report.get("reported_by", "")).strip()
        if not reporter or decision not in ("approved", "rejected"):
            return
        profiles = self.db.get(self.PROFILE_KEY, {})
        profiles = profiles if isinstance(profiles, dict) else {}
        profile = profiles.get(reporter, {}) if isinstance(profiles.get(reporter), dict) else {}
        profile[decision] = int(profile.get(decision, 0) or 0) + 1
        profile["updated_at"] = datetime.datetime.now().isoformat()
        profiles[reporter] = profile
        self.db.set(self.PROFILE_KEY, profiles)
        metrics = self.db.get(self.METRICS_KEY, {})
        metrics = metrics if isinstance(metrics, dict) else {}
        metrics[decision] = int(metrics.get(decision, 0) or 0) + 1
        metrics["last_resolution_at"] = profile["updated_at"]
        self.db.set(self.METRICS_KEY, metrics)

    def calibration(self):
        metrics = self.db.get(self.METRICS_KEY, {})
        metrics = metrics if isinstance(metrics, dict) else {}
        approved = int(metrics.get("approved", 0) or 0)
        rejected = int(metrics.get("rejected", 0) or 0)
        total = approved + rejected
        return {"decisions": total, "approved": approved, "rejected": rejected,
                "precision_proxy": round(approved / total, 3) if total else None,
                "model": self.MODEL_VERSION}

    @staticmethod
    def render_markdown(report, resolved_status=None):
        analysis = report.get("analysis") or {}
        status = resolved_status or report.get("status", "pending")
        labels = {"pending": "Pendiente de intervención", "approved": "GBAN confirmado",
                  "rejected": "Reporte rechazado y cuarentena revocada"}
        signals = analysis.get("signals") or []
        signal_lines = [
            f"- `{row.get('signal', 'señal')}`: {int(row.get('points', 0) or 0):+d} puntos"
            for row in signals[:12] if isinstance(row, dict)
        ]
        return (
            "# 🛡️ Propuesta comunitaria de GBAN\n\n"
            f"> **Estado:** {labels.get(status, status)}\n\n"
            "| Campo | Resultado |\n|---|---|\n"
            f"| Usuario | `{report.get('user_id', '')}` |\n"
            f"| Grupo | `{report.get('chat_id', '')}` |\n"
            f"| Riesgo | **{analysis.get('score', 0)}/100** |\n"
            f"| Confianza | {round(float(analysis.get('confidence', 0) or 0) * 100)}% |\n"
            f"| Recomendación | `{analysis.get('recommendation', 'master_review')}` |\n\n"
            f"## Motivo\n{report.get('reason') or 'Sin motivo'}\n\n"
            "<details><summary>Señales analizadas</summary>\n\n"
            + ("\n".join(signal_lines) or "- Sin señales adicionales")
            + "\n\n</details>\n\n"
            f"_Motor: {analysis.get('engine', GbanIntelligenceEngine.MODEL_VERSION)}_"
        )[:32768]

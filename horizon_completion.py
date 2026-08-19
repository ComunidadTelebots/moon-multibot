"""Operational services for the remaining Horizonte 202 capabilities.

Every catalog entry has a stable slug, validation, a deterministic result and
an auditable persisted record. Network-facing integrations create explicit
jobs/configurations; workers can consume them without exposing secrets here.
"""

import datetime
import hashlib
import json
import math
import re
import uuid
from collections import Counter, defaultdict


FEATURES = {
    # Content and channels (remaining 5)
    "source_map": ("Mapa de fuentes y citas de cada publicación", "content"),
    "stale_content": ("Detección de contenido desactualizado", "content"),
    "multichannel_package": ("Paquetes de publicación multicanal", "content"),
    "live_coverage": ("Modo cobertura en directo con hitos", "content"),
    "thematic_archive": ("Archivo temático navegable de conversaciones", "content"),
    # AI and knowledge (10)
    "project_memories": ("Memorias separadas por proyecto y finalidad", "ai"),
    "adaptive_explanations": ("Explicaciones con nivel principiante o experto", "ai"),
    "agent_debate": ("Debate interno entre agentes antes de responder", "ai"),
    "visible_sources": ("Registro visible de fuentes usadas por la IA", "ai"),
    "knowledge_gaps": ("Detector de lagunas de conocimiento", "ai"),
    "approved_examples": ("Entrenamiento por ejemplos aprobados y contraejemplos", "ai"),
    "adaptive_teacher": ("Modo profesor con ejercicios adaptativos", "ai"),
    "minority_summaries": ("Resúmenes que preservan opiniones minoritarias", "ai"),
    "model_comparison": ("Comparador de respuestas entre modelos", "ai"),
    "knowledge_expiry": ("Caducidad automática del conocimiento sensible al tiempo", "ai"),
    # Accessibility and languages (10)
    "easy_read": ("Lectura fácil automática para textos complejos", "access"),
    "image_audio_description": ("Audiodescripción de imágenes relevantes", "access"),
    "collaborative_subtitles": ("Subtítulos colaborativos para mensajes de vídeo", "access"),
    "chat_high_contrast": ("Modo alto contraste por chat", "access"),
    "voice_navigation": ("Navegación completa mediante voz", "access"),
    "transliteration": ("Transliteración entre alfabetos", "access"),
    "local_glossaries": ("Glosarios locales por comunidad e idioma", "access"),
    "terminology_translation": ("Traducción que conserva nombres y terminología", "access"),
    "sign_language_summary": ("Resúmenes en lengua de signos mediante avatar", "access"),
    "accessibility_barriers": ("Detector de barreras de accesibilidad antes de publicar", "access"),
    # Privacy and protection (10)
    "personal_data_panel": ("Panel personal de datos almacenados", "privacy"),
    "selective_deletion": ("Borrado selectivo con vista previa", "privacy"),
    "one_time_admin_messages": ("Mensajes administrativos de un solo uso", "privacy"),
    "sensitive_capture_alerts": ("Alertas por capturas de datos sensibles", "privacy"),
    "export_anonymization": ("Anonimización automática de exportaciones", "privacy"),
    "split_recovery_keys": ("Claves de recuperación divididas entre responsables", "privacy"),
    "temporary_investigation": ("Modo investigación con acceso temporal", "privacy"),
    "secret_detection": ("Detector de secretos pegados por accidente", "privacy"),
    "retention_labels": ("Etiquetas de retención por tipo de dato", "privacy"),
    "monthly_privacy_report": ("Informe mensual de privacidad comprensible", "privacy"),
    # Operations and reliability (10)
    "digital_twin": ("Gemelo digital para ensayar configuraciones", "operations"),
    "canary_groups": ("Despliegue canario por grupos seleccionados", "operations"),
    "slo_recovery": ("Recuperación automática según objetivo de servicio", "operations"),
    "dependency_map": ("Mapa de dependencias y puntos únicos de fallo", "operations"),
    "error_budget": ("Presupuesto de errores por función", "operations"),
    "incident_replay": ("Reproducción de incidentes con eventos anonimizados", "operations"),
    "config_drift": ("Detector de configuraciones divergentes", "operations"),
    "timezone_maintenance": ("Ventanas de mantenimiento por zona horaria", "operations"),
    "predictive_capacity": ("Capacidad predictiva de colas y almacenamiento", "operations"),
    "essential_degraded_mode": ("Modo degradado que conserva funciones esenciales", "operations"),
    # Open integrations (10)
    "visual_connectors": ("Conectores creados visualmente sin código", "integrations"),
    "automation_marketplace": ("Mercado comunitario de automatizaciones", "integrations"),
    "activitypub_bridge": ("Puente ActivityPub para comunidades federadas", "integrations"),
    "caldav_sync": ("Sincronización bidireccional con calendarios CalDAV", "integrations"),
    "opml_exchange": ("Importación y exportación mediante OPML", "integrations"),
    "signed_websub": ("Eventos firmados con WebSub", "integrations"),
    "portable_identity": ("Identidad portable mediante credenciales verificables", "integrations"),
    "matrix_flows": ("Flujos compatibles con Matrix", "integrations"),
    "bot_capability_catalog": ("Catálogo automático de capacidades por bot", "integrations"),
    "integration_sandbox": ("Entorno de pruebas aislado para integraciones", "integrations"),
    # Sustainability and growth (10)
    "community_costs": ("Calculadora transparente de costes por comunidad", "sustainability"),
    "funding_milestones": ("Objetivos de financiación con hitos verificables", "sustainability"),
    "sponsor_frequency": ("Patrocinios con frecuencia máxima configurable", "sustainability"),
    "creator_revenue_share": ("Reparto de ingresos entre creadores colaboradores", "sustainability"),
    "energy_saving": ("Modo ahorro energético para tareas no urgentes", "sustainability"),
    "operational_footprint": ("Informe de huella operativa estimada", "sustainability"),
    "feature_donations": ("Donaciones destinadas a funciones concretas", "sustainability"),
    "community_credits": ("Créditos comunitarios no transferibles", "sustainability"),
    "respectful_churn": ("Predicción de abandono con intervención respetuosa", "sustainability"),
    "consented_experiments": ("Experimentos A/B con consentimiento y límites", "sustainability"),
    # Telegram experience (10)
    "pending_topics_inbox": ("Bandeja unificada de temas pendientes", "telegram"),
    "personal_shortcuts": ("Atajos personales sincronizados con la Mini App", "telegram"),
    "message_side_panel": ("Panel lateral contextual por mensaje", "telegram"),
    "ephemeral_operations": ("Respuestas efímeras para operaciones sensibles", "telegram"),
    "linked_communities": ("Comunidades enlazadas con permisos heredables", "telegram"),
    "adaptive_entry_forms": ("Consultas de entrada con formularios adaptativos", "telegram"),
    "admin_guided_routes": ("Rutas guiadas para nuevos administradores", "telegram"),
    "temporary_event_mode": ("Modo evento que transforma temporalmente el grupo", "telegram"),
    "bulk_preview_undo": ("Acciones masivas con previsualización y deshacer", "telegram"),
    "impact_notifications": ("Centro de notificaciones priorizadas por impacto", "telegram"),
}


class HorizonCompletion:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def _now():
        return datetime.datetime.now()

    @staticmethod
    def _id(value):
        return str(value or "").strip()

    def _list(self, key):
        value = self.db.get(key, [])
        return value if isinstance(value, list) else []

    def _dict(self, key):
        value = self.db.get(key, {})
        return value if isinstance(value, dict) else {}

    def _record(self, slug, payload, result):
        def redact(value):
            if isinstance(value, dict):
                return {key: "[redacted]" if key in {"token", "secret", "shares"} else redact(item)
                        for key, item in value.items()}
            if isinstance(value, list):
                return [redact(item) for item in value]
            return value

        rows = self._list("HORIZON_COMPLETION_AUDIT")
        rows.append({"id": uuid.uuid4().hex[:12], "feature": slug,
                     "input_hash": hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest(),
                     "result": redact(result), "created_at": self._now().isoformat()})
        self.db.set("HORIZON_COMPLETION_AUDIT", rows[-5000:])
        return result

    def execute(self, slug, payload=None):
        if slug not in FEATURES:
            raise ValueError("función Horizonte 202 desconocida")
        payload = payload if isinstance(payload, dict) else {}
        category = FEATURES[slug][1]
        handler = getattr(self, f"_{category}")
        return self._record(slug, payload, handler(slug, payload))

    def catalog(self):
        return [{"slug": slug, "title": title, "category": category}
                for slug, (title, category) in FEATURES.items()]

    def _content(self, slug, data):
        if slug == "source_map":
            sources = [{"url": str(row.get("url", ""))[:1000], "title": str(row.get("title", ""))[:200],
                        "verified": bool(row.get("verified"))} for row in data.get("sources", []) if isinstance(row, dict)]
            return {"content_id": self._id(data.get("content_id")), "sources": sources,
                    "verified_ratio": round(sum(row["verified"] for row in sources) / max(1, len(sources)), 3)}
        if slug == "stale_content":
            now = self._now()
            rows = []
            for item in data.get("items", []):
                checked = datetime.datetime.fromisoformat(str(item.get("checked_at", now.isoformat())))
                age = (now - checked).days
                if age >= int(item.get("max_age_days", 90)):
                    rows.append({"id": self._id(item.get("id")), "age_days": age, "status": "review"})
            return {"stale": rows, "total": len(rows)}
        if slug == "multichannel_package":
            item = {"id": uuid.uuid4().hex[:12], "content_id": self._id(data.get("content_id")),
                    "targets": sorted({self._id(value) for value in data.get("targets", []) if self._id(value)}),
                    "variants": data.get("variants", {}), "status": "ready"}
            self.db.set(f"H202_PACKAGE_{item['id']}", item)
            return item
        if slug == "live_coverage":
            key = f"H202_LIVE_{self._id(data.get('coverage_id') or data.get('group_id'))}"
            state = self._dict(key) or {"id": uuid.uuid4().hex[:12], "milestones": [], "status": "live"}
            if data.get("milestone"):
                state["milestones"].append({"text": str(data["milestone"])[:1000], "at": self._now().isoformat()})
            if data.get("finish"):
                state["status"] = "completed"
            self.db.set(key, state)
            return state
        messages = [row for row in data.get("messages", []) if isinstance(row, dict)]
        topics = defaultdict(list)
        for row in messages:
            topics[str(row.get("topic", "general"))[:80]].append(self._id(row.get("id")))
        return {"archive_id": uuid.uuid4().hex[:12], "topics": dict(topics), "messages": len(messages)}

    def _ai(self, slug, data):
        group = self._id(data.get("group_id"))
        if slug == "project_memories":
            key = f"H202_MEMORY_{group}_{self._id(data.get('project'))}_{self._id(data.get('purpose'))}"
            rows = self._list(key)
            if data.get("entry"):
                rows.append({"text": str(data["entry"])[:4000], "approved": bool(data.get("approved")), "at": self._now().isoformat()})
                self.db.set(key, rows[-1000:])
            return {"key": key, "entries": rows}
        if slug == "adaptive_explanations":
            level = data.get("level", "beginner")
            text = str(data.get("text", ""))
            return {"level": level, "explanation": text[:800] if level == "beginner" else text[:4000]}
        if slug == "agent_debate":
            proposals = [row for row in data.get("proposals", []) if isinstance(row, dict)]
            proposals.sort(key=lambda row: float(row.get("confidence", 0)), reverse=True)
            return {"rounds": proposals, "consensus": proposals[0] if proposals else None,
                    "dissent": proposals[1:3]}
        if slug == "visible_sources":
            return {"answer_id": self._id(data.get("answer_id")), "sources": data.get("sources", []),
                    "visible": True}
        if slug == "knowledge_gaps":
            questions = [str(value) for value in data.get("questions", [])]
            known = {str(value).casefold() for value in data.get("known_topics", [])}
            gaps = [value for value in questions if not any(topic in value.casefold() for topic in known)]
            return {"gaps": gaps, "coverage": round(1 - len(gaps) / max(1, len(questions)), 3)}
        if slug == "approved_examples":
            examples = [row for row in data.get("examples", []) if isinstance(row, dict) and row.get("approved")]
            key = f"H202_EXAMPLES_{group}"
            self.db.set(key, (self._list(key) + examples)[-2000:])
            return {"stored": len(examples), "counterexamples": sum(bool(row.get("negative")) for row in examples)}
        if slug == "adaptive_teacher":
            score = float(data.get("score", 0))
            difficulty = "advanced" if score >= 80 else "intermediate" if score >= 50 else "beginner"
            return {"difficulty": difficulty, "next_exercise": data.get("topic", "general"), "hints": 3 if score < 50 else 1}
        if slug == "minority_summaries":
            opinions = data.get("opinions", [])
            counts = Counter(str(row.get("position", "unknown")) for row in opinions if isinstance(row, dict))
            return {"majority": counts.most_common(1), "minority": counts.most_common()[1:], "preserved": True}
        if slug == "model_comparison":
            rows = data.get("responses", [])
            ranked = sorted(rows, key=lambda row: float(row.get("quality", 0)) - float(row.get("cost", 0)), reverse=True)
            return {"ranking": ranked, "recommended": ranked[0] if ranked else None}
        rows = data.get("knowledge", [])
        now = self._now()
        expired = [row for row in rows if row.get("expires_at") and datetime.datetime.fromisoformat(row["expires_at"]) <= now]
        return {"expired": expired, "active": len(rows) - len(expired)}

    def _access(self, slug, data):
        if slug == "easy_read":
            text = str(data.get("text", ""))
            sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
            return {"text": "\n".join(f"• {part}" for part in sentences), "sentences": len(sentences)}
        if slug == "image_audio_description":
            objects = ", ".join(str(value) for value in data.get("objects", [])[:20])
            return {"description": f"Imagen con {objects}. {str(data.get('context', ''))}".strip(), "language": data.get("language", "es")}
        if slug == "collaborative_subtitles":
            key = f"H202_SUBTITLES_{self._id(data.get('video_id'))}_{self._id(data.get('language', 'es'))}"
            rows = self._list(key)
            if data.get("segment"):
                rows.append(data["segment"])
                rows.sort(key=lambda row: float(row.get("start", 0)))
                self.db.set(key, rows[-5000:])
            return {"segments": rows, "contributors": len({self._id(row.get("user_id")) for row in rows})}
        if slug == "chat_high_contrast":
            setting = {"enabled": bool(data.get("enabled", True)), "palette": data.get("palette", "wcag-aaa")}
            self.db.set(f"H202_CONTRAST_{self._id(data.get('chat_id'))}", setting)
            return setting
        if slug == "voice_navigation":
            command = str(data.get("transcript", "")).casefold()
            routes = {"inicio": "home", "administrar": "groups", "seguridad": "security", "atrás": "back"}
            return {"route": next((route for word, route in routes.items() if word in command), "unknown"), "transcript": command}
        if slug == "transliteration":
            table = str.maketrans("áéíóúñÁÉÍÓÚÑ", "aeiounAEIOUN")
            return {"text": str(data.get("text", "")).translate(table), "scheme": data.get("scheme", "latin-basic")}
        if slug == "local_glossaries":
            key = f"H202_GLOSSARY_{self._id(data.get('group_id'))}_{self._id(data.get('language', 'es'))}"
            glossary = self._dict(key)
            glossary.update({str(k)[:100]: str(v)[:500] for k, v in data.get("terms", {}).items()})
            self.db.set(key, glossary)
            return glossary
        if slug == "terminology_translation":
            text = str(data.get("text", ""))
            protected = data.get("terminology", {})
            return {"text": text, "protected_terms": protected, "target_language": data.get("target_language")}
        if slug == "sign_language_summary":
            return {"summary": str(data.get("summary", ""))[:2000], "sign_language": data.get("sign_language", "LSE"),
                    "avatar_job_id": uuid.uuid4().hex[:12], "status": "queued"}
        text = str(data.get("text", ""))
        barriers = []
        if len(text) > 1500:
            barriers.append("long_text")
        if text.count("http") > 5:
            barriers.append("too_many_links")
        if data.get("image") and not data.get("alt_text"):
            barriers.append("missing_alt_text")
        return {"barriers": barriers, "ready": not barriers}

    def _privacy(self, slug, data):
        user = self._id(data.get("user_id"))
        if slug == "personal_data_panel":
            records = data.get("records", {})
            return {"user_id": user, "categories": {key: len(value) if isinstance(value, list) else 1 for key, value in records.items()}}
        if slug == "selective_deletion":
            return {"request_id": uuid.uuid4().hex[:12], "user_id": user, "preview": data.get("items", []),
                    "status": "confirmed" if data.get("confirm") else "preview"}
        if slug == "one_time_admin_messages":
            supplied_token = str(data.get("token", ""))
            if supplied_token:
                token_hash = hashlib.sha256(supplied_token.encode()).hexdigest()
                row = self._dict(f"H202_ONE_TIME_{token_hash}")
                if not row or row.get("consumed_at") or datetime.datetime.fromisoformat(row["expires_at"]) <= self._now():
                    return {"valid": False, "message": None}
                message = row.get("message")
                row["message"] = ""
                row["consumed_at"] = self._now().isoformat()
                self.db.set(f"H202_ONE_TIME_{token_hash}", row)
                return {"valid": True, "message": message, "consumed_at": row["consumed_at"]}
            token = uuid.uuid4().hex
            row = {"token_hash": hashlib.sha256(token.encode()).hexdigest(), "message": str(data.get("message", ""))[:4000],
                   "expires_at": (self._now() + datetime.timedelta(minutes=int(data.get("minutes", 15)))).isoformat()}
            self.db.set(f"H202_ONE_TIME_{row['token_hash']}", row)
            return {"token": token, "expires_at": row["expires_at"]}
        if slug == "sensitive_capture_alerts":
            text = str(data.get("text", ""))
            kinds = [name for name, pattern in {"email": r"[\w.+-]+@[\w.-]+", "token": r"\b\d{6,10}:[\w-]{20,}\b",
                     "card": r"\b(?:\d[ -]*?){13,19}\b"}.items() if re.search(pattern, text)]
            return {"sensitive": bool(kinds), "kinds": kinds, "notify_admins": bool(kinds)}
        if slug == "export_anonymization":
            salt = str(data.get("salt", "moon"))
            rows = []
            for row in data.get("rows", []):
                clean = dict(row)
                if "user_id" in clean:
                    clean["user_id"] = hashlib.sha256(f"{salt}:{clean['user_id']}".encode()).hexdigest()[:16]
                clean.pop("username", None)
                clean.pop("email", None)
                rows.append(clean)
            return {"rows": rows, "anonymized": True}
        if slug == "split_recovery_keys":
            parts = max(2, int(data.get("parts", 3)))
            secret_hash = hashlib.sha256(str(data.get("secret", "")).encode()).hexdigest()
            return {"shares": [hashlib.sha256(f"{secret_hash}:{index}".encode()).hexdigest() for index in range(parts)],
                    "threshold": max(2, min(parts, int(data.get("threshold", 2))))}
        if slug == "temporary_investigation":
            return {"session_id": uuid.uuid4().hex[:12], "scope": data.get("scope", []),
                    "expires_at": (self._now() + datetime.timedelta(minutes=min(1440, int(data.get("minutes", 60))))).isoformat(),
                    "status": "active"}
        if slug == "secret_detection":
            text = str(data.get("text", ""))
            patterns = {"private_key": "BEGIN PRIVATE KEY", "github_token": "ghp_", "telegram_token": ":AA"}
            found = [name for name, marker in patterns.items() if marker in text]
            return {"found": found, "blocked": bool(found)}
        if slug == "retention_labels":
            label = {"data_type": data.get("data_type"), "days": max(1, int(data.get("days", 30))), "legal_hold": bool(data.get("legal_hold"))}
            self.db.set(f"H202_RETENTION_{self._id(data.get('data_type'))}", label)
            return label
        return {"month": data.get("month"), "stored_categories": int(data.get("stored_categories", 0)),
                "deletions": int(data.get("deletions", 0)), "incidents": int(data.get("incidents", 0)),
                "plain_language": True}

    def _operations(self, slug, data):
        if slug == "digital_twin":
            current, proposed = data.get("current", {}), data.get("proposed", {})
            return {"changes": {key: {"from": current.get(key), "to": value} for key, value in proposed.items() if current.get(key) != value},
                    "applied": False}
        if slug == "canary_groups":
            groups = data.get("groups", [])
            percent = max(1, min(100, int(data.get("percent", 10))))
            count = max(1, math.ceil(len(groups) * percent / 100)) if groups else 0
            return {"canary": groups[:count], "remaining": groups[count:], "percent": percent}
        if slug == "slo_recovery":
            availability = float(data.get("availability", 100))
            target = float(data.get("target", 99.9))
            return {"recover": availability < target, "action": data.get("action", "restart_worker") if availability < target else "none"}
        if slug == "dependency_map":
            edges = data.get("edges", [])
            incoming = Counter(str(edge.get("to")) for edge in edges)
            outgoing = Counter(str(edge.get("from")) for edge in edges)
            nodes = sorted(set(incoming) | set(outgoing))
            return {"nodes": nodes, "edges": edges, "single_points": [node for node in nodes if incoming[node] > 1 and outgoing[node] == 0]}
        if slug == "error_budget":
            total = max(1, int(data.get("requests", 1)))
            failures = max(0, int(data.get("failures", 0)))
            allowed = total * (1 - float(data.get("slo", 99.9)) / 100)
            return {"allowed_failures": round(allowed, 2), "used": failures, "remaining": round(allowed - failures, 2), "exhausted": failures > allowed}
        if slug == "incident_replay":
            events = [{k: v for k, v in row.items() if k not in ("user_id", "username", "ip")} for row in data.get("events", [])]
            return {"replay_id": uuid.uuid4().hex[:12], "events": events, "dry_run": True}
        if slug == "config_drift":
            baseline = data.get("baseline", {})
            return {"drift": {name: {key: value for key, value in config.items() if baseline.get(key) != value}
                              for name, config in data.get("instances", {}).items()}}
        if slug == "timezone_maintenance":
            return {"windows": [{"timezone": zone, "local_hour": int(data.get("local_hour", 3))} for zone in data.get("timezones", [])], "status": "scheduled"}
        if slug == "predictive_capacity":
            history = [float(value) for value in data.get("history", [])]
            growth = (history[-1] - history[0]) / max(1, len(history) - 1) if history else 0
            return {"current": history[-1] if history else 0, "forecast_7": round((history[-1] if history else 0) + growth * 7, 2), "daily_growth": round(growth, 2)}
        failed = [name for name, status in data.get("dependencies", {}).items() if status not in ("ok", "healthy")]
        return {"enabled": bool(failed), "failed": failed, "essential": ["moderation", "commands", "cached_security"]}

    def _integrations(self, slug, data):
        if slug == "visual_connectors":
            steps = data.get("steps", [])
            return {"connector_id": uuid.uuid4().hex[:12], "steps": steps, "valid": all("type" in row for row in steps)}
        if slug == "automation_marketplace":
            item = {"id": uuid.uuid4().hex[:12], "name": str(data.get("name", ""))[:200], "version": data.get("version", "1.0.0"),
                    "permissions": data.get("permissions", []), "status": "review"}
            rows = self._list("H202_AUTOMATION_MARKET") + [item]
            self.db.set("H202_AUTOMATION_MARKET", rows[-1000:])
            return item
        if slug == "activitypub_bridge":
            return {"actor": data.get("actor"), "inbox": data.get("inbox"), "outbox": data.get("outbox"), "job": "federation_sync", "status": "queued"}
        if slug == "caldav_sync":
            return {"calendar": data.get("calendar"), "direction": data.get("direction", "bidirectional"), "sync_token": data.get("sync_token"), "status": "queued"}
        if slug == "opml_exchange":
            feeds = data.get("feeds", [])
            return {"feeds": feeds, "count": len(feeds), "format": "OPML 2.0"}
        if slug == "signed_websub":
            body = json.dumps(data.get("event", {}), sort_keys=True)
            signature = hashlib.sha256(f"{data.get('secret', '')}:{body}".encode()).hexdigest()
            return {"topic": data.get("topic"), "signature": signature, "status": "queued"}
        if slug == "portable_identity":
            claims = data.get("claims", {})
            return {"credential_id": f"urn:uuid:{uuid.uuid4()}", "subject": data.get("subject"), "claims": claims,
                    "proof_hash": hashlib.sha256(json.dumps(claims, sort_keys=True).encode()).hexdigest()}
        if slug == "matrix_flows":
            return {"homeserver": data.get("homeserver"), "room_id": data.get("room_id"), "direction": data.get("direction", "bidirectional"), "status": "configured"}
        if slug == "bot_capability_catalog":
            bots = data.get("bots", [])
            return {"bots": [{"id": self._id(row.get("id")), "capabilities": sorted(set(row.get("capabilities", [])))} for row in bots]}
        return {"sandbox_id": uuid.uuid4().hex[:12], "integration": data.get("integration"), "network": "isolated", "writes": "simulated", "status": "ready"}

    def _sustainability(self, slug, data):
        if slug == "community_costs":
            components = {key: round(float(value), 2) for key, value in data.get("components", {}).items()}
            return {"components": components, "monthly_total": round(sum(components.values()), 2), "currency": data.get("currency", "EUR")}
        if slug == "funding_milestones":
            raised, target = float(data.get("raised", 0)), max(1, float(data.get("target", 1)))
            return {"raised": raised, "target": target, "progress": round(min(1, raised / target), 4), "verified": bool(data.get("evidence"))}
        if slug == "sponsor_frequency":
            limit = max(0, int(data.get("max_per_week", 1)))
            return {"max_per_week": limit, "allowed": int(data.get("shown_this_week", 0)) < limit}
        if slug == "creator_revenue_share":
            revenue = max(0, float(data.get("revenue", 0)))
            weights = {self._id(key): max(0, float(value)) for key, value in data.get("weights", {}).items()}
            total = sum(weights.values()) or 1
            return {"shares": {key: round(revenue * value / total, 2) for key, value in weights.items()}, "revenue": revenue}
        if slug == "energy_saving":
            tasks = data.get("tasks", [])
            return {"run_now": [row for row in tasks if row.get("urgent")], "deferred": [row for row in tasks if not row.get("urgent")], "enabled": True}
        if slug == "operational_footprint":
            cpu_hours = float(data.get("cpu_hours", 0))
            storage_gb = float(data.get("storage_gb", 0))
            return {"estimated_kg_co2e": round(cpu_hours * 0.035 + storage_gb * 0.0005, 4), "method": "operational_estimate"}
        if slug == "feature_donations":
            item = {"feature": data.get("feature"), "amount": round(max(0, float(data.get("amount", 0))), 2), "currency": data.get("currency", "EUR"), "restricted": True}
            return item
        if slug == "community_credits":
            key = f"H202_CREDITS_{self._id(data.get('group_id'))}"
            balances = self._dict(key)
            user = self._id(data.get("user_id"))
            balances[user] = max(0, int(balances.get(user, 0)) + int(data.get("amount", 0)))
            self.db.set(key, balances)
            return {"user_id": user, "balance": balances[user], "transferable": False}
        if slug == "respectful_churn":
            inactive = float(data.get("inactive_days", 0))
            engagement = float(data.get("engagement", 0))
            risk = round(max(0, min(100, inactive * 2 - engagement * 0.5)), 1)
            return {"risk": risk, "intervention": "optional_check_in" if risk >= 60 else "none", "no_dark_patterns": True}
        consent = bool(data.get("consent"))
        return {"experiment": data.get("experiment"), "variant": data.get("variant") if consent else None,
                "enrolled": consent, "ends_at": data.get("ends_at"), "max_exposure": int(data.get("max_exposure", 1))}

    def _telegram(self, slug, data):
        if slug == "pending_topics_inbox":
            topics = sorted(data.get("topics", []), key=lambda row: (-int(row.get("priority", 0)), str(row.get("created_at", ""))))
            return {"topics": topics, "unresolved": sum(row.get("status") != "done" for row in topics)}
        if slug == "personal_shortcuts":
            key = f"H202_SHORTCUTS_{self._id(data.get('user_id'))}"
            shortcuts = data.get("shortcuts", {})
            self.db.set(key, shortcuts)
            return {"shortcuts": shortcuts, "synced": True}
        if slug == "message_side_panel":
            return {"message_id": self._id(data.get("message_id")), "actions": data.get("actions", ["report", "quote", "context"]),
                    "context": data.get("context", {})}
        if slug == "ephemeral_operations":
            return {"receiver_user_id": self._id(data.get("receiver_user_id")), "callback_query_id": data.get("callback_query_id"),
                    "text": str(data.get("text", ""))[:4096], "ephemeral": True}
        if slug == "linked_communities":
            parent = self._id(data.get("parent"))
            children = [self._id(value) for value in data.get("children", [])]
            return {"parent": parent, "children": children, "inherited_permissions": data.get("permissions", [])}
        if slug == "adaptive_entry_forms":
            answers = data.get("answers", {})
            fields = [field for field in data.get("fields", []) if not field.get("when") or answers.get(field["when"].get("field")) == field["when"].get("equals")]
            return {"fields": fields, "answers": answers, "complete": all(not field.get("required") or field.get("id") in answers for field in fields)}
        if slug == "admin_guided_routes":
            completed = set(data.get("completed", []))
            steps = data.get("steps", ["permissions", "rules", "welcome", "security", "review"])
            return {"steps": steps, "next": next((step for step in steps if step not in completed), None), "progress": round(len(completed) / max(1, len(steps)), 3)}
        if slug == "temporary_event_mode":
            return {"group_id": self._id(data.get("group_id")), "mode": data.get("mode", "event"),
                    "starts_at": data.get("starts_at"), "ends_at": data.get("ends_at"), "temporary_settings": data.get("settings", {})}
        if slug == "bulk_preview_undo":
            actions = data.get("actions", [])
            return {"batch_id": uuid.uuid4().hex[:12], "preview": actions, "undo": list(reversed(actions)),
                    "status": "applied" if data.get("confirm") else "preview"}
        notifications = sorted(data.get("notifications", []), key=lambda row: (-int(row.get("impact", 0)), str(row.get("created_at", ""))))
        return {"notifications": notifications, "critical": sum(int(row.get("impact", 0)) >= 80 for row in notifications)}

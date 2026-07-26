"""Servicios persistentes para el roadmap avanzado de Moonbot.

El motor no depende de Flask ni de Telegram: expone operaciones deterministas,
auditables y reutilizables por el bot, la web clásica y la Mini App.
"""

import datetime
import hashlib
import hmac
import json
import secrets
import uuid
from collections import Counter, defaultdict
from urllib.parse import urlparse


class RoadmapEngine:
    def __init__(self, db, secret="moonbot"):
        self.db = db
        self.secret = str(secret or "moonbot").encode()

    @staticmethod
    def _now():
        return datetime.datetime.now()

    @staticmethod
    def _id(value):
        return str(value).strip()

    def _list(self, key):
        value = self.db.get(key, [])
        return value if isinstance(value, list) else []

    def _dict(self, key):
        value = self.db.get(key, {})
        return value if isinstance(value, dict) else {}

    def _append(self, key, item, limit=5000):
        rows = self._list(key)
        rows.append(item)
        self.db.set(key, rows[-limit:])
        return item

    def _record(self, category, action, payload):
        return self._append("ROADMAP_AUDIT", {
            "id": uuid.uuid4().hex[:12], "category": category, "action": action,
            "payload": payload, "created_at": self._now().isoformat(),
        })

    # 2–6 · Moderación y seguridad
    def raid_signal(self, group_id, joins, messages, unique_users, window=60):
        score = min(100, round(joins * 3 + messages * 0.3 + max(0, joins - unique_users) * 5))
        row = {"group_id": self._id(group_id), "joins": int(joins), "messages": int(messages),
               "unique_users": int(unique_users), "window": int(window), "risk": score,
               "created_at": self._now().isoformat()}
        self._append("SECURITY_RAID_SIGNALS", row)
        recent = [x for x in self._list("SECURITY_RAID_SIGNALS")
                  if (self._now() - datetime.datetime.fromisoformat(x["created_at"])).total_seconds() <= 600]
        coordinated = len({x["group_id"] for x in recent if x["risk"] >= 60}) >= 2
        return {**row, "coordinated": coordinated, "affected_groups": sorted({x["group_id"] for x in recent if x["risk"] >= 60})}

    def quarantine_decision(self, user_id, reputation, signals=None):
        signals = signals or {}
        risk = max(0, min(100, 50 - int(reputation) + int(signals.get("raid", 0)) +
                          int(signals.get("spam", 0)) + int(signals.get("cas", 0))))
        level = "strict" if risk >= 75 else "review" if risk >= 40 else "none"
        return {"user_id": self._id(user_id), "risk": risk, "level": level,
                "restrictions": ["media", "links", "forwarding"] if level == "strict" else ["links"] if level == "review" else []}

    def shared_recurrence(self, user_id, requesting_group, authorized_groups):
        allowed = {self._id(x) for x in authorized_groups}
        sanctions = self._list("SHARED_SANCTIONS")
        matches = [x for x in sanctions if self._id(x.get("user_id")) == self._id(user_id)
                   and self._id(x.get("group_id")) in allowed]
        result = {"user_id": self._id(user_id), "requesting_group": self._id(requesting_group),
                  "authorized_groups": sorted(allowed), "incidents": len(matches),
                  "severity": "high" if len(matches) >= 3 else "medium" if matches else "none",
                  "records": matches[-20:]}
        self._record("security", "shared_recurrence", {k: v for k, v in result.items() if k != "records"})
        return result

    # Horizonte 202 · primera fase operativa
    def conversation_escalation(self, group_id, samples, window_seconds=300):
        rows = [x for x in (samples or []) if isinstance(x, dict)][-200:]
        messages = len(rows)
        users = len({self._id(x.get("user_id")) for x in rows if x.get("user_id") is not None})
        negative = sum(float(x.get("negative", x.get("toxicity", 0)) or 0) for x in rows)
        caps = sum(str(x.get("text", "")).isupper() and len(str(x.get("text", ""))) >= 8 for x in rows)
        reports = sum(bool(x.get("reported")) for x in rows)
        pace = round(messages * 60 / max(1, int(window_seconds)), 2)
        score = min(100, round(pace * 1.5 + negative * 12 + caps * 4 + reports * 12))
        level = "critical" if score >= 75 else "watch" if score >= 40 else "calm"
        result = {"group_id": self._id(group_id), "score": score, "level": level,
                  "messages": messages, "users": users, "messages_per_minute": pace,
                  "signals": {"negative": round(negative, 2), "caps": caps, "reports": reports},
                  "recommended_action": "activate_mediator" if score >= 75 else "notify_admins" if score >= 40 else "none",
                  "created_at": self._now().isoformat()}
        self._append("H202_ESCALATION_RADAR", result, 1000)
        return result

    def mediator_session(self, group_id, action, user_id=None, statement=None):
        key = self._id(group_id)
        sessions = self._dict("H202_MEDIATOR_SESSIONS")
        session = sessions.get(key)
        if action == "start":
            session = {"group_id": key, "status": "active", "queue": [], "turns": [],
                       "started_at": self._now().isoformat()}
        elif not session:
            raise ValueError("no existe una sesión de mediación activa")
        elif action == "join":
            uid = self._id(user_id)
            if not uid:
                raise ValueError("user_id requerido")
            if uid not in session["queue"]:
                session["queue"].append(uid)
        elif action == "turn":
            uid = self._id(user_id)
            if not session["queue"] or session["queue"][0] != uid:
                raise ValueError("no es el turno de ese usuario")
            session["turns"].append({"user_id": uid, "statement": str(statement or "")[:2000],
                                     "created_at": self._now().isoformat()})
            session["queue"] = session["queue"][1:] + [uid]
        elif action == "close":
            session["status"] = "closed"; session["closed_at"] = self._now().isoformat()
        else:
            raise ValueError("acción de mediación inválida")
        sessions[key] = session; self.db.set("H202_MEDIATOR_SESSIONS", sessions)
        return session

    def domain_quarantine(self, url, domain_age_days=None, trusted_domains=None, minimum_age_days=30):
        parsed = urlparse(str(url or "").strip())
        domain = (parsed.hostname or "").casefold().rstrip(".")
        if parsed.scheme not in ("http", "https") or not domain:
            raise ValueError("URL HTTP/HTTPS inválida")
        trusted = {str(x).casefold().rstrip(".") for x in (trusted_domains or [])}
        age = int(domain_age_days) if domain_age_days is not None else None
        quarantined = domain not in trusted and (age is None or age < int(minimum_age_days))
        result = {"url": str(url), "domain": domain, "domain_age_days": age,
                  "minimum_age_days": int(minimum_age_days), "trusted": domain in trusted,
                  "quarantined": quarantined,
                  "reason": "edad desconocida" if quarantined and age is None else "dominio reciente" if quarantined else "permitido"}
        self._record("security", "domain_quarantine", result)
        return result

    def peer_review(self, action, case_id=None, reviewer_id=None, verdict=None, payload=None, quorum=3):
        cases = self._dict("H202_PEER_REVIEWS")
        if action == "create":
            case_id = uuid.uuid4().hex[:12]
            cases[case_id] = {"id": case_id, "payload": payload or {}, "status": "review",
                              "votes": {}, "quorum": max(2, int(quorum)), "created_at": self._now().isoformat()}
        else:
            case_id = self._id(case_id); case = cases.get(case_id)
            if not case:
                raise ValueError("caso no encontrado")
            if action == "vote":
                if verdict not in ("confirm", "dismiss", "abstain"):
                    raise ValueError("veredicto inválido")
                case["votes"][self._id(reviewer_id)] = verdict
                decisive = [v for v in case["votes"].values() if v != "abstain"]
                if len(decisive) >= case["quorum"]:
                    case["status"] = "confirmed" if decisive.count("confirm") > decisive.count("dismiss") else "dismissed"
                    case["resolved_at"] = self._now().isoformat()
            elif action != "get":
                raise ValueError("acción de revisión inválida")
        self.db.set("H202_PEER_REVIEWS", cases)
        return cases[case_id]

    def rule_impact_simulation(self, group_id, rule, samples):
        rule = rule or {}; action = str(rule.get("action", "notify"))
        keyword = str(rule.get("keyword", "")).casefold().strip()
        minimum_score = float(rule.get("minimum_score", 0) or 0)
        matches = []
        for index, sample in enumerate((samples or [])[:1000]):
            item = sample if isinstance(sample, dict) else {"text": str(sample)}
            text = str(item.get("text", ""))
            if (not keyword or keyword in text.casefold()) and float(item.get("score", 0) or 0) >= minimum_score:
                matches.append({"index": index, "preview": text[:120], "user_id": item.get("user_id")})
        total = len(samples or [])
        result = {"group_id": self._id(group_id), "rule": rule, "action": action,
                  "sample_size": total, "matches": len(matches),
                  "impact_percent": round(len(matches) * 100 / max(1, total), 1),
                  "examples": matches[:20], "safe_to_apply": action != "ban" or len(matches) <= max(3, total * 0.1)}
        self._append("H202_RULE_SIMULATIONS", result, 500)
        return result

    def coordinated_brigade(self, events, minimum_groups=2, minimum_users=3):
        campaigns = defaultdict(lambda: {"groups": set(), "users": set(), "events": 0})
        for event in (events or [])[-2000:]:
            if not isinstance(event, dict):
                continue
            fingerprint = str(event.get("fingerprint") or event.get("url") or event.get("phrase") or "").casefold().strip()
            if not fingerprint:
                continue
            row = campaigns[hashlib.sha256(fingerprint.encode()).hexdigest()[:12]]
            row["groups"].add(self._id(event.get("group_id")))
            row["users"].add(self._id(event.get("user_id")))
            row["events"] += 1
        matches = [{"fingerprint": key, "groups": sorted(x for x in row["groups"] if x),
                    "users": sorted(x for x in row["users"] if x), "events": row["events"]}
                   for key, row in campaigns.items()
                   if len({x for x in row["groups"] if x}) >= int(minimum_groups)
                   and len({x for x in row["users"] if x}) >= int(minimum_users)]
        result = {"coordinated": bool(matches), "campaigns": matches,
                  "events_analyzed": len(events or []), "created_at": self._now().isoformat()}
        self._append("H202_BRIGADE_SCANS", result, 500)
        return result

    def reputation_passport(self, user_id, metrics, consent=False):
        if not consent:
            raise ValueError("se requiere consentimiento explícito del usuario")
        safe = {key: max(0, int((metrics or {}).get(key, 0)))
                for key in ("helpful", "verified", "participation", "sanctions")}
        score = max(0, min(100, safe["helpful"] * 2 + safe["verified"] * 5 +
                           safe["participation"] - safe["sanctions"] * 15))
        payload = {"subject": self._id(user_id), "score": score, "metrics": safe,
                   "issued_at": self._now().isoformat(), "version": 1}
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return {"passport": payload, "signature": hmac.new(self.secret, raw.encode(), hashlib.sha256).hexdigest()}

    def voice_clone_risk(self, features):
        features = features or {}
        weights = {"synthetic_probability": 45, "speaker_mismatch": 25,
                   "replay_probability": 15, "metadata_anomaly": 15}
        contributions = {key: round(max(0, min(1, float(features.get(key, 0) or 0))) * weight, 2)
                         for key, weight in weights.items()}
        score = min(100, round(sum(contributions.values())))
        return {"score": score, "risk": "high" if score >= 70 else "review" if score >= 35 else "low",
                "signals": contributions, "human_review_required": score >= 35,
                "note": "Resultado orientativo; no identifica por sí solo una clonación."}

    def incident_timeline(self, group_id, action="list", event=None):
        key = f"H202_INCIDENT_TIMELINE_{self._id(group_id)}"
        rows = self._list(key)
        if action == "add":
            event = event or {}
            row = {"id": uuid.uuid4().hex[:12], "kind": str(event.get("kind", "note"))[:50],
                   "title": str(event.get("title", "Incidente"))[:300],
                   "detail": str(event.get("detail", ""))[:2000],
                   "severity": str(event.get("severity", "info"))[:20],
                   "occurred_at": event.get("occurred_at") or self._now().isoformat()}
            rows.append(row); self.db.set(key, rows[-1000:])
        elif action != "list":
            raise ValueError("acción de cronología inválida")
        return {"group_id": self._id(group_id), "events": sorted(rows, key=lambda x: x.get("occurred_at", ""))}

    def evidence_chain(self, case_id, action="append", evidence=None):
        key = f"H202_EVIDENCE_CHAIN_{self._id(case_id)}"
        chain = self._list(key)
        if action == "append":
            evidence = evidence or {}
            previous = chain[-1]["hash"] if chain else "GENESIS"
            payload = {"type": str(evidence.get("type", "note"))[:50],
                       "reference": str(evidence.get("reference", ""))[:1000],
                       "digest": str(evidence.get("digest", ""))[:200],
                       "created_at": self._now().isoformat()}
            digest = hashlib.sha256((previous + json.dumps(payload, sort_keys=True, separators=(",", ":"))).encode()).hexdigest()
            chain.append({"index": len(chain), "previous_hash": previous, "hash": digest, "evidence": payload})
            self.db.set(key, chain[-1000:])
        elif action != "verify":
            raise ValueError("acción de evidencia inválida")
        valid = True; previous = "GENESIS"
        for index, item in enumerate(chain):
            expected = hashlib.sha256((previous + json.dumps(item["evidence"], sort_keys=True, separators=(",", ":"))).encode()).hexdigest()
            if item.get("index") != index or item.get("previous_hash") != previous or item.get("hash") != expected:
                valid = False; break
            previous = item["hash"]
        return {"case_id": self._id(case_id), "valid": valid, "entries": len(chain), "chain": chain}

    # Horizonte 202 · comunidad y participación
    def assembly(self, group_id, action, assembly_id=None, actor_id=None, data=None):
        assemblies = self._dict("H202_ASSEMBLIES"); data = data or {}
        if action == "create":
            assembly_id = uuid.uuid4().hex[:12]
            assemblies[assembly_id] = {"id": assembly_id, "group_id": self._id(group_id),
                "title": str(data.get("title", "Asamblea"))[:300], "status": "open",
                "proposals": [], "created_by": self._id(actor_id), "created_at": self._now().isoformat()}
        else:
            assembly_id = self._id(assembly_id); item = assemblies.get(assembly_id)
            if not item or item["group_id"] != self._id(group_id): raise ValueError("asamblea no encontrada")
            if action in ("proposal", "amendment"):
                item["proposals"].append({"id": uuid.uuid4().hex[:10], "type": action,
                    "parent_id": data.get("parent_id"), "text": str(data.get("text", ""))[:2000],
                    "author_id": self._id(actor_id), "votes": {}})
            elif action == "vote":
                proposal = next((x for x in item["proposals"] if x["id"] == self._id(data.get("proposal_id"))), None)
                if not proposal or data.get("vote") not in ("yes", "no", "abstain"): raise ValueError("voto o propuesta inválidos")
                proposal["votes"][self._id(actor_id)] = data["vote"]
            elif action == "close": item["status"] = "closed"; item["closed_at"] = self._now().isoformat()
            elif action != "get": raise ValueError("acción de asamblea inválida")
        self.db.set("H202_ASSEMBLIES", assemblies); return assemblies[assembly_id]

    def participatory_budget(self, group_id, action, budget_id=None, user_id=None, data=None):
        budgets = self._dict("H202_BUDGETS"); data = data or {}
        if action == "create":
            budget_id = uuid.uuid4().hex[:12]
            budgets[budget_id] = {"id": budget_id, "group_id": self._id(group_id),
                "amount": max(0, float(data.get("amount", 0))), "projects": data.get("projects") or [],
                "allocations": {}, "status": "open"}
        else:
            budget_id = self._id(budget_id); budget = budgets.get(budget_id)
            if not budget or budget["group_id"] != self._id(group_id): raise ValueError("presupuesto no encontrado")
            if action == "allocate":
                allocations = {str(k): max(0, float(v)) for k, v in (data.get("allocations") or {}).items()}
                weight = max(0.1, min(5, float(data.get("weight", 1))))
                if sum(allocations.values()) > 100: raise ValueError("la asignación supera 100 puntos")
                budget["allocations"][self._id(user_id)] = {"points": allocations, "weight": weight}
            elif action == "close": budget["status"] = "closed"
            elif action != "get": raise ValueError("acción presupuestaria inválida")
        budget = budgets[budget_id]; totals = Counter()
        for vote in budget["allocations"].values():
            for project, points in vote["points"].items(): totals[project] += points * vote["weight"]
        budget["ranking"] = [{"project": k, "score": round(v, 2)} for k, v in totals.most_common()]
        self.db.set("H202_BUDGETS", budgets); return budget

    def interest_circle(self, group_id, action, circle_id=None, user_id=None, data=None):
        circles = self._dict("H202_INTEREST_CIRCLES"); data = data or {}
        if action == "create":
            circle_id = uuid.uuid4().hex[:12]; expires = self._now() + datetime.timedelta(days=max(1, int(data.get("days", 30))))
            circles[circle_id] = {"id": circle_id, "group_id": self._id(group_id),
                "topic": str(data.get("topic", "Interés"))[:200], "members": [], "expires_at": expires.isoformat(), "status": "active"}
        else:
            circle_id = self._id(circle_id); circle = circles.get(circle_id)
            if not circle or circle["group_id"] != self._id(group_id): raise ValueError("círculo no encontrado")
            if action == "join" and self._id(user_id) not in circle["members"]: circle["members"].append(self._id(user_id))
            elif action == "leave": circle["members"] = [x for x in circle["members"] if x != self._id(user_id)]
            elif action == "close": circle["status"] = "closed"
            elif action not in ("join", "get"): raise ValueError("acción de círculo inválida")
        self.db.set("H202_INTEREST_CIRCLES", circles); return circles[circle_id]

    def time_bank(self, group_id, action, user_id=None, target_id=None, hours=0, note=""):
        key = f"H202_TIME_BANK_{self._id(group_id)}"; state = self._dict(key)
        balances, ledger = state.get("balances", {}), state.get("ledger", [])
        amount = round(float(hours), 2)
        if action == "credit": balances[self._id(user_id)] = round(float(balances.get(self._id(user_id), 0)) + max(0, amount), 2)
        elif action == "transfer":
            source, target = self._id(user_id), self._id(target_id)
            if amount <= 0 or float(balances.get(source, 0)) < amount: raise ValueError("saldo u horas insuficientes")
            balances[source] = round(float(balances[source]) - amount, 2); balances[target] = round(float(balances.get(target, 0)) + amount, 2)
        elif action != "balance": raise ValueError("acción de banco de tiempo inválida")
        if action != "balance": ledger.append({"action": action, "from": self._id(user_id), "to": self._id(target_id), "hours": amount, "note": str(note)[:500], "created_at": self._now().isoformat()})
        state = {"balances": balances, "ledger": ledger[-1000:]}; self.db.set(key, state); return state

    def welcome_round(self, group_id, member_id, hosts, capacity=3):
        hosts = [self._id(x) for x in hosts if self._id(x)]
        rounds = self._list(f"H202_WELCOME_ROUNDS_{self._id(group_id)}")
        recent = Counter(x.get("host_id") for x in rounds[-100:])
        available = [x for x in hosts if recent[x] < max(1, int(capacity))]
        host = min(available or hosts, key=lambda x: recent[x], default=None)
        row = {"id": uuid.uuid4().hex[:12], "member_id": self._id(member_id), "host_id": host,
               "status": "assigned" if host else "waiting", "created_at": self._now().isoformat()}
        self._append(f"H202_WELCOME_ROUNDS_{self._id(group_id)}", row, 1000); return row

    def collaborative_mission(self, operation, group_ids=None, mission_id=None, user_id=None,
                              title="", target=1, progress=0):
        rows = self._list("H202_COLLABORATIVE_MISSIONS")
        if operation == "create":
            groups = sorted({self._id(value) for value in (group_ids or []) if self._id(value)})
            if len(groups) < 2:
                raise ValueError("una misión colaborativa necesita al menos dos grupos")
            item = {"id": uuid.uuid4().hex[:12], "title": str(title)[:200], "groups": groups,
                    "target": max(1, int(target)), "progress": 0, "participants": [],
                    "status": "active", "created_at": self._now().isoformat()}
            rows.append(item)
        else:
            item = next((row for row in rows if row.get("id") == mission_id), None)
            if not item:
                return None
            if operation == "join":
                participant = self._id(user_id)
                if participant and participant not in item["participants"]:
                    item["participants"].append(participant)
            elif operation == "progress":
                item["progress"] = min(item["target"], item["progress"] + max(0, int(progress)))
                if item["progress"] >= item["target"]:
                    item["status"] = "completed"
                    item["completed_at"] = self._now().isoformat()
            elif operation != "status":
                raise ValueError("operación de misión inválida")
        self.db.set("H202_COLLABORATIVE_MISSIONS", rows[-500:])
        return item

    def invisible_contributions(self, group_id, events):
        weights = {"welcome": 3, "report": 2, "answer": 2, "mediation": 5, "resource": 3}
        scores = defaultdict(lambda: {"score": 0, "actions": 0, "kinds": Counter()})
        for event in (events or [])[-2000:]:
            if not isinstance(event, dict):
                continue
            user = self._id(event.get("user_id"))
            kind = str(event.get("kind", "other"))[:30]
            if not user:
                continue
            scores[user]["score"] += weights.get(kind, 1)
            scores[user]["actions"] += 1
            scores[user]["kinds"][kind] += 1
        ranking = [{"user_id": user, "score": value["score"], "actions": value["actions"],
                    "kinds": dict(value["kinds"])} for user, value in scores.items()]
        ranking.sort(key=lambda row: (-row["score"], row["user_id"]))
        result = {"group_id": self._id(group_id), "ranking": ranking[:100],
                  "calculated_at": self._now().isoformat()}
        self.db.set(f"H202_INVISIBLE_CONTRIBUTIONS_{self._id(group_id)}", result)
        return result

    def social_health(self, group_id, metrics):
        values = {"participation": float(metrics.get("participation", 0)),
                  "retention": float(metrics.get("retention", 0)),
                  "response_rate": float(metrics.get("response_rate", 0)),
                  "conflict_rate": float(metrics.get("conflict_rate", 0)),
                  "moderator_load": float(metrics.get("moderator_load", 0))}
        positive = (values["participation"] + values["retention"] + values["response_rate"]) / 3
        pressure = (values["conflict_rate"] + values["moderator_load"]) / 2
        score = round(max(0, min(100, positive * 0.75 + (100 - pressure) * 0.25)), 1)
        result = {"group_id": self._id(group_id), "score": score,
                  "level": "healthy" if score >= 75 else "watch" if score >= 50 else "attention",
                  "metrics": values, "privacy": "aggregate_only", "calculated_at": self._now().isoformat()}
        self.db.set(f"H202_SOCIAL_HEALTH_{self._id(group_id)}", result)
        return result

    def admin_relay(self, group_id, operation, outgoing_id=None, incoming_id=None,
                    starts_at=None, ends_at=None, relay_id=None):
        key = f"H202_ADMIN_RELAYS_{self._id(group_id)}"
        rows = self._list(key)
        if operation == "create":
            item = {"id": uuid.uuid4().hex[:12], "outgoing_id": self._id(outgoing_id),
                    "incoming_id": self._id(incoming_id), "starts_at": str(starts_at or self._now().isoformat()),
                    "ends_at": str(ends_at or ""), "status": "pending", "checklist": [],
                    "created_at": self._now().isoformat()}
            rows.append(item)
        else:
            item = next((row for row in rows if row.get("id") == relay_id), None)
            if not item:
                return None
            if operation == "accept":
                item["status"] = "scheduled"
                item["accepted_at"] = self._now().isoformat()
            elif operation == "complete":
                item["status"] = "completed"
                item["completed_at"] = self._now().isoformat()
            elif operation != "status":
                raise ValueError("operación de relevo inválida")
        self.db.set(key, rows[-500:])
        return item

    def annual_memory(self, group_id, year, highlights=None, metrics=None, contributors=None):
        year = int(year)
        if year < 2000 or year > self._now().year:
            raise ValueError("año fuera de rango")
        item = {"group_id": self._id(group_id), "year": year,
                "highlights": [str(value)[:300] for value in (highlights or [])[:50]],
                "metrics": {str(key)[:50]: value for key, value in (metrics or {}).items()},
                "contributors": [self._id(value) for value in (contributors or [])[:100]],
                "privacy": "community_approved_content_only", "generated_at": self._now().isoformat()}
        self.db.set(f"H202_ANNUAL_MEMORY_{self._id(group_id)}_{year}", item)
        return item

    def editorial_series(self, operation, series_id=None, title="", description="",
                         content_id=None, position=None):
        rows = self._list("H202_EDITORIAL_SERIES")
        if operation == "create":
            item = {"id": uuid.uuid4().hex[:12], "title": str(title)[:200],
                    "description": str(description)[:1000], "items": [], "status": "draft",
                    "created_at": self._now().isoformat()}
            rows.append(item)
        else:
            item = next((row for row in rows if row.get("id") == series_id), None)
            if not item:
                return None
            if operation == "add":
                entry = {"content_id": self._id(content_id), "position": int(position or len(item["items"]) + 1)}
                item["items"] = [row for row in item["items"] if row.get("content_id") != entry["content_id"]]
                item["items"].append(entry)
                item["items"].sort(key=lambda row: row["position"])
            elif operation in ("publish", "archive"):
                item["status"] = "published" if operation == "publish" else "archived"
                item["updated_at"] = self._now().isoformat()
            elif operation != "status":
                raise ValueError("operación de serie editorial inválida")
        self.db.set("H202_EDITORIAL_SERIES", rows[-500:])
        return item

    def content_reuse_candidates(self, items, minimum_age_days=30, limit=20):
        candidates = []
        for item in (items or [])[-2000:]:
            if not isinstance(item, dict):
                continue
            age = max(0, int(item.get("age_days", 0)))
            if age < int(minimum_age_days):
                continue
            engagement = max(0, min(100, float(item.get("engagement", 0))))
            evergreen = 20 if item.get("evergreen") else 0
            stale_penalty = min(30, max(0, age - 365) / 30)
            score = round(max(0, min(100, engagement * 0.7 + evergreen + 15 - stale_penalty)), 1)
            candidates.append({"content_id": self._id(item.get("id")), "title": str(item.get("title", ""))[:200],
                               "age_days": age, "reuse_score": score,
                               "recommendation": "refresh" if age > 365 else "republish"})
        candidates.sort(key=lambda row: (-row["reuse_score"], -row["age_days"]))
        result = {"candidates": candidates[:max(1, min(100, int(limit)))],
                  "calculated_at": self._now().isoformat()}
        self.db.set("H202_CONTENT_REUSE_LAST", result)
        return result

    def silence_calendar(self, group_id, operation, starts_at=None, ends_at=None,
                         reason="", window_id=None, check_at=None):
        key = f"H202_SILENCE_CALENDAR_{self._id(group_id)}"
        rows = self._list(key)
        if operation == "create":
            start = datetime.datetime.fromisoformat(str(starts_at))
            end = datetime.datetime.fromisoformat(str(ends_at))
            if end <= start:
                raise ValueError("el silencio debe terminar después de comenzar")
            item = {"id": uuid.uuid4().hex[:12], "starts_at": start.isoformat(), "ends_at": end.isoformat(),
                    "reason": str(reason)[:300], "status": "scheduled"}
            rows.append(item)
            self.db.set(key, rows[-500:])
            return item
        if operation == "cancel":
            item = next((row for row in rows if row.get("id") == window_id), None)
            if not item:
                return None
            item["status"] = "cancelled"
            self.db.set(key, rows[-500:])
            return item
        if operation != "check":
            raise ValueError("operación de calendario de silencios inválida")
        moment = datetime.datetime.fromisoformat(str(check_at)) if check_at else self._now()
        active = [row for row in rows if row.get("status") == "scheduled"
                  and datetime.datetime.fromisoformat(row["starts_at"]) <= moment
                  < datetime.datetime.fromisoformat(row["ends_at"])]
        return {"group_id": self._id(group_id), "can_publish": not active, "active_windows": active}

    def compare_headlines(self, headlines):
        clickbait_terms = {"increíble", "secreto", "urgente", "impactante", "no creerás", "última hora"}
        rows = []
        for index, headline in enumerate((headlines or [])[:20]):
            text = str(headline).strip()[:300]
            lower = text.casefold()
            length_score = max(0, 100 - abs(len(text) - 65) * 2)
            clickbait = sum(term in lower for term in clickbait_terms)
            clarity = 100 if 25 <= len(text) <= 90 else 65
            score = round(max(0, min(100, length_score * 0.55 + clarity * 0.45 - clickbait * 18)), 1)
            rows.append({"index": index, "headline": text, "score": score,
                         "clickbait_signals": clickbait, "length": len(text)})
        rows.sort(key=lambda row: (-row["score"], row["index"]))
        result = {"ranking": rows, "recommended": rows[0] if rows else None}
        self._append("H202_HEADLINE_COMPARISONS", result, 500)
        return result

    def public_announcement_version(self, operation, announcement_id=None, title="", body="",
                                    correction_note="", actor_id=None):
        rows = self._list("H202_PUBLIC_ANNOUNCEMENTS")
        if operation == "publish":
            item = {"id": uuid.uuid4().hex[:12], "title": str(title)[:300], "status": "published",
                    "versions": [], "created_at": self._now().isoformat()}
            rows.append(item)
        else:
            item = next((row for row in rows if row.get("id") == announcement_id), None)
            if not item:
                return None
            if operation == "history":
                return item
            if operation != "correct":
                raise ValueError("operación de comunicado inválida")
        version_number = len(item["versions"]) + 1
        content = str(body)[:16000]
        version = {"version": version_number, "body": content,
                   "correction_note": str(correction_note)[:1000], "actor_id": self._id(actor_id),
                   "checksum": hashlib.sha256(content.encode()).hexdigest(), "published_at": self._now().isoformat()}
        item["versions"].append(version)
        item["current_version"] = version_number
        self.db.set("H202_PUBLIC_ANNOUNCEMENTS", rows[-1000:])
        return item

    def impersonation_check(self, candidate, administrators):
        name = str(candidate.get("name", "")).casefold().strip()
        username = str(candidate.get("username", "")).casefold().lstrip("@")
        matches = []
        for admin in administrators or []:
            admin_name = str(admin.get("name", "")).casefold().strip()
            distance = self._edit_distance(name, admin_name)
            if admin_name and (name == admin_name or distance <= max(1, len(admin_name) // 8)):
                matches.append({"admin_id": self._id(admin.get("id")), "reason": "nombre similar", "distance": distance})
            if username and username == str(admin.get("username", "")).casefold().lstrip("@") and self._id(candidate.get("id")) != self._id(admin.get("id")):
                matches.append({"admin_id": self._id(admin.get("id")), "reason": "username duplicado"})
        return {"impersonation": bool(matches), "matches": matches}

    @staticmethod
    def _edit_distance(left, right):
        if not left:
            return len(right)
        previous = list(range(len(right) + 1))
        for i, a in enumerate(left, 1):
            current = [i]
            for j, b in enumerate(right, 1):
                current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (a != b)))
            previous = current
        return previous[-1]

    def link_chain(self, url, hops=None):
        hops = [str(x) for x in (hops or [])][:10]
        domains = [urlparse(str(url)).netloc.lower()] + [urlparse(x).netloc.lower() for x in hops]
        shorteners = {"bit.ly", "t.co", "tinyurl.com", "cutt.ly", "is.gd", "buff.ly", "rebrand.ly"}
        flags = []
        if any(x in shorteners for x in domains):
            flags.append("shortener")
        if len(set(filter(None, domains))) >= 3:
            flags.append("redirect_chain")
        if any(x.startswith("xn--") for x in domains):
            flags.append("punycode")
        return {"url": str(url), "hops": hops, "domains": domains, "flags": flags,
                "risk": min(100, len(flags) * 30 + max(0, len(hops) - 2) * 10)}

    def file_risk(self, filename, mime, digest, size=0):
        dangerous_ext = {".exe", ".scr", ".bat", ".cmd", ".ps1", ".js", ".jar", ".apk", ".msi"}
        ext = "." + str(filename).lower().rsplit(".", 1)[-1] if "." in str(filename) else ""
        mismatched = (ext in {".jpg", ".png", ".gif"} and not str(mime).startswith("image/"))
        known = self._dict("SECURITY_DANGEROUS_HASHES").get(str(digest).lower())
        flags = (["dangerous_extension"] if ext in dangerous_ext else []) + (["mime_mismatch"] if mismatched else []) + (["known_hash"] if known else [])
        return {"filename": str(filename), "mime": str(mime), "hash": str(digest), "size": int(size),
                "flags": flags, "known": known, "risk": min(100, len(flags) * 40)}

    # 31–40 · Automatización y contenido
    def content_create(self, kind, title, body, actor, **options):
        item = {"id": uuid.uuid4().hex[:12], "kind": str(kind), "title": str(title)[:300],
                "body": str(body)[:12000], "actor": self._id(actor), "options": options,
                "status": "draft", "created_at": self._now().isoformat()}
        return self._append("CONTENT_ITEMS", item)

    def content_schedule(self, content_id, targets, execute_at, recurrence=None, expires_at=None):
        when = datetime.datetime.fromisoformat(str(execute_at))
        item = {"id": uuid.uuid4().hex[:12], "content_id": content_id,
                "targets": [self._id(x) for x in targets], "execute_at": when.isoformat(),
                "recurrence": recurrence, "expires_at": expires_at, "status": "scheduled",
                "created_at": self._now().isoformat()}
        return self._append("CONTENT_SCHEDULE", item)

    def due_content(self):
        now, due, rows = self._now(), [], self._list("CONTENT_SCHEDULE")
        for item in rows:
            try:
                expired = item.get("expires_at") and datetime.datetime.fromisoformat(item["expires_at"]) <= now
                if expired:
                    item["status"] = "expired"
                elif item.get("status") == "scheduled" and datetime.datetime.fromisoformat(item["execute_at"]) <= now:
                    item["status"] = "ready"; due.append(item)
            except (TypeError, ValueError):
                item["status"] = "invalid"
        self.db.set("CONTENT_SCHEDULE", rows)
        return due

    def complete_content_schedule(self, schedule_id, successful):
        rows = self._list("CONTENT_SCHEDULE")
        for item in rows:
            if item["id"] != schedule_id:
                continue
            if successful and item.get("recurrence"):
                delta = {"daily": 1, "weekly": 7, "monthly": 30}.get(item["recurrence"])
                if delta:
                    item["execute_at"] = (self._now() + datetime.timedelta(days=delta)).isoformat()
                    item["status"] = "scheduled"
                else:
                    item["status"] = "completed"
            else:
                item["status"] = "completed" if successful else "failed"
            self.db.set("CONTENT_SCHEDULE", rows)
            return item
        return None

    def editorial_decision(self, content_id, actor, decision, comment=""):
        if decision not in ("approved", "rejected", "changes"):
            raise ValueError("decisión editorial no válida")
        items = self._list("CONTENT_ITEMS")
        target = next((x for x in items if x["id"] == content_id), None)
        if not target:
            return None
        target["status"] = decision
        target.setdefault("editorial", []).append({"actor": self._id(actor), "decision": decision,
                                                   "comment": str(comment)[:1000], "at": self._now().isoformat()})
        self.db.set("CONTENT_ITEMS", items)
        return target

    def library_save(self, title, body, tags=None):
        item = {"id": uuid.uuid4().hex[:12], "title": str(title)[:300], "body": str(body)[:12000],
                "tags": [str(x)[:50] for x in (tags or [])], "created_at": self._now().isoformat()}
        return self._append("CONTENT_LIBRARY", item)

    @staticmethod
    def render_template(template, variables):
        rendered = str(template)
        for key, value in (variables or {}).items():
            rendered = rendered.replace("{{" + str(key) + "}}", str(value))
        return rendered

    def translation_job(self, content_id, languages):
        item = {"id": uuid.uuid4().hex[:12], "content_id": content_id,
                "languages": [str(x)[:10] for x in languages], "status": "queued",
                "created_at": self._now().isoformat()}
        return self._append("CONTENT_TRANSLATIONS", item)

    def keyword_rule(self, group_id, keyword, response, conditions=None):
        item = {"id": uuid.uuid4().hex[:12], "group_id": self._id(group_id), "keyword": str(keyword)[:150],
                "response": str(response)[:4000], "conditions": conditions or {}, "active": True}
        return self._append("CONTENT_KEYWORD_RULES", item)

    def keyword_match(self, group_id, text, context=None):
        context = context or {}
        for rule in reversed(self._list("CONTENT_KEYWORD_RULES")):
            if rule["active"] and rule["group_id"] == self._id(group_id) and rule["keyword"].casefold() in str(text).casefold():
                conditions = rule.get("conditions", {})
                if all(context.get(k) == v for k, v in conditions.items()):
                    return rule
        return None

    def form_save(self, title, fields, destination):
        item = {"id": uuid.uuid4().hex[:12], "title": str(title)[:200],
                "fields": [x for x in fields if isinstance(x, dict)][:30],
                "destination": self._id(destination), "active": True}
        return self._append("CONTENT_FORMS", item)

    def form_submit(self, form_id, user_id, answers):
        forms = self._list("CONTENT_FORMS")
        form = next((x for x in forms if x["id"] == form_id and x["active"]), None)
        if not form:
            return None
        item = {"id": uuid.uuid4().hex[:12], "form_id": form_id, "user_id": self._id(user_id),
                "answers": answers or {}, "created_at": self._now().isoformat()}
        return self._append("CONTENT_FORM_SUBMISSIONS", item)

    def webhook_save(self, group_id, url, events, secret=None):
        item = {"id": uuid.uuid4().hex[:12], "group_id": self._id(group_id), "url": str(url)[:1000],
                "events": [str(x)[:80] for x in events], "secret": secret or secrets.token_hex(16),
                "active": True, "created_at": self._now().isoformat()}
        return self._append("INTEGRATION_WEBHOOKS", item)

    def webhook_enqueue(self, event, group_id, payload):
        jobs = []
        for hook in self._list("INTEGRATION_WEBHOOKS"):
            if hook.get("active") and hook["group_id"] == self._id(group_id) and event in hook["events"]:
                body = json.dumps(payload, sort_keys=True)
                jobs.append(self._append("WEBHOOK_QUEUE", {
                    "id": uuid.uuid4().hex[:12], "webhook_id": hook["id"], "url": hook["url"],
                    "event": event, "payload": payload,
                    "signature": hmac.new(hook["secret"].encode(), body.encode(), hashlib.sha256).hexdigest(),
                    "attempts": 0, "status": "queued", "next_attempt": self._now().isoformat(),
                }))
        return jobs

    def webhook_result(self, job_id, success, error=""):
        rows = self._list("WEBHOOK_QUEUE")
        for item in rows:
            if item["id"] != job_id:
                continue
            item["attempts"] += 1
            if success:
                item["status"] = "delivered"
            elif item["attempts"] >= 5:
                item["status"] = "dead_letter"; item["error"] = str(error)[:500]
            else:
                item["status"] = "retry"
                item["next_attempt"] = (self._now() + datetime.timedelta(minutes=2 ** item["attempts"])).isoformat()
            self.db.set("WEBHOOK_QUEUE", rows)
            return item
        return None

    # 41–50 · Inteligencia artificial
    def ai_source(self, group_id, title, content, approved=True):
        item = {"id": uuid.uuid4().hex[:12], "group_id": self._id(group_id), "title": str(title)[:300],
                "content": str(content)[:50000], "approved": bool(approved), "created_at": self._now().isoformat()}
        return self._append("AI_APPROVED_SOURCES", item)

    def ai_summary(self, group_id, messages, period="daily", topic=None):
        rows = [str(x.get("text", "")) for x in messages if not topic or topic.casefold() in str(x.get("text", "")).casefold()]
        words = Counter(word.casefold().strip(".,:;!?") for text in rows for word in text.split() if len(word) > 4)
        return {"group_id": self._id(group_id), "period": period, "topic": topic,
                "messages": len(rows), "keywords": words.most_common(12),
                "summary": " ".join(rows[-10:])[:4000], "generated_at": self._now().isoformat()}

    def unanswered_questions(self, messages, response_window=10):
        pending = []
        for index, message in enumerate(messages):
            text = str(message.get("text", ""))
            if "?" not in text:
                continue
            following = messages[index + 1:index + 1 + int(response_window)]
            if not any(self._id(x.get("reply_to")) == self._id(message.get("id")) for x in following):
                pending.append(message)
        return pending

    def classify_topics(self, messages):
        groups = defaultdict(list)
        dictionary = {"security": ["spam", "ban", "virus", "estafa"], "support": ["ayuda", "error", "problema"],
                      "community": ["evento", "grupo", "miembro"], "technology": ["api", "bot", "código", "ia"]}
        for message in messages:
            text = str(message.get("text", "")).casefold()
            scores = {topic: sum(word in text for word in words) for topic, words in dictionary.items()}
            topic = max(scores, key=scores.get) if max(scores.values(), default=0) else "other"
            groups[topic].append(message)
        return dict(groups)

    def moderation_explanation(self, decision, evidence, policy):
        return {"decision": decision, "because": [str(x) for x in evidence],
                "policy": str(policy), "reviewable": True,
                "text": f"Se aplicó {decision} por {', '.join(map(str, evidence))}; regla: {policy}."}

    def model_evaluation(self, model, correct, total, latency_ms, cost=0):
        row = {"model": str(model), "correct": int(correct), "total": int(total),
               "accuracy": round(int(correct) / max(1, int(total)), 4),
               "latency_ms": float(latency_ms), "cost": float(cost), "created_at": self._now().isoformat()}
        return self._append("AI_MODEL_EVALUATIONS", row)

    def ab_assignment(self, experiment, user_id, variants):
        digest = hashlib.sha256(f"{experiment}:{user_id}".encode()).digest()
        return variants[int.from_bytes(digest[:4], "big") % len(variants)]

    def memory_export(self, group_id):
        return {"group_id": self._id(group_id), "sources": [x for x in self._list("AI_APPROVED_SOURCES") if x["group_id"] == self._id(group_id)],
                "memory": self.db.get(f"AI_MEMORY_{self._id(group_id)}", [])}

    def tone_signal(self, group_id, messages):
        negative = {"odio", "idiota", "estafa", "mentira", "basura", "amenaza"}
        scores = [sum(word in str(x.get("text", "")).casefold() for word in negative) for x in messages]
        recent, previous = sum(scores[-20:]), sum(scores[-40:-20])
        return {"group_id": self._id(group_id), "negative_recent": recent, "negative_previous": previous,
                "emerging_conflict": recent >= max(3, previous * 2)}

    def draft_rules(self, community_type, priorities):
        base = ["Respeta a los demás.", "No publiques spam ni estafas.", "Protege los datos personales.",
                "Usa los canales y temas adecuados.", "Sigue las indicaciones de moderación."]
        return {"community_type": str(community_type), "rules": base + [f"Prioridad: {str(x)}." for x in priorities]}

    # 61–70 · Analítica
    def analytics(self, memberships, messages, campaigns=None):
        campaigns = campaigns or []
        cohorts, funnel, activity = defaultdict(lambda: {"joined": 0, "active": set()}), Counter(), Counter()
        for member in memberships:
            joined = datetime.datetime.fromisoformat(member["joined_at"])
            cohort = joined.strftime("%Y-%m")
            cohorts[cohort]["joined"] += 1
            if member.get("active"):
                cohorts[cohort]["active"].add(self._id(member.get("user_id")))
            funnel["requests"] += int(bool(member.get("requested", True)))
            funnel["approved"] += int(bool(member.get("approved")))
            funnel["participated"] += int(bool(member.get("active")))
        for message in messages:
            stamp = datetime.datetime.fromisoformat(message["created_at"])
            activity[f"{stamp.weekday()}-{stamp.hour:02d}"] += 1
        cohort_rows = {key: {"joined": value["joined"], "retained": len(value["active"]),
                             "retention": round(len(value["active"]) * 100 / max(1, value["joined"]), 1)}
                       for key, value in cohorts.items()}
        organic = sum(1 for x in memberships if not x.get("campaign"))
        return {"cohorts": cohort_rows, "funnel": dict(funnel), "activity": dict(activity),
                "growth": {"organic": organic, "campaign": len(memberships) - organic},
                "campaigns": campaigns}

    def health_score(self, metrics):
        activity = min(30, float(metrics.get("active_ratio", 0)) * 30)
        retention = min(30, float(metrics.get("retention", 0)) * .3)
        safety = max(0, 25 - float(metrics.get("incidents", 0)) * 2)
        response = min(15, 15 / max(1, float(metrics.get("response_hours", 1))))
        score = round(activity + retention + safety + response, 1)
        return {"score": score, "status": "healthy" if score >= 70 else "watch" if score >= 45 else "critical"}

    def anomaly(self, metric, current, history):
        values = [float(x) for x in history]
        mean = sum(values) / max(1, len(values))
        variance = sum((x - mean) ** 2 for x in values) / max(1, len(values))
        deviation = variance ** .5
        z = (float(current) - mean) / deviation if deviation else 0
        return {"metric": metric, "current": current, "mean": round(mean, 3), "z_score": round(z, 3), "anomaly": abs(z) >= 2.5}

    def goal(self, group_id, metric, target, month):
        goals = self._dict("ANALYTICS_GOALS")
        key = f"{self._id(group_id)}:{month}:{metric}"
        goals[key] = {"group_id": self._id(group_id), "metric": metric, "target": float(target),
                      "current": 0, "month": month}
        self.db.set("ANALYTICS_GOALS", goals)
        return goals[key]

    def bi_export(self, dataset):
        rows = dataset if isinstance(dataset, list) else [dataset]
        keys = sorted({key for row in rows if isinstance(row, dict) for key in row})
        return {"schema": [{"name": key, "type": "string"} for key in keys],
                "rows": [{key: row.get(key) for key in keys} for row in rows]}

    def report_schedule(self, group_id, channel, frequency, recipients):
        item = {"id": uuid.uuid4().hex[:12], "group_id": self._id(group_id), "channel": str(channel),
                "frequency": str(frequency), "recipients": [str(x) for x in recipients],
                "next_run": (self._now() + datetime.timedelta(days=1 if frequency == "daily" else 7)).isoformat(),
                "active": True}
        return self._append("ANALYTICS_REPORT_SCHEDULES", item)

    def anonymous_benchmark(self, group_ids, metric_rows):
        values = [float(metric_rows.get(self._id(gid), 0)) for gid in group_ids]
        mean = sum(values) / max(1, len(values))
        return [{"anonymous_group": hashlib.sha256(self._id(gid).encode()).hexdigest()[:8],
                 "value": value, "difference_from_average": round(value - mean, 3)}
                for gid, value in zip(group_ids, values)]

    # 71–80 · Integraciones y API
    def module_register(self, name, version, permissions, checksum, verified=False):
        item = {"id": uuid.uuid4().hex[:12], "name": str(name)[:100], "version": str(version)[:30],
                "permissions": list(permissions), "checksum": str(checksum), "verified": bool(verified)}
        return self._append("MODULE_MARKETPLACE", item)

    def api_token(self, name, scopes, expires_at=None):
        raw = "moon_" + secrets.token_urlsafe(32)
        item = {"id": uuid.uuid4().hex[:12], "name": str(name)[:100], "hash": hashlib.sha256(raw.encode()).hexdigest(),
                "prefix": raw[:12], "scopes": list(scopes), "expires_at": expires_at,
                "created_at": self._now().isoformat(), "status": "active"}
        self._append("API_TOKENS", item)
        return {"token": raw, "metadata": {k: v for k, v in item.items() if k != "hash"}}

    def rotate_token(self, token_id):
        rows = self._list("API_TOKENS")
        old = next((x for x in rows if x["id"] == token_id), None)
        if not old:
            return None
        old["status"] = "rotated"; old["rotated_at"] = self._now().isoformat()
        self.db.set("API_TOKENS", rows)
        return self.api_token(old["name"], old["scopes"], old.get("expires_at"))

    def sandbox(self, bot_id, enabled=True):
        sandboxes = self._dict("BOT_SANDBOXES")
        sandboxes[self._id(bot_id)] = {"bot_id": self._id(bot_id), "enabled": bool(enabled),
                                       "isolated_prefix": f"SANDBOX_{self._id(bot_id)}_", "updated_at": self._now().isoformat()}
        self.db.set("BOT_SANDBOXES", sandboxes)
        return sandboxes[self._id(bot_id)]

    def quota(self, bot_id, method, used, limit, reset_at=None):
        row = {"bot_id": self._id(bot_id), "method": str(method), "used": int(used), "limit": int(limit),
               "ratio": round(int(used) / max(1, int(limit)), 4), "reset_at": reset_at}
        quotas = self._dict("BOT_QUOTAS"); quotas[f"{bot_id}:{method}"] = row; self.db.set("BOT_QUOTAS", quotas)
        return row

    def signed_config(self, payload):
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return {"payload": payload, "signature": hmac.new(self.secret, raw.encode(), hashlib.sha256).hexdigest()}

    def verify_config(self, bundle):
        expected = self.signed_config(bundle.get("payload"))["signature"]
        return hmac.compare_digest(expected, str(bundle.get("signature", "")))

    def incident_link(self, provider, external_id, group_id, title):
        item = {"id": uuid.uuid4().hex[:12], "provider": str(provider), "external_id": str(external_id),
                "group_id": self._id(group_id), "title": str(title)[:300], "status": "open"}
        return self._append("INTEGRATION_INCIDENTS", item)

    def calendar_link(self, provider, calendar_id, group_id, sync_token=None):
        item = {"id": uuid.uuid4().hex[:12], "provider": str(provider), "calendar_id": str(calendar_id),
                "group_id": self._id(group_id), "sync_token": sync_token, "status": "active",
                "updated_at": self._now().isoformat()}
        return self._append("INTEGRATION_CALENDARS", item)

    def sdk_manifest(self):
        return {"name": "moonbot-extension-sdk", "version": "1.0", "events": [
            "message.created", "member.joined", "moderation.applied", "content.published",
            "event.started", "security.alert"], "authentication": "scoped bearer token"}

    # 81–90 · Operaciones y fiabilidad
    def deployment(self, version, instances, batch_size=1):
        item = {"id": uuid.uuid4().hex[:12], "version": str(version), "instances": list(instances),
                "batch_size": max(1, int(batch_size)), "completed": [], "failed": [],
                "status": "ready", "created_at": self._now().isoformat()}
        return self._append("OPS_DEPLOYMENTS", item)

    def health_result(self, deployment_id, instance, healthy):
        rows = self._list("OPS_DEPLOYMENTS")
        target = next((x for x in rows if x["id"] == deployment_id), None)
        if not target:
            return None
        bucket = "completed" if healthy else "failed"
        if instance not in target[bucket]:
            target[bucket].append(instance)
        target["status"] = "rollback" if target["failed"] else "running"
        self.db.set("OPS_DEPLOYMENTS", rows)
        return target

    def backup_policy(self, retention_days, encrypted=True, modules=None):
        policy = {"retention_days": max(1, int(retention_days)), "encrypted": bool(encrypted),
                  "modules": modules or ["all"], "updated_at": self._now().isoformat()}
        self.db.set("OPS_BACKUP_POLICY", policy)
        return policy

    def restore_plan(self, backup_id, groups=None, modules=None):
        item = {"id": uuid.uuid4().hex[:12], "backup_id": str(backup_id), "groups": groups or [],
                "modules": modules or [], "status": "pending_confirmation"}
        return self._append("OPS_RESTORE_PLANS", item)

    def dependency_status(self, name, status, latency_ms=None, detail=""):
        deps = self._dict("OPS_DEPENDENCIES")
        deps[str(name)] = {"name": str(name), "status": str(status), "latency_ms": latency_ms,
                           "detail": str(detail)[:500], "checked_at": self._now().isoformat()}
        self.db.set("OPS_DEPENDENCIES", deps)
        return deps[str(name)]

    def resource_alerts(self, metrics, thresholds=None):
        thresholds = thresholds or {"cpu": 90, "memory": 90, "disk": 90, "latency": 2000}
        return [{"metric": key, "value": metrics.get(key), "threshold": limit, "severity": "critical"}
                for key, limit in thresholds.items() if float(metrics.get(key, 0)) >= float(limit)]

    def degraded_mode(self, dependencies):
        failed = [name for name, state in dependencies.items() if state not in ("ok", "healthy")]
        capabilities = {"ai": "ai" not in failed, "cas_live": "cas" not in failed,
                        "moderation": True, "cached_reputation": True}
        return {"degraded": bool(failed), "failed": failed, "capabilities": capabilities}

    def diagnose(self, metrics, errors):
        recommendations = []
        if float(metrics.get("memory", 0)) > 85:
            recommendations.append("reiniciar workers con crecimiento de memoria")
        if float(metrics.get("disk", 0)) > 85:
            recommendations.append("rotar registros y revisar copias antiguas")
        if any("timeout" in str(x).casefold() for x in errors):
            recommendations.append("aumentar timeout o activar circuito degradado")
        return {"health": "attention" if recommendations else "healthy", "recommendations": recommendations}

    def group_errors(self, errors):
        groups = defaultdict(list)
        for error in errors:
            signature = hashlib.sha256(f"{error.get('type')}:{error.get('message')}".encode()).hexdigest()[:12]
            groups[signature].append(error)
        return [{"signature": key, "count": len(value), "sample": value[0]} for key, value in groups.items()]

    def maintenance_window(self, starts_at, ends_at, modules, message=""):
        start, end = datetime.datetime.fromisoformat(str(starts_at)), datetime.datetime.fromisoformat(str(ends_at))
        if end <= start:
            raise ValueError("la ventana debe terminar después de comenzar")
        item = {"id": uuid.uuid4().hex[:12], "starts_at": start.isoformat(), "ends_at": end.isoformat(),
                "modules": list(modules), "message": str(message)[:1000], "status": "scheduled"}
        return self._append("OPS_MAINTENANCE_WINDOWS", item)

    def snapshot(self):
        return {
            "security": {"raids": self._list("SECURITY_RAID_SIGNALS")[-50:]},
            "horizon202": {"escalation": self._list("H202_ESCALATION_RADAR")[-50:],
                           "mediators": self._dict("H202_MEDIATOR_SESSIONS"),
                           "peer_reviews": self._dict("H202_PEER_REVIEWS"),
                           "rule_simulations": self._list("H202_RULE_SIMULATIONS")[-20:],
                           "brigade_scans": self._list("H202_BRIGADE_SCANS")[-20:]},
            "content": {"items": list(reversed(self._list("CONTENT_ITEMS")))[:100],
                        "schedule": list(reversed(self._list("CONTENT_SCHEDULE")))[:100],
                        "library": list(reversed(self._list("CONTENT_LIBRARY")))[:100],
                        "forms": list(reversed(self._list("CONTENT_FORMS")))[:100],
                        "webhooks": list(reversed(self._list("INTEGRATION_WEBHOOKS")))[:100]},
            "ai": {"sources": list(reversed(self._list("AI_APPROVED_SOURCES")))[:100],
                   "models": list(reversed(self._list("AI_MODEL_EVALUATIONS")))[:100]},
            "analytics": {"goals": self._dict("ANALYTICS_GOALS")},
            "integrations": {"modules": self._list("MODULE_MARKETPLACE"), "tokens": [
                {k: v for k, v in x.items() if k != "hash"} for x in self._list("API_TOKENS")],
                "quotas": self._dict("BOT_QUOTAS"), "incidents": self._list("INTEGRATION_INCIDENTS")},
            "operations": {"deployments": list(reversed(self._list("OPS_DEPLOYMENTS")))[:100],
                           "dependencies": self._dict("OPS_DEPENDENCIES"),
                           "maintenance": list(reversed(self._list("OPS_MAINTENANCE_WINDOWS")))[:100]},
        }

"""Mentoría, encuestas, buzón y ciclo completo de eventos comunitarios."""

import datetime
import hashlib
import random
import secrets
import uuid


class CommunityEngagement:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def _uid(value):
        return str(value).strip()

    @staticmethod
    def _rows(db, key):
        rows = db.get(key, [])
        return rows if isinstance(rows, list) else []

    def mentor_profile(self, user_id, skills=None, capacity=3, active=True):
        uid = self._uid(user_id)
        mentors = self.db.get("COMMUNITY_MENTORS", {})
        mentors = mentors if isinstance(mentors, dict) else {}
        mentors[uid] = {
            "user_id": uid, "skills": [str(x)[:80] for x in (skills or [])][:20],
            "capacity": max(1, min(int(capacity), 20)), "active": bool(active),
            "updated_at": datetime.datetime.now().isoformat(),
        }
        self.db.set("COMMUNITY_MENTORS", mentors)
        return mentors[uid]

    def mentor_match(self, mentee_id, skills=None):
        mentors = self.db.get("COMMUNITY_MENTORS", {})
        matches = self._rows(self.db, "COMMUNITY_MENTOR_MATCHES")
        requested = {str(x).lower() for x in (skills or [])}
        occupied = {}
        for item in matches:
            if item.get("status") == "active":
                occupied[item["mentor_id"]] = occupied.get(item["mentor_id"], 0) + 1
        candidates = []
        for mentor in mentors.values() if isinstance(mentors, dict) else []:
            if not mentor.get("active") or occupied.get(mentor["user_id"], 0) >= mentor["capacity"]:
                continue
            overlap = len(requested & {x.lower() for x in mentor.get("skills", [])})
            candidates.append((overlap, -occupied.get(mentor["user_id"], 0), mentor))
        if not candidates:
            return None
        mentor = sorted(candidates, key=lambda row: (row[0], row[1]), reverse=True)[0][2]
        item = {"id": uuid.uuid4().hex[:12], "mentor_id": mentor["user_id"],
                "mentee_id": self._uid(mentee_id), "skills": list(requested),
                "status": "active", "created_at": datetime.datetime.now().isoformat()}
        matches.append(item)
        self.db.set("COMMUNITY_MENTOR_MATCHES", matches[-1000:])
        return item

    def create_survey(self, title, options, anonymous=True, closes_at=None):
        clean = [str(option).strip()[:150] for option in options if str(option).strip()]
        if len(clean) < 2:
            raise ValueError("la encuesta necesita al menos dos opciones")
        rows = self._rows(self.db, "COMMUNITY_SURVEYS")
        item = {"id": uuid.uuid4().hex[:12], "title": str(title)[:300],
                "options": [{"id": str(i), "text": text, "votes": 0} for i, text in enumerate(clean)],
                "anonymous": bool(anonymous), "voters": {}, "status": "open",
                "closes_at": closes_at, "created_at": datetime.datetime.now().isoformat()}
        rows.append(item); self.db.set("COMMUNITY_SURVEYS", rows[-300:])
        return item

    def vote_survey(self, survey_id, user_id, option_id):
        rows = self._rows(self.db, "COMMUNITY_SURVEYS")
        for survey in rows:
            if survey.get("id") != survey_id or survey.get("status") != "open":
                continue
            uid = self._uid(user_id)
            previous = survey["voters"].get(uid)
            if previous is not None:
                for option in survey["options"]:
                    if option["id"] == previous:
                        option["votes"] = max(0, option["votes"] - 1)
            target = next((x for x in survey["options"] if x["id"] == str(option_id)), None)
            if not target:
                return None
            target["votes"] += 1; survey["voters"][uid] = target["id"]
            self.db.set("COMMUNITY_SURVEYS", rows[-300:])
            return self._public_survey(survey)
        return None

    @staticmethod
    def _public_survey(survey):
        return {key: value for key, value in survey.items() if key != "voters"}

    def surveys(self):
        return [self._public_survey(row) for row in reversed(self._rows(self.db, "COMMUNITY_SURVEYS"))]

    def anonymous_message(self, user_id, text, category="general"):
        text = str(text).strip()
        if len(text) < 5:
            raise ValueError("el mensaje es demasiado corto")
        uid = self._uid(user_id)
        now = datetime.datetime.now()
        rate = self.db.get("COMMUNITY_ANONYMOUS_RATE", {})
        rate = rate if isinstance(rate, dict) else {}
        recent = []
        for value in rate.get(uid, []):
            try:
                stamp = datetime.datetime.fromisoformat(value)
                if now - stamp < datetime.timedelta(hours=1):
                    recent.append(stamp.isoformat())
            except (TypeError, ValueError):
                continue
        if len(recent) >= 3:
            raise ValueError("límite anónimo alcanzado; inténtalo dentro de una hora")
        recent.append(now.isoformat())
        rate[uid] = recent
        self.db.set("COMMUNITY_ANONYMOUS_RATE", rate)
        salt = secrets.token_hex(8)
        sender_hash = hashlib.sha256(f"{salt}:{uid}".encode()).hexdigest()
        rows = self._rows(self.db, "COMMUNITY_ANONYMOUS_INBOX")
        item = {"id": uuid.uuid4().hex[:12], "sender_hash": sender_hash,
                "category": str(category)[:50], "text": text[:2000], "status": "new",
                "created_at": datetime.datetime.now().isoformat()}
        rows.append(item); self.db.set("COMMUNITY_ANONYMOUS_INBOX", rows[-1000:])
        return {key: value for key, value in item.items() if key != "sender_hash"}

    def create_event(self, title, starts_at, capacity=0, description="", kind="event"):
        start = datetime.datetime.fromisoformat(str(starts_at))
        rows = self._rows(self.db, "COMMUNITY_EVENTS")
        item = {"id": uuid.uuid4().hex[:12], "title": str(title)[:200],
                "description": str(description)[:2000], "kind": str(kind)[:50],
                "starts_at": start.isoformat(), "capacity": max(0, min(int(capacity), 100000)),
                "attendees": [], "waitlist": [], "checkins": [], "status": "scheduled",
                "submissions": [], "questions": [], "reminders_sent": [],
                "created_at": datetime.datetime.now().isoformat()}
        rows.append(item); self.db.set("COMMUNITY_EVENTS", rows[-500:])
        return item

    def register_event(self, event_id, user_id):
        rows = self._rows(self.db, "COMMUNITY_EVENTS"); uid = self._uid(user_id)
        for event in rows:
            if event.get("id") != event_id or event.get("status") != "scheduled":
                continue
            if uid in event["attendees"] or uid in event["waitlist"]:
                return {"event": event, "registration": "existing"}
            if event["capacity"] and len(event["attendees"]) >= event["capacity"]:
                event["waitlist"].append(uid); registration = "waitlist"
            else:
                event["attendees"].append(uid); registration = "confirmed"
            self.db.set("COMMUNITY_EVENTS", rows[-500:])
            return {"event": event, "registration": registration}
        return None

    def cancel_registration(self, event_id, user_id):
        rows = self._rows(self.db, "COMMUNITY_EVENTS"); uid = self._uid(user_id)
        for event in rows:
            if event.get("id") != event_id:
                continue
            event["attendees"] = [x for x in event["attendees"] if x != uid]
            event["waitlist"] = [x for x in event["waitlist"] if x != uid]
            promoted = None
            if event["waitlist"] and (not event["capacity"] or len(event["attendees"]) < event["capacity"]):
                promoted = event["waitlist"].pop(0); event["attendees"].append(promoted)
            self.db.set("COMMUNITY_EVENTS", rows[-500:])
            return {"event": event, "promoted": promoted}
        return None

    def checkin(self, event_id, user_id):
        rows = self._rows(self.db, "COMMUNITY_EVENTS"); uid = self._uid(user_id)
        for event in rows:
            if event.get("id") == event_id and uid in event["attendees"]:
                if uid not in event["checkins"]: event["checkins"].append(uid)
                self.db.set("COMMUNITY_EVENTS", rows[-500:]); return event
        return None

    def events(self):
        return list(reversed(self._rows(self.db, "COMMUNITY_EVENTS")))

    def event_stats(self, event_id):
        event = next((x for x in self.events() if x.get("id") == event_id), None)
        if not event: return None
        attendees, checkins = len(event["attendees"]), len(event["checkins"])
        return {"event_id": event_id, "registered": attendees, "waitlisted": len(event["waitlist"]),
                "attended": checkins, "attendance_rate": round(checkins * 100 / attendees, 1) if attendees else 0}

    def submit_contest(self, event_id, user_id, title, content):
        rows = self._rows(self.db, "COMMUNITY_EVENTS")
        for event in rows:
            if event.get("id") == event_id and event.get("kind") == "contest":
                item = {"id": uuid.uuid4().hex[:12], "user_id": self._uid(user_id),
                        "title": str(title)[:200], "content": str(content)[:2000], "votes": []}
                event.setdefault("submissions", []).append(item)
                self.db.set("COMMUNITY_EVENTS", rows[-500:]); return item
        return None

    def vote_contest(self, event_id, submission_id, user_id):
        rows = self._rows(self.db, "COMMUNITY_EVENTS"); uid = self._uid(user_id)
        for event in rows:
            if event.get("id") != event_id: continue
            for submission in event.get("submissions", []):
                submission["votes"] = [x for x in submission.get("votes", []) if x != uid]
            target = next((x for x in event.get("submissions", []) if x.get("id") == submission_id), None)
            if not target: return None
            target["votes"].append(uid); self.db.set("COMMUNITY_EVENTS", rows[-500:]); return target
        return None

    def score_contest(self, event_id, submission_id, juror_id, score):
        rows = self._rows(self.db, "COMMUNITY_EVENTS")
        score = max(0, min(float(score), 10))
        for event in rows:
            if event.get("id") != event_id or event.get("kind") != "contest":
                continue
            target = next((x for x in event.get("submissions", []) if x.get("id") == submission_id), None)
            if not target:
                return None
            target.setdefault("jury_scores", {})[self._uid(juror_id)] = score
            scores = list(target["jury_scores"].values())
            target["jury_average"] = round(sum(scores) / len(scores), 2)
            self.db.set("COMMUNITY_EVENTS", rows[-500:])
            return target
        return None

    def qa_question(self, event_id, user_id, text):
        rows = self._rows(self.db, "COMMUNITY_EVENTS")
        for event in rows:
            if event.get("id") == event_id and event.get("kind") == "qa":
                item = {"id": uuid.uuid4().hex[:12], "user_id": self._uid(user_id),
                        "text": str(text)[:1000], "votes": [], "status": "pending"}
                event.setdefault("questions", []).append(item)
                self.db.set("COMMUNITY_EVENTS", rows[-500:]); return item
        return None

    def moderate_question(self, event_id, question_id, status):
        rows = self._rows(self.db, "COMMUNITY_EVENTS")
        for event in rows:
            if event.get("id") != event_id: continue
            question = next((x for x in event.get("questions", []) if x.get("id") == question_id), None)
            if question and status in ("approved", "rejected", "answered"):
                question["status"] = status; self.db.set("COMMUNITY_EVENTS", rows[-500:]); return question
        return None

    def agenda_ics(self):
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Moonbot//Community//ES"]
        for event in reversed(self.events()):
            start = datetime.datetime.fromisoformat(event["starts_at"]).strftime("%Y%m%dT%H%M%S")
            title = self._ics_escape(event["title"])
            description = self._ics_escape(event.get("description", ""))
            lines += ["BEGIN:VEVENT", f"UID:{event['id']}@moonbot", f"DTSTART:{start}",
                      f"SUMMARY:{title}", f"DESCRIPTION:{description}", "END:VEVENT"]
        lines.append("END:VCALENDAR")
        return "\r\n".join(lines)

    @staticmethod
    def _ics_escape(value):
        return str(value).replace("\\", "\\\\").replace("\r", "").replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")

    def due_event_reminders(self, hours=24):
        rows = self._rows(self.db, "COMMUNITY_EVENTS"); now = datetime.datetime.now(); due = []
        for event in rows:
            if event.get("status") != "scheduled": continue
            delta = datetime.datetime.fromisoformat(event["starts_at"]) - now
            marker = f"{hours}h"
            if datetime.timedelta(0) < delta <= datetime.timedelta(hours=hours) and marker not in event.setdefault("reminders_sent", []):
                event["reminders_sent"].append(marker)
                due.append({"event_id": event["id"], "title": event["title"],
                            "starts_at": event["starts_at"], "users": list(event["attendees"])})
        self.db.set("COMMUNITY_EVENTS", rows[-500:]); return due

    def create_challenge(self, title, target, ends_at):
        rows = self._rows(self.db, "COMMUNITY_CHALLENGES")
        item = {"id": uuid.uuid4().hex[:12], "title": str(title)[:200],
                "target": max(1, int(target)), "ends_at": datetime.datetime.fromisoformat(str(ends_at)).isoformat(),
                "progress": {}, "created_at": datetime.datetime.now().isoformat()}
        rows.append(item); self.db.set("COMMUNITY_CHALLENGES", rows[-300:]); return item

    def challenge_progress(self, challenge_id, user_id, amount=1):
        rows = self._rows(self.db, "COMMUNITY_CHALLENGES")
        for challenge in rows:
            if challenge.get("id") == challenge_id:
                uid = self._uid(user_id)
                challenge["progress"][uid] = max(0, int(challenge["progress"].get(uid, 0)) + int(amount))
                self.db.set("COMMUNITY_CHALLENGES", rows[-300:])
                ranking = sorted(challenge["progress"].items(), key=lambda row: row[1], reverse=True)
                return {"challenge": challenge, "ranking": ranking[:100]}
        return None

    def draw(self, event_id, winners=1, seed=None):
        event = next((x for x in self.events() if x.get("id") == event_id), None)
        if not event or not event["attendees"]: return None
        seed = seed or secrets.token_hex(16)
        rng = random.Random(f"{event_id}:{seed}")
        selected = rng.sample(event["attendees"], min(max(1, int(winners)), len(event["attendees"])))
        result = {"id": uuid.uuid4().hex[:12], "event_id": event_id, "seed": seed,
                  "participants_hash": hashlib.sha256(",".join(sorted(event["attendees"])).encode()).hexdigest(),
                  "winners": selected, "created_at": datetime.datetime.now().isoformat()}
        rows = self._rows(self.db, "COMMUNITY_DRAWS"); rows.append(result)
        self.db.set("COMMUNITY_DRAWS", rows[-300:]); return result

    def certificate(self, event_id, user_id):
        event = next((x for x in self.events() if x.get("id") == event_id), None)
        uid = self._uid(user_id)
        if not event or uid not in event["checkins"]: return None
        token = hashlib.sha256(f"{event_id}:{uid}:{event['starts_at']}".encode()).hexdigest()[:20]
        return {"certificate_id": token, "event_id": event_id, "user_id": uid,
                "title": event["title"], "issued_at": datetime.datetime.now().isoformat()}

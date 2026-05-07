import datetime
import hashlib
import re
import time

from core.telegram_api import extract_guest_update


class InvokedAIService:
    def __init__(self, ia, db, ban_manager, cas_checker, log_func, bot_username="MoonBot"):
        self.ia = ia
        self.db = db
        self.ban_manager = ban_manager
        self.cas_checker = cas_checker
        self.log = log_func
        self.bot_username = bot_username or "MoonBot"
        self.guest_reply_times = {}
        self.inline_reply_times = {}
        self.inline_answer_cache = {}

    def set_bot_username(self, bot_username):
        self.bot_username = bot_username or self.bot_username

    def build_prompt(self, mode, text, uname="Usuario", context_text=""):
        mode_label = "Guest Mode" if mode == "guest" else "Inline Mode"
        parts = [
            f"Modo Telegram: {mode_label}.",
            "Responde en espanol, de forma util, breve y lista para publicar en Telegram.",
            "No menciones limitaciones internas ni digas que eres un modelo.",
        ]
        if mode == "guest":
            parts.append("Has sido invocado temporalmente en un chat donde no debes asumir permisos ni historial completo.")
        else:
            parts.append("El usuario esta preparando una respuesta inline; genera texto reutilizable y claro.")
        if context_text:
            parts.append(f"Contexto citado: {context_text[:500]}")
        parts.append(f"{uname}: {text[:700]}")
        return "\n".join(parts)

    def generate_reply(self, mode, text, uid, uname="Usuario", cid=None, context_text=""):
        text = (text or "").strip() or "Crea una respuesta breve y util."
        chat_key = f"{mode}:{cid or uid}"
        prompt = self.build_prompt(mode, text, uname, context_text)
        answer = (self.ia.generate(prompt[:1000], chat_id=chat_key) or "").strip()
        if not answer:
            answer = "Estoy listo. Dame un poco mas de contexto y te respondo mejor."
        return answer[:3500]

    def is_user_blocked_for_remote_ai(self, uid):
        if self.ban_manager.is_global_banned(uid):
            return True
        settings = self.db.get("GLOBAL_SETTINGS", {})
        if settings.get("cas_protection", "on") != "on":
            return False
        cas_status = self.cas_checker(uid)
        return bool(cas_status.get("banned"))

    def build_inline_results(self, query, answer):
        digest = hashlib.sha1(f"{query}|{answer}|{time.time()}".encode("utf-8")).hexdigest()[:16]
        short_answer = answer[:180]
        concise = answer[:900]
        refined_prompt = (
            "Necesito una respuesta clara para Telegram sobre: "
            f"{(query or 'esta idea')[:700]}. "
            "Incluye puntos concretos, evita relleno y termina con una accion util."
        )
        return [
            {
                "type": "article",
                "id": f"moon_ai_{digest}",
                "title": "Respuesta IA",
                "description": short_answer,
                "input_message_content": {
                    "message_text": answer[:4096],
                    "parse_mode": "Markdown",
                },
            },
            {
                "type": "article",
                "id": f"moon_ai_short_{digest}",
                "title": "Respuesta breve",
                "description": concise[:120],
                "input_message_content": {
                    "message_text": concise,
                    "parse_mode": "Markdown",
                },
            },
            {
                "type": "article",
                "id": f"moon_ai_prompt_{digest}",
                "title": "Mejorar prompt",
                "description": "Convierte la idea en una peticion mas clara para el chat.",
                "input_message_content": {
                    "message_text": refined_prompt,
                    "parse_mode": "Markdown",
                },
            },
        ]

    def get_cached_inline_answer(self, query, uid, uname):
        cache_key = f"{uid}:{query.lower().strip()}"
        now_s = time.time()
        cached = self.inline_answer_cache.get(cache_key)
        if cached and now_s - cached["time"] < 20:
            return cached["answer"]
        answer = self.generate_reply("inline", query, uid or "inline", uname=uname)
        self.inline_answer_cache[cache_key] = {"time": now_s, "answer": answer}
        if len(self.inline_answer_cache) > 200:
            oldest = sorted(self.inline_answer_cache.items(), key=lambda item: item[1]["time"])[:50]
            for key, _ in oldest:
                self.inline_answer_cache.pop(key, None)
        return answer

    def answer_inline_query(self, update, answer_inline_query):
        inline = update.get("inline_query")
        if not inline:
            return False
        query_id = inline.get("id")
        user = inline.get("from", {})
        uid = str(user.get("id", ""))
        uname = user.get("first_name", "Usuario")
        query = (inline.get("query") or "").strip()
        if not query_id:
            return True

        key = f"inline:{uid}"
        now_s = time.time()
        if now_s - self.inline_reply_times.get(key, 0) < 3:
            answer_inline_query(query_id, [], cache_time=1)
            return True
        self.inline_reply_times[key] = now_s

        if uid and self.is_user_blocked_for_remote_ai(uid):
            answer_inline_query(query_id, [], cache_time=10)
            self.log("SECURITY", f"Inline IA bloqueada para usuario baneado/CAS {uid}.")
            return True

        try:
            answer = self.get_cached_inline_answer(query, uid or "inline", uname)
            results = self.build_inline_results(query or "Moon IA", answer)
            answer_inline_query(query_id, results, cache_time=2, is_personal=True)
            self.log("IA", f"Inline IA respondida para {uname} ({uid}).")
        except Exception as e:
            self.log("ERROR", f"Fallo procesando inline IA: {e}")
            answer_inline_query(query_id, [], cache_time=1)
        return True

    def record_chosen_inline_result(self, update):
        chosen = update.get("chosen_inline_result")
        if not chosen:
            return False
        events = self.db.get("INLINE_AI_CHOICES", [])
        events.append({
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "result_id": chosen.get("result_id"),
            "query": chosen.get("query", "")[:300],
            "user_id": str(chosen.get("from", {}).get("id", "")),
        })
        self.db.set("INLINE_AI_CHOICES", events[-100:])
        return True

    def answer_guest_update(self, update, send_msg, enforce_existing_ban, enforce_cas_ban):
        field, guest = extract_guest_update(update)
        if not guest:
            return False
        msg = guest.get("message") or guest.get("summoning_message") or guest
        if not isinstance(msg, dict) or "chat" not in msg:
            events = self.db.get("GUEST_BOT_UPDATES", [])
            events.append({"time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "field": field, "update": guest})
            self.db.set("GUEST_BOT_UPDATES", events[-100:])
            self.log("INFO", f"Guest Bot update registrado ({field}) sin mensaje ejecutable.")
            return True

        cid = str(msg["chat"]["id"])
        user = msg.get("from", {})
        uid = str(user.get("id", cid))
        uname = user.get("first_name", "Guest")
        text = msg.get("text") or msg.get("caption") or ""
        text = re.sub(rf"@{re.escape(self.bot_username)}\b", "", text, flags=re.IGNORECASE).strip()
        if not text:
            text = "Responde de forma breve y util a esta invocacion."

        key = f"{cid}:{uid}"
        now_s = time.time()
        if now_s - self.guest_reply_times.get(key, 0) < 5:
            self.log("DEBUG", f"Guest Bot rate limit para {key}")
            return True
        self.guest_reply_times[key] = now_s

        if enforce_existing_ban(cid, uid, uname, msg.get("message_id")):
            return True
        if enforce_cas_ban(cid, uid, uname, msg.get("message_id")):
            return True

        try:
            quoted = msg.get("reply_to_message", {}).get("text", "") if msg.get("reply_to_message") else ""
            answer = self.generate_reply("guest", text, uid, uname=uname, cid=cid, context_text=quoted)
            send_msg(cid, answer)
            self.log("INFO", f"Guest Bot respondio en {cid} a {uname}.")
        except Exception as e:
            self.log("ERROR", f"Fallo procesando Guest Bot update: {e}")
        return True

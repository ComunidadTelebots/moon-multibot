import datetime
import json
import threading
from ctypes import CDLL, CFUNCTYPE, c_char_p, c_double, c_int
from ctypes.util import find_library

from core.config import TDLIB_PATH as TDLIB_SO


class TDLibClient:
    def __init__(self, api_id, api_hash, db, log_func=None):
        self._api_id = int(api_id)
        self._api_hash = api_hash
        self._db = db
        self._log = log_func or (lambda lvl, txt: None)
        self._client_id = None
        self._running = False
        self._auth_state = "not_loaded"
        self._pending = {}
        self._extra_counter = 0
        self._extra_lock = threading.Lock()
        self._tdjson = None
        self._log_cb_ref = None
        self._load_library()

    def _load_library(self):
        path = find_library("tdjson") or TDLIB_SO
        try:
            lib = CDLL(path)
        except OSError as e:
            self._log("ERROR", f"TDLib no encontrado en {path}: {e}")
            return

        lib.td_create_client_id.restype = c_int
        lib.td_create_client_id.argtypes = []
        lib.td_receive.restype = c_char_p
        lib.td_receive.argtypes = [c_double]
        lib.td_send.restype = None
        lib.td_send.argtypes = [c_int, c_char_p]
        lib.td_execute.restype = c_char_p
        lib.td_execute.argtypes = [c_char_p]

        log_cb_type = CFUNCTYPE(None, c_int, c_char_p)

        @log_cb_type
        def _on_log(verbosity, message):
            if verbosity == 0:
                self._log("ERROR", f"TDLib fatal: {message.decode('utf-8', errors='replace')}")

        lib.td_set_log_message_callback.restype = None
        lib.td_set_log_message_callback.argtypes = [c_int, log_cb_type]
        lib.td_set_log_message_callback(2, _on_log)

        self._log_cb_ref = _on_log  # evitar que el GC lo destruya
        self._tdjson = lib
        self._auth_state = "not_started"
        self._log("TDLIB", "Librería libtdjson cargada correctamente")

    def start(self):
        if not self._tdjson:
            return False
        self._client_id = self._tdjson.td_create_client_id()
        self._running = True
        threading.Thread(target=self._receive_loop, daemon=True, name="tdlib-recv").start()
        self.send({"@type": "getOption", "name": "version"})
        self._log("TDLIB", f"Cliente TDLib iniciado (id={self._client_id})")
        return True

    def stop(self):
        self._running = False
        if self._tdjson and self._client_id is not None:
            self.send({"@type": "close"})

    # ── Primitivas de comunicación ────────────────────────────────

    def _next_extra(self):
        with self._extra_lock:
            self._extra_counter += 1
            return str(self._extra_counter)

    def send(self, query: dict):
        if not self._tdjson or self._client_id is None:
            return
        self._tdjson.td_send(self._client_id, json.dumps(query).encode())

    def execute(self, query: dict):
        if not self._tdjson:
            return None
        result = self._tdjson.td_execute(json.dumps(query).encode())
        return json.loads(result) if result else None

    def send_await(self, query: dict, timeout: float = 15.0):
        extra = self._next_extra()
        query["@extra"] = extra
        event = threading.Event()
        holder = [None]
        self._pending[extra] = (event, holder)
        self.send(query)
        event.wait(timeout)
        self._pending.pop(extra, None)
        return holder[0]

    # ── Loop receptor ─────────────────────────────────────────────

    def _receive_loop(self):
        while self._running:
            raw = self._tdjson.td_receive(1.0)
            if not raw:
                continue
            try:
                event = json.loads(raw)
            except Exception:
                continue
            self._dispatch(event)

    def _dispatch(self, event: dict):
        extra = event.get("@extra")
        if extra and extra in self._pending:
            ev, holder = self._pending[extra]
            holder[0] = event
            ev.set()
            return

        t = event.get("@type", "")
        if t == "updateAuthorizationState":
            self._handle_auth(event["authorization_state"])

    # ── Máquina de estados de autenticación ───────────────────────

    def _handle_auth(self, state: dict):
        t = state["@type"]
        self._auth_state = t
        self._log("TDLIB", f"Auth: {t}")

        if t == "authorizationStateWaitTdlibParameters":
            self.send({
                "@type": "setTdlibParameters",
                "database_directory": "tdlib_data",
                "files_directory": "tdlib_files",
                "use_message_database": True,
                "use_secret_chats": False,
                "api_id": self._api_id,
                "api_hash": self._api_hash,
                "system_language_code": "es",
                "device_model": "Moon Multibot",
                "application_version": "1.0",
            })
        elif t == "authorizationStateReady":
            self._log("TDLIB", "✅ TDLib autenticado y listo")
        elif t == "authorizationStateClosed":
            self._running = False

    # ── Helpers de auth (llamados desde Flask) ────────────────────

    def auth_set_phone(self, phone: str):
        self.send({"@type": "setAuthenticationPhoneNumber", "phone_number": phone})

    def auth_set_code(self, code: str):
        self.send({"@type": "checkAuthenticationCode", "code": code})

    def auth_set_password(self, password: str):
        self.send({"@type": "checkAuthenticationPassword", "password": password})

    # ── API pública ───────────────────────────────────────────────

    def get_status(self) -> dict:
        return {
            "loaded": self._tdjson is not None,
            "running": self._running,
            "auth_state": self._auth_state,
            "ready": self._auth_state == "authorizationStateReady",
        }

    def get_history(self, chat_id: int, limit: int = 100) -> list:
        if self._auth_state != "authorizationStateReady":
            return []
        result = self.send_await({
            "@type": "getChatHistory",
            "chat_id": chat_id,
            "from_message_id": 0,
            "offset": 0,
            "limit": limit,
            "only_local": False,
        }, timeout=20)
        if not result or result.get("@type") != "messages":
            return []
        entries = []
        for msg in result.get("messages", []):
            content = msg.get("content", {})
            content_type = content.get("@type", "")
            text = ""
            media = None
            if content_type == "messageText":
                text = content.get("text", {}).get("text", "")
            else:
                media = content_type
            sender = msg.get("sender_id", {})
            uid = str(sender.get("user_id") or sender.get("chat_id", ""))
            ts = datetime.datetime.fromtimestamp(msg.get("date", 0)).strftime("%H:%M")
            entries.append({
                "time": ts,
                "sender": uid,
                "uid": uid,
                "text": text[:1000],
                "media": media,
            })
        return list(reversed(entries))  # cronológico (más antiguo primero)

    def sync_to_db(self, chat_id: int, limit: int = 200) -> int:
        entries = self.get_history(chat_id, limit)
        if not entries:
            return 0
        cid = str(chat_id)
        existing = self._db.get(f"CHAT_HIST_{cid}", [])
        existing_keys = {(e["time"], e["uid"], e["text"][:20]) for e in existing}
        new_entries = [e for e in entries if (e["time"], e["uid"], e["text"][:20]) not in existing_keys]
        merged = (existing + new_entries)[-200:]
        self._db.set(f"CHAT_HIST_{cid}", merged)
        self._log("TDLIB", f"Sincronizados {len(new_entries)} mensajes nuevos en chat {cid}")
        return len(new_entries)

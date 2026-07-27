import datetime


class TelegramEventStore:
    def __init__(self, db, log_func):
        self.db = db
        self.log = log_func
        self.business_connections = db.get("BUSINESS_CONNECTIONS", {})

    def list_business_connections(self):
        return self.business_connections

    def record_managed_bot_update(self, update):
        managed = update.get("managed_bot")
        if not managed:
            return False
        bot = managed.get("bot") or {}
        owner = managed.get("user") or {}
        events = self.db.get("MANAGED_BOT_UPDATES", [])
        event = {
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "update": managed,
            "bot_id": str(bot.get("id", "")),
            "username": bot.get("username"),
            "owner_id": str(owner.get("id", "")),
        }
        events.append(event)
        self.db.set("MANAGED_BOT_UPDATES", events[-100:])
        registry = self.db.get("MANAGED_BOTS", {})
        registry = registry if isinstance(registry, dict) else {}
        if bot.get("id") is not None:
            current = registry.get(str(bot["id"]), {})
            current.update({
                "bot_id": str(bot["id"]), "username": bot.get("username"),
                "name": bot.get("first_name"), "owner_id": str(owner.get("id", "")),
                "status": current.get("status", "detected"), "updated_at": event["time"],
            })
            registry[str(bot["id"])] = current
            self.db.set("MANAGED_BOTS", registry)
        self.log("INFO", f"Managed bot update recibido: @{bot.get('username', 'sin_username')}.")
        return True

    def record_business_update(self, update):
        conn = update.get("business_connection")
        if not conn:
            return False
        conn_id = conn.get("id")
        if conn_id:
            self.business_connections[conn_id] = conn
            self.db.set("BUSINESS_CONNECTIONS", self.business_connections)
        self.log("INFO", f"Business connection actualizada: {conn_id or 'sin id'}")
        return True

    def record_subscription_update(self, update):
        subscription = update.get("subscription")
        if not subscription:
            return False
        user = subscription.get("user") or {}
        event = {
            "time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "user_id": str(user.get("id", "")),
            "username": user.get("username"),
            "name": " ".join(filter(None, [user.get("first_name"), user.get("last_name")])),
            "state": subscription.get("state"),
            "invoice_payload": subscription.get("invoice_payload"),
        }
        events = self.db.get("BOT_SUBSCRIPTION_UPDATES", []) or []
        events.append(event)
        self.db.set("BOT_SUBSCRIPTION_UPDATES", events[-500:])
        self.log("INFO", f"Suscripción Telegram 10.2: {event['user_id']} -> {event['state']}")
        return True

    def record_community_message(self, message):
        added = message.get("community_chat_added")
        removed = message.get("community_chat_removed")
        if not added and removed is None:
            return False
        chat = message.get("chat") or {}
        chat_id = str(chat.get("id", ""))
        registry = self.db.get("TELEGRAM_COMMUNITIES", {}) or {}
        if added:
            community = added.get("community") or {}
            registry[chat_id] = {
                "chat_id": chat_id, "chat_title": chat.get("title"),
                "community": community,
                "community_id": str(community.get("id", "")),
                "active": True,
                "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
        else:
            current = registry.get(chat_id, {"chat_id": chat_id, "chat_title": chat.get("title")})
            current.update({"active": False, "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()})
            registry[chat_id] = current
        self.db.set("TELEGRAM_COMMUNITIES", registry)
        self.log("INFO", f"Comunidad Telegram 10.2 actualizada para chat {chat_id}")
        return True

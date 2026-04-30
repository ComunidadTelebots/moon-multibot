"""
Ban Manager - Gestión centralizada de baneos entre múltiples bots
Mantiene una lista negra global sincronizada
"""

class BanManager:
    """Gestiona baneos globales y locales entre múltiples bots"""

    def __init__(self, db_manager):
        """
        Args:
            db_manager: Instancia de DBManager para persistencia
        """
        self.db = db_manager
        self.local_bans = set()  # Cache en memoria para rápido acceso
        self.load_from_db()

    def load_from_db(self):
        """Carga la lista de baneos desde BD"""
        bans_data = self.db.get("GLOBAL_BANS", {"users": [], "hashes": []})
        self.local_bans = set(str(uid) for uid in bans_data.get("users", []))

    def is_banned(self, uid: str) -> bool:
        """Verifica si un UID está baneado globalmente"""
        return str(uid) in self.local_bans

    def ban_user(self, uid: str, reason: str = "", source: str = "manual") -> bool:
        """
        Baña un usuario globalmente

        Args:
            uid: User ID a banear
            reason: Razón del baneo
            source: Fuente del baneo (manual, cas, spam, etc)

        Returns:
            True si se baneó, False si ya estaba baneado
        """
        uid_str = str(uid)

        if uid_str in self.local_bans:
            return False  # Ya estaba baneado

        # Añadir a caché local
        self.local_bans.add(uid_str)

        # Guardar en BD
        bans_data = self.db.get("GLOBAL_BANS", {"users": [], "hashes": []})
        if uid_str not in bans_data["users"]:
            bans_data["users"].append(uid_str)

        # Registrar información del baneo
        ban_record = {
            "uid": uid_str,
            "reason": reason,
            "source": source,
            "timestamp": datetime.datetime.now().isoformat(),
        }

        ban_history = self.db.get("BAN_HISTORY", [])
        ban_history.append(ban_record)

        self.db.set("GLOBAL_BANS", bans_data)
        self.db.set("BAN_HISTORY", ban_history[-1000:])  # Mantener últimos 1000

        return True

    def unban_user(self, uid: str) -> bool:
        """
        Quita baneo a un usuario

        Args:
            uid: User ID a desbanear

        Returns:
            True si se desbaneó, False si no estaba baneado
        """
        uid_str = str(uid)

        if uid_str not in self.local_bans:
            return False

        # Remover de caché local
        self.local_bans.discard(uid_str)

        # Remover de BD
        bans_data = self.db.get("GLOBAL_BANS", {"users": [], "hashes": []})
        if uid_str in bans_data["users"]:
            bans_data["users"].remove(uid_str)

        self.db.set("GLOBAL_BANS", bans_data)

        return True

    def get_all_bans(self) -> dict:
        """Obtiene todos los baneos (usuarios y hashes)"""
        return self.db.get("GLOBAL_BANS", {"users": [], "hashes": []})

    def get_ban_history(self, limit: int = 100) -> list:
        """Obtiene historial de baneos recientes"""
        history = self.db.get("BAN_HISTORY", [])
        return history[-limit:]

    def get_ban_stats(self) -> dict:
        """Obtiene estadísticas de baneos"""
        bans_data = self.get_all_bans()
        history = self.get_ban_history(1000)

        # Contar por fuente
        sources = {}
        for record in history:
            source = record.get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1

        return {
            "total_banned_users": len(bans_data.get("users", [])),
            "total_banned_hashes": len(bans_data.get("hashes", [])),
            "recent_bans": len([r for r in history if (
                datetime.datetime.fromisoformat(r["timestamp"]) >
                datetime.datetime.now() - datetime.timedelta(days=1)
            )]),
            "sources": sources
        }

    def sync_with_cas(self, uid: str, cas_banned: bool) -> bool:
        """
        Sincroniza estado de baneo con CAS

        Args:
            uid: User ID
            cas_banned: True si está baneado en CAS

        Returns:
            True si se realizó algún cambio
        """
        if cas_banned and not self.is_banned(uid):
            # Usuario está en CAS pero no en nuestro local
            self.ban_user(uid, reason="Auto-sync from CAS", source="cas")
            return True

        return False


import datetime

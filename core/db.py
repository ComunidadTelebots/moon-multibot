import json
import sqlite3
import threading

from .config import DB_PATH


class DBManager:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS kv_store (key TEXT PRIMARY KEY, value TEXT)")
        self.conn.commit()
        self.lock = threading.Lock()

    def get(self, key, default=None):
        with self.lock:
            self.cursor.execute("SELECT value FROM kv_store WHERE key=?", (key,))
            res = self.cursor.fetchone()
            return json.loads(res[0]) if res else default

    def set(self, key, value):
        with self.lock:
            self.cursor.execute("INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)", (key, json.dumps(value)))
            self.conn.commit()

    def keys(self, prefix=None):
        with self.lock:
            if prefix is None:
                self.cursor.execute("SELECT key FROM kv_store")
            else:
                self.cursor.execute("SELECT key FROM kv_store WHERE key LIKE ?", (f"{prefix}%",))
            return [row[0] for row in self.cursor.fetchall()]

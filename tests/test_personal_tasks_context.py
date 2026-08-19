import unittest
import json
from pathlib import Path

from flask import Flask
import core.routes_public as routes
from plugins.todo_manager import add_task, list_tasks, update_task

ROOT = Path(__file__).parents[1]
HUB = (ROOT / "web" / "hub.html").read_text(encoding="utf-8")


class MemoryDB:
    def __init__(self): self.values = {}
    def get(self, key, default=None): return self.values.get(key, default)
    def set(self, key, value): self.values[key] = value


class PersonalTaskContextTests(unittest.TestCase):
    def test_store_is_isolated_and_migrates_legacy_strings(self):
        db = MemoryDB(); db.set("PLUGIN_TODO_-1001_10", ["Tarea antigua"])
        self.assertEqual(list_tasks(db, "10", "-1001")[0]["title"], "Tarea antigua")
        add_task(db, "10", "-1001", "Grupo A"); add_task(db, "10", "-1002", "Grupo B")
        self.assertEqual(len(list_tasks(db, "10", "-1001")), 2)
        self.assertEqual(len(list_tasks(db, "10", "-1002")), 1)
        self.assertEqual(list_tasks(db, "11", "-1001"), [])

    def test_complete_reopen_and_delete(self):
        db = MemoryDB(); rows = add_task(db, "10", None, "Personal"); task_id = rows[0]["id"]
        self.assertTrue(update_task(db, "10", None, task_id, done=True)[0]["done"])
        self.assertFalse(update_task(db, "10", None, task_id, done=False)[0]["done"])
        self.assertEqual(update_task(db, "10", None, task_id, delete=True), [])

    def test_internal_inspector_requires_admin_key(self):
        app = Flask(__name__); app.register_blueprint(routes.bp); original = routes._internal_admin_authorized
        try:
            routes._internal_admin_authorized = lambda: False
            self.assertEqual(app.test_client().post("/api/internal/security/url-inspect", json={"url":"https://example.com"}).status_code, 401)
            routes._internal_admin_authorized = lambda: True
            response = app.test_client().post("/api/internal/security/url-inspect", json={"url":"https://example.com"})
            self.assertEqual(response.status_code, 200); self.assertEqual(response.get_json()["inspection"]["host"], "example.com")
        finally: routes._internal_admin_authorized = original

    def test_public_route_rejects_unverified_group_context(self):
        app = Flask(__name__); app.register_blueprint(routes.bp)
        original = routes._db, routes._verify_init_data, routes._miniapp_feature_context
        try:
            routes._db = MemoryDB(); routes._verify_init_data = lambda value: {"id": "10"} if value == "valid" else None
            routes._miniapp_feature_context = lambda user, group: (_ for _ in ()).throw(PermissionError()) if group == "-999" else ("user", [], None)
            client = app.test_client()
            self.assertEqual(client.post("/api/public/personal/tasks", json={"action":"list"}).status_code, 401)
            self.assertEqual(client.post("/api/public/personal/tasks", json={"initData":"valid","chat_id":"-999"}).status_code, 403)
        finally: routes._db, routes._verify_init_data, routes._miniapp_feature_context = original

    def test_hub_and_roadmap_expose_the_same_feature(self):
        for marker in ('id="userPersonalTasks"', 'id="personalTaskContext"', 'class="userchip"'):
            self.assertIn(marker, HUB)
        roadmap = json.loads((ROOT / "web" / "future-features.json").read_text(encoding="utf-8"))
        release = next(item for item in roadmap["recently_implemented"] if item["version"] == "v18.23.34")
        self.assertEqual(len(release["features"]), 2)


if __name__ == "__main__": unittest.main()

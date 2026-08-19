"""Tareas personales aisladas por usuario y contexto de chat."""

import datetime
import secrets


def task_key(user_id, chat_id=None):
    context = str(chat_id or "personal").strip()
    return f"PLUGIN_TODO_{context}_{str(user_id).strip()}"


def list_tasks(db, user_id, chat_id=None):
    rows = db.get(task_key(user_id, chat_id), []) or []
    normalized = []
    for index, row in enumerate(rows[-100:]):
        if isinstance(row, dict):
            title = str(row.get("title") or "").strip()
            if title:
                normalized.append({"id": str(row.get("id") or f"legacy-{index}"), "title": title[:240],
                    "done": bool(row.get("done", False)), "created_at": str(row.get("created_at") or "")[:40]})
        elif str(row).strip():
            normalized.append({"id": f"legacy-{index}", "title": str(row).strip()[:240], "done": False, "created_at": ""})
    return normalized


def save_tasks(db, user_id, chat_id, rows):
    db.set(task_key(user_id, chat_id), rows[-100:])
    return rows[-100:]


def add_task(db, user_id, chat_id, title):
    title = str(title or "").strip()
    if not title: raise ValueError("título obligatorio")
    rows = list_tasks(db, user_id, chat_id)
    rows.append({"id": secrets.token_hex(8), "title": title[:240], "done": False,
                 "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()})
    return save_tasks(db, user_id, chat_id, rows)


def update_task(db, user_id, chat_id, task_id, *, done=None, delete=False):
    rows = list_tasks(db, user_id, chat_id); task_id = str(task_id or "")
    if delete: rows = [row for row in rows if row["id"] != task_id]
    elif done is not None:
        for row in rows:
            if row["id"] == task_id: row["done"] = bool(done)
    return save_tasks(db, user_id, chat_id, rows)


def handle_command(bot, cid, uid, text, rank):
    t = text.strip(); low = t.lower()
    if not (low.startswith("/todo") or low == "/todos"): return False
    from moon_multibot import db
    todos = list_tasks(db, uid, cid)
    if low == "/todos":
        visible = [row for row in todos if not row["done"]]
        bot.send_msg(cid, "No tienes tareas." if not visible else "Tus tareas:\n" + "\n".join(f"{i+1}. {row['title']}" for i, row in enumerate(visible[:50])))
        return True
    parts = t.split(maxsplit=2)
    if len(parts) < 2:
        bot.send_msg(cid, "Uso: /todo add <tarea> | /todo done <num> | /todos"); return True
    action = parts[1].lower()
    if action == "add" and len(parts) >= 3:
        add_task(db, uid, cid, parts[2]); bot.send_msg(cid, "Tarea agregada."); return True
    if action == "done" and len(parts) >= 3 and parts[2].isdigit():
        visible = [row for row in todos if not row["done"]]; idx = int(parts[2]) - 1
        if 0 <= idx < len(visible):
            update_task(db, uid, cid, visible[idx]["id"], done=True); bot.send_msg(cid, f"Completada: {visible[idx]['title'][:40]}"); return True
        bot.send_msg(cid, "Índice inválido."); return True
    bot.send_msg(cid, "Uso: /todo add <tarea> | /todo done <num> | /todos"); return True

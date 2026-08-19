"""Persistent Telegram user assignments for simulator release channels."""

from core.feature_access import normalize_release_channel

COLLECTION = "feature_release_access"


def ensure_schema(pb):
    fields = [
        {"name": "telegram_id", "type": "text", "required": True},
        {"name": "display_name", "type": "text"},
        {"name": "release_channel", "type": "text", "required": True},
        {"name": "enabled", "type": "bool"},
        {"name": "assigned_by", "type": "text"},
        {"name": "assigned_at", "type": "date"},
    ]
    pb.ensure_collection(COLLECTION, fields, [
        "CREATE UNIQUE INDEX `idx_release_telegram` ON `feature_release_access` (`telegram_id`)"
    ])
    for field in fields:
        pb.ensure_field(COLLECTION, field)


def list_assignments(pb):
    return pb.list(COLLECTION, sort="-updated", per_page=500)


def assign(pb, telegram_id, channel, *, display_name="", assigned_by="", assigned_at=""):
    user_id = str(telegram_id or "").strip()
    if not user_id.isdigit():
        raise ValueError("telegram_id debe ser numérico")
    value = str(channel or "").strip().lower()
    if value not in {"stable", "rc", "beta", "alpha"}:
        raise ValueError("canal no válido")
    payload = {
        "telegram_id": user_id,
        "display_name": str(display_name or "")[:120],
        "release_channel": normalize_release_channel(value),
        "enabled": True,
        "assigned_by": str(assigned_by or ""),
        "assigned_at": assigned_at,
    }
    return pb.upsert(COLLECTION, f"telegram_id='{pb.esc(user_id)}'", payload)


def revoke(pb, telegram_id):
    user_id = str(telegram_id or "").strip()
    record = pb.first(COLLECTION, f"telegram_id='{pb.esc(user_id)}'")
    if record:
        pb.update(COLLECTION, record["id"], {"enabled": False})
    return bool(record)

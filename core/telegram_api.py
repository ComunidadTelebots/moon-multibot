import requests


TELEGRAM_BOT_API_VERSION = "9.6"

DEPRECATED_METHOD_ALIASES = {
    "kickChatMember": "banChatMember",
}

DEFAULT_ALLOWED_UPDATES = [
    "message",
    "edited_message",
    "channel_post",
    "edited_channel_post",
    "business_connection",
    "business_message",
    "edited_business_message",
    "deleted_business_messages",
    "callback_query",
    "my_chat_member",
    "chat_member",
    "chat_join_request",
    "chat_boost",
    "removed_chat_boost",
    "purchased_paid_media",
    "poll",
    "poll_answer",
    "managed_bot",
    "guest_message",
    "guest_interaction",
]

GUEST_UPDATE_FIELDS = (
    "guest_message",
    "guest_interaction",
    "guest_bot",
)


def normalize_method(method):
    return DEPRECATED_METHOD_ALIASES.get(method, method)


def telegram_api_call(session, base_url, method, params=None, files=None, timeout=35):
    method = normalize_method(method)
    params = params or {}
    try:
        if files:
            response = session.post(base_url + method, data=params, files=files, timeout=timeout)
        else:
            response = session.post(base_url + method, json=params, timeout=timeout)
        try:
            data = response.json()
        except ValueError:
            return {
                "ok": False,
                "description": f"Telegram returned non-JSON response ({response.status_code})",
            }
        if not isinstance(data, dict):
            return {"ok": False, "description": "Telegram returned an invalid payload"}
        return data
    except requests.exceptions.RequestException as exc:
        return {"ok": False, "description": str(exc)}


def build_get_updates_payload(offset, timeout=20, allowed_updates=None):
    return {
        "offset": offset + 1,
        "timeout": timeout,
        "allowed_updates": allowed_updates or DEFAULT_ALLOWED_UPDATES,
    }


def extract_guest_update(update):
    for field in GUEST_UPDATE_FIELDS:
        value = update.get(field)
        if isinstance(value, dict):
            return field, value
    return None, None

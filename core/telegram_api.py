import re
import time
import requests


TELEGRAM_BOT_API_VERSION = "10.2"

RICH_MARKDOWN_MODES = {"richmarkdown", "rich_markdown", "rich-markdown"}
RICH_MESSAGE_MAX_CHARS = 32768
RICH_MESSAGE_MAX_BLOCKS = 500
RICH_MESSAGE_MAX_MEDIA = 50

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
    "inline_query",
    "chosen_inline_result",
    "callback_query",
    "my_chat_member",
    "chat_member",
    "chat_join_request",
    "chat_boost",
    "removed_chat_boost",
    "purchased_paid_media",
    "poll",
    "poll_answer",
    "message_reaction",
    "message_reaction_count",
    "managed_bot",
    "subscription",
]

GUEST_UPDATE_FIELDS = (
    "guest_message",
    "guest_interaction",
    "guest_bot",
)


def normalize_method(method):
    return DEPRECATED_METHOD_ALIASES.get(method, method)


def is_rich_markdown_mode(parse_mode):
    return str(parse_mode or "").strip().lower() in RICH_MARKDOWN_MODES


def build_input_rich_message(markdown=None, html=None, blocks=None, media=None,
                             is_rtl=False, skip_entity_detection=False):
    """Build and validate the Bot API 10.2 InputRichMessage payload."""
    provided = sum(value is not None for value in (markdown, html, blocks))
    if provided != 1:
        raise ValueError("exactly one of markdown, html or blocks is required")
    payload = {}
    if markdown is not None:
        markdown = str(markdown)
        if len(markdown) > RICH_MESSAGE_MAX_CHARS:
            raise ValueError("rich markdown exceeds 32768 characters")
        payload["markdown"] = markdown
    elif html is not None:
        html = str(html)
        if len(html) > RICH_MESSAGE_MAX_CHARS:
            raise ValueError("rich HTML exceeds 32768 characters")
        payload["html"] = html
    else:
        if not isinstance(blocks, list) or len(blocks) > RICH_MESSAGE_MAX_BLOCKS:
            raise ValueError("rich message blocks must be a list of at most 500 items")
        payload["blocks"] = blocks
    if media is not None:
        if not isinstance(media, list) or len(media) > RICH_MESSAGE_MAX_MEDIA:
            raise ValueError("rich message media must be a list of at most 50 items")
        clean_media = []
        for item in media:
            if not isinstance(item, dict):
                raise ValueError("each rich message media item must be an object")
            media_id = str(item.get("id") or "")
            media_value = item.get("media")
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", media_id):
                raise ValueError("rich message media id must contain 1-64 letters, numbers, _ or -")
            if not isinstance(media_value, dict):
                raise ValueError("rich message media payload must be an object")
            media_type = str(media_value.get("type") or "")
            if media_type not in {"animation", "audio", "photo", "video", "voice_note"}:
                raise ValueError("unsupported rich message media type")
            if not str(media_value.get("media") or "").strip():
                raise ValueError("rich message media file or URL is required")
            clean_media.append({"id": media_id, "media": media_value})
        payload["media"] = clean_media
    if is_rtl:
        payload["is_rtl"] = True
    if skip_entity_detection:
        payload["skip_entity_detection"] = True
    return payload


def telegram_api_call(session, base_url, method, params=None, files=None, timeout=35, _retries=3):
    method = normalize_method(method)
    params = params or {}
    for attempt in range(_retries):
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
            # Manejo de rate limit 429: esperar retry_after y reintentar
            if not data.get("ok") and data.get("error_code") == 429:
                retry_after = data.get("parameters", {}).get("retry_after", 5)
                time.sleep(retry_after)
                continue
            return data
        except requests.exceptions.ConnectionError:
            if attempt < _retries - 1:
                time.sleep(2 ** attempt)
                continue
            return {"ok": False, "description": "Connection error after retries"}
        except requests.exceptions.Timeout:
            if attempt < _retries - 1:
                time.sleep(2 ** attempt)
                continue
            return {"ok": False, "description": "Timeout after retries"}
        except requests.exceptions.RequestException as exc:
            return {"ok": False, "description": str(exc)}
    return {"ok": False, "description": "Max retries exceeded"}


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

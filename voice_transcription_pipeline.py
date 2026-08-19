"""Pure safety boundary for voice-note transcription.

This module validates and plans work. It deliberately performs no network,
filesystem, decoding, or transcription operations.
"""

import datetime as _datetime
import math
import pathlib
import secrets


MAX_VOICE_BYTES = 20 * 1024 * 1024
MAX_VOICE_DURATION_SECONDS = 10 * 60
ALLOWED_VOICE_MIME_TYPES = {
    "audio/ogg": ".ogg",
    "audio/opus": ".opus",
    "audio/webm": ".webm",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
}
CONSENT_KEY_PREFIX = "voice_transcription_consent:"


class VoicePipelineError(ValueError):
    """A safe, normalized pipeline rejection."""

    def __init__(self, code, message, field=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.field = field

    def as_dict(self):
        value = {"code": self.code, "message": self.message, "retryable": False}
        if self.field:
            value["field"] = self.field
        return value


def _positive_number(value, field):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise VoicePipelineError("INVALID_METADATA", f"{field} debe ser un número positivo.", field)
    return value


def validate_voice_metadata(metadata):
    """Return a small trusted metadata object or raise ``VoicePipelineError``."""
    if not isinstance(metadata, dict):
        raise VoicePipelineError("INVALID_METADATA", "Los metadatos de voz no son válidos.")

    file_id = str(metadata.get("file_id") or "").strip()
    if not file_id or len(file_id) > 512:
        raise VoicePipelineError("INVALID_METADATA", "Falta un identificador de archivo válido.", "file_id")

    size = int(_positive_number(metadata.get("file_size"), "file_size"))
    if size > MAX_VOICE_BYTES:
        raise VoicePipelineError("FILE_TOO_LARGE", "La nota de voz supera el límite de 20 MiB.", "file_size")

    duration = float(_positive_number(metadata.get("duration"), "duration"))
    if duration > MAX_VOICE_DURATION_SECONDS:
        raise VoicePipelineError("DURATION_TOO_LONG", "La nota de voz supera el límite de 10 minutos.", "duration")

    mime_type = str(metadata.get("mime_type") or "").split(";", 1)[0].strip().lower()
    if mime_type not in ALLOWED_VOICE_MIME_TYPES:
        raise VoicePipelineError("UNSUPPORTED_MIME", "El formato de audio no es compatible.", "mime_type")

    return {
        "file_id": file_id,
        "file_unique_id": str(metadata.get("file_unique_id") or "").strip()[:128] or None,
        "file_size": size,
        "duration": duration,
        "mime_type": mime_type,
    }


def _consent_key(group_id):
    group = str(group_id or "").strip()
    if not group:
        raise VoicePipelineError("INVALID_GROUP", "Falta el identificador del grupo.", "group_id")
    return CONSENT_KEY_PREFIX + group


def get_group_transcription_consent(storage, group_id):
    value = storage.get(_consent_key(group_id), {}) if storage else {}
    if not isinstance(value, dict):
        value = {}
    return {
        "enabled": value.get("enabled") is True,
        "updated_at": value.get("updated_at"),
        "updated_by": value.get("updated_by"),
    }


def set_group_transcription_consent(storage, group_id, enabled, actor_id, now=None):
    if not storage or not hasattr(storage, "set"):
        raise VoicePipelineError("STORAGE_UNAVAILABLE", "No se puede guardar el consentimiento del grupo.")
    if not actor_id:
        raise VoicePipelineError("ACTOR_REQUIRED", "Falta el responsable del cambio.", "actor_id")
    timestamp = now or _datetime.datetime.now(_datetime.timezone.utc).isoformat()
    value = {"enabled": enabled is True, "updated_at": timestamp, "updated_by": str(actor_id)}
    storage.set(_consent_key(group_id), value)
    return value.copy()


def voice_deletion_policy():
    """Policy an executor must enforce around its temporary download."""
    return {
        "delete_on": ["completed", "failed", "cancelled"],
        "delete_before_return": True,
        "best_effort_on_process_exit": True,
        "max_retention_seconds": 15 * 60,
        "retain_source": False,
        "retain_transcript": False,
    }


def build_voice_download_plan(metadata, consent, temp_directory, token_factory=None):
    """Create a download plan, without creating or downloading a file."""
    trusted = validate_voice_metadata(metadata)
    if not isinstance(consent, dict) or consent.get("enabled") is not True:
        raise VoicePipelineError("CONSENT_REQUIRED", "La transcripción no está habilitada para este grupo.")
    root = pathlib.Path(temp_directory).resolve()
    opaque_token = (token_factory or (lambda: secrets.token_hex(16)))()
    if not isinstance(opaque_token, str) or not opaque_token.isalnum() or len(opaque_token) < 16:
        raise VoicePipelineError("INVALID_TEMP_TOKEN", "No se pudo generar un nombre temporal seguro.")
    filename = f"voice-{opaque_token}{ALLOWED_VOICE_MIME_TYPES[trusted['mime_type']]}"
    return {
        "status": "ready",
        "metadata": trusted,
        "temporary_path": str(root / filename),
        "temporary_name": filename,
        "deletion": voice_deletion_policy(),
        "network_performed": False,
        "transcription_performed": False,
    }


def normalize_transcription_result(text=None, error=None, language=None):
    """Normalize an adapter result; never manufactures transcript content."""
    if error is not None:
        if isinstance(error, VoicePipelineError):
            safe_error = error.as_dict()
        else:
            safe_error = {"code": "TRANSCRIPTION_FAILED", "message": "No se pudo transcribir la nota de voz.", "retryable": True}
        return {"ok": False, "status": "failed", "text": None, "language": None, "error": safe_error, "delete_temporary": True}
    cleaned = text.strip() if isinstance(text, str) else ""
    if not cleaned:
        safe_error = {"code": "EMPTY_TRANSCRIPT", "message": "El audio no contiene texto reconocible.", "retryable": False}
        return {"ok": False, "status": "failed", "text": None, "language": None, "error": safe_error, "delete_temporary": True}
    return {"ok": True, "status": "completed", "text": cleaned, "language": str(language or "und"), "error": None, "delete_temporary": True}

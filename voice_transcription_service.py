"""Real Telegram voice transcription executor with strict cleanup and no fake fallback."""

import os
import tempfile

import requests

from voice_transcription_pipeline import VoicePipelineError, build_voice_download_plan, normalize_transcription_result


def transcribe_telegram_voice(bot, voice, config, api_key=None, temp_directory=None):
    if not isinstance(config, dict) or config.get("enabled") is not True:
        return normalize_transcription_result(error=VoicePipelineError("CONSENT_REQUIRED", "La transcripción no está habilitada para este grupo."))
    metadata = {"file_id": (voice or {}).get("file_id"), "file_unique_id": (voice or {}).get("file_unique_id"), "file_size": (voice or {}).get("file_size"), "duration": (voice or {}).get("duration"), "mime_type": (voice or {}).get("mime_type") or "audio/ogg"}
    try:
        plan = build_voice_download_plan(metadata, {"enabled": True}, temp_directory or tempfile.gettempdir())
    except VoicePipelineError as error:
        return normalize_transcription_result(error=error)
    path = plan["temporary_path"]
    try:
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise VoicePipelineError("PROVIDER_UNAVAILABLE", "El proveedor de transcripción no está configurado.")
        file_info = bot.api_call("getFile", {"file_id": plan["metadata"]["file_id"]}, silent=True)
        remote_path = str(((file_info or {}).get("result") or {}).get("file_path") or "") if isinstance(file_info, dict) and file_info.get("ok") else ""
        if not remote_path:
            raise VoicePipelineError("TELEGRAM_FILE_UNAVAILABLE", "Telegram no pudo preparar la nota de voz.")
        downloaded = 0
        with requests.get(f"https://api.telegram.org/file/bot{bot.token}/{remote_path}", stream=True, timeout=(5, 30)) as response:
            response.raise_for_status()
            with open(path, "xb") as target:
                for chunk in response.iter_content(64 * 1024):
                    if not chunk:
                        continue
                    downloaded += len(chunk)
                    if downloaded > plan["metadata"]["file_size"] or downloaded > 20 * 1024 * 1024:
                        raise VoicePipelineError("FILE_TOO_LARGE", "La descarga supera el tamaño declarado.")
                    target.write(chunk)
        from openai import OpenAI
        client = OpenAI(api_key=key, timeout=45.0, max_retries=1)
        with open(path, "rb") as audio:
            kwargs = {"model": config.get("model") or "whisper-1", "file": audio}
            if config.get("language"):
                kwargs["language"] = config["language"]
            transcript = client.audio.transcriptions.create(**kwargs)
        return normalize_transcription_result(text=getattr(transcript, "text", None), language=config.get("language") or "und")
    except VoicePipelineError as error:
        return normalize_transcription_result(error=error)
    except Exception as error:
        return normalize_transcription_result(error=error)
    finally:
        try:
            if os.path.exists(path): os.remove(path)
        except OSError:
            pass

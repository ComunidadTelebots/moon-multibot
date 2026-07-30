import os
import tempfile
import unittest
from unittest import mock

from voice_transcription_service import transcribe_telegram_voice


VOICE = {"file_id": "abc", "file_unique_id": "u", "file_size": 8, "duration": 2, "mime_type": "audio/ogg"}


class Bot:
    token = "secret-token"
    def __init__(self): self.calls = []
    def api_call(self, method, payload, silent=False):
        self.calls.append((method, payload, silent))
        return {"ok": True, "result": {"file_path": "voice/file.ogg"}}


class VoiceServiceTests(unittest.TestCase):
    def test_disabled_consent_performs_no_telegram_or_network(self):
        bot = Bot()
        result = transcribe_telegram_voice(bot, VOICE, {"enabled": False})
        self.assertFalse(result["ok"]); self.assertEqual(bot.calls, [])

    def test_missing_provider_never_creates_fake_text(self):
        bot = Bot()
        with mock.patch.dict(os.environ, {}, clear=True):
            result = transcribe_telegram_voice(bot, VOICE, {"enabled": True})
        self.assertFalse(result["ok"]); self.assertIsNone(result["text"])
        self.assertEqual(result["error"]["code"], "PROVIDER_UNAVAILABLE")

    def test_failed_download_always_removes_temporary_file(self):
        bot = Bot()
        with tempfile.TemporaryDirectory() as folder, mock.patch.dict(os.environ, {"OPENAI_API_KEY": "x"}), mock.patch("voice_transcription_service.requests.get", side_effect=RuntimeError("offline")):
            result = transcribe_telegram_voice(bot, VOICE, {"enabled": True}, temp_directory=folder)
            self.assertFalse(result["ok"])
            self.assertEqual(os.listdir(folder), [])


if __name__ == "__main__": unittest.main()

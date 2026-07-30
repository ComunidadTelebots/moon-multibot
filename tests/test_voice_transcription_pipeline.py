import os
import unittest

from voice_transcription_pipeline import (
    VoicePipelineError,
    build_voice_download_plan,
    get_group_transcription_consent,
    normalize_transcription_result,
    set_group_transcription_consent,
    validate_voice_metadata,
)


class MemoryStorage:
    def __init__(self):
        self.values = {}

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value):
        self.values[key] = value


VALID_METADATA = {
    "file_id": "telegram-file-id",
    "file_unique_id": "stable-id",
    "file_size": 1024,
    "duration": 12,
    "mime_type": "audio/ogg; codecs=opus",
}


class VoiceTranscriptionPipelineTests(unittest.TestCase):
    def test_metadata_is_normalized(self):
        result = validate_voice_metadata(VALID_METADATA)
        self.assertEqual(result["mime_type"], "audio/ogg")
        self.assertEqual(result["file_size"], 1024)

    def test_rejects_unsafe_metadata(self):
        cases = [
            ({**VALID_METADATA, "file_size": 21 * 1024 * 1024}, "FILE_TOO_LARGE"),
            ({**VALID_METADATA, "duration": 601}, "DURATION_TOO_LONG"),
            ({**VALID_METADATA, "mime_type": "application/octet-stream"}, "UNSUPPORTED_MIME"),
            ({**VALID_METADATA, "file_size": 0}, "INVALID_METADATA"),
            ({**VALID_METADATA, "duration": float("nan")}, "INVALID_METADATA"),
        ]
        for metadata, code in cases:
            with self.subTest(code=code), self.assertRaises(VoicePipelineError) as raised:
                validate_voice_metadata(metadata)
            self.assertEqual(raised.exception.code, code)

    def test_consent_is_explicit_and_scoped_per_group(self):
        storage = MemoryStorage()
        self.assertFalse(get_group_transcription_consent(storage, "group-a")["enabled"])
        set_group_transcription_consent(storage, "group-a", True, "admin-1", now="2026-07-30T00:00:00+00:00")
        self.assertTrue(get_group_transcription_consent(storage, "group-a")["enabled"])
        self.assertFalse(get_group_transcription_consent(storage, "group-b")["enabled"])

    def test_plan_requires_consent_and_uses_opaque_name(self):
        with self.assertRaises(VoicePipelineError) as raised:
            build_voice_download_plan(VALID_METADATA, {"enabled": False}, "/safe/temp")
        self.assertEqual(raised.exception.code, "CONSENT_REQUIRED")

        plan = build_voice_download_plan(
            VALID_METADATA, {"enabled": True}, "/safe/temp",
            token_factory=lambda: "a1b2c3d4e5f60708",
        )
        self.assertEqual(plan["temporary_name"], "voice-a1b2c3d4e5f60708.ogg")
        self.assertEqual(os.path.basename(plan["temporary_path"]), plan["temporary_name"])
        self.assertFalse(plan["network_performed"])
        self.assertFalse(plan["transcription_performed"])
        self.assertTrue(plan["deletion"]["delete_before_return"])

    def test_results_and_unknown_errors_are_normalized(self):
        success = normalize_transcription_result("  texto real del adaptador  ", language="es")
        self.assertTrue(success["ok"])
        self.assertEqual(success["text"], "texto real del adaptador")
        self.assertTrue(success["delete_temporary"])

        failure = normalize_transcription_result(error=RuntimeError("secret detail"))
        self.assertFalse(failure["ok"])
        self.assertEqual(failure["error"]["code"], "TRANSCRIPTION_FAILED")
        self.assertNotIn("secret detail", failure["error"]["message"])


if __name__ == "__main__":
    unittest.main()

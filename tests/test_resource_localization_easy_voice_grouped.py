"""Per-ID tests for the Moonbot future-5042..future-5159 lot."""

import importlib
import unittest

import resource_localization_easy_reading_engines as easy
import resource_voice_grouped_notification_engines as voice
from resource_localization_easy_voice_grouped_manifest import MANIFEST


LOCALIZATION_PAYLOADS = (
    {"panel_id": "master-1", "title": "Panel principal", "visible_widgets": ["grupos", "seguridad"], "updated_at": "2026-07-30T10:00:00Z"},
    {"directory_id": "directory-1", "title": "Canales", "entry_count": 1500, "verified_count": 1200},
    {"url": "https://example.org/info", "label": "Información", "reputation": "safe", "checked_at": "2026-07-30T10:00:00Z"},
)


def _test_localization(index):
    def test(self):
        result = easy.LOCALIZATION_APIS[index](LOCALIZATION_PAYLOADS[index], "es-ES")
        self.assertEqual(result["feature_id"], easy.IDS[index])
        self.assertEqual(result["locale"], "es-ES")
        self.assertEqual(result["direction"], "ltr")
        self.assertTrue(result["identifiers_preserved"])
        self.assertFalse(result["user_content_translated"])
        self.assertFalse(result["executed"])
    return test


def _test_easy(index):
    def test(self):
        jargon = next(iter(easy._EASY_SPECS[index][1]))
        content = {
            "title": "Información clara",
            "summary": f"El término {jargon} aparece en @CanalOficial. Esta frase explica qué ha ocurrido de una forma que se puede comprobar.",
            "steps": ["Revise la información y siga el paso indicado."],
            "warnings": ["No comparta datos privados."],
        }
        result = easy.EASY_READ_APIS[index](content, max_words=12)
        self.assertEqual(result["feature_id"], easy.IDS[3 + index])
        self.assertEqual(result["reading_level"], "easy")
        self.assertIn(jargon, result["glossary_terms_used"])
        self.assertIn("@CanalOficial", result["plain_text"])
        self.assertTrue(all(len(row["text"].split()) <= 12 for row in result["sentences"]))
        self.assertFalse(result["executed"])
    return test


def _test_voice(index):
    def test(self):
        result = voice.VOICE_APIS[index]("listar", locale="es")
        self.assertEqual(result["feature_id"], voice.IDS[index])
        self.assertTrue(result["matched"])
        self.assertEqual(result["intent"], "list")
        self.assertFalse(result["requires_confirmation"])
        self.assertFalse(result["executed"])
    return test


def _group_events(index):
    resource, entity_field, kinds = voice._GROUP_SPECS[index]
    kind = sorted(kinds)[0]
    base = {
        entity_field: f"{resource}-1", "kind": kind, "severity": "warning",
        "occurred_at": "2026-07-30T10:05:00Z", "title": "Cambio detectado",
        "details": {"token": "must-not-leak"},
    }
    first = {**base, "id": f"event-{index}-a"}
    second = {**base, "id": f"event-{index}-b", "severity": "critical", "occurred_at": "2026-07-30T10:10:00Z"}
    return first, second


def _test_group(index):
    def test(self):
        first, second = _group_events(index)
        result = voice.GROUP_APIS[index]([first, first.copy(), second], window_minutes=30)
        self.assertEqual(result["feature_id"], voice.IDS[17 + index])
        self.assertEqual(result["input_count"], 3)
        self.assertEqual(result["unique_count"], 2)
        self.assertEqual(result["notification_count"], 1)
        self.assertEqual(result["notifications"][0]["severity"], "critical")
        self.assertFalse(result["delivery_requested"])
        self.assertFalse(result["executed"])
    return test


class ResourceLocalizationEasyVoiceGroupedPerIdTests(unittest.TestCase):
    pass


for _index, _entry in enumerate(MANIFEST):
    if _index < 3:
        _test = _test_localization(_index)
    elif _index < 20:
        _test = _test_easy(_index - 3)
    elif _index < 37:
        _test = _test_voice(_index - 20)
    else:
        _test = _test_group(_index - 37)
    setattr(
        ResourceLocalizationEasyVoiceGroupedPerIdTests,
        f"test_{_entry['id'].replace('-', '_')}",
        _test,
    )


class ResourceLocalizationEasyVoiceGroupedInvariantTests(unittest.TestCase):
    def test_manifest_contract_is_complete_and_callable(self):
        self.assertEqual(len(MANIFEST), 40)
        for entry in MANIFEST:
            self.assertEqual(set(entry), {"id", "title", "capability", "module", "api", "test", "preflight"})
            module = importlib.import_module(entry["module"].removesuffix(".py"))
            self.assertTrue(callable(getattr(module, entry["api"])))

    def test_destructive_voice_action_requires_confirmation(self):
        result = voice.navigate_temporary_roles_by_voice("revocar role-123", locale="es")
        self.assertTrue(result["matched"])
        self.assertTrue(result["requires_confirmation"])
        self.assertEqual(len(result["confirmation_token"]), 24)
        self.assertFalse(result["executed"])

    def test_voice_rejects_multi_command_transcript(self):
        with self.assertRaises(ValueError):
            voice.navigate_managed_groups_by_voice("listar\nsalir grupo-1")

    def test_grouping_rejects_wrong_event_kind(self):
        first, second = _group_events(0)
        second["kind"] = "campaign_click"
        with self.assertRaises(ValueError):
            voice.group_creator_accounts_notifications([first, second])

    def test_external_link_rejects_credentials(self):
        payload = dict(LOCALIZATION_PAYLOADS[2])
        payload["url"] = "https://user:secret@example.org/info"
        with self.assertRaises(ValueError):
            easy.localize_external_link(payload, "es-ES")


if __name__ == "__main__":
    unittest.main()

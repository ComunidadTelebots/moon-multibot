import unittest

from core.telegram_api import format_command_rich_markdown, looks_like_rich_markdown


class RichCommandMessagesTests(unittest.TestCase):
    def test_simple_command_response_gets_rich_heading(self):
        rendered = format_command_rich_markdown("/clima", "Madrid: 22 °C")
        self.assertTrue(rendered.startswith("## 🌤️ Tiempo"))
        self.assertIn("Madrid: 22 °C", rendered)

    def test_existing_rich_message_is_not_wrapped_twice(self):
        original = "## Informe\n\n| Dato | Valor |\n|---|---|\n| Riesgo | 10 |"
        self.assertTrue(looks_like_rich_markdown(original))
        self.assertEqual(format_command_rich_markdown("/info", original), original)

    def test_code_blocks_are_preserved(self):
        original = "```python\nprint('hola')\n```"
        self.assertEqual(format_command_rich_markdown("/man", original), original)

    def test_metrics_become_a_visual_table(self):
        rendered = format_command_rich_markdown(
            "/clima", "Temperatura: 22 °C\nHumedad: 40 %\nViento: 8 km/h"
        )
        self.assertIn("| Dato | Valor |", rendered)
        self.assertIn("| Temperatura | 22 °C |", rendered)
        self.assertIn("`INFORMACIÓN`", rendered)

    def test_errors_become_warning_cards(self):
        rendered = format_command_rich_markdown("/wiki", "No se pudo completar la consulta")
        self.assertIn("⚠️ Atención", rendered)
        self.assertIn("`REVISAR`", rendered)


if __name__ == "__main__":
    unittest.main()

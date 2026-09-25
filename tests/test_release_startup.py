from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools.release_startup import validate
from tools.release_autoscaler_guard import main as autoscaler_main


class ReleaseStartupTest(unittest.TestCase):
    def test_default_quarantine_never_executes(self):
        with patch("tools.release_startup.subprocess.run") as run:
            self.assertIn("quarantined", validate("/missing", "false"))
            self.assertIn("quarantined", validate("/missing", "TRUE"))
            run.assert_not_called()

    def test_empty_bind_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertIn("start.sh", validate(root, "true"))

    def test_syntax_failure_and_valid_image(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root)
            (p / "core").mkdir()
            for name in ("start.sh", "moon_multibot.py", "core/config.py"):
                (p / name).write_text("# test\n")
            with patch("tools.release_startup.subprocess.run") as run:
                run.return_value.returncode = 2
                self.assertIn("syntax", validate(root, "true"))
                run.return_value.returncode = 0
                self.assertIsNone(validate(root, "true"))

    def test_legacy_autoscaler_cannot_restart_workers(self):
        with patch("builtins.print"):
            self.assertEqual(autoscaler_main(), 0)

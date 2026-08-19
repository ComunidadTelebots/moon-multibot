import unittest

from core.plugin_security import validate_plugin_filename


class PluginFilenameSecurityTests(unittest.TestCase):
    def test_accepts_plain_python_plugin_filenames(self):
        for name in ["welcome.py", "anti_spam-v2.py", "plugin_1.py"]:
            with self.subTest(name=name):
                self.assertEqual(validate_plugin_filename(name), name)

    def test_rejects_traversal_absolute_and_non_plugin_names(self):
        names = [
        "../moon_multibot.py",
        "..\\moon_multibot.py",
        "/tmp/payload.py",
        "C:\\tmp\\payload.py",
        ".hidden.py",
        "payload.py.disabled",
        "payload.txt",
        "folder/payload.py",
        "",
        None,
        ]
        for name in names:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    validate_plugin_filename(name)

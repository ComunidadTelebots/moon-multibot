import pathlib
import unittest


class HubJoinCaptchaControlsTests(unittest.TestCase):
    def test_local_bulk_controls_remain_bound_after_global_settings_move(self):
        source = pathlib.Path("web/hub.html").read_text(encoding="utf-8")
        start = source.index("async function loadJoinCaptcha()")
        end = source.index("function bindDropdown", start)
        block = source[start:end]
        self.assertIn('document.getElementById("gjoinReverify").onclick', block)
        self.assertIn('document.getElementById("gjoinPreview").onclick', block)
        self.assertIn('const cancelBulk=document.getElementById("gjoinCancel")', block)
        self.assertIn('/group/join/reverify-all', block)
        self.assertIn('/group/join/reverify-control', block)


if __name__ == "__main__":
    unittest.main()

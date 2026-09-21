import tempfile
import unittest
from pathlib import Path
from core.traffic_control import TrafficControl, identity


class TrafficControlTest(unittest.TestCase):
    def test_pause_drains_and_persists_checkpoint_without_token(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / 'traffic.json')
            control = TrafficControl(path, node='worker', default_paused=False)
            url = 'https://api.telegram.org/botSECRET/'
            bot = identity(url)
            with control.admit(url) as admitted:
                self.assertTrue(admitted)
                paused = control.change(bot, True, 0)
                self.assertEqual(paused['inflight'], 1)
                # Nested sends in an already admitted processing batch may finish.
                with control.admit(url) as nested:
                    self.assertTrue(nested)
                control.checkpoint(url, 42)
            with control.admit(url) as admitted:
                self.assertFalse(admitted)
            self.assertEqual(control.status(bot)['inflight'], 0)
            reopened = TrafficControl(path, node='worker', default_paused=False)
            self.assertEqual(reopened.status(bot)['offset'], 42)
            self.assertTrue(reopened.status(bot)['paused'])
            self.assertNotIn('SECRET', Path(path).read_text())
            with self.assertRaises(ValueError):
                reopened.change(bot, False, 0)
            reopened.change(bot, False, 1, 45)
            with reopened.admit(url) as admitted:
                self.assertTrue(admitted)
            self.assertEqual(reopened.offset(url), 45)

    def test_corrupt_state_denies_traffic_and_disabled_mode_preserves_legacy(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'traffic.json'
            path.write_text('bad data')
            control = TrafficControl(str(path), node='worker')
            with control.admit('url') as admitted:
                self.assertFalse(admitted)
            legacy = TrafficControl(str(path), node='')
            with legacy.admit('url') as admitted:
                self.assertTrue(admitted)

    def test_default_standby_paused_and_cross_node_state_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / 'traffic.json')
            first = TrafficControl(path, node='first', default_paused=True)
            with first.admit('url') as admitted:
                self.assertFalse(admitted)
            first.change(identity('url'), False, 0)
            other = TrafficControl(path, node='other')
            with other.admit('url') as admitted:
                self.assertFalse(admitted)


if __name__ == '__main__':
    unittest.main()

import ast
import subprocess
import tempfile
import unittest
from pathlib import Path

from core.bot_governor import BotWorker


class GovernorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.seen = []
        self.worker = BotWorker(self.tmp.name, 'testbot', self.seen.append)

    def test_restart_recovers_pending_and_checkpoint(self):
        self.worker.submit({'update_id': 15, 'message': {'text': 'private'}})
        other = BotWorker(self.tmp.name, 'testbot', self.seen.append)
        self.assertEqual(other.offset(), 15)
        self.assertTrue(other.step())
        self.assertEqual(len(self.seen), 1)
        other.submit({'update_id': 15, 'message': {'text': 'private'}})
        self.assertFalse(other.step())
        self.assertNotIn('private', str(other.snapshot()))

    def test_failed_effect_is_not_replayed_and_blocks_following(self):
        def fail(update):
            self.seen.append(update)
            raise RuntimeError('uncertain send')
        self.worker.handler = fail
        self.worker.submit({'update_id': 1})
        self.worker.submit({'update_id': 2})
        self.assertTrue(self.worker.step())
        self.assertFalse(self.worker.step())
        self.assertEqual(len(self.seen), 1)
        self.assertEqual(self.worker.snapshot()['states']['uncertain'], 1)

    def test_full_queue_does_not_advance_checkpoint(self):
        self.worker.queue.capacity = 1
        self.worker.submit({'update_id': 1})
        with self.assertRaises(ValueError):
            self.worker.submit({'update_id': 2})
        self.assertEqual(self.worker.offset(), 1)

    def test_handler_preserves_original_plugin_dispatch(self):
        original = ast.parse(subprocess.check_output(['git', 'show', 'a36f9bc:moon_multibot.py']).decode('utf-8-sig'))
        run = next(n for n in ast.walk(original) if isinstance(n, ast.FunctionDef) and n.name == 'run')
        loop = next(n for n in ast.walk(run) if isinstance(n, ast.For) and isinstance(n.target, ast.Name) and n.target.id == 'u')
        current = ast.parse(Path('moon_multibot.py').read_text(encoding='utf-8-sig'))
        handler = next(n for n in ast.walk(current) if isinstance(n, ast.FunctionDef) and n.name == '_process_update')
        actual = next(n for n in handler.body if isinstance(n, ast.For))
        self.assertEqual([ast.dump(n) for n in loop.body[1:]], [ast.dump(n) for n in actual.body])

if __name__ == '__main__':
    unittest.main()

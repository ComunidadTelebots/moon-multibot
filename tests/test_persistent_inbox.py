import tempfile
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from core.persistent_inbox import PersistentInbox


class InboxTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'inbox.db'
        self.now = [1000]
        self.queue = PersistentInbox(self.path, clock=lambda: self.now[0])

    def test_duplicate_conflict_and_restart(self):
        first = self.queue.enqueue('bot:1', 'bot:chat', {'text': 'test'})
        self.assertEqual(PersistentInbox(self.path).enqueue('bot:1', 'bot:chat', {'text': 'test'}), first)
        with self.assertRaises(ValueError):
            self.queue.enqueue('bot:1', 'bot:chat', {'text': 'different'})

    def test_order_per_partition_allows_another_chat(self):
        for key, chat in [('1', 'a'), ('2', 'a'), ('3', 'b')]:
            self.queue.enqueue(key, chat, {'key': key})
        a = self.queue.claim('worker1')
        b = self.queue.claim('worker2')
        self.assertEqual(a['payload']['key'], '1')
        self.assertEqual(b['payload']['key'], '3')
        self.assertIsNone(self.queue.claim('worker3'))

    def test_claim_expiration_is_fenced_but_running_is_not_blindly_replayed(self):
        self.queue.enqueue('1', 'chat', {})
        old = self.queue.claim('worker1', seconds=1)
        self.now[0] += 2
        fresh = self.queue.claim('worker2')
        self.assertFalse(self.queue.start(old['id'], 'worker1', old['lease']))
        self.assertTrue(self.queue.start(fresh['id'], 'worker2', fresh['lease'], seconds=1))
        self.now[0] += 2
        self.assertIsNone(self.queue.claim('worker3'))
        self.assertEqual(self.queue.stats()['states']['uncertain'], 1)
        self.assertFalse(self.queue.finish(fresh['id'], 'worker2', fresh['lease']))

    def test_two_connections_cannot_claim_same_job(self):
        self.queue.enqueue('1', 'chat', {})
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = list(pool.map(lambda worker: PersistentInbox(self.path).claim(worker), ['worker1', 'worker2']))
        self.assertEqual(sum(job is not None for job in jobs), 1)

    def test_pause_reassigns_unstarted_work_and_completed_payload_is_cleared(self):
        first = self.queue.enqueue('1', 'chat', {'text': 'private'})
        old = self.queue.claim('worker1')
        self.queue.pause('worker1')
        self.assertFalse(self.queue.start(old['id'], 'worker1', old['lease']))
        job = self.queue.claim('worker2')
        self.assertTrue(self.queue.start(job['id'], 'worker2', job['lease']))
        self.assertTrue(self.queue.finish(job['id'], 'worker2', job['lease']))
        self.assertEqual(self.queue.enqueue('1', 'chat', {'text': 'private'}), first)
        with self.queue.transaction() as db:
            self.assertIsNone(db.execute('SELECT payload FROM jobs').fetchone()[0])
        self.assertNotIn('private', str(self.queue.stats()))

    def test_backpressure_does_not_evict_pending_jobs(self):
        queue = PersistentInbox(self.path, capacity=1)
        queue.enqueue('1', 'chat', {})
        with self.assertRaises(ValueError):
            queue.enqueue('2', 'chat', {})
        self.assertEqual(queue.stats()['states']['pending'], 1)

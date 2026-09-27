"""Single-host durable ingestion; one serialized plugin worker per bot.

Opt-in until each deployment's plugin state has been validated. No automatic
replay of jobs whose effects are uncertain, and no credentials in telemetry.
"""
import hashlib
import os
import threading
import time
from pathlib import Path

from core.persistent_inbox import PersistentInbox


class BotWorker:
    def __init__(self, directory, identity, handler, capacity=10000, maintenance=None):
        Path(directory).mkdir(parents=True, exist_ok=True, mode=0o700)
        self.identity = identity
        self.handler = handler
        self.maintenance = maintenance
        self.last_maintenance = 0
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.wake = threading.Event()
        self.queue = PersistentInbox(Path(directory) / (identity + '.sqlite3'), capacity=capacity)
        self.worker_id = identity + '-plugins'
        self.error = None
        with self.queue.transaction() as db:
            db.execute('CREATE TABLE IF NOT EXISTS checkpoint (id INTEGER PRIMARY KEY, offset INTEGER NOT NULL)')
        self.thread = None

    def offset(self):
        with self.queue.transaction() as db:
            row = db.execute('SELECT offset FROM checkpoint WHERE id=1').fetchone()
            return row[0] if row else 0

    def submit(self, update):
        identifier = update.get('update_id')
        if type(identifier) is not int or identifier < 0:
            raise ValueError('Invalid update identity')
        # A single partition preserves all shared plugin state within this bot.
        self.queue.enqueue(str(identifier), self.identity, update)
        with self.queue.transaction() as db:
            db.execute('INSERT INTO checkpoint VALUES(1,?) ON CONFLICT(id) DO UPDATE SET offset=MAX(offset,excluded.offset)', (identifier,))
        self.wake.set()
        return identifier

    def step(self):
        job = self.queue.claim(self.worker_id)
        if not job or not self.queue.start(job['id'], self.worker_id, job['lease'], seconds=3600):
            return False
        try:
            with self.lock:
                self.handler(job['payload'])
        except Exception:  # noqa: BLE001 - plugins may fail after a side effect
            self.error = 'processing_uncertain'
            self.queue.finish(job['id'], self.worker_id, job['lease'], success=False)
        else:
            if not self.queue.finish(job['id'], self.worker_id, job['lease']):
                self.error = 'processing_uncertain'
        return True

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        def loop():
            while not self.stop_event.is_set():
                try:
                    worked = self.step()
                    if self.maintenance and time.monotonic() - self.last_maintenance >= 30:
                        with self.lock:
                            self.maintenance()
                        self.last_maintenance = time.monotonic()
                    if worked:
                        continue
                except Exception:  # noqa: BLE001 - keep the supervisor alive
                    self.error = 'queue_unavailable'
                self.wake.wait(0.5)
                self.wake.clear()
        self.thread = threading.Thread(target=loop, name=self.worker_id, daemon=True)
        self.thread.start()

    def snapshot(self):
        return {'id': self.identity, 'processing_workers': 1,
                'running': bool(self.thread and self.thread.is_alive()),
                'error': self.error, **self.queue.stats()}


class BotGovernor:
    def __init__(self):
        self.lock = threading.Lock()
        self.workers = {}

    def register(self, bot):
        directory = os.getenv('MOON_GOVERNOR_PATH', '').strip()
        if not directory:
            return None
        identity = hashlib.sha256(bot.url.encode()).hexdigest()[:12]
        with self.lock:
            if identity in self.workers:
                raise ValueError('Bot already has a receiver in this process')
            Path(directory).mkdir(parents=True, exist_ok=True)
            owner = open(Path(directory) / (identity + '.lock'), 'a+b')  # noqa: SIM115 - lifetime ownership lock
            try:
                if os.name == 'nt':
                    import msvcrt
                    owner.seek(0)
                    owner.write(b'0')
                    owner.flush()
                    owner.seek(0)
                    msvcrt.locking(owner.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(owner.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                worker = BotWorker(directory, identity, bot._process_update, maintenance=bot.run_periodic_maintenance)
            except Exception:
                owner.close()
                raise
            worker.owner = owner
            self.workers[identity] = worker
            worker.start()
            return worker

    def snapshot(self):
        with self.lock:
            workers = list(self.workers.values())
        return {'enabled': bool(os.getenv('MOON_GOVERNOR_PATH', '').strip()),
                'scope': 'single_process', 'automatic_bot_creation': False,
                'workers': [worker.snapshot() for worker in workers]}


governor = BotGovernor()


def register_governor(app):
    from flask import jsonify, request
    import hmac

    @app.get('/api/internal/governor')
    def governor_status():
        expected = os.getenv('MOON_ADMIN_API_KEY', '').strip()
        supplied = request.headers.get('X-Moon-Admin-Key', '').strip()
        if not expected or not supplied or not hmac.compare_digest(expected.encode(), supplied.encode()):
            return jsonify({'ok': False}), 401
        response = jsonify({'ok': True, **governor.snapshot()})
        response.headers['Cache-Control'] = 'no-store'
        return response

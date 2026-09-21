"""Single-host persistent queue for a gateway and Docker workers.

Share a local Docker volume, never a network filesystem. Claims not started may
be reassigned. Expired processing is quarantined: a Telegram side effect may
already have happened, so replay requires operator reconciliation.
"""
import hashlib
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager, closing
from pathlib import Path


class PersistentInbox:
    def __init__(self, filename, clock=time.time, capacity=10000):
        self.filename, self.clock, self.capacity = str(filename), clock, capacity
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.filename)) as db, db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('''CREATE TABLE IF NOT EXISTS jobs (
                seq INTEGER PRIMARY KEY AUTOINCREMENT, event_key TEXT UNIQUE NOT NULL,
                partition_key TEXT NOT NULL, payload TEXT, digest TEXT NOT NULL,
                state TEXT NOT NULL, worker TEXT, lease TEXT, deadline REAL,
                created REAL NOT NULL, updated REAL NOT NULL)''')
            db.execute('CREATE INDEX IF NOT EXISTS jobs_partition ON jobs(partition_key, seq, state)')
            db.execute('CREATE TABLE IF NOT EXISTS workers (id TEXT PRIMARY KEY, paused INTEGER NOT NULL DEFAULT 0)')
        Path(filename).chmod(0o600)

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.filename, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA synchronous=FULL')
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def enqueue(self, event_key, partition_key, payload):
        if not all(isinstance(key, str) and 0 < len(key) <= 200 for key in (event_key, partition_key)):
            raise ValueError('Invalid queue identity')
        encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False)
        if len(encoded.encode()) > 262144:
            raise ValueError('Payload exceeds 256 KiB')
        digest = hashlib.sha256(encoded.encode()).hexdigest()
        now = self.clock()
        with self.transaction() as db:
            previous = db.execute('SELECT seq, digest, partition_key FROM jobs WHERE event_key=?', (event_key,)).fetchone()
            if previous:
                if previous['digest'] != digest or previous['partition_key'] != partition_key:
                    raise ValueError('Conflicting duplicate event')
                return previous['seq']
            size = db.execute("SELECT count(*) FROM jobs WHERE state!='done'").fetchone()[0]
            if size >= self.capacity:
                raise ValueError('Queue full; receiver must not acknowledge input')
            return db.execute("INSERT INTO jobs(event_key,partition_key,payload,digest,state,created,updated) VALUES (?,?,?,?,'pending',?,?)",
                              (event_key, partition_key, encoded, digest, now, now)).lastrowid

    def _expire(self, db):
        now = self.clock()
        db.execute("UPDATE jobs SET state='pending',worker=NULL,lease=NULL,deadline=NULL,updated=? WHERE state='claimed' AND deadline<=?", (now, now))
        db.execute("UPDATE jobs SET state='uncertain',updated=? WHERE state='running' AND deadline<=?", (now, now))

    def claim(self, worker, seconds=30):
        if not isinstance(worker, str) or not 0 < len(worker) <= 64 or not 1 <= seconds <= 300:
            raise ValueError('Invalid worker or claim duration')
        with self.transaction() as db:
            self._expire(db)
            db.execute('INSERT OR IGNORE INTO workers(id) VALUES (?)', (worker,))
            if db.execute('SELECT paused FROM workers WHERE id=?', (worker,)).fetchone()[0]:
                return None
            row = db.execute("""SELECT j.* FROM jobs j WHERE j.state='pending' AND NOT EXISTS
                (SELECT 1 FROM jobs prior WHERE prior.partition_key=j.partition_key
                 AND prior.seq<j.seq AND prior.state!='done') ORDER BY j.seq LIMIT 1""").fetchone()
            if row is None:
                return None
            lease = uuid.uuid4().hex
            db.execute("UPDATE jobs SET state='claimed',worker=?,lease=?,deadline=?,updated=? WHERE seq=?",
                       (worker, lease, self.clock() + seconds, self.clock(), row['seq']))
            return {'id': row['seq'], 'lease': lease, 'payload': json.loads(row['payload'])}

    def start(self, job_id, worker, lease, seconds=120):
        if not 1 <= seconds <= 3600:
            raise ValueError('Invalid processing duration')
        with self.transaction() as db:
            self._expire(db)
            changed = db.execute("""UPDATE jobs SET state='running',deadline=?,updated=? WHERE
                seq=? AND worker=? AND lease=? AND state='claimed' AND NOT EXISTS
                (SELECT 1 FROM workers WHERE id=? AND paused=1)""",
                (self.clock() + seconds, self.clock(), job_id, worker, lease, worker)).rowcount
            return changed == 1

    def finish(self, job_id, worker, lease, success=True):
        with self.transaction() as db:
            self._expire(db)
            return db.execute("""UPDATE jobs SET state=?,payload=CASE WHEN ? THEN NULL ELSE payload END,updated=?
                WHERE seq=? AND worker=? AND lease=? AND state='running'""",
                ('done' if success else 'uncertain', success, self.clock(), job_id, worker, lease)).rowcount == 1

    def pause(self, worker, paused=True):
        with self.transaction() as db:
            db.execute('INSERT INTO workers(id,paused) VALUES (?,?) ON CONFLICT(id) DO UPDATE SET paused=excluded.paused', (worker, int(paused)))
            if paused:
                db.execute("UPDATE jobs SET state='pending',worker=NULL,lease=NULL,deadline=NULL WHERE worker=? AND state='claimed'", (worker,))

    def stats(self):
        with self.transaction() as db:
            self._expire(db)
            states = {row['state']: row['n'] for row in db.execute('SELECT state,count(*) n FROM jobs GROUP BY state')}
            workers = [dict(row) for row in db.execute('''SELECT w.id,w.paused,
                sum(CASE WHEN j.state='running' THEN 1 ELSE 0 END) running,
                sum(CASE WHEN j.state='done' THEN 1 ELSE 0 END) completed
                FROM workers w LEFT JOIN jobs j ON j.worker=w.id GROUP BY w.id ORDER BY w.id''')]
            oldest = db.execute("SELECT min(created) FROM jobs WHERE state='pending'").fetchone()[0]
            return {'states': states, 'workers': workers, 'capacity': self.capacity,
                    'oldest_pending_seconds': max(0, self.clock() - oldest) if oldest is not None else 0}

    def prune_completed(self, retention=604800):
        if retention < 86400:
            raise ValueError('Retain deduplication markers for at least one day')
        with self.transaction() as db:
            return db.execute("DELETE FROM jobs WHERE state='done' AND updated<?", (self.clock() - retention,)).rowcount

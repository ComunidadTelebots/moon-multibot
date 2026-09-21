"""Message metadata only, local to this Moonbot deployment; rolling 30-day retention."""
import os
import sqlite3
import time
from pathlib import Path
from threading import RLock

TYPES = ('animation', 'photo', 'video', 'video_note', 'voice', 'audio', 'document',
         'sticker', 'poll', 'contact', 'location', 'venue', 'dice', 'text', 'other')
_lock = RLock()


def message_type(message):
    # A caption is not a second text message; animation can also include document.
    return next((kind for kind in TYPES[:-1] if kind in message), 'other')


class MessageAnalytics:
    def __init__(self, filename=None, now=time.time):
        self.filename = filename or os.getenv('MOON_MESSAGE_ANALYTICS_FILE', 'data/message-analytics.sqlite3')
        self.now = now
        self.last_cleanup = 0

    def connect(self):
        Path(self.filename).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.filename, timeout=2)
        connection.execute('PRAGMA journal_mode=WAL')
        connection.execute('CREATE TABLE IF NOT EXISTS messages (chat TEXT, mid INTEGER, at REAL, kind TEXT, PRIMARY KEY(chat, mid))')
        connection.execute('CREATE INDEX IF NOT EXISTS message_time ON messages(at)')
        connection.execute('CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY, title TEXT)')
        return connection

    def record(self, message):
        chat = message.get('chat') or {}
        # The ranking covers groups and channels, not personal/business conversations.
        if chat.get('type') not in ('group', 'supergroup', 'channel') or not isinstance(message.get('message_id'), int):
            return
        with _lock:
            connection = self.connect()
            try:
                with connection:
                    current = self.now()
                    connection.execute('INSERT OR IGNORE INTO messages VALUES (?, ?, ?, ?)',
                                       (str(chat['id']), message['message_id'], current, message_type(message)))
                    connection.execute('INSERT OR REPLACE INTO chats VALUES (?, ?)',
                                       (str(chat['id']), str(chat.get('title') or chat['id'])[:160]))
                    if current - self.last_cleanup >= 3600:
                        connection.execute('DELETE FROM messages WHERE at < ?', (current - 30 * 86400,))
                        connection.execute('DELETE FROM chats WHERE id NOT IN (SELECT DISTINCT chat FROM messages)')
                        self.last_cleanup = current
            finally:
                connection.close()

    def ranking(self, days=7, kind='all'):
        if days not in (1, 7, 30) or kind not in ('all', *TYPES):
            raise ValueError('Invalid ranking filters')
        with _lock:
            connection = self.connect()
            try:
                cutoff = self.now() - days * 86400
                rows = connection.execute('SELECT m.chat, c.title, m.kind, COUNT(*) FROM messages m LEFT JOIN chats c ON c.id=m.chat WHERE m.at >= ? GROUP BY m.chat,m.kind', (cutoff,)).fetchall()
                chats = {}
                for cid, title, category, count in rows:
                    row = chats.setdefault(cid, dict(id=cid, name=title or cid, total=0, types={}))
                    row['types'][category] = count
                    row['total'] += count
                for row in chats.values():
                    row['score'] = row['total'] if kind == 'all' else row['types'].get(kind, 0)
                ordered = sorted((r for r in chats.values() if r['score']), key=lambda r: (-r['score'], r['id']))
                return dict(ok=True, days=days, kind=kind, rows=ordered[:100], chats=len(ordered),
                            total=sum(r['score'] for r in ordered), types=list(TYPES),
                            observed_since=connection.execute('SELECT MIN(at) FROM messages').fetchone()[0],
                            generated_at=self.now(), source='local-deployment')
            finally:
                connection.close()


analytics = MessageAnalytics()

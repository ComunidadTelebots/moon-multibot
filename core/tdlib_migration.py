"""Read-only migration readiness; never publishes credentials or message content."""
import json
from pathlib import Path
from core.traffic_control import identity


def migration_snapshot(bots, configured):
    try:
        report = json.loads((Path(__file__).resolve().parents[1] / 'TDLIB_COMPATIBILITY.json').read_text(encoding='utf-8-sig'))
        summary = report['summary']
    except (OSError, ValueError, KeyError):
        summary = None
    rows = []
    for bot in list(bots)[:200]:
        client = getattr(bot, '_tdlib', None)
        status = client.get_status() if client else {}
        rows.append({'id': identity(bot.url), 'loaded': status.get('loaded', False),
                     'ready': status.get('ready', False), 'running': status.get('running', False),
                     'receiver': status.get('receiver'), 'incoming': 'bot_api',
                     'auth_state': status.get('auth_state', 'not_configured')})
    return {'ok': True, 'schema': 1, 'configured': bool(configured),
            'ready_for_full_migration': False, 'audit': summary, 'bots': rows,
            'bots_truncated': len(bots) > 200}

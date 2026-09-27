"""Date-only arithmetic: no timezone assumptions or background jobs."""
from datetime import date, timedelta

HELP = 'Uso: /diasentre AAAA-MM-DD AAAA-MM-DD | /sumardias AAAA-MM-DD días. Se usan fechas de calendario, sin hora.'


def handle_command(bot, cid, uid, text, rank):
    parts = text.strip().split()
    if not parts or parts[0].lower() not in ('/diasentre', '/sumardias'):
        return False
    reply = HELP
    try:
        if len(parts) == 3 and len(parts[1]) == 10:
            start = date.fromisoformat(parts[1])
            if parts[0].lower() == '/diasentre':
                if len(parts[2]) != 10:
                    raise ValueError()
                reply = f'Diferencia: {(date.fromisoformat(parts[2]) - start).days} días.'
            else:
                if len(parts[2]) > 7:
                    raise ValueError()
                days = int(parts[2])
                if abs(days) > 365000:
                    raise ValueError()
                reply = f'Fecha: {(start + timedelta(days=days)).isoformat()}'
    except (ValueError, OverflowError):
        reply = 'Fecha o cantidad de días no válida. ' + HELP
    bot.send_msg(cid, reply)
    return True

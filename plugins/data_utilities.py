"""Local text utilities: never evaluate code or echo submitted JSON."""
import hashlib
import json

HELP = 'Utilidades: /convertir 10 km m; /unidades; /diasentre 2026-01-01 2026-02-01; /sumardias 2026-01-01 7; /jsonvalidar <JSON>; /hashtexto <texto>. SHA-256 calcula una huella, no cifra el texto.'


def handle_command(bot, cid, uid, text, rank):
    parts = text.strip().split(maxsplit=1)
    if not parts or parts[0].lower() not in ('/jsonvalidar', '/hashtexto', '/utilidades'):
        return False
    command = parts[0].lower()
    body = parts[1] if len(parts) > 1 else ''
    if command == '/utilidades':
        reply = HELP
    elif not body or len(body) > 6000:
        reply = 'Incluye un texto de hasta 6000 caracteres.'
    elif command == '/hashtexto':
        reply = 'SHA-256: ' + hashlib.sha256(body.encode('utf-8')).hexdigest()
    else:
        def reject_constant(value):
            raise ValueError('Non-standard JSON')
        try:
            value = json.loads(body, parse_constant=reject_constant)
            kind = 'objeto' if isinstance(value, dict) else 'lista' if isinstance(value, list) else 'valor simple'
            reply = f'JSON válido: {kind}.'
            if isinstance(value, (dict, list)):
                reply += f' {len(value)} elementos en el primer nivel.'
        except json.JSONDecodeError as exc:
            reply = f'JSON no válido: línea {exc.lineno}, columna {exc.colno}.'
        except (ValueError, RecursionError):
            reply = 'JSON no válido o demasiado anidado.'
    bot.send_msg(cid, reply)
    return True

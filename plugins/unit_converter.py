"""Bounded, stateless conversions shared by every bot."""
from decimal import Decimal, InvalidOperation

UNITS = {
    'mm': ('length', '0.001'), 'cm': ('length', '0.01'), 'm': ('length', '1'), 'km': ('length', '1000'),
    'in': ('length', '0.0254'), 'ft': ('length', '0.3048'), 'mi': ('length', '1609.344'),
    'g': ('mass', '1'), 'kg': ('mass', '1000'), 'lb': ('mass', '453.59237'),
    'ml': ('volume', '1'), 'l': ('volume', '1000'),
    's': ('time', '1'), 'min': ('time', '60'), 'h': ('time', '3600'),
}
HELP = 'Uso: /convertir 10 km m. Unidades: mm cm m km in ft mi; g kg lb; ml l; s min h; c f k.'


def handle_command(bot, cid, uid, text, rank):
    parts = text.strip().split()
    if not parts or parts[0].lower() not in ('/convertir', '/unidades'):
        return False
    reply = HELP
    try:
        if parts[0].lower() == '/convertir' and len(parts) == 4:
            if len(parts[1]) > 40:
                raise ValueError()
            value = Decimal(parts[1].replace(',', '.'))
            if not value.is_finite() or abs(value) > Decimal('1e15') or (value and abs(value) < Decimal('1e-15')):
                raise ValueError()
            source, target = parts[2].lower(), parts[3].lower()
            if source in ('c', 'f', 'k') and target in ('c', 'f', 'k'):
                kelvin = value + Decimal('273.15') if source == 'c' else (value - 32) * 5 / 9 + Decimal('273.15') if source == 'f' else value
                if kelvin < 0:
                    raise ValueError()
                result = kelvin - Decimal('273.15') if target == 'c' else (kelvin - Decimal('273.15')) * 9 / 5 + 32 if target == 'f' else kelvin
            else:
                family, factor = UNITS[source]
                other, divisor = UNITS[target]
                if family != other:
                    raise ValueError()
                result = value * Decimal(factor) / Decimal(divisor)
            formatted = format(Decimal(format(result, '.10g')), 'f')
            if '.' in formatted:
                formatted = formatted.rstrip('0').rstrip('.')
            reply = f'Resultado: {formatted} {target}'
    except (ValueError, InvalidOperation, KeyError):
        reply = 'Conversión no válida: revisa el valor y usa unidades de la misma magnitud. ' + HELP
    bot.send_msg(cid, reply)
    return True

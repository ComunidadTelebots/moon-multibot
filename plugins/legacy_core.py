"""Compatibilidad con comandos generales del bot TeleBots clásico."""


HELP_ADMIN = """Ayuda para administrar grupos
/warn (respondiendo) — advertir
/mute y /unmute — silenciar o restaurar
/ban y /unban — expulsar o restaurar
/reglas — mostrar las reglas configuradas
/report — avisar a los administradores
/settings — revisar la configuración
El bot necesita ser administrador y disponer de los permisos correspondientes."""


def _convert(expression):
    # Formatos: "ff hex dec", "255 dec hex", "1010 bin dec".
    parts = expression.lower().split()
    if len(parts) != 3:
        raise ValueError("Uso: /conv <valor> <origen> <destino>. Ejemplo: /conv ff hex dec")
    value, source, target = parts
    bases = {"bin": 2, "oct": 8, "dec": 10, "hex": 16, "2": 2, "8": 8, "10": 10, "16": 16}
    if source not in bases or target not in bases:
        raise ValueError("Bases admitidas: bin, oct, dec y hex.")
    number = int(value, bases[source])
    if not -(2 ** 63) <= number < 2 ** 63:
        raise ValueError("El valor está fuera del intervalo admitido.")
    functions = {2: lambda n: format(n, "b"), 8: lambda n: format(n, "o"), 10: str, 16: lambda n: format(n, "x")}
    if number < 0 and bases[target] != 10:
        result = "-" + functions[bases[target]](-number)
    else:
        result = functions[bases[target]](number)
    return f"{value} ({source}) = {result} ({target})"


def handle_command(bot, cid, uid, text, rank):
    parts = text.strip().split(maxsplit=1)
    cmd = parts[0].lower() if parts else ""
    argument = parts[1].strip() if len(parts) > 1 else ""
    if cmd not in {"/helpadmin", "/conv", "/info", "/reglas"}:
        return False
    if cmd == "/helpadmin":
        answer = HELP_ADMIN
    elif cmd == "/conv":
        try:
            answer = _convert(argument)
        except (ValueError, OverflowError) as exc:
            answer = str(exc)
    elif cmd == "/info":
        result = bot.api_call("getMe", {}, silent=True)
        me = (result or {}).get("result") or {}
        username = me.get("username") or getattr(bot, "bot_username", "Moonbot") or "Moonbot"
        answer = (
            f"@{username} · Moon Multibot\n"
            "Moderación, seguridad, utilidades, IA supervisada y administración desde web y Mini App.\n"
            "Servicio comunitario gratuito y sin ánimo de lucro.\n"
            "https://todosobreall.tech"
        )
    else:
        raw = bot.db.get(f"GROUPSUITE_{cid}", {}) or {}
        rules = raw.get("rules") if isinstance(raw, dict) else []
        visible = []
        for rule in rules or []:
            if isinstance(rule, str) and rule.strip():
                visible.append(rule.strip())
            elif isinstance(rule, dict):
                label = rule.get("text") or rule.get("name") or rule.get("description")
                if label and rule.get("enabled", True):
                    visible.append(str(label).strip())
        answer = "Reglas del grupo:\n" + "\n".join(f"{index}. {rule}" for index, rule in enumerate(visible[:30], 1)) if visible else "Este grupo todavía no ha publicado reglas en Moonbot."
    bot.send_msg(cid, answer, parse_mode=None)
    return True

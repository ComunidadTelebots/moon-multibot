import ast
import math
import operator


def _safe_eval(expr):
    if len(expr) > 256:
        raise ValueError('Expresión demasiado larga')
    tree = ast.parse(expr, mode='eval')
    if sum(1 for _ in ast.walk(tree)) > 80:
        raise ValueError('Demasiadas operaciones')
    operations = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                  ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod}
    def evaluate(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            value = node.value
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = evaluate(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        elif isinstance(node, ast.BinOp):
            left, right = evaluate(node.left), evaluate(node.right)
            if isinstance(node.op, ast.Pow):
                if abs(right) > 12 or (left < 0 and right != int(right)):
                    raise ValueError('Potencia fuera del límite')
                value = left ** right
            elif type(node.op) in operations:
                value = operations[type(node.op)](left, right)
            else:
                raise ValueError('Operación no permitida')
        else:
            raise ValueError('Expresión no permitida')
        if not math.isfinite(value) or abs(value) > 1e100:
            raise ValueError('Resultado fuera del límite')
        return value
    return evaluate(tree.body)


def handle_command(bot, cid, uid, text, rank):
    parts = text.strip().split(maxsplit=1)
    if not parts:
        return False
    cmd = parts[0].lower()
    if cmd not in ["/calc", "/math"]:
        return False
    if len(parts) < 2:
        bot.send_msg(cid, "Uso: /calc <expresion>. Ej: /calc (2+5)*3")
        return True
    expr = parts[1].strip()
    try:
        result = _safe_eval(expr)
        bot.send_msg(cid, f"Resultado: `{result}`")
    except (ValueError, SyntaxError, ZeroDivisionError, OverflowError, RecursionError) as e:
        bot.send_msg(cid, f"Error en expresion: {e}")
    return True

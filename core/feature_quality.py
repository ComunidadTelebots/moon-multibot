"""Auditoría estructural del registro de funciones implementadas."""

import ast
import importlib
import inspect
from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parents[1]


def resolve_locator(locator):
    parts = str(locator).split(".")
    for boundary in range(len(parts), 0, -1):
        try:
            value = importlib.import_module(".".join(parts[:boundary]))
        except ModuleNotFoundError:
            continue
        for attribute in parts[boundary:]:
            value = getattr(value, attribute)
        return value
    raise ImportError(f"no se pudo resolver {locator}")


def _meaningful_statements(function):
    source = textwrap.dedent(inspect.getsource(function))
    tree = ast.parse(source)
    definition = next(node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
    statements = list(definition.body)
    if statements and isinstance(statements[0], ast.Expr) and isinstance(statements[0].value, ast.Constant) and isinstance(statements[0].value.value, str):
        statements.pop(0)
    return statements


def implementation_problem(function):
    try:
        statements = _meaningful_statements(function)
    except (OSError, TypeError, SyntaxError, StopIteration) as error:
        return f"fuente no auditable: {error}"
    if not statements:
        return "cuerpo vacío"
    if all(isinstance(statement, ast.Pass) for statement in statements):
        return "solo contiene pass"
    if len(statements) == 1:
        statement = statements[0]
        if isinstance(statement, ast.Raise) and isinstance(statement.exc, ast.Call) and getattr(statement.exc.func, "id", "") == "NotImplementedError":
            return "lanza NotImplementedError"
        if isinstance(statement, ast.Return):
            value = statement.value
            if value is None or (isinstance(value, ast.Constant) and value.value in (None, Ellipsis)):
                return "retorno vacío"
            if isinstance(value, (ast.Dict, ast.List, ast.Tuple, ast.Set)) and not getattr(value, "elts", None) and not getattr(value, "keys", None):
                return "retorno de colección vacía"
    return None


def audit_features(features):
    problems = []
    seen_tests = {}
    for feature in features:
        feature_id = feature.get("id", "sin-id")
        for field in ("api", "module", "test", "preflight", "minimum_role", "scope"):
            if not feature.get(field):
                problems.append(f"{feature_id}: falta {field}")
        function = feature.get("callable")
        if not callable(function):
            problems.append(f"{feature_id}: API no invocable")
        else:
            issue = implementation_problem(function)
            if issue:
                problems.append(f"{feature_id}: {issue}")
        locator = feature.get("test")
        if locator:
            try:
                if "/" in locator or "\\" in locator or locator.endswith(".py"):
                    test_path = ROOT / locator.split("::", 1)[0].replace("\\", "/")
                    if not test_path.is_file():
                        problems.append(f"{feature_id}: archivo de prueba ausente ({locator})")
                else:
                    test = seen_tests.setdefault(locator, resolve_locator(locator))
                    if not callable(test):
                        problems.append(f"{feature_id}: prueba no invocable")
            except (ImportError, AttributeError, ModuleNotFoundError) as error:
                problems.append(f"{feature_id}: prueba ausente ({error})")
    return problems

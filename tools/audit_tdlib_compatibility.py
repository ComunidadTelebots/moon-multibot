"""Static compatibility inventory. Does not import plugins or read credentials."""
import ast
import json
from pathlib import Path


def inventory(root):
    findings, errors = [], []
    for path in sorted(Path(root).rglob('*.py')):
        relative = path.relative_to(root)
        if any(part.startswith('.') or part in {'tests', 'tools', 'venv', '__pycache__', 'node_modules'} for part in relative.parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        except (SyntaxError, UnicodeError) as error:
            errors.append({'file': relative.as_posix(), 'error': type(error).__name__})
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, 'id', '')
            if name not in {'api_call', 'call_api', 'telegram_api_call'}:
                continue
            index = 2 if name == 'telegram_api_call' else 0
            argument = node.args[index] if len(node.args) > index else next((k.value for k in node.keywords if k.arg in {'method', 'm'}), None)
            method = argument.value if isinstance(argument, ast.Constant) and isinstance(argument.value, str) else None
            findings.append({'file': relative.as_posix(), 'line': node.lineno,
                             'method': method, 'entry': name,
                             'status': 'requires_adapter' if method else 'dynamic_review_required'})
    methods = sorted({row['method'] for row in findings if row['method']})
    return {'schema': 1, 'ready_for_full_migration': False,
            'summary': {'methods': len(methods), 'call_sites': len(findings),
                        'dynamic_calls': sum(row['method'] is None for row in findings),
                        'parse_errors': len(errors)},
            'methods': methods, 'findings': findings, 'errors': errors,
            'limitations': ['Static calls only; runtime-loaded plugins and direct HTTP need separate review.',
                            'Presence of a TDLib method does not prove Bot API payload/response compatibility.']}


if __name__ == '__main__':
    print(json.dumps(inventory(Path(__file__).resolve().parents[1]), ensure_ascii=False, indent=2))

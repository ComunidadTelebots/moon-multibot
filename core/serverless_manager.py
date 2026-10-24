import ast
import json
import os
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


class ServerlessError(RuntimeError):
    pass


class ServerlessManager:
    ACTIONS = {
        "refresh": ["fetch"],
        "deploy": ["push"],
        "migrate": ["migrate", "--safe"],
        "webhook": ["webhook", "sync"],
    }

    def __init__(self, root, registry_path, enabled=False, timeout=45):
        self.root = Path(root).resolve()
        self.registry_path = Path(registry_path).resolve()
        self.enabled = bool(enabled)
        self.timeout = max(10, min(int(timeout), 180))

    def _registry(self):
        if not self.registry_path.is_file():
            return []
        try:
            rows = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ServerlessError(f"Registro Serverless no valido: {exc}") from exc
        if not isinstance(rows, list):
            raise ServerlessError("El registro Serverless debe ser una lista")
        return rows

    def _project(self, bot_id):
        bot_id = str(bot_id or "").strip()
        row = next((item for item in self._registry() if item.get("id") == bot_id), None)
        if not row:
            raise ServerlessError("Bot Serverless no registrado")
        relative = Path(str(row.get("project_dir", "")))
        project = (self.root / relative).resolve()
        if self.root not in project.parents or not project.is_dir():
            raise ServerlessError("Directorio Serverless no disponible")
        if not (project / "tgcloud.jsonc").is_file():
            raise ServerlessError("El proyecto no contiene tgcloud.jsonc")
        return row, project

    @staticmethod
    def _redact(text):
        text = str(text or "")
        text = re.sub(r"\b\d{6,}:[A-Za-z0-9_-]{20,}\b", "[token protegido]", text)
        text = re.sub(r"(?i)(authorization:\s*bearer\s+)\S+", r"\1[protegido]", text)
        return text[-12000:]

    @staticmethod
    def _command(project):
        local_bin = project / "node_modules" / ".bin" / (
            "tgcloud.cmd" if os.name == "nt" else "tgcloud"
        )
        if local_bin.is_file():
            return str(local_bin)
        executable = shutil.which("tgcloud")
        if executable:
            return executable
        raise ServerlessError("tgcloud no esta instalado en el servidor")

    def _run(self, project, args, timeout=None):
        if not self.enabled:
            raise ServerlessError("El control Serverless esta desactivado")
        command = [self._command(project), "--no-pager", *args]
        env = os.environ.copy()
        env.update({"NO_COLOR": "1", "TERM": "dumb", "CI": "1"})
        try:
            result = subprocess.run(
                command,
                cwd=project,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout or self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ServerlessError("La operacion Serverless agoto el tiempo de espera") from exc
        output = self._redact("\n".join(part for part in (result.stdout, result.stderr) if part).strip())
        return result.returncode, output

    @staticmethod
    def _status_payload(row, project, output, returncode):
        revision = re.search(r"Local revision:\s*(\d+)", output)
        static_url = re.search(r"Static \([^)]*\s→\s(https?://[^)]+)\)", output)
        changed = []
        for line in output.splitlines():
            match = re.match(r"\s*[+~!-]\s+([^\s].*)", line)
            if match:
                changed.append(match.group(1).strip())
        return {
            "id": row.get("id"),
            "name": row.get("name") or row.get("id"),
            "app_id": str(row.get("app_id") or ""),
            "project_dir": row.get("project_dir"),
            "linked": "Linked to app" in output,
            "credentials_ready": (project / ".tgcloud" / "credentials").is_file(),
            "revision": int(revision.group(1)) if revision else None,
            "clean": "Working directory clean" in output,
            "changed": changed,
            "static_url": static_url.group(1) if static_url else row.get("static_url"),
            "ok": returncode == 0,
            "message": output,
        }

    def status(self, bot_id):
        row, project = self._project(bot_id)
        code, output = self._run(project, ["status"], timeout=20)
        payload = self._status_payload(row, project, output, code)
        if payload["credentials_ready"]:
            try:
                payload["stats"] = self.stats(bot_id)
            except ServerlessError as exc:
                payload["stats_error"] = str(exc)
        return payload

    def list_status(self):
        rows = self._registry()
        with ThreadPoolExecutor(max_workers=min(4, max(1, len(rows)))) as pool:
            futures = [pool.submit(self.status, row.get("id")) for row in rows]
            results = []
            for row, future in zip(rows, futures):
                try:
                    results.append(future.result())
                except ServerlessError as exc:
                    results.append({
                        "id": row.get("id"),
                        "name": row.get("name") or row.get("id"),
                        "app_id": str(row.get("app_id") or ""),
                        "ok": False,
                        "message": str(exc),
                    })
        return results

    def stats(self, bot_id):
        row, project = self._project(bot_id)
        endpoint = str(row.get("stats_endpoint") or "moonStats")
        code, output = self._run(
            project,
            [
                "run", f"endpoints/{endpoint}", "{}", "--ctx",
                '{"initData":{"user":{"id":-5724481351,"first_name":"Moonbot"}}}',
            ],
            timeout=30,
        )
        if code != 0:
            raise ServerlessError(output or "No se pudieron consultar las estadisticas")
        match = re.search(r"^<\s+(.+?)\s+\d+ms\s*$", output, flags=re.MULTILINE)
        if not match:
            raise ServerlessError("Telegram Cloud devolvio un formato de estadisticas inesperado")
        value = match.group(1).strip()
        try:
            if value[:1] in ("'", '"'):
                value = ast.literal_eval(value)
            return json.loads(value)
        except (ValueError, SyntaxError) as exc:
            raise ServerlessError("No se pudo interpretar la telemetria Serverless") from exc

    def action(self, bot_id, action):
        if action not in self.ACTIONS:
            raise ServerlessError("Accion Serverless no permitida")
        row, project = self._project(bot_id)
        code, output = self._run(project, self.ACTIONS[action], timeout=120)
        if action == "deploy" and code != 0 and "files uploaded" in output:
            fetch_code, fetch_output = self._run(project, ["fetch"], timeout=45)
            output = f"{output}\n{fetch_output}".strip()
            code = fetch_code
        if code != 0:
            raise ServerlessError(output or "La operacion Serverless fallo")
        return {
            "bot_id": row.get("id"),
            "action": action,
            "output": output,
            "status": self.status(bot_id),
        }

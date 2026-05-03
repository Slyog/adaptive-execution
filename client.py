import json
import os
from urllib import error, request


class ExecutionEngineClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self.base_url = base_url.rstrip("/")

    def run_code(self, code: str) -> dict:
        payload = json.dumps({"code": code}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        api_key = os.getenv("AI_EXECUTION_ENGINE_API_KEY") or os.getenv("API_KEY")
        if api_key:
            headers["x-api-key"] = api_key

        req = request.Request(
            f"{self.base_url}/execute",
            data=payload,
            headers=headers,
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=60) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            if exc.code == 422 or self._is_invalid_input(raw):
                message = f"Execution engine rejected request: HTTP {exc.code}: {raw}"
            else:
                message = f"HTTP {exc.code}: {raw or exc.reason}"
            return {
                "stdout": "",
                "stderr": message,
                "exit_code": 1,
            }
        except error.URLError as exc:
            return {
                "stdout": "",
                "stderr": str(exc.reason),
                "exit_code": 1,
            }

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {
                "stdout": raw,
                "stderr": "",
                "exit_code": 0,
            }

        if self._is_invalid_input(raw):
            return {
                "stdout": "",
                "stderr": f"Execution engine rejected request: HTTP 200: {raw}",
                "exit_code": 1,
            }

        return self._normalize_response(data)

    def _is_invalid_input(self, body: str) -> bool:
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return False

        return data.get("detail") == "invalid_input"

    def _normalize_response(self, data: dict) -> dict:
        source = data

        for key in ("result", "run", "execution", "output"):
            value = data.get(key)
            if isinstance(value, dict):
                source = value
                break

        stdout = source.get("stdout", source.get("final_stdout", source.get("std_out", source.get("output", ""))))
        stderr = source.get(
            "stderr",
            source.get("final_stderr", source.get("last_error", source.get("std_err", source.get("error", "")))),
        )
        exit_code = source.get(
            "exit_code",
            source.get("returncode", source.get("return_code", source.get("status_code"))),
        )

        try:
            normalized_exit_code = int(exit_code)
        except (TypeError, ValueError):
            status = source.get("status")
            normalized_exit_code = 0 if status in ("completed", "success", "ok") or exit_code is True else 1

        return {
            "stdout": "" if stdout is None else str(stdout),
            "stderr": "" if stderr is None else str(stderr),
            "exit_code": normalized_exit_code,
        }

import json
from urllib import error, request


class ExecutionEngineClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self.base_url = base_url.rstrip("/")

    def run_code(self, code: str) -> dict:
        payload = json.dumps({"code": code}).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/agent-runs",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=60) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            return {
                "stdout": "",
                "stderr": raw or str(exc),
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

        return self._normalize_response(data)

    def _normalize_response(self, data: dict) -> dict:
        source = data

        for key in ("result", "run", "execution", "output"):
            value = data.get(key)
            if isinstance(value, dict):
                source = value
                break

        stdout = source.get("stdout", source.get("std_out", source.get("output", "")))
        stderr = source.get("stderr", source.get("std_err", source.get("error", "")))
        exit_code = source.get(
            "exit_code",
            source.get("returncode", source.get("return_code", source.get("status_code", 1))),
        )

        try:
            normalized_exit_code = int(exit_code)
        except (TypeError, ValueError):
            normalized_exit_code = 0 if exit_code in ("success", "ok", True) else 1

        return {
            "stdout": "" if stdout is None else str(stdout),
            "stderr": "" if stderr is None else str(stderr),
            "exit_code": normalized_exit_code,
        }

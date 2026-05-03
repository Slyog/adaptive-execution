import os
import re
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def _load_dotenv_file(path: str = ".env") -> None:
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


def _load_environment() -> None:
    if load_dotenv is not None:
        load_dotenv()
        return

    _load_dotenv_file()


def _strip_markdown_fences(text: str) -> str:
    stripped = text.strip()
    match = re.match(r"^```(?:python|py)?\s*(.*?)\s*```$", stripped, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return stripped


API_ERROR_TYPES = {
    "HTTPUnauthorized",
    "HTTPNotFound",
    "HTTPServerError",
    "JSONDecodeError",
    "RequestTimeout",
    "ConnectionError",
}


def _matching_line(text: str, pattern: str) -> str:
    for line in text.splitlines():
        if re.search(pattern, line, re.IGNORECASE):
            return line.strip()
    return text.strip()


def _parse_api_error(text: str) -> dict | None:
    if not text.strip():
        return None

    patterns = [
        ("HTTPUnauthorized", r"\b(?:http\s*)?401\b|unauthorized"),
        ("HTTPNotFound", r"\b(?:http\s*)?404\b|(?:http|status(?:_code)?|response).*not found|not found.*(?:http|status|response)"),
        ("HTTPServerError", r"\b(?:http\s*)?5\d\d\b|server error|internal server error"),
        ("JSONDecodeError", r"json(?:\.decoder)?\.JSONDecodeError|JSONDecodeError|expecting value"),
        ("RequestTimeout", r"requests\.exceptions\.(?:ReadTimeout|ConnectTimeout|Timeout)|\b(?:read |connect )?timeout\b|timed out"),
        (
            "ConnectionError",
            r"requests\.exceptions\.ConnectionError|ConnectionError|connection refused|failed to establish a new connection|max retries exceeded|name resolution|nodename nor servname",
        ),
    ]

    for error_type, pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return {
                "error_type": error_type,
                "error_message": _matching_line(text, pattern),
            }

    return None


def parse_error(stderr: str, stdout: str = "") -> dict:
    message = (stderr or "").strip()
    combined_output = "\n".join(part for part in (stderr or "", stdout or "") if part).strip()
    if not message:
        api_error = _parse_api_error(combined_output)
        if api_error:
            return api_error
        return {
            "error_type": None,
            "error_message": "",
        }

    api_error = _parse_api_error(combined_output)
    if api_error:
        return api_error

    for line in reversed(message.splitlines()):
        line = line.strip()
        if not line:
            continue

        match = re.match(r"^([A-Za-z_][A-Za-z0-9_.]*):\s*(.*)$", line)
        if match:
            error_type = match.group(1)
            if error_type == "json.decoder.JSONDecodeError":
                error_type = "JSONDecodeError"
            return {
                "error_type": error_type,
                "error_message": match.group(2),
            }

    return {
        "error_type": None,
        "error_message": message,
    }


def select_strategy(error_type: str | None) -> str:
    if error_type == "FileNotFoundError":
        return "handle_file_missing"
    if error_type == "ModuleNotFoundError":
        return "avoid_missing_dependency"
    if error_type == "ZeroDivisionError":
        return "add_guard"
    if error_type == "TypeError":
        return "fix_type"
    if error_type == "SyntaxError":
        return "fix_syntax"
    if error_type == "HTTPUnauthorized":
        return "add_auth_hint"
    if error_type == "HTTPNotFound":
        return "validate_endpoint"
    if error_type == "HTTPServerError":
        return "handle_server_error"
    if error_type == "JSONDecodeError":
        return "safe_json_parse"
    if error_type == "RequestTimeout":
        return "add_timeout_and_retry"
    if error_type == "ConnectionError":
        return "handle_connection_error"
    return "generic_fix"


def _is_api_objective(objective: str) -> bool:
    lowered = objective.lower()
    return "api endpoint" in lowered or "using python requests" in lowered or "http://" in lowered or "https://" in lowered


def _objective_value(objective: str, key: str) -> str:
    pattern = rf"^\s*{re.escape(key)}\s*:\s*(.+?)\s*$"
    match = re.search(pattern, objective, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else ""


def _deterministic_http_client_probe(objective: str) -> str | None:
    url = _objective_value(objective, "URL")
    method = (_objective_value(objective, "Method") or "POST").upper()
    if not url or method != "POST":
        return None

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None

    return f'''import http.client
import json
from urllib.parse import urlparse


url = {url!r}
parsed = urlparse(url)
connection_class = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
host = parsed.netloc
path = parsed.path or "/"
if parsed.query:
    path += "?" + parsed.query


def send(payload, headers):
    body = json.dumps(payload)
    conn = connection_class(host, timeout=10)
    try:
        conn.request("POST", path, body=body, headers=headers)
        response = conn.getresponse()
        text = response.read().decode("utf-8", errors="replace")
        print(response.status, text)
    finally:
        conn.close()


send(
    {{"email": "test@test.com", "age": "25"}},
    {{"Content-Type": "application/json"}},
)
send(
    {{"email": "test@test.com", "age": "25"}},
    {{"Content-Type": "application/json", "Authorization": "Bearer demo"}},
)
send(
    {{"email": "test@test.com", "age": 25}},
    {{"Content-Type": "application/json", "Authorization": "Bearer demo"}},
)
'''


def _api_strategy_guidance(strategy: str) -> str:
    strategy_details = {
        "add_auth_hint": "- If the response is 401 or Unauthorized, print that authentication may be required.\n",
        "validate_endpoint": "- If the response is 404 or Not Found, print that the endpoint URL/path should be validated.\n",
        "handle_server_error": "- If the response is 5xx, print that the server returned an error and include the response body.\n",
        "safe_json_parse": "- Do not assume the response body is JSON; catch JSONDecodeError/ValueError around response.json().\n",
        "add_timeout_and_retry": "- Add timeout=10 to requests calls and catch requests.exceptions.Timeout.\n",
        "handle_connection_error": "- Catch requests.exceptions.ConnectionError and print the connection failure cleanly.\n",
    }

    return (
        "For API integration repair:\n"
        "- Use the requests library.\n"
        "- Pass timeout=10 to every request.\n"
        "- Print status_code for every response.\n"
        "- Print response.text safely, even for non-JSON bodies.\n"
        "- Wrap response.json() parsing in try/except and print a helpful message when JSON parsing fails.\n"
        "- Handle non-2xx responses by printing the exact phrase 'Handled non-2xx response' with the error details instead of crashing.\n"
        "- Catch requests.exceptions.Timeout and requests.exceptions.ConnectionError.\n"
        f"{strategy_details.get(strategy, '')}\n"
    )


def _build_user_prompt(objective: str, previous_attempts: list[dict]) -> str:
    if not previous_attempts:
        api_guidance = ""
        if _is_api_objective(objective):
            api_guidance = (
                "\nFor this API integration objective:\n"
                "- Use the requests library.\n"
                "- Pass timeout=10 to every request.\n"
                "- Print status_code and response.text.\n"
                "- If you parse JSON, wrap response.json() in try/except.\n"
                "- Handle non-2xx responses cleanly without hiding the status code.\n"
            )
        return (
            f"Objective:\n{objective}\n\n"
            "Generate an initial Python solution.\n"
            f"{api_guidance}"
            "Return only valid Python code."
        )

    last_attempt = previous_attempts[-1]
    parsed_error = {
        "error_type": last_attempt.get("error_type"),
        "error_message": last_attempt.get("error_message"),
    }
    if not parsed_error["error_type"] and not parsed_error["error_message"]:
        parsed_error = parse_error(last_attempt.get("stderr", ""))

    error_type = parsed_error["error_type"] or "UnknownError"
    error_message = parsed_error["error_message"]
    strategy = last_attempt.get("strategy") or select_strategy(parsed_error["error_type"])
    strategy_guidance = ""
    if strategy == "avoid_missing_dependency":
        strategy_guidance = (
            "For this strategy:\n"
            "- Do not ask the user to install packages.\n"
            "- Do not exit with failure because a package is missing.\n"
            "- Prefer Python standard library alternatives.\n"
            "- For HTTP calls, use urllib.request instead of requests.\n\n"
        )
    elif strategy in {
        "add_auth_hint",
        "validate_endpoint",
        "handle_server_error",
        "safe_json_parse",
        "add_timeout_and_retry",
        "handle_connection_error",
    }:
        strategy_guidance = _api_strategy_guidance(strategy)

    return (
        f"Original objective:\n{objective}\n\n"
        "You previously wrote:\n\n"
        f"{last_attempt['code']}\n\n"
        "It failed with:\n\n"
        f"{error_type}: {error_message}\n\n"
        "Repair strategy:\n"
        f"{strategy}\n\n"
        f"{strategy_guidance}"
        "Fix the code so that:\n"
        "- it no longer crashes\n"
        "- it follows the repair strategy\n"
        "- it preserves original inputs and constraints\n"
        "- it still fulfills the objective\n\n"
        "Do not change given constants or input assignments just to avoid the error.\n"
        "Fix by adding validation, fallback behavior, or explicit error handling.\n"
        "The repaired code must still represent the original scenario.\n\n"
        "Do not repeat the same solution.\n"
        "Return only valid Python code."
    )


def propose_code(objective: str, previous_attempts: list[dict]) -> str:
    if not previous_attempts:
        deterministic_code = _deterministic_http_client_probe(objective)
        if deterministic_code is not None:
            return deterministic_code

    _load_environment()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    messages = [
        {
            "role": "system",
            "content": (
                "You write executable Python code only. "
                "Return raw Python code with no markdown fences, no prose, and no explanations. "
                "Use previous runtime feedback to fix failures. "
                "Prefer simple deterministic code."
            ),
        },
        {
            "role": "user",
            "content": _build_user_prompt(objective, previous_attempts),
        },
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
    )

    code = response.choices[0].message.content or ""
    return _strip_markdown_fences(code)

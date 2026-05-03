import re
from urllib.parse import ParseResult, urlparse, urlunparse


def objective_value(objective: str, key: str) -> str:
    pattern = rf"^\s*{re.escape(key)}\s*:\s*(.+?)\s*$"
    match = re.search(pattern, objective, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else ""


def initial_api_state(objective: str) -> dict | None:
    url = objective_value(objective, "URL")
    method = (objective_value(objective, "Method") or "POST").upper()
    parsed = urlparse(url)
    if method != "POST" or parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return {
        "url": url,
        "method": method,
        "authorization": False,
        "valid_payload": False,
    }


def _host_docker_url(url: str) -> str:
    parsed = urlparse(url)
    netloc = "host.docker.internal"
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    return urlunparse(ParseResult(parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))


def decide_next_attempt(attempt: dict, state: dict) -> dict:
    signals = attempt.get("api_signals") if isinstance(attempt.get("api_signals"), dict) else {}
    next_state = dict(state)
    action = "stop"
    reason = "no_retry_rule_matched"

    if signals.get("is_infrastructure_failure"):
        next_state["url"] = _host_docker_url(str(state.get("url") or ""))
        action = "switch_target_to_host_docker_internal"
        reason = "network_failure_observed"
    elif signals.get("auth_failure_observed") and not state.get("authorization"):
        next_state["authorization"] = True
        action = "add_authorization_header"
        reason = "auth_failure_observed"
    elif signals.get("validation_failure_observed") and not state.get("valid_payload"):
        next_state["valid_payload"] = True
        action = "fix_payload_types"
        reason = "validation_failure_observed"

    return {
        "action": action,
        "reason": reason,
        "next_state": next_state,
    }


def build_http_client_attempt_code(state: dict) -> str:
    headers = {"Content-Type": "application/json"}
    if state.get("authorization"):
        headers["Authorization"] = "Bearer demo"
    age = 25 if state.get("valid_payload") else "25"

    return f'''import http.client
import json
from urllib.parse import urlparse


url = {str(state["url"])!r}
parsed = urlparse(url)
connection_class = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
host = parsed.netloc
path = parsed.path or "/"
if parsed.query:
    path += "?" + parsed.query

payload = {{"email": "test@test.com", "age": {age!r}}}
headers = {headers!r}
body = json.dumps(payload)
conn = connection_class(host, timeout=10)
try:
    conn.request("POST", path, body=body, headers=headers)
    response = conn.getresponse()
    text = response.read().decode("utf-8", errors="replace")
    print(response.status, text)
finally:
    conn.close()
'''

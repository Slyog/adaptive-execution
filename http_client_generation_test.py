from adaptive_decisions import build_http_client_attempt_code, decide_next_attempt, initial_api_state


def test_deterministic_api_probe_uses_header_dicts() -> None:
    objective = """Debug a broken API request that returns 400 and explain the failure.

Call this API endpoint using Python requests.
URL: http://127.0.0.1:8080/demo/users
Method: POST
Print the full response and handle errors."""

    state = initial_api_state(objective)
    code = build_http_client_attempt_code(state)

    assert "import http.client" in code
    assert "headers=None" not in code
    assert "headers = None" not in code
    assert "headers = {'Content-Type': 'application/json'}" in code
    assert "Authorization" not in code
    assert code.count('conn.request("POST", path, body=body, headers=headers)') == 1

    decision = decide_next_attempt(
        {"api_signals": {"auth_failure_observed": True, "is_infrastructure_failure": False}},
        state,
    )
    code = build_http_client_attempt_code(decision["next_state"])
    assert "'Authorization': 'Bearer demo'" in code
    assert '"age": \'25\'' in code

    decision = decide_next_attempt(
        {"api_signals": {"validation_failure_observed": True, "is_infrastructure_failure": False}},
        decision["next_state"],
    )
    code = build_http_client_attempt_code(decision["next_state"])
    assert "'Authorization': 'Bearer demo'" in code
    assert '"age": 25' in code


if __name__ == "__main__":
    test_deterministic_api_probe_uses_header_dicts()
    print("http client generation tests passed")

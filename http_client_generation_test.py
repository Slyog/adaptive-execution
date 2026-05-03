from llm import propose_code


def test_initial_api_probe_uses_header_dicts() -> None:
    objective = """Debug a broken API request that returns 400 and explain the failure.

Call this API endpoint using Python requests.
URL: http://127.0.0.1:8080/demo/users
Method: POST
Print the full response and handle errors."""

    code = propose_code(objective, [])

    assert "import http.client" in code
    assert "headers=None" not in code
    assert "headers = None" not in code
    assert '{"Content-Type": "application/json"}' in code
    assert '{"Content-Type": "application/json", "Authorization": "Bearer demo"}' in code
    assert code.count('conn.request("POST", path, body=body, headers=headers)') == 1


if __name__ == "__main__":
    test_initial_api_probe_uses_header_dicts()
    print("http client generation tests passed")

from llm import parse_error, select_strategy


CASES = [
    ("", "status_code: 401\nUnauthorized", "HTTPUnauthorized", "add_auth_hint"),
    ("", "HTTP 404: Not Found", "HTTPNotFound", "validate_endpoint"),
    ("", "status_code: 500\nServer Error", "HTTPServerError", "handle_server_error"),
    ("json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)", "", "JSONDecodeError", "safe_json_parse"),
    ("requests.exceptions.Timeout: request timed out", "", "RequestTimeout", "add_timeout_and_retry"),
    ("requests.exceptions.ConnectionError: failed to establish a new connection", "", "ConnectionError", "handle_connection_error"),
    ("ZeroDivisionError: division by zero", "", "ZeroDivisionError", "add_guard"),
    ("FileNotFoundError: [Errno 2] No such file or directory: 'data.txt'", "", "FileNotFoundError", "handle_file_missing"),
]


def main() -> None:
    for stderr, stdout, expected_error_type, expected_strategy in CASES:
        parsed = parse_error(stderr, stdout)
        strategy = select_strategy(parsed["error_type"])
        assert parsed["error_type"] == expected_error_type, (parsed, expected_error_type)
        assert strategy == expected_strategy, (strategy, expected_strategy)

    print("error detection tests passed")


if __name__ == "__main__":
    main()

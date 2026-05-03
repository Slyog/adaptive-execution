from api_signals import extract_api_signals, extract_api_signals_from_outputs


def test_success_sequence() -> None:
    signals = extract_api_signals(
        '\n'.join(
            [
                '401 {"error":"Unauthorized","details":"missing bearer token"}',
                '400 {"error":"Validation failed","details":{"age":"must be integer"}}',
                '200 {"status":"created","user":{"email":"test@test.com","age":25}}',
            ]
        )
    )

    assert signals["network_reachable"] is True
    assert signals["auth_failure_observed"] is True
    assert signals["validation_failure_observed"] is True
    assert signals["success_observed"] is True
    assert signals["status_sequence"] == [401, 400, 200]
    assert signals["final_success"] is True
    assert signals["failure_category"] == "none"
    assert signals["is_infrastructure_failure"] is False
    assert signals["success"] is True


def test_success_sequence_across_outputs() -> None:
    signals = extract_api_signals_from_outputs(
        [
            {"stdout": '401 {"error":"Unauthorized","details":"missing bearer token"}', "stderr": ""},
            {"stdout": '400 {"error":"Validation failed","details":{"age":"must be integer"}}', "stderr": ""},
            {"stdout": '200 {"status":"created","user":{"email":"test@test.com","age":25}}', "stderr": ""},
        ]
    )

    assert signals["status_sequence"] == [401, 400, 200]
    assert signals["failure_category"] == "none"
    assert signals["success"] is True


def test_connection_refused_is_network_failure() -> None:
    signals = extract_api_signals("", "Connection refused")

    assert signals["network_reachable"] is False
    assert signals["is_infrastructure_failure"] is True
    assert signals["failure_category"] == "network"
    assert signals["success"] is False


def test_socket_gaierror_errno_minus_3_is_network_failure() -> None:
    signals = extract_api_signals("", "socket.gaierror: [Errno -3] Try again")

    assert signals["network_reachable"] is False
    assert signals["is_infrastructure_failure"] is True
    assert signals["failure_category"] == "network"
    assert signals["success"] is False
    assert signals["final_success"] is False


def test_401_only_is_auth_failure() -> None:
    signals = extract_api_signals('401 {"error":"Unauthorized","details":"missing bearer token"}')

    assert signals["auth_failure_observed"] is True
    assert signals["status_sequence"] == [401]
    assert signals["failure_category"] == "auth"
    assert signals["success"] is False


def test_400_only_is_validation_failure() -> None:
    signals = extract_api_signals('400 {"error":"Validation failed","details":{"age":"must be integer"}}')

    assert signals["validation_failure_observed"] is True
    assert signals["status_sequence"] == [400]
    assert signals["failure_category"] == "validation"
    assert signals["success"] is False


def main() -> None:
    test_success_sequence()
    test_success_sequence_across_outputs()
    test_connection_refused_is_network_failure()
    test_socket_gaierror_errno_minus_3_is_network_failure()
    test_401_only_is_auth_failure()
    test_400_only_is_validation_failure()
    print("api signal tests passed")


if __name__ == "__main__":
    main()

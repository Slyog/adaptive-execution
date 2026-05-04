from unittest.mock import patch

import adaptive_execution


def test_deterministic_retry_reaches_success_with_decisions() -> None:
    outputs = [
        {
            "stdout": '401 {"error":"Unauthorized","details":"missing bearer token"}',
            "stderr": "",
            "exit_code": 0,
        },
        {
            "stdout": '400 {"error":"Validation failed","details":{"age":"must be integer"}}',
            "stderr": "",
            "exit_code": 0,
        },
        {
            "stdout": '200 {"status":"created","user":{"email":"test@test.com","age":25}}',
            "stderr": "",
            "exit_code": 0,
        },
    ]

    class FakeClient:
        def __init__(self):
            self.index = 0

        def run_code(self, code, allow_network=False):
            assert allow_network is True
            assert "headers=None" not in code
            output = outputs[self.index]
            self.index += 1
            return output

    def fail_llm(*args, **kwargs):
        raise AssertionError("deterministic API retry should not call the LLM")

    objective = """Debug a broken API request that returns 400 and explain the failure.

Call this API endpoint using Python requests.
URL: http://127.0.0.1:8080/demo/users
Method: POST
Print the full response and handle errors."""

    with (
        patch.object(adaptive_execution, "ExecutionEngineClient", FakeClient),
        patch.object(adaptive_execution, "propose_code", fail_llm),
        patch.object(adaptive_execution, "parse_error", lambda stderr, stdout: {"error_type": None, "error_message": ""}),
        patch.object(adaptive_execution, "select_strategy", lambda error_type: "generic_fix"),
    ):
        result = adaptive_execution.run_adaptive_execution(objective, max_attempts=3, allow_network=True)

    assert result["success"] is True
    assert result["allow_network"] is True
    assert result["api_signals"]["status_sequence"] == [401, 400, 200]
    assert result["api_signals"]["final_success"] is True
    assert result["api_signals"]["failure_category"] == "none"
    final_attempt_signals = result["attempts"][2]["api_signals"]
    assert final_attempt_signals["success_observed"] is True
    assert final_attempt_signals["final_success"] is True
    assert final_attempt_signals["success"] is True
    assert final_attempt_signals["failure_category"] == "none"
    assert [event["event"] for event in result["events"]] == [
        "execute",
        "observe",
        "decision",
        "execute",
        "observe",
        "decision",
        "execute",
        "observe",
    ]
    assert result["events"][2]["action"] == "add_authorization_header"
    assert result["events"][5]["action"] == "fix_payload_types"
    final_observe_signals = result["events"][7]["api_signals"]
    assert final_observe_signals["success_observed"] is True
    assert final_observe_signals["final_success"] is True
    assert final_observe_signals["success"] is True
    assert final_observe_signals["failure_category"] == "none"


def test_network_failure_decision_switches_to_host_docker_internal() -> None:
    state = {
        "url": "http://127.0.0.1:8080/demo/users",
        "method": "POST",
        "authorization": False,
        "valid_payload": False,
    }
    decision = adaptive_execution.decide_next_attempt(
        {"api_signals": {"is_infrastructure_failure": True}},
        state,
    )

    assert decision["action"] == "switch_target_to_host_docker_internal"
    assert decision["next_state"]["url"] == "http://host.docker.internal:8080/demo/users"


def test_network_failure_decision_preserves_codespaces_path_and_uses_8880() -> None:
    state = {
        "url": "https://stunning-space-happiness-69j455w46v4247p7-8880.app.github.dev/demo/users",
        "method": "POST",
        "authorization": False,
        "valid_payload": False,
    }
    decision = adaptive_execution.decide_next_attempt(
        {"api_signals": {"is_infrastructure_failure": True}},
        state,
    )

    assert decision["action"] == "switch_target_to_host_docker_internal"
    assert decision["next_state"]["url"] == "http://host.docker.internal:8880/demo/users"


if __name__ == "__main__":
    test_deterministic_retry_reaches_success_with_decisions()
    test_network_failure_decision_switches_to_host_docker_internal()
    test_network_failure_decision_preserves_codespaces_path_and_uses_8880()
    print("adaptive retry tests passed")

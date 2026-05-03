from unittest.mock import patch

import adaptive_execution


def test_run_response_includes_api_signal_fields():
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
            output = outputs[self.index]
            self.index += 1
            return output

    with (
        patch.object(adaptive_execution, "ExecutionEngineClient", FakeClient),
        patch.object(adaptive_execution, "propose_code", lambda objective, attempts: f"code {len(attempts) + 1}"),
        patch.object(adaptive_execution, "parse_error", lambda stderr, stdout: {"error_type": None, "error_message": ""}),
        patch.object(adaptive_execution, "select_strategy", lambda error_type: "generic_fix"),
    ):
        result = adaptive_execution.run_adaptive_execution("demo users", max_attempts=3)

    assert result["success"] is True
    assert result["failure_category"] == "none"
    assert result["is_infrastructure_failure"] is False
    assert result["api_signals"]["status_sequence"] == [401, 400, 200]
    assert result["api_signals"]["network_reachable"] is True
    assert result["api_signals"]["auth_failure_observed"] is True
    assert result["api_signals"]["validation_failure_observed"] is True
    assert result["api_signals"]["success_observed"] is True
    assert result["api_signals"]["final_success"] is True

    for attempt in result["attempts"]:
        assert "api_signals" in attempt
        assert attempt["failure_category"] == attempt["api_signals"]["failure_category"]
        assert attempt["is_infrastructure_failure"] == attempt["api_signals"]["is_infrastructure_failure"]

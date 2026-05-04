import json
from unittest.mock import patch

import adaptive_execution
from adaptive_tool import adaptive_execution_run


def test_adaptive_execution_run_tool_returns_compact_success_result() -> None:
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
            output = outputs[self.index]
            self.index += 1
            return output

    def fail_llm(*args, **kwargs):
        raise AssertionError("tool adapter should reuse deterministic adaptive execution")

    with (
        patch.object(adaptive_execution, "ExecutionEngineClient", FakeClient),
        patch.object(adaptive_execution, "propose_code", fail_llm),
        patch.object(adaptive_execution, "parse_error", lambda stderr, stdout: {"error_type": None, "error_message": ""}),
        patch.object(adaptive_execution, "select_strategy", lambda error_type: "generic_fix"),
    ):
        result = adaptive_execution_run(
            endpoint_url="http://127.0.0.1:8880/demo/users",
            method="POST",
            objective="Debug the API request.",
            allow_network=True,
            max_attempts=3,
        )

    assert result["final_success"] is True
    assert result["status_sequence"] == [401, 400, 200]
    assert len(result["attempts"]) == 3
    json.dumps(result)


if __name__ == "__main__":
    test_adaptive_execution_run_tool_returns_compact_success_result()
    print("adaptive tool tests passed")

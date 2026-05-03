import argparse
import json
from typing import Optional

from api_signals import extract_api_signals, extract_api_signals_from_outputs
from client import ExecutionEngineClient
from llm import API_ERROR_TYPES, parse_error, propose_code, select_strategy


def _api_error_was_handled(stdout: str, error_type: str | None) -> bool:
    if error_type not in API_ERROR_TYPES:
        return False

    text = (stdout or "").lower()
    handled_markers = [
        "handled non-2xx response",
        "json parsing failed",
        "response is not valid json",
        "request timed out",
        "connection error",
        "authentication may be required",
        "endpoint url/path should be validated",
        "server returned an error",
    ]
    return any(marker in text for marker in handled_markers)


def run_adaptive_execution(objective: str, max_attempts: int = 3) -> dict:
    client = ExecutionEngineClient()
    attempts = []
    final_attempt: Optional[dict] = None

    for attempt_number in range(1, max_attempts + 1):
        code = propose_code(objective, attempts)

        if attempts and code.strip() == attempts[-1]["code"].strip():
            attempt = {
                "attempt_number": attempt_number,
                "code": code,
                "stdout": "",
                "stderr": "duplicate attempt",
                "exit_code": 1,
                "success": False,
                "error_type": None,
                "error_message": "duplicate attempt",
                "strategy": "generic_fix",
                "reason": "duplicate_attempt",
                "api_signals": extract_api_signals("", "duplicate attempt"),
            }
            attempts.append(attempt)
            final_attempt = attempt

            print(f"attempt_number: {attempt_number}")
            print(f"exit_code: {attempt['exit_code']}")
            print(f"success: {attempt['success']}")
            break

        result = client.run_code(code)
        api_signals = extract_api_signals(result["stdout"], result["stderr"])
        parsed_error = parse_error(result["stderr"], result["stdout"])

        api_error_type = parsed_error["error_type"] if parsed_error["error_type"] in API_ERROR_TYPES else None
        handled_api_error = _api_error_was_handled(result["stdout"], api_error_type)
        success = api_signals["success"] or (
            result["exit_code"] == 0
            and not api_signals["is_infrastructure_failure"]
            and api_signals["failure_category"] not in {"auth", "validation"}
            and (api_error_type is None or handled_api_error)
        )
        strategy = None if success else select_strategy(parsed_error["error_type"])
        attempt = {
            "attempt_number": attempt_number,
            "code": code,
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "exit_code": result["exit_code"],
            "success": success,
            "error_type": parsed_error["error_type"],
            "error_message": parsed_error["error_message"],
            "strategy": strategy,
            "failure_category": api_signals["failure_category"],
            "api_signals": api_signals,
        }

        attempts.append(attempt)
        final_attempt = attempt

        print(f"attempt_number: {attempt_number}")
        print(f"exit_code: {attempt['exit_code']}")
        print(f"success: {attempt['success']}")

        if success:
            break

    api_signals = extract_api_signals_from_outputs(attempts)
    return {
        "objective": objective,
        "success": api_signals["success"] or bool(final_attempt and final_attempt["success"]),
        "api_signals": api_signals,
        "final_attempt": final_attempt,
        "attempts": attempts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an adaptive execution loop.")
    parser.add_argument("objective", help="Objective for the LLM-generated Python code.")
    parser.add_argument("--max-attempts", type=int, default=3)
    args = parser.parse_args()

    result = run_adaptive_execution(args.objective, args.max_attempts)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

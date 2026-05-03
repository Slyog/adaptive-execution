import argparse
import json
from typing import Optional

from client import ExecutionEngineClient
from llm import propose_code


def run_adaptive_execution(objective: str, max_attempts: int = 3) -> dict:
    client = ExecutionEngineClient()
    attempts = []
    final_attempt: Optional[dict] = None

    for attempt_number in range(1, max_attempts + 1):
        code = propose_code(objective, attempts)
        result = client.run_code(code)

        success = result["exit_code"] == 0
        attempt = {
            "attempt_number": attempt_number,
            "code": code,
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "exit_code": result["exit_code"],
            "success": success,
        }

        attempts.append(attempt)
        final_attempt = attempt

        print(f"attempt_number: {attempt_number}")
        print(f"exit_code: {attempt['exit_code']}")
        print(f"success: {attempt['success']}")

        if success:
            break

    return {
        "objective": objective,
        "success": bool(final_attempt and final_attempt["success"]),
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

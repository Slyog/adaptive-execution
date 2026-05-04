from typing import Any

from adaptive_execution import run_adaptive_execution


def _objective_with_endpoint(objective: str, endpoint_url: str, method: str) -> str:
    return "\n".join(
        [
            f"URL: {endpoint_url}",
            f"Method: {method.upper()}",
            "",
            objective.strip(),
        ]
    ).strip()


def _compact_attempt(attempt: dict[str, Any]) -> dict[str, Any]:
    api_signals = attempt.get("api_signals") if isinstance(attempt.get("api_signals"), dict) else {}
    return {
        "attempt_number": attempt.get("attempt_number"),
        "success": attempt.get("success"),
        "exit_code": attempt.get("exit_code"),
        "status_sequence": api_signals.get("status_sequence", []),
        "failure_category": api_signals.get("failure_category"),
        "final_success": api_signals.get("final_success"),
        "stdout": attempt.get("stdout", ""),
        "stderr": attempt.get("stderr", ""),
    }


def _compact_decision(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "attempt_number": event.get("attempt_number"),
        "reason": event.get("reason"),
        "action": event.get("action"),
        "next_attempt_strategy": event.get("next_attempt_strategy") or event.get("action"),
        "next_state": event.get("next_state"),
    }


def adaptive_execution_run(
    endpoint_url: str,
    method: str,
    objective: str,
    allow_network: bool,
    max_attempts: int,
) -> dict[str, Any]:
    result = run_adaptive_execution(
        _objective_with_endpoint(objective, endpoint_url, method),
        max_attempts=max_attempts,
        allow_network=allow_network,
    )
    api_signals = result.get("api_signals") if isinstance(result.get("api_signals"), dict) else {}
    attempts = result.get("attempts") if isinstance(result.get("attempts"), list) else []
    events = result.get("events") if isinstance(result.get("events"), list) else []
    final_attempt = result.get("final_attempt") if isinstance(result.get("final_attempt"), dict) else {}

    return {
        "final_success": bool(api_signals.get("final_success") or result.get("success")),
        "status_sequence": api_signals.get("status_sequence", []),
        "attempts": [_compact_attempt(attempt) for attempt in attempts],
        "decisions": [_compact_decision(event) for event in events if event.get("event") == "decision"],
        "final_stdout": final_attempt.get("stdout", ""),
    }

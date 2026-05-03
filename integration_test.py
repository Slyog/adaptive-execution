import json
import sys
from urllib import error, request


URL = "http://127.0.0.1:8080/adaptive-execution/run"


OBJECTIVES = [
    "Write Python code that reads a file named data.txt and prints its content.",
    (
        "Call this API endpoint using Python requests.\n"
        "URL: https://httpbin.org/status/404\n"
        "Method: GET\n"
        "Body: \n"
        "Print the full response and handle errors."
    ),
    (
        "Call this API endpoint using Python requests.\n"
        "URL: https://httpbin.org/json\n"
        "Method: GET\n"
        "Body: \n"
        "Print the full response and handle errors."
    ),
]


def run_objective(objective: str) -> bool:
    payload = json.dumps(
        {
            "objective": objective,
            "max_attempts": 3,
        }
    ).encode("utf-8")

    req = request.Request(
        URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=300) as response:
            body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"request failed: HTTP {exc.code}: {body}")
        return False
    except error.URLError as exc:
        print(f"request failed: {exc.reason}")
        return False
    except TimeoutError:
        print("request failed: timed out")
        return False

    try:
        result = json.loads(body)
    except json.JSONDecodeError:
        print(f"request failed: invalid JSON response: {body}")
        return False

    print("=" * 72)
    print(f"objective: {objective}")
    attempts = result.get("attempts", [])
    print(f"success: {result.get('success')}")
    print(f"attempt_count: {len(attempts)}")

    for attempt in attempts:
        print(
            "attempt "
            f"{attempt.get('attempt_number')}: "
            f"exit_code={attempt.get('exit_code')} "
            f"success={attempt.get('success')} "
            f"error_type={attempt.get('error_type')} "
            f"strategy={attempt.get('strategy')}"
        )

    return result.get("success") is True


def main() -> int:
    successes = [run_objective(objective) for objective in OBJECTIVES]
    return 0 if all(successes) else 1


if __name__ == "__main__":
    sys.exit(main())

import json
import sys
from urllib import error, request


URL = "http://127.0.0.1:8080/openclaw/run"


def main() -> int:
    payload = json.dumps(
        {
            "objective": "Write Python code that reads a file named data.txt and prints its content.",
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
        return 1
    except error.URLError as exc:
        print(f"request failed: {exc.reason}")
        return 1
    except TimeoutError:
        print("request failed: timed out")
        return 1

    try:
        result = json.loads(body)
    except json.JSONDecodeError:
        print(f"request failed: invalid JSON response: {body}")
        return 1

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

    return 0 if result.get("success") is True else 1


if __name__ == "__main__":
    sys.exit(main())

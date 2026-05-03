import os
import re

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def _load_dotenv_file(path: str = ".env") -> None:
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


def _load_environment() -> None:
    if load_dotenv is not None:
        load_dotenv()
        return

    _load_dotenv_file()


def _strip_markdown_fences(text: str) -> str:
    stripped = text.strip()
    match = re.match(r"^```(?:python|py)?\s*(.*?)\s*```$", stripped, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return stripped


def parse_error(stderr: str) -> dict:
    message = (stderr or "").strip()
    if not message:
        return {
            "error_type": None,
            "error_message": "",
        }

    for line in reversed(message.splitlines()):
        line = line.strip()
        if not line:
            continue

        match = re.match(r"^([A-Za-z_][A-Za-z0-9_.]*):\s*(.*)$", line)
        if match:
            return {
                "error_type": match.group(1),
                "error_message": match.group(2),
            }

    return {
        "error_type": None,
        "error_message": message,
    }


def _build_user_prompt(objective: str, previous_attempts: list[dict]) -> str:
    if not previous_attempts:
        return (
            f"Objective:\n{objective}\n\n"
            "Generate an initial Python solution.\n"
            "Return only valid Python code."
        )

    last_attempt = previous_attempts[-1]
    parsed_error = {
        "error_type": last_attempt.get("error_type"),
        "error_message": last_attempt.get("error_message"),
    }
    if not parsed_error["error_type"] and not parsed_error["error_message"]:
        parsed_error = parse_error(last_attempt.get("stderr", ""))

    error_type = parsed_error["error_type"] or "UnknownError"
    error_message = parsed_error["error_message"]

    return (
        f"Original objective:\n{objective}\n\n"
        "You previously wrote the following code:\n\n"
        f"{last_attempt['code']}\n\n"
        "It failed with the following error:\n\n"
        f"{error_type}: {error_message}\n\n"
        "Fix the code so that:\n"
        "- it no longer crashes\n"
        "- it still fulfills the original objective\n\n"
        "- Preserve the original objective and its given input values.\n"
        "- Do not change given constants or input assignments just to avoid the error.\n"
        "- Fix the program by adding validation, fallback behavior, or explicit error handling.\n"
        "- The repaired code must still represent the original scenario.\n\n"
        "Do not repeat the same solution.\n"
        "Return only valid Python code."
    )


def propose_code(objective: str, previous_attempts: list[dict]) -> str:
    _load_environment()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    messages = [
        {
            "role": "system",
            "content": (
                "You write executable Python code only. "
                "Return raw Python code with no markdown fences, no prose, and no explanations. "
                "Use previous runtime feedback to fix failures. "
                "Prefer simple deterministic code."
            ),
        },
        {
            "role": "user",
            "content": _build_user_prompt(objective, previous_attempts),
        },
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
    )

    code = response.choices[0].message.content or ""
    return _strip_markdown_fences(code)

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


def _format_previous_attempts(previous_attempts: list[dict]) -> str:
    if not previous_attempts:
        return "No previous attempts."

    formatted = []
    for attempt in previous_attempts:
        formatted.append(
            "\n".join(
                [
                    f"Attempt {attempt['attempt_number']}:",
                    f"Code:\n{attempt['code']}",
                    f"stdout:\n{attempt['stdout']}",
                    f"stderr:\n{attempt['stderr']}",
                    f"exit_code: {attempt['exit_code']}",
                ]
            )
        )
    return "\n\n".join(formatted)


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
            "content": (
                f"Objective:\n{objective}\n\n"
                f"Previous attempts and real execution feedback:\n"
                f"{_format_previous_attempts(previous_attempts)}\n\n"
                "Return only the next complete Python program."
            ),
        },
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
    )

    code = response.choices[0].message.content or ""
    return _strip_markdown_fences(code)

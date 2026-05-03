# adaptive-execution

Minimal adaptive execution loop for improving Python code using real runtime feedback.

## What This Is

- A Phase 1 execution-first retry loop.
- A small system that asks an LLM to propose Python code, executes that code, observes the result, and retries with failure context.
- A client of the AI Execution Engine raw execution endpoint.
- An in-memory process with explicit attempts and visible failures.

## What This Is Not

- Not a chatbot.
- Not a UI.
- Not a simulation.
- Not a replacement for the AI Execution Engine.
- Not a nested LLM execution engine.
- Not a database-backed runtime.

## Architecture

```text
objective
  -> adaptive_execution.py
  -> llm.py proposes Python code
  -> client.py sends raw code to AI Execution Engine POST /execute
  -> AI Execution Engine runs code in Docker
  -> stdout, stderr, exit_code
  -> adaptive_execution.py decides success or retries
```

Responsibilities:

- `adaptive_execution.py` owns the retry loop and attempt structure.
- `llm.py` proposes executable Python code.
- `client.py` sends raw generated code to the AI Execution Engine.
- AI Execution Engine executes code in Docker and returns runtime output.

Success is determined by execution:

```text
exit_code == 0
```

## How To Run

Requirements:

- AI Execution Engine running on `http://127.0.0.1:8000`
- Docker available to the AI Execution Engine
- `OPENAI_API_KEY` set in the environment or local `.env`

Run:

```powershell
python adaptive_execution.py "Write Python code that reads a file named data.txt and prints its content."
```

The loop prints each attempt:

```text
attempt_number: 1
exit_code: 1
success: False
attempt_number: 2
exit_code: 0
success: True
```

## Validation Example

Validated objective:

```text
Write Python code that reads a file named data.txt and prints its content.
```

Observed behavior:

- Attempt 1 generated code that tried to read `data.txt` directly.
- Attempt 1 failed with `FileNotFoundError`.
- Attempt 2 used the previous `stderr` failure context.
- Attempt 2 succeeded by checking whether `data.txt` exists before reading it.

This validates the Phase 1 behavior: runtime failure feedback is included in the next LLM proposal, and the loop adapts based on real execution output.

## Current Limitations

- Phase 1 only.
- Uses in-memory attempt history only.
- No database.
- No UI.
- No background worker.
- No concurrency.
- No evaluation beyond `exit_code == 0`.
- Depends on the AI Execution Engine for Docker execution.
- Depends on an LLM provider for code proposals.
- Does not modify the AI Execution Engine.

## Phase 1 Status

Validated.

The current implementation demonstrates a working adaptive retry loop using real execution feedback from the AI Execution Engine raw code execution endpoint.

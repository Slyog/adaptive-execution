# AI Execution System – adaptive-execution (Decision Layer)

Adaptive-execution is the decision layer of a 3-part AI execution system.

It observes real runtime failures, maps them to deterministic repair strategies, and retries execution until success.

---

## System Overview

This repository is part of a 3-layer execution system:

| Layer | Role | Repo |
|---|---|---|
| **AI-Execution-Engine** | Executes Python code in a deterministic Docker runtime | [Slyog/AI-Execution-Engine](https://github.com/Slyog/AI-Execution-Engine) |
| **adaptive-execution** *(this repo)* | Interprets failures and applies repair strategies | [Slyog/adaptive-execution](https://github.com/Slyog/adaptive-execution) |
| **Tracewell Runtime** (UI) | Visualizes execution traces and decisions | [Slyog/execution-trace-ui](https://github.com/Slyog/execution-trace-ui) |

**Architecture:**

```text
objective
→ adaptive-execution     (decision layer)
→ AI-Execution-Engine    (runtime)
→ real API / environment
→ stdout, stderr, exit_code
→ adaptive-execution interprets + retries
```

---

## What This Layer Does

- Runs an adaptive retry loop
- Interprets runtime failures
- Maps failures to repair strategies
- Generates improved attempts
- Stops when success is observed or attempts are exhausted

> This layer does not execute code directly.  
> It depends on the AI Execution Engine for runtime truth.

---

## What This Is Not

- Not a chatbot
- Not a UI
- Not a simulation
- Not a replacement for the execution engine
- Not a database-backed system

---

## Core Behavior

```text
execute → observe → decision → execute → observe → decision → execute → observe
```

Each attempt:

1. Code is proposed
2. Code is executed in Docker (via AI-Execution-Engine)
3. Runtime output is collected
4. Failures are mapped to signals
5. Deterministic repair rules are applied

**Example:**

```text
Attempt 1 → failure
  POST /users returns 401
  auth_failure_observed = true

Attempt 2 → partial fix
  Authorization header added
  POST /users returns 400
  validation_failure_observed = true

Attempt 3 → success
  Payload fixed (age as integer)
  POST /users returns 200
  success_observed = true
```

---

## Key Idea

> **LLM proposals are not trusted. Execution output is the source of truth.**  
> All repair decisions are based on observed runtime signals.

---

## Architecture (Detailed)

```text
objective
  → adaptive_execution.py
  → llm.py proposes Python code
  → client.py sends raw code to AI Execution Engine POST /execute
  → AI Execution Engine runs code in Docker
  → stdout, stderr, exit_code
  → adaptive_execution.py decides success or retries
```

**Responsibilities:**

| File | Role |
|---|---|
| `adaptive_execution.py` | Owns retry loop and attempt structure |
| `llm.py` | Proposes executable Python code |
| `client.py` | Sends code to AI Execution Engine |
| AI Execution Engine | Executes code and returns runtime output |

---

## Success Criteria

For CLI runs:

```text
exit_code == 0
```

For API runs:

```json
{
  "final_success": true,
  "status_sequence": [401, 400, 200]
}
```

---

## How To Run (CLI)

**Requirements:**

- AI Execution Engine running on `http://127.0.0.1:8000`
- Docker available to the AI Execution Engine
- `OPENAI_API_KEY` set in environment or `.env`

**Run:**

```powershell
python adaptive_execution.py "Write Python code that reads a file named data.txt and prints its content."
```

**Output:**

```text
attempt_number: 1
exit_code: 1
success: False

attempt_number: 2
exit_code: 0
success: True
```

---

## Adaptive Execution API

**Start:**

```powershell
uvicorn api:app --host 0.0.0.0 --port 8880
```

**Health check:**

```powershell
curl http://localhost:8880/health
```

**Run:**

```bash
curl -X POST http://localhost:8880/adaptive-execution/run \
  -H "Content-Type: application/json" \
  -d '{"objective":"Write Python code that prints hello"}'
```

**Example request body:**

```json
{
  "objective": "Write Python code that reads a file named data.txt and prints its content.",
  "max_attempts": 3
}
```

**Observed behavior:**

- Attempt 1 fails with `FileNotFoundError`
- Attempt 2 adapts using failure context
- Attempt 2 succeeds

```text
attempt 1: exit_code=1  success=false  error_type=FileNotFoundError  strategy=handle_file_missing
attempt 2: exit_code=0  success=true   error_type=null               strategy=null
```

---

## Current Limitations

- In-memory attempt history only
- No persistence / database
- No concurrency
- No UI — handled by [Tracewell Runtime](https://github.com/Slyog/execution-trace-ui)
- Depends on AI Execution Engine for Docker execution
- LLM used only for code proposals, not for decision-making

---

## Phase 1 Status

**Validated.**

This implementation demonstrates a working adaptive retry loop using real execution feedback from the AI Execution Engine.

- CLI validated
- API validated
- Structured repair strategy validated

---

## Optional: Agent Integration

This layer can be exposed as a tool (e.g. for OpenClaw):

```python
adaptive_execution_run(objective, max_attempts, allow_network)
```

Agents can invoke execution — but decisions remain deterministic and based on runtime signals.

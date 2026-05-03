from fastapi import FastAPI
from pydantic import BaseModel, Field

from adaptive_execution import run_adaptive_execution


app = FastAPI(title="adaptive-execution")


class RunRequest(BaseModel):
    objective: str
    max_attempts: int = Field(default=3, ge=1)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def _run(request: RunRequest) -> dict:
    print(f"[adaptive-execution] objective={request.objective} max_attempts={request.max_attempts}")
    return run_adaptive_execution(request.objective, request.max_attempts)


@app.post("/adaptive-execution/run")
def run_adaptive_execution_endpoint(request: RunRequest) -> dict:
    return _run(request)


@app.post("/openclaw/run")
def run_openclaw_deprecated(request: RunRequest) -> dict:
    result = _run(request)
    return {
        "warning": "Deprecated endpoint. Use /adaptive-execution/run",
        **result,
    }

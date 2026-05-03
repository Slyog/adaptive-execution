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


@app.post("/openclaw/run")
def run_openclaw(request: RunRequest) -> dict:
    print(f"[openclaw] objective={request.objective} max_attempts={request.max_attempts}")
    return run_adaptive_execution(request.objective, request.max_attempts)

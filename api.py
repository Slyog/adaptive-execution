from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from adaptive_execution import run_adaptive_execution


app = FastAPI(title="adaptive-execution")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    objective: str
    max_attempts: int = Field(default=3, ge=1)
    allow_network: bool = False


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/cors-debug")
def cors_debug() -> dict:
    return {"cors": "enabled"}


# Demo:
# curl -X POST http://localhost:8880/demo/users \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer demo" \
#   -d '{"email":"test@test.com","age":"25"}'
# Expected: 400 Validation failed
@app.post("/demo/users")
async def create_demo_user(request: Request):
    if "authorization" not in request.headers:
        return JSONResponse(
            status_code=401,
            content={
                "error": "Unauthorized",
                "details": "missing bearer token",
            },
        )

    payload = await request.json()
    age = payload.get("age")
    if type(age) is not int:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Validation failed",
                "details": {
                    "age": "must be integer",
                },
            },
        )

    return {
        "status": "created",
        "user": {
            "email": payload.get("email"),
            "age": age,
        },
    }


def _run(request: RunRequest) -> dict:
    print(
        f"[adaptive-execution] objective={request.objective} "
        f"max_attempts={request.max_attempts} "
        f"network={'enabled' if request.allow_network else 'none'}"
    )
    return run_adaptive_execution(request.objective, request.max_attempts, allow_network=request.allow_network)


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

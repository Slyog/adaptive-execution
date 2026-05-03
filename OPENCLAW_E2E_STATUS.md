# OpenClaw E2E Status

## Confirmed Working

- `adaptive-execution` service is running at `http://127.0.0.1:8080`.
- AI Execution Engine is running at `http://127.0.0.1:8000`.
- OpenClaw gateway starts successfully on `http://127.0.0.1:18789`.
- The local plugin path is linked into OpenClaw:
  - `c:\Users\slyse\Documents\adaptive-execution\openclaw-plugin`
- Gateway startup logs show:
  - `http server listening (1 plugin: adaptive-execution; ...)`
- Runtime inspection confirms the plugin loads and declares/registers:
  - `adaptive_execution_run`

## Runtime Inspection Command

```powershell
npx -y -p node@22 -p openclaw openclaw plugins inspect adaptive-execution --runtime --json
```

Observed runtime inspection result included:

```json
{
  "plugin": {
    "id": "adaptive-execution",
    "status": "loaded",
    "toolNames": ["adaptive_execution_run"],
    "contracts": {
      "tools": ["adaptive_execution_run"]
    },
    "diagnostics": []
  }
}
```

## Gateway Invoke Request Attempted

```powershell
$body = @{
  name = "adaptive_execution_run"
  args = @{
    objective = "Write Python code that reads a file named data.txt and prints its content."
    max_attempts = 3
  }
  sessionKey = "main"
} | ConvertTo-Json -Depth 8

Invoke-WebRequest `
  -Uri "http://127.0.0.1:18789/tools/invoke" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body `
  -UseBasicParsing `
  -TimeoutSec 420
```

Equivalent request body:

```json
{
  "name": "adaptive_execution_run",
  "args": {
    "objective": "Write Python code that reads a file named data.txt and prints its content.",
    "max_attempts": 3
  },
  "sessionKey": "main"
}
```

## 404 Response

Observed response:

```text
HTTP 404
```

No JSON error body was returned.

## Likely Causes

- The direct invocation route may not be the correct route for this plugin/tool path.
- The request body shape for `POST /tools/invoke` may still differ from the attempted `name/tool + args + sessionKey` shape.
- Gateway tool allowlist or policy resolution may still exclude the plugin tool even though plugin runtime inspection sees it.
- The plugin may be registered for OpenClaw agent runtime discovery, but not exposed through direct Gateway HTTP invocation.

## Environment Boundary Notes

- AI Execution Engine Docker runtime works in the GitHub Codespaces/workspace environment, not on local Windows.
- If OpenClaw Gateway runs inside the same Codespace as `adaptive-execution`, the plugin `baseUrl` can be:

```text
http://127.0.0.1:8080
```

- If OpenClaw Gateway runs locally on Windows, the plugin `baseUrl` must point to the Codespaces forwarded URL:

```text
https://verbose-waffle-jjxq779qx9vhpxv6-8880.app.github.dev
```

- Local Windows cannot complete the full E2E path if the AI Execution Engine depends on the Docker runtime that only works in the workspace.

## Next Minimal Verification

- Invoke `adaptive_execution_run` through the actual OpenClaw chat/agent path, where plugin tools are planned and called by the agent runtime.
- If direct HTTP invocation is required, confirm the exact supported direct invocation endpoint and request shape from OpenClaw source/docs before making more config changes.
- Recommended next path: run OpenClaw Gateway in the same Codespace and invoke `adaptive_execution_run` there, or configure plugin `baseUrl` to the forwarded Codespace URL for local OpenClaw testing.
- Do not claim full E2E success until `adaptive_execution_run` is invoked through OpenClaw and returns adaptive-execution details.

## Current Conclusion

The plugin is linked and runtime-registered, but full end-to-end execution through OpenClaw has not been proven. The blocker is the OpenClaw Gateway direct invocation returning HTTP 404 for `adaptive_execution_run`.

# OpenClaw Integration Plan

## Goal

Integrate `adaptive-execution` as a separate OpenClaw tool service.

`adaptive-execution` remains its own HTTP service. OpenClaw calls it through a small native plugin tool. The adaptive retry loop, LLM proposal logic, and AI Execution Engine integration stay unchanged.

## OpenClaw Findings

OpenClaw supports native plugins with:

- `package.json` containing `openclaw.extensions`
- `openclaw.plugin.json` in the plugin root
- a TypeScript entry file exporting `definePluginEntry(...)`
- runtime tool registration through `api.registerTool(...)`

Agent tools must be declared in `openclaw.plugin.json` under:

```json
{
  "contracts": {
    "tools": ["adaptive_execution_run"]
  }
}
```

Tools are registered with a typed parameter schema and an `execute(toolCallId, params)` function.

## Integration Shape

OpenClaw calls the plugin tool:

```text
adaptive_execution_run
```

Tool input:

```json
{
  "objective": "Write Python code that prints hello",
  "max_attempts": 3
}
```

The plugin sends:

```text
POST /adaptive-execution/run
```

Request body:

```json
{
  "objective": "Write Python code that prints hello",
  "max_attempts": 3
}
```

Required adaptive-execution endpoint:

```text
POST http://127.0.0.1:8080/adaptive-execution/run
```

Returned fields consumed by OpenClaw:

- `success`
- `attempts`
- `final_attempt`

The plugin returns the full response as structured `details` and a compact text summary for the agent.

## Configuration

Default service URL:

```text
http://127.0.0.1:8080
```

Override options:

- OpenClaw plugin config: `plugins.entries.adaptive-execution.config.baseUrl`
- environment variable: `ADAPTIVE_EXECUTION_URL`

Example OpenClaw config:

```json5
{
  plugins: {
    load: {
      paths: ["./openclaw-plugin"]
    },
    entries: {
      "adaptive-execution": {
        enabled: true,
        config: {
          baseUrl: "http://127.0.0.1:8080"
        }
      }
    }
  },
  tools: {
    allow: ["adaptive_execution_run"]
  }
}
```

## Local Run

Start adaptive-execution:

```bash
uvicorn api:app --host 0.0.0.0 --port 8080
```

Install or load the plugin in OpenClaw from the local path:

```bash
openclaw plugins install ./openclaw-plugin
openclaw gateway restart
openclaw plugins inspect adaptive-execution --runtime --json
```

## Boundaries

- No database.
- No authentication yet.
- No OpenClaw vendoring.
- No adaptive-execution core refactor.
- OpenClaw owns tool invocation.
- adaptive-execution owns adaptation.
- AI Execution Engine owns code execution truth.

## Status

Plugin interface is clear enough for a minimal native tool wrapper.

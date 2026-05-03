import { Type } from "@sinclair/typebox";
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";

type OpenClawRunParams = {
  objective: string;
  max_attempts?: number;
};

type AdaptiveExecutionResult = {
  success?: boolean;
  attempts?: unknown[];
  final_attempt?: unknown;
  [key: string]: unknown;
};

function resolveBaseUrl(config: Record<string, unknown> | undefined): string {
  const configured = config?.baseUrl;
  if (typeof configured === "string" && configured.trim()) {
    return configured.trim().replace(/\/+$/, "");
  }

  const envUrl = process.env.ADAPTIVE_EXECUTION_URL;
  if (envUrl && envUrl.trim()) {
    return envUrl.trim().replace(/\/+$/, "");
  }

  return "http://127.0.0.1:8080";
}

function summarizeResult(result: AdaptiveExecutionResult): string {
  const attempts = Array.isArray(result.attempts) ? result.attempts : [];
  return [
    `success: ${String(result.success)}`,
    `attempt_count: ${attempts.length}`,
  ].join("\n");
}

export default definePluginEntry({
  id: "adaptive-execution",
  name: "adaptive-execution",
  description: "Calls the adaptive-execution HTTP service as an OpenClaw tool.",
  register(api) {
    api.registerTool({
      name: "adaptive_execution_run",
      description:
        "Run adaptive-execution for a Python coding objective and return the full attempt history.",
      parameters: Type.Object(
        {
          objective: Type.String({
            description: "Objective for adaptive-execution to solve.",
          }),
          max_attempts: Type.Optional(
            Type.Integer({
              minimum: 1,
              default: 3,
              description: "Maximum adaptive attempts.",
            }),
          ),
        },
        { additionalProperties: false },
      ),
      async execute(_toolCallId, params) {
        const input = params as OpenClawRunParams;
        const baseUrl = resolveBaseUrl(api.pluginConfig);
        const response = await fetch(`${baseUrl}/adaptive-execution/run`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            objective: input.objective,
            max_attempts: input.max_attempts ?? 3,
          }),
        });

        const text = await response.text();
        if (!response.ok) {
          return {
            content: [
              {
                type: "text",
                text: `adaptive-execution request failed: HTTP ${response.status}: ${text}`,
              },
            ],
            details: {
              success: false,
              status: response.status,
              body: text,
            },
          };
        }

        let result: AdaptiveExecutionResult;
        try {
          result = JSON.parse(text) as AdaptiveExecutionResult;
        } catch {
          return {
            content: [{ type: "text", text: `adaptive-execution returned invalid JSON: ${text}` }],
            details: {
              success: false,
              body: text,
            },
          };
        }

        return {
          content: [{ type: "text", text: summarizeResult(result) }],
          details: result,
        };
      },
    });
  },
});

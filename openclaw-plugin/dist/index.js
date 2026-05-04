import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
function resolveBaseUrl(config) {
    const configured = config?.baseUrl;
    if (typeof configured === "string" && configured.trim()) {
        return configured.trim().replace(/\/+$/, "");
    }
    return "http://127.0.0.1:8880";
}
function summarizeResult(result) {
    const attempts = Array.isArray(result.attempts) ? result.attempts : [];
    const statusSequence = Array.isArray(result.status_sequence) ? result.status_sequence.join(",") : "";
    return [
        `final_success: ${String(result.final_success)}`,
        `status_sequence: [${statusSequence}]`,
        `attempt_count: ${attempts.length}`,
    ].join("\n");
}
function isRecord(value) {
    return typeof value === "object" && value !== null;
}
function parseArguments(value) {
    if (typeof value !== "string") {
        return value;
    }
    try {
        return JSON.parse(value);
    }
    catch {
        return value;
    }
}
function extractRunParams(params) {
    if (!isRecord(params)) {
        return {};
    }
    const argumentsValue = parseArguments(params.arguments);
    if (isRecord(argumentsValue)) {
        return argumentsValue;
    }
    return params;
}
export default definePluginEntry({
    id: "adaptive-execution",
    name: "adaptive-execution",
    description: "Calls the adaptive-execution HTTP service as an OpenClaw tool.",
    register(api) {
        api.registerTool({
            name: "adaptive_execution_run",
            description: "Run adaptive-execution for an API objective and return compact deterministic retry results.",
            parameters: {
                type: "object",
                additionalProperties: false,
                required: ["endpoint_url", "method", "objective", "allow_network", "max_attempts"],
                properties: {
                    endpoint_url: {
                        type: "string",
                        description: "API endpoint URL to call.",
                    },
                    method: {
                        type: "string",
                        description: "HTTP method for the API request.",
                    },
                    objective: {
                        type: "string",
                        description: "Objective for adaptive-execution to solve.",
                    },
                    allow_network: {
                        type: "boolean",
                        description: "Whether sandbox execution may use network access.",
                    },
                    max_attempts: {
                        type: "integer",
                        minimum: 1,
                        description: "Maximum adaptive attempts.",
                    },
                },
            },
            async execute(_toolCallId, params) {
                const input = extractRunParams(params);
                const baseUrl = resolveBaseUrl(api.pluginConfig);
                const response = await fetch(`${baseUrl}/tools/adaptive_execution_run`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        endpoint_url: input.endpoint_url,
                        method: input.method,
                        objective: input.objective,
                        allow_network: input.allow_network,
                        max_attempts: input.max_attempts,
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
                let result;
                try {
                    result = JSON.parse(text);
                }
                catch {
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
        }, { name: "adaptive_execution_run" });
    },
});

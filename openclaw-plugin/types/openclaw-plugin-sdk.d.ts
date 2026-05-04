declare module "openclaw/plugin-sdk/plugin-entry" {
  type ToolDefinition = {
    name: string;
    description?: string;
    parameters?: unknown;
    execute: (toolCallId: string, params: unknown) => Promise<unknown> | unknown;
  };

  type PluginApi = {
    pluginConfig?: Record<string, unknown>;
    registerTool: (tool: ToolDefinition, options?: { name?: string }) => void;
  };

  type PluginEntry = {
    id: string;
    name: string;
    description?: string;
    register: (api: PluginApi) => void;
  };

  export function definePluginEntry(entry: PluginEntry): PluginEntry;
}

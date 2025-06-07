// src/mcp-client.ts

import { McpServerConfig, McpTool } from "./types";

/**
 * Port of mc_pygame_controller/mcp_client.py
 * A browser-compatible MCP client that communicates via HTTP/SSE.
 * It does not support stdio transport, which is unavailable in browsers.
 */
class Tool implements McpTool {
  name: string;
  description: string;
  inputSchema: any;

  constructor(name: string, description: string, inputSchema: any) {
    this.name = name;
    this.description = description;
    this.inputSchema = inputSchema;
  }

  toOpenAiSchema() {
    return {
      type: "function",
      function: {
        name: this.name,
        description: this.description,
        parameters: this.inputSchema,
      },
    };
  }
}

export class Server {
  public name: string;
  public config: McpServerConfig;
  public session: { initialized: boolean } | null = null;
  // In a real implementation, an EventSource would be stored here for SSE notifications.

  constructor(name: string, config: McpServerConfig) {
    this.name = name;
    this.config = config;
  }

  async initialize(): Promise<void> {
    try {
      // In browser, initialization might mean fetching server info or opening a connection.
      // We'll simulate this with a GET request to the server's root.
      const response = await fetch(this.config.url);
      if (!response.ok) {
        throw new Error(`Server at ${this.config.url} is not available.`);
      }
      const serverInfo = await response.json();
      console.log(`✅ Connected to MCP server: ${serverInfo.name} v${serverInfo.version}`);
      this.session = { initialized: true };
    } catch (e) {
      console.error(`Error initializing server ${this.name}:`, e);
      await this.cleanup();
      throw e;
    }
  }

  async listTools(): Promise<McpTool[]> {
    if (!this.session) throw new Error(`Server ${this.name} not initialized`);

    const response = await fetch(`${this.config.url}/tools`);
    if (!response.ok) throw new Error(`Failed to list tools from ${this.name}`);
    
    // The MCP spec returns a JSON array where the tool list is a tuple ["tools", [...]].
    const toolsResponse = await response.json();
    const toolList = toolsResponse.find((item: any) => Array.isArray(item) && item[0] === 'tools');

    if (!toolList) return [];

    return toolList[1].map((t: any) => new Tool(t.name, t.description, t.inputSchema));
  }
  
  async executeTool(toolName: string, args: any, retries: number = 2, delay: number = 1000): Promise<any> {
      if (!this.session) throw new Error(`Server ${this.name} not initialized`);

      let attempt = 0;
      while(attempt < retries) {
          try {
              console.log(`Executing ${toolName} with args:`, args);
              const response = await fetch(`${this.config.url}/tools/${toolName}/call`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify(args),
              });

              if (!response.ok) {
                  const errorBody = await response.text();
                  throw new Error(`Tool call failed with status ${response.status}: ${errorBody}`);
              }

              const result = await response.json();

              // MCP returns results in a specific format, e.g., ["ok", { content: [...] }]
              if (Array.isArray(result) && result[0] === 'ok') {
                return result[1]; // Return the payload
              } else if (Array.isArray(result) && result[0] === 'error') {
                throw new Error(result[1]?.message || "Unknown tool execution error");
              }
              return result; // Fallback for non-standard responses
          } catch(e) {
              attempt++;
              console.warn(`Error executing tool: ${e}. Attempt ${attempt} of ${retries}.`);
              if (attempt < retries) {
                  await new Promise(resolve => setTimeout(resolve, delay));
              } else {
                  console.error("Max retries reached. Failing.");
                  throw e;
              }
          }
      }
  }

  async cleanup(): Promise<void> {
    console.log(`Cleaning up server: ${this.name}`);
    // Close EventSource connection if it exists.
    this.session = null;
  }
}

// Port of mcp_client.py:create_tool_functions
export async function createToolFunctions(servers: Server[]): Promise<{ toolSchemas: any[], toolMapping: { [key: string]: Function } }> {
  const toolSchemas: any[] = [];
  const toolMapping: { [key: string]: Function } = {};

  for (const server of servers) {
    const tools = await server.listTools();
    for (const tool of tools) {
      toolSchemas.push(tool.toOpenAiSchema());
      
      toolMapping[tool.name] = async (args: any) => {
          try {
              const result = await server.executeTool(tool.name, args);
              // Handle CallToolResult properly
              if (result && result.content) {
                  if (Array.isArray(result.content) && result.content.length > 0) {
                      return {
                          content: result.content.map((item: any) => ({
                              type: item.type || 'text',
                              text: item.text,
                              data: item.data,
                              mimeType: item.mimeType,
                          }))
                      };
                  } else {
                      return String(result.content);
                  }
              }
              return String(result);
          } catch (e: any) {
              return `Error executing tool ${tool.name}: ${e.message}`;
          }
      };
    }
  }
  return { toolSchemas, toolMapping };
}

// src/types.ts

/**
 * Defines common types and interfaces used throughout the application.
 */

export interface Point {
  x: number;
  y: number;
}

export interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
}

export type Color = string;

// Port of mc_pygame_controller/conversation.py:Message
// Represents a single message in a conversation, compatible with OpenAI's format.
export interface Message {
  role: "system" | "user" | "assistant" | "tool";
  content: string | (string | { type: string; [key: string]: any })[] | null;
  tool_calls?: any[] | null;
  tool_call_id?: string | null;
  name?: string | null;
}

// Represents a tool that can be executed by the MCP server.
export interface McpTool {
  name: string;
  description: string;
  inputSchema: any;
  toOpenAiSchema: () => any;
}

// Represents the configuration for an MCP server connection.
// In the browser, we use a URL instead of a command.
export interface McpServerConfig {
  url: string; // Base URL for the MCP server, e.g., 'http://localhost:3000'
  name: string;
  [key: string]: any;
}

/**
 * @file mcp_client.ts
 * Manages configuration, MCP server connections, and tool execution.
 *
 * !!! IMPORTANT STUB IMPLEMENTATION !!!
 * This file provides a structural translation of the Python mcp_client.py.
 * The actual MCP (Minecraft Control Protocol) communication (`mcp` library in Python)
 * is NOT implemented here. This requires a dedicated TypeScript MCP library.
 * The `Server` class uses mock/stubbed versions of `ClientSession`,
 * `StdioServerParameters`, and `stdio_client` from the Python `mcp` library.
 * Therefore, this `Server` class will not be able to communicate with an
 * actual MCP server process. It's provided to allow porting of dependent classes
 * like `MinecraftControllerBase`.
 */

import * as fs from 'fs';
import * as path from 'path';
import * as dotenv from 'dotenv';
import { execSync } from 'child_process'; // For a shutil.which equivalent (platform-dependent)

// --- BEGIN MCP Library Stubs ---
// These are minimal stubs to allow Server class structure to be ported.
// A real implementation would require a TypeScript MCP library.

interface MockStdioTransport {
    read: (n: number) => Promise<Buffer | null>;
    write: (data: Buffer) => Promise<void>;
    close?: () => Promise<void>; // Optional: for cleanup
}

/**
 * Mock StdioServerParameters.
 */
class MockStdioServerParameters {
    constructor(
        public command: string,
        public args: string[],
        public env?: Record<string, string> | null
    ) {}
}

/**
 * Mock stdio_client function.
 * In a real scenario, this would establish and manage a stdio connection
 * to a server process.
 */
async function mockStdioClient(params: MockStdioServerParameters): Promise<MockStdioTransport> {
    console.warn(`[MCP STUB] mockStdioClient called for command: ${params.command} ${params.args.join(' ')}`);
    // This mock does not actually start a process or create pipes.
    // It returns a dummy transport object.
    return {
        read: async (n: number) => {
            console.warn("[MCP STUB] read called on mock transport");
            // Simulate end-of-stream or no data
            await new Promise(resolve => setTimeout(resolve, 100)); // Small delay
            return null;
        },
        write: async (data: Buffer) => {
            console.warn(`[MCP STUB] write called on mock transport with data: ${data.toString()}`);
        },
        close: async () => {
             console.warn("[MCP STUB] close called on mock transport");
        }
    };
}

/**
 * Mock ClientSession.
 */
class MockClientSession {
    private transport: MockStdioTransport;
    constructor(read: MockStdioTransport['read'], write: MockStdioTransport['write']) {
        // In a real client, read/write would be part of the transport passed in.
        // Here, we directly use the transport methods for simplicity of the stub.
        // This part of the stub might need adjustment based on how `stdio_client` actually provides the transport.
        // For this stub, we'll assume `stdio_client` gives us an object with read/write.
        // This part is tricky to stub without knowing the exact mcp library's internal structure.
        // Let's assume the transport itself has read/write.
        console.warn("[MCP STUB] MockClientSession created. This is a non-functional stub.");
    }

    async initialize(): Promise<void> {
        console.warn("[MCP STUB] session.initialize() called. No actual initialization.");
    }

    async list_tools(): Promise<[string, any[]][]> {
        console.warn("[MCP STUB] session.list_tools() called. Returning empty tools list.");
        return [['tools', []]]; // Mocked response structure
    }

    async call_tool(tool_name: string, arguments_json: any): Promise<any> {
        console.warn(`[MCP STUB] session.call_tool('${tool_name}') called with args:`, arguments_json, ". Returning mock success.");
        // Simulate a generic successful response structure
        return {
            type: "tool_result", // Or other relevant type
            tool_name: tool_name,
            result: {
                // Mock content; a real tool would have specific output
                content: [{ type: "text", text: `Mock success for ${tool_name}` }]
            }
        };
    }

    async close(): Promise<void> {
        console.warn("[MCP STUB] session.close() called.");
    }
}

/**
 * Mock AsyncExitStack.
 * A real AsyncExitStack manages multiple async context managers.
 * This stub simplifies it to manage a list of closeable resources.
 */
class MockAsyncExitStack {
    private resources: ({ close: () => Promise<void> } | { (): Promise<void> })[] = [];

    async enter_async_context<T extends { close?: () => Promise<void> }>(context_manager_result: T): Promise<T> {
        // A real implementation would call context_manager.__aenter__
        // This stub assumes the result itself might have a close method, or is a close function.
        if (typeof context_manager_result.close === 'function') {
            this.resources.push(context_manager_result as { close: () => Promise<void> });
        }
        return context_manager_result;
    }

    // Special handling if the context manager itself is the session (from ClientSession(read,write))
    async enter_client_session(session: MockClientSession): Promise<MockClientSession> {
        this.resources.push(session); // Add session to be closed
        return session;
    }


    async aclose(): Promise<void> {
        console.warn("[MCP STUB] AsyncExitStack.aclose() called.");
        for (let i = this.resources.length - 1; i >= 0; i--) {
            const resource = this.resources[i];
            try {
                if (typeof resource === 'function') {
                    await resource();
                } else if (resource && typeof resource.close === 'function') {
                    await resource.close();
                }
            } catch (e: any) {
                console.error(`[MCP STUB] Error closing resource in AsyncExitStack: ${e.message}`);
            }
        }
        this.resources = [];
    }
}

// --- END MCP Library Stubs ---

export class Configuration {
    public api_key: string | undefined;

    constructor() {
        this.load_env();
        this.api_key = process.env.OPENROUTER_API_KEY;
    }

    public static load_env(): void {
        dotenv.config();
    }

    public static load_config(file_path: string): Record<string, any> {
        if (!fs.existsSync(file_path)) {
            throw new Error(`Configuration file not found: ${file_path}`);
        }
        const fileContent = fs.readFileSync(file_path, 'utf-8');
        return JSON.parse(fileContent);
    }

    get llm_api_key(): string {
        if (!this.api_key) {
            throw new Error("OPENROUTER_API_KEY not found in environment variables");
        }
        return this.api_key;
    }
}

export class Tool {
    constructor(
        public name: string,
        public description: string,
        public input_schema: Record<string, any>
    ) {}

    to_openai_schema(): Record<string, any> {
        return {
            type: "function",
            function: {
                name: this.name,
                description: this.description,
                parameters: this.input_schema,
            },
        };
    }
}

export class Server {
    public name: string;
    public config: Record<string, any>;
    private session: MockClientSession | null = null;
    private exit_stack: MockAsyncExitStack = new MockAsyncExitStack();
    // private _cleanup_lock: asyncio.Lock; // Async locks are complex; simplify for stub

    constructor(name: string, config: Record<string, any>) {
        this.name = name;
        this.config = config;
        // this._cleanup_lock = new asyncio.Lock(); // In Node.js, use a library or Promise-based mutex
        console.warn(`[MCP STUB] Server "${name}" created. This server is non-functional due to MCP library stubs.`);
    }

    private _which(command: string): string | null {
        // Basic polyfill for shutil.which, platform dependent
        // For 'npx', it's often in PATH. For other commands, full path might be needed.
        if (command === "npx") { // npx should generally be in path for Node environments
             try {
                // Check if npx is available
                execSync('npx --version', { stdio: 'ignore' });
                return 'npx';
            } catch (e) {
                console.error("npx command not found. Please ensure Node.js and npm are installed and in your PATH.");
                return null;
            }
        }
        // For other commands, this is a very simplified check
        // A more robust solution might involve checking common bin paths or using a library
        try {
            const GCR = global['process'].env.PATH.split(global['process'].platform === 'win32' ? ';' : ':').find(p => fs.existsSync(path.join(p, command)));
            if (GCR) return path.join(GCR, command);
            if (fs.existsSync(command)) return command; // if it's already a full path
        } catch (e) { /* ignore */ }
        return null;
    }


    async initialize(): Promise<void> {
        console.warn(`[MCP STUB] Server "${this.name}": initialize() called.`);
        const commandPath = this.config["command"] === "npx" ? this._which("npx") : this._which(this.config["command"]);

        if (!commandPath) {
            throw new Error(`Command not found: ${this.config["command"]}`);
        }

        const server_params = new MockStdioServerParameters(
            commandPath,
            this.config["args"],
            this.config["env"] ? { ...process.env, ...this.config["env"] } : process.env
        );

        try {
            // stdio_client returns a transport; ClientSession takes read/write parts of it.
            // This part is highly dependent on the actual mcp library's API.
            // The Python code uses `await self.exit_stack.enter_async_context(stdio_client(server_params))`
            // then `await self.exit_stack.enter_async_context(ClientSession(read, write))`

            const stdio_transport = await mockStdioClient(server_params);
            await this.exit_stack.enter_async_context(stdio_transport); // Manage transport lifetime

            // How read/write are extracted from stdio_transport depends on the mcp library.
            // Assuming stdio_transport directly provides them for the stub.
            const session = new MockClientSession(stdio_transport.read, stdio_transport.write);
            await this.exit_stack.enter_client_session(session); // Manage session lifetime

            await session.initialize();
            this.session = session;
            console.warn(`[MCP STUB] Server "${this.name}": Session supposedly initialized.`);
        } catch (e: any) {
            console.error(`[MCP STUB] Error initializing server ${this.name}: ${e.message}`);
            await this.cleanup();
            throw e;
        }
    }

    async list_tools(): Promise<Tool[]> {
        if (!this.session) {
            throw new Error(`[MCP STUB] Server ${this.name} not initialized`);
        }
        console.warn(`[MCP STUB] Server "${this.name}": list_tools() called.`);
        const tools_response = await this.session.list_tools(); // Returns mock data
        const tools: Tool[] = [];
        for (const item of tools_response) {
            if (Array.isArray(item) && item[0] === "tools") {
                tools.push(...item[1].map((t: any) => new Tool(t.name, t.description, t.inputSchema)));
            }
        }
        return tools;
    }

    async execute_tool(
        tool_name: string,
        args: Record<string, any>,
        retries: number = 2,
        delay: number = 1.0
    ): Promise<any> {
        if (!this.session) {
            throw new Error(`[MCP STUB] Server ${this.name} not initialized`);
        }
        console.warn(`[MCP STUB] Server "${this.name}": execute_tool('${tool_name}') called.`);

        let attempt = 0;
        while (attempt < retries) {
            try {
                // Arguments should be passed as a JSON object (string in some MCP versions, object in others)
                // The Python mcp library handles this. Here, we assume the stub takes an object.
                const result = await this.session.call_tool(tool_name, args);
                return result; // Returns mock success
            } catch (e: any) {
                attempt++;
                console.warn(`[MCP STUB] Error executing tool: ${e.message}. Attempt ${attempt} of ${retries}.`);
                if (attempt < retries) {
                    console.log(`[MCP STUB] Retrying in ${delay} seconds...`);
                    await new Promise(resolve => setTimeout(resolve, delay * 1000));
                } else {
                    console.error("[MCP STUB] Max retries reached. Failing.");
                    throw e;
                }
            }
        }
    }

    async cleanup(): Promise<void> {
        // Simplified cleanup without async lock for stub
        console.warn(`[MCP STUB] Server "${this.name}": cleanup() called.`);
        try {
            if (this.session) {
                await new Promise(resolve => setTimeout(resolve, 100)); // Brief delay
            }
            await this.exit_stack.aclose();
            this.session = null;
        } catch (e: any) {
            console.error(`[MCP STUB] Error during cleanup of server ${this.name}: ${e.message}`);
        }
    }
}

/**
 * Creates tool functions callable from a chain, based on tools listed by servers.
 * @param servers - A list of initialized Server instances.
 * @returns A tuple containing a list of OpenAI-compatible tool schemas and a mapping of tool names to callable functions.
 */
export async function create_tool_functions(servers: Server[]): Promise<[Record<string, any>[], Record<string, (...args: any[]) => Promise<any>>]> {
    const tool_schemas: Record<string, any>[] = [];
    const tool_mapping: Record<string, (...args: any[]) => Promise<any>> = {};

    for (const server of servers) {
        try {
            const tools = await server.list_tools(); // This will use the stubbed list_tools
            for (const tool of tools) {
                tool_schemas.push(tool.to_openai_schema());

                // Create an async function that calls server.execute_tool
                // This structure matches the Python version.
                const make_tool_function = (srv: Server, tl: Tool) => {
                    return async (kwargs: Record<string, any>): Promise<any> => { // Changed from ...args to kwargs object
                        try {
                            const result = await srv.execute_tool(tl.name, kwargs);
                            // Process result (stubbed version will just return mock success)
                             if (result && result.content && Array.isArray(result.content)) {
                                return {
                                    content: result.content.map((item: any) => ({
                                        type: item.type || "text",
                                        text: item.text || null,
                                        data: item.data || null,
                                        mimeType: item.mimeType || null,
                                    }))
                                };
                            }
                            return result ? String(result) : "No result";
                        } catch (e: any) {
                            console.error(`[MCP STUB] Error in tool_function for ${tl.name}: ${e.message}`);
                            return `Error executing tool ${tl.name}: ${e.message}`;
                        }
                    };
                };
                tool_mapping[tool.name] = make_tool_function(server, tool);
            }
        } catch (error: any) {
            console.error(`[MCP STUB] Failed to list tools for server ${server.name}: ${error.message}`);
            // Continue to process other servers if one fails
        }
    }
    return [tool_schemas, tool_mapping];
}

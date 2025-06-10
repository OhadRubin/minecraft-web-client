/**
 * @file conversation.ts
 * Manages conversation messages, captures actions for human demonstrations,
 * and can generate mock API responses.
 */

import { strict as assert } from 'assert'; // For potential assertions if needed

/**
 * Represents a message in the conversation.
 * Based on the Python dataclass.
 */
export interface Message {
    role: string;
    content?: string | Array<Record<string, string>> | null;
    tool_calls?: Array<any> | null; // Define more specific type for tool_calls if known
    tool_call_id?: string | null;
    name?: string | null;
    should_cache?: boolean; // Defaulted to false in Python, TS handles default in constructor/init
}

// --- Mock Response Types (local to ConversationPanel or can be moved out if widely used) ---
interface MockFunction {
    name: string;
    arguments: string; // JSON string
}

interface MockToolCall {
    id: string;
    type: "function";
    function: MockFunction;
}

interface MockMessageData {
    content: string | null;
    tool_calls: MockToolCall[] | null;
}

interface MockChoice {
    message: MockMessageData;
}

interface MockUsage {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
}

interface MockResponse {
    choices: MockChoice[];
    usage: MockUsage;
}
// --- End Mock Response Types ---


/**
 * Manages conversation messages for display and human demonstrations.
 * In the original Python, this class seemed to be a simple wrapper with formatting.
 * This TypeScript version maintains that structure.
 */
export class ConversationPanel {
    public messages: Message[];
    public captured_actions: any[]; // Array of MCP commands
    public human_demo_mode: boolean;

    constructor() {
        this.messages = [];
        this.captured_actions = [];
        this.human_demo_mode = true; // Default as per Python __init__
    }

    /**
     * Captures an MCP command.
     * @param mcp_command - The MCP command object (e.g., `{ tool: "walk", parameters: { duration: 1000 } }`).
     */
    public capture_mcp_action(mcp_command: { tool: string; parameters: Record<string, any> }): void {
        this.captured_actions.push(mcp_command);
        console.log(
            `📝 Captured action: ${mcp_command.tool}(${JSON.stringify(mcp_command.parameters)})`
        );
    }

    /**
     * Converts captured actions into a mock OpenAI-style response structure.
     * This is used when `human_demo_mode` is true.
     * @returns A  message data object with content and tool_calls.
     */
    public convert_actions_to_mock_response(): { content: string | null; tool_calls: MockToolCall[] | null } {
        if (this.captured_actions.length === 0) {
            return {
                content: "I'll explore and take some actions in Minecraft.",
                tool_calls: null,
            };
        }

        const action_descriptions: string[] = [];
        const tool_calls: MockToolCall[] = [];

        this.captured_actions.forEach((action, i) => {
            const tool_name = action.tool as string;
            const params = action.parameters as Record<string, any>;
            const tool_call_id = `call_${i}_${tool_name}`;

            tool_calls.push({
                id: tool_call_id,
                type: "function",
                function: { name: tool_name, arguments: JSON.stringify(params) },
            });

            switch (tool_name) {
                case "lookAngle":
                    action_descriptions.push(`look around (x: ${params.xAngle || 0}°, y: ${params.yAngle || 0}°)`);
                    break;
                case "walk":
                    action_descriptions.push(`move forward for ${params.duration || 1000}ms`);
                    break;
                case "leftClick":
                    action_descriptions.push("break/attack with left click");
                    break;
                case "rightClick":
                    action_descriptions.push("place/use with right click");
                    break;
                case "setHotbarSlot":
                    action_descriptions.push(`select hotbar slot ${ (params.slot || 0) + 1}`);
                    break;
                default:
                    action_descriptions.push(`use ${tool_name}`);
            }
        });

        let content: string;
        if (action_descriptions.length === 1) {
            content = `I'll ${action_descriptions[0]} to explore the area.`;
        } else {
            const last_action = action_descriptions.pop();
            content = `I'll ${action_descriptions.join(', ')} and ${last_action} to navigate and explore.`;
        }

        this.captured_actions = []; // Clear actions after converting
        return { content, tool_calls: tool_calls.length > 0 ? tool_calls : null };
    }

    /**
     * Renders messages into a mock API response.
     * In the original Python, this method was async but didn't perform any actual async operations
     * when `human_demo_mode` was true. It constructed a mock response.
     * @param _api_params - Optional API parameters (not used in mock generation).
     * @returns A Promise resolving to a mock response object.
     */
    public async _render_messages(_api_params?: any): Promise<MockResponse> {
        if (this.messages.length > 0) {
            console.log(`📄 Conversation has ${this.messages.length} messages`);
        }

        let message_data: { content: string | null; tool_calls: MockToolCall[] | null };

        if (this.human_demo_mode) {
            message_data = this.convert_actions_to_mock_response();
        } else {
            message_data = {
                content: "MCP/Pygame mode - no OpenAI call made",
                tool_calls: null,
            };
        }

        // Constructing the mock response structure inline
        const mockMessage: MockMessageData = {
            content: message_data.content,
            tool_calls: message_data.tool_calls ? message_data.tool_calls.map(tc => ({
                id: tc.id,
                type: tc.type,
                function: {
                    name: tc.function.name,
                    arguments: tc.function.arguments,
                },
            })) : null,
        };

        const mockChoice: MockChoice = { message: mockMessage };
        const mockUsage: MockUsage = { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 };

        return {
            choices: [mockChoice],
            usage: mockUsage,
        };
    }
}

/**
 * Creates a user message string from a list of captured actions.
 * @param captured_actions - An array of MCP command objects.
 * @returns A string describing the actions performed.
 */
export function create_user_message(captured_actions: any[]): string {
    if (!captured_actions || captured_actions.length === 0) {
        return "I performed no specific actions.";
    }
    const action_descriptions: string[] = [];
    for (const action of captured_actions) {
        const tool_name = action.tool as string;
        const params = action.parameters as Record<string, any>;
        if (tool_name === "lookAngle") {
            const x_angle = (params.xAngle || 0) as number;
            const y_angle = (params.yAngle || 0) as number;
            action_descriptions.push(
                `look ${x_angle.toFixed(1)}° horizontally, ${y_angle.toFixed(1)}° vertically`
            );
        } else {
            action_descriptions.push(`use ${tool_name}`);
        }
    }
    return `I performed these actions: ${action_descriptions.join(', ')}`;
}

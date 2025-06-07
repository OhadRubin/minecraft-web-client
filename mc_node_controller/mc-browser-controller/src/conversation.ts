// src/conversation.ts
import { Message } from './types';

/**
 * Port of mc_pygame_controller/conversation.py
 * Manages the conversation state and converts human actions into mock LLM responses
 * for creating demonstration data.
 */

// A helper to create a mock OpenAI-like tool call structure
function createMockToolCall(id: string, name: string, args: any) {
    return {
        id,
        type: 'function',
        function: {
            name,
            arguments: JSON.stringify(args)
        }
    };
}
 
// A helper to create a mock response object
function createMockResponse(content: string | null, tool_calls: any[] | null) {
    return {
        choices: [{
            message: {
                content,
                tool_calls,
                // Simulate the structure of an OpenAI message object
                ...(!tool_calls ? {} : {
                    tool_calls: tool_calls.map(tc => ({
                        ...tc,
                        function: {
                            ...tc.function,
                            arguments: tc.function.arguments, // Already a string
                        }
                    }))
                })
            }
        }],
        usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 }
    };
}


export class ConversationPanel {
    messages: Message[] = [];
    capturedActions: { tool: string; parameters: any }[] = [];
    humanDemoMode: boolean = true;

    captureMcpAction(mcpCommand: { tool: string; parameters: any }) {
        this.capturedActions.push(mcpCommand);
        console.log(`📝 Captured action: ${mcpCommand.tool}(${JSON.stringify(mcpCommand.parameters)})`);
    }

    convertActionsToMockResponse() {
        if (this.capturedActions.length === 0) {
            return {
                content: "I'll explore and take some actions in Minecraft.",
                tool_calls: null
            };
        }

        const actionDescriptions: string[] = [];
        const tool_calls: any[] = [];
        this.capturedActions.forEach((action, i) => {
            const tool_name = action.tool;
            const params = action.parameters;
            tool_calls.push(createMockToolCall(`call_${i}_${tool_name}`, tool_name, params));

            switch (tool_name) {
                case "lookAngle":
                    actionDescriptions.push(`look around (x: ${params.xAngle}°, y: ${params.yAngle}°)`);
                    break;
                case "walk":
                    actionDescriptions.push(`move forward for ${params.duration}ms`);
                    break;
                case "leftClick":
                    actionDescriptions.push("break/attack with left click");
                    break;
                case "rightClick":
                    actionDescriptions.push("place/use with right click");
                    break;
                case "setHotbarSlot":
                    actionDescriptions.push(`select hotbar slot ${params.slot + 1}`);
                    break;
                default:
                    actionDescriptions.push(`use ${tool_name}`);
            }
        });

        let content = "I'll perform some actions.";
        if (actionDescriptions.length === 1) {
            content = `I'll ${actionDescriptions[0]} to explore the area.`;
        } else if (actionDescriptions.length > 1) {
            const allButLast = actionDescriptions.slice(0, -1).join(', ');
            content = `I'll ${allButLast} and ${actionDescriptions[actionDescriptions.length - 1]} to navigate and explore.`;
        }
        
        this.capturedActions = []; // Clear after conversion
        return { content, tool_calls };
    }

    /**
     * This is the core of the human demonstration system. Instead of calling a real LLM,
     * it converts captured human actions into a mock LLM response with tool calls.
     */
    async renderMessages(apiParams: any) {
        if (this.messages) {
            console.log(`📄 Conversation has ${this.messages.length} messages`);
        }
        
        if (this.humanDemoMode) {
            const { content, tool_calls } = this.convertActionsToMockResponse();
            return createMockResponse(content, tool_calls);
        } else {
            // Fallback for non-demo mode (not used in this port)
            return createMockResponse("MCP/Browser mode - no OpenAI call made", null);
        }
    }
}

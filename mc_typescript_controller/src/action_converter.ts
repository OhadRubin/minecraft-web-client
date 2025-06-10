/**
 * @file action_converter.ts
 * Provides a centralized converter for Pygame-like actions to MCP (Minecraft Control Protocol) format.
 * This eliminates duplicated business logic and ensures consistent conversion.
 */

import { Console } from "console";

// Define more specific types if the structure of actions and parameters is known
type PygameAction = Record<string, any>;
type McpAction = { tool: string; parameters: Record<string, any> };
type OpenAiToolCall = {
    id: string;
    type: "function";
    function: {
        name: string;
        arguments: string; // JSON string
    };
};

/**
 * Centralized converter for Pygame-like actions to MCP format.
 */
export class ActionConverter {
    // Shared constants
    public static readonly MOVEMENT_THRESHOLD = 0.1;
    public static readonly LOOK_THRESHOLD = 0.2;
    public static readonly SENSITIVITY = 5.0;
    public static readonly MAGNITUDE_DURATION_SCALE = 2000;

    /**
     * Converts a single Pygame-like action to a normalized MCP data structure.
     * @param action - The Pygame action object (e.g., `{ type: "move", x: 0.5, z: 0.3 }`).
     * @returns An MCP action object or `null` if no conversion is applicable.
     */
    public static convert_pygame_action(action: PygameAction): McpAction | null {
        if (typeof action !== 'object' || action === null) {
            return null;
        }

        const actionType = action["type"] as string;

        switch (actionType) {
            case "move":
                return ActionConverter._convert_move_action(action);
            case "look":
                return ActionConverter._convert_look_action(action);
            case "documentMouseEvent":
                // Only convert mouse down events for left click, skip mouse up
                if (action["button"] === 0 && action["action"] === "down") {
                    return ActionConverter._convert_left_click_action(action);
                }
                return null;
            case "rightDown":
                return ActionConverter._convert_right_click_action(action);
            default:
                return null;
        }
    }

    private static _convert_move_action(action: PygameAction): McpAction | null {
        const x = (action["x"] as number) || 0;
        const z = (action["z"] as number) || 0;

        if (Math.abs(x) > ActionConverter.MOVEMENT_THRESHOLD || Math.abs(z) > ActionConverter.MOVEMENT_THRESHOLD) {
            const magnitude = Math.sqrt(x ** 2 + z ** 2);
            const duration = Math.round(magnitude * ActionConverter.MAGNITUDE_DURATION_SCALE);
            return { tool: "walk", parameters: { duration } };
        }
        return null;
    }

    private static _convert_look_action(action: PygameAction): McpAction | null {
        const movementX = (action["movementX"] as number) || 0;
        const movementY = (action["movementY"] as number) || 0;

        const xAngle = movementX / ActionConverter.SENSITIVITY;
        const yAngle = -(movementY / ActionConverter.SENSITIVITY); // Invert Y axis

        if (Math.abs(xAngle) > ActionConverter.LOOK_THRESHOLD || Math.abs(yAngle) > ActionConverter.LOOK_THRESHOLD) {
            return {
                tool: "lookAngle",
                parameters: {
                    xAngle: parseFloat(xAngle.toFixed(1)),
                    yAngle: parseFloat(yAngle.toFixed(1)),
                    speed: "normal",
                },
            };
        }
        return null;
    }

    private static _convert_left_click_action(action: PygameAction): McpAction {
        return { tool: "leftClick", parameters: { duration: "short" } };
    }

    private static _convert_right_click_action(action: PygameAction): McpAction {
        return { tool: "rightClick", parameters: { duration: "short" } };
    }

    /**
     * Converts multiple Pygame-like actions to MCP format.
     * @param actions - A list of Pygame actions (either objects or strings for legacy compatibility).
     * @returns A list of converted MCP actions, excluding any null results.
     */
    public static convert_pygame_actions_bulk(actions: any[]): McpAction[] {
        const mcpActions: McpAction[] = [];

        for (const action of actions) {
            let converted: McpAction | null = null;
            if (typeof action === 'object' && action !== null) {
                converted = ActionConverter.convert_pygame_action(action as PygameAction);
            } else if (typeof action === 'string') {
                converted = ActionConverter._convert_string_action(action);
            }

            if (converted) {
                mcpActions.push(converted);
            }
        }
        return mcpActions;
    }

    private static _convert_string_action(actionStr: string): McpAction | null {
        try {
            if (actionStr.includes('"move":')) {
                return { tool: "walk", parameters: { duration: 1000 } }; // Default for legacy
            } else if (actionStr.includes('"look":')) {
                const actionData = JSON.parse(actionStr);
                if (actionData["look"]) {
                    const lookData = actionData["look"];
                    const dictAction: PygameAction = {
                        type: "look",
                        movementX: lookData["movementX"] || 0,
                        movementY: lookData["movementY"] || 0,
                    };
                    return ActionConverter.convert_pygame_action(dictAction);
                }
            }
        } catch (e) {
            console.warn(`⚠️ Could not parse legacy action: ${actionStr} - ${e}`);
        }
        return null;
    }

    // Format Adapters

    /**
     * Returns the conversions in a simple array format.
     * This is the default format from `convert_pygame_actions_bulk`.
     * @param conversions - List of MCP actions.
     * @returns The same list of MCP actions.
     */
    public static to_simple_format(conversions: McpAction[]): McpAction[] {
        return conversions;
    }

    /**
     * Converts MCP actions to the OpenAI tool call format.
     * @param conversions - List of MCP actions.
     * @param sequence_id - A unique identifier for this sequence of tool calls.
     * @returns A list of actions formatted as OpenAI tool calls.
     */
    public static to_openai_format(conversions: McpAction[], sequence_id: string): OpenAiToolCall[] {
        const tool_calls: OpenAiToolCall[] = [];
        conversions.forEach((conversion, i) => {
            if (conversion) {
                tool_calls.push({
                    id: `call_${sequence_id}_${conversion.tool}_${i}`,
                    type: "function",
                    function: {
                        name: conversion.tool,
                        arguments: JSON.stringify(conversion.parameters),
                    },
                });
            }
        });
        return tool_calls;
    }

    // Convenience methods

    /**
     * Convenience method for converting Pygame actions to simple MCP format.
     * @param actions - List of Pygame actions.
     * @returns List of MCP actions.
     */
    public static pygame_to_mcp_simple(actions: any[]): McpAction[] {
        const conversions = ActionConverter.convert_pygame_actions_bulk(actions);
        return ActionConverter.to_simple_format(conversions);
    }

    /**
     * Convenience method for converting Pygame actions to OpenAI tool call format.
     * @param actions - List of Pygame actions.
     * @param sequence_id - Sequence identifier.
     * @returns List of OpenAI tool calls.
     */
    public static pygame_to_openai_tools(actions: any[], sequence_id: string): OpenAiToolCall[] {
        const conversions = ActionConverter.convert_pygame_actions_bulk(actions);
        return ActionConverter.to_openai_format(conversions, sequence_id);
    }
}

/**
 * Converts specific command types and parameters to MCP format.
 * This function handles a predefined set of commands.
 * @param command_type - The type of command (e.g., "left_click", "walk").
 * @param params - Parameters for the command.
 * @returns An MCP action object or `null` if the command type is not recognized.
 */
export function convert_to_mcp_format(command_type: string, params: Record<string, any>): McpAction | null {
    switch (command_type) {
        case "left_click":
        case "leftClick":
            return {
                tool: "leftClick",
                parameters: { duration: params["duration"] || "medium" },
            };
        case "right_click":
        case "rightClick":
            return {
                tool: "rightClick",
                parameters: { duration: params["duration"] || "medium" },
            };
        case "walk":
            return {
                tool: "walk",
                parameters: { duration: params["duration"] || 1000 },
            };
        case "setHotbarSlot":
            return {
                tool: "setHotbarSlot",
                parameters: { slot: params["slot"] || 0 },
            };
        case "jump":
            return {
                tool: "jump",
                parameters: { duration: params["duration"] || "short" },
            };
        case "sneak":
            return {
                tool: "sneak",
                parameters: { state: params["state"] !== undefined ? params["state"] : true },
            };
        case "sprint":
            return {
                tool: "sprint",
                parameters: { state: params["state"] !== undefined ? params["state"] : true },
            };
        case "toggleInventory":
            return {
                tool: "toggleInventory",
                parameters: {},
            };
        case "dropItem":
            return {
                tool: "dropItem",
                parameters: { amount: params["amount"] || 1 },
            };
        case "swapHands":
            return {
                tool: "swapHands",
                parameters: {},
            };
        default:
            return null;
    }
}

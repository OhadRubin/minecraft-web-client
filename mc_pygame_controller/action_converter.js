// === START_OF: action_converter.py
// =======================================================================

class ActionConverter {
    // Shared constants - single source of truth
    static MOVEMENT_THRESHOLD = 0.1;
    static LOOK_THRESHOLD = 0.2;
    static SENSITIVITY = 5.0;
    static MAGNITUDE_DURATION_SCALE = 2000;

    static convert_pygame_action(action) {
        if (typeof action !== 'object' || action === null) {
            return null;
        }

        const actionType = action.type;

        if (actionType === "move") {
            return ActionConverter._convert_move_action(action);
        } else if (actionType === "look") {
            return ActionConverter._convert_look_action(action);
        } else if (actionType === "documentMouseEvent" && action.button === 0) {
            if (action.action === "down") {
                return ActionConverter._convert_left_click_action(action);
            }
            return null;
        } else if (actionType === "rightDown") {
            return ActionConverter._convert_right_click_action(action);
        }

        return null;
    }

    static _convert_move_action(action) {
        const x = action.x ?? 0;
        const z = action.z ?? 0;

        if (Math.abs(x) > ActionConverter.MOVEMENT_THRESHOLD || Math.abs(z) > ActionConverter.MOVEMENT_THRESHOLD) {
            const magnitude = Math.sqrt(x ** 2 + z ** 2);
            const duration = Math.floor(magnitude * ActionConverter.MAGNITUDE_DURATION_SCALE);
            return { tool: "walk", parameters: { duration } };
        }
        return null;
    }

    static _convert_look_action(action) {
        const movementX = action.movementX ?? 0;
        const movementY = action.movementY ?? 0;

        const xAngle = movementX / ActionConverter.SENSITIVITY;
        const yAngle = -(movementY / ActionConverter.SENSITIVITY); // Invert Y axis

        if (Math.abs(xAngle) > ActionConverter.LOOK_THRESHOLD || Math.abs(yAngle) > ActionConverter.LOOK_THRESHOLD) {
            return {
                tool: "lookAngle",
                parameters: {
                    xAngle: Math.round(xAngle * 10) / 10,
                    yAngle: Math.round(yAngle * 10) / 10,
                    speed: "normal",
                },
            };
        }
        return null;
    }

    static _convert_left_click_action(action) {
        return { tool: "leftClick", parameters: { duration: "short" } };
    }

    static _convert_right_click_action(action) {
        return { tool: "rightClick", parameters: { duration: "short" } };
    }

    static convert_pygame_actions_bulk(actions) {
        const mcp_actions = [];
        for (const action of actions) {
            if (typeof action === 'object' && action !== null) {
                const converted = ActionConverter.convert_pygame_action(action);
                if (converted) {
                    mcp_actions.push(converted);
                }
            } else if (typeof action === 'string') {
                const converted = ActionConverter._convert_string_action(action);
                if (converted) {
                    mcp_actions.push(converted);
                }
            }
        }
        return mcp_actions;
    }

    static _convert_string_action(action_str) {
        try {
            if (action_str.includes('"move":')) {
                return { tool: "walk", parameters: { duration: 1000 } };
            } else if (action_str.includes('"look":')) {
                const action_data = JSON.parse(action_str);
                if ("look" in action_data) {
                    const look_data = action_data.look;
                    const dict_action = {
                        type: "look",
                        movementX: look_data.movementX ?? 0,
                        movementY: look_data.movementY ?? 0,
                    };
                    return ActionConverter.convert_pygame_action(dict_action);
                }
            }
        } catch (e) {
            console.warn(`⚠️ Could not parse legacy action: ${action_str} - ${e}`);
        }
        return null;
    }

    static to_simple_format(conversions) {
        return conversions; // Already in the correct format
    }

    static to_openai_format(conversions, sequence_id) {
        const tool_calls = [];
        for (let i = 0; i < conversions.length; i++) {
            const conversion = conversions[i];
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
        }
        return tool_calls;
    }

    static pygame_to_mcp_simple(actions) {
        const conversions = ActionConverter.convert_pygame_actions_bulk(actions);
        return ActionConverter.to_simple_format(conversions);
    }

    static pygame_to_openai_tools(actions, sequence_id) {
        const conversions = ActionConverter.convert_pygame_actions_bulk(actions);
        return ActionConverter.to_openai_format(conversions, sequence_id);
    }
}

// This function seems separate from the class, so we port it as a standalone function.
function convert_to_mcp_format(command_type, params) {
    switch (command_type) {
        case "left_click":
        case "leftClick":
            return { tool: "leftClick", parameters: { duration: params.duration ?? "medium" } };
        case "right_click":
        case "rightClick":
            return { tool: "rightClick", parameters: { duration: params.duration ?? "medium" } };
        case "walk":
            return { tool: "walk", parameters: { duration: params.duration ?? 1000 } };
        case "setHotbarSlot":
            return { tool: "setHotbarSlot", parameters: { slot: params.slot ?? 0 } };
        case "jump":
            return { tool: "jump", parameters: { duration: params.duration ?? "short" } };
        case "sneak":
            return { tool: "sneak", parameters: { state: params.state ?? true } };
        case "sprint":
            return { tool: "sprint", parameters: { state: params.state ?? true } };
        case "toggleInventory":
            return { tool: "toggleInventory", parameters: {} };
        case "dropItem":
            return { tool: "dropItem", parameters: { amount: params.amount ?? 1 } };
        case "swapHands":
            return { tool: "swapHands", parameters: {} };
        default:
            return null;
    }
}

// =======================================================================
export { ActionConverter, convert_to_mcp_format };
// === END_OF: action_converter.py

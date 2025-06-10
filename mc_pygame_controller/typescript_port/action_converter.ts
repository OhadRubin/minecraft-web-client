// TypeScript interfaces for Pygame actions
interface PygameBaseAction {
  type: string;
  [key: string]: any; // Allow other properties
}

interface PygameMoveAction extends PygameBaseAction {
  type: "move";
  x?: number;
  z?: number;
}

interface PygameLookAction extends PygameBaseAction {
  type: "look";
  movementX?: number;
  movementY?: number;
}

interface PygameMouseAction extends PygameBaseAction {
  type: "documentMouseEvent";
  button: number; // 0 for left, 1 for middle, 2 for right (typically)
  action: "down" | "up";
}

interface PygameRightDownAction extends PygameBaseAction {
  type: "rightDown";
}

// Union type for all specific Pygame actions used by ActionConverter
type PygameAction = PygameMoveAction | PygameLookAction | PygameMouseAction | PygameRightDownAction | PygameBaseAction; // PygameBaseAction for fallback

// TypeScript interfaces for MCP (Minecraft Protocol) actions
interface McpParameters {
  [key: string]: string | number | boolean;
}

interface McpWalkParams extends McpParameters {
  duration: number;
}

interface McpLookAngleParams extends McpParameters {
  xAngle: number;
  yAngle: number;
  speed: string;
}

interface McpClickParams extends McpParameters {
  duration: string; // "short", "medium", etc.
}

interface McpSetHotbarSlotParams extends McpParameters {
    slot: number;
}

interface McpJumpParams extends McpParameters {
    duration: string;
}

interface McpSneakParams extends McpParameters {
    state: boolean;
}

interface McpSprintParams extends McpParameters {
    state: boolean;
}

interface McpDropItemParams extends McpParameters {
    amount: number;
}

interface McpToggleInventoryParams extends McpParameters {}
interface McpSwapHandsParams extends McpParameters {}


interface McpAction {
  tool: string;
  parameters: McpParameters;
}

interface McpWalkAction extends McpAction {
  tool: "walk";
  parameters: McpWalkParams;
}

interface McpLookAngleAction extends McpAction {
  tool: "lookAngle";
  parameters: McpLookAngleParams;
}

interface McpLeftClickAction extends McpAction {
  tool: "leftClick";
  parameters: McpClickParams;
}

interface McpRightClickAction extends McpAction {
  tool: "rightClick";
  parameters: McpClickParams;
}

interface McpSetHotbarSlotAction extends McpAction {
    tool: "setHotbarSlot";
    parameters: McpSetHotbarSlotParams;
}

interface McpJumpAction extends McpAction {
    tool: "jump";
    parameters: McpJumpParams;
}
interface McpSneakAction extends McpAction {
    tool: "sneak";
    parameters: McpSneakParams;
}
interface McpSprintAction extends McpAction {
    tool: "sprint";
    parameters: McpSprintParams;
}

interface McpToggleInventoryAction extends McpAction {
    tool: "toggleInventory";
    parameters: McpToggleInventoryParams;
}

interface McpDropItemAction extends McpAction {
    tool: "dropItem";
    parameters: McpDropItemParams;
}
interface McpSwapHandsAction extends McpAction {
    tool: "swapHands";
    parameters: McpSwapHandsParams;
}


// Union type for specific McpActions known to ActionConverter and convert_to_mcp_format
type KnownMcpAction =
  | McpWalkAction
  | McpLookAngleAction
  | McpLeftClickAction
  | McpRightClickAction
  | McpSetHotbarSlotAction
  | McpJumpAction
  | McpSneakAction
  | McpSprintAction
  | McpToggleInventoryAction
  | McpDropItemAction
  | McpSwapHandsAction;


// Interface for OpenAI tool call format
interface OpenAiFunction {
  name: string;
  arguments: string; // JSON string of parameters
}

interface OpenAiToolCall {
  id: string;
  type: "function";
  function: OpenAiFunction;
}

// Type for actions list input (can be objects or strings for legacy)
type InputPygameAction = PygameAction | Record<string, any> | string;


class ActionConverter {
  // Shared constants - single source of truth
  static readonly MOVEMENT_THRESHOLD: number = 0.1;
  static readonly LOOK_THRESHOLD: number = 0.2;
  static readonly SENSITIVITY: number = 5.0;
  static readonly MAGNITUDE_DURATION_SCALE: number = 2000;

  static convert_pygame_action(action: InputPygameAction): KnownMcpAction | null {
    if (typeof action !== 'object' || action === null || typeof (action as PygameBaseAction).type !== 'string') {
      return null;
    }
    const pygameAction = action as PygameBaseAction; // More specific types handled in cases

    switch (pygameAction.type) {
      case "move":
        return ActionConverter._convert_move_action(pygameAction as PygameMoveAction);
      case "look":
        return ActionConverter._convert_look_action(pygameAction as PygameLookAction);
      case "documentMouseEvent":
        const mouseEvent = pygameAction as PygameMouseAction;
        if (mouseEvent.button === 0 && mouseEvent.action === "down") {
          return ActionConverter._convert_left_click_action(mouseEvent);
        }
        return null;
      case "rightDown":
        return ActionConverter._convert_right_click_action(pygameAction as PygameRightDownAction);
      default:
        return null;
    }
  }

  private static _convert_move_action(action: PygameMoveAction): McpWalkAction | null {
    const x = action.x || 0;
    const z = action.z || 0;

    if (
      Math.abs(x) > ActionConverter.MOVEMENT_THRESHOLD ||
      Math.abs(z) > ActionConverter.MOVEMENT_THRESHOLD
    ) {
      const magnitude = Math.sqrt(x ** 2 + z ** 2);
      const duration = parseInt((magnitude * ActionConverter.MAGNITUDE_DURATION_SCALE).toString(), 10);
      return { tool: "walk", parameters: { duration } };
    }
    return null;
  }

  private static _convert_look_action(action: PygameLookAction): McpLookAngleAction | null {
    const movement_x = action.movementX || 0;
    const movement_y = action.movementY || 0;

    const x_angle = movement_x / ActionConverter.SENSITIVITY;
    const y_angle = -(movement_y / ActionConverter.SENSITIVITY); // Invert Y axis

    if (
      Math.abs(x_angle) > ActionConverter.LOOK_THRESHOLD ||
      Math.abs(y_angle) > ActionConverter.LOOK_THRESHOLD
    ) {
      return {
        tool: "lookAngle",
        parameters: {
          xAngle: parseFloat(x_angle.toFixed(1)),
          yAngle: parseFloat(y_angle.toFixed(1)),
          speed: "normal",
        },
      };
    }
    return null;
  }

  private static _convert_left_click_action(action: PygameMouseAction): McpLeftClickAction {
    return { tool: "leftClick", parameters: { duration: "short" } };
  }

  private static _convert_right_click_action(action: PygameRightDownAction): McpRightClickAction {
    return { tool: "rightClick", parameters: { duration: "short" } };
  }

  static convert_pygame_actions_bulk(actions: InputPygameAction[]): KnownMcpAction[] {
    const mcp_actions: KnownMcpAction[] = [];

    for (const action of actions) {
      let converted: KnownMcpAction | null = null;
      if (typeof action === 'object' && action !== null && 'type' in action) {
        converted = ActionConverter.convert_pygame_action(action as PygameAction);
      } else if (typeof action === 'string') {
        converted = ActionConverter._convert_string_action(action);
      }

      if (converted) {
        mcp_actions.push(converted);
      }
    }
    return mcp_actions;
  }

  private static _convert_string_action(action_str: string): KnownMcpAction | null {
    try {
      if (action_str.includes('"move":')) {
        return { tool: "walk", parameters: { duration: 1000 } };
      } else if (action_str.includes('"look":')) {
        const action_data = JSON.parse(action_str);
        if (action_data.look) {
          const look_data = action_data.look;
          const dict_action: PygameLookAction = {
            type: "look",
            movementX: look_data.movementX || 0,
            movementY: look_data.movementY || 0,
          };
          return ActionConverter.convert_pygame_action(dict_action);
        }
      }
    } catch (e) {
      console.warn(`⚠️ Could not parse legacy action: ${action_str} - ${e}`);
    }
    return null;
  }

  static to_simple_format(conversions: KnownMcpAction[]): KnownMcpAction[] {
    return conversions;
  }

  static to_openai_format(conversions: KnownMcpAction[], sequence_id: string): OpenAiToolCall[] {
    const tool_calls: OpenAiToolCall[] = [];

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

  static pygame_to_mcp_simple(actions: InputPygameAction[]): KnownMcpAction[] {
    const conversions = ActionConverter.convert_pygame_actions_bulk(actions);
    return ActionConverter.to_simple_format(conversions);
  }

  static pygame_to_openai_tools(actions: InputPygameAction[], sequence_id: string): OpenAiToolCall[] {
    const conversions = ActionConverter.convert_pygame_actions_bulk(actions);
    return ActionConverter.to_openai_format(conversions, sequence_id);
  }
}


function validate_conversion_consistency(): boolean {
  const test_actions: InputPygameAction[] = [
    { type: "move", x: 0.5, z: 0.3 },
    { type: "look", movementX: 10, movementY: -5 },
    { type: "documentMouseEvent", button: 0, action: "down" } as PygameMouseAction,
    { type: "rightDown" } as PygameRightDownAction,
  ];

  const simple_format = ActionConverter.pygame_to_mcp_simple(test_actions);
  const openai_format = ActionConverter.pygame_to_openai_tools(test_actions, "test_seq");

  console.log(`✅ Simple format: ${simple_format.length} actions`);
  console.log(`✅ OpenAI format: ${openai_format.length} tool calls`);

  let consistent: boolean = true;
  if (simple_format.length !== openai_format.length) {
    console.error("❌ Length mismatch between simple and OpenAI formats.");
    consistent = false;
  } else {
    for (let i = 0; i < simple_format.length; i++) {
      const simple = simple_format[i] as KnownMcpAction; // Type assertion
      const openai = openai_format[i] as OpenAiToolCall; // Type assertion

      const simple_tool = simple.tool;
      const openai_tool = openai.function.name;
      if (simple_tool !== openai_tool) {
        console.error(`❌ Tool mismatch at index ${i}: ${simple_tool} != ${openai_tool}`);
        consistent = false;
      }

      const simple_params_str = JSON.stringify(simple.parameters);
      const openai_params_str = openai.function.arguments;

      if (simple_params_str !== openai_params_str) {
        try {
          const openai_params_obj = JSON.parse(openai_params_str);
          if (JSON.stringify(simple.parameters) !== JSON.stringify(openai_params_obj)) {
            console.error(`❌ Parameters mismatch at index ${i}:`);
            console.error(`  Simple: ${JSON.stringify(simple.parameters)}`);
            console.error(`  OpenAI: ${JSON.stringify(openai_params_obj)}`);
            consistent = false;
          }
        } catch (e) {
          console.error(`❌ Error parsing OpenAI parameters at index ${i}: ${openai_params_str}`, e);
          consistent = false;
        }
      }
    }
  }

  if (consistent) {
    console.log("✅ Conversion consistency validated!");
  } else {
    console.error("❌ Conversion consistency validation failed.");
  }
  return consistent;
}

// Type for params in convert_to_mcp_format
type ConvertToMcpParams = {
    duration?: string | number;
    slot?: number;
    state?: boolean;
    amount?: number;
    [key: string]: any; // Allow other potential params
};


function convert_to_mcp_format(command_type: string, params?: ConvertToMcpParams): KnownMcpAction | null {
  params = params || {};

  switch (command_type) {
    case "left_click":
    case "leftClick":
      return {
        tool: "leftClick",
        parameters: { duration: (params.duration as string) || "medium" },
      } as McpLeftClickAction;
    case "right_click":
    case "rightClick":
      return {
        tool: "rightClick",
        parameters: { duration: (params.duration as string) || "medium" },
      } as McpRightClickAction;
    case "walk":
      return {
        tool: "walk",
        parameters: { duration: (params.duration as number) || 1000 },
      } as McpWalkAction;
    case "setHotbarSlot":
      return {
        tool: "setHotbarSlot",
        parameters: { slot: params.slot !== undefined ? params.slot : 0 },
      } as McpSetHotbarSlotAction;
    case "jump":
      return {
        tool: "jump",
        parameters: { duration: (params.duration as string) || "short" },
      } as McpJumpAction;
    case "sneak":
      return {
        tool: "sneak",
        parameters: { state: params.state !== undefined ? params.state : true },
      } as McpSneakAction;
    case "sprint":
      return {
        tool: "sprint",
        parameters: { state: params.state !== undefined ? params.state : true },
      } as McpSprintAction;
    case "toggleInventory":
      return {
        tool: "toggleInventory",
        parameters: {},
      } as McpToggleInventoryAction;
    case "dropItem":
      return {
        tool: "dropItem",
        parameters: { amount: params.amount || 1 },
      } as McpDropItemAction;
    case "swapHands":
      return {
        tool: "swapHands",
        parameters: {},
      } as McpSwapHandsAction;
    default:
      return null;
  }
}

// For potential Node.js environment export / ES module export
export {
  ActionConverter,
  validate_conversion_consistency,
  convert_to_mcp_format,
  // Export types if they are to be used by other modules
  PygameAction,
  PygameMoveAction,
  PygameLookAction,
  PygameMouseAction,
  PygameRightDownAction,
  McpAction,
  McpWalkAction,
  McpLookAngleAction,
  McpLeftClickAction,
  McpRightClickAction,
  McpSetHotbarSlotAction,
  McpJumpAction,
  McpSneakAction,
  McpSprintAction,
  McpToggleInventoryAction,
  McpDropItemAction,
  McpSwapHandsAction,
  KnownMcpAction,
  OpenAiToolCall,
  InputPygameAction,
  ConvertToMcpParams
};

// To make it runnable for testing (e.g. `ts-node action_converter.ts` or after compiling to JS)
// This check ensures it only runs when the script is executed directly
if (typeof require !== 'undefined' && require.main === module) {
  validate_conversion_consistency();
  console.log("\nTesting convert_to_mcp_format:");
  console.log(convert_to_mcp_format("walk", { duration: 500 }));
  console.log(convert_to_mcp_format("jump", {}));
  console.log(convert_to_mcp_format("setHotbarSlot", { slot: 3 }));
  console.log(convert_to_mcp_format("unknown_action", {}));
}

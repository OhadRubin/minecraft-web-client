// Placeholder for ConversationPanel and its methods until it's defined
// This is to allow PygameMCPAsyncMessageChain to be implemented
interface Action {
  tool_name: string;
  tool_args: Record<string, any>;
}

class ConversationPanel {
  static convert_actions_to_mock_response(actions: Action[]): { content: string | null; tool_calls: ToolCall[] } {
    if (!actions || actions.length === 0) {
      return { content: "No actions to perform.", tool_calls: [] };
    }
    const tool_calls: ToolCall[] = actions.map((action, index) => ({
      id: `call_${index}_${action.tool_name}_${Date.now()}`,
      type: "function",
      function: {
        name: action.tool_name,
        arguments: JSON.stringify(action.tool_args),
      },
    }));
    return {
      content: null, // Or some summary message if appropriate
      tool_calls,
    };
  }
}
// End Placeholder

export interface ToolCall {
  id: string;
  type: "function";
  function: {
    name: string;
    arguments: string; // JSON string of arguments
  };
}

export interface Message {
  role: "system" | "user" | "assistant" | "tool";
  content: string | null;
}

export interface SystemMessage extends Message {
  role: "system";
  content: string;
}

export interface UserMessage extends Message {
  role: "user";
  content: string;
}

export interface AssistantMessage extends Message {
  role: "assistant";
  content: string | null;
  tool_calls?: ToolCall[];
}

export interface ToolMessage extends Message {
  role: "tool";
  content: string; // Output of the tool
  tool_call_id: string;
  name?: string; // Name of the tool that was called
}

export type AnyMessage = SystemMessage | UserMessage | AssistantMessage | ToolMessage;

export interface PygameMCPAsyncMessageChainData {
  messages: AnyMessage[];
  system_prompt: string | null;
  memory_key: string;
  input_key: string;
  output_key: string;
  human_role: "user"; // Or allow other roles if necessary
  ai_role: "assistant"; // Or allow other roles
  client_info: Record<string, any> | null;
}

export class PygameMCPAsyncMessageChain {
  messages: AnyMessage[];
  system_prompt: string | null;
  memory_key: string;
  input_key: string;
  output_key: string;
  human_role: "user";
  ai_role: "assistant";
  client_info: Record<string, any> | null;

  constructor(data: PygameMCPAsyncMessageChainData) {
    this.messages = data.messages || [];
    this.system_prompt = data.system_prompt || null;
    this.memory_key = data.memory_key || "history";
    this.input_key = data.input_key || "input";
    this.output_key = data.output_key || "output";
    this.human_role = data.human_role || "user";
    this.ai_role = data.ai_role || "assistant";
    this.client_info = data.client_info || null;
  }

  serialize(): AnyMessage[] {
    const serializedMessages: AnyMessage[] = [];
    if (this.system_prompt) {
      serializedMessages.push({ role: "system", content: this.system_prompt });
    }
    this.messages.forEach(msg => {
      const messageCopy = { ...msg }; // Create a shallow copy to avoid modifying original
      if (messageCopy.role === "assistant") {
        // Ensure tool_calls are included if they exist
        if (!messageCopy.tool_calls || messageCopy.tool_calls.length === 0) {
          delete (messageCopy as AssistantMessage).tool_calls;
        }
      } else if (messageCopy.role === "tool") {
        // Ensure tool_call_id is included, and name if it exists
        // 'name' is optional in our ToolMessage, but good to keep if present
        if (!(messageCopy as ToolMessage).name) {
            // delete (messageCopy as ToolMessage).name; // Not strictly needed if undefined
        }
      }
      serializedMessages.push(messageCopy);
    });
    return serializedMessages;
  }

  static from_dict(data: Partial<PygameMCPAsyncMessageChainData>): PygameMCPAsyncMessageChain {
    const completeData: PygameMCPAsyncMessageChainData = {
      messages: [],
      system_prompt: null,
      memory_key: "history",
      input_key: "input",
      output_key: "output",
      human_role: "user",
      ai_role: "assistant",
      client_info: null,
      ...data,
    };
    return new PygameMCPAsyncMessageChain(completeData);
  }

  static from_json(json_string: string): PygameMCPAsyncMessageChain {
    const data = JSON.parse(json_string) as Partial<PygameMCPAsyncMessageChainData>;
    return PygameMCPAsyncMessageChain.from_dict(data);
  }

  // Simplified generate method
  generate(actions: Action[], user_prompt: string = "Perform the following actions."): AnyMessage[] {
    const messages_to_store: AnyMessage[] = [];

    // 1. User Message
    messages_to_store.push({ role: "user", content: user_prompt } as UserMessage);

    // 2. Assistant Message (from actions)
    const assistant_response = ConversationPanel.convert_actions_to_mock_response(actions);
    const assistant_message: AssistantMessage = {
      role: "assistant",
      content: assistant_response.content,
      tool_calls: assistant_response.tool_calls,
    };
    messages_to_store.push(assistant_message);

    // 3. Tool Messages (mocked)
    if (assistant_response.tool_calls) {
      assistant_response.tool_calls.forEach(tool_call => {
        messages_to_store.push({
          role: "tool",
          tool_call_id: tool_call.id,
          name: tool_call.function.name, // Added name here
          content: `Executed ${tool_call.function.name} successfully with args ${tool_call.function.arguments}`, // Mocked content
        } as ToolMessage);
      });
    }

    // This method is designed to produce a list of messages for TrajectoryStorage,
    // so we might not add them to this.messages directly, or perhaps we do and then return them.
    // For now, just returning them as per the requirement.
    // If these messages should also update the instance's state, this.messages.push(...messages_to_store) would be needed.
    return messages_to_store;
  }

  // Example of how one might add messages to the internal state
  add_messages(new_messages: AnyMessage[]): void {
    this.messages.push(...new_messages);
  }
}

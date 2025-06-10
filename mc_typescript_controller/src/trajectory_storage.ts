import * as fs from 'fs';
import * as path from 'path';
import { AnyMessage, ToolCall, UserMessage, AssistantMessage, ToolMessage } from './pygame_mcp_chain'; // Assuming interfaces are exported

// Placeholder for ConversationPanel's mock response structure
// This should align with what convert_actions_to_mock_response actually returns.
export interface MockResponse {
  content: string | null;
  tool_calls?: ToolCall[];
}

// A trajectory step now consists of a sequence of messages
// (e.g., user prompt, assistant response with tool calls, tool execution results)
export interface TrajectoryStep {
  user_context_message: UserMessage;
  assistant_response_messages: (AssistantMessage | ToolMessage)[];
  timestamp: number;
}

export interface Trajectory {
  session_id: string;
  steps: TrajectoryStep[]; // Each step is now a collection of messages
  timestamp: number; // Timestamp for when the trajectory was finalized
}

export class TrajectoryStorage {
  private currentSessionId: string | null = null;
  private currentSessionSteps: TrajectoryStep[] = [];
  private trajectoriesDir = 'trajectories';

  constructor() {
    if (!fs.existsSync(this.trajectoriesDir)) {
      fs.mkdirSync(this.trajectoriesDir, { recursive: true });
    }
  }

  start_session(sessionId: string): void {
    if (this.currentSessionId) {
      console.warn(`Session ${this.currentSessionId} is already active. Ending it before starting a new one.`);
      this.end_session();
    }
    this.currentSessionId = sessionId;
    this.currentSessionSteps = [];
    console.log(`Session ${sessionId} started.`);
  }

  add_step(user_context: string, mock_response: MockResponse): void {
    if (!this.currentSessionId) {
      console.error('Cannot add step: No active session. Call start_session first.');
      return;
    }

    const user_message: UserMessage = { role: 'user', content: user_context };
    const assistant_response_messages: (AssistantMessage | ToolMessage)[] = [];

    const assistant_message: AssistantMessage = {
      role: 'assistant',
      content: mock_response.content,
    };
    if (mock_response.tool_calls && mock_response.tool_calls.length > 0) {
      assistant_message.tool_calls = mock_response.tool_calls;
    }
    assistant_response_messages.push(assistant_message);

    if (mock_response.tool_calls) {
      mock_response.tool_calls.forEach(tc => {
        assistant_response_messages.push({
          role: 'tool',
          tool_call_id: tc.id,
          name: tc.function.name,
          content: `Mocked execution of ${tc.function.name} with args ${tc.function.arguments}`, // Placeholder content
        } as ToolMessage);
      });
    }

    this.currentSessionSteps.push({
        user_context_message: user_message,
        assistant_response_messages: assistant_response_messages,
        timestamp: Date.now()
    });
    console.log(`Step added to session ${this.currentSessionId}.`);
  }

  end_session(final_mock_response?: MockResponse): void {
    if (!this.currentSessionId) {
      console.warn('No active session to end.');
      return;
    }

    if (final_mock_response) {
        // Similar to add_step, but perhaps with a different user context or as a final action.
        // For simplicity, let's assume a generic user context if a final response is given.
        this.add_step("Finalizing session actions.", final_mock_response);
    }

    const trajectoryData: Trajectory = {
      session_id: this.currentSessionId,
      steps: this.currentSessionSteps,
      timestamp: Date.now(),
    };

    const filename = `${this.currentSessionId}_${trajectoryData.timestamp}.json`;
    const filepath = path.join(this.trajectoriesDir, filename);

    try {
      fs.writeFileSync(filepath, JSON.stringify(trajectoryData, null, 2));
      console.log(`Trajectory saved to ${filepath}`);
    } catch (error) {
      console.error(`Failed to save trajectory to ${filepath}:`, error);
    }

    // Reset session
    const endedSessionId = this.currentSessionId;
    this.currentSessionId = null;
    this.currentSessionSteps = [];
    console.log(`Session ${endedSessionId} ended.`);
    // The Python version returns the filepath, which might be useful.
    // return filepath; // Uncomment if needed
  }
}

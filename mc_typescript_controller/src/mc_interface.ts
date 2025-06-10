import { TrajectoryStorage, MockResponse } from './trajectory_storage';
import { ConversationPanel, MCPAction } from './conversation';
// PygameMCPAsyncMessageChain might not be directly needed here if TrajectoryStorage handles formatting
// import { PygameMCPAsyncMessageChain } from './pygame_mcp_chain';

export class MinecraftControllerInterface {
  private trajectoryStorage: TrajectoryStorage;
  private conversationPanel: ConversationPanel;

  constructor() {
    this.trajectoryStorage = new TrajectoryStorage();
    this.conversationPanel = new ConversationPanel();
    console.log("MinecraftControllerInterface initialized.");
  }

  capture_command(mcp_action: MCPAction): void {
    this.conversationPanel.capture_mcp_action(mcp_action);
    console.log(`Command captured: ${mcp_action.tool}`);
  }

  start_trajectory_recording(session_name: string = "human_demo"): void {
    this.trajectoryStorage.start_session(session_name);
    // console.log(`Trajectory recording started for session: ${session_name}`); // Already logged by TrajectoryStorage
  }

  stop_trajectory_recording(): void | null { // Adjusted to match Python's potential None return (void in TS if no explicit return)
    if (this.conversationPanel.captured_actions.length === 0 && this.trajectoryStorage['currentSessionSteps'] && this.trajectoryStorage['currentSessionSteps'].length === 0 ) { // Check if any actions were ever captured for this session
      console.log("No actions captured for the current trajectory. Stopping recording without saving empty data.");
      // Ensure session is ended even if no data, to reset state
      this.trajectoryStorage.end_session();
      return null;
    }

    // The prompt mentioned: "Get mock_response = this.conversationPanel.convert_actions_to_mock_response()"
    // "Call this.trajectoryStorage.end_session(mock_response)"
    // This implies that any pending captured actions should be treated as the "final" response for the session.

    let final_mock_response: MockResponse | undefined = undefined;
    if (this.conversationPanel.captured_actions.length > 0) {
        final_mock_response = this.conversationPanel.convert_actions_to_mock_response();
        console.log("Converted final captured actions to mock response for end_session.");
    } else {
        console.log("No pending actions in conversationPanel, ending session with existing steps.");
    }

    // end_session in TrajectoryStorage now accepts an optional final_mock_response
    // and will add it as a last step if provided.
    // It then saves all accumulated steps for the session.
    this.trajectoryStorage.end_session(final_mock_response);

    // The Python version might return the filepath. TrajectoryStorage.end_session could be modified to do so.
    // For now, returning void as per current TS TrajectoryStorage.end_session.
    // If TrajectoryStorage.end_session returns filepath, this method could return it too.
    return; // Explicitly return to match void|null, though void is implicit.
  }

  save_demonstration_step(user_context: string = "exploring"): boolean {
    if (this.conversationPanel.captured_actions.length === 0) {
      console.log("No actions captured in conversationPanel to save as a step.");
      return false;
    }

    const mock_response = this.conversationPanel.convert_actions_to_mock_response();
    // console.log("Converted actions to mock response for save_demonstration_step:", mock_response); // Optional: for debugging

    this.trajectoryStorage.add_step(user_context, mock_response);
    // console.log(`Demonstration step saved with user_context: ${user_context}`); // Already logged by TrajectoryStorage
    return true;
  }

  // Omitted methods:
  // execute_command
  // set_controller
}

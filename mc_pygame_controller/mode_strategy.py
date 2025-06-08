"""
Mode Strategy Pattern Implementation for MinecraftController

This module implements the Strategy Pattern to eliminate mode-specific if/else 
logic scattered throughout the controller by creating specialized mode handlers.
"""

import time
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

# Phase 2 imports - Leverage existing infrastructure!
try:
    from .async_mcp_executor import AsyncMCPExecutor, MCPActionRequest
    from .action_sequence_tracker import ActionSequenceTracker
    from .mcp_client import Server
    from .chain import PygameMCPAsyncMessageChain
    from .data_collection_controller import DataCollectionController
except ImportError:
    # Handle direct script execution
    from async_mcp_executor import AsyncMCPExecutor, MCPActionRequest
    from action_sequence_tracker import ActionSequenceTracker
    from mcp_client import Server
    from chain import PygameMCPAsyncMessageChain
    from data_collection_controller import DataCollectionController


class ModeStrategy(ABC):
    """Abstract base class for controller mode strategies."""

    def __init__(self, controller):
        """Initialize with reference to the controller for accessing shared state and utilities."""
        self.controller = controller

    @abstractmethod
    def handle_movement(self, x: float, z: float):
        """Handle movement commands for this mode."""
        pass

    @abstractmethod
    def handle_timed_action(
        self, 
        action_name: str, 
        duration: str, 
        pygame_down_cmd: Dict[str, Any] = None,
        pygame_up_cmd: Dict[str, Any] = None,
        **kwargs
    ):
        """Handle timed actions (clicks, jump, etc.) for this mode."""
        pass

    @abstractmethod
    def handle_toggle_action(self, action_name: str, state: bool, pygame_control: str = None):
        """Handle toggle actions (sneak, sprint) for this mode."""
        pass

    @abstractmethod
    def handle_simple_action(self, action_name: str, pygame_cmd: Dict[str, Any] = None, **params):
        """Handle simple one-shot actions (drop, swap, inventory, etc.) for this mode."""
        pass

    @abstractmethod
    def connect(self):
        """Initialize connection/setup for this mode."""
        pass

    @abstractmethod
    def process_continuous_state(self, mouse_pos, mouse_pressed, keys_pressed):
        """Process continuous state updates for this mode (e.g., button holds)."""
        pass

# if we wanted to create a MCPPygameModeStrategy, that would be able to send commands via both the websocket and via MCP, we would need to init it the same way we do with MCP mode right?
class PygameModeStrategy(ModeStrategy):
    """Strategy for pygame mode - sends WebSocket commands to Minecraft client."""

    def __init__(
        self,
        controller,
        mcp_server: Optional[Server] = None,
        data_collection_enabled=False,
    ):
        super().__init__(controller)
        # Track previous movement state for continuous streaming
        self.was_moving = False

        # This logic now clearly defines the two operational modes of this strategy
        if mcp_server and data_collection_enabled:
            # --- MOCK + OBSERVE MODE INITIALIZATION ---
            print("🔧 PygameModeStrategy: Initializing MOCK + OBSERVE mode")
            print(
                "🎭 Actions will be mocked, only getBotStatus executed for real observation"
            )
            self.mcp_server = mcp_server
            self.data_collection_enabled = True
            # ✅ No async_executor needed - we only call getBotStatus directly!
            self.async_executor = None
            self.sequence_tracker = ActionSequenceTracker()
            self.data_collector = DataCollectionController()
        else:
            # --- PURE MODE INITIALIZATION ---
            print("🔧 PygameModeStrategy: Initializing in PURE WebSocket mode.")
            self.mcp_server = None
            self.data_collection_enabled = False
            self.async_executor = None
            self.sequence_tracker = None
            self.data_collector = None

        # Phase 1: Simple queue for tracking (maintained for compatibility)
        self._mcp_action_queue = []

        print(
            f"🔧 PygameModeStrategy: Mode={self.data_collection_enabled and 'MOCK+OBSERVE' or 'PURE'}, "
            f"Server={'✅' if self.mcp_server else '❌'}, "
            f"Data Collection={'✅' if self.data_collection_enabled else '❌'}"
        )

    def handle_movement(self, x: float, z: float):
        """Send movement command via WebSocket and log for MCP compatibility."""
        command = {"type": "move", "x": x, "z": z}
        self.controller.send_command_sync(command)

        # Phase 2 enhancement: Queue parallel MCP execution for data collection
        if self.data_collection_enabled and self.mcp_server:
            task_context = getattr(self.controller, "current_task_description", "")
            self._queue_parallel_mcp_execution([command], task_context)

        # Log movement in pygame mode if logging enabled
        if self.controller.enable_logging and (abs(x) > 0.1 or abs(z) > 0.1):
            # Calculate duration based on movement magnitude (same as MCP mode)
            magnitude = (x**2 + z**2) ** 0.5
            duration = int(magnitude * 2000)  # Scale to reasonable duration
            self.controller.action_handler._log_mcp_command("walk", {"duration": duration})

    def handle_timed_action(
        self, 
        action_name: str, 
        duration: str, 
        pygame_down_cmd: Dict[str, Any] = None,
        pygame_up_cmd: Dict[str, Any] = None,
        **kwargs
    ):
        """Send pygame down/up commands and log MCP equivalent."""
        commands_sent = []

        if pygame_down_cmd:
            self.controller.send_command_sync(pygame_down_cmd)
            commands_sent.append(pygame_down_cmd)
        if pygame_up_cmd:
            self.controller.send_command_sync(pygame_up_cmd)
            commands_sent.append(pygame_up_cmd)

        # Phase 2 enhancement: Queue parallel MCP execution for data collection
        if self.data_collection_enabled and self.mcp_server and commands_sent:
            task_context = getattr(self.controller, "current_task_description", "")
            self._queue_parallel_mcp_execution(commands_sent, task_context)

        # Log the action in pygame mode
        mcp_params = {"duration": duration, **kwargs}
        self.controller.action_handler._log_mcp_command(action_name, mcp_params)

    def handle_toggle_action(self, action_name: str, state: bool, pygame_control: str = None):
        """Send pygame control command and log MCP equivalent."""
        command_sent = None

        if pygame_control:
            command = {"type": "control", "control": pygame_control, "state": state}
            self.controller.send_command_sync(command)
            command_sent = command

        # Phase 2 enhancement: Queue parallel MCP execution for data collection
        if self.data_collection_enabled and self.mcp_server and command_sent:
            task_context = getattr(self.controller, "current_task_description", "")
            self._queue_parallel_mcp_execution([command_sent], task_context)

        self.controller.action_handler._log_mcp_command(action_name, {"state": state})

    def handle_simple_action(self, action_name: str, pygame_cmd: Dict[str, Any] = None, **params):
        """Send pygame command and log MCP equivalent."""
        if pygame_cmd:
            self.controller.send_command_sync(pygame_cmd)

            # Phase 2 enhancement: Queue parallel MCP execution for data collection
            if self.data_collection_enabled and self.mcp_server:
                task_context = getattr(self.controller, "current_task_description", "")
                self._queue_parallel_mcp_execution([pygame_cmd], task_context)

        self.controller.action_handler._log_mcp_command(action_name, params)

    def connect(self):
        """Start WebSocket connection for pygame mode."""
        self.controller.start_websocket_connection()

    def process_continuous_state(self, mouse_pos, mouse_pressed, keys_pressed):
        """Process continuous state for pygame mode - handles streaming behavior."""
        # Handle continuous movement streaming - CRITICAL FIX!
        # In pygame mode, we need to send movement commands every frame while keys are held
        # The ActionHandler only sends when movement values change, but we need continuous streaming
        keyboard_move_x, keyboard_move_y = (
            self.controller.ui_manager.keyboard_movement.handle_keyboard(keys_pressed)
        )

        # Get joystick values by calculating from knob position
        joystick = self.controller.ui_manager.movement_joystick
        joystick_move_x = (joystick.knob_x - joystick.center_x) / joystick.radius
        joystick_move_y = (joystick.knob_y - joystick.center_y) / joystick.radius

        # Determine active movement (same logic as UI manager)
        movement_x, movement_z = 0.0, 0.0
        if abs(joystick_move_x) < 0.1 and abs(joystick_move_y) < 0.1:
            if abs(keyboard_move_x) > 0.1 or abs(keyboard_move_y) > 0.1:
                movement_x, movement_z = keyboard_move_x, keyboard_move_y
        else:
            movement_x, movement_z = joystick_move_x, joystick_move_y

        # Check if currently moving
        is_moving = abs(movement_x) > 0.1 or abs(movement_z) > 0.1

        # Send movement commands or stop commands based on state changes
        if is_moving:
            # Send continuous movement while keys are held
            command = {"type": "move", "x": movement_x, "z": movement_z}
            self.controller.send_command_sync(command)
        elif self.was_moving and not is_moving:
            # Send stop command when transitioning from moving to not moving
            command = {"type": "move", "x": 0.0, "z": 0.0}
            self.controller.send_command_sync(command)

        # Update movement state for next frame
        self.was_moving = is_moving

        # Check for continuous button holds (mining/building)
        left_click_state = self.controller.state.action_states.get("left_click", {})
        if left_click_state.get("active", False):
            # Left click is being held - send continuous mining command
            command = {
                "type": "documentMouseEvent",
                "button": 0,
                "action": "down",
                "updateMouse": True,
            }
            self.controller.send_command_sync(command)

        right_click_state = self.controller.state.action_states.get("right_click", {})
        if right_click_state.get("active", False):
            # Right click is being held - send continuous right click command
            command = {"type": "rightDown"}
            self.controller.send_command_sync(command)

        # Phase 2 enhancement: Async execution methods

    async def start_async_execution(self):
        """Initialize async components for mock+observe pattern."""
        return await self.initialize_async_components()

    async def stop_async_execution(self):
        """Cleanup async components for mock+observe pattern."""
        return await self.cleanup_async_components()

    async def initialize_async_components(self):
        """Initialize async components for data collection (mock+observe pattern)."""
        if self.data_collection_enabled:
            print("✅ Mock+observe data collection mode initialized")
            print(
                "🎭 Actions will be mocked, getBotStatus will be executed for real observation"
            )
            return True
        return True

    async def cleanup_async_components(self):
        """Cleanup async components for data collection (mock+observe pattern)."""
        if self.data_collection_enabled:
            # Clean up any remaining active tasks
            if hasattr(self, "_active_tasks"):
                remaining_tasks = len(self._active_tasks)
                if remaining_tasks > 0:
                    print(
                        f"🧹 Cancelling {remaining_tasks} remaining getBotStatus tasks"
                    )
                    for task in list(self._active_tasks):
                        task.cancel()
                    self._active_tasks.clear()
            print("✅ Mock+observe data collection mode cleaned up")
        return True

    # Phase 2: Enhanced MCP integration with existing infrastructure
    def _queue_parallel_mcp_execution(
        self, actions: List[str], task_context: str = ""
    ) -> None:
        """
        Simple pattern:
        1. ALWAYS execute getBotStatus (capture game state)
        2. Mock the pygame actions we just received
        3. Save conversation ONLY if recording
        """
        if not self.data_collection_enabled or not self.mcp_server:
            return

        # Convert pygame actions to mock MCP format
        mcp_actions = self._convert_actions_to_mcp_format(actions)
        print(f"🎭 Mock actions: {[action['tool'] for action in mcp_actions]}")

        # ALWAYS execute getBotStatus
        try:
            task = asyncio.create_task(
                self._always_execute_getbotstatus(actions, mcp_actions, task_context)
            )
            if not hasattr(self, "_active_tasks"):
                self._active_tasks = set()
            self._active_tasks.add(task)
            task.add_done_callback(self._active_tasks.discard)
        except RuntimeError as e:
            print(f"⚠️ Cannot create async task: {e}")

    async def _always_execute_getbotstatus(
        self, pygame_actions, mcp_actions, task_context
    ):
        """ALWAYS execute getBotStatus. Save conversation only if recording."""
        try:
            # ALWAYS execute getBotStatus
            real_response = await self.mcp_server.execute_tool("getBotStatus", {})

            # Show full getBotStatus result like startup does
            print(f"📊 RUNTIME getBotStatus result: {real_response}")
            print(f"📊 getBotStatus executed: {len(str(real_response))} chars")

            # Save conversation ONLY if recording
            recording = self.data_collector and self.data_collector.current_session
            if recording:
                print(f"💾 Recording active - saving conversation")
                self._save_mock_conversation(
                    pygame_actions, mcp_actions, real_response, task_context
                )
            else:
                print(f"📊 Not recording - getBotStatus captured but not saved")

        except Exception as e:
            print(f"❌ getBotStatus failed: {e}")

    def _save_mock_conversation(
        self, pygame_actions, mcp_actions, getbotstatus_response, task_context
    ):
        """Save conversation with mock actions + real getBotStatus response."""
        # Create sequence
        sequence_id = self.sequence_tracker.start_sequence(
            pygame_actions, task_context, expected_responses=1
        )

        # Add real getBotStatus response
        observation_response = {
            "tool": "getBotStatus",
            "content": getbotstatus_response.get("content", []),
            "timestamp": time.time(),
            "tool_call_id": f"real_getbotstatus_{int(time.time() * 1000000) % 1000000}",
        }

        self.sequence_tracker.add_mcp_response(sequence_id, observation_response)

        # Build and save conversation
        sequence = self.sequence_tracker.active_sequences[sequence_id]
        completed_sequence = self.sequence_tracker.complete_sequence(sequence_id)

        if completed_sequence:
            chain = self._build_mock_conversation_chain(completed_sequence, mcp_actions)
            if chain and self.data_collector.current_session:
                conversation_data = {
                    "conversation_id": f"conv_{sequence_id}",
                    "task_description": task_context,
                    "start_time": completed_sequence.start_time,
                    "end_time": completed_sequence.end_time,
                    "duration": completed_sequence.end_time
                    - completed_sequence.start_time,
                    "messages": chain.to_dict().get("messages", []),
                    "sequence_metadata": {
                        "pygame_actions": len(pygame_actions),
                        "mocked_mcp_actions": len(mcp_actions),
                        "sequence_id": sequence_id,
                    },
                }
                self.data_collector.add_completed_sequence(conversation_data)
                print(f"💾 Conversation saved")

    def _build_mock_conversation_chain(self, completed_sequence, mocked_actions):
        """Build conversation chain with mocked actions and real observation."""
        from .chain import PygameMCPAsyncMessageChain

        # Start new chain
        chain = PygameMCPAsyncMessageChain()

        # Add user task
        task_content = (
            completed_sequence.task_context or "Perform spatial reasoning actions"
        )
        chain = chain.user(task_content)

        # Add assistant response with mock tool calls (never executed)
        from .action_converter import ActionConverter

        mock_tool_calls = ActionConverter.pygame_to_openai_tools(
            completed_sequence.pygame_actions, completed_sequence.sequence_id
        )

        chain = chain.bot(
            content="I'll perform these spatial reasoning actions.",
            tool_calls=mock_tool_calls,
        )

        # Add the real getBotStatus observation
        for response in completed_sequence.mcp_responses:
            if response.get("tool") == "getBotStatus":
                chain = chain.tool(
                    content=response.get("content", ""),
                    tool_call_id=response.get("tool_call_id", ""),
                    name="getBotStatus",
                )

        return chain

    def _convert_actions_to_mcp_format(self, pygame_actions):
        """Convert pygame WebSocket commands to MCP tool calls using shared ActionConverter."""
        # ✅ REFACTORED: Use shared ActionConverter to eliminate duplication
        from .action_converter import ActionConverter

        return ActionConverter.pygame_to_mcp_simple(pygame_actions)

    def start_data_collection_session(self, task_description: str) -> str:
        """Start a new data collection session."""
        if not self.data_collector:
            print("⚠️ Data collection not enabled for this strategy.")
            return None

        return self.data_collector.start_collection_session(task_description)

    def save_data_collection_session(self) -> str:
        """Save the current data collection session."""
        if self.data_collector:
            return self.data_collector.save_session()
        return None

    def cancel_data_collection_session(self) -> None:
        """Cancel the current data collection session."""
        if self.data_collector:
            self.data_collector.cancel_session()
        else:
            print("⚠️ No data collection session to cancel.")

    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        if self.data_collector:
            return self.data_collector.get_session_stats()
        return {"status": "data_collection_disabled"}


class MCPModeStrategy(ModeStrategy):
    """Strategy for MCP mode - converts actions to MCP tool calls."""

    def handle_movement(self, x: float, z: float):
        """Convert movement to walk command with timing control."""
        # Only send walk command if enough time has passed (avoid spamming)
        if time.time() - self.controller.last_moved_in_mcp_mode > 2:
            # Calculate duration based on movement magnitude
            magnitude = (x**2 + z**2) ** 0.5
            # Use a fixed duration for consistency (calculated_duration could be used for scaling)
            self.handle_simple_action("walk", duration=1000)
            self.controller.last_moved_in_mcp_mode = time.time()

    def handle_timed_action(
        self, 
        action_name: str, 
        duration: str, 
        pygame_down_cmd: Dict[str, Any] = None,
        pygame_up_cmd: Dict[str, Any] = None,
        **kwargs
    ):
        """Execute MCP timed action."""
        # pygame commands not used in MCP mode (parameters kept for interface compatibility)
        _ = pygame_down_cmd, pygame_up_cmd  # Suppress unused warnings
        params = {"duration": duration, **kwargs}
        self.controller.handle_other_commands(action_name, **params)

    def handle_toggle_action(self, action_name: str, state: bool, pygame_control: str = None):
        """Execute MCP toggle action."""
        # pygame_control not used in MCP mode (parameter kept for interface compatibility)
        _ = pygame_control  # Suppress unused warning
        self.controller.handle_other_commands(action_name, state=state)

    def handle_simple_action(self, action_name: str, pygame_cmd: Dict[str, Any] = None, **params):
        """Execute MCP simple action."""
        # pygame_cmd not used in MCP mode (parameter kept for interface compatibility)
        _ = pygame_cmd  # Suppress unused warning
        self.controller.handle_other_commands(action_name, **params)

    def connect(self):
        """MCP mode doesn't need WebSocket connection."""
        print("MCP mode ready. No WebSocket connection needed.")

    def process_continuous_state(self, mouse_pos, mouse_pressed, keys_pressed):
        """MCP mode does not handle continuous state streaming - uses discrete actions only."""
        pass

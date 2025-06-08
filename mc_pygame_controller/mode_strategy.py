"""
Mode Strategy Pattern Implementation for MinecraftController

This module implements the Strategy Pattern to eliminate mode-specific if/else 
logic scattered throughout the controller by creating specialized mode handlers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import time
import asyncio

# Phase 2 imports - Leverage existing infrastructure!
try:
    from .async_mcp_executor import AsyncMCPExecutor, MCPActionRequest
    from .action_sequence_tracker import ActionSequenceTracker
    from .mcp_client import Server
    from .chain import PygameMCPAsyncMessageChain
except ImportError:
    # Handle direct script execution
    from async_mcp_executor import AsyncMCPExecutor, MCPActionRequest
    from action_sequence_tracker import ActionSequenceTracker
    from mcp_client import Server
    from chain import PygameMCPAsyncMessageChain


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


class PygameModeStrategy(ModeStrategy):
    """Strategy for pygame mode - sends WebSocket commands to Minecraft client."""

    def __init__(
        self, controller, mcp_server: Server = None, data_collection_enabled=False
    ):
        super().__init__(controller)
        # Track previous movement state for continuous streaming
        self.was_moving = False

        # Use existing Server instead of generic mcp_client
        self.mcp_server = mcp_server
        self.data_collection_enabled = data_collection_enabled

        # Phase 1: Simple queue for tracking (maintained for compatibility)
        self._mcp_action_queue = []

        # Phase 2: Use existing infrastructure
        self.async_executor = AsyncMCPExecutor(mcp_server) if mcp_server else None
        self.sequence_tracker = ActionSequenceTracker()

        print(
            f"🔧 PygameModeStrategy using existing Server infrastructure: data_collection={data_collection_enabled}"
        )

    def handle_movement(self, x: float, z: float):
        """Send movement command via WebSocket and log for MCP compatibility."""
        command = {"type": "move", "x": x, "z": z}
        self.controller.send_command_sync(command)

        # Phase 2 enhancement: Queue parallel MCP execution for data collection
        if self.data_collection_enabled and self.mcp_server:
            self._queue_parallel_mcp_execution([command])

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
            self._queue_parallel_mcp_execution(commands_sent)

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
            self._queue_parallel_mcp_execution([command_sent])

        self.controller.action_handler._log_mcp_command(action_name, {"state": state})

    def handle_simple_action(self, action_name: str, pygame_cmd: Dict[str, Any] = None, **params):
        """Send pygame command and log MCP equivalent."""
        if pygame_cmd:
            self.controller.send_command_sync(pygame_cmd)

            # Phase 2 enhancement: Queue parallel MCP execution for data collection
            if self.data_collection_enabled and self.mcp_server:
                self._queue_parallel_mcp_execution([pygame_cmd])

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
        """Start background MCP execution."""
        if self.async_executor:
            await self.async_executor.start_background_execution()

    async def stop_async_execution(self):
        """✅ Fix Bug #16 & #18: Stop background MCP execution with proper cleanup."""
        if self.async_executor:
            await self.async_executor.stop_background_execution()

        # Clean up any remaining active tasks
        if hasattr(self, "_active_tasks"):
            remaining_tasks = len(self._active_tasks)
            if remaining_tasks > 0:
                print(f"🧹 Cancelling {remaining_tasks} remaining tasks")
                for task in list(self._active_tasks):
                    task.cancel()
                self._active_tasks.clear()

    # Phase 2: Enhanced MCP integration with existing infrastructure
    def _queue_parallel_mcp_execution(
        self, actions: List[str], task_context: str = ""
    ) -> None:
        """Enhanced version using existing mcp_client.py infrastructure."""
        if not self.data_collection_enabled or not self.async_executor:
            return

        # Phase 1: Still maintain simple queue for compatibility
        mcp_actions = self._convert_actions_to_mcp_format(actions)
        for mcp_action in mcp_actions:
            self._mcp_action_queue.append(mcp_action)

        # Always add getBotStatus for complete state capture
        mcp_actions.append({"tool": "getBotStatus", "parameters": {}})

        # Phase 2: Start tracking this action sequence
        sequence_id = self.sequence_tracker.start_sequence(actions, task_context)

        # ✅ Fix Bug #7 & #20: Create proper closure to capture sequence_id
        def create_response_handler(seq_id):
            def handler(response):
                self._handle_sequence_completion(seq_id, response)

            return handler

        # Phase 2: Register completion handler that builds PygameMCPAsyncMessageChain
        self.async_executor.register_response_handler(
            sequence_id,
            create_response_handler(sequence_id),
        )

        # Phase 2: Queue actions using simplified executor with existing Server
        # ✅ Fix Bug #9: Handle asyncio.create_task in try/except for event loop issues
        for mcp_action in mcp_actions:
            action_request = MCPActionRequest(
                tool=mcp_action["tool"],
                parameters=mcp_action["parameters"],
                sequence_id=sequence_id,
                timestamp=time.time(),
            )

            # ✅ Fix Bug #6: Store task reference to prevent garbage collection
            try:
                task = asyncio.create_task(
                    self.async_executor.queue_mcp_action(action_request)
                )
                # Store task to prevent garbage collection
                if not hasattr(self, "_active_tasks"):
                    self._active_tasks = set()
                self._active_tasks.add(task)
                task.add_done_callback(self._active_tasks.discard)
            except RuntimeError as e:
                print(f"⚠️ Cannot create async task (no event loop): {e}")
                print("💡 MCP data collection requires async event loop")

    def _handle_sequence_completion(self, sequence_id: str, response) -> None:
        """Handle completion using existing chain infrastructure."""
        # Add response to sequence tracker
        response_dict = response if isinstance(response, dict) else response.__dict__
        self.sequence_tracker.add_mcp_response(sequence_id, response_dict)

        print(
            f"📥 MCP response for {sequence_id}: {response_dict.get('tool', 'unknown')}"
        )

        # Check if sequence is complete (all expected responses received)
        if self.sequence_tracker.is_sequence_complete(sequence_id):
            # ✅ Fix Bug #3: Get the sequence BEFORE completing it (removing from active_sequences)
            sequence = self.sequence_tracker.active_sequences.get(sequence_id)

            # Complete sequence and get the data
            completed_sequence = self.sequence_tracker.complete_sequence(sequence_id)

            if completed_sequence:
                # Build conversation chain using existing infrastructure
                chain = self.sequence_tracker.build_conversation_chain(
                    completed_sequence
                )

                if chain:
                    # Save in format ready for training
                    chain_json = chain.to_json()
                    print(
                        f"💾 Built conversation chain: {len(chain.messages)} messages"
                    )

                    # TODO Phase 3: Save to file using existing format
                    print(f"🎬 Conversation ready for spatial reasoning training data")

                print(f"✅ Sequence {sequence_id} completed and processed")

                # ✅ Fix Bug #13: Clean up response handler to prevent memory leak
                if self.async_executor:
                    self.async_executor.cleanup_response_handler(sequence_id)

    def _convert_actions_to_mcp_format(self, pygame_actions):
        """Convert pygame WebSocket commands to MCP tool calls using shared ActionConverter."""
        # ✅ REFACTORED: Use shared ActionConverter to eliminate duplication
        from .action_converter import ActionConverter

        return ActionConverter.pygame_to_mcp_simple(pygame_actions)


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

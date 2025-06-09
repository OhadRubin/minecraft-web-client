"""
Mode Strategy Pattern Implementation for MinecraftController

This module implements the Strategy Pattern to eliminate mode-specific if/else 
logic scattered throughout the controller by creating specialized mode handlers.
"""

import time
import asyncio
import os
import base64
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

# Phase 2 imports - Leverage existing infrastructure!
try:
    from .mcp_client import Server
    from .chain import PygameMCPAsyncMessageChain
except ImportError:
    # Handle direct script execution
    from mcp_client import Server
    from chain import PygameMCPAsyncMessageChain


def save_screenshot_file(base64_data: str, session_id: str, tool_name: str) -> str:
    """Save screenshot to file and return filename. MVP-minimal approach."""
    os.makedirs(f"screenshots/{session_id}", exist_ok=True)
    filename = f"{int(time.time())}_{tool_name}.png"
    filepath = f"screenshots/{session_id}/{filename}"

    with open(filepath, "wb") as f:
        f.write(base64.b64decode(base64_data))

    return filename



def get_text_from_multimodal_output(output: Any) -> str:
    multimodal_content = output["multimodal_content"]

    text_parts = [
        item["text"] for item in multimodal_content if item.get("type") == "text"
    ]
    return " ".join(text_parts)


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

import os
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
        # Create directories for trajectory data
        import os
        import time
        
        # Create basic directory structure
        self.trajectories_dir = "trajectories"
        timestamp = int(time.time())
        self.current_dir = f"trajectories/trajectory_{timestamp}"
        self.images_dir = f"{self.current_dir}/images"
        
        # Make directories if they don't exist
        os.makedirs(self.trajectories_dir, exist_ok=True)
        os.makedirs(self.current_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)

        # This logic now clearly defines the two operational modes of this strategy
        if mcp_server and data_collection_enabled:
            # --- MOCK + OBSERVE MODE INITIALIZATION ---
            print("🔧 PygameModeStrategy: Initializing MOCK + OBSERVE mode")
            print(
                "🎭 Actions will be mocked, only getBotStatus executed for real observation"
            )
            self.mcp_server = mcp_server
            self.data_collection_enabled = True
        else:
            # --- PURE MODE INITIALIZATION ---
            print("🔧 PygameModeStrategy: Initializing in PURE WebSocket mode.")
            self.mcp_server = None
            self.data_collection_enabled = False

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

        # DISABLED: Old movement logging - now using continuous state tracking pattern
        # The process_continuous_state method handles movement summarization
        # Phase 2 enhancement: Queue parallel MCP execution for data collection
        # if self.data_collection_enabled and self.mcp_server:
        #     task_context = getattr(self.controller, "current_task_description", "")
        #     self._queue_parallel_mcp_execution([command], task_context)

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

        # Movement tracking pattern (similar to camera tracking)
        if is_moving and not self.was_moving:
            # Start movement tracking
            print("🚶‍♂️ Movement started - beginning walk tracking")
            self.movement_start_time = time.time()
            self.movement_accumulator = {"total_distance": 0.0, "last_pos": (movement_x, movement_z)}
            
        if is_moving:
            # Send continuous movement while keys are held (immediate game response)
            command = {"type": "move", "x": movement_x, "z": movement_z}
            self.controller.send_command_sync(command)
            
            # Accumulate movement distance for summarization
            if hasattr(self, 'movement_accumulator'):
                last_x, last_z = self.movement_accumulator["last_pos"]
                distance = ((movement_x - last_x)**2 + (movement_z - last_z)**2)**0.5
                self.movement_accumulator["total_distance"] += distance
                self.movement_accumulator["last_pos"] = (movement_x, movement_z)

        elif self.was_moving and not is_moving:
            # Movement ended - summarize and log for data collection
            print("🚶‍♂️ Movement ended - summarizing walk action")
            
            # Send stop command
            command = {"type": "move", "x": 0.0, "z": 0.0}
            self.controller.send_command_sync(command)
            
            # Log summarized movement for data collection
            if self.data_collection_enabled and hasattr(self, 'movement_accumulator'):
                duration = int((time.time() - self.movement_start_time) * 1000)  # ms
                distance = self.movement_accumulator["total_distance"]
                
                # Create summarized movement command for data collection only
                # Use the last movement direction for the summary
                last_x, last_z = self.movement_accumulator["last_pos"]
                summarized_command = {"type": "move", "x": last_x, "z": last_z, "duration": duration, "distance": distance}
                print(f"📊 Walk summary: direction=({last_x:.2f}, {last_z:.2f}), distance={distance:.2f}, duration={duration}ms")
                
                task_context = getattr(self.controller, "current_task_description", "")
                self._queue_parallel_mcp_execution([summarized_command], task_context)

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

            tool_text = real_response.content[0].text
            base64_string = real_response.content[1].data
            print(f"📊 RUNTIME getBotStatus result:\n\n====\n{tool_text}\n====\n\n")
            
            # Save screenshot to images directory with timestamp
            timestamp = int(time.time())
            screenshot_path = f"{self.images_dir}/{timestamp}_screenshot.png"
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(base64_string))
            
            # Save latest screenshot for quick reference
            with open("latest_screenshot.png", "wb") as f:
                f.write(base64.b64decode(base64_string))
            
            # Log the data to trace.txt in append mode
            trace_data = f"📊 RUNTIME getBotStatus result:\n\n====\n{tool_text}\n====\n\n"
            trace_data += f"📊 pygame_actions: {pygame_actions}\n"
            trace_data += f"📊 mcp_actions: {mcp_actions}\n\n"
            
            # Check if trace.txt exists, if not print we're creating it
            trace_file_path = f"{self.current_dir}/trace.txt"
            file_exists = os.path.exists(trace_file_path)
            if not file_exists:
                print(f"Creating trace file at {trace_file_path}")
            
            with open(trace_file_path, "a") as f:
                f.write(trace_data)
                
            print(f"📊 pygame_actions: {pygame_actions}")
            print(f"📊 mcp_actions: {mcp_actions}")


        except Exception as e:
            print(f"❌ getBotStatus failed: {e}")

    def _convert_actions_to_mcp_format(self, pygame_actions):
        """Convert pygame WebSocket commands to MCP tool calls using shared ActionConverter."""
        # ✅ REFACTORED: Use shared ActionConverter to eliminate duplication
        from .action_converter import ActionConverter

        return ActionConverter.pygame_to_mcp_simple(pygame_actions)

    def start_data_collection_session(self, task_description: str) -> str:
        """Start a new data collection session."""
        pass
        # if not self.data_collector:
        #     print("⚠️ Data collection not enabled for this strategy.")
        #     return None

        # return self.data_collector.start_collection_session(task_description)

    def save_data_collection_session(self) -> str:
        """Save the current data collection session."""
        pass
        # if self.data_collector:
        #     return self.data_collector.save_session()
        # return None

    def cancel_data_collection_session(self) -> None:
        """Cancel the current data collection session."""
        # if self.data_collector:
        #     self.data_collector.cancel_session()
        # else:
        #  print("⚠️ No data collection session to cancel.")

    # def get_session_stats(self) -> Dict[str, Any]:
    #     """Get current session statistics."""
    #     if self.data_collector:
    #         return self.data_collector.get_session_stats()
    #     return {"status": "data_collection_disabled"}


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

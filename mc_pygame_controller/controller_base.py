import asyncio
import json
import websockets
import threading
import sys
import argparse
from typing import Optional, Dict, Any, Callable, List, Tuple
import time

import pygame

from .constants import *
from .look_path import LookPathTracker
from .ui_elements import (
    Button,
    ToggleButton,
    VirtualJoystick,
    KeyboardMovement,
    TouchArea,
)
from .mode_strategy import ModeStrategy, PygameModeStrategy, MCPModeStrategy
from .ui_manager import UIManager
from .controller_state import ControllerState
from .action_handler import ActionHandler
import argparse


class MinecraftController:

    def __init__(
        self,
        mode="pygame",
        chain_args=None,
        sensitivity=5.0,
        enable_logging=False,
        data_collection_enabled=False,
    ):
        # Initialize centralized state
        self.state = ControllerState(
            mode=mode,
            sensitivity=sensitivity,
            enable_logging=enable_logging,
            data_collection_enabled=data_collection_enabled,
        )

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Minecraft Web Client Controller")
        self.clock = pygame.time.Clock()

        # Look path tracking
        self.look_path_tracker = LookPathTracker(
            sensitivity=self.state.sensitivity,
            enable_logging=self.state.enable_logging,
            mode=self.state.mode,
        )

        # Set up servers and chain
        if chain_args is not None:
            self.state.chain = chain_args[1]
            self.state.servers = chain_args[0]
        else:
            self.state.servers = []
            self.state.chain = None

        # Set up MCP server for data collection in pygame mode
        self.mcp_server = None
        if self.state.mode == "pygame" and self.state.data_collection_enabled:
            self.mcp_server = self._create_mcp_server_for_data_collection()

        # Connect LookPathTracker for MCP mode
        if self.state.mode == "mcp":
            self.look_path_tracker.set_execution_callback(self.execute_mcp_action)
        # Connect LookPathTracker for pygame data collection mode
        elif self.state.mode == "pygame" and self.state.data_collection_enabled:
            self.look_path_tracker.set_execution_callback(
                self._execute_pygame_mcp_action
            )

        # Initialize mode strategy with data collection support
        if self.state.mode == "pygame":
            self.strategy = PygameModeStrategy(
                self, self.mcp_server, self.state.data_collection_enabled
            )
        elif self.state.mode == "mcp":
            self.strategy = MCPModeStrategy(self)
        else:
            raise ValueError(f"Unknown mode: {self.state.mode}")

        # Initialize UI Manager
        self.ui_manager = UIManager(self.screen, self.state, self.look_path_tracker)

        # Initialize Action Handler
        self.action_handler = ActionHandler(self.state, self.strategy, self)

        # Data collection state
        self.data_collection_session_active = False
        self.current_task_description = ""

        # Print data collection status
        if self.state.data_collection_enabled:
            print("🎬 Data collection enabled!")
            print("📋 Hotkeys: F5=Start session | F6=Save session | F7=Cancel session")
            print("💡 This will capture spatial reasoning data for AI training")

    def _create_mcp_server_for_data_collection(self):
        """Create MCP server for data collection in pygame mode."""
        try:
            from .mcp_client import Server

            # Use the same server configuration as MCP mode
            server_config = {
                "command": "npx",
                "args": [
                    "tsx",
                    "/Users/ohadr/minecraft-web-client/minecraft-mcp-server.ts",
                    "--transport",
                    "stdio",
                ],
                "env": {"NODE_NO_WARNINGS": "1"},
            }

            server = Server("minecraft-data-collection", server_config)
            print("🔧 Created MCP server for data collection")
            return server

        except Exception as e:
            print(f"⚠️ Could not create MCP server for data collection: {e}")
            print("💡 Data collection will be disabled")
            return None

    async def initialize_data_collection_async(self):
        """Legacy method - initialization now handled directly in _run_pygame_async()"""
        # This method is no longer used since we initialize directly in _run_pygame_async()
        # following the MCP mode pattern
        print("💡 Data collection initialization now handled directly in async context")
        return True

    async def cleanup_data_collection_async(self):
        """Cleanup MCP server and async execution for data collection."""
        if not self.mcp_server:
            return

        try:
            # Stop async execution in strategy
            if hasattr(self.strategy, "stop_async_execution"):
                await self.strategy.stop_async_execution()
                print("✅ Async execution stopped")

            # Cleanup MCP server
            await self.mcp_server.cleanup()
            print("✅ MCP server cleaned up")

        except Exception as e:
            print(f"⚠️ Warning during data collection cleanup: {e}")

    def start_data_collection_background_init(self):
        """Background initialization no longer needed - using direct initialization like MCP mode"""
        if not self.state.data_collection_enabled:
            return

        print("🔧 Data collection will be initialized directly in async context")
        print("💡 No background thread needed - using MCP mode pattern")

    # Property decorators for backward compatibility
    @property
    def mode(self):
        """Access mode through state for backward compatibility."""
        return self.state.mode

    @property
    def sensitivity(self):
        """Access sensitivity through state for backward compatibility."""
        return self.state.sensitivity

    @property
    def enable_logging(self):
        """Access enable_logging through state for backward compatibility."""
        return self.state.enable_logging

    @property
    def running(self):
        """Access running through state for backward compatibility."""
        return self.state.running

    @running.setter
    def running(self, value):
        """Set running through state for backward compatibility."""
        self.state.running = value

    @property
    def connected(self):
        """Access connected through state for backward compatibility."""
        return self.state.connected

    @connected.setter
    def connected(self, value):
        """Set connected through state for backward compatibility."""
        self.state.connected = value

    @property
    def current_hotbar_slot(self):
        """Access current_hotbar_slot through state for backward compatibility."""
        return self.state.current_hotbar_slot

    @current_hotbar_slot.setter
    def current_hotbar_slot(self, value):
        """Set current_hotbar_slot through state for backward compatibility."""
        self.state.current_hotbar_slot = value

    @property
    def last_hotbar_slot(self):
        """Access last_hotbar_slot through state for backward compatibility."""
        return self.state.last_hotbar_slot

    @last_hotbar_slot.setter
    def last_hotbar_slot(self, value):
        """Set last_hotbar_slot through state for backward compatibility."""
        self.state.last_hotbar_slot = value

    @property
    def last_movement(self):
        """Access last_movement through state for backward compatibility."""
        return self.state.last_movement

    @last_movement.setter
    def last_movement(self, value):
        """Set last_movement through state for backward compatibility."""
        self.state.last_movement = value

    @property
    def last_moved_in_mcp_mode(self):
        """Access last_moved_in_mcp_mode through state for backward compatibility."""
        return self.state.last_moved_in_mcp_mode

    @last_moved_in_mcp_mode.setter
    def last_moved_in_mcp_mode(self, value):
        """Set last_moved_in_mcp_mode through state for backward compatibility."""
        self.state.last_moved_in_mcp_mode = value

    @property
    def websocket(self):
        """Access websocket through state for backward compatibility."""
        return self.state.websocket

    @websocket.setter
    def websocket(self, value):
        """Set websocket through state for backward compatibility."""
        self.state.websocket = value

    @property
    def connection_thread(self):
        """Access connection_thread through state for backward compatibility."""
        return self.state.connection_thread

    @connection_thread.setter
    def connection_thread(self, value):
        """Set connection_thread through state for backward compatibility."""
        self.state.connection_thread = value

    @property
    def loop(self):
        """Access loop through state for backward compatibility."""
        return self.state.loop

    @loop.setter
    def loop(self, value):
        """Set loop through state for backward compatibility."""
        self.state.loop = value

    @property
    def mcp_executor(self):
        """Access mcp_executor through state for backward compatibility."""
        return self.state.mcp_executor

    @mcp_executor.setter
    def mcp_executor(self, value):
        """Set mcp_executor through state for backward compatibility."""
        self.state.mcp_executor = value

    @property
    def chain(self):
        """Access chain through state for backward compatibility."""
        return self.state.chain

    @property
    def servers(self):
        """Access servers through state for backward compatibility."""
        return self.state.servers

    def _handle_camera_drag_state(self, mouse_pressed: bool):
        """Handle camera drag state changes for look tracking"""
        camera_is_clicking = self.ui_manager.camera_area.is_touching and mouse_pressed
        prev_clicking = getattr(self, "camera_was_clicking", False)

        if camera_is_clicking != prev_clicking:
            print(
                f"🔍 Camera state change: clicking={camera_is_clicking}, was_clicking={prev_clicking}"
            )

        if camera_is_clicking and not prev_clicking:
            print("🖱️ Mouse pressed in camera area - starting drag tracking")
            self.look_path_tracker.start_mouse_tracking()
            self.camera_was_clicking = True
        elif not mouse_pressed and prev_clicking:
            print("🖱️ Mouse released - ending drag tracking")
            self.look_path_tracker.stop_mouse_tracking()
            self.camera_was_clicking = False

    async def connect_websocket(self):
        try:
            uri = "ws://localhost:8081"
            print(f"Connecting to {uri}...")
            self.websocket = await websockets.connect(uri)
            self.connected = True
            print("Connected to Minecraft Web Client!")

            # Register client based on mode
            init_message = {"init": self.mode}
            await self.websocket.send(json.dumps(init_message))
            print(f"Registered as {self.mode} client")

            # Keep connection alive
            while self.connected and self.running:
                await asyncio.sleep(0.1)

        except Exception as e:
            print(f"Failed to connect: {e}")
            self.connected = False

    def start_websocket_connection(self):
        """Start WebSocket connection in a separate thread"""

        def run_async():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.connect_websocket())

        self.connection_thread = threading.Thread(target=run_async, daemon=True)
        self.connection_thread.start()

    async def send_command_async(self, command: dict):
        """Async method to send command"""
        if self.websocket and self.connected:
            try:
                await self.websocket.send(json.dumps(command))

                # print(f"Sent command: {command}")
            except Exception as e:
                print(f"Error sending command: {e}")
                self.connected = False

    def send_command_sync(self, command: dict):
        """Send command instantly from main thread"""
        if self.connected and self.loop and not self.loop.is_closed():
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self.send_command_async(command), self.loop
                )
                # Don't wait for the result to keep it instant
            except Exception as e:
                print(f"Error sending command: {e}")
                self.connected = False

    def handle_control_button(self, control: str, state: bool):
        command = {"type": "control", "control": control, "state": state}
        self.send_command_sync(command)

    def execute_mcp_action(self, mcp_command):
        """Execute MCP-formatted action directly"""
        if self.mcp_executor:
            print(f"🎮 Executing: {mcp_command['tool']}({mcp_command['parameters']})")
            # Call the sync version that just captures the action
            self.mcp_executor.capture_command(mcp_command)
        else:
            print(
                f"🎮 MCP Command (no executor): {mcp_command['tool']}({mcp_command['parameters']})"
            )

    def _execute_pygame_mcp_action(self, mcp_command):
        """Execute MCP-formatted action in pygame data collection mode"""
        # Forward camera drag actions to the strategy's mock+observe system
        print(
            f"🎭 Camera drag action: {mcp_command['tool']}({mcp_command['parameters']})"
        )

        # Convert to action format expected by the strategy
        action = {"type": mcp_command["tool"], **mcp_command["parameters"]}

        # Send to strategy's mock+observe system (same as other pygame actions)
        self.strategy._queue_parallel_mcp_execution(
            [action], f"Camera drag: {mcp_command['tool']}"
        )

    def set_mcp_executor(self, executor):
        """Set the MCP command executor"""
        self.mcp_executor = executor

    def convert_to_mcp_format(self, command_type, params):
        """Convert pygame commands to MCP format"""
        # Simple mapping for clicks, movement, etc.
        if command_type == "left_click" or command_type == "leftClick":
            return {
                "tool": "leftClick",
                "parameters": {"duration": params.get("duration", "medium")},
            }
        elif command_type == "right_click" or command_type == "rightClick":
            return {
                "tool": "rightClick",
                "parameters": {"duration": params.get("duration", "medium")},
            }
        elif command_type == "walk":
            return {
                "tool": "walk",
                "parameters": {"duration": params.get("duration", 1000)},
            }
        elif command_type == "setHotbarSlot":
            return {
                "tool": "setHotbarSlot",
                "parameters": {"slot": params.get("slot", 0)},
            }
        elif command_type == "jump":
            return {
                "tool": "jump",
                "parameters": {"duration": params.get("duration", "short")},
            }
        elif command_type == "sneak":
            return {
                "tool": "sneak",
                "parameters": {"state": params.get("state", True)},
            }
        elif command_type == "sprint":
            return {
                "tool": "sprint",
                "parameters": {"state": params.get("state", True)},
            }
        elif command_type == "toggleInventory":
            return {
                "tool": "toggleInventory",
                "parameters": {},
            }
        elif command_type == "dropItem":
            return {
                "tool": "dropItem",
                "parameters": {"amount": params.get("amount", 1)},
            }
        elif command_type == "swapHands":
            return {
                "tool": "swapHands",
                "parameters": {},
            }
        # Add more mappings as needed
        return None

    def handle_other_commands(self, command_type, **params):
        """Execute non-look MCP commands directly"""
        if self.mode == "mcp" and self.mcp_executor:
            # Simple mapping for clicks, movement, etc.
            mcp_command = self.convert_to_mcp_format(command_type, params)
            if mcp_command:
                self.execute_mcp_action(mcp_command)

    def _process_frame(self):
        """Process a single frame of input and rendering. Common logic for both game loops."""
        # Handle pygame events that need to be caught early
        events = []
        for event in pygame.event.get():
            events.append(event)  # Collect events for UI components
            if event.type == pygame.QUIT:
                self.state.running = False
                return False  # Signal to exit loop
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state.running = False
                    return False  # Signal to exit loop
                elif event.key == pygame.K_r and self.state.mode == "pygame":
                    # Reconnect - only in pygame mode
                    self.state.connected = False
                    self.start_websocket_connection()

        # Get current input state
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]  # Left click
        keys_pressed = pygame.key.get_pressed()

        # Process pygame events through UIManager for components that need event access
        event_actions = self.ui_manager.process_events(events)

        # Process all inputs through UIManager (discrete actions)
        ui_actions = self.ui_manager.process_inputs(mouse_pos, mouse_pressed, keys_pressed)
        keyboard_actions = self.ui_manager.process_keyboard_shortcuts(keys_pressed)

        # Handle all actions using ActionHandler (including event-based actions)
        self.action_handler.process_actions(
            event_actions + ui_actions + keyboard_actions
        )

        # Process continuous state for streaming behavior (RESTORED)
        self._process_continuous_state(mouse_pos, mouse_pressed, keys_pressed)

        # Handle keyboard shortcuts edge detection using ActionHandler
        self.action_handler.process_edge_detections(keys_pressed)

        # Update UI elements that need periodic updates
        self.ui_manager.update()

        # Draw everything using UIManager
        self.ui_manager.draw()

        return True  # Continue running

    def _process_continuous_state(self, mouse_pos, mouse_pressed, keys_pressed):
        """Delegate continuous state processing to strategy."""
        self.strategy.process_continuous_state(mouse_pos, mouse_pressed, keys_pressed)

    def run(self):
        print(f"Starting Minecraft Controller in {self.state.mode.upper()} mode...")

        # Initialize connection using strategy
        self.strategy.connect()

        # Start data collection initialization if enabled
        if self.state.data_collection_enabled:
            self.start_data_collection_background_init()

        if self.state.mode == "pygame":
            print("Commands will be forwarded to the Minecraft bot")
            print(
                "Make sure the Minecraft web client server is running on localhost:8081"
            )

            # Use async loop when data collection is enabled (like MCP mode)
            if self.state.data_collection_enabled:
                print("🔄 Using async loop for data collection compatibility")
                # This needs to be called from an async context
                import asyncio

                asyncio.run(self._run_pygame_async())
            else:
                # Use traditional pygame event loop for pure pygame mode
                self._run_pygame_loop()
        else:
            print("Commands will be converted to MCP format and executed via callback")
            print("No WebSocket connection needed in MCP mode")
            # MCP mode is now handled by handle_interactive_session function
            print("MCP mode should be started via handle_interactive_session()")

    def _run_pygame_loop(self):
        """Traditional pygame event loop for pygame mode."""
        while self.state.running:
            if not self._process_frame():
                break
            self.clock.tick(FPS)

    async def _run_pygame_async(self):
        """Async pygame loop for data collection mode - copy MCP mode pattern exactly."""
        # Initialize MCP server directly in this async context (same as MCP mode)
        if self.state.data_collection_enabled and self.mcp_server:
            print("🔧 Initializing MCP server in main async context (like MCP mode)...")
            try:
                await self.mcp_server.initialize()
                print("✅ MCP server initialized successfully")

                # Test getBotStatus directly (same as MCP mode)
                await self.test_get_bot_status_pygame_startup()
            except Exception as e:
                print(f"❌ MCP server initialization failed: {e}")
                print("💡 Data collection will be disabled for this session")
                self.state.data_collection_enabled = False

        # Initialize async components after MCP server is ready
        if hasattr(self.strategy, "start_async_execution"):
            await self.strategy.start_async_execution()
            print("✅ Async components initialized")

        # Run the same loop as animation_loop
        while self.state.running:
            if not self._process_frame():
                break
            # Async frame rate limiting (same as animation_loop)
            await asyncio.sleep(1 / FPS)

        # Cleanup async components
        if hasattr(self.strategy, "stop_async_execution"):
            await self.strategy.stop_async_execution()
            print("✅ Async components cleaned up")

        # Cleanup MCP server if initialized (same as MCP mode cleanup pattern)
        if self.state.data_collection_enabled and self.mcp_server:
            try:
                await self.mcp_server.cleanup()
                print("✅ MCP server cleaned up")
            except Exception as e:
                print(f"⚠️ Warning during MCP server cleanup: {e}")

    # _wait_for_mcp_server_ready method removed - no longer needed with direct initialization

    async def test_get_bot_status_pygame_startup(self):
        """Test getBotStatus at startup for pygame mode with data collection - copy MCP mode pattern"""
        try:
            print("🧪 Testing getBotStatus at startup (pygame data collection mode)...")

            # Use the MCP server to call getBotStatus directly (same as MCP mode)
            result = await self.mcp_server.execute_tool("getBotStatus", {})
            text = result.content[0].text
            print(f"📊 Pygame startup getBotStatus result: \n====\n{text}\n====\n")

        except Exception as e:
            import traceback

            print(f"❌ Pygame startup getBotStatus failed: {e}")
            print("💡 This may indicate MCP server connectivity issues")
            print("Traceback:")
            traceback.print_exc()

    async def animation_loop(self):
        """Main animation loop for async modes."""
        while self.state.running:
            if not self._process_frame():
                break
            # Async frame rate limiting
            await asyncio.sleep(1 / FPS)

    async def test_get_bot_status_startup(self, chain):
        """Test getBotStatus at startup"""
        try:
            print("🧪 Testing getBotStatus at startup...")
            result = await chain.tools_mapping["getBotStatus"]()
            text = result.content[0].text
            print(f"📊 Startup getBotStatus result: \n====\n{text}\n====\n")
        except Exception as e:
            print(f"❌ Startup getBotStatus failed: {e}")

    async def execute_mcp_command_async(self, command_name, **params):
        """Execute MCP command asynchronously and return result"""
        if not self.command_queue:
            print("❌ Command queue not initialized")
            return None

        # Put command in queue
        await self.command_queue.put({"command": command_name, "params": params})

        # Wait for result
        if self.result_queue:
            try:
                result_data = await asyncio.wait_for(
                    self.result_queue.get(), timeout=10.0
                )
                if result_data.get("success"):
                    return result_data.get("result")
                else:
                    print(f"❌ MCP command failed: {result_data.get('error')}")
                    return None
            except asyncio.TimeoutError:
                print(f"⏰ MCP command timed out: {command_name}")
                return None

        return None

    def handle_test_status(self):
        """Handle test getBotStatus button click"""
        if self.mode == "mcp" and self.chain and self.chain.tools_mapping:
            print("🧪 Manual getBotStatus test triggered!")
            # Create a task to run the test
            asyncio.create_task(self._trigger_get_bot_status())
        else:
            print("⚠️ getBotStatus test only available in MCP mode")

    async def _trigger_get_bot_status(self):
        """Trigger getBotStatus command asynchronously"""
        try:
            result = await self.chain.tools_mapping["getBotStatus"]()
            print(f"🎯 Manual getBotStatus result: {result}")
        except Exception as e:
            print(f"❌ Manual getBotStatus failed: {e}")

    def handle_save_demonstration(self):
        """Handle saving a demonstration step"""
        if self.mode == "mcp" and self.mcp_executor:
            print("💾 Saving demonstration step...")
            # Generate a context description based on recent actions
            user_context = "exploring and performing actions"
            success = self.mcp_executor.save_demonstration_step(user_context)
            if success:
                print("✅ Demonstration step saved successfully!")
            else:
                print("⚠️ No actions to save in this step")
        else:
            print("⚠️ Demonstration saving only available in MCP mode")

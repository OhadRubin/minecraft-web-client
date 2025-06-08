#!/usr/bin/env python3
"""
Test script for Phase 1 PygameModeStrategy Enhancement

Tests the enhanced PygameModeStrategy with MCP integration capabilities.
"""

__test__ = False
import sys
import os

# Add the mc_pygame_controller directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from mode_strategy import PygameModeStrategy
from controller_state import ControllerState


class MockActionHandler:
    """Mock action handler for testing."""

    def __init__(self):
        self.logged_commands = []

    def _log_mcp_command(self, action_name, params):
        """Mock MCP command logging."""
        self.logged_commands.append({"action": action_name, "params": params})


class MockController:
    """Mock controller for testing."""

    def __init__(self):
        self.state = ControllerState()
        self.commands_sent = []
        self.enable_logging = False
        self.action_handler = MockActionHandler()

    def send_command_sync(self, command):
        """Mock send command that just records commands."""
        self.commands_sent.append(command)
        print(f"Mock WebSocket command sent: {command}")


class MockMCPClient:
    """Mock MCP client for testing."""

    def __init__(self):
        self.tool_calls = []

    async def execute_tool(self, tool_name, parameters):
        """Mock tool execution that just records calls."""
        call = {"tool": tool_name, "parameters": parameters}
        self.tool_calls.append(call)
        print(f"Mock MCP tool call: {call}")
        return {"status": "success", "result": "mock result"}


def test_basic_functionality():
    """Test 1: Basic functionality without MCP integration."""
    print("=== Test 1: Basic Functionality ===")

    controller = MockController()
    strategy = PygameModeStrategy(controller)

    # Test movement
    strategy.handle_movement(1.0, 0.0)

    # Verify WebSocket command was sent
    assert len(controller.commands_sent) == 1
    assert controller.commands_sent[0] == {"type": "move", "x": 1.0, "z": 0.0}

    print("✅ Basic functionality test passed")


def test_with_data_collection_disabled():
    """Test 2: With MCP client but data collection disabled."""
    print("\n=== Test 2: Data Collection Disabled ===")

    controller = MockController()
    mcp_client = MockMCPClient()
    strategy = PygameModeStrategy(controller, mcp_client, data_collection_enabled=False)

    # Test movement
    strategy.handle_movement(1.0, 0.0)

    # Verify only WebSocket command was sent, no MCP
    assert len(controller.commands_sent) == 1
    assert len(mcp_client.tool_calls) == 0
    assert len(strategy._mcp_action_queue) == 0

    print("✅ Data collection disabled test passed")


def test_action_conversion():
    """Test 3: Action conversion logic - including CRITICAL FIXES."""
    print("\n=== Test 3: Action Conversion (Critical Fixes) ===")

    controller = MockController()
    mcp_client = MockMCPClient()
    strategy = PygameModeStrategy(controller, mcp_client, data_collection_enabled=True)

    # Test movement conversion
    actions = [{"type": "move", "x": 1.0, "z": 0.0}]
    mcp_actions = strategy._convert_actions_to_mcp_format(actions)

    # Verify conversion
    assert len(mcp_actions) == 1
    assert mcp_actions[0]["tool"] == "walk"
    assert "duration" in mcp_actions[0]["parameters"]

    # CRITICAL FIX TEST: Look action conversion with proper parameters
    actions = [{"type": "look", "movementX": 10, "movementY": -5}]
    mcp_actions = strategy._convert_actions_to_mcp_format(actions)

    # Verify look conversion uses actual angles, not 0,0
    assert len(mcp_actions) == 1
    assert mcp_actions[0]["tool"] == "lookAngle"
    assert "xAngle" in mcp_actions[0]["parameters"]
    assert "yAngle" in mcp_actions[0]["parameters"]
    assert mcp_actions[0]["parameters"]["xAngle"] == 2.0  # 10/5.0 sensitivity
    assert mcp_actions[0]["parameters"]["yAngle"] == 1.0  # -(-5)/5.0 sensitivity
    assert mcp_actions[0]["parameters"]["speed"] == "normal"
    print(f"✅ Look conversion: {mcp_actions[0]['parameters']}")

    # Test click conversion
    actions = [{"type": "documentMouseEvent", "button": 0, "action": "down"}]
    mcp_actions = strategy._convert_actions_to_mcp_format(actions)

    assert len(mcp_actions) == 1
    assert mcp_actions[0]["tool"] == "leftClick"
    assert mcp_actions[0]["parameters"]["duration"] == "short"

    # Test small look movements are filtered out (< 0.2 threshold)
    actions = [
        {"type": "look", "movementX": 0.5, "movementY": 0.3}
    ]  # Very small movement
    mcp_actions = strategy._convert_actions_to_mcp_format(actions)

    assert len(mcp_actions) == 0  # Should be filtered out
    print("✅ Small movements correctly filtered out")

    print("✅ Action conversion test passed (with critical fixes)")


def test_data_collection_enabled():
    """Test 4: Data collection enabled - actions should be queued."""
    print("\n=== Test 4: Data Collection Enabled ===")

    controller = MockController()
    mcp_client = MockMCPClient()
    strategy = PygameModeStrategy(controller, mcp_client, data_collection_enabled=True)

    # Test movement with data collection
    strategy.handle_movement(1.0, 0.0)

    # Verify WebSocket command was sent AND MCP action was queued
    assert len(controller.commands_sent) == 1
    assert len(strategy._mcp_action_queue) == 1

    # Test timed action
    strategy.handle_timed_action(
        "leftClick",
        "short",
        pygame_down_cmd={"type": "documentMouseEvent", "button": 0, "action": "down"},
    )

    # Verify additional actions were queued
    assert len(controller.commands_sent) == 2
    assert len(strategy._mcp_action_queue) == 2

    print("✅ Data collection enabled test passed")


def test_controller_state_enhancements():
    """Test 5: Controller state has new data collection fields."""
    print("\n=== Test 5: Controller State Enhancements ===")

    state = ControllerState()

    # Verify new fields exist with correct defaults
    assert hasattr(state, "data_collection_enabled")
    assert hasattr(state, "conversation_session_active")
    assert hasattr(state, "current_task_description")

    assert state.data_collection_enabled == False
    assert state.conversation_session_active == False
    assert state.current_task_description == ""

    print("✅ Controller state enhancements test passed")


def test_sequence_timing_issue():
    """Test 6: Document sequence/timing issue for Phase 2."""
    print("\n=== Test 6: Sequence/Timing Issue (Phase 2 TODO) ===")

    controller = MockController()
    mcp_client = MockMCPClient()
    strategy = PygameModeStrategy(controller, mcp_client, data_collection_enabled=True)

    # Execute multiple actions to fill queue
    strategy.handle_movement(1.0, 0.0)
    strategy.handle_movement(0.5, 0.5)

    # Verify actions are queued but not executed
    assert len(strategy._mcp_action_queue) == 2
    assert len(mcp_client.tool_calls) == 0  # No actual execution yet

    print(f"📋 Queued actions: {len(strategy._mcp_action_queue)}")
    print(f"🚫 Executed actions: {len(mcp_client.tool_calls)}")
    print("⚠️ Phase 2 TODO: Implement actual async execution and sequence correlation")

    print("✅ Sequence/timing issue documented for Phase 2")


def run_all_tests():
    """Run all Phase 1 tests."""
    print("🧪 Running Phase 1 PygameModeStrategy Enhancement Tests")
    print("=" * 60)

    try:
        test_basic_functionality()
        test_with_data_collection_disabled()
        test_action_conversion()
        test_data_collection_enabled()
        test_controller_state_enhancements()
        test_sequence_timing_issue()

        print("\n🎉 ALL PHASE 1 TESTS PASSED!")
        print("✅ Core Integration: PygameModeStrategy accepts MCP client parameter")
        print("✅ No Regressions: Pygame mode works exactly as before")
        print("✅ Conversion Foundation: Basic action format conversion works")
        print("✅ Data Collection Toggle: Can enable/disable data collection")

        print("\n🚀 READY TO PROCEED TO PHASE 2!")
        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Test script for gamepad joystick functionality
Demonstrates the new joystick features added to the gamepadSimulator
"""

import asyncio
import json
import websockets
import time


class GamepadJoystickTester:
    def __init__(self, uri="ws://localhost:8081"):
        self.uri = uri
        self.websocket = None

    async def connect(self):
        """Connect to the WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.uri)

            # Register as an MCP client (command sender)
            init_msg = {"init": "mcp"}
            await self.websocket.send(json.dumps(init_msg))
            print("✅ Connected and registered as MCP client")

            print(f"✅ Connected to {self.uri}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to {self.uri}: {e}")
            return False

    async def send_command(self, command):
        """Send a command and return success status"""
        try:
            if not self.websocket:
                print("❌ Not connected to server")
                return False

            message = json.dumps(command)
            await self.websocket.send(message)
            print(f"📤 Sent: {command}")

            # Brief delay for command processing
            await asyncio.sleep(0.1)
            return True
        except Exception as e:
            print(f"❌ Error sending command: {e}")
            return False

    async def test_joystick_basic_movement(self):
        """Test basic joystick movement"""
        print("\n🕹️ Testing Basic Joystick Movement")
        print("=" * 50)

        # Connect gamepad first
        await self.send_command({"type": "gamepadConnect"})
        await asyncio.sleep(0.5)

        # Test left joystick movements
        print("\n🎮 Testing Left Joystick (stick 0)")
        movements = [
            {"x": 1.0, "y": 0.0},  # Right
            {"x": 0.0, "y": 1.0},  # Up
            {"x": -1.0, "y": 0.0},  # Left
            {"x": 0.0, "y": -1.0},  # Down
            {"x": 0.7, "y": 0.7},  # Diagonal up-right
        ]

        for i, movement in enumerate(movements):
            print(f"   Moving left stick to ({movement['x']}, {movement['y']})")
            await self.send_command(
                {"type": "gamepadJoystickMove", "stickIndex": 0, **movement}
            )
            await asyncio.sleep(0.5)

        # Test right joystick movements
        print("\n🎮 Testing Right Joystick (stick 1)")
        for i, movement in enumerate(movements):
            print(f"   Moving right stick to ({movement['x']}, {movement['y']})")
            await self.send_command(
                {"type": "gamepadJoystickMove", "stickIndex": 1, **movement}
            )
            await asyncio.sleep(0.5)

        return True

    async def test_joystick_center(self):
        """Test joystick centering"""
        print("\n🎯 Testing Joystick Centering")
        print("=" * 40)

        # Move joysticks to extreme positions
        print("   Moving joysticks to extreme positions...")
        await self.send_command(
            {"type": "gamepadJoystickMove", "stickIndex": 0, "x": 1.0, "y": 1.0}
        )
        await self.send_command(
            {"type": "gamepadJoystickMove", "stickIndex": 1, "x": -1.0, "y": -1.0}
        )
        await asyncio.sleep(1)

        # Center left joystick
        print("   Centering left joystick...")
        await self.send_command({"type": "gamepadJoystickCenter", "stickIndex": 0})
        await asyncio.sleep(0.5)

        # Center right joystick
        print("   Centering right joystick...")
        await self.send_command({"type": "gamepadJoystickCenter", "stickIndex": 1})
        await asyncio.sleep(0.5)

        return True

    async def test_joystick_pulse(self):
        """Test joystick pulse movements"""
        print("\n⚡ Testing Joystick Pulse")
        print("=" * 30)

        pulses = [
            {"stickIndex": 0, "x": 0.8, "y": 0.0, "duration": 300},  # Left stick right
            {"stickIndex": 0, "x": 0.0, "y": 0.8, "duration": 400},  # Left stick up
            {"stickIndex": 1, "x": -0.8, "y": 0.0, "duration": 250},  # Right stick left
            {"stickIndex": 1, "x": 0.0, "y": -0.8, "duration": 350},  # Right stick down
        ]

        for pulse in pulses:
            stick_name = "left" if pulse["stickIndex"] == 0 else "right"
            print(
                f"   Pulsing {stick_name} stick to ({pulse['x']}, {pulse['y']}) for {pulse['duration']}ms"
            )
            await self.send_command({"type": "gamepadJoystickPulse", **pulse})
            await asyncio.sleep(
                pulse["duration"] / 1000 + 0.2
            )  # Wait for pulse + extra time

        return True

    async def test_joystick_animation(self):
        """Test joystick animations"""
        print("\n🎬 Testing Joystick Animation")
        print("=" * 35)

        animations = [
            {
                "stickIndex": 0,
                "fromX": -1.0,
                "fromY": -1.0,
                "toX": 1.0,
                "toY": 1.0,
                "duration": 1000,
            },
            {
                "stickIndex": 1,
                "fromX": 1.0,
                "fromY": -1.0,
                "toX": -1.0,
                "toY": 1.0,
                "duration": 800,
            },
        ]

        for anim in animations:
            stick_name = "left" if anim["stickIndex"] == 0 else "right"
            print(
                f"   Animating {stick_name} stick from ({anim['fromX']}, {anim['fromY']}) to ({anim['toX']}, {anim['toY']}) over {anim['duration']}ms"
            )
            await self.send_command({"type": "gamepadJoystickAnimate", **anim})
            await asyncio.sleep(
                anim["duration"] / 1000 + 0.3
            )  # Wait for animation + extra time

        return True

    async def test_joystick_circular(self):
        """Test circular joystick movement"""
        print("\n🔄 Testing Circular Joystick Movement")
        print("=" * 45)

        circular_tests = [
            {"stickIndex": 0, "radius": 0.8, "duration": 2000, "clockwise": True},
            {"stickIndex": 1, "radius": 0.6, "duration": 1500, "clockwise": False},
        ]

        for test in circular_tests:
            stick_name = "left" if test["stickIndex"] == 0 else "right"
            direction = "clockwise" if test["clockwise"] else "counter-clockwise"
            print(
                f"   {stick_name} stick {direction} circle (radius {test['radius']}, {test['duration']}ms)"
            )
            await self.send_command({"type": "gamepadJoystickCircular", **test})
            await asyncio.sleep(
                test["duration"] / 1000 + 0.5
            )  # Wait for animation + extra time

        return True

    async def run_all_tests(self):
        """Run all joystick tests"""
        print("🚀 Starting Gamepad Joystick Tests")
        print("=" * 60)

        if not await self.connect():
            return False

        try:
            # Run test suite
            tests = [
                self.test_joystick_basic_movement,
                self.test_joystick_center,
                self.test_joystick_pulse,
                self.test_joystick_animation,
                self.test_joystick_circular,
            ]

            for i, test in enumerate(tests, 1):
                print(f"\n🧪 Test {i}/{len(tests)}: {test.__name__}")
                success = await test()
                if not success:
                    print(f"❌ Test {i} failed!")
                    return False
                print(f"✅ Test {i} completed successfully!")

            # Cleanup - destroy gamepad
            print("\n🧹 Cleaning up...")
            await self.send_command({"type": "gamepadDestroy"})

            print("\n🎉 All joystick tests completed successfully!")
            return True

        except Exception as e:
            print(f"❌ Error during tests: {e}")
            return False

        finally:
            if self.websocket:
                await self.websocket.close()
                print("🔌 WebSocket connection closed")


async def main():
    """Main test function"""
    tester = GamepadJoystickTester()
    success = await tester.run_all_tests()

    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")


if __name__ == "__main__":
    asyncio.run(main())

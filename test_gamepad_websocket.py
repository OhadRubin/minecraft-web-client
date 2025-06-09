#!/usr/bin/env python3
"""
Test script for Gamepad Simulator WebSocket Commands
Tests the gamepad integration via WebSocket commands.
"""

import asyncio
import websockets
import json
import argparse
from typing import Dict, Any


class GamepadTester:
    def __init__(self, host: str = "localhost", port: int = 8081):
        self.host = host
        self.port = port
        self.ws_url = f"ws://{host}:{port}"
        self.websocket = None

    async def connect(self):
        """Connect to the WebSocket server"""
        try:
            print(f"🔌 Connecting to WebSocket server at {self.ws_url}")
            self.websocket = await websockets.connect(self.ws_url)

            # Register as an MCP client (command sender)
            init_msg = {"init": "pygame"}
            await self.websocket.send(json.dumps(init_msg))
            print("✅ Connected and registered as MCP client")
            return True

        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False

    async def send_command(self, command: Dict[str, Any]) -> bool:
        """Send a command and handle any response"""
        try:
            command_json = json.dumps(command)
            print(f"📤 Sending: {command_json}")

            await self.websocket.send(command_json)

            # Try to receive any immediate response (with timeout)
            try:
                response = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                print(f"📥 Response: {response}")
            except asyncio.TimeoutError:
                print("📥 No immediate response (normal)")

            return True

        except Exception as e:
            print(f"❌ Error sending command: {e}")
            return False

    async def press_button(self, button_index: int, duration: int = 100):
        """Press a specific gamepad button"""
        print(f"\n🔘 Pressing button {button_index} for {duration}ms")
        
        # Connect gamepad
        # await self.send_command({"type": "gamepadConnect"})
        # await asyncio.sleep(1)  # Wait for connection
        
        # Press the button
        await self.send_command({
            "type": "gamepadButtonPress",
            "buttonIndex": button_index,
            "duration": duration
        })
        
        # await asyncio.sleep(1)
        
        # Cleanup
        # await self.send_command({"type": "gamepadDestroy"})

    async def disconnect(self):
        """Close the WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            print("🔌 Disconnected from WebSocket server")


async def main():
    parser = argparse.ArgumentParser(description="Test Gamepad WebSocket Commands")
    parser.add_argument("--host", default="localhost", help="WebSocket server host")
    parser.add_argument("--port", type=int, default=8081, help="WebSocket server port")
    parser.add_argument("--button", type=int, default=0, help="Button index to press (0-16)")
    parser.add_argument("--duration", type=int, default=100, help="Button press duration in ms")

    args = parser.parse_args()

    tester = GamepadTester(args.host, args.port)

    # Connect to server
    connected = await tester.connect()
    if not connected:
        print("❌ Could not connect to WebSocket server")
        print("💡 Make sure the server is running on port 8081")
        return

    try:
        # Press the specified button
        await tester.press_button(args.button, args.duration)
        print("\n✅ Command executed successfully")

    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        await tester.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

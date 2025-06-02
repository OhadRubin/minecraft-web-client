#!/usr/bin/env python3
"""
Simple test script to verify WebSocket connection to Minecraft Web Client
Run this before using the pygame controller to ensure everything is working.
"""

import asyncio
import json
import websockets
import sys


async def test_connection():
    uri = "ws://localhost:8081"

    try:
        print(f"Testing connection to {uri}...")
        async with websockets.connect(uri) as ws:
            print("✅ Successfully connected to WebSocket server!")

            # Test sending a simple movement command
            test_command = {"type": "move", "x": 0, "z": 0}
            await ws.send(json.dumps(test_command))
            print("✅ Successfully sent test command")

            # Test camera look command
            look_command = {"type": "look", "movementX": 0, "movementY": 0}
            await ws.send(json.dumps(look_command))
            print("✅ Successfully sent look command")

            # Test the new lookTouch command
            touch_command = {
                "type": "lookTouch",
                "currentX": 100,
                "lastX": 90,
                "currentY": 100,
                "lastY": 95,
            }
            await ws.send(json.dumps(touch_command))
            print("✅ Successfully sent lookTouch command")

            print("\n🎉 All tests passed! The pygame controller should work properly.")
            print("You can now run: python pygame_controller.py")

    except ConnectionRefusedError:
        print("❌ Connection refused!")
        print("Make sure the Minecraft web client server is running.")
        print("Run: node server.js")
        return False

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

    return True


async def main():
    print("Minecraft Web Client - Connection Test")
    print("=====================================\n")

    success = await test_connection()

    if not success:
        print("\n🔧 Troubleshooting:")
        print("1. Make sure you're in the minecraft-web-client directory")
        print("2. Run: node server.js")
        print("3. Open the web client in your browser")
        print("4. Make sure you're connected to a world/server in the web client")
        print("5. Try running this test again")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

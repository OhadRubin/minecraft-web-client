import argparse
from mc_pygame_controller import MinecraftController

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Minecraft Web Client Controller")
    parser.add_argument(
        "--mcp",
        action="store_true",
        help="Run in MCP mode (commands sent directly to bot) instead of pygame mode (commands forwarded to bot)",
    )
    args = parser.parse_args()

    # Determine mode
    mode = "mcp" if args.mcp else "pygame"

    # Create and run controller
    controller = MinecraftController(mode=mode)
    controller.run()

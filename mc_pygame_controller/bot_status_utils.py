"""
Bot Status Processing Utilities - Eliminates getBotStatus Code Duplication

This module centralizes the complex getBotStatus parsing logic that was duplicated in:
- interface.py:51-78 (28 lines of nested parsing)
- chain.py:282-309 (28 lines of identical parsing)

Key Features:
- Single source of truth for complex multimodal parsing
- Consistent error handling patterns
- Reusable for different contexts (executor vs generator)
"""

from typing import Dict, Optional, List, Any


class BotStatusProcessor:
    """Centralized processor for getBotStatus responses with complex parsing logic."""

    @staticmethod
    async def get_and_process_status(
        tools_mapping: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Execute getBotStatus and extract the complex parsing logic.

        This method encapsulates the 28-line duplication found in both interface.py and chain.py.

        Args:
            tools_mapping: Dictionary containing tool functions including "getBotStatus"

        Returns:
            Dict with parsed status data or None if processing failed
            Format: {
                "position_line": str,
                "looking_at_line": str | None,
                "raw_status_text": str,
                "lines": List[str]
            }
        """
        try:
            print("👁️ Getting updated view after look command...")
            status_result = await tools_mapping["getBotStatus"]()

            if (
                status_result
                and isinstance(status_result, dict)
                and "content" in status_result
            ):

                status_content = status_result["content"]

                if isinstance(status_content, list) and len(status_content) > 0:
                    status_text = status_content[0].get("text", "")

                    if status_text:
                        # Complex parsing logic - single source of truth
                        lines = status_text.split("\n")
                        position_line = lines[0] if lines else ""

                        # Extract looking_at_line with consistent logic
                        looking_at_line = [
                            line for line in lines if "Looking at:" in line
                        ]

                        return {
                            "position_line": position_line,
                            "looking_at_line": (
                                looking_at_line[0] if looking_at_line else None
                            ),
                            "raw_status_text": status_text,
                            "lines": lines,
                        }

        except Exception as e:
            print(f"⚠️ Could not get updated status after look: {e}")

        return None

    @staticmethod
    def print_status(status_data: Optional[Dict[str, Any]]) -> None:
        """
        Print formatted status using consistent formatting.

        Args:
            status_data: Parsed status data from get_and_process_status()
        """
        if status_data:
            print(f"🎯 {status_data['position_line']}")
            if status_data.get("looking_at_line"):
                print(f"🎯 {status_data['looking_at_line']}")

    @staticmethod
    async def get_status_after_look(tools_mapping: Dict[str, Any]) -> None:
        """
        Convenience method that combines getBotStatus execution and printing.

        This replaces the entire duplicated block in both interface.py and chain.py.

        Args:
            tools_mapping: Dictionary containing tool functions
        """
        if "getBotStatus" not in tools_mapping:
            return

        status_data = await BotStatusProcessor.get_and_process_status(tools_mapping)
        BotStatusProcessor.print_status(status_data)

    @staticmethod
    def extract_position_info(status_text: str) -> Dict[str, Any]:
        """
        Extract position information from raw status text.

        Useful for additional processing beyond just printing.

        Args:
            status_text: Raw status text from getBotStatus

        Returns:
            Dict with extracted position data
        """
        if not status_text:
            return {}

        lines = status_text.split("\n")
        position_line = lines[0] if lines else ""
        looking_at_lines = [line for line in lines if "Looking at:" in line]

        return {
            "position_line": position_line,
            "looking_at_line": looking_at_lines[0] if looking_at_lines else None,
            "all_lines": lines,
            "looking_at_count": len(looking_at_lines),
        }

    @staticmethod
    async def enhanced_status_check(
        tools_mapping: Dict[str, Any], context: str = "look command"
    ) -> Optional[Dict[str, Any]]:
        """
        Enhanced version with additional context and error handling.

        Args:
            tools_mapping: Tools mapping dictionary
            context: Context string for logging (e.g., "look command", "movement")

        Returns:
            Enhanced status data with additional metadata
        """
        if "getBotStatus" not in tools_mapping:
            print(f"⚠️ getBotStatus not available for {context}")
            return None

        try:
            print(f"👁️ Getting updated view after {context}...")
            status_result = await tools_mapping["getBotStatus"]()

            # Use the core processing logic
            if (
                status_result
                and isinstance(status_result, dict)
                and "content" in status_result
            ):

                status_content = status_result["content"]

                if isinstance(status_content, list) and len(status_content) > 0:
                    status_text = status_content[0].get("text", "")

                    if status_text:
                        extracted = BotStatusProcessor.extract_position_info(
                            status_text
                        )

                        # Add metadata
                        extracted.update(
                            {
                                "context": context,
                                "success": True,
                                "raw_result": status_result,
                            }
                        )

                        return extracted

            # If we get here, parsing failed
            return {
                "context": context,
                "success": False,
                "error": "Could not parse status result",
                "raw_result": status_result,
            }

        except Exception as e:
            print(f"⚠️ Could not get updated status after {context}: {e}")
            return {
                "context": context,
                "success": False,
                "error": str(e),
                "raw_result": None,
            }


# Validation helper for testing consistency
def validate_status_processing():
    """
    Validate that the status processing produces consistent results.
    This helps ensure refactoring doesn't break the parsing logic.
    """
    # Mock status text matching the actual format
    test_status_text = """Position: x=123.45, y=64.0, z=678.90
Health: 20/20
Hunger: 20/20
Looking at: minecraft:stone at (125, 65, 680)
Inventory: 36 slots, 12 items"""

    # Test extraction
    extracted = BotStatusProcessor.extract_position_info(test_status_text)

    assert "Position:" in extracted["position_line"]
    assert "Looking at:" in extracted["looking_at_line"]
    assert len(extracted["all_lines"]) == 5
    assert extracted["looking_at_count"] == 1

    print("✅ Status processing validation passed!")
    print(f"   Position: {extracted['position_line']}")
    print(f"   Looking at: {extracted['looking_at_line']}")


if __name__ == "__main__":
    validate_status_processing()

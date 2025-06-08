import asyncio
import time
from typing import Dict, Callable
from dataclasses import dataclass

# Leverage existing infrastructure!
try:
    from .mcp_client import Server
except ImportError:
    from mcp_client import Server


@dataclass
class MCPActionRequest:
    """Represents a queued MCP action."""

    tool: str
    parameters: dict
    sequence_id: str
    timestamp: float


@dataclass
class MCPActionResponse:
    """Represents a completed MCP action response."""

    tool: str
    content: str
    screenshot: str = None
    timestamp: float = None
    sequence_id: str = None
    tool_call_id: str = None


class AsyncMCPExecutor:
    """Executes MCP tools asynchronously using existing Server infrastructure."""

    def __init__(self, mcp_server: Server):  # Accept Server directly
        self.mcp_server = mcp_server
        self.execution_queue = asyncio.Queue()
        self.response_handlers: Dict[str, Callable] = {}
        self.background_task = None
        print(f"🔧 AsyncMCPExecutor using existing Server infrastructure")

    async def start_background_execution(self):
        """Start the background task that processes MCP actions."""
        if self.background_task is None:
            self.background_task = asyncio.create_task(self._background_executor())
            print("🚀 AsyncMCPExecutor background task started")

    async def stop_background_execution(self):
        """✅ Fix Bug #16: Stop the background execution task with proper cleanup."""
        if self.background_task:
            self.background_task.cancel()
            try:
                await self.background_task
            except asyncio.CancelledError:
                pass
            self.background_task = None

            # Clean up all response handlers to prevent memory leaks
            self.cleanup_all_handlers()

            print("🛑 AsyncMCPExecutor background task stopped with cleanup")

    async def queue_mcp_action(self, action_request: MCPActionRequest) -> None:
        """Queue an MCP action for background execution."""
        await self.execution_queue.put(action_request)
        print(
            f"📋 Queued MCP action: {action_request.tool} (sequence: {action_request.sequence_id})"
        )

    def register_response_handler(self, sequence_id: str, handler: Callable) -> None:
        """Register a callback for when a sequence completes."""
        self.response_handlers[sequence_id] = handler
        print(f"📞 Registered response handler for sequence: {sequence_id}")

    def cleanup_response_handler(self, sequence_id: str) -> None:
        """✅ Fix Bug #13: Clean up response handler to prevent memory leak."""
        if sequence_id in self.response_handlers:
            del self.response_handlers[sequence_id]
            print(f"🧹 Cleaned up response handler for sequence: {sequence_id}")

    def cleanup_all_handlers(self) -> None:
        """Clean up all response handlers."""
        handler_count = len(self.response_handlers)
        self.response_handlers.clear()
        if handler_count > 0:
            print(f"🧹 Cleaned up {handler_count} response handlers")

    async def _background_executor(self) -> None:
        """Background task that processes queued MCP actions."""
        print("⚡ Background MCP executor started")
        while True:
            try:
                # Get next action from queue
                action_request = await self.execution_queue.get()
                print(f"🔄 Executing MCP tool: {action_request.tool}")

                # Execute MCP tool using existing infrastructure
                response = await self._execute_mcp_tool(action_request)

                # Call response handler if registered
                if action_request.sequence_id in self.response_handlers:
                    handler = self.response_handlers[action_request.sequence_id]
                    handler(response)

                    # ✅ Fix Bug #13: Clean up handler after use to prevent memory leak
                    # Note: Only remove after sequence is complete, not after every response
                    # (Sequence completion will be handled by the handler itself)
                else:
                    print(
                        f"⚠️ No handler registered for sequence: {action_request.sequence_id}"
                    )

            except asyncio.CancelledError:
                print("🛑 Background executor cancelled")
                break
            except Exception as e:
                print(f"⚠️ MCP execution error: {e}")

    async def _execute_mcp_tool(self, action_request: MCPActionRequest):
        """Execute using existing Server.execute_tool() - much simpler!"""
        try:
            # Use existing proven execution with retries
            result = await self.mcp_server.execute_tool(
                action_request.tool, action_request.parameters
            )

            # ✅ Fix Bug #16 & #19: Handle CallToolResult serialization properly
            content = ""
            if hasattr(result, "content"):
                # Handle MCP CallToolResult format
                if isinstance(result.content, list):
                    # Multimodal content - extract text parts
                    text_parts = []
                    for item in result.content:
                        if (
                            hasattr(item, "type")
                            and item.type == "text"
                            and hasattr(item, "text")
                        ):
                            text_parts.append(item.text)
                    content = (
                        "\n".join(text_parts) if text_parts else str(result.content)
                    )
                else:
                    content = str(result.content)
            elif isinstance(result, dict):
                content = result.get("content", str(result))
            else:
                content = str(result)

            # ✅ Fix Bug #14: Use consistent tool call ID format
            tool_call_id = f"call_{action_request.sequence_id}_{action_request.tool}_{int(action_request.timestamp * 1000) % 1000000}"

            return {
                "tool": action_request.tool,
                "content": content,  # Properly serialized content
                "timestamp": time.time(),
                "sequence_id": action_request.sequence_id,
                "tool_call_id": tool_call_id,
            }

        except Exception as e:
            # ✅ Fix Bug #18: Notify sequence tracker of failure
            print(f"❌ MCP tool {action_request.tool} failed: {str(e)}")
            tool_call_id = f"call_{action_request.sequence_id}_{action_request.tool}_{int(action_request.timestamp * 1000) % 1000000}"

            return {
                "tool": action_request.tool,
                "content": f"Error: {str(e)}",
                "timestamp": time.time(),
                "sequence_id": action_request.sequence_id,
                "tool_call_id": tool_call_id,
                "error": True,  # Mark as error for sequence tracker
            }

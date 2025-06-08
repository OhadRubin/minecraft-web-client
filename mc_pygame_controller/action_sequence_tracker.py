import time
import json
from typing import Dict, List, Any
from dataclasses import dataclass, field

# Leverage existing chain infrastructure!
try:
    from .chain import PygameMCPAsyncMessageChain
except ImportError:
    from chain import PygameMCPAsyncMessageChain


@dataclass
class ActionSequence:
    """Tracks a sequence of related pygame actions and their MCP responses."""

    sequence_id: str
    pygame_actions: List[Dict[str, Any]]
    task_context: str
    start_time: float
    end_time: float = 0.0
    mcp_responses: List[dict] = field(default_factory=list)
    status: str = "pending"  # pending, executing, completed, failed
    expected_responses: int = 1  # Expected number of MCP responses


class ActionSequenceTracker:
    """Tracks sequences of pygame actions for correlation with MCP responses."""

    def __init__(self):
        self.current_sequence_id = 0
        self.active_sequences: Dict[str, ActionSequence] = {}

    def start_sequence(
        self,
        pygame_actions: List[Dict[str, Any]],
        task_context: str = "",
        expected_responses: int = None,
    ) -> str:
        """Start tracking a new action sequence."""
        # ✅ Fix Bug #12: Add microseconds to prevent ID collision
        sequence_id = f"seq_{self.current_sequence_id}_{int(time.time())}_{int(time.time() * 1000000) % 1000000}"
        self.current_sequence_id += 1

        # Calculate expected responses if not provided
        if expected_responses is None:
            expected_responses = (
                len(pygame_actions) + 1
            )  # +1 for getBotStatus (fallback)

        sequence = ActionSequence(
            sequence_id=sequence_id,
            pygame_actions=pygame_actions.copy(),
            task_context=task_context,
            start_time=time.time(),
            expected_responses=expected_responses,
        )

        self.active_sequences[sequence_id] = sequence
        print(
            f"🎬 Started tracking sequence {sequence_id} with {len(pygame_actions)} pygame actions, expecting {expected_responses} MCP responses"
        )
        return sequence_id

    def add_mcp_response(self, sequence_id: str, response: dict) -> None:
        """Add an MCP response to the sequence."""
        if sequence_id in self.active_sequences:
            self.active_sequences[sequence_id].mcp_responses.append(response)
            sequence = self.active_sequences[sequence_id]
            print(
                f"📥 Added MCP response to sequence {sequence_id}: {response.get('tool', 'unknown')} (total: {len(sequence.mcp_responses)})"
            )
        else:
            print(f"⚠️ Cannot add response to unknown sequence: {sequence_id}")

    def complete_sequence(self, sequence_id: str) -> ActionSequence:
        """Mark sequence as completed and return the data."""
        if sequence_id in self.active_sequences:
            sequence = self.active_sequences[sequence_id]
            sequence.status = "completed"
            sequence.end_time = time.time()

            duration = sequence.end_time - sequence.start_time
            print(
                f"✅ Completed sequence {sequence_id}: {len(sequence.pygame_actions)} actions, {len(sequence.mcp_responses)} responses, {duration:.2f}s"
            )

            # Remove from active tracking
            del self.active_sequences[sequence_id]
            return sequence

        print(f"⚠️ Cannot complete unknown sequence: {sequence_id}")
        return None

    def get_active_sequences(self) -> Dict[str, ActionSequence]:
        """Get all currently active sequences."""
        return self.active_sequences.copy()

    def cleanup_old_sequences(self, max_age_seconds: float = 300.0) -> None:
        """Clean up sequences older than max_age_seconds."""
        current_time = time.time()
        to_remove = []

        for seq_id, sequence in self.active_sequences.items():
            if current_time - sequence.start_time > max_age_seconds:
                to_remove.append(seq_id)

        for seq_id in to_remove:
            sequence = self.active_sequences[seq_id]
            print(
                f"🗑️ Cleaning up old sequence {seq_id} (age: {current_time - sequence.start_time:.1f}s)"
            )
            del self.active_sequences[seq_id]

        if to_remove:
            print(f"🧹 Cleaned up {len(to_remove)} old sequences")

    def get_sequence_status(self, sequence_id: str) -> str:
        """Get the status of a specific sequence."""
        if sequence_id in self.active_sequences:
            return self.active_sequences[sequence_id].status
        return "unknown"

    def update_sequence_status(self, sequence_id: str, status: str) -> None:
        """Update the status of a sequence."""
        if sequence_id in self.active_sequences:
            old_status = self.active_sequences[sequence_id].status
            self.active_sequences[sequence_id].status = status
            print(f"🔄 Updated sequence {sequence_id} status: {old_status} → {status}")
        else:
            print(f"⚠️ Cannot update status for unknown sequence: {sequence_id}")

    def get_sequence_summary(self, sequence_id: str) -> Dict:
        """Get a summary of a sequence."""
        if sequence_id in self.active_sequences:
            sequence = self.active_sequences[sequence_id]
            return {
                "sequence_id": sequence_id,
                "status": sequence.status,
                "pygame_actions": len(sequence.pygame_actions),
                "mcp_responses": len(sequence.mcp_responses),
                "duration": time.time() - sequence.start_time,
                "task_context": sequence.task_context,
            }
        return {"sequence_id": sequence_id, "status": "unknown"}

    def get_all_summaries(self) -> List[Dict]:
        """Get summaries of all active sequences."""
        return [
            self.get_sequence_summary(seq_id) for seq_id in self.active_sequences.keys()
        ]

    def build_conversation_chain(
        self, sequence: ActionSequence
    ) -> PygameMCPAsyncMessageChain:
        """Convert completed sequence to PygameMCPAsyncMessageChain format."""
        if not sequence:
            print(f"⚠️ Cannot build chain for None sequence")
            return None

        # Build chain using existing sophisticated infrastructure
        chain = PygameMCPAsyncMessageChain()

        # Add user task request
        task_content = sequence.task_context or "Perform spatial reasoning task"
        chain = chain.user(task_content)

        # Add assistant response with tool calls
        tool_calls = self._convert_pygame_to_tool_calls(
            sequence.pygame_actions, sequence.sequence_id
        )
        chain = chain.bot(
            content="I'll perform these spatial reasoning actions.",
            tool_calls=tool_calls,
        )

        # Add tool responses
        for response in sequence.mcp_responses:
            chain = chain.tool(
                content=response.get("content", ""),
                tool_call_id=response.get("tool_call_id", ""),
                name=response.get("tool", ""),
            )

        print(f"🔗 Built conversation chain with {len(chain.messages)} messages")
        return chain

    def _convert_pygame_to_tool_calls(self, pygame_actions, sequence_id):
        """Convert pygame actions to OpenAI tool call format using shared ActionConverter."""
        # ✅ REFACTORED: Use shared ActionConverter to eliminate duplication
        from .action_converter import ActionConverter

        return ActionConverter.pygame_to_openai_tools(pygame_actions, sequence_id)

    def is_sequence_complete(
        self, sequence_id: str, expected_responses: int = None
    ) -> bool:
        """Check if sequence has received all expected responses."""
        if sequence_id not in self.active_sequences:
            return False

        sequence = self.active_sequences[sequence_id]

        # Use stored expected responses count
        if expected_responses is None:
            expected_responses = sequence.expected_responses

        # Only complete when we have all expected responses
        is_complete = len(sequence.mcp_responses) >= expected_responses

        if is_complete:
            print(
                f"🎯 Sequence {sequence_id} complete: {len(sequence.mcp_responses)}/{expected_responses} responses"
            )

        return is_complete

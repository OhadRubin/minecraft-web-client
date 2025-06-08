import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List


class DataCollectionController:
    """High-level controller for spatial reasoning data collection."""

    def __init__(self, output_dir: str = "collected_trajectories"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.current_session: Optional[Dict[str, Any]] = None
        self.session_conversations: List[Dict[str, Any]] = []

    def start_collection_session(
        self, task_description: str, session_name: str = None
    ) -> str:
        """Start a new data collection session."""
        session_id = session_name or f"session_{int(time.time())}"

        self.current_session = {
            "session_id": session_id,
            "task_description": task_description,
            "start_time": time.time(),
            "conversations": [],
            "status": "active",
        }

        self.session_conversations = []

        print(f"🎬 Started collection session: {session_id}")
        print(f"📋 Task: {task_description}")
        return session_id

    def add_completed_sequence(self, completed_conversation: Dict[str, Any]) -> None:
        """Add a completed conversation to the current session."""
        if not self.current_session:
            print("⚠️ No active session. Start a session first.")
            return

        # Add to session
        self.session_conversations.append(completed_conversation)
        self.current_session["conversations"].append(completed_conversation)

        conversation_id = completed_conversation.get("conversation_id", "unknown")
        print(f"📝 Added conversation {conversation_id} to session")

    def save_session(self) -> Optional[str]:
        """Save the current session to file."""
        if not self.current_session:
            print("⚠️ No active session to save.")
            return None

        # Finalize session metadata
        self.current_session.update(
            {
                "end_time": time.time(),
                "duration": time.time() - self.current_session["start_time"],
                "total_conversations": len(self.session_conversations),
                "total_actions": sum(
                    len(conv.get("messages", []))
                    for conv in self.session_conversations
                    if conv.get("messages")
                ),
                "status": "completed",
            }
        )

        # Save to file
        filename = f"{self.current_session['session_id']}.json"
        filepath = self.output_dir / filename

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.current_session, f, indent=2, ensure_ascii=False)

            print(f"💾 Saved session: {filename}")
            print(
                f"📊 {self.current_session['total_conversations']} conversations, "
                f"{self.current_session['total_actions']} total messages"
            )
            print(f"⏱️ Duration: {self.current_session['duration']:.1f} seconds")

            # Reset for next session
            saved_session_id = self.current_session["session_id"]
            saved_filepath = str(filepath)
            self.current_session = None
            self.session_conversations = []

            return saved_filepath

        except Exception as e:
            print(f"❌ Error saving session: {e}")
            return None

    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        if not self.current_session:
            return {"status": "no_active_session"}

        return {
            "session_id": self.current_session["session_id"],
            "task_description": self.current_session["task_description"],
            "conversations_count": len(self.session_conversations),
            "duration": time.time() - self.current_session["start_time"],
            "status": "active",
        }

    def cancel_session(self) -> None:
        """Cancel the current session without saving."""
        if self.current_session:
            session_id = self.current_session["session_id"]
            self.current_session = None
            self.session_conversations = []
            print(f"❌ Cancelled session: {session_id}")
        else:
            print("⚠️ No active session to cancel.")

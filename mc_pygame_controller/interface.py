import asyncio
import time
from .conversation import ConversationPanel

class MinecraftControllerInterface:
    """Interface for capturing human demonstrations in MCP mode."""

    def __init__(self, mode="mcp"):
        from .controller_base import MinecraftController

        self.mode = mode
        self.conv_panel = ConversationPanel()
        self.tools_mapping = {}
        self.controller: MinecraftController | None = None
        self.trajectory_storage = TrajectoryStorage()

        if mode == "mcp":
            self.conv_panel.human_demo_mode = True
            print(f"🎮 MinecraftControllerInterface initialized in {mode} mode")

    def capture_command(self, mcp_command):
        self.conv_panel.capture_mcp_action(mcp_command)
        print(
            f"📝 Interface captured: {mcp_command['tool']}({mcp_command['parameters']})"
        )
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.execute_command(mcp_command))
            else:
                print("⚠️ No running event loop for command execution")
        except Exception as e:
            print(f"⚠️ Could not schedule command execution: {e}")

    async def execute_command(self, action):
        tool_name = action["tool"]
        params = action["parameters"]
        print(f"🎮 Executing: {tool_name}({params})")
        if tool_name in self.tools_mapping:
            try:
                result = await self.tools_mapping[tool_name](**params)
                print(f"✅ Executed {tool_name} successfully")
                if result and isinstance(result, dict) and "content" in result:
                    content = result["content"]
                    if isinstance(content, list) and len(content) > 0:
                        text_content = content[0].get("text", "")
                        if text_content:
                            first_line = text_content.split("\n")[0]
                            print(f"📋 Result: {first_line}")
                if tool_name == "lookAngle" and "getBotStatus" in self.tools_mapping:
                    try:
                        print("👁️ Getting updated view after look command...")
                        status_result = await self.tools_mapping["getBotStatus"]()
                        if (
                            status_result
                            and isinstance(status_result, dict)
                            and "content" in status_result
                        ):
                            status_content = status_result["content"]
                            if (
                                isinstance(status_content, list)
                                and len(status_content) > 0
                            ):
                                status_text = status_content[0].get("text", "")
                                if status_text:
                                    lines = status_text.split("\n")
                                    position_line = lines[0] if lines else ""
                                    looking_at_line = [
                                        line for line in lines if "Looking at:" in line
                                    ]
                                    if looking_at_line:
                                        print(f"🎯 {position_line}")
                                        print(f"🎯 {looking_at_line[0]}")
                                    else:
                                        print(f"🎯 {position_line}")
                    except Exception as e:
                        print(f"⚠️ Could not get updated status after look: {e}")
                return result
            except Exception as e:
                print(f"❌ Error executing {tool_name}: {e}")
                import traceback
                traceback.print_exc()
                return None
        else:
            print(f"⚠️ Tool {tool_name} not found in tools_mapping")
            available_tools = (
                list(self.tools_mapping.keys()) if self.tools_mapping else []
            )
            print(f"💡 Available tools: {available_tools}")
            return None

    def set_controller(self, controller):
        self.controller = controller
        controller.set_mcp_executor(self)
        print("🔗 Controller connected to interface")

    def start_trajectory_recording(self, session_name="human_demo"):
        self.trajectory_storage.start_session(session_name)
        print(f"🎬 Started trajectory recording: {session_name}")

    def stop_trajectory_recording(self):
        if self.conv_panel.captured_actions:
            mock_response = self.conv_panel.convert_actions_to_mock_response()
            trajectory = self.trajectory_storage.end_session(mock_response)
            print(
                f"🎬 Stopped recording. Saved trajectory with {len(trajectory.get('messages', []))} messages"
            )
            return trajectory
        else:
            print("🎬 Stopped recording. No actions captured.")
            return None

    def save_demonstration_step(self, user_context="exploring"):
        if self.conv_panel.captured_actions:
            mock_response = self.conv_panel.convert_actions_to_mock_response()
            self.trajectory_storage.add_step(user_context, mock_response)
            print(f"💾 Saved demonstration step: {user_context}")
            return True
        return False


class TrajectoryStorage:
    """Store human demonstration trajectories."""

    def __init__(self):
        self.current_session = None
        self.session_data = []

    def start_session(self, session_name):
        self.current_session = {
            "session_name": session_name,
            "timestamp": time.time(),
            "messages": [],
            "actions": [],
        }

    def add_step(self, user_context, mock_response):
        if not self.current_session:
            return
        user_message = {
            "role": "user",
            "content": user_context,
            "timestamp": time.time(),
        }
        assistant_message = {
            "role": "assistant",
            "content": mock_response["content"],
            "tool_calls": mock_response["tool_calls"],
            "timestamp": time.time(),
        }
        self.current_session["messages"].extend([user_message, assistant_message])
        if mock_response["tool_calls"]:
            for tool_call in mock_response["tool_calls"]:
                tool_result = {
                    "role": "tool",
                    "content": f"Executed {tool_call['function']['name']} successfully",
                    "tool_call_id": tool_call["id"],
                    "name": tool_call["function"]["name"],
                    "timestamp": time.time(),
                }
                self.current_session["messages"].append(tool_result)

    def end_session(self, final_response=None):
        if not self.current_session:
            return None
        if final_response:
            self.add_step("final actions", final_response)
        filename = f"trajectories/{self.current_session['session_name']}_{int(self.current_session['timestamp'])}.json"
        import os
        os.makedirs("trajectories", exist_ok=True)
        with open(filename, "w") as f:
            json.dump(self.current_session, f, indent=2)
        trajectory = self.current_session
        self.current_session = None
        print(f"💾 Saved trajectory to {filename}")
        return trajectory

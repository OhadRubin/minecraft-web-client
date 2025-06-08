"""
Controller State Management

Centralized state management for the MinecraftController to improve organization
and make state sharing between components easier.
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple, Any, Optional
import websockets


@dataclass
class ControllerState:
    """Centralized state container for MinecraftController."""
    
    # Basic controller state
    running: bool = True
    connected: bool = False
    mode: str = "pygame"
    sensitivity: float = 5.0
    enable_logging: bool = False
    
    # Hotbar state
    current_hotbar_slot: int = 0
    last_hotbar_slot: int = -1
    
    # Movement state
    last_movement: Tuple[float, float] = (0.0, 0.0)
    last_moved_in_mcp_mode: float = 0
    
    # Action state tracking with timing
    action_states: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "left_click": {"active": False, "start_time": None},
        "right_click": {"active": False, "start_time": None},
        "jump": {"active": False, "start_time": None},
        "sneak": {"active": False},
        "sprint": {"active": False},
    })
    
    # Keyboard shortcut states
    key_states: Dict[str, bool] = field(default_factory=lambda: {
        "ctrl": False,
        "tab": False,
        "z": False,
        "x": False,
        "space": False,
        "q": False,
        "f": False,
        "c": False,
    })
    
    # Key press tracking for edge detection
    last_key_states: Dict[str, bool] = field(default_factory=dict)
    
    # Mouse tracking state for camera area
    camera_was_clicking: bool = False
    
    # WebSocket connection
    websocket: Optional[websockets.WebSocketServerProtocol] = None
    connection_thread: Optional[Any] = None
    loop: Optional[Any] = None
    
    # MCP execution state
    mcp_executor: Optional[Any] = None
    
    # Asyncio integration
    event_loop: Optional[Any] = None
    event_queue: Optional[Any] = None
    command_queue: Optional[Any] = None
    result_queue: Optional[Any] = None
    
    # Additional state that was scattered in controller
    chain: Optional[Any] = None
    servers: list = field(default_factory=list)
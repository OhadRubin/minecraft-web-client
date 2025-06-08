Of course! This is a substantial class, and the author has already done a great job applying DRY principles. The comments at the top show a clear intent to write clean code. The next level of refactoring would involve architectural changes, primarily focused on the **Single Responsibility Principle (SRP)** and using design patterns to handle complexity.

The main issue with the current class is that it's doing too much. It's a "God Class" that handles:
1.  **State Management:** Tracking clicks, keys, hotbars, joystick position, etc.
2.  **UI Rendering:** Drawing all the buttons, text, and visual elements.
3.  **Input Handling:** Processing mouse and keyboard events.
4.  **Command Logic:** Deciding what commands to send (`pygame` vs `mcp`).
5.  **Network Communication:** Managing the WebSocket connection and asyncio loop.

Here are several ways to refactor this class, from simple to more architectural changes.

---

### 1. Architectural Refactoring: Decompose the Class

The most impactful change would be to break `MinecraftController` into smaller, more focused classes.

#### a) Strategy Pattern for `mode`

The `if self.mode == 'pygame': ... else: ...` checks are scattered throughout the code. This is a classic use case for the **Strategy Pattern**.

**Suggestion:** Create a `ModeStrategy` interface and two concrete implementations.

```python
from abc import ABC, abstractmethod

class ModeStrategy(ABC):
    """Abstract base class for a controller mode strategy."""
    def __init__(self, controller):
        self.controller = controller # To access logging, state, etc.

    @abstractmethod
    def handle_movement(self, x, z): pass

    @abstractmethod
    def handle_timed_action(self, tool_name, duration, **kwargs): pass

    @abstractmethod
    def handle_toggle_action(self, tool_name, state): pass
    
    @abstractmethod
    def handle_simple_action(self, tool_name, **kwargs): pass
    
    @abstractmethod
    def connect(self): pass

# --- Concrete Strategies ---

class PygameModeStrategy(ModeStrategy):
    def handle_movement(self, x, z):
        command = {"type": "move", "x": x, "z": z}
        self.controller.send_command_sync(command)
        # ... logging logic ...

    def handle_timed_action(self, tool_name, duration, **kwargs):
        # This one is tricky because pygame mode has separate up/down events.
        # The main controller would still need to manage this, but the logging
        # could be delegated here.
        pygame_down_cmd = kwargs.get('pygame_down_cmd')
        pygame_up_cmd = kwargs.get('pygame_up_cmd')
        # ... logic to send down/up commands ...
        self.controller._log_mcp_command(tool_name, {"duration": duration})
    
    def handle_simple_action(self, tool_name, **kwargs):
        pygame_cmd = kwargs.get('pygame_cmd')
        mcp_params = kwargs.get('mcp_params')
        if pygame_cmd:
            self.controller.send_command_sync(pygame_cmd)
        if mcp_params:
            self.controller._log_mcp_command(tool_name, mcp_params)

    def connect(self):
        self.controller.start_websocket_connection()

class MCPModeStrategy(ModeStrategy):
    def handle_movement(self, x, z):
        # In MCP mode, movement is handled by "walk" commands, which are timed.
        # This could be handled within the generic action handlers.
        # Let's assume walk is a simple action for now.
        if time.time() - self.controller.last_moved_in_mcp_mode > 2:
            self.handle_simple_action("walk", duration=1000)
            self.controller.last_moved_in_mcp_mode = time.time()

    def handle_timed_action(self, tool_name, duration, **kwargs):
        params = {"duration": duration, **kwargs}
        self.controller.execute_mcp_action({"tool": tool_name, "parameters": params})

    def handle_simple_action(self, tool_name, **kwargs):
        self.controller.execute_mcp_action({"tool": tool_name, "parameters": kwargs})
        
    def connect(self):
        # No websocket needed for MCP mode
        print("MCP mode ready. No WebSocket connection needed.")
        pass

```

**In `MinecraftController`:**

```python
class MinecraftController:
    def __init__(self, mode="pygame", ...):
        # ... other initializations ...
        if mode == "pygame":
            self.strategy = PygameModeStrategy(self)
        elif mode == "mcp":
            self.strategy = MCPModeStrategy(self)
        else:
            raise ValueError(f"Unknown mode: {mode}")

        self.strategy.connect()

    def handle_drop_item(self):
        print("DROP ITEM - sending command")
        self.strategy.handle_simple_action(
            "dropItem", 
            pygame_cmd={"type": "dropItem", "amount": 1}, 
            mcp_params={"amount": 1}
        )
```
This completely removes the `if self.mode == ...` checks from the action handlers, making them cleaner and delegating the mode-specific logic to the strategy objects.

#### b) Create a `UIManager` Class

The controller is cluttered with button instances and drawing logic. Extract this into a dedicated class.

**Suggestion:** Create a `UIManager` class to own all UI elements and the `draw_ui` method.

```python
class UIManager:
    def __init__(self, screen, controller_state):
        self.screen = screen
        self.state = controller_state # Pass state for drawing (e.g., hotbar)
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # All UI elements are created and owned here
        self.movement_joystick = VirtualJoystick(...)
        self.camera_area = TouchArea(...)
        self.left_click_btn = Button(...)
        # ... and so on for all buttons
        
    def handle_inputs(self, event, mouse_pos, mouse_pressed):
        """Processes inputs and returns high-level actions."""
        actions = []
        
        # Example: instead of calling controller methods directly,
        # return a list of actions for the controller to process.
        if self.left_click_btn.handle_mouse(mouse_pos, mouse_pressed):
             actions.append(("left_click_btn_pressed", self.left_click_btn.is_pressed))
             
        if self.inventory_btn.handle_mouse(mouse_pos, mouse_pressed):
            actions.append(("inventory_toggled", None))
            
        # ... handle all other UI elements ...
        
        return actions

    def draw(self):
        self.screen.fill(BLACK)
        # ... all the drawing logic from the old draw_ui method ...
        # It can read from self.state to draw dynamic things like connection status
        # or the highlighted hotbar slot.
```
The `MinecraftController` would then become much cleaner:
```python
class MinecraftController:
    def __init__(self, ...):
        # ...
        self.state = ControllerState() # A new class to hold all state
        self.ui_manager = UIManager(self.screen, self.state)
        # ...
    
    def _run_pygame_loop(self):
        # ...
        actions = self.ui_manager.handle_inputs(event, mouse_pos, mouse_pressed)
        for action, value in actions:
            if action == "inventory_toggled":
                self.handle_inventory()
            # ... process other actions
        
        self.ui_manager.draw()
        pygame.display.flip()
```

---

### 2. Method-Level and State Management Refactoring

#### a) Generalize Action Dispatching

You've already created excellent generic handlers (`_handle_timed_action`, `_handle_toggle_action`). We can create one more for simple, one-shot actions like `dropItem`, `swapHands`, `inventory`, etc.

**Suggestion:** Create a `_dispatch_simple_action` method.

```python
# (This is an alternative to the strategy pattern, or can be used with it)
def _dispatch_simple_action(self, mcp_tool: str, mcp_params: Dict, pygame_cmd: Dict):
    """Generic handler for simple one-shot commands."""
    print(f"{mcp_tool.upper()} - sending command")
    if self.mode == "pygame":
        self.send_command_sync(pygame_cmd)
        self._log_mcp_command(mcp_tool, mcp_params)
    else:  # mcp mode
        self.handle_other_commands(mcp_tool, **mcp_params)

# Then, specific handlers become one-liners:
def handle_drop_item(self):
    self._dispatch_simple_action(
        mcp_tool="dropItem",
        mcp_params={"amount": 1},
        pygame_cmd={"type": "dropItem", "amount": 1}
    )

def handle_swap_hands(self):
    self._dispatch_simple_action(
        mcp_tool="swapHands",
        mcp_params={},
        pygame_cmd={"type": "swapHands"}
    )
```

#### b) Consolidate State into a Dataclass or a Dedicated State Class

Instead of many individual state attributes (`self.connected`, `self.running`, `self.last_movement`, etc.), group them into a state object. This makes it explicit what constitutes the "state" of the controller and is easier to pass around (e.g., to the `UIManager`).

**Suggestion:** Use a dataclass for simplicity.

```python
from dataclasses import dataclass, field
from typing import Dict, Tuple

@dataclass
class ControllerState:
    running: bool = True
    connected: bool = False
    mode: str = "pygame"
    current_hotbar_slot: int = 0
    last_hotbar_slot: int = -1
    last_movement: Tuple[float, float] = (0.0, 0.0)
    
    # Using field(default_factory=...) for mutable defaults
    action_states: Dict[str, Dict] = field(default_factory=lambda: {
        "left_click": {"active": False, "start_time": None},
        "right_click": {"active": False, "start_time": None},
        "jump": {"active": False, "start_time": None},
        "sneak": {"active": False},
        "sprint": {"active": False},
    })
    key_states: Dict[str, bool] = field(default_factory=dict)
```
In `MinecraftController`:
```python
class MinecraftController:
    def __init__(self, mode="pygame", ...):
        self.state = ControllerState(mode=mode)
        # ...
    
    # Access state via self.state
    def handle_hotbar_slot(self, slot: int):
        if 0 <= slot <= 8 and slot != self.state.last_hotbar_slot:
            #...
            self.state.current_hotbar_slot = slot
            self.state.last_hotbar_slot = slot
```

### 3. Configuration-Driven UI Layout

The UI layout is hardcoded with "magic numbers" in `_init_ui_buttons`. This makes it difficult to change the layout.

**Suggestion:** Define the UI layout in a data structure (like a dictionary or list) and build the UI programmatically.

```python
# In a constants file or at the top of the UIManager
UI_LAYOUT = {
    "buttons": [
        {"name": "left_click_btn", "cls": Button, "pos": (1300, 600), "size": (100, 40), "text": "Left Click", "color": RED},
        {"name": "right_click_btn", "cls": Button, "pos": (1390, 600), "size": (100, 40), "text": "Right Click", "color": BLUE},
        {"name": "sneak_btn", "cls": ToggleButton, "pos": (1390, 650), "size": (100, 40), "text": "Sneak", "color": ORANGE},
        # ... etc for all buttons
    ],
    "hotbar": {
        "count": 9,
        "start_pos": (50, WINDOW_HEIGHT - 60),
        "size": (50, 40),
        "spacing": 55,
    }
}

# Inside your UIManager or MinecraftController
def _init_ui_from_layout(self, layout):
    self.buttons = {}
    for config in layout["buttons"]:
        button = config["cls"](
            config["pos"][0], config["pos"][1],
            config["size"][0], config["size"][1],
            config["text"], config["color"]
        )
        self.buttons[config["name"]] = button
        # You can also set it as an attribute for easier access if needed
        setattr(self, config["name"], button)
    
    # ... logic to create hotbar buttons from layout["hotbar"] ...
```

### Summary of Suggested Refactorings:

1.  **High-Priority (Architectural):**
    *   **Use the Strategy Pattern** to eliminate `if self.mode == ...` checks. This will drastically simplify your action handlers and separate concerns.
    *   **Extract a `UIManager` class** to own all UI elements and drawing logic. This will declutter the main controller and follow SRP.
    *   **Extract a `ControllerState` class/dataclass** to centralize all state variables.

2.  **Medium-Priority (Code Quality):**
    *   **Create a `_dispatch_simple_action` helper** to further reduce duplication in one-shot action handlers (`drop`, `swap`, etc.).
    *   **Use a data-driven approach for the UI layout** to make it configurable and remove magic numbers.

3.  **Low-Priority (Nice-to-haves):**
    *   Consider creating a `CommunicationHandler` class to encapsulate all the `websockets` and `asyncio` logic, further isolating responsibilities.
    *   Use `Enum` for action names or modes to avoid "stringly-typed" code. (`class Mode(Enum): PYGAME="pygame"; MCP="mcp"`)

Applying these changes, especially the architectural ones, will transform the class from a single, large entity into a well-orchestrated system of smaller, more manageable components. This makes the code easier to understand, maintain, and extend in the future.
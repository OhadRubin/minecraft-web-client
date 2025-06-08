
# Refactoring Suggestion 1: Eliminate State Property Boilerplate (High-Impact, Low-Risk)

This is the most straightforward and impactful cleanup. The `MinecraftController` class has over 120 lines dedicated to property decorators that simply proxy access to `self.state`. This was a good transitional step but now serves only to obscure the code.

**Problem:** Lines 97-221 are boilerplate code.

**High-Level Plan:**
1.  **Identify all property decorators** in `controller_base.py` that act as simple proxies to `self.state` attributes.
2.  **Remove these property decorators** from the `MinecraftController` class.
3.  **Update all internal references** within `MinecraftController` that previously used these properties to directly access the corresponding attributes on `self.state`. For example, `self.running` becomes `self.state.running`.
4.  **Search for external usages** of these properties in other project files. This might involve a project-wide search for patterns like `controller_instance.property_name`.
5.  **Update external usages** to directly access `self.state.attribute_name`. For example, `my_controller.mode` would change to `my_controller.state.mode`.
6.  **Test thoroughly** to ensure that all state access and modifications behave as expected after the changes.

**Defensive Plan:**

1.  **Controller's Internal Logic (`controller_base.py`):**
    *   **Watch Out For:** Simple find-and-replace might miss edge cases. The implementer must change both **read accesses** (e.g., `if self.mode == ...`) and **write accesses** (e.g., `self.running = False`). The latter is easier to miss.
    *   **Defensive Action:** Manually audit every usage of the old properties within `MinecraftController` to ensure they are replaced with `self.state.property_name`. For setters, `self.property = value` must become `self.state.property = value`.

2.  **External Module Dependencies:** The controller instance is passed to other modules. These will break if not updated.
    *   **`mode_strategy.py`:** This is a high-risk area. The strategy classes frequently call back to the controller to get state (e.g., `self.controller.enable_logging`) or set it (`self.controller.last_moved_in_mcp_mode = ...`).
        *   **Defensive Action:** The implementer must update all property accesses on `self.controller` within the strategy classes to `self.controller.state`.
    *   **`controller.py` (Main Entrypoint):** The script creates and interacts with the controller instance.
        *   **Watch Out For:** The `while controller.running:` loop in `handle_interactive_session` and the `controller.run()` call.
        *   **Defensive Action:** Change `controller.running` to `controller.state.running`. Ensure any other direct property access is updated.
    *   **`interface.py`:** The `MinecraftControllerInterface` holds a reference to the controller.
        *   **Watch Out For:** The `set_controller` method calls `controller.set_mcp_executor(self)`. The `set_mcp_executor` method itself needs to be updated internally from `self.mcp_executor = executor` to `self.state.mcp_executor = executor`.
        *   **Defensive Action:** Audit `interface.py` for any direct property access on `self.controller`. Update the bodies of any controller methods that were used to *set* state.
        *   **Important Distinction:** Note that the call from `interface.py` to `set_mcp_executor` remains the same, but the implementation inside `controller_base.py` must change from `self.mcp_executor = ...` to `self.state.mcp_executor = ...`. This distinction between the external call and internal implementation is critical.

3.  **The Process:**
    *   **Defensive Action:** The implementer should not rely solely on their IDE's refactoring tool. A project-wide text search for each property name (`.running`, `.mode`, `.connected`, etc.) is mandatory to find all usages. This manual verification step is the most critical part of the defense.

**Benefits:**
*   **Reduces Code by ~125 lines:** Instantly makes the class much shorter and easier to read.
*   **Improves Clarity:** Makes it explicit that state is being manipulated via the `self.state` object.
*   **Enforces Consistency:** Establishes a single, clear pattern for state access throughout the project.


# Refactoring Suggestion 2: Strengthen the Strategy Pattern

The controller currently uses a `ModeStrategy`, but some mode-specific logic still resides within the controller itself. This refactoring aims to move all mode-dependent behavior into the respective strategy classes, making the controller truly mode-agnostic.

**Problem:** The `handle_camera_look` method in `controller_base.py` contains conditional logic based on the current mode (`if self.mode == "pygame":`). This violates the principle of the Strategy Pattern, where such decisions should be delegated to the strategy object.

**High-Level Plan:**
1.  **Identify methods in `MinecraftController`** that contain mode-specific conditional logic (e.g., `if self.state.mode == '...'` or `if self.mode == '...'`).
2.  For each identified method:
    a.  **Define a new abstract method** in the `ModeStrategy` abstract base class (e.g., `handle_camera_look(self, scaled_x: int, scaled_y: int)`).
    b.  **Implement this method in each concrete strategy class** (`PygameModeStrategy`, `MCPModeStrategy`). The implementation should contain the logic that was previously executed conditionally in the controller.
        *   For `PygameModeStrategy`: Send the WebSocket command.
        *   For `MCPModeStrategy`: This might be a no-op if `LookPathTracker` handles it, or it could include MCP-specific logging or actions.
    c.  **Modify the original method in `MinecraftController`** to remove the conditional logic and instead unconditionally call the new method on the current strategy object (e.g., `self.strategy.handle_camera_look(scaled_x, scaled_y)`).
3.  **Review `MinecraftController`** for any remaining mode checks and repeat step 2 if necessary. The goal is to eliminate direct mode checks from the controller's methods.
4.  **Test each mode** to ensure that the behavior previously handled by conditional logic in the controller is now correctly managed by the respective strategy implementations.

**Defensive Plan:**

1.  **Method Signatures and Parameters:**
    *   **Watch Out For:** The new abstract methods in `ModeStrategy` must have signatures that match what `MinecraftController` will provide. For `handle_camera_look`, the controller calculates `scaled_x` and `scaled_y`, so the strategy method must be prepared to accept those, not the raw `delta_x`, `delta_y`.
    *   **Defensive Action:** The implementer must first decide on the exact data to be passed, define the abstract method signature in `ModeStrategy`, and then implement it, ensuring the call site in `MinecraftController` provides the correct arguments.

2.  **Dependencies of Moved Logic:**
    *   **Watch Out For:** The logic being moved (e.g., `self.send_command_sync(command)`) depends on methods within `MinecraftController`.
    *   **Defensive Action:** Remind the implementer that this is expected and will work correctly, as the strategy instance holds a reference `self.controller`. All calls must be prefixed accordingly: `self.controller.send_command_sync(...)`.

3.  **Identifying All Candidates for Moving:**
    *   **Watch Out For:** Stopping after moving just one piece of logic. The goal is to make the controller mode-agnostic.
    *   **Defensive Action:** The plan should explicitly guide the implementer to search `controller_base.py` for all instances of `if self.state.mode ==`. A key candidate is the `_process_continuous_state` method, which is entirely `pygame`-specific. The entire body of this method should be moved into a new method within `PygameModeStrategy`, and the `MCPModeStrategy` version should be empty.

4.  **Distinguishing Setup vs. Runtime Logic:**
    *   **Watch Out For:** Trying to move `__init__` logic into the strategy. The mode-check in `MinecraftController.__init__` (e.g., setting the `execution_callback`) is setup logic that configures the object graph. This is acceptable to leave in the controller's constructor.
    *   **Defensive Action:** The plan should advise focusing on runtime methods called within the main loop (`_process_frame`), not one-time setup methods.

5.  **The Null Case Implementation:**
    *   **Watch Out For:** Hesitation about implementing "empty" methods.
    *   **Defensive Action:** Explicitly state that for the `MCPModeStrategy`, an empty implementation like `def handle_camera_look(...): pass` is not only acceptable but *correct*. This is by design, as the `LookPathTracker`'s callback system handles the action in MCP mode. Reassure the implementer that an empty method is a valid design choice in this context.

**Benefits:**
*   **SOLID Principles:** Adheres more closely to the Open/Closed Principle. The controller becomes closed for modification when new modes are added (as new modes would just require a new strategy implementation).
*   **Removes Conditionals:** Simplifies `MinecraftController` by removing mode-checking `if/else` blocks.
*   **Improves Cohesion:** Mode-specific behavior is now entirely encapsulated within the strategy classes, making each class more focused.


# Refactoring Suggestion 3: Encapsulate the Camera Drag State Machine

The logic for managing camera drag operations (tracking when the mouse is pressed, moving over the camera area, and released) is currently spread across `MinecraftController`, `UIManager`, and `LookPathTracker`. This distribution makes the state machine fragile and hard to understand. This refactoring proposes encapsulating this logic into a new, dedicated class.

**Problem:** The state for camera dragging is managed by attributes like `camera_was_clicking` on the controller, and its state transitions are triggered by checks scattered in the main processing loop. This has led to bugs and makes reasoning about the camera drag behavior difficult.

**High-Level Plan:**
1.  **Define a new class `CameraDragHandler`**. This class will be responsible for managing the state of a camera drag operation.
    *   It will likely need to be initialized with a reference to `LookPathTracker` to signal the start and end of mouse tracking.
    *   Internal state variables will include `_was_dragging` (or similar) to track the previous state.
2.  **Implement an `update` method in `CameraDragHandler`**.
    *   This method will take the current relevant inputs, such as `is_in_camera_area: bool` and `is_mouse_pressed: bool`.
    *   Inside `update`, implement the state machine logic:
        *   **Start of drag:** If the mouse is now pressed in the camera area AND it wasn't dragging before, call `look_path_tracker.start_mouse_tracking()`.
        *   **End of drag:** If the mouse is now released AND it was dragging before, call `look_path_tracker.stop_mouse_tracking()`.
        *   Update the internal state (e.g., `_was_dragging = is_dragging_now`).
3.  **Integrate `CameraDragHandler` into `MinecraftController`**:
    *   Instantiate `CameraDragHandler` in the `MinecraftController.__init__` method, passing the `look_path_tracker` instance.
    *   Remove the old `camera_was_clicking` attribute and its related logic from `MinecraftController`.
    *   In `MinecraftController._process_frame` (or the equivalent main loop method):
        *   Gather the necessary inputs (e.g., `self.ui_manager.camera_area.is_touching`, `pygame.mouse.get_pressed()[0]`).
        *   Call `self.camera_drag_handler.update()` with these inputs.
4.  **Remove Redundant Logic**:
    *   The `_handle_camera_drag_state` method in `MinecraftController` can likely be removed.
    *   The `"camera_drag_state"` action from `UIManager` might no longer be needed if the `CameraDragHandler` directly uses `UIManager` properties or receives the necessary boolean flags.
5.  **Test camera drag functionality thoroughly** to ensure the new handler correctly manages all state transitions and interactions with `LookPathTracker`.

**Defensive Plan:**

1.  **Complete Removal of the Old State Machine:**
    *   **Watch Out For:** Leaving pieces of the old system in place. This could lead to two conflicting state machines running at once.
    *   **Defensive Action:** The implementer must perform a **"seek and destroy"** mission for the old logic. This includes:
        1.  Deleting the `self.camera_was_clicking` attribute from `MinecraftController`.
        2.  Deleting the `_handle_camera_drag_state` method from `MinecraftController`.
        3.  Removing the `"camera_drag_state"` key-value pair from the `_action_handlers` dictionary.

2.  **New Data Flow:**
    *   **Watch Out For:** The new `CameraDragHandler.update()` method needs inputs. The old flow involved `UIManager` creating an action. The new flow should be more direct.
    *   **Defensive Action:** The plan must specify the new data path: `MinecraftController._process_frame` is responsible for gathering `is_in_camera_area` (from `self.ui_manager.camera_area.is_touching`) and `is_mouse_pressed` (from `pygame`) and passing them directly to `self.camera_drag_handler.update()`. The `"camera_drag_state"` action from `UIManager` becomes obsolete.

3.  **Correct State Logic Replication:**
    *   **Watch Out For:** The `README` details the precise state transition logic that works. An incorrect implementation in the new handler will reintroduce old bugs (e.g., "works first time only").
    *   **Defensive Action:** The implementer must carefully review the state machine logic in the `README` (lines 276-294) and ensure it is perfectly replicated inside the `CameraDragHandler.update()` method. The core logic is checking the transition from `_was_dragging=False` to `True`, and from `True` to `False`.

**Benefits:**
*   **Encapsulation:** The complex state logic for camera dragging is moved into its own well-defined class, improving separation of concerns.
*   **Eliminates Fragile State:** Removes the scattered `camera_was_clicking` attribute and its associated complex logic from the main controller.
*   **Improved Testability:** `CameraDragHandler` can be unit-tested in isolation, making it easier to verify its correctness.
*   **Readability:** The main processing loop in `MinecraftController` becomes clearer, as it delegates the drag handling to the new class.


# Refactoring Suggestion 4: Decompose the Controller with an `ActionHandler` Class

The `MinecraftController` class currently has a very broad set of responsibilities. It manages the main loop, connections, UI interactions, and the logic for every specific game action (movement, clicking, etc.). This makes it a "God Object" and difficult to maintain. This refactoring proposes extracting the action-handling logic into a separate `ActionHandler` class.

**Problem:** `MinecraftController` contains numerous `handle_*` and `_handle_*` methods, along with a large `_action_handlers` dictionary. This mixes high-level orchestration responsibilities with the low-level implementation details of each action.

**High-Level Plan:**
1.  **Define a new class `ActionHandler`**.
    *   It will be initialized with references to `ControllerState`, the current `ModeStrategy`, and the `MinecraftController` instance itself (for sending commands or accessing other components if necessary).
    *   The `_action_handlers` dictionary (mapping action names to handler methods) will be moved from `MinecraftController` to this new class.
2.  **Move Action Implementation Methods**:
    *   Transfer all `handle_*` methods (e.g., `handle_movement`, `handle_left_click`, etc.) from `MinecraftController` to `ActionHandler`.
    *   Update these methods to use the passed-in `state`, `strategy`, and `controller` references as needed (e.g., `self.state.last_movement` instead of `self.controller.state.last_movement` if accessed from within `ActionHandler`).
    *   Any helper methods exclusively used by these action handlers (e.g., `_calculate_duration`) should also be moved to `ActionHandler`.
3.  **Implement `process_actions` in `ActionHandler`**:
    *   This method will take a list of actions (e.g., `actions: List[Tuple[str, Any]]`) as input.
    *   It will iterate through the actions, look up the appropriate handler in its `_action_handlers` dictionary, and call it with the provided value(s). This logic will be similar to what's currently in `MinecraftController._process_ui_actions`.
4.  **Modify `MinecraftController`**:
    *   In `__init__`, instantiate the `ActionHandler`, passing `self.state`, `self.strategy`, and `self`.
    *   Remove the `_action_handlers` dictionary and all the `handle_*` methods that were moved to `ActionHandler`.
    *   Update `_process_ui_actions` to simply delegate to `self.action_handler.process_actions(actions)`.
5.  **Refine Dependencies**:
    *   Carefully check the moved methods in `ActionHandler`. If they need to call methods on `MinecraftController` that are *not* about sending commands or basic state access (e.g., methods related to connection management), consider if those represent further coupling that could be reduced. For instance, if an action handler needs to send a command, it could call `self.controller.send_command_sync()`.
6.  **Thoroughly test all actions** to ensure they are processed correctly by the new `ActionHandler` and that all necessary state and components are accessed appropriately.

**Defensive Plan:**

1.  **The `self` Context Change:**
    *   **Watch Out For:** This is the **number one risk**. Inside a moved method like `handle_movement`, `self` now refers to the `ActionHandler` instance, *not* the `MinecraftController`. Any code that was `self.some_method()` will break if `some_method` was not also moved.
    *   **Defensive Action:** The implementer must audit **every single line** of the moved methods. Any call that needs to access a method or attribute remaining on the controller must be changed from `self.x` to `self.controller.x`. For example, `self.send_command_sync()` must become `self.controller.send_command_sync()`. This requires meticulous attention to detail.

2.  **Moving Helper Methods:**
    *   **Watch Out For:** Moving a public-facing handler (e.g., `handle_left_click`) but forgetting its private helper (`_handle_timed_action`).
    *   **Defensive Action:** The plan must explicitly list the key helper methods (`_handle_timed_action`, `_handle_toggle_action`, `_calculate_duration`, `_detect_key_edge`) and state they **must be moved** into `ActionHandler` along with their callers.

3.  **Dependency Injection:**
    *   **Watch Out For:** Instantiating `ActionHandler` without all its necessary dependencies.
    *   **Defensive Action:** The constructor signature `ActionHandler.__init__(self, state, strategy, controller)` must be strictly followed. The plan should emphasize that `controller` is a required dependency specifically to solve the `self` context problem mentioned in point 1.

4.  **Circular Reference Awareness:**
    *   **Watch Out For:** A developer being concerned about creating a circular reference (`controller` has an `action_handler`, which has a `controller`).
    *   **Defensive Action:** The plan should acknowledge that this refactoring intentionally creates this structure. Assure the implementer that this is a standard decomposition pattern and Python's garbage collector handles it correctly. This prevents them from trying to "fix" it and breaking the design.

5.  **The Complexity of Edge Detection:**
    *   **Watch Out For:** The `_detect_key_edge` helper method relies on a state dictionary, `self.state.last_key_states`. When moved to `ActionHandler`, it will need to access `self.state.last_key_states`. However, the method that uses this helper, `_handle_keyboard_shortcuts_edge_detection`, currently remains in `MinecraftController`. This creates a split responsibility.
    *   **Defensive Action:** For a more complete refactoring, consider that since the `ActionHandler` is now responsible for handling all actions (including keyboard shortcuts), the `_handle_keyboard_shortcuts_edge_detection` loop should *also* move into the `ActionHandler`. The `_process_frame` would then just pass `keys_pressed` to a new `action_handler.process_edge_detections(keys_pressed)` method. This would fully consolidate all action logic in one place, making `MinecraftController` a pure orchestrator of the main loop.

**Benefits:**
*   **Single Responsibility Principle:** `MinecraftController` will focus on orchestration (main loop, component setup, connection management), while `ActionHandler` will be solely responsible for implementing the logic of game actions.
*   **Massive Simplification of `MinecraftController`:** The controller class will become significantly smaller, less complex, and easier to understand.
*   **Better Organization:** All action-specific logic will be co-located in the `ActionHandler` class, improving code navigation and maintainability.
*   **Improved Testability:** `ActionHandler` can be tested more independently, focusing on the correctness of action implementations.

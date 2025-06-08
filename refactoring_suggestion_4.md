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

**Benefits:**
*   **Single Responsibility Principle:** `MinecraftController` will focus on orchestration (main loop, component setup, connection management), while `ActionHandler` will be solely responsible for implementing the logic of game actions.
*   **Massive Simplification of `MinecraftController`:** The controller class will become significantly smaller, less complex, and easier to understand.
*   **Better Organization:** All action-specific logic will be co-located in the `ActionHandler` class, improving code navigation and maintainability.
*   **Improved Testability:** `ActionHandler` can be tested more independently, focusing on the correctness of action implementations.

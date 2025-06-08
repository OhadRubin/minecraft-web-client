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

**Benefits:**
*   **SOLID Principles:** Adheres more closely to the Open/Closed Principle. The controller becomes closed for modification when new modes are added (as new modes would just require a new strategy implementation).
*   **Removes Conditionals:** Simplifies `MinecraftController` by removing mode-checking `if/else` blocks.
*   **Improves Cohesion:** Mode-specific behavior is now entirely encapsulated within the strategy classes, making each class more focused.

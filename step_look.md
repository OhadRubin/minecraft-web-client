
Okay, I've analyzed the `pygame_controller.py` (especially the `LookPathTracker`), the `trace.txt`, and your `goal.md`. Based on this, I'll outline a strategy for implementing the `look(X_angle, Y_angle)` LLM interface to produce natural-seeming camera movements. This involves converting the target angular change into a sequence of smaller, timed pixel-based look commands.

Here's a new document explaining the approach:

---

## Implementing Natural Look Movements for LLM Control

### 1. Introduction

The goal is to enable a Large Language Model (LLM) to control the Minecraft character's camera orientation (look direction) using a high-level command: `look(target_X_angle_delta, target_Y_angle_delta)`. `target_X_angle_delta` would correspond to yaw (left/right looking) and `target_Y_angle_delta` to pitch (up/down looking), relative to the current camera position.

The main challenge is to translate this single angular command into a sequence of low-level, pixel-based movement commands (`{"type": "look", "movementX": dX, "movementY": dY}`) that the existing `wsCommandClient.ts` interface (as used by `pygame_controller.py`) expects. Critically, this sequence should mimic natural, smooth human-like mouse movements.

This document draws insights from `pygame_controller.py` (particularly its `LookPathTracker` class and `handle_camera_look` method) and the command sequences observed in `trace.txt`.

### 2. Understanding the Existing System

*   **Pixel-Based Commands:** The `pygame_controller.py` captures mouse movements as `delta_x` and `delta_y` from a touch/drag area. These are scaled (e.g., `scaled_x = delta_x * 2`) and sent as discrete `(movementX, movementY)` pixel deltas to the WebSocket server.
*   **`LookPathTracker` Analysis:** This class in `pygame_controller.py` records the sequence of `(movement_x, movement_y)` deltas. It then analyzes this path *after the fact* to calculate metrics like total displacement, overall angle of the 2D mouse path, path efficiency, etc. It does not generate movements to achieve a predefined angle; it analyzes movements that have already occurred.
*   **`trace.txt` Observations:** The log file shows that typical human-generated look actions (via the Pygame controller) consist of multiple small `(dX, dY)` updates. The magnitude of these individual deltas is often less than 20-30 pixels per update, and a single "look" gesture is composed of a stream of such updates. The `LookPathTracker` also indicates resets due to inactivity (e.g., after 2 seconds), suggesting that a complete "look" action should feel continuous and complete within such a timeframe.

### 3. Core Problem: Angle-to-Pixel Conversion & Simulating Natural Motion

To implement the LLM's `look(target_X_angle_delta, target_Y_angle_delta)` command, two main problems must be solved:

1.  **Angle-to-Pixel Conversion:** Determine the total cumulative `(TotalPixelX, TotalPixelY)` displacement needed on the screen to achieve the desired `target_X_angle_delta` (yaw) and `target_Y_angle_delta` (pitch) in-game.
2.  **Natural Motion Generation:** Break down this `(TotalPixelX, TotalPixelY)` displacement into a series of smaller `(dX, dY)` sub-commands, timed appropriately, to simulate a smooth, non-robotic mouse movement.

### 4. Proposed Implementation Strategy for `look(target_X_angle_delta, target_Y_angle_delta)`

The implementation of this LLM command would involve the following steps:

#### a. Calibration (Crucial Prerequisite)

This is the most critical step and requires empirical measurement.
*   **Define `Sensitivity_X`:** The average number of `movementX` pixels (as sent in the command, e.g., `scaled_x`) required to produce one degree of yaw change in-game.
*   **Define `Sensitivity_Y`:** The average number of `movementY` pixels (e.g., `scaled_y`) required to produce one degree of pitch change in-game.

These sensitivities are dependent on the game's internal look sensitivity settings and how it interprets the `movementX`/`movementY` values. They can be determined by:
1.  Sending a known, fixed `movementX` (e.g., 100 pixels) and measuring the resulting yaw change in degrees.
2.  Repeating for `movementY` and pitch.
3.  Averaging over several trials.

#### b. Calculate Total Pixel Displacement

Once sensitivities are known, for a given LLM command `look(target_X_angle_delta, target_Y_angle_delta)`:
*   `TotalPixelX = target_X_angle_delta * Sensitivity_X`
*   `TotalPixelY = target_Y_angle_delta * Sensitivity_Y`

#### c. Generate Movement Sub-Steps

This `(TotalPixelX, TotalPixelY)` displacement needs to be achieved over a sequence of `N` sub-steps to appear smooth.

*   **Determine the Number of Sub-Steps (`N`):**
    *   `N` directly influences the speed and smoothness of the look movement. For a given angular change, more sub-steps (`N`) will result in a slower, potentially smoother movement.
    *   **How many steps for "natural" look?**
        *   This is not a single fixed number. It depends on the total angular distance and desired speed.
        *   A short, quick "flick" might use fewer steps (e.g., `N=5-10`) over a short duration (e.g., 100-200ms).
        *   A more deliberate, longer turn (e.g., 90 degrees) might use more steps (e.g., `N=15-30`) over a longer duration (e.g., 300-700ms).
    *   **Adaptive `N`:** `N` can be calculated based on the magnitude of the displacement:
        `N = ceil(max(abs(TotalPixelX), abs(TotalPixelY)) / avg_pixels_per_sub_step)`
        Where `avg_pixels_per_sub_step` could be a value like 5-15 pixels, based on `trace.txt` observations of typical delta magnitudes.
    *   A maximum `N` or a maximum duration for the entire `look` action should be considered to prevent excessively long movements from a single command. The entire sequence should ideally complete well within the `LookPathTracker`'s inactivity timeout (e.g., < 1.5 seconds).

*   **Calculate Per-Sub-Step Deltas (Base):**
    *   `base_dX_per_sub_step = TotalPixelX / N`
    *   `base_dY_per_sub_step = TotalPixelY / N`

*   **Temporal Distribution (Easing for Natural Pacing):**
    *   Human mouse movements typically have an acceleration and deceleration phase. To simulate this, apply an easing function (e.g., ease-in-out, sine curve) to distribute the `(TotalPixelX, TotalPixelY)` over the `N` sub-steps.
    *   This means sub-steps at the beginning and end of the movement will have smaller `(dX, dY)` magnitudes, while those in the middle will be larger.
    *   The sum of all `N` eased sub-step deltas must still equal `(TotalPixelX, TotalPixelY)`.
    *   Example: If `N=10`, an easing profile might scale `base_dX_per_sub_step` by multipliers like `[0.2, 0.5, 0.8, 1.1, 1.4, 1.4, 1.1, 0.8, 0.5, 0.2]` (these would need to be normalized so their sum is `N`).

*   **Path Naturalness (Optional Micro-Variations):**
    *   To avoid perfectly straight, robotic paths, especially for diagonal movements, subtle noise or a slight perpendicular component can be added to each `(dX, dY)` sub-step. This should be minor and ideally average out, or be part of a more complex path planning algorithm if very high fidelity is required.

#### d. Timing Between Sub-Steps

*   After calculating the `(dX_i, dY_i)` for each sub-step `i`, send the command:
    `{"type": "look", "movementX": dX_i, "movementY": dY_i}`
*   A pause is needed between sending each sub-step. This delay, along with `N`, determines the total duration of the look action.
    *   A delay of 16ms to 50ms per sub-step is reasonable. The Pygame controller runs at 60 FPS (approx. 16.7ms per frame), so updates can be frequent.
    *   Total Duration ≈ `N * inter_step_delay`.

### 5. Example Scenario

1.  LLM issues: `look(X_angle_delta=30, Y_angle_delta=0)` (look right 30 degrees).
2.  Calibration: Assume `Sensitivity_X = 5 pixels/degree`.
3.  Total Displacement: `TotalPixelX = 30 * 5 = 150` pixels. `TotalPixelY = 0`.
4.  Sub-Steps:
    *   Let `avg_pixels_per_sub_step = 10`.
    *   `N = ceil(max(150, 0) / 10) = 15` sub-steps.
5.  Base Deltas: `base_dX_per_sub_step = 150 / 15 = 10` pixels. `base_dY_per_sub_step = 0`.
6.  Easing: Apply an ease-in-out profile over the 15 steps. For instance, the sequence of `dX` values might be `[2, 4, 6, 8, 10, 12, 14, 15, 14, 12, 10, 8, 6, 4, 2]` (example values, must sum to 150).
7.  Timing: If `inter_step_delay = 30ms`, total duration = `15 * 30ms = 450ms`.
8.  Execution: Send 15 commands, each with the calculated `dX` from the eased sequence (and `dY=0`), pausing 30ms between each.

### 6. Further Considerations

*   **Calibration Precision:** The perceived quality and accuracy of the LLM's look commands will heavily depend on accurate `Sensitivity_X` and `Sensitivity_Y` values.
*   **Dynamic Speed Control:** The LLM interface could be extended, e.g., `look(X, Y, speed='fast'/'slow')`. This parameter would adjust `N` and/or `inter_step_delay`.
*   **Feedback Loop (Advanced):** For highly precise final orientations, one could envision a system where the actual in-game angle (if readable) is checked periodically during the sub-step sequence, and the remaining steps are adjusted. However, the `LookPathTracker` provides analysis on sent commands, not necessarily the absolute in-game state.
*   **Relationship to "Touch Functionality" (`goal.md`):** This strategy simulates the *outcome* of a smooth touch-drag gesture (i.e., camera rotation) rather than the raw touch mechanics themselves (e.g., specific screen coordinates of a drag). If the goal is to expose literal touch events (start, move, end coordinates), the LLM interface would need to be different. The current proposal aims for direct, natural-looking camera control based on angular targets.

---

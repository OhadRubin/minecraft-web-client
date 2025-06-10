/**
 * @file look_path.ts
 * Translates the Python LookPathTracker class for managing and analyzing mouse look movements.
 */

// Note: Pygame-specific imports like `pygame` and `time` (for time.time())
// are replaced with JavaScript equivalents like `Date.now()`.
// Constants are not directly imported from './constants' in the Python version's LookPathTracker logic,
// they are typically passed via constructor or are inherent to the logic (like math constants).

/**
 * Represents a single recorded mouse movement.
 */
export interface LookMovement {
    /** Timestamp of the movement in milliseconds. */
    timestamp: number;
    /** Horizontal movement in pixels. */
    movement_x: number;
    /** Vertical movement in pixels. */
    movement_y: number;
    /** Time elapsed in milliseconds since the first movement in the current drag. */
    relative_time: number;
}

/**
 * Represents an accumulated position, including the original movement data.
 */
export interface LookPosition extends LookMovement {
    /** Accumulated horizontal position in pixels. */
    x: number;
    /** Accumulated vertical position in pixels. */
    y: number;
}

/**
 * Detailed statistics calculated from a sequence of look movements.
 */
export interface LookStats {
    /** Total displacement as [x, y] pixels. */
    total_displacement: [number, number];
    /** Total straight-line distance from start to end in pixels. */
    total_distance: number;
    /** Overall angle of movement from start to end in degrees. */
    overall_angle_deg: number;
    /** Overall angle of movement from start to end in radians. */
    overall_angle_rad: number;
    /** Angle of the horizontal component of movement in degrees. */
    x_component_angle_deg: number;
    /** Angle of the horizontal component of movement in radians. */
    x_component_angle_rad: number;
    /** Angle of the vertical component of movement in degrees. */
    y_component_angle_deg: number;
    /** Angle of the vertical component of movement in radians. */
    y_component_angle_rad: number;
    /** Horizontal magnitude direction: 0° for right, 180° for left. */
    x_magnitude_angle: number;
    /** Vertical magnitude direction: 90° for down, -90° for up. */
    y_magnitude_angle: number;
    /** Average angle of all individual movement segments in degrees (circular mean). */
    avg_movement_angle_deg: number;
    /** List of angles for each individual movement segment in degrees. */
    movement_angles: number[];
    /** List of angles for X-only movements (0° or 180°). */
    x_only_angles: number[];
    /** List of angles for Y-only movements (90° or -90°). */
    y_only_angles: number[];
    /** Ratio of total_distance to path_length (0 to 1). */
    path_efficiency: number;
    /** Total number of recorded movement segments. */
    num_movements: number;
    /** Total length of the path traveled by summing individual segment lengths in pixels. */
    path_length: number;
    /** Compass angle derived from overall_angle_deg (0° North, 90° East, etc.). */
    compass_angle: number;
    /** Cardinal/intercardinal direction string (e.g., "North", "Northeast"). */
    compass_direction: string;
    /** Count of movements that were only horizontal. */
    x_only_movements: number;
    /** Count of movements that were only vertical. */
    y_only_movements: number;
    /** Count of movements that had both horizontal and vertical components. */
    mixed_movements: number;
    /** Count of segments with no movement. */
    no_movements: number;
}

/**
 * Callback function type for executing a command.
 * The command structure is generic for now.
 */
export type ExecutionCallback = (command: any) => void;

/**
 * Helper function to convert radians to degrees.
 * @param radians Angle in radians.
 * @returns Angle in degrees.
 */
function degrees(radians: number): number {
    return radians * (180 / Math.PI);
}

/**
 * Tracks and analyzes sequences of mouse look movements,
 * providing statistics and command execution capabilities.
 */
export class LookPathTracker {
    public movements: LookMovement[];
    public positions: LookPosition[];
    public max_history: number;
    public current_stats: LookStats | null;
    public execution_callback: ExecutionCallback | null;
    public sensitivity: number;
    public enable_logging: boolean;
    public mode: string; // "pygame" or "mcp"

    public mouse_tracking_active: boolean;
    private drag_start_time: number | null;

    /**
     * Initializes a new LookPathTracker.
     * @param sensitivity Pixels per degree for converting movement to angles in MCP mode.
     * @param enable_logging Whether to enable logging, especially in "pygame" mode.
     * @param mode Operating mode, "pygame" or "mcp".
     */
    constructor(sensitivity: number = 5.0, enable_logging: boolean = false, mode: string = "pygame") {
        this.movements = [];
        this.positions = [];
        this.max_history = 1000; // Limit history to prevent memory issues
        this.current_stats = null; // Store latest angle analysis
        this.execution_callback = null; // Callback for MCP command execution
        this.sensitivity = sensitivity;
        this.enable_logging = enable_logging;
        this.mode = mode;

        this.mouse_tracking_active = false;
        this.drag_start_time = null;
    }

    /**
     * Adds a new look movement to the history if mouse tracking is active.
     * @param movement_x Horizontal pixel movement.
     * @param movement_y Vertical pixel movement.
     */
    add_movement(movement_x: number, movement_y: number): void {
        if (!this.mouse_tracking_active) {
            console.log(`🚫 Movement ignored: tracking not active (${movement_x}, ${movement_y})`);
            return;
        }

        const currentTime = Date.now(); // milliseconds

        const movement: LookMovement = {
            timestamp: currentTime,
            movement_x,
            movement_y,
            relative_time: currentTime - (this.movements.length > 0 ? this.movements[0].timestamp : currentTime),
        };
        this.movements.push(movement);

        let position: LookPosition;
        if (this.positions.length === 0) {
            position = { x: 0, y: 0, ...movement };
        } else {
            const last_pos = this.positions[this.positions.length - 1];
            position = {
                x: last_pos.x + movement_x,
                y: last_pos.y + movement_y,
                ...movement,
            };
        }
        this.positions.push(position);

        if (this.movements.length > this.max_history) {
            this.movements.shift(); // pop(0) equivalent
            this.positions.shift(); // pop(0) equivalent
        }

        this._update_angle_analysis();
    }

    /**
     * Updates the `current_stats` object with detailed analysis of the recorded movements.
     */
    private _update_angle_analysis(): void {
        if (this.movements.length === 0) {
            this.current_stats = null;
            return;
        }

        const movement_tuples: [number, number][] = this.movements.map(m => [m.movement_x, m.movement_y]);

        const total_x = movement_tuples.reduce((sum, [mx, my]) => sum + mx, 0);
        const total_y = movement_tuples.reduce((sum, [mx, my]) => sum + my, 0);

        const overall_angle_rad = Math.atan2(total_y, total_x);
        const overall_angle_deg = degrees(overall_angle_rad);

        let x_component_angle_rad = 0;
        let x_component_angle_deg = 0;
        if (total_x !== 0) {
            x_component_angle_rad = Math.atan2(0, total_x);
            x_component_angle_deg = degrees(x_component_angle_rad);
        }

        let y_component_angle_rad = 0;
        let y_component_angle_deg = 0;
        if (total_y !== 0) {
            y_component_angle_rad = Math.atan2(total_y, 0);
            y_component_angle_deg = degrees(y_component_angle_rad);
        }

        const x_magnitude_angle = total_x >= 0 ? 0 : 180;
        const y_magnitude_angle = total_y >= 0 ? 90 : -90; // Note: Original Python code uses >= for 90, which is down.

        const total_distance = Math.sqrt(total_x ** 2 + total_y ** 2);

        const movement_angles: number[] = [];
        const x_only_angles: number[] = [];
        const y_only_angles: number[] = [];

        for (const [mx, my] of movement_tuples) {
            if (mx !== 0 || my !== 0) {
                const angle = Math.atan2(my, mx);
                movement_angles.push(degrees(angle));
                if (mx !== 0) {
                    x_only_angles.push(mx > 0 ? 0 : 180);
                }
                if (my !== 0) {
                    y_only_angles.push(my > 0 ? 90 : -90); // Assuming my > 0 is downwards
                }
            }
        }

        let avg_angle_deg = 0;
        if (movement_angles.length > 0) {
            const angles_rad = movement_angles.map(a => a * (Math.PI / 180));
            const mean_x = angles_rad.reduce((sum, a) => sum + Math.cos(a), 0) / angles_rad.length;
            const mean_y = angles_rad.reduce((sum, a) => sum + Math.sin(a), 0) / angles_rad.length;
            const avg_angle_rad = Math.atan2(mean_y, mean_x);
            avg_angle_deg = degrees(avg_angle_rad);
        }

        const path_length = movement_tuples.reduce((sum, [mx, my]) => {
            if (mx !== 0 || my !== 0) return sum + Math.sqrt(mx ** 2 + my ** 2);
            return sum;
        }, 0);
        const efficiency = path_length > 0 ? total_distance / path_length : 0;

        const x_only_count = movement_tuples.filter(([mx, my]) => mx !== 0 && my === 0).length;
        const y_only_count = movement_tuples.filter(([mx, my]) => mx === 0 && my !== 0).length;
        const mixed_count = movement_tuples.filter(([mx, my]) => mx !== 0 && my !== 0).length;
        const no_movement_count = movement_tuples.filter(([mx, my]) => mx === 0 && my === 0).length;

        let compass_angle = (90 - overall_angle_deg) % 360;
        if (compass_angle > 180) compass_angle -= 360;
        if (compass_angle < -180) compass_angle += 360; // Ensure it's within -180 to 180

        let direction = "Unknown";
        if (-22.5 <= compass_angle && compass_angle < 22.5) direction = "North";
        else if (22.5 <= compass_angle && compass_angle < 67.5) direction = "Northeast";
        else if (67.5 <= compass_angle && compass_angle < 112.5) direction = "East";
        else if (112.5 <= compass_angle && compass_angle < 157.5) direction = "Southeast";
        else if ((157.5 <= compass_angle && compass_angle <= 180) || (-180 <= compass_angle && compass_angle < -157.5)) direction = "South";
        else if (-157.5 <= compass_angle && compass_angle < -112.5) direction = "Southwest";
        else if (-112.5 <= compass_angle && compass_angle < -67.5) direction = "West";
        else if (-67.5 <= compass_angle && compass_angle < -22.5) direction = "Northwest";

        this.current_stats = {
            total_displacement: [total_x, total_y],
            total_distance,
            overall_angle_deg,
            overall_angle_rad,
            x_component_angle_deg,
            x_component_angle_rad,
            y_component_angle_deg,
            y_component_angle_rad,
            x_magnitude_angle,
            y_magnitude_angle,
            avg_movement_angle_deg,
            movement_angles,
            x_only_angles,
            y_only_angles,
            path_efficiency: efficiency,
            num_movements: this.movements.length,
            path_length,
            compass_angle,
            compass_direction: direction,
            x_only_movements: x_only_count,
            y_only_movements: y_only_count,
            mixed_movements: mixed_count,
            no_movements: no_movement_count,
        };
    }

    /**
     * Prints the current movement analysis statistics to the console.
     */
    private _print_current_stats(): void {
        if (!this.current_stats) {
            console.log("No movement data to analyze");
            return;
        }
        const stats = this.current_stats;
        console.log(`📊 Movement Analysis:`);
        console.log(`  • Overall angle: ${stats.overall_angle_deg.toFixed(1)}° (${stats.compass_direction})`);
        console.log(`  • X component: ${stats.x_component_angle_deg.toFixed(1)}° (${stats.x_magnitude_angle}°)`);
        console.log(`  • Y component: ${stats.y_component_angle_deg.toFixed(1)}° (${stats.y_magnitude_angle}°)`);
        console.log(`  • Movements: ${stats.x_only_movements} X-only, ${stats.y_only_movements} Y-only, ${stats.mixed_movements} mixed`);
        console.log(`  • Efficiency: ${(stats.path_efficiency * 100).toFixed(1)}%`);
    }

    /**
     * Gets the current angle analysis statistics.
     * @returns The current LookStats object, or null if no movements have been recorded.
     */
    get_current_stats(): LookStats | null {
        return this.current_stats;
    }

    /**
     * Clears all recorded movement history and statistics.
     */
    clear_history(): void {
        console.log("🗑️ Look path manually cleared");
        if (this.current_stats) {
            console.log("📊 Final stats before clear:");
            this._print_current_stats();
        }
        this.movements = [];
        this.positions = [];
        this.current_stats = null;
        this.drag_start_time = null; // Also reset drag start time as history is gone
    }

    /**
     * Gets the most recent recorded position.
     * @returns The latest LookPosition, or null if no positions are recorded.
     */
    get_latest_position(): LookPosition | null {
        return this.positions.length > 0 ? this.positions[this.positions.length - 1] : null;
    }

    /**
     * Gets the duration of the current drag operation in seconds.
     * @returns Duration in seconds, or null if not currently dragging.
     */
    get_drag_duration(): number | null {
        if (this.drag_start_time === null || !this.mouse_tracking_active) {
            return null;
        }
        return (Date.now() - this.drag_start_time) / 1000.0;
    }

    /**
     * Checks if a drag operation is currently active.
     * @returns True if dragging, false otherwise.
     */
    is_dragging(): boolean {
        return this.mouse_tracking_active;
    }

    /**
     * Sets the callback function to be invoked when an accumulated movement is executed.
     * @param callback The function to call with the generated command.
     */
    set_execution_callback(callback: ExecutionCallback): void {
        this.execution_callback = callback;
        console.log(`🔗 LookPathTracker execution callback connected`);
    }

    /**
     * Starts tracking mouse movements for a drag operation.
     * Called when the user presses the mouse button in the camera control area.
     */
    start_mouse_tracking(): void {
        if (!this.mouse_tracking_active) {
            console.log("🖱️ Started drag operation - accumulating movements");
            this.mouse_tracking_active = true;
            this.drag_start_time = Date.now();
            // Reset tracking data for the new drag session
            this._reset_tracking_data_internal(); // Use internal reset to avoid console log duplication
        } else {
            console.warn("⚠️ start_mouse_tracking() called but tracking already active!");
        }
    }

    /**
     * Stops tracking mouse movements, typically on mouse release, and executes the accumulated movement.
     */
    stop_mouse_tracking(): void {
        if (this.mouse_tracking_active) {
            const drag_duration = this.get_drag_duration();
            console.log(`🖱️ Drag completed (${drag_duration !== null ? drag_duration.toFixed(1) : 'N/A'}s) - executing command`);
            this.mouse_tracking_active = false;
            // this.drag_start_time = null; // drag_start_time is reset in _reset_tracking_data

            this._execute_accumulated_movement("drag_complete");
        }
    }

    /**
     * Converts accumulated pixel displacement to look angles and executes the command via callback.
     * @param trigger_reason A string indicating why this execution was triggered (e.g., "drag_complete").
     */
    private _execute_accumulated_movement(trigger_reason: string): void {
        if (this.current_stats) {
            const [total_x, total_y] = this.current_stats.total_displacement;

            const x_angle = total_x / this.sensitivity;
            const y_angle = -(total_y / this.sensitivity); // Invert Y for natural camera control

            console.log(`📊 Drag analysis (${trigger_reason}):`);
            this._print_current_stats();
            console.log(`   🎯 Camera rotation: ${x_angle.toFixed(1)}°, ${y_angle.toFixed(1)}°`);

            const command = {
                tool: "lookAngle",
                parameters: {
                    xAngle: parseFloat(x_angle.toFixed(1)), // Ensure numeric, not string
                    yAngle: parseFloat(y_angle.toFixed(1)), // Ensure numeric, not string
                    speed: "normal",
                },
            };

            if (this.execution_callback && (Math.abs(x_angle) > 0.2 || Math.abs(y_angle) > 0.2)) {
                console.log(`   ✅ Executing MCP command`);
                this.execution_callback(command);
                if (this.mode === "pygame" && this.enable_logging) {
                    console.log(`LOGGED: ${JSON.stringify(command)}`);
                }
            } else if (!this.execution_callback) {
                console.log(`   ⚠️  No execution callback set - command not executed`);
                if (this.mode === "pygame" && this.enable_logging && (Math.abs(x_angle) > 0.2 || Math.abs(y_angle) > 0.2)) {
                    console.log(`LOGGED (no exec): ${JSON.stringify(command)}`);
                }
            } else {
                console.log(`   🔇 Movement too small to execute: ${x_angle.toFixed(1)}°, ${y_angle.toFixed(1)}°`);
            }
        } else {
            console.log(`🔇 No movement data recorded during drag`);
        }
        this._reset_tracking_data(); // Reset after execution attempt
    }

    /**
     * Resets the movement and position history, and current statistics.
     * Called after a command execution or when starting a new drag.
     */
    private _reset_tracking_data(): void {
        this.movements = [];
        this.positions = [];
        this.current_stats = null;
        // this.drag_start_time = null; // Resetting drag_start_time here means get_drag_duration will be incorrect if called after stop_mouse_tracking but before next start.
                                     // drag_start_time is primarily for the *active* drag.
        console.log("🗑️ Reset drag tracking data");
    }

    /**
     * Internal version of reset for use within start_mouse_tracking to avoid duplicate logs.
     */
    private _reset_tracking_data_internal(): void {
        this.movements = [];
        this.positions = [];
        this.current_stats = null;
        // drag_start_time is set by the caller (start_mouse_tracking)
    }
}

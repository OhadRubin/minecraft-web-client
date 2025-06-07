// src/look-path-tracker.ts

/**
 * Port of mc_pygame_controller/look_path.py LookPathTracker
 * Tracks continuous mouse movement for looking around, segments it into
 * discrete actions, and converts them into MCP `lookAngle` commands.
 */
type Movement = {
    timestamp: number;
    movement_x: number;
    movement_y: number;
    relative_time: number;
};

type Position = Movement & { x: number; y: number; };

type McpCommand = {
    tool: string;
    parameters: any;
};

export class LookPathTracker {
    private movements: Movement[] = [];
    private positions: Position[] = [];
    private max_history = 1000;
    private inactivity_timeout_ms: number;
    private sensitivity: number;
    private last_movement_time: number | null = null;
    private current_stats: any | null = null;
    private execution_callback: ((command: McpCommand) => void) | null = null;

    private mouse_tracking_active = false;

    constructor(inactivity_timeout_ms = 2000, sensitivity = 5.0) {
        this.inactivity_timeout_ms = inactivity_timeout_ms;
        this.sensitivity = sensitivity; // Pixels per degree
    }

    set_execution_callback(callback: (command: McpCommand) => void) {
        this.execution_callback = callback;
        console.log("🔗 LookPathTracker execution callback connected");
    }

    add_movement(movement_x: number, movement_y: number) {
        if (movement_x === 0 && movement_y === 0) return;
        
        const current_time = Date.now();

        if (this.last_movement_time !== null) {
            if (current_time - this.last_movement_time > this.inactivity_timeout_ms) {
                this.execute_accumulated_movement("inactivity_timeout");
            }
        }
        this.last_movement_time = current_time;

        const movement: Movement = {
            timestamp: current_time,
            movement_x,
            movement_y,
            relative_time: current_time - (this.movements[0]?.timestamp ?? current_time),
        };
        this.movements.push(movement);

        const last_pos = this.positions[this.positions.length - 1] ?? { x: 0, y: 0 };
        const position: Position = {
            ...movement,
            x: last_pos.x + movement_x,
            y: last_pos.y + movement_y,
        };
        this.positions.push(position);

        if (this.movements.length > this.max_history) {
            this.movements.shift();
            this.positions.shift();
        }

        this.update_angle_analysis();
    }

    start_mouse_tracking() {
        if (!this.mouse_tracking_active) {
            console.log("🖱️ Started mouse tracking for look path");
            this.mouse_tracking_active = true;
            // Do not reset here to allow accumulation across multiple drags if needed,
            // though typical use is one command per drag.
        }
    }
    
    stop_mouse_tracking() {
        if (this.mouse_tracking_active) {
            console.log("🖱️ Stopped mouse tracking - executing command");
            this.mouse_tracking_active = false;
            this.execute_accumulated_movement("mouse_release");
        }
    }
    
    private execute_accumulated_movement(trigger_reason: string) {
        if (this.current_stats && this.execution_callback) {
            const [total_x, total_y] = this.current_stats.total_displacement;

            const xAngle = total_x / this.sensitivity;
            // Invert Y axis for natural camera control (drag down -> look up)
            const yAngle = - (total_y / this.sensitivity);

            // Only execute meaningful movements (filter noise)
            if (Math.abs(xAngle) > 0.2 || Math.abs(yAngle) > 0.2) {
                const mcp_command: McpCommand = {
                    tool: "lookAngle",
                    parameters: {
                        xAngle: parseFloat(xAngle.toFixed(1)),
                        yAngle: parseFloat(yAngle.toFixed(1)),
                        speed: "normal",
                    },
                };
                console.log(`🎯 Executing accumulated look: ${xAngle.toFixed(1)}°, ${yAngle.toFixed(1)}° (reason: ${trigger_reason})`);
                this.execution_callback(mcp_command);
            } else {
                console.log(`🔇 Movement too small to execute: ${xAngle.toFixed(1)}°, ${yAngle.toFixed(1)}°`);
            }
        }
        this.reset_tracking_data();
    }

    private reset_tracking_data() {
        this.movements = [];
        this.positions = [];
        this.current_stats = null;
        this.last_movement_time = null;
    }

    clear_history() {
        console.log("🗑️ Look path manually cleared");
        this.execute_accumulated_movement("manual_clear");
        this.reset_tracking_data();
    }

    private update_angle_analysis() {
        if (!this.movements.length) {
            this.current_stats = null;
            return;
        }

        const movement_tuples = this.movements.map(m => [m.movement_x, m.movement_y]);
        const total_x = movement_tuples.reduce((sum, [mx, my]) => sum + mx, 0);
        const total_y = movement_tuples.reduce((sum, [mx, my]) => sum + my, 0);

        const overall_angle_rad = Math.atan2(total_y, total_x);
        const overall_angle_deg = (overall_angle_rad * 180) / Math.PI;

        const total_distance = Math.hypot(total_x, total_y);
        const path_length = movement_tuples.reduce((sum, [mx, my]) => sum + Math.hypot(mx, my), 0);
        const efficiency = path_length > 0 ? total_distance / path_length : 0;
        
        let compass_angle = (90 - overall_angle_deg + 360) % 360;
        const directions = ["North", "Northeast", "East", "Southeast", "South", "Southwest", "West", "Northwest"];
        const direction = directions[Math.round(compass_angle / 45) % 8];

        this.current_stats = {
            total_displacement: [total_x, total_y],
            total_distance,
            overall_angle_deg,
            path_efficiency: efficiency,
            num_movements: this.movements.length,
            compass_direction: direction,
        };
    }

    get_current_stats() {
        return this.current_stats;
    }
}

// === START_OF: look_path.py (Inferred Implementation)
// =======================================================================

class LookPathTracker {
    constructor(sensitivity, enable_logging, mode) {
        this.sensitivity = sensitivity;
        this.enable_logging = enable_logging;
        this.mode = mode;
        this.path = [];
        this.is_tracking = false;
        this.execution_callback = null;
    }

    set_execution_callback(callback) {
        this.execution_callback = callback;
    }

    start_mouse_tracking() {
        if (this.is_tracking) return;
        this.is_tracking = true;
        this.path = [];
        if (this.enable_logging) console.log("👁️ Look tracking started.");
    }

    stop_mouse_tracking() {
        if (!this.is_tracking) return;
        this.is_tracking = false;
        if (this.path.length > 2) { // Need at least 3 points for a meaningful path
            if (this.enable_logging) console.log(`👁️ Look tracking stopped. Path has ${this.path.length} points.`);
            this.convert_path_to_action();
        } else {
            if (this.enable_logging) console.log("👁️ Look tracking stopped. Path too short, ignoring.");
        }
        this.path = [];
    }

    add_movement(dx, dy) {
        if (this.is_tracking) {
            this.path.push({ dx, dy, t: performance.now() });
        }
    }

    clear_history() {
        this.path = [];
        if (this.enable_logging) console.log("👁️ Look path history cleared.");
    }
    
    convert_path_to_action() {
        if (!this.execution_callback || this.path.length === 0) return;

        let total_dx = 0;
        let total_dy = 0;
        for (const p of this.path) {
            total_dx += p.dx;
            total_dy += p.dy;
        }

        const xAngle = total_dx / this.sensitivity;
        const yAngle = -(total_dy / this.sensitivity); // Invert Y

        // Simplified: convert the entire drag into one lookAngle command
        const mcp_command = {
            tool: 'lookAngle',
            parameters: {
                xAngle: Math.round(xAngle * 10) / 10,
                yAngle: Math.round(yAngle * 10) / 10,
                speed: "normal"
            }
        };

        if (this.enable_logging) {
            console.log("Executing look command from path:", mcp_command);
        }
        this.execution_callback(mcp_command);
    }
}

// =======================================================================
export { LookPathTracker };
// === END_OF: look_path.py

// === START_OF: look_path.py (Inferred Implementation)
// =======================================================================

/**
 * Represents a point in the look path with movement deltas and timestamp
 */
interface PathPoint {
    dx: number;
    dy: number;
    t: number;
}

/**
 * MCP command structure for lookAngle tool
 */
interface MCPLookCommand {
    tool: 'lookAngle';
    parameters: {
        xAngle: number;
        yAngle: number;
        speed: string;
    };
}

/**
 * Callback function type for executing MCP commands
 */
type ExecutionCallback = (command: MCPLookCommand) => void;

/**
 * Operating mode for the look path tracker
 */
type TrackerMode = string;

/**
 * Tracks mouse look movements and converts them to MCP lookAngle commands
 */
class LookPathTracker {
    private sensitivity: number;
    private enable_logging: boolean;
    private mode: TrackerMode;
    private path: PathPoint[];
    private is_tracking: boolean;
    private execution_callback: ExecutionCallback | null;

    constructor(sensitivity: number, enable_logging: boolean, mode: TrackerMode) {
        this.sensitivity = sensitivity;
        this.enable_logging = enable_logging;
        this.mode = mode;
        this.path = [];
        this.is_tracking = false;
        this.execution_callback = null;
    }

    /**
     * Sets the callback function to execute MCP commands
     */
    set_execution_callback(callback: ExecutionCallback): void {
        this.execution_callback = callback;
    }

    /**
     * Starts tracking mouse movements for look path recording
     */
    start_mouse_tracking(): void {
        if (this.is_tracking) return;
        this.is_tracking = true;
        this.path = [];
        if (this.enable_logging) console.log("👁️ Look tracking started.");
    }

    /**
     * Stops tracking and converts accumulated path to MCP command if valid
     */
    stop_mouse_tracking(): void {
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

    /**
     * Adds a movement point to the current tracking path
     */
    add_movement(dx: number, dy: number): void {
        if (this.is_tracking) {
            this.path.push({ dx, dy, t: performance.now() });
        }
    }

    /**
     * Clears the accumulated path history
     */
    clear_history(): void {
        this.path = [];
        if (this.enable_logging) console.log("👁️ Look path history cleared.");
    }
    
    /**
     * Converts the accumulated path to an MCP lookAngle command and executes it
     */
    private convert_path_to_action(): void {
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
        const mcp_command: MCPLookCommand = {
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
export { LookPathTracker, type PathPoint, type MCPLookCommand, type ExecutionCallback, type TrackerMode };
// === END_OF: look_path.py
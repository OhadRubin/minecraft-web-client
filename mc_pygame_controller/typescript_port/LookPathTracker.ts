interface Movement {
  timestamp: number;
  movement_x: number;
  movement_y: number;
  relative_time: number;
}

interface Position extends Movement {
  x: number;
  y: number;
}

interface McpLookAngleCommand {
  tool: 'lookAngle';
  parameters: {
    xAngle: number;
    yAngle: number;
    speed: 'normal' | string; // Allow 'normal' or other string values for speed
  };
}

interface LookPathStats {
  total_displacement: [number, number];
  total_distance: number;
  overall_angle_deg: number;
  overall_angle_rad: number;
  x_component_angle_deg: number;
  x_component_angle_rad: number;
  y_component_angle_deg: number;
  y_component_angle_rad: number;
  x_magnitude_angle: number;
  y_magnitude_angle: number;
  avg_movement_angle_deg: number;
  movement_angles: number[];
  x_only_angles: number[];
  y_only_angles: number[];
  path_efficiency: number;
  num_movements: number;
  path_length: number;
  compass_angle: number;
  compass_direction: string;
  x_only_movements: number;
  y_only_movements: number;
  mixed_movements: number;
  no_movements: number;
}

// Type for the execution callback
type ExecutionCallback = (command: McpLookAngleCommand) => void;

class LookPathTracker {
  private movements: Movement[] = [];
  private positions: Position[] = [];
  private current_x = 0;
  private current_y = 0;
  private start_time: number;
  private execution_callback: ExecutionCallback | null;
  private max_movements: number;
  private debug: boolean;

  constructor(
    execution_callback: ExecutionCallback | null = null,
    max_movements = 100, // Default to 100, similar to Python
    debug = false
  ) {
    this.execution_callback = execution_callback;
    this.max_movements = max_movements;
    this.debug = debug;
    this.start_time = Date.now();
    this.add_movement(0, 0); // Initialize with a zero movement
  }

  public add_movement(movement_x: number, movement_y: number): void {
    const timestamp = Date.now();
    const relative_time = (timestamp - this.start_time) / 1000; // in seconds

    const movement: Movement = {
      timestamp,
      movement_x,
      movement_y,
      relative_time,
    };
    this.movements.push(movement);

    this.current_x += movement_x;
    this.current_y += movement_y;

    const position: Position = {
      ...movement,
      x: this.current_x,
      y: this.current_y,
    };
    this.positions.push(position);

    if (this.movements.length > this.max_movements) {
      this.movements.shift(); // Remove the oldest movement
    }
    if (this.positions.length > this.max_movements) {
      this.positions.shift(); // Remove the oldest position
    }

    if (this.debug) {
      console.log(`Movement: x=${movement_x}, y=${movement_y}`);
      console.log(`Current Position: x=${this.current_x}, y=${this.current_y}`);
    }
  }

  public reset(): void {
    this.movements = [];
    this.positions = [];
    this.current_x = 0;
    this.current_y = 0;
    this.start_time = Date.now();
    this.add_movement(0, 0); // Initialize with a zero movement
    if (this.debug) {
      console.log('LookPathTracker reset');
    }
  }

  public get_path_stats(): LookPathStats | null {
    if (this.positions.length < 2) {
      if (this.debug) {
        console.warn('Not enough positions to calculate path stats.');
      }
      return null;
    }

    const first_pos = this.positions[0];
    const last_pos = this.positions[this.positions.length - 1];

    const total_displacement_x = last_pos.x - first_pos.x;
    const total_displacement_y = last_pos.y - first_pos.y;

    let total_distance = 0;
    for (let i = 1; i < this.positions.length; i++) {
      const p1 = this.positions[i - 1];
      const p2 = this.positions[i];
      total_distance += Math.sqrt(
        Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2)
      );
    }

    const overall_angle_rad = Math.atan2(
      total_displacement_y,
      total_displacement_x
    );
    const overall_angle_deg = overall_angle_rad * (180 / Math.PI);

    const x_component_angle_rad = Math.atan2(0, total_displacement_x);
    const x_component_angle_deg = x_component_angle_rad * (180 / Math.PI);

    const y_component_angle_rad = Math.atan2(total_displacement_y, 0);
    const y_component_angle_deg = y_component_angle_rad * (180 / Math.PI);

    const x_magnitude_angle = Math.abs(total_displacement_x);
    const y_magnitude_angle = Math.abs(total_displacement_y);

    const movement_angles: number[] = [];
    const x_only_angles: number[] = [];
    const y_only_angles: number[] = [];

    let x_only_movements = 0;
    let y_only_movements = 0;
    let mixed_movements = 0;
    let no_movements = 0;

    for (const move of this.movements) {
      if (move.movement_x === 0 && move.movement_y === 0) {
        no_movements++;
        continue;
      }
      const angle = Math.atan2(move.movement_y, move.movement_x) * (180 / Math.PI);
      movement_angles.push(angle);
      if (move.movement_x !== 0 && move.movement_y === 0) {
        x_only_angles.push(angle);
        x_only_movements++;
      } else if (move.movement_y !== 0 && move.movement_x === 0) {
        y_only_angles.push(angle);
        y_only_movements++;
      } else {
        mixed_movements++;
      }
    }
    
    const avg_movement_angle_deg = movement_angles.length > 0 
        ? movement_angles.reduce((sum, angle) => sum + angle, 0) / movement_angles.length
        : 0;

    const path_efficiency =
      total_distance > 0
        ? Math.sqrt(
            Math.pow(total_displacement_x, 2) +
              Math.pow(total_displacement_y, 2)
          ) / total_distance
        : 0;

    const num_movements = this.movements.length;
    const path_length = total_distance;

    // Compass angle and direction
    let compass_angle = (overall_angle_deg + 360) % 360; // Normalize to 0-360
     // Adjust for Minecraft's coordinate system if necessary (e.g. 0 degrees is South)
     // Assuming 0 degrees is East in atan2, adjust if Minecraft's 0 is different
    compass_angle = (compass_angle + 90) % 360; // Example: if 0 deg is South in MC, +90 to atan2 result.

    let compass_direction = '';
    if (compass_angle >= 337.5 || compass_angle < 22.5) compass_direction = 'N';
    else if (compass_angle >= 22.5 && compass_angle < 67.5) compass_direction = 'NE';
    else if (compass_angle >= 67.5 && compass_angle < 112.5) compass_direction = 'E';
    else if (compass_angle >= 112.5 && compass_angle < 157.5) compass_direction = 'SE';
    else if (compass_angle >= 157.5 && compass_angle < 202.5) compass_direction = 'S';
    else if (compass_angle >= 202.5 && compass_angle < 247.5) compass_direction = 'SW';
    else if (compass_angle >= 247.5 && compass_angle < 292.5) compass_direction = 'W';
    else if (compass_angle >= 292.5 && compass_angle < 337.5) compass_direction = 'NW';


    const stats: LookPathStats = {
      total_displacement: [total_displacement_x, total_displacement_y],
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
      path_efficiency,
      num_movements,
      path_length,
      compass_angle: Math.round(compass_angle * 10) / 10,
      compass_direction,
      x_only_movements,
      y_only_movements,
      mixed_movements,
      no_movements,
    };

    if (this.debug) {
      console.log('Path Stats:', stats);
    }
    return stats;
  }

  public execute_look_command(xAngle: number, yAngle: number, speed: string = 'normal'): void {
    if (this.execution_callback) {
      const command: McpLookAngleCommand = {
        tool: 'lookAngle',
        parameters: {
          xAngle: Math.round(xAngle * 10) / 10, // Round to 1 decimal place
          yAngle: Math.round(yAngle * 10) / 10, // Round to 1 decimal place
          speed: speed,
        },
      };
      this.execution_callback(command);
      if (this.debug) {
        console.log('Executed look command:', command);
      }
    } else if (this.debug) {
      console.warn('Execution callback not set. Command not sent.');
    }
  }

  public look_at_target(target_x: number, target_y: number, speed: string = 'normal'): void {
    const delta_x = target_x - this.current_x;
    const delta_y = target_y - this.current_y;

    // These would be angles to turn by, not absolute angles.
    // Assuming the input `target_x` and `target_y` are screen coordinates
    // or represent an angle in a consistent system.
    // For now, let's assume they are direct angle inputs,
    // but this might need adjustment based on how PyGame/MCP handles look angles.
    // If current_x, current_y are pixel positions, and target_x, target_y are also pixel positions,
    // then delta_x and delta_y are pixel differences. These need to be converted to angle changes.
    // This conversion factor is missing (pixels_to_degrees_x, pixels_to_degrees_y)
    // For this example, I'll assume delta_x and delta_y are already angular movements.
    // This part might need significant refinement based on "constants.PIXELS_TO_DEGREES_X/Y"

    if (this.debug) {
        console.log(`Looking at target: (${target_x}, ${target_y}) from (${this.current_x}, ${this.current_y})`);
        console.log(`Delta: dx=${delta_x}, dy=${delta_y}`);
    }
    // Assuming delta_x and delta_y are the desired angle changes.
    // The actual McpLookAngleCommand likely takes absolute pitch/yaw or relative changes.
    // If it's relative, then delta_x and delta_y are correct.
    // If it's absolute, we'd need to know the current absolute look angle.
    // The Python code used `delta_x * constants.PIXELS_TO_DEGREES_X`
    // For now, let's pass delta_x and delta_y, assuming they are angular values.
    this.execute_look_command(delta_x, delta_y, speed);
  }

  public get_current_position(): { x: number; y: number } {
    return { x: this.current_x, y: this.current_y };
  }

  public get_movements(): Movement[] {
    return this.movements;
  }

  public get_positions(): Position[] {
    return this.positions;
  }
}

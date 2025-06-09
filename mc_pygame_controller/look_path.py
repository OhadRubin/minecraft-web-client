import pygame
import time
import math
from typing import Optional, Tuple, List, Dict

from .constants import *

class LookPathTracker:

    def __init__(self, sensitivity=5.0, enable_logging=False, mode="pygame"):
        self.movements: List[Dict] = []
        self.positions: List[Dict] = []
        self.max_history = 1000  # Limit history to prevent memory issues
        self.current_stats = None  # Store latest angle analysis
        self.execution_callback = None  # Callback for MCP command execution
        self.sensitivity = sensitivity  # Pixels per degree for MCP conversion
        self.enable_logging = enable_logging  # Enable logging in pygame mode
        self.mode = mode  # Current mode (pygame or mcp)

        # Mouse-based drag detection - primary mechanism
        self.mouse_tracking_active = False  # Track if mouse is currently pressed in camera area
        self.drag_start_time = None  # When current drag started

    def add_movement(self, movement_x: int, movement_y: int):
        """Add a new look movement to the history (only during active mouse tracking)"""
        # Only accumulate movements during active mouse tracking (drag)
        if not self.mouse_tracking_active:
            print(f"🚫 Movement ignored: tracking not active ({movement_x}, {movement_y})")
            return

        current_time = int(time.time() * 1000)  # milliseconds

        movement = {
            "timestamp": current_time,
            "movement_x": movement_x,
            "movement_y": movement_y,
            "relative_time": current_time
            - (self.movements[0]["timestamp"] if self.movements else current_time),
        }

        self.movements.append(movement)

        # Calculate accumulated position
        if len(self.positions) == 0:
            # First position is at origin
            position = {"x": 0, "y": 0, **movement}
        else:
            # Accumulate from last position
            last_pos = self.positions[-1]
            position = {
                "x": last_pos["x"] + movement_x,
                "y": last_pos["y"] + movement_y,
                **movement,
            }

        self.positions.append(position)

        # Limit history size
        if len(self.movements) > self.max_history:
            self.movements.pop(0)
            self.positions.pop(0)

        # Update angle analysis after each movement
        self._update_angle_analysis()

    def _update_angle_analysis(self):
        """Update angle analysis statistics using the same logic as simple_angle_analyzer.py"""
        if not self.movements:
            self.current_stats = None
            return

        # Extract movement tuples for analysis (same format as simple_angle_analyzer.py)
        movement_tuples = [(m["movement_x"], m["movement_y"]) for m in self.movements]

        # Total displacement
        total_x = sum(mx for mx, my in movement_tuples)
        total_y = sum(my for mx, my in movement_tuples)

        # Overall angle (from start to end) - same logic as simple_angle_analyzer.py
        overall_angle_rad = math.atan2(total_y, total_x)
        overall_angle_deg = math.degrees(overall_angle_rad)

        # X and Y component angles - using exact same logic as simple_angle_analyzer.py
        # X component angle (horizontal movement angle)
        if total_x != 0:
            x_component_angle_rad = math.atan2(0, total_x)  # Pure horizontal
            x_component_angle_deg = math.degrees(x_component_angle_rad)
        else:
            x_component_angle_rad = 0
            x_component_angle_deg = 0

        # Y component angle (vertical movement angle)
        if total_y != 0:
            y_component_angle_rad = math.atan2(total_y, 0)  # Pure vertical
            y_component_angle_deg = math.degrees(y_component_angle_rad)
        else:
            y_component_angle_rad = 0
            y_component_angle_deg = 0

        # Alternative X and Y angles relative to their respective axes
        x_magnitude_angle = 0 if total_x >= 0 else 180  # 0° for right, 180° for left
        y_magnitude_angle = 90 if total_y >= 0 else -90  # 90° for down, -90° for up

        # Total distance traveled
        total_distance = math.sqrt(total_x**2 + total_y**2)

        # Individual movement angles - same logic as simple_angle_analyzer.py
        movement_angles = []
        x_only_angles = []
        y_only_angles = []

        for mx, my in movement_tuples:
            if mx != 0 or my != 0:  # Avoid division by zero
                angle = math.atan2(my, mx)
                movement_angles.append(math.degrees(angle))

                # X-only and Y-only movement angles
                if mx != 0:
                    x_only_angles.append(0 if mx > 0 else 180)
                if my != 0:
                    y_only_angles.append(90 if my > 0 else -90)

        # Average angle of individual movements (circular mean) - same logic as simple_angle_analyzer.py
        if movement_angles:
            # Convert to radians for circular mean calculation
            angles_rad = [math.radians(a) for a in movement_angles]
            mean_x = sum(math.cos(a) for a in angles_rad) / len(angles_rad)
            mean_y = sum(math.sin(a) for a in angles_rad) / len(angles_rad)
            avg_angle_rad = math.atan2(mean_y, mean_x)
            avg_angle_deg = math.degrees(avg_angle_rad)
        else:
            avg_angle_deg = 0

        # Path efficiency (straight line distance / total path length) - same logic as simple_angle_analyzer.py
        path_length = sum(
            math.sqrt(mx**2 + my**2) for mx, my in movement_tuples if mx != 0 or my != 0
        )
        efficiency = total_distance / path_length if path_length > 0 else 0

        # Movement type counts
        x_only_count = sum(1 for mx, my in movement_tuples if mx != 0 and my == 0)
        y_only_count = sum(1 for mx, my in movement_tuples if mx == 0 and my != 0)
        mixed_count = sum(1 for mx, my in movement_tuples if mx != 0 and my != 0)
        no_movement_count = sum(1 for mx, my in movement_tuples if mx == 0 and my == 0)

        # Convert to compass direction - same logic as simple_angle_analyzer.py
        compass_angle = (90 - overall_angle_deg) % 360
        if compass_angle > 180:
            compass_angle -= 360

        # Determine compass direction - same logic as simple_angle_analyzer.py
        if -22.5 <= compass_angle < 22.5:
            direction = "North"
        elif 22.5 <= compass_angle < 67.5:
            direction = "Northeast"
        elif 67.5 <= compass_angle < 112.5:
            direction = "East"
        elif 112.5 <= compass_angle < 157.5:
            direction = "Southeast"
        elif 157.5 <= compass_angle <= 180 or -180 <= compass_angle < -157.5:
            direction = "South"
        elif -157.5 <= compass_angle < -112.5:
            direction = "Southwest"
        elif -112.5 <= compass_angle < -67.5:
            direction = "West"
        elif -67.5 <= compass_angle < -22.5:
            direction = "Northwest"
        else:
            direction = "Unknown"

        # Store all statistics - now includes x_only_angles and y_only_angles like simple_angle_analyzer.py
        self.current_stats = {
            "total_displacement": (total_x, total_y),
            "total_distance": total_distance,
            "overall_angle_deg": overall_angle_deg,
            "overall_angle_rad": overall_angle_rad,
            "x_component_angle_deg": x_component_angle_deg,
            "x_component_angle_rad": x_component_angle_rad,
            "y_component_angle_deg": y_component_angle_deg,
            "y_component_angle_rad": y_component_angle_rad,
            "x_magnitude_angle": x_magnitude_angle,
            "y_magnitude_angle": y_magnitude_angle,
            "avg_movement_angle_deg": avg_angle_deg,
            "movement_angles": movement_angles,
            "x_only_angles": x_only_angles,  # Added from simple_angle_analyzer.py
            "y_only_angles": y_only_angles,  # Added from simple_angle_analyzer.py
            "path_efficiency": efficiency,
            "num_movements": len(self.movements),
            "path_length": path_length,
            "compass_angle": compass_angle,
            "compass_direction": direction,
            "x_only_movements": x_only_count,
            "y_only_movements": y_only_count,
            "mixed_movements": mixed_count,
            "no_movements": no_movement_count,
        }

    def _print_current_stats(self):
        """Print current angle analysis stats"""
        if not self.current_stats:
            print("No movement data to analyze")
            return

        stats = self.current_stats
        print(f"📊 Movement Analysis:")
        print(
            f"  • Overall angle: {stats['overall_angle_deg']:.1f}° ({stats['compass_direction']})"
        )
        print(
            f"  • X component: {stats['x_component_angle_deg']:.1f}° ({stats['x_magnitude_angle']}°)"
        )
        print(
            f"  • Y component: {stats['y_component_angle_deg']:.1f}° ({stats['y_magnitude_angle']}°)"
        )
        print(
            f"  • Movements: {stats['x_only_movements']} X-only, {stats['y_only_movements']} Y-only, {stats['mixed_movements']} mixed"
        )
        print(f"  • Efficiency: {stats['path_efficiency']:.1%}")

    def get_current_stats(self) -> Optional[Dict]:
        """Get the current angle analysis statistics"""
        return self.current_stats

    def clear_history(self):
        """Clear all movement history (manual reset)"""
        print("🗑️ Look path manually cleared")
        if self.current_stats:
            print("📊 Final stats before clear:")
            self._print_current_stats()
        self.movements.clear()
        self.positions.clear()
        self.current_stats = None
        self.drag_start_time = None

    def get_latest_position(self) -> Optional[Dict]:
        """Get the most recent position"""
        return self.positions[-1] if self.positions else None

    def get_drag_duration(self) -> Optional[float]:
        """Get duration of current drag in seconds, or None if not dragging"""
        if self.drag_start_time is None or not self.mouse_tracking_active:
            return None
        current_time = int(time.time() * 1000)
        return (current_time - self.drag_start_time) / 1000.0

    def is_dragging(self) -> bool:
        """Check if currently in a drag operation"""
        return self.mouse_tracking_active

    def set_execution_callback(self, callback):
        """Set callback to execute discrete MCP commands"""
        self.execution_callback = callback
        print(f"🔗 LookPathTracker execution callback connected")

    def start_mouse_tracking(self):
        """Called when user starts dragging in camera area (mouse press)"""
        if not self.mouse_tracking_active:
            print("🖱️ Started drag operation - accumulating movements")
            self.mouse_tracking_active = True
            self.drag_start_time = int(time.time() * 1000)
            # Reset tracking data for new drag session
            self.movements.clear()
            self.positions.clear()
            self.current_stats = None
        else:
            print("⚠️ start_mouse_tracking() called but tracking already active!")

    def stop_mouse_tracking(self):
        """Called when user stops dragging in camera area (mouse release)"""
        if self.mouse_tracking_active:
            drag_duration = self.get_drag_duration()
            print(f"🖱️ Drag completed ({drag_duration:.1f}s) - executing command")
            self.mouse_tracking_active = False
            self.drag_start_time = None

            # Execute accumulated movement immediately
            self._execute_accumulated_movement("drag_complete")

    def _execute_accumulated_movement(self, trigger_reason):
        """Execute the accumulated movement as an MCP command"""
        if self.current_stats:
            total_x, total_y = self.current_stats["total_displacement"]

            # Convert pixels to degrees using configurable sensitivity
            x_angle = total_x / self.sensitivity
            y_angle = -(
                total_y / self.sensitivity
            )  # Invert Y axis for natural camera control

            # Always print drag analysis report
            print(f"📊 Drag analysis ({trigger_reason}):")
            self._print_current_stats()
            print(f"   🎯 Camera rotation: {x_angle:.1f}°, {y_angle:.1f}°")

            # Execute command if callback is available and movement is significant
            if self.execution_callback and (abs(x_angle) > 0.2 or abs(y_angle) > 0.2):
                mcp_command = {
                    "tool": "lookAngle",
                    "parameters": {
                        "xAngle": round(x_angle, 1),
                        "yAngle": round(y_angle, 1),
                        "speed": "normal",
                    },
                }
                print(f"   ✅ Executing MCP command")
                self.execution_callback(mcp_command)
                
                # NEW: Also log in pygame mode if logging enabled
                if self.mode == "pygame" and self.enable_logging:
                    print(f"LOGGED: {mcp_command}")
                    
            elif not self.execution_callback:
                print(f"   ⚠️  No execution callback set - command not executed")
                
                # NEW: Print in pygame mode if logging enabled (even without execution)
                if self.mode == "pygame" and self.enable_logging and (abs(x_angle) > 0.2 or abs(y_angle) > 0.2):
                    mcp_command = {
                        "tool": "lookAngle",
                        "parameters": {
                            "xAngle": round(x_angle, 1),
                            "yAngle": round(y_angle, 1),
                            "speed": "normal",
                        },
                    }
                    print(f"LOGGED: {mcp_command}")
                    
            else:
                print(
                    f"   🔇 Movement too small to execute: {x_angle:.1f}°, {y_angle:.1f}°"
                )
        else:
            print(f"🔇 No movement data recorded during drag")

        # Always reset after drag completion
        self._reset_tracking_data()

    def _reset_tracking_data(self):
        """Reset tracking data after command execution"""
        self.movements.clear()
        self.positions.clear()
        self.current_stats = None
        print("🗑️ Reset drag tracking data")

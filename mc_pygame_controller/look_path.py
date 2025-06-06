import pygame
import time
import math
from typing import Optional, Tuple, List, Dict

from .constants import *

class LookPathTracker:
    def __init__(self, inactivity_timeout_ms=2000):
        self.movements: List[Dict] = []
        self.positions: List[Dict] = []
        self.max_history = 1000  # Limit history to prevent memory issues
        self.inactivity_timeout_ms = inactivity_timeout_ms  # Default 2 seconds
        self.last_movement_time = None
        self.current_stats = None  # Store latest angle analysis
        self.execution_callback = None  # Callback for MCP command execution

    def add_movement(self, movement_x: int, movement_y: int):
        """Add a new look movement to the history"""
        current_time = int(time.time() * 1000)  # milliseconds

        # Check for inactivity-based reset
        if self.last_movement_time is not None:
            time_since_last = current_time - self.last_movement_time
            if time_since_last > self.inactivity_timeout_ms:
                # Reset due to inactivity
                self._reset_with_message(time_since_last)

        # Update last movement time
        self.last_movement_time = current_time

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

    def _reset_with_message(self, inactivity_duration_ms):
        """Internal method to reset with console logging"""
        # Print final stats before reset if we have any
        if self.current_stats:
            print("\n🔄 Path reset due to inactivity! Final stats:")
            self._print_current_stats()
            print(f"⏱️  Inactivity duration: {inactivity_duration_ms/1000:.1f}s\n")

            # NEW: Convert to MCP format for execution
            if self.execution_callback:
                total_x, total_y = self.current_stats["total_displacement"]

                # Convert pixels to degrees (MCP server uses 5px = 1 degree)
                x_angle = total_x / 5.0
                y_angle = total_y / 5.0

                # Only execute meaningful movements (filter noise)
                if abs(x_angle) > 0.2 or abs(y_angle) > 0.2:
                    mcp_command = {
                        "tool": "lookAngle",
                        "parameters": {
                            "xAngle": round(x_angle, 1),
                            "yAngle": round(y_angle, 1),
                            "speed": "normal",
                        },
                    }
                    self.execution_callback(mcp_command)
        else:
            print(
                f"🕐 Look path reset due to inactivity ({inactivity_duration_ms/1000:.1f}s gap)"
            )

        self.movements.clear()
        self.positions.clear()
        self.current_stats = None

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
        print(f"🔄 Path reset due to inactivity! Final stats:")
        self._print_current_stats()
        # print(f"⏱️  Inactivity duration: {inactivity_duration_ms/1000:.1f}s\n")
        self.movements.clear()
        self.positions.clear()
        self.last_movement_time = None

    def set_inactivity_timeout(self, timeout_ms: int):
        """Set the inactivity timeout in milliseconds"""
        self.inactivity_timeout_ms = timeout_ms
        print(f"⏰ Inactivity timeout set to {timeout_ms/1000:.1f} seconds")

    def get_latest_position(self) -> Optional[Dict]:
        """Get the most recent position"""
        return self.positions[-1] if self.positions else None

    def get_time_since_last_movement(self) -> Optional[float]:
        """Get time in seconds since last movement, or None if no movements yet"""
        if self.last_movement_time is None:
            return None
        current_time = int(time.time() * 1000)
        return (current_time - self.last_movement_time) / 1000.0

    def set_execution_callback(self, callback):
        """Set callback to execute discrete MCP commands"""
        self.execution_callback = callback


class LookPathVisualizationArea:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.origin_x = x + width // 2
        self.origin_y = y + height // 2
        self.scale = 0.5  # Scale factor for movement visualization
        self.grid_size = 20
        self.font = pygame.font.Font(None, 16)

    def draw(self, surface, path_tracker: LookPathTracker):
        # Draw background
        pygame.draw.rect(surface, (20, 20, 20), self.rect)
        pygame.draw.rect(surface, WHITE, self.rect, 2)

        # Draw grid
        self._draw_grid(surface)

        # Draw axes
        self._draw_axes(surface)

        # Draw origin
        self._draw_origin(surface)

        # Draw path and movements
        if len(path_tracker.positions) > 0:
            self._draw_path(surface, path_tracker.positions)
            self._draw_position_markers(surface, path_tracker.positions)
            self._draw_latest_info(surface, path_tracker)

    def _draw_grid(self, surface):
        """Draw grid lines"""
        # Vertical lines
        for x in range(self.rect.x, self.rect.x + self.rect.width, self.grid_size):
            pygame.draw.line(
                surface,
                (40, 40, 40),
                (x, self.rect.y),
                (x, self.rect.y + self.rect.height),
            )
        # Horizontal lines
        for y in range(self.rect.y, self.rect.y + self.rect.height, self.grid_size):
            pygame.draw.line(
                surface,
                (40, 40, 40),
                (self.rect.x, y),
                (self.rect.x + self.rect.width, y),
            )

    def _draw_axes(self, surface):
        """Draw coordinate axes"""
        # Horizontal axis through origin
        pygame.draw.line(
            surface,
            GRAY,
            (self.rect.x, self.origin_y),
            (self.rect.x + self.rect.width, self.origin_y),
            2,
        )
        # Vertical axis through origin
        pygame.draw.line(
            surface,
            GRAY,
            (self.origin_x, self.rect.y),
            (self.origin_x, self.rect.y + self.rect.height),
            2,
        )

    def _draw_origin(self, surface):
        """Draw origin point"""
        pygame.draw.circle(surface, RED, (self.origin_x, self.origin_y), 6)
        pygame.draw.circle(surface, WHITE, (self.origin_x, self.origin_y), 6, 2)

        # Origin label
        text = self.font.render("ORIGIN", True, RED)
        surface.blit(text, (self.origin_x + 10, self.origin_y - 10))

    def _draw_path(self, surface, positions):
        """Draw the accumulated path"""
        if len(positions) < 2:
            return

        # Create points for the path, clipped to the visualization area
        points = []
        for pos in positions:
            x = self.origin_x + pos["x"] * self.scale
            y = self.origin_y + pos["y"] * self.scale

            # Clip to bounds
            x = max(self.rect.x, min(self.rect.x + self.rect.width, x))
            y = max(self.rect.y, min(self.rect.y + self.rect.height, y))
            points.append((int(x), int(y)))

        # Draw path as connected lines
        if len(points) > 1:
            pygame.draw.lines(surface, CYAN, False, points, 2)

    def _draw_position_markers(self, surface, positions):
        """Draw position markers"""
        for i, pos in enumerate(positions):
            x = self.origin_x + pos["x"] * self.scale
            y = self.origin_y + pos["y"] * self.scale

            # Skip if outside bounds
            if (
                x < self.rect.x
                or x > self.rect.x + self.rect.width
                or y < self.rect.y
                or y > self.rect.y + self.rect.height
            ):
                continue

            # Draw small markers for all positions
            pygame.draw.circle(surface, DARK_GRAY, (int(x), int(y)), 2)

        # Draw larger marker for current position
        if positions:
            curr_pos = positions[-1]
            x = self.origin_x + curr_pos["x"] * self.scale
            y = self.origin_y + curr_pos["y"] * self.scale

            if (
                self.rect.x <= x <= self.rect.x + self.rect.width
                and self.rect.y <= y <= self.rect.y + self.rect.height
            ):
                pygame.draw.circle(surface, PURPLE, (int(x), int(y)), 5)
                pygame.draw.circle(surface, WHITE, (int(x), int(y)), 5, 2)

    def _draw_latest_info(self, surface, path_tracker: LookPathTracker):
        """Draw information about the latest movement"""
        # Info panel background
        info_rect = pygame.Rect(
            self.rect.x + 5, self.rect.y + 5, 200, 180
        )  # Made taller
        pygame.draw.rect(surface, (0, 0, 0, 128), info_rect)
        pygame.draw.rect(surface, WHITE, info_rect, 1)

        if not path_tracker.current_stats:
            # Show basic info when no movements
            info_lines = [
                f"No movements recorded",
                f"Inactivity timeout: {path_tracker.inactivity_timeout_ms/1000:.1f}s",
                f"Time since last: N/A",
            ]

            y_offset = info_rect.y + 8
            for line in info_lines:
                text = self.font.render(line, True, WHITE)
                surface.blit(text, (info_rect.x + 5, y_offset))
                y_offset += 16
            return

        stats = path_tracker.current_stats
        latest = path_tracker.get_latest_position()

        # Get time since last movement
        time_since_last = path_tracker.get_time_since_last_movement()
        time_since_str = (
            f"{time_since_last:.1f}s" if time_since_last is not None else "N/A"
        )

        # Color code based on inactivity timeout proximity
        timeout_threshold = path_tracker.inactivity_timeout_ms / 1000.0
        if time_since_last and time_since_last > timeout_threshold * 0.8:
            time_color = (255, 200, 0)  # Orange
        elif time_since_last and time_since_last > timeout_threshold * 0.6:
            time_color = (255, 255, 0)  # Yellow
        else:
            time_color = WHITE

        # Info text with angle analysis
        info_lines = [
            f"Movements: {stats['num_movements']}",
            f"Position: ({latest['x']}, {latest['y']})",
            f"Last Δ: ({latest['movement_x']}, {latest['movement_y']})",
            f"Overall: {stats['overall_angle_deg']:.1f}° ({stats['compass_direction']})",
            f"X angle: {stats['x_component_angle_deg']:.1f}°",
            f"Y angle: {stats['y_component_angle_deg']:.1f}°",
            f"Efficiency: {stats['path_efficiency']:.1%}",
            f"X/Y/Mixed: {stats['x_only_movements']}/{stats['y_only_movements']}/{stats['mixed_movements']}",
            f"Timeout: {timeout_threshold:.1f}s",
        ]

        y_offset = info_rect.y + 8
        for line in info_lines:
            text = self.font.render(line, True, WHITE)
            surface.blit(text, (info_rect.x + 5, y_offset))
            y_offset += 16

        # Special handling for time since last movement (with color coding)
        time_text = f"Idle: {time_since_str}"
        time_surface = self.font.render(time_text, True, time_color)
        surface.blit(time_surface, (info_rect.x + 5, y_offset))

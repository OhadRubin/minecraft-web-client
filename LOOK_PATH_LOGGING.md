# Look Path Logging Mechanism (in pygame)

## Overview
The `LookPathTracker` class in `look_path.py` implements a comprehensive logging system that tracks camera movement patterns and provides real-time analytics with automatic console output.

## Logging Components

### 1. Automatic Reset Logging
**Trigger**: When camera is idle for more than `inactivity_timeout_ms` (default: 2000ms)
**Method**: `_reset_with_message(inactivity_duration_ms)`

```python
# Example output:
🔄 Path reset due to inactivity! Final stats:
📊 Movement Analysis:
  • Overall angle: 45.2° (Northeast)
  • X component: 0.0° (0°)
  • Y component: 90.0° (90°)
  • Movements: 5 X-only, 3 Y-only, 12 mixed
  • Efficiency: 78.5%
⏱️  Inactivity duration: 2.1s
```

### 2. Manual Clear Logging
**Trigger**: When `clear_history()` is called (typically via 'C' key)
**Method**: `clear_history()`

```python
# Example output:
🗑️ Look path manually cleared
🔄 Path reset due to inactivity! Final stats:
[Same detailed stats as above]
```

### 3. Configuration Change Logging
**Trigger**: When inactivity timeout is modified
**Method**: `set_inactivity_timeout(timeout_ms)`

```python
# Example output:
⏰ Inactivity timeout set to 3.0 seconds
```

### 4. Statistics Format
**Method**: `_print_current_stats()`

The stats output includes:
- **Overall angle**: Primary direction of accumulated movement with compass bearing
- **Component angles**: Separate X and Y axis analysis
- **Movement breakdown**: Count of X-only, Y-only, and mixed movements
- **Path efficiency**: Ratio of straight-line distance to actual path length

## Real-Time Data Tracking

### Continuous Analysis
Every camera movement triggers `_update_angle_analysis()` which calculates:

```python
# Statistics stored in self.current_stats:
{
    "total_displacement": (total_x, total_y),
    "total_distance": float,
    "overall_angle_deg": float,
    "compass_direction": str,  # "North", "Northeast", etc.
    "path_efficiency": float,  # 0.0 to 1.0
    "num_movements": int,
    "x_only_movements": int,
    "y_only_movements": int, 
    "mixed_movements": int,
    "movement_angles": List[float],
    # ... additional metrics
}
```

### Visual Status Integration
The logging system integrates with visual display in `LookPathVisualizationArea`:

- **Color-coded idle timer**: Changes color as timeout approaches
- **Real-time stats display**: Shows current statistics in UI panel
- **Position tracking**: Visual markers for movement history

## Timing and Reset Logic

### Inactivity Detection
```python
# Reset triggers when:
time_since_last = current_time - self.last_movement_time
if time_since_last > self.inactivity_timeout_ms:
    self._reset_with_message(time_since_last)
```

### Movement Timestamp Tracking
Each movement stores:
```python
movement = {
    "timestamp": current_time_ms,
    "movement_x": int,
    "movement_y": int,
    "relative_time": int  # Time since first movement
}
```

## Console Output Examples

### Typical Reset Sequence
```
🔄 Path reset due to inactivity! Final stats:
📊 Movement Analysis:
  • Overall angle: -23.7° (Northwest)
  • X component: 180.0° (180°)
  • Y component: -90.0° (-90°)
  • Movements: 8 X-only, 12 Y-only, 15 mixed
  • Efficiency: 65.2%
⏱️  Inactivity duration: 2.3s
```

### Manual Clear
```
🗑️ Look path manually cleared
🔄 Path reset due to inactivity! Final stats:
📊 Movement Analysis:
  • Overall angle: 127.4° (Southeast)
  • X component: 0.0° (0°)
  • Y component: 90.0° (90°)  
  • Movements: 2 X-only, 4 Y-only, 8 mixed
  • Efficiency: 92.1%
```

### No Movement Data
```
🕐 Look path reset due to inactivity (2.1s gap)
```

## Integration with Controller

### Key Bindings
- **'C' key**: Triggers `clear_history()` → Manual reset with logging
- **'R' key**: Reconnect WebSocket (separate from path logging)

### Visual Feedback
The logging system provides data for:
- **Info panel**: Real-time statistics display
- **Color coding**: Idle timeout proximity warnings
- **Path visualization**: Movement history and efficiency

## Usage Patterns

### Data Collection
The logging system is designed for:
1. **Debugging**: Understanding camera movement patterns
2. **Analytics**: Measuring look efficiency and behavior
3. **Research**: Collecting spatial navigation data
4. **User feedback**: Visual confirmation of tracking accuracy

### Performance Considerations
- **History limit**: Max 1000 movements to prevent memory issues
- **Automatic cleanup**: Inactivity-based reset prevents data accumulation
- **Efficient calculation**: Statistics updated incrementally, not recalculated

## Configuration Options

### Timeout Adjustment
```python
tracker.set_inactivity_timeout(3000)  # 3 seconds
# Output: ⏰ Inactivity timeout set to 3.0 seconds
```

### Access to Statistics
```python
stats = tracker.get_current_stats()  # Returns Dict or None
time_idle = tracker.get_time_since_last_movement()  # Returns float or None
```

This logging mechanism provides comprehensive tracking of camera movement patterns with automatic cleanup and detailed console feedback for debugging and analysis purposes. 
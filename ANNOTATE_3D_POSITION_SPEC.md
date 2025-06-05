# annotate_3d_position Command Specification

## Overview

The `annotate_3d_position` command adds a visual marker at specified world coordinates in the Minecraft 3D scene. This enables spatial reasoning by allowing agents to mark locations of interest and receive visual confirmation.

**Status**: Core feasibility validated through browser console testing.

## Command Specification

### Input Format

```json
{
  "type": "annotate_3d_position",
  "worldX": <number>,
  "worldY": <number>, 
  "worldZ": <number>,
  "label": <string, optional>,
  "color": <string, optional>,
  "markerId": <string, optional>
}
```

### Parameters

| Field | Type | Required | Description | Default |
|-------|------|----------|-------------|---------|
| `worldX` | number | Yes | World X coordinate | - |
| `worldY` | number | Yes | World Y coordinate | - |
| `worldZ` | number | Yes | World Z coordinate | - |
| `label` | string | No | Text label displayed above marker | `""` |
| `color` | string | No | CSS color for marker (hex, named, hsl) | `"red"` |
| `markerId` | string | No | Unique identifier for marker | auto-generated |

### Behavior

1. **Marker Creation**: Places a semi-transparent sphere at the specified coordinates
2. **Label Rendering**: If label provided, displays text sprite above marker
3. **Scene Integration**: Adds marker to existing Three.js scene without affecting gameplay
4. **Visual Feedback**: Captures screenshot showing the newly placed marker
5. **Response**: Returns success confirmation with marker details and screenshot

### Output Format

#### Success Response
```json
{
  "type": "annotate_3d_position_result",
  "success": true,
  "markerId": "<generated_or_provided_id>",
  "coordinates": {"x": <number>, "y": <number>, "z": <number>},
  "label": "<provided_label>",
  "color": "<resolved_color>",
  "screenshot": "<base64_encoded_image>",
  "message": "Added 3D marker at (<x>, <y>, <z>)"
}
```

#### Error Response
```json
{
  "type": "annotate_3d_position_result",
  "success": false,
  "error": "<error_description>"
}
```

## Visual Specification

### Marker Appearance
- **Shape**: Sphere with 0.5 block radius
- **Material**: Basic material (no lighting), semi-transparent (80% opacity)
- **Color**: User-specified or red default
- **Positioning**: Exact world coordinates, no snapping to block grid

### Label Appearance  
- **Position**: 1.5 blocks above marker center
- **Style**: White text with black outline, 20px Arial font
- **Background**: Transparent sprite, always faces camera
- **Size**: 4:1 aspect ratio sprite

### Visual Integration
- **Render Order**: Markers render above terrain but below UI
- **Persistence**: Markers remain until page reload (no automatic cleanup)
- **Interaction**: Markers are visual-only (no collision or interaction)

## Error Conditions

| Condition | Error Message | Recovery |
|-----------|---------------|----------|
| Missing coordinates | "Missing required coordinates" | Provide x, y, z values |
| Invalid coordinates | "Invalid coordinate values" | Use numeric values |
| Scene unavailable | "Three.js scene not accessible" | Wait for world load |
| Invalid color | Warning logged, defaults to red | Use valid CSS color |
| Screenshot failure | Returns 1px fallback image | Check canvas state |

## Integration Points

### WebSocket Interface
- **Command Type**: `annotate_3d_position` added to existing command system
- **Response Handling**: Follows existing async response pattern
- **Error Format**: Consistent with other command error responses

### MCP Tool Interface
```
Function: annotate_3d_position(x, y, z, label="", color="red")
Returns: {success: boolean, markerId: string, screenshot: string}
Throws: Error on failure with descriptive message
```

### Three.js Scene
- **Access Method**: Via `window.world.scene` global reference  
- **Object Naming**: Markers use `marker_<timestamp>_<random>` format
- **Metadata**: Objects tagged with `isAnnotationMarker: true`
- **Cleanup**: No automatic removal (future enhancement)

## Performance Characteristics

### Resource Usage
- **Memory**: ~1KB per marker (minimal geometry + material)
- **Rendering**: Uses efficient BasicMaterial, no lighting calculations
- **Limits**: No enforced maximum (monitor performance in practice)

### Response Time
- **Typical**: <100ms for marker creation + screenshot
- **Maximum**: 10 second timeout before error response
- **Factors**: Scene complexity affects screenshot capture time

## Validation Rules

### Input Validation
- Coordinates must be finite numbers
- Color must be valid CSS color string (or empty for default)
- Label must be string under 100 characters (recommended)
- MarkerId must be unique if provided

### Scene Validation  
- Three.js scene must be accessible
- WebGL context must be active
- Canvas element must be available for screenshots

## Success Criteria

1. **Functional**: Marker appears at exact specified coordinates
2. **Visual**: Marker is clearly visible with correct color/label
3. **Response**: Screenshot shows marker in scene context
4. **Integration**: Works seamlessly with existing MCP tool chain
5. **Reliability**: <5% failure rate under normal conditions

## Future Considerations

### Planned Enhancements
- Marker removal command
- List/query existing markers  
- Update marker properties
- Custom marker shapes

### Scope Limitations
- No marker management in initial version
- No persistence across sessions
- No complex animations or effects
- Basic sphere shape only

## Testing Strategy

### Validation Levels
1. **Unit**: WebSocket command processing
2. **Integration**: MCP tool → WebSocket → Scene modification  
3. **End-to-end**: Agent loop → Screenshot → Visual confirmation
4. **Load**: Multiple markers performance testing

### Test Cases
- Valid coordinates with/without label/color
- Invalid inputs (missing coords, bad colors)  
- Scene not ready conditions
- Multiple rapid marker creation
- Screenshot capture under various scene states

## Dependencies

- **Three.js Scene**: Must be initialized and accessible
- **WebSocket Connection**: Active connection for command/response
- **Canvas Element**: Available for screenshot capture  
- **WebGL Support**: Required for 3D rendering

**Implementation Target**: 1-2 days for basic functionality following existing command patterns. 
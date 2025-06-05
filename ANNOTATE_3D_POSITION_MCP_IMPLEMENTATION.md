# annotate_3d_position MCP Tool Specification

## Overview

This specification defines the requirements for adding the `annotate_3d_position` tool to the existing Minecraft MCP server. The tool enables spatial reasoning by placing visual markers at 3D world coordinates and returning visual confirmation via screenshots.

## Functional Requirements

### Tool Interface

**Function Signature**: `annotate_3d_position(x: number, y: number, z: number, label?: string, color?: string)`

**Parameters**:
- `x`, `y`, `z`: World coordinates for marker placement (required, finite numbers)
- `label`: Optional text label displayed above marker (default: empty string)
- `color`: Marker color from predefined set (default: "red")

**Return Value**: Tool execution result containing success confirmation and screenshot showing the placed marker

### Behavioral Requirements

1. **Marker Placement**: Tool must place a visual marker at exact world coordinates
2. **Color Support**: Must support standard color palette (red, blue, green, yellow, orange, purple, pink, cyan, white)
3. **Label Display**: Optional text labels positioned above markers
4. **Visual Confirmation**: Screenshot capture showing marker in scene context
5. **Error Handling**: Graceful failure with descriptive error messages

### Integration Requirements

1. **MCP Compatibility**: Tool must integrate with existing FastMCP server infrastructure
2. **WebSocket Communication**: Use existing WebSocket connection to Minecraft client
3. **Screenshot Integration**: Leverage existing screenshot capture functionality
4. **Error Consistency**: Follow established error handling patterns

## Technical Architecture

### Command Flow

1. MCP tool receives parameters and validates input
2. Tool sends annotation command via existing WebSocket infrastructure
3. Browser client creates 3D marker in Three.js scene
4. Tool captures screenshot showing annotation result
5. Tool returns formatted response with confirmation and visual proof

### Data Contracts

**WebSocket Command Format**:
```
Command Type: "annotate_3d_position"
Required Fields: worldX, worldY, worldZ
Optional Fields: label, color
```

**Response Format**:
```
Success Response: Contains text confirmation and base64 screenshot
Error Response: Contains error message and failure details
```

### Browser Integration Requirements

1. **Command Recognition**: Browser must recognize annotation command type
2. **3D Object Creation**: Create visual marker (cube geometry) at specified coordinates
3. **Material Properties**: Semi-transparent colored material for visibility
4. **Text Rendering**: Optional text sprite for labels using canvas texture
5. **Scene Management**: Add objects to existing Three.js scene without disruption

## Validation Requirements

### Input Validation

- Coordinates must be finite numeric values
- Color must be from approved color set or default to red
- Label must be reasonable string length (under 100 characters)
- All parameters properly typed and sanitized

### Scene Validation

- Three.js scene must be accessible and ready
- WebGL context must be active for rendering
- Canvas element available for screenshot capture

### Error Conditions

| Condition | Expected Behavior |
|-----------|------------------|
| Invalid coordinates | Return descriptive error message |
| Unsupported color | Default to red, log warning |
| Scene not ready | Return error indicating world not loaded |
| Screenshot failure | Return error with fallback handling |

## Performance Requirements

### Resource Management

- Markers use minimal geometry and material resources
- No automatic cleanup (markers persist until page reload)
- No enforced limits on marker count initially

### Response Time

- Marker creation should complete within 200ms
- Screenshot capture should complete within 10 seconds
- Total tool execution should not exceed 15 seconds

## Quality Requirements

### Reliability

- Tool should succeed under normal conditions (>95% success rate)
- Graceful degradation when dependencies unavailable
- Consistent behavior across different browser states

### Usability

- Markers clearly visible in 3D scene
- Labels readable and properly positioned
- Colors distinguishable and meaningful
- Screenshots capture marker in context

### Maintainability

- Tool follows existing MCP server patterns
- Browser code integrates with existing WebSocket handlers
- Error messages provide actionable feedback

## Testing Requirements

### Validation Criteria

1. **Functional Testing**: Marker appears at exact coordinates with correct color and label
2. **Integration Testing**: Tool works with existing MCP infrastructure
3. **Error Testing**: Appropriate error handling for all failure modes
4. **Visual Testing**: Screenshots clearly show annotation results
5. **Load Testing**: Performance acceptable with multiple markers

### Test Scenarios

- Valid coordinates with and without labels/colors
- Invalid inputs (non-numeric coordinates, unsupported colors)
- Browser state variations (scene not ready, WebGL issues)
- Multiple rapid tool calls
- Screenshot capture under various scene conditions

## Compatibility Requirements

### Existing System Integration

- Must not interfere with existing MCP tools
- Must not disrupt existing WebSocket communication
- Must not affect existing browser functionality
- Must follow established response format conventions

### Browser Requirements

- Works with existing Three.js scene setup
- Compatible with current WebSocket command structure
- Functions within existing security constraints

## Implementation Constraints

### Scope Limitations

- Basic cube markers only (no complex shapes)
- Standard color palette only
- No marker management features (removal, editing)
- No persistence across browser sessions
- No animations or advanced visual effects

### Dependencies

- Existing MCP server infrastructure
- Active WebSocket connection to browser
- Three.js scene initialization
- Screenshot capture capability

## Success Criteria

1. **Core Functionality**: Tool successfully places markers at specified coordinates
2. **Visual Feedback**: Screenshots clearly show placed markers
3. **Error Handling**: Appropriate responses for all error conditions
4. **Performance**: Meets response time requirements
5. **Integration**: Works seamlessly with existing tools
6. **Reliability**: Consistent operation under normal usage

## Future Considerations

### Planned Enhancements

- Marker removal functionality
- Additional marker shapes
- Marker querying and listing
- Enhanced visual properties

### Scope Boundaries

- No complex marker management initially
- No advanced graphics or animations
- No persistent storage requirements
- Focus on basic spatial annotation needs

**Target Outcome**: Fully functional 3D annotation capability enabling spatial reasoning for Visual SKETCHPAD trajectory collection. 
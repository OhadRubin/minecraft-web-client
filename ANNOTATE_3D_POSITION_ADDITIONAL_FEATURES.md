# Additional Feature Ideas for `annotate_3d_position`

These enhancements build on the initial implementation of the `annotate_3d_position` command. They are not yet implemented but would provide useful functionality for future trajectory collection and spatial reasoning experiments.

## Marker Management
- **Remove Markers**: Add `remove_3d_marker(markerId)` command to delete markers by ID.
- **List Markers**: Expose a command to enumerate existing markers with coordinates and labels.
- **Update Markers**: Allow changing label, color, or position of an existing marker.
- **Persistent Markers**: Optionally store markers in the MCP server so they survive page reloads.

## Visualization Options
- **Different Shapes**: Support cubes, arrows, or bounding boxes in addition to spheres.
- **Size Control**: Parameter for marker radius/scale to highlight larger areas.
- **Animated Markers**: Pulsing or spinning markers to draw attention.
- **Grouped Markers**: Tag markers with categories and toggle visibility per group.

## Interaction Features
- **Clickable Markers**: Display marker info on click or allow teleporting the player/agent.
- **Measurement Tools**: Compute distances between markers or show coordinate differences.
- **Path Annotation**: Connect multiple markers with lines to visualize trajectories.

## Collaboration & Export
- **Shareable Markers**: Broadcast markers to other connected viewers or store them in trajectory logs.
- **Import/Export**: Load and save marker sets as JSON for later review.

These features would expand the usefulness of 3D annotations and help gather richer Visual SKETCHPAD data.

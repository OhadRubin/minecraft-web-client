# Annotate 3D Position - Potential Enhancements

This document lists potential additional features for the `annotate_3d_position` tool that could further support Visual SKETCHPAD data collection and analysis.

1. **Marker Removal**
   - Command to remove a specific marker by `markerId` or clear all markers.
2. **Marker Listing & Querying**
   - Retrieve a list of existing markers with their coordinates and labels for inspection or automated reasoning.
3. **Update Existing Markers**
   - Ability to change color, label or position of an existing marker without recreating it.
4. **Different Marker Shapes**
   - Support cubes, arrows, and crosshair styles in addition to the default sphere for richer annotations.
5. **Size & Orientation Parameters**
   - Optional parameters to control marker size and facing direction, useful for emphasizing points of interest.
6. **Distance Measurement Utilities**
   - Tools to draw and label lines between markers to quickly measure distances or create simple 3D sketches.
7. **Persistent Marker Storage**
   - Optionally save marker data to local storage or server-side so annotations persist across sessions.
8. **Automatic Marker Numbering**
   - Auto-generate sequential labels (e.g., "1", "2", "3") to reference markers easily in conversations.
9. **Visibility Toggling**
   - UI control or command to hide/show all annotations to avoid clutter while exploring the world.
10. **Export/Import Markers**
    - Serialize markers to JSON for dataset generation or to share annotations between users.

These enhancements are not required for the initial implementation but could improve usability and dataset quality as the project evolves.

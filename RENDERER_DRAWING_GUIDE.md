# 3D Visual SKETCHPAD Tools - Renderer Implementation Guide

This guide explains how to implement the 3D Visual SKETCHPAD tools in the Minecraft web client's Three.js renderer for the Visual SKETCHPAD research project.

## Project Context

**Goal**: Implement 3D spatial reasoning tools for collecting 50K Visual SKETCHPAD trajectories in Minecraft.

**Research Hypothesis**: 3D spatial reasoning skills learned in Minecraft will transfer to web agents and other domains.

**Phase 0 MVP Tools** (Priority Implementation):
1. `annotate_3d_position(x, y, z, label, color)` - Mark 3D coordinates with visual indicators
2. `zoom_and_orient(target_x, target_y, target_z, distance)` - Point camera toward coordinates  
3. `detect_blocks_in_view(block_types)` - Scan and return block coordinates

## Architecture Overview

```
Agent Loop (Python) 
    ↓ MCP calls
MCP Server (TypeScript) - minecraft-mcp-server.ts
    ↓ WebSocket commands  
Minecraft Web Client (Browser/Three.js)
    ↓ Visual feedback
Screenshots back to LLM
```

## Key Files for 3D Visual SKETCHPAD

### Core Implementation Files
- `minecraft-mcp-server.ts` - MCP server with tool definitions
- `renderer/viewer/lib/worldrendererThree.ts` - Three.js scene access
- `renderer/viewer/three/worldrendererThree.ts` - World rendering implementation
- `src/wsCommandClient.ts` - WebSocket command handling

### Development Setup

1. **Start the full stack**:
   ```bash
   pnpm start  # Start Minecraft web client
   ```

2. **Access the Global Renderer** (for testing):
   In browser console: `renderer` (WebGLRenderer instance is globally accessible)

## Implementation Priority: `annotate_3d_position` Tool

**Start Here**: This is the highest priority tool to prove scene modification works.

### 1. Browser Console Testing (Do This First!)

Test Three.js scene access in browser console to prove feasibility:

```javascript
// Verify renderer access
console.log(renderer);

// Get the scene (try different access patterns)
const scene = viewer?.scene || renderer?.scene || window.scene;
console.log(scene);

// Create a test marker
const geometry = new THREE.BoxGeometry(1, 1, 1);
const material = new THREE.MeshBasicMaterial({ color: 0xff0000 });
const testCube = new THREE.Mesh(geometry, material);
testCube.position.set(0, 65, 0);  // Place above ground
scene.add(testCube);

// If successful, you should see a red cube in the world!
```

**Success Criteria**: Can add a visible colored cube to the Minecraft world at specific coordinates.

### 2. `annotate_3d_position` Implementation Pattern

Once browser testing works, implement in MCP server:

```typescript
// In minecraft-mcp-server.ts
async function annotate3dPosition(x: number, y: number, z: number, label: string, color: string = 'red') {
  // Send WebSocket command to add 3D marker
  const command = {
    type: 'annotate_3d_position',
    x, y, z, label, color
  };
  
  await sendWebSocketCommand(command);
  
  // Capture screenshot showing the annotation
  const screenshot = await captureScreenshot();
  return screenshot;
}
```

### 3. WebSocket Command Handler

Add to web client's WebSocket handler:

```typescript
// In src/wsCommandClient.ts (or appropriate file)
case 'annotate_3d_position':
  const { x, y, z, label, color } = data;
  
  // Access the Three.js scene
  const scene = getWorldScene(); // Function to get scene reference
  
  // Create 3D marker
  const marker = create3DMarker(x, y, z, color, label);
  scene.add(marker);
  break;
```

### 4. 3D Marker Creation Functions

```typescript
function create3DMarker(x: number, y: number, z: number, color: string, label?: string) {
  // Create sphere marker
  const geometry = new THREE.SphereGeometry(0.3, 12, 8);
  const material = new THREE.MeshBasicMaterial({ color: color });
  const marker = new THREE.Mesh(geometry, material);
  marker.position.set(x, y, z);
  
  // Add text label if provided
  if (label) {
    const textSprite = createTextSprite(label);
    textSprite.position.set(x, y + 1, z);
    marker.add(textSprite);
  }
  
  return marker;
}

function createTextSprite(text: string) {
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d');
  context.font = '20px Arial';
  context.fillStyle = 'white';
  context.fillText(text, 0, 20);
  
  const texture = new THREE.CanvasTexture(canvas);
  const spriteMaterial = new THREE.SpriteMaterial({ map: texture });
  const sprite = new THREE.Sprite(spriteMaterial);
  sprite.scale.set(2, 1, 1);
  
  return sprite;
}
```

## Next Steps: Implementation Roadmap

### ⚠️ SCOPE DISCIPLINE WARNING ⚠️

**Remember**: The goal is to prove the core hypothesis with minimal implementation. Don't get distracted by perfect graphics or complex features!

### Immediate Actions (This Week):

1. **Browser Console Test** (TODAY):
   - Open Minecraft web client
   - Test scene access patterns in console
   - Add a simple colored cube
   - **Success = Scene modification is possible**

2. **Implement `annotate_3d_position`** (Day 1-2):
   - Add WebSocket command handler
   - Create simple sphere markers
   - Test via MCP server
   - **Success = LLM can mark 3D locations**

3. **Implement `zoom_and_orient`** (Day 3):
   - Calculate yaw/pitch from coordinates
   - Use existing `lookAngle` tool
   - **Success = LLM can adjust viewpoint**

4. **Implement `detect_blocks_in_view`** (Day 4):
   - Scan bot's nearby blocks
   - Filter by block type
   - Return coordinate list
   - **Success = LLM can identify objects**

### Testing Pattern:

```bash
# Test each tool via agent loop
python simple_client.py --msg "annotate_3d_position(100, 64, 200, 'test', 'red')"
python simple_client.py --msg "zoom_and_orient(100, 64, 200, 5)"
python simple_client.py --msg "detect_blocks_in_view(['chest', 'door'])"
```

### Success Criteria for Phase 0:
- ✅ LLM can mark specific 3D locations (spatial reasoning)
- ✅ LLM can adjust viewpoint for better visibility (camera control)  
- ✅ LLM can identify and locate objects in 3D space (object detection)
- ✅ All tools work together in a single trajectory (integration)
- ✅ Takes <2 weeks to implement (speed)

## Implementation Scope Limits

### ✅ DO (Minimum Viable):
- Simple colored spheres for markers
- Basic text sprites for labels
- Coordinate-based camera pointing
- Simple block coordinate scanning
- File-based screenshots

### ❌ DON'T (Scope Creep):
- Fancy particle effects or animations
- Complex UI for annotation management  
- Computer vision for object detection
- Advanced graphics or shaders
- In-memory image processing
- Multiple marker types or styles
- Sophisticated error handling

### MVP Mantras:
- **"Proof of Concept"** - Show it works, don't perfect it
- **"Single Path"** - Don't explore multiple approaches
- **"Existing Tools"** - Leverage working WebSocket/MCP setup
- **"If it doesn't help collect 50 trajectories, it's scope creep!"**

## Key Files to Modify

1. **`minecraft-mcp-server.ts`** - Add 3 new tool definitions
2. **`src/wsCommandClient.ts`** - Add WebSocket command handlers  
3. **Three.js scene access** - Find the right scene reference pattern
4. **Screenshot integration** - Use existing `captureScreenshot()`

## Current Status

**Where we left off**: User confirmed `renderer` object is accessible in Chrome DevTools. 

**Next action**: Test adding a 3D marker in browser console to prove scene modification works.

**Decision point**: If Three.js test works → implement full tools. If not → find alternative approach.

## Remember: Tools as Research Novelty

The 3D spatial reasoning tools are the unique research contribution. Everything else (collection, training, evaluation) builds on existing patterns. Focus on getting these 3 tools working, not on making them perfect.




WHAT WORKED:
```
  // Add a grid of colored cubes around the player
  if (window.world && window.world.scene) {
      // Get player position if available
      const playerPos = window.world.camera?.position || { x: 0, y: 64, z: 0 };
      console.log('Player position:', playerPos);

      // Create a 5x5 grid of cubes near the player
      for (let x = -5; x <= 5; x++) {
          for (let z = -5; z <= 5; z++) {
              const geometry = new THREE.BoxGeometry(1, 1, 1);
              // Different colors based on position
              const hue = (x + 5) * 36 + (z + 5) * 12; // Creates rainbow effect
              const material = new THREE.MeshBasicMaterial({
                  color: new THREE.Color(`hsl(${hue}, 100%, 50%)`)
              });
              const cube = new THREE.Mesh(geometry, material);

              // Position relative to player, at ground level + 5 blocks up
              cube.position.set(
                  playerPos.x + x * 2,
                  playerPos.y + 5,
                  playerPos.z + z * 2
              );
              cube.name = `test-cube-${x}-${z}`;

              window.world.scene.add(cube);
          }
      }

      console.log('✅ Added 121 colored cubes in a 5x5 grid above player!');
      console.log('Scene children count:', window.world.scene.children.length);

      // Also add a large red cube right in front of the camera
      const bigGeometry = new THREE.BoxGeometry(3, 3, 3);
      const bigMaterial = new THREE.MeshBasicMaterial({ color: 0xff0000 });
      const bigCube = new THREE.Mesh(bigGeometry, bigMaterial);
      bigCube.position.set(playerPos.x, playerPos.y, playerPos.z - 10); // 10 blocks in front
      bigCube.name = 'big-red-cube';
      window.world.scene.add(bigCube);

      console.log('✅ Added big red cube in front of camera!');
  }
  ```
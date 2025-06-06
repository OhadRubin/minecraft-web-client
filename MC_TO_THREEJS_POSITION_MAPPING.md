# Mapping Minecraft Block Coordinates to Three.js Positions

Understanding how Minecraft's world coordinates translate to the Three.js scene is important when adding custom geometry or positioning the camera in the web client.

## Blocks vs. Three.js Units

- The renderer uses **one Three.js unit per Minecraft block**.
- Block models are centered on the block position. To align a mesh with the center of a block, add `0.5` to the `x`, `y`, and `z` coordinates.

## Helper Function

The file `renderer/viewer/lib/mesher/standaloneRenderer.ts` exports a utility to handle this offset:

```ts
export const setBlockPosition = (object: THREE.Object3D, position: { x: number, y: number, z: number }) => {
  object.position.set(position.x + 0.5, position.y + 0.5, position.z + 0.5)
}
```

This function ensures that any mesh is placed at the exact center of a Minecraft block.

## Camera Placement Example

The `resetCamera` method in `renderer/playground/baseScene.ts` demonstrates the same +0.5 offset when positioning the camera and its target:

```ts
this.controls?.target.set(targetPos.x + 0.5, targetPos.y + 0.5, targetPos.z + 0.5)
viewer.camera.lookAt(targetPos.x + 0.5, targetPos.y + 0.5, targetPos.z + 0.5)
viewer.camera.position.set(cameraPos.x + 0.5, cameraPos.y + 0.5, cameraPos.z + 0.5)
```

## Practical Steps

1. **Get the block coordinates** (e.g., from `bot.entity.position` or `window.world.camera.position`).
2. **Add 0.5 to each axis** when you want the object centered on that block.
3. **Set the mesh position** with the adjusted coordinates and add it to `window.world.scene`.

This approach aligns Three.js objects precisely with the Minecraft world, making it easy to overlay custom visuals like blocks, indicators, or camera targets.

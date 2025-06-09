import { MouseCommand } from '../types'
import { onCameraMove } from '../../cameraRotationControls'
import { moveWsCursorBy, emitWsMousemove } from '../../react/WsCursor'
import { miscUiState } from '../../globalState'

export class MovementCommandHandler {
  constructor(private bot: any) {}

  async handleControl(cmd: MouseCommand) {
    this.bot.setControlState(cmd.control!, cmd.state)
  }

  async handleMove(cmd: MouseCommand) {
    const coordToAction = [
      ['z', -1, 'forward'],
      ['z', 1, 'back'],
      ['x', -1, 'left'],
      ['x', 1, 'right']
    ] as const
    const vector: Record<string, number | undefined> = { x: cmd.x, z: cmd.z }
    const newState: Record<string, boolean> = {}
    for (const [coord, v] of Object.entries(vector)) {
      if (v === undefined || Math.abs(v) < 0.3) continue
      const mappedValue = v < 0 ? -1 : 1
      const foundAction = coordToAction.find(([c, mapV]) => c === coord && mapV === mappedValue)?.[2]
      if (foundAction) newState[foundAction] = true
    }
    for (const key of ['forward', 'back', 'left', 'right'] as const) {
      const desired = !!newState[key]
      if (desired !== this.bot.controlState[key]) {
        this.bot.setControlState(key, desired)
      }
    }
    if (cmd.x !== undefined && cmd.z !== undefined) {
      const dx = cmd.x * 2
      const dy = cmd.z * 2
      moveWsCursorBy(dx, dy)
      emitWsMousemove()
    }
  }

  async handleLook(cmd: MouseCommand) {
    onCameraMove({ movementX: cmd.movementX ?? 0, movementY: cmd.movementY ?? 0, type: 'ws' })

    // Also move cursor when using gamepad input (for inventory/UI navigation)
    if (miscUiState.usingGamepadInput && (cmd.movementX !== undefined || cmd.movementY !== undefined)) {
      const dx = (cmd.movementX || 0) * 0.1 // Adjust sensitivity as needed
      const dy = (cmd.movementY || 0) * 0.1
      moveWsCursorBy(dx, dy)
      emitWsMousemove()
    }
  }

  async handleLookTouch(cmd: MouseCommand) {
    if (cmd.currentX !== undefined && cmd.lastX !== undefined &&
      cmd.currentY !== undefined && cmd.lastY !== undefined) {
      onCameraMove({
        movementX: (cmd.currentX - cmd.lastX),
        movementY: (cmd.currentY - cmd.lastY),
        type: 'touchmove',
        stopPropagation: () => { } // No-op function for WebSocket context
      })
    }
  }
}
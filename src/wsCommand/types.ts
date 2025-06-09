export interface MouseCommand {
  type:
    | 'control'
    | 'leftDown'
    | 'leftUp'
    | 'rightDown'
    | 'rightUp'
    | 'chat'
    | 'move'
    | 'look'
    | 'lookTouch'
    | 'clickElement'
    | 'documentMouseEvent'
    | 'setHotbarSlot'
    | 'scrollHotbar'
    | 'dropItem'
    | 'swapHands'
    | 'cursor'
    | 'getScreenshot'
    | 'getBotStatus'
    | 'annotate_3d_position'
    | 'inventory'
  control?: string
  state?: boolean
  message?: string
  x?: number
  z?: number
  movementX?: number
  movementY?: number
  currentX?: number
  lastX?: number
  currentY?: number
  lastY?: number
  selector?: string
  action?: 'down' | 'up' | 'click'
  // documentMouseEvent fields
  button?: 0 | 2
  updateMouse?: boolean
  // setHotbarSlot fields
  slot?: number
  // scrollHotbar fields
  direction?: 1 | -1
  // dropItem fields
  amount?: number
  // annotate_3d_position fields
  worldX?: number
  worldY?: number
  worldZ?: number
  label?: string
  color?: string
  markerId?: string
}
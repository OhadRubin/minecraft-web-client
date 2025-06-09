export interface MouseCommand {
  type:
    | 'control'
    | 'leftDown'
    | 'leftUp'
    | 'rightDown'
    | 'rightUp'
    | 'contextRightClick'
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
  | 'gamepadConnect'
  | 'gamepadDisconnect'
  | 'gamepadButtonPress'
  | 'gamepadDestroy'
  | 'gamepadJoystickMove'
  | 'gamepadJoystickCenter'
  | 'gamepadJoystickPulse'
  | 'gamepadJoystickAnimate'
  | 'gamepadJoystickCircular'
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
  // gamepad fields
  buttonIndex?: number
  duration?: number
  // gamepad joystick fields
  stickIndex?: number // 0 for left stick, 1 for right stick
  y?: number // -1 to 1 for joystick Y axis (note: x is already defined above)
  fromX?: number // for animation from position
  fromY?: number // for animation from position  
  toX?: number // for animation to position
  toY?: number // for animation to position
  radius?: number // for circular movement
  clockwise?: boolean // for circular movement direction
}
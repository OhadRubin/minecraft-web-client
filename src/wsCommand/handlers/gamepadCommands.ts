import { MouseCommand } from '../types'
import { gamepadSimulator } from '../../gamepadSimulator'

export class GamepadCommandHandler {
  private isConnected = false

  constructor() { }

  async handleGamepadConnect(cmd: MouseCommand) {
    try {
      console.log('[WsCommandClient] Creating virtual gamepad')

      // Create the visual gamepad
      gamepadSimulator.create()

      // Connect it (dispatches gamepadconnected event)
      gamepadSimulator.connect()

      this.isConnected = true
      console.log('[WsCommandClient] Virtual gamepad connected successfully')
    } catch (error) {
      console.error('[WsCommandClient] Error connecting gamepad:', error)
    }
  }

  async handleGamepadDisconnect(cmd: MouseCommand) {
    try {
      console.log('[WsCommandClient] Disconnecting virtual gamepad')

      gamepadSimulator.disconnect()
      this.isConnected = false

      console.log('[WsCommandClient] Virtual gamepad disconnected successfully')
    } catch (error) {
      console.error('[WsCommandClient] Error disconnecting gamepad:', error)
    }
  }

  async handleGamepadButtonPress(cmd: MouseCommand) {
    try {
      const buttonIndex = cmd.buttonIndex ?? 0
      const duration = cmd.duration ?? 100

      console.log(`[WsCommandClient] Pressing gamepad button ${buttonIndex} for ${duration}ms`)

      // pressButton() now handles auto-connect internally
      gamepadSimulator.pressButton(buttonIndex, duration)

      // Update our tracking state if it auto-connected
      if (gamepadSimulator.fakeController.connected) {
        this.isConnected = true
      }

      console.log(`[WsCommandClient] Successfully pressed gamepad button ${buttonIndex}`)
    } catch (error) {
      console.error('[WsCommandClient] Error pressing gamepad button:', error)
    }
  }

  async handleGamepadJoystickMove(cmd: MouseCommand) {
    try {
      const stickIndex = cmd.stickIndex ?? 0 // 0 for left stick, 1 for right stick
      const x = cmd.x ?? 0 // -1 to 1
      const y = cmd.y ?? 0 // -1 to 1

      console.log(`[WsCommandClient] Moving gamepad ${stickIndex === 0 ? 'left' : 'right'} joystick to (${x}, ${y})`)

      gamepadSimulator.moveJoystick(stickIndex, x, y)

      // Update our tracking state if it auto-connected
      if (gamepadSimulator.fakeController.connected) {
        this.isConnected = true
      }

      console.log(`[WsCommandClient] Successfully moved gamepad joystick`)
    } catch (error) {
      console.error('[WsCommandClient] Error moving gamepad joystick:', error)
    }
  }

  async handleGamepadJoystickCenter(cmd: MouseCommand) {
    try {
      const stickIndex = cmd.stickIndex ?? 0 // 0 for left stick, 1 for right stick

      console.log(`[WsCommandClient] Centering gamepad ${stickIndex === 0 ? 'left' : 'right'} joystick`)

      gamepadSimulator.centerJoystick(stickIndex)

      console.log(`[WsCommandClient] Successfully centered gamepad joystick`)
    } catch (error) {
      console.error('[WsCommandClient] Error centering gamepad joystick:', error)
    }
  }

  async handleGamepadJoystickPulse(cmd: MouseCommand) {
    try {
      const stickIndex = cmd.stickIndex ?? 0 // 0 for left stick, 1 for right stick
      const x = cmd.x ?? 0 // -1 to 1
      const y = cmd.y ?? 0 // -1 to 1
      const duration = cmd.duration ?? 500

      console.log(`[WsCommandClient] Pulsing gamepad ${stickIndex === 0 ? 'left' : 'right'} joystick to (${x}, ${y}) for ${duration}ms`)

      gamepadSimulator.pulseJoystick(stickIndex, x, y, duration)

      // Update our tracking state if it auto-connected
      if (gamepadSimulator.fakeController.connected) {
        this.isConnected = true
      }

      console.log(`[WsCommandClient] Successfully pulsed gamepad joystick`)
    } catch (error) {
      console.error('[WsCommandClient] Error pulsing gamepad joystick:', error)
    }
  }

  async handleGamepadJoystickAnimate(cmd: MouseCommand) {
    try {
      const stickIndex = cmd.stickIndex ?? 0 // 0 for left stick, 1 for right stick
      const fromX = cmd.fromX ?? 0
      const fromY = cmd.fromY ?? 0
      const toX = cmd.toX ?? 0
      const toY = cmd.toY ?? 0
      const duration = cmd.duration ?? 1000

      console.log(`[WsCommandClient] Animating gamepad ${stickIndex === 0 ? 'left' : 'right'} joystick from (${fromX}, ${fromY}) to (${toX}, ${toY}) over ${duration}ms`)

      gamepadSimulator.animateJoystick(stickIndex, fromX, fromY, toX, toY, duration)

      // Update our tracking state if it auto-connected
      if (gamepadSimulator.fakeController.connected) {
        this.isConnected = true
      }

      console.log(`[WsCommandClient] Successfully started gamepad joystick animation`)
    } catch (error) {
      console.error('[WsCommandClient] Error animating gamepad joystick:', error)
    }
  }

  async handleGamepadJoystickCircular(cmd: MouseCommand) {
    try {
      const stickIndex = cmd.stickIndex ?? 0 // 0 for left stick, 1 for right stick
      const radius = cmd.radius ?? 0.8
      const duration = cmd.duration ?? 2000
      const clockwise = cmd.clockwise ?? true

      console.log(`[WsCommandClient] Starting ${clockwise ? 'clockwise' : 'counter-clockwise'} circular movement for gamepad ${stickIndex === 0 ? 'left' : 'right'} joystick`)

      gamepadSimulator.circularJoystickMovement(stickIndex, radius, duration, clockwise)

      // Update our tracking state if it auto-connected
      if (gamepadSimulator.fakeController.connected) {
        this.isConnected = true
      }

      console.log(`[WsCommandClient] Successfully started gamepad joystick circular movement`)
    } catch (error) {
      console.error('[WsCommandClient] Error starting gamepad joystick circular movement:', error)
    }
  }

  async handleGamepadDestroy(cmd: MouseCommand) {
    try {
      console.log('[WsCommandClient] Destroying virtual gamepad')

      gamepadSimulator.destroy()
      this.isConnected = false

      console.log('[WsCommandClient] Virtual gamepad destroyed successfully')
    } catch (error) {
      console.error('[WsCommandClient] Error destroying gamepad:', error)
    }
  }
}
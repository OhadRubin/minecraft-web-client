import { MouseCommand } from '../types'
import { gamepadSimulator } from '../../gamepadSimulator'
import { gamepadUiCursorState, moveGamepadCursorBy } from '../../react/GamepadUiCursor'
import { emitMousemove } from '../../controls'
import { isGameActive } from '../../globalState'

export class GamepadCommandHandler {
  private isConnected = false
  // Track active button states to prevent duplicate actions
  private activeButtons = new Set<number>()
  // Track button press timing
  private buttonStartTimes = new Map<number, number>()

  constructor(private bot: any) { }

  async handleGamepadConnect(cmd: MouseCommand) {
    try {

      // Create the visual gamepad
      gamepadSimulator.create()

      // Connect it (dispatches gamepadconnected event)
      gamepadSimulator.connect()

      this.isConnected = true
    } catch (error) {
      console.error('[WsCommandClient] Error connecting gamepad:', error)
    }
  }

  async handleGamepadDisconnect(cmd: MouseCommand) {
    try {

      gamepadSimulator.disconnect()
      this.isConnected = false

    } catch (error) {
      console.error('[WsCommandClient] Error disconnecting gamepad:', error)
    }
  }

  async handleGamepadButtonPressDown(cmd: MouseCommand) {
    try {
      const buttonIndex = cmd.buttonIndex ?? 0

      // Check if this is a mouse-equivalent button and if modals are open
      const hasModalsOpen = !isGameActive(true)
      console.log(`[WsCommandClient] Executing gamepadButtonPressDown ${buttonIndex}, hasModalsOpen=${hasModalsOpen}`)

      // Handle trigger buttons with context-aware behavior
      if (buttonIndex === 6) { // Left Trigger -> right click (interactPlace)
        await this.handleGamepadLeftTriggerDown(cmd)
        return
      } else if (buttonIndex === 7) { // Right Trigger -> left click (attackDestroy)
        await this.handleGamepadRightTriggerDown(cmd)
        return
      }

      // Handle A button (0) and Y button (3) as left/right click in modals
      if (hasModalsOpen && gamepadUiCursorState.display) {
        if (buttonIndex === 0) { // A button -> left click
          await this.handleGamepadLeftClickDown(cmd)
          return
        } else if (buttonIndex === 3) { // Y button -> right click  
          await this.handleGamepadRightClickDown(cmd)
          return
        }
      }

      // Default gamepad simulation for all other cases
      // Start button press without auto-release
      gamepadSimulator.startButtonPress(buttonIndex)

      // Update our tracking state if it auto-connected
      if (gamepadSimulator.fakeController.connected) {
        this.isConnected = true
      }

    } catch (error) {
      console.error('[WsCommandClient] Error pressing gamepad button down:', error)
    }
  }

  async handleGamepadButtonPressUp(cmd: MouseCommand) {
    try {
      const buttonIndex = cmd.buttonIndex ?? 0

      // Check if this is a mouse-equivalent button and if modals are open
      const hasModalsOpen = !isGameActive(true)
      console.log(`[WsCommandClient] Executing gamepadButtonPressUp ${buttonIndex}, hasModalsOpen=${hasModalsOpen}`)

      // Handle trigger buttons with context-aware behavior
      if (buttonIndex === 6) { // Left Trigger -> right click (interactPlace)
        await this.handleGamepadLeftTriggerUp(cmd)
        return
      } else if (buttonIndex === 7) { // Right Trigger -> left click (attackDestroy)
        await this.handleGamepadRightTriggerUp(cmd)
        return
      }

      // Handle A button (0) and Y button (3) as left/right click in modals
      if (hasModalsOpen && gamepadUiCursorState.display) {
        if (buttonIndex === 0) { // A button -> left click
          await this.handleGamepadLeftClickUp(cmd)
          return
        } else if (buttonIndex === 3) { // Y button -> right click  
          await this.handleGamepadRightClickUp(cmd)
          return
        }
      }

      // Default gamepad simulation for all other cases
      // End button press
      gamepadSimulator.endButtonPress(buttonIndex)

    } catch (error) {
      console.error('[WsCommandClient] Error releasing gamepad button:', error)
    }
  }

  async handleGamepadJoystickMove(cmd: MouseCommand) {
    try {
      const stickIndex = cmd.stickIndex ?? 0 // 0 for left stick, 1 for right stick
      const x = cmd.x ?? 0 // -1 to 1
      const y = cmd.y ?? 0 // -1 to 1


      gamepadSimulator.moveJoystick(stickIndex, x, y)

      // Update our tracking state if it auto-connected
      if (gamepadSimulator.fakeController.connected) {
        this.isConnected = true
      }

    } catch (error) {
      console.error('[WsCommandClient] Error moving gamepad joystick:', error)
    }
  }

  async handleGamepadJoystickCenter(cmd: MouseCommand) {
    try {
      const stickIndex = cmd.stickIndex ?? 0 // 0 for left stick, 1 for right stick


      gamepadSimulator.centerJoystick(stickIndex)

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


      gamepadSimulator.pulseJoystick(stickIndex, x, y, duration)

      // Update our tracking state if it auto-connected
      if (gamepadSimulator.fakeController.connected) {
        this.isConnected = true
      }

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


      gamepadSimulator.animateJoystick(stickIndex, fromX, fromY, toX, toY, duration)

      // Update our tracking state if it auto-connected
      if (gamepadSimulator.fakeController.connected) {
        this.isConnected = true
      }

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


      gamepadSimulator.circularJoystickMovement(stickIndex, radius, duration, clockwise)

      // Update our tracking state if it auto-connected
      if (gamepadSimulator.fakeController.connected) {
        this.isConnected = true
      }

    } catch (error) {
      console.error('[WsCommandClient] Error starting gamepad joystick circular movement:', error)
    }
  }

  async handleGamepadDestroy(cmd: MouseCommand) {
    try {

      gamepadSimulator.destroy()
      this.isConnected = false

    } catch (error) {
      console.error('[WsCommandClient] Error destroying gamepad:', error)
    }
  }

  async handleDocumentMouseEvent(cmd: MouseCommand) {
    try {
      const timestamp = Date.now()

      const buttonKey = cmd.button!

      if (cmd.action === 'down') {
        // Only start if not already active (prevent duplicate starts)
        if (!this.activeButtons.has(buttonKey)) {
          this.activeButtons.add(buttonKey)
          this.buttonStartTimes.set(buttonKey, timestamp)

          const event = new MouseEvent('mousedown', {
            bubbles: true,
            cancelable: true,
            button: cmd.button,
            buttons: cmd.button === 0 ? 1 : 2
          })

          // Add a special property to mark this as a WebSocket synthetic event
          Object.defineProperty(event, 'isWebSocketEvent', {
            value: true,
            writable: false,
            enumerable: false
          })

          document.dispatchEvent(event)

          // Call bot.mouse.update() immediately after dispatching, just like touch buttons do
          if (cmd.updateMouse && this.bot?.mouse?.update) {
            this.bot.mouse.update()
          }

        } else {
        }
      } else if (cmd.action === 'up') {
        // Only stop if currently active
        if (this.activeButtons.has(buttonKey)) {
          this.activeButtons.delete(buttonKey)

          const startTime = this.buttonStartTimes.get(buttonKey)
          const duration = startTime ? timestamp - startTime : 'unknown'
          this.buttonStartTimes.delete(buttonKey)

          const event = new MouseEvent('mouseup', {
            bubbles: true,
            cancelable: true,
            button: cmd.button,
            buttons: 0
          })

          // Add a special property to mark this as a WebSocket synthetic event
          Object.defineProperty(event, 'isWebSocketEvent', {
            value: true,
            writable: false,
            enumerable: false
          })

          document.dispatchEvent(event)

        } else {
        }
      }

    } catch (error) {
      console.error('[WsCommandClient] Error in documentMouseEvent:', error)
    }
  }

  async handleCursor(cmd: MouseCommand) {
    try {
      if (cmd.x !== undefined && cmd.z !== undefined) {
        // Set absolute cursor position (0-100 percentage)
        gamepadUiCursorState.x = Math.min(100, Math.max(0, cmd.x))
        gamepadUiCursorState.y = Math.min(100, Math.max(0, cmd.z))
        emitMousemove()
      } else if (cmd.movementX !== undefined || cmd.movementY !== undefined) {
        // Relative cursor movement
        const dx = (cmd.movementX || 0) * 0.5 // Adjust sensitivity as needed
        const dy = (cmd.movementY || 0) * 0.5
        moveGamepadCursorBy(dx, dy)
        emitMousemove()
      }
    } catch (error) {
      console.error('[WsCommandClient] Error moving cursor:', error)
    }
  }

  async handleGamepadLeftClickDown(cmd: MouseCommand) {
    try {
      const hasModalsOpen = !isGameActive(true)
      console.log(`[WsCommandClient] Executing gamepadLeftClickDown, hasModalsOpen=${hasModalsOpen}`)

      if (hasModalsOpen) {
        // UI interaction with cursor positioning for modals (inventory, crafting, etc.)
        if (gamepadUiCursorState.display) {
          // Handle explicit positioning if provided
          if (cmd.x !== undefined && cmd.y !== undefined) {
            gamepadUiCursorState.x = Math.min(100, Math.max(0, cmd.x))
            gamepadUiCursorState.y = Math.min(100, Math.max(0, cmd.y))
          }

          const x = (gamepadUiCursorState.x / 100) * window.innerWidth
          const y = (gamepadUiCursorState.y / 100) * window.innerHeight
          const event = new MouseEvent('mousedown', {
            bubbles: true,
            cancelable: true,
            clientX: x,
            clientY: y,
            button: 0,
            buttons: 1
          })
          const elementAtCursor = document.elementFromPoint(x, y)
          if (elementAtCursor) {
            elementAtCursor.dispatchEvent(event)
          }
        }
      } else {
        // Game world interaction: use documentMouseEvent
        console.log('[WsCommandClient] Using documentMouseEvent for game world gamepadLeftClickDown')
        await this.handleDocumentMouseEvent({
          ...cmd,
          type: 'documentMouseEvent',
          button: 0,
          action: 'down',
          updateMouse: true
        })
      }
    } catch (error) {
      console.error('[WsCommandClient] Error in gamepadLeftClickDown:', error)
    }
  }

  async handleGamepadLeftClickUp(cmd: MouseCommand) {
    try {
      const hasModalsOpen = !isGameActive(true)
      console.log(`[WsCommandClient] Executing gamepadLeftClickUp, hasModalsOpen=${hasModalsOpen}`)

      if (hasModalsOpen) {
        // UI interaction with cursor positioning for modals (inventory, crafting, etc.)
        if (gamepadUiCursorState.display) {
          // Handle explicit positioning if provided
          if (cmd.x !== undefined && cmd.y !== undefined) {
            gamepadUiCursorState.x = Math.min(100, Math.max(0, cmd.x))
            gamepadUiCursorState.y = Math.min(100, Math.max(0, cmd.y))
          }

          const x = (gamepadUiCursorState.x / 100) * window.innerWidth
          const y = (gamepadUiCursorState.y / 100) * window.innerHeight
          const event = new MouseEvent('mouseup', {
            bubbles: true,
            cancelable: true,
            clientX: x,
            clientY: y,
            button: 0,
            buttons: 0
          })
          const elementAtCursor = document.elementFromPoint(x, y)
          if (elementAtCursor) {
            elementAtCursor.dispatchEvent(event)
            // Also dispatch click for complete interaction
            elementAtCursor.dispatchEvent(new MouseEvent('click', {
              bubbles: true,
              clientX: x,
              clientY: y
            }))
          }
        }
      } else {
        // Game world interaction: use documentMouseEvent
        console.log('[WsCommandClient] Using documentMouseEvent for game world gamepadLeftClickUp')
        await this.handleDocumentMouseEvent({
          ...cmd,
          type: 'documentMouseEvent',
          button: 0,
          action: 'up',
          updateMouse: false
        })
      }
    } catch (error) {
      console.error('[WsCommandClient] Error in gamepadLeftClickUp:', error)
    }
  }

  async handleGamepadRightClickDown(cmd: MouseCommand) {
    try {
      const hasModalsOpen = !isGameActive(true)
      console.log(`[WsCommandClient] Executing gamepadRightClickDown, hasModalsOpen=${hasModalsOpen}`)

      if (hasModalsOpen) {
        // UI interaction with cursor positioning for modals (inventory, crafting, etc.)
        if (gamepadUiCursorState.display) {
          // Handle explicit positioning if provided
          if (cmd.x !== undefined && cmd.y !== undefined) {
            gamepadUiCursorState.x = Math.min(100, Math.max(0, cmd.x))
            gamepadUiCursorState.y = Math.min(100, Math.max(0, cmd.y))
          }

          const x = (gamepadUiCursorState.x / 100) * window.innerWidth
          const y = (gamepadUiCursorState.y / 100) * window.innerHeight
          const event = new MouseEvent('mousedown', {
            bubbles: true,
            cancelable: true,
            clientX: x,
            clientY: y,
            button: 2,
            buttons: 2
          })
          const elementAtCursor = document.elementFromPoint(x, y)
          if (elementAtCursor) {
            elementAtCursor.dispatchEvent(event)
          }
        }
      } else {
        // Game world interaction: use documentMouseEvent
        console.log('[WsCommandClient] Using documentMouseEvent for game world gamepadRightClickDown')
        await this.handleDocumentMouseEvent({
          ...cmd,
          type: 'documentMouseEvent',
          button: 2,
          action: 'down',
          updateMouse: true
        })
      }
    } catch (error) {
      console.error('[WsCommandClient] Error in gamepadRightClickDown:', error)
    }
  }

  async handleGamepadRightClickUp(cmd: MouseCommand) {
    try {
      const hasModalsOpen = !isGameActive(true)
      console.log(`[WsCommandClient] Executing gamepadRightClickUp, hasModalsOpen=${hasModalsOpen}`)

      if (hasModalsOpen) {
        // UI interaction with cursor positioning for modals (inventory, crafting, etc.)
        if (gamepadUiCursorState.display) {
          // Handle explicit positioning if provided
          if (cmd.x !== undefined && cmd.y !== undefined) {
            gamepadUiCursorState.x = Math.min(100, Math.max(0, cmd.x))
            gamepadUiCursorState.y = Math.min(100, Math.max(0, cmd.y))
          }

          const x = (gamepadUiCursorState.x / 100) * window.innerWidth
          const y = (gamepadUiCursorState.y / 100) * window.innerHeight
          const event = new MouseEvent('mouseup', {
            bubbles: true,
            cancelable: true,
            clientX: x,
            clientY: y,
            button: 2,
            buttons: 0
          })
          const elementAtCursor = document.elementFromPoint(x, y)
          if (elementAtCursor) {
            elementAtCursor.dispatchEvent(event)
            // Also dispatch contextmenu for complete interaction
            elementAtCursor.dispatchEvent(new MouseEvent('contextmenu', {
              bubbles: true,
              clientX: x,
              clientY: y
            }))
          }
        }
      } else {
        // Game world interaction: use documentMouseEvent
        console.log('[WsCommandClient] Using documentMouseEvent for game world gamepadRightClickUp')
        await this.handleDocumentMouseEvent({
          ...cmd,
          type: 'documentMouseEvent',
          button: 2,
          action: 'up',
          updateMouse: false
        })
      }
    } catch (error) {
      console.error('[WsCommandClient] Error in gamepadRightClickUp:', error)
    }
  }

  async handleGamepadLeftTriggerDown(cmd: MouseCommand) {
    try {
      const hasModalsOpen = !isGameActive(true)
      console.log(`[WsCommandClient] Executing gamepadLeftTriggerDown (interactPlace/rightClick), hasModalsOpen=${hasModalsOpen}`)

      if (hasModalsOpen) {
        // UI interaction - mousedown for modals
        if (gamepadUiCursorState.display) {
          // Handle explicit positioning if provided
          if (cmd.x !== undefined && cmd.y !== undefined) {
            gamepadUiCursorState.x = Math.min(100, Math.max(0, cmd.x))
            gamepadUiCursorState.y = Math.min(100, Math.max(0, cmd.y))
          }

          const x = (gamepadUiCursorState.x / 100) * window.innerWidth
          const y = (gamepadUiCursorState.y / 100) * window.innerHeight
          const event = new MouseEvent('mousedown', {
            bubbles: true,
            cancelable: true,
            clientX: x,
            clientY: y,
            button: 2,
            buttons: 2
          })
          const elementAtCursor = document.elementFromPoint(x, y)
          if (elementAtCursor) {
            elementAtCursor.dispatchEvent(event)
          }
        } else {
          console.log('[WsCommandClient] Gamepad cursor not active, ignoring modal leftTriggerDown')
        }
      } else {
        // Game world interaction: mousedown
        console.log('[WsCommandClient] Using documentMouseEvent down for game world leftTriggerDown')
        await this.handleDocumentMouseEvent({
          ...cmd,
          type: 'documentMouseEvent',
          button: 2,
          action: 'down',
          updateMouse: true
        })
      }
    } catch (error) {
      console.error('[WsCommandClient] Error in gamepadLeftTriggerDown:', error)
    }
  }

  async handleGamepadLeftTriggerUp(cmd: MouseCommand) {
    try {
      const hasModalsOpen = !isGameActive(true)
      console.log(`[WsCommandClient] Executing gamepadLeftTriggerUp (interactPlace/rightClick), hasModalsOpen=${hasModalsOpen}`)

      if (hasModalsOpen) {
        // UI interaction - mouseup for modals
        if (gamepadUiCursorState.display) {
          // Handle explicit positioning if provided
          if (cmd.x !== undefined && cmd.y !== undefined) {
            gamepadUiCursorState.x = Math.min(100, Math.max(0, cmd.x))
            gamepadUiCursorState.y = Math.min(100, Math.max(0, cmd.y))
          }

          const x = (gamepadUiCursorState.x / 100) * window.innerWidth
          const y = (gamepadUiCursorState.y / 100) * window.innerHeight
          const event = new MouseEvent('mouseup', {
            bubbles: true,
            cancelable: true,
            clientX: x,
            clientY: y,
            button: 2,
            buttons: 0
          })
          const elementAtCursor = document.elementFromPoint(x, y)
          if (elementAtCursor) {
            elementAtCursor.dispatchEvent(event)
            // Also dispatch contextmenu for complete interaction
            elementAtCursor.dispatchEvent(new MouseEvent('contextmenu', {
              bubbles: true,
              clientX: x,
              clientY: y
            }))
          }
        } else {
          console.log('[WsCommandClient] Gamepad cursor not active, ignoring modal leftTriggerUp')
        }
      } else {
        // Game world interaction: mouseup
        console.log('[WsCommandClient] Using documentMouseEvent up for game world leftTriggerUp')
        await this.handleDocumentMouseEvent({
          ...cmd,
          type: 'documentMouseEvent',
          button: 2,
          action: 'up',
          updateMouse: false
        })
      }
    } catch (error) {
      console.error('[WsCommandClient] Error in gamepadLeftTriggerUp:', error)
    }
  }

  async handleGamepadRightTriggerDown(cmd: MouseCommand) {
    try {
      const hasModalsOpen = !isGameActive(true)
      console.log(`[WsCommandClient] Executing gamepadRightTriggerDown (attackDestroy/leftClick), hasModalsOpen=${hasModalsOpen}`)

      if (hasModalsOpen) {
        // UI interaction - mousedown for modals
        if (gamepadUiCursorState.display) {
          // Handle explicit positioning if provided
          if (cmd.x !== undefined && cmd.y !== undefined) {
            gamepadUiCursorState.x = Math.min(100, Math.max(0, cmd.x))
            gamepadUiCursorState.y = Math.min(100, Math.max(0, cmd.y))
          }

          const x = (gamepadUiCursorState.x / 100) * window.innerWidth
          const y = (gamepadUiCursorState.y / 100) * window.innerHeight
          const event = new MouseEvent('mousedown', {
            bubbles: true,
            cancelable: true,
            clientX: x,
            clientY: y,
            button: 0,
            buttons: 1
          })
          const elementAtCursor = document.elementFromPoint(x, y)
          if (elementAtCursor) {
            elementAtCursor.dispatchEvent(event)
          }
        } else {
          console.log('[WsCommandClient] Gamepad cursor not active, ignoring modal rightTriggerDown')
        }
      } else {
        // Game world interaction: mousedown
        console.log('[WsCommandClient] Using documentMouseEvent down for game world rightTriggerDown')
        await this.handleDocumentMouseEvent({
          ...cmd,
          type: 'documentMouseEvent',
          button: 0,
          action: 'down',
          updateMouse: true
        })
      }
    } catch (error) {
      console.error('[WsCommandClient] Error in gamepadRightTriggerDown:', error)
    }
  }

  async handleGamepadRightTriggerUp(cmd: MouseCommand) {
    try {
      const hasModalsOpen = !isGameActive(true)
      console.log(`[WsCommandClient] Executing gamepadRightTriggerUp (attackDestroy/leftClick), hasModalsOpen=${hasModalsOpen}`)

      if (hasModalsOpen) {
        // UI interaction - mouseup for modals
        if (gamepadUiCursorState.display) {
          // Handle explicit positioning if provided
          if (cmd.x !== undefined && cmd.y !== undefined) {
            gamepadUiCursorState.x = Math.min(100, Math.max(0, cmd.x))
            gamepadUiCursorState.y = Math.min(100, Math.max(0, cmd.y))
          }

          const x = (gamepadUiCursorState.x / 100) * window.innerWidth
          const y = (gamepadUiCursorState.y / 100) * window.innerHeight
          const event = new MouseEvent('mouseup', {
            bubbles: true,
            cancelable: true,
            clientX: x,
            clientY: y,
            button: 0,
            buttons: 0
          })
          const elementAtCursor = document.elementFromPoint(x, y)
          if (elementAtCursor) {
            elementAtCursor.dispatchEvent(event)
            // Also dispatch click for complete interaction
            elementAtCursor.dispatchEvent(new MouseEvent('click', {
              bubbles: true,
              clientX: x,
              clientY: y
            }))
          }
        } else {
          console.log('[WsCommandClient] Gamepad cursor not active, ignoring modal rightTriggerUp')
        }
      } else {
        // Game world interaction: mouseup
        console.log('[WsCommandClient] Using documentMouseEvent up for game world rightTriggerUp')
        await this.handleDocumentMouseEvent({
          ...cmd,
          type: 'documentMouseEvent',
          button: 0,
          action: 'up',
          updateMouse: false
        })
      }
    } catch (error) {
      console.error('[WsCommandClient] Error in gamepadRightTriggerUp:', error)
    }
  }
}
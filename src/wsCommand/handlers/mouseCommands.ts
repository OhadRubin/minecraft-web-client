import { MouseCommand } from '../types'
import { gamepadUiCursorState, moveGamepadCursorBy } from '../../react/GamepadUiCursor'
import { emitMousemove } from '../../controls'
import { isGameActive } from '../../globalState'

export class MouseCommandHandler {
  // Track active button states to prevent duplicate actions
  private activeButtons = new Set<number>()
  // Track button press timing
  private buttonStartTimes = new Map<number, number>()

  constructor(private bot: any) {}

  async handleLeftDown(cmd: MouseCommand) {
    try {
      const hasModalsOpen = !isGameActive(true)
      console.log(`[WsCommandClient] Executing leftDown command, hasModalsOpen=${hasModalsOpen}`)

      if (hasModalsOpen) {
        // UI interaction with cursor positioning for modals (inventory, crafting, etc.)
        if (gamepadUiCursorState.display) {
          // Handle explicit positioning if provided
          if (cmd.x !== undefined && cmd.y !== undefined) {
            gamepadUiCursorState.x = Math.min(100, Math.max(0, cmd.x))
            gamepadUiCursorState.y = Math.min(100, Math.max(0, cmd.y))
            console.log(`[WsCommandClient] Positioned cursor at ${gamepadUiCursorState.x}%, ${gamepadUiCursorState.y}%`)
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
            console.log(`[WsCommandClient] Left clicked at cursor position (${x}, ${y}) on element:`, elementAtCursor.tagName)
          } else {
            console.log('[WsCommandClient] No element found at cursor position')
          }
        } else {
          console.log('[WsCommandClient] WebSocket input not active, ignoring modal leftDown')
        }
      } else {
        // Game world interaction: use documentMouseEvent
        console.log('[WsCommandClient] Using documentMouseEvent for game world leftDown')
        await this.handleDocumentMouseEvent({
          ...cmd,
          type: 'documentMouseEvent',
          button: 0,
          action: 'down',
          updateMouse: true
        })
      }
    } catch (error) {
      console.error('[WsCommandClient] Error in leftDown:', error)
    }
  }

  async handleLeftUp(cmd: MouseCommand) {
    try {
      const hasModalsOpen = !isGameActive(true)
      console.log(`[WsCommandClient] Executing leftUp command, hasModalsOpen=${hasModalsOpen}`)

      if (hasModalsOpen) {
        // UI interaction with cursor positioning for modals (inventory, crafting, etc.)
        if (gamepadUiCursorState.display) {
          // Handle explicit positioning if provided
          if (cmd.x !== undefined && cmd.y !== undefined) {
            gamepadUiCursorState.x = Math.min(100, Math.max(0, cmd.x))
            gamepadUiCursorState.y = Math.min(100, Math.max(0, cmd.y))
            console.log(`[WsCommandClient] Positioned cursor at ${gamepadUiCursorState.x}%, ${gamepadUiCursorState.y}%`)
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
            console.log(`[WsCommandClient] Left click released at cursor position (${x}, ${y}) on element:`, elementAtCursor.tagName)
          } else {
            console.log('[WsCommandClient] No element found at cursor position')
          }
        } else {
          console.log('[WsCommandClient] WebSocket input not active, ignoring modal leftUp')
        }
      } else {
        // Game world interaction: use documentMouseEvent
        console.log('[WsCommandClient] Using documentMouseEvent for game world leftUp')
        await this.handleDocumentMouseEvent({
          ...cmd,
          type: 'documentMouseEvent',
          button: 0,
          action: 'up',
          updateMouse: false
        })
      }
    } catch (error) {
      console.error('[WsCommandClient] Error in leftUp:', error)
    }
  }

  async handleRightDown(cmd: MouseCommand) {
    try {
      const hasModalsOpen = !isGameActive(true)
      console.log(`[WsCommandClient] Executing rightDown command, hasModalsOpen=${hasModalsOpen}`)

      if (hasModalsOpen) {
        // UI interaction with cursor positioning for modals (inventory, crafting, etc.)
        if (gamepadUiCursorState.display) {
          // Handle explicit positioning if provided
          if (cmd.x !== undefined && cmd.y !== undefined) {
            gamepadUiCursorState.x = Math.min(100, Math.max(0, cmd.x))
            gamepadUiCursorState.y = Math.min(100, Math.max(0, cmd.y))
            console.log(`[WsCommandClient] Positioned cursor at ${gamepadUiCursorState.x}%, ${gamepadUiCursorState.y}%`)
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
            console.log(`[WsCommandClient] Right clicked at cursor position (${x}, ${y}) on element:`, elementAtCursor.tagName)
          } else {
            console.log('[WsCommandClient] No element found at cursor position')
          }
        } else {
          console.log('[WsCommandClient] WebSocket input not active, ignoring modal rightDown')
        }
      } else {
        // Game world interaction: use documentMouseEvent
        console.log('[WsCommandClient] Using documentMouseEvent for game world rightDown')
        await this.handleDocumentMouseEvent({
          ...cmd,
          type: 'documentMouseEvent',
          button: 2,
          action: 'down',
          updateMouse: true
        })
      }
    } catch (error) {
      console.error('[WsCommandClient] Error in rightDown:', error)
    }
  }

  async handleRightUp(cmd: MouseCommand) {
    try {
      const hasModalsOpen = !isGameActive(true)
      console.log(`[WsCommandClient] Executing rightUp command, hasModalsOpen=${hasModalsOpen}`)

      if (hasModalsOpen) {
        // UI interaction with cursor positioning for modals (inventory, crafting, etc.)
        if (gamepadUiCursorState.display) {
          // Handle explicit positioning if provided
          if (cmd.x !== undefined && cmd.y !== undefined) {
            gamepadUiCursorState.x = Math.min(100, Math.max(0, cmd.x))
            gamepadUiCursorState.y = Math.min(100, Math.max(0, cmd.y))
            console.log(`[WsCommandClient] Positioned cursor at ${gamepadUiCursorState.x}%, ${gamepadUiCursorState.y}%`)
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
            console.log(`[WsCommandClient] Right click released at cursor position (${x}, ${y}) on element:`, elementAtCursor.tagName)
          } else {
            console.log('[WsCommandClient] No element found at cursor position')
          }
        } else {
          console.log('[WsCommandClient] WebSocket input not active, ignoring modal rightUp')
        }
      } else {
        // Game world interaction: use documentMouseEvent
        console.log('[WsCommandClient] Using documentMouseEvent for game world rightUp')
        await this.handleDocumentMouseEvent({
          ...cmd,
          type: 'documentMouseEvent',
          button: 2,
          action: 'up',
          updateMouse: false
        })
      }
    } catch (error) {
      console.error('[WsCommandClient] Error in rightUp:', error)
    }
  }

  async handleContextRightClick(cmd: MouseCommand) {
    try {
      console.log('[WsCommandClient] Executing contextRightClick command (context-aware)')
      
      // Detect if inventory is open by checking for inventory elements
      const inventoryElement = document.querySelector('.inventory-window, .inventory, [class*="inventory"]') as HTMLElement
      const isInventoryOpen = inventoryElement && inventoryElement.style.display !== 'none'
      
      console.log(`[WsCommandClient] Context detection: inventory open = ${isInventoryOpen}`)
      
      if (isInventoryOpen) {
        // Use UI interaction for inventory
        console.log('[WsCommandClient] Using UI interaction for inventory context')
        await this.handleRightDown(cmd)
        await new Promise(resolve => setTimeout(resolve, cmd.duration || 200))
        await this.handleRightUp(cmd)
      } else {
        // Use documentMouseEvent for game world
        console.log('[WsCommandClient] Using documentMouseEvent for game world context')
        await this.handleDocumentMouseEvent({
          ...cmd,
          type: 'documentMouseEvent',
          button: 2,
          action: 'down',
          updateMouse: true
        })
        await new Promise(resolve => setTimeout(resolve, cmd.duration || 200))
        await this.handleDocumentMouseEvent({
          ...cmd,
          type: 'documentMouseEvent',
          button: 2,
          action: 'up',
          updateMouse: false
        })
      }
    } catch (error) {
      console.error('[WsCommandClient] Error in contextRightClick:', error)
    }
  }

  async handleDocumentMouseEvent(cmd: MouseCommand) {
    try {
      const timestamp = Date.now()
      console.log(`[WsCommandClient] Received ${cmd.action} command for button ${cmd.button} at ${timestamp}`)

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
            console.log('[WsCommandClient] Calling bot.mouse.update() synchronously after event dispatch')
            this.bot.mouse.update()
          }

          console.log(`[WsCommandClient] Started button ${cmd.button} press (keeping active)`)
        } else {
          console.log(`[WsCommandClient] Button ${cmd.button} already active, ignoring duplicate down`)
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

          console.log(`[WsCommandClient] Ended button ${cmd.button} press (held for ${duration}ms)`)
        } else {
          console.log(`[WsCommandClient] Button ${cmd.button} not active, ignoring up`)
        }
      }

      console.log(`[WsCommandClient] Active buttons: [${Array.from(this.activeButtons).join(', ')}]`)
    } catch (error) {
      console.error('[WsCommandClient] Error in documentMouseEvent:', error)
    }
  }

  async handleCursor(cmd: MouseCommand) {
    try {
      console.log(`[WsCommandClient] Moving cursor to position: ${cmd.x}, ${cmd.z}`)
      if (cmd.x !== undefined && cmd.z !== undefined) {
        // Set absolute cursor position (0-100 percentage)
        gamepadUiCursorState.x = Math.min(100, Math.max(0, cmd.x))
        gamepadUiCursorState.y = Math.min(100, Math.max(0, cmd.z))
        emitMousemove()
        console.log(`[WsCommandClient] Successfully moved cursor to ${gamepadUiCursorState.x}%, ${gamepadUiCursorState.y}%`)
      } else if (cmd.movementX !== undefined || cmd.movementY !== undefined) {
        // Relative cursor movement
        const dx = (cmd.movementX || 0) * 0.5 // Adjust sensitivity as needed
        const dy = (cmd.movementY || 0) * 0.5
        moveGamepadCursorBy(dx, dy)
        emitMousemove()
        console.log(`[WsCommandClient] Moved cursor by ${dx}, ${dy}`)
      }
    } catch (error) {
      console.error('[WsCommandClient] Error moving cursor:', error)
    }
  }
}
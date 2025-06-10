import { MouseCommand } from '../types'
import { moveWsCursorBy, emitWsMousemove, wsCursorState } from '../../react/WsCursor'
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

      if (hasModalsOpen) {
        // UI interaction with cursor positioning for modals (inventory, crafting, etc.)
        if (wsCursorState.usingWsInput) {
          // Auto-position cursor at center for UI interactions (if not explicitly positioned)
          if (cmd.x === undefined && cmd.y === undefined) {
            wsCursorState.x = 50
            wsCursorState.y = 50
          } else if (cmd.x !== undefined && cmd.y !== undefined) {
            wsCursorState.x = Math.min(100, Math.max(0, cmd.x))
            wsCursorState.y = Math.min(100, Math.max(0, cmd.y))
          }

          const x = (wsCursorState.x / 100) * window.innerWidth
          const y = (wsCursorState.y / 100) * window.innerHeight
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
          } else {
          }
        } else {
        }
      } else {
        // Game world interaction: use documentMouseEvent
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

      if (hasModalsOpen) {
        // UI interaction with cursor positioning for modals (inventory, crafting, etc.)
        if (wsCursorState.usingWsInput) {
          // Auto-position cursor at center for UI interactions (if not explicitly positioned)
          if (cmd.x === undefined && cmd.y === undefined) {
            wsCursorState.x = 50
            wsCursorState.y = 50
          } else if (cmd.x !== undefined && cmd.y !== undefined) {
            wsCursorState.x = Math.min(100, Math.max(0, cmd.x))
            wsCursorState.y = Math.min(100, Math.max(0, cmd.y))
          }

          const x = (wsCursorState.x / 100) * window.innerWidth
          const y = (wsCursorState.y / 100) * window.innerHeight
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
          } else {
          }
        } else {
        }
      } else {
        // Game world interaction: use documentMouseEvent
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

      if (hasModalsOpen) {
        // UI interaction with cursor positioning for modals (inventory, crafting, etc.)
        if (wsCursorState.usingWsInput) {
          // Auto-position cursor at center for UI interactions (if not explicitly positioned)
          if (cmd.x === undefined && cmd.y === undefined) {
            wsCursorState.x = 50
            wsCursorState.y = 50
          } else if (cmd.x !== undefined && cmd.y !== undefined) {
            wsCursorState.x = Math.min(100, Math.max(0, cmd.x))
            wsCursorState.y = Math.min(100, Math.max(0, cmd.y))
          }

          const x = (wsCursorState.x / 100) * window.innerWidth
          const y = (wsCursorState.y / 100) * window.innerHeight
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
          } else {
          }
        } else {
        }
      } else {
        // Game world interaction: use documentMouseEvent
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

      if (hasModalsOpen) {
        // UI interaction with cursor positioning for modals (inventory, crafting, etc.)
        if (wsCursorState.usingWsInput) {
          // Auto-position cursor at center for UI interactions (if not explicitly positioned)
          if (cmd.x === undefined && cmd.y === undefined) {
            wsCursorState.x = 50
            wsCursorState.y = 50
          } else if (cmd.x !== undefined && cmd.y !== undefined) {
            wsCursorState.x = Math.min(100, Math.max(0, cmd.x))
            wsCursorState.y = Math.min(100, Math.max(0, cmd.y))
          }

          const x = (wsCursorState.x / 100) * window.innerWidth
          const y = (wsCursorState.y / 100) * window.innerHeight
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
          } else {
          }
        } else {
        }
      } else {
        // Game world interaction: use documentMouseEvent
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
      
      // Detect if inventory is open by checking for inventory elements
      const inventoryElement = document.querySelector('.inventory-window, .inventory, [class*="inventory"]') as HTMLElement
      const isInventoryOpen = inventoryElement && inventoryElement.style.display !== 'none'
      
      
      if (isInventoryOpen) {
        // Use UI interaction for inventory
        await this.handleRightDown(cmd)
        await new Promise(resolve => setTimeout(resolve, cmd.duration || 200))
        await this.handleRightUp(cmd)
      } else {
        // Use documentMouseEvent for game world
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
        wsCursorState.x = Math.min(100, Math.max(0, cmd.x))
        wsCursorState.y = Math.min(100, Math.max(0, cmd.z))
        emitWsMousemove()
      } else if (cmd.movementX !== undefined || cmd.movementY !== undefined) {
        // Relative cursor movement
        const dx = (cmd.movementX || 0) * 0.5 // Adjust sensitivity as needed
        const dy = (cmd.movementY || 0) * 0.5
        moveWsCursorBy(dx, dy)
        emitWsMousemove()
      }
    } catch (error) {
      console.error('[WsCommandClient] Error moving cursor:', error)
    }
  }
}
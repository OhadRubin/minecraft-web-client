import { MouseCommand } from '../types'
import { moveWsCursorBy, emitWsMousemove, wsCursorState } from '../../react/WsCursor'

export class MouseCommandHandler {
  // Track active button states to prevent duplicate actions
  private activeButtons = new Set<number>()
  // Track button press timing
  private buttonStartTimes = new Map<number, number>()

  constructor(private bot: any) {}

  async handleLeftDown(cmd: MouseCommand) {
    try {
      console.log('[WsCommandClient] Executing leftDown command (UI interaction)')

      // UI interaction with cursor positioning
      if (wsCursorState.usingWsInput) {
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
          console.log(`[WsCommandClient] Left clicked at cursor position (${x}, ${y}) on element:`, elementAtCursor.tagName)
        } else {
          console.log('[WsCommandClient] No element found at cursor position')
        }
      } else {
        console.log('[WsCommandClient] WebSocket input not active, ignoring leftDown')
      }
    } catch (error) {
      console.error('[WsCommandClient] Error in leftDown:', error)
    }
  }

  async handleLeftUp(cmd: MouseCommand) {
    try {
      console.log('[WsCommandClient] Executing leftUp command (UI interaction)')

      // UI interaction with cursor positioning
      if (wsCursorState.usingWsInput) {
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
          console.log(`[WsCommandClient] Left click released at cursor position (${x}, ${y}) on element:`, elementAtCursor.tagName)
        } else {
          console.log('[WsCommandClient] No element found at cursor position')
        }
      } else {
        console.log('[WsCommandClient] WebSocket input not active, ignoring leftUp')
      }
    } catch (error) {
      console.error('[WsCommandClient] Error in leftUp:', error)
    }
  }

  async handleRightDown(cmd: MouseCommand) {
    try {
      console.log('[WsCommandClient] Executing rightDown command (context-aware)')

      // Detect if inventory is open by checking bot state and DOM elements
      const bot = (window as any).bot
      const hasActiveWindow = bot?.currentWindow && bot.currentWindow.type !== null
      const inventoryElement = document.querySelector('.inventory-window, .inventory, [class*="inventory"], [data-testid*="inventory"]') as HTMLElement
      const hasModals = document.querySelector('[class*="modal"], [id*="modal"], .react-modal')
      const gameElement = document.querySelector('canvas, #game-canvas, [class*="game"]')
      const isGameFocused = gameElement && document.activeElement === gameElement
      
      // More comprehensive context detection
      const isInventoryContext = hasActiveWindow || 
                                 (inventoryElement && inventoryElement.style.display !== 'none') || 
                                 hasModals || 
                                 !isGameFocused
      
      console.log(`[WsCommandClient] Context detection: bot.currentWindow=${bot?.currentWindow?.type}, hasActiveWindow=${hasActiveWindow}, hasModals=${!!hasModals}, isGameFocused=${isGameFocused}, inventory/UI context = ${isInventoryContext}`)

      if (isInventoryContext && wsCursorState.usingWsInput) {
        // UI interaction with cursor positioning for inventory
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
          console.log(`[WsCommandClient] Right clicked at cursor position (${x}, ${y}) on element:`, elementAtCursor.tagName)
        } else {
          console.log('[WsCommandClient] No element found at cursor position')
        }
      } else {
        // Use documentMouseEvent for game world
        console.log('[WsCommandClient] Using documentMouseEvent for game world context')
        const event = new MouseEvent('mousedown', {
          bubbles: true,
          cancelable: true,
          button: 2,
          buttons: 2
        })
        Object.defineProperty(event, 'isWebSocketEvent', {
          value: true,
          writable: false,
          enumerable: false
        })
        document.dispatchEvent(event)
        if (this.bot?.mouse?.update) {
          console.log('[WsCommandClient] Calling bot.mouse.update() after game world rightDown')
          this.bot.mouse.update()
        }
      }
    } catch (error) {
      console.error('[WsCommandClient] Error in rightDown:', error)
    }
  }

  async handleRightUp(cmd: MouseCommand) {
    try {
      console.log('[WsCommandClient] Executing rightUp command (context-aware)')

      // Detect if inventory is open by checking bot state and DOM elements
      const bot = (window as any).bot
      const hasActiveWindow = bot?.currentWindow && bot.currentWindow.type !== null
      const inventoryElement = document.querySelector('.inventory-window, .inventory, [class*="inventory"], [data-testid*="inventory"]') as HTMLElement
      const hasModals = document.querySelector('[class*="modal"], [id*="modal"], .react-modal')
      const gameElement = document.querySelector('canvas, #game-canvas, [class*="game"]')
      const isGameFocused = gameElement && document.activeElement === gameElement
      
      // More comprehensive context detection
      const isInventoryContext = hasActiveWindow || 
                                 (inventoryElement && inventoryElement.style.display !== 'none') || 
                                 hasModals || 
                                 !isGameFocused
      
      console.log(`[WsCommandClient] Context detection: bot.currentWindow=${bot?.currentWindow?.type}, hasActiveWindow=${hasActiveWindow}, hasModals=${!!hasModals}, isGameFocused=${isGameFocused}, inventory/UI context = ${isInventoryContext}`)

      if (isInventoryContext && wsCursorState.usingWsInput) {
        // UI interaction with cursor positioning for inventory
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
          console.log(`[WsCommandClient] Right click released at cursor position (${x}, ${y}) on element:`, elementAtCursor.tagName)
        } else {
          console.log('[WsCommandClient] No element found at cursor position')
        }
      } else {
        // Use documentMouseEvent for game world
        console.log('[WsCommandClient] Using documentMouseEvent for game world context')
        const event = new MouseEvent('mouseup', {
          bubbles: true,
          cancelable: true,
          button: 2,
          buttons: 0
        })
        Object.defineProperty(event, 'isWebSocketEvent', {
          value: true,
          writable: false,
          enumerable: false
        })
        document.dispatchEvent(event)
        console.log('[WsCommandClient] Game world rightUp completed')
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
        wsCursorState.x = Math.min(100, Math.max(0, cmd.x))
        wsCursorState.y = Math.min(100, Math.max(0, cmd.z))
        emitWsMousemove()
        console.log(`[WsCommandClient] Successfully moved cursor to ${wsCursorState.x}%, ${wsCursorState.y}%`)
      } else if (cmd.movementX !== undefined || cmd.movementY !== undefined) {
        // Relative cursor movement
        const dx = (cmd.movementX || 0) * 0.5 // Adjust sensitivity as needed
        const dy = (cmd.movementY || 0) * 0.5
        moveWsCursorBy(dx, dy)
        emitWsMousemove()
        console.log(`[WsCommandClient] Moved cursor by ${dx}, ${dy}`)
      }
    } catch (error) {
      console.error('[WsCommandClient] Error moving cursor:', error)
    }
  }
}
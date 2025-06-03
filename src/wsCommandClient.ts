import { onCameraMove } from './cameraRotationControls'
import { moveWsCursorBy, emitWsMousemove, wsCursorState } from './react/WsCursor'

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
}

class TouchEvaluator {
  constructor(private bot: any) {}

  // Track active button states to prevent duplicate actions
  private activeButtons = new Set<number>()
  // Track button press timing
  private buttonStartTimes = new Map<number, number>()

  async setup () {
    return !!this.bot
  }
  async execute (cmd: MouseCommand) {
    // Enable WebSocket input mode when any command is received
    wsCursorState.usingWsInput = true

    switch (cmd.type) {
      case 'control':
        this.bot.setControlState(cmd.control!, cmd.state)
        break
      case 'leftDown':
        try {
          console.log('[WsCommandClient] Executing leftDown command')
          if (typeof this.bot.leftClickStart === 'function') {
            this.bot.leftClickStart()
            console.log('[WsCommandClient] leftClickStart executed successfully')
          } else {
            console.error('[WsCommandClient] leftClickStart is not a function:', typeof this.bot.leftClickStart)
          }
        } catch (error) {
          console.error('[WsCommandClient] Error in leftDown:', error)
        }
        break
      case 'leftUp':
        try {
          console.log('[WsCommandClient] Executing leftUp command')
          if (typeof this.bot.leftClickEnd === 'function') {
            this.bot.leftClickEnd()
            console.log('[WsCommandClient] leftClickEnd executed successfully')
          } else {
            console.error('[WsCommandClient] leftClickEnd is not a function:', typeof this.bot.leftClickEnd)
          }
        } catch (error) {
          console.error('[WsCommandClient] Error in leftUp:', error)
        }
        break
      case 'rightDown':
        try {
          console.log('[WsCommandClient] Executing rightDown command')
          if (typeof this.bot.rightClickStart === 'function') {
            this.bot.rightClickStart()
            console.log('[WsCommandClient] rightClickStart executed successfully')
          } else {
            console.error('[WsCommandClient] rightClickStart is not a function:', typeof this.bot.rightClickStart)
          }
        } catch (error) {
          console.error('[WsCommandClient] Error in rightDown:', error)
        }
        break
      case 'rightUp':
        try {
          console.log('[WsCommandClient] Executing rightUp command')
          if (typeof this.bot.rightClickEnd === 'function') {
            this.bot.rightClickEnd()
            console.log('[WsCommandClient] rightClickEnd executed successfully')
          } else {
            console.error('[WsCommandClient] rightClickEnd is not a function:', typeof this.bot.rightClickEnd)
          }
        } catch (error) {
          console.error('[WsCommandClient] Error in rightUp:', error)
        }
        break
      case 'chat':
        this.bot.chat(cmd.message!)
        break
      case 'move': {
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
        break
      }
      case 'look':
        onCameraMove({ movementX: cmd.movementX ?? 0, movementY: cmd.movementY ?? 0, type: 'ws' })
        break
      case 'lookTouch': {
        if (cmd.currentX !== undefined && cmd.lastX !== undefined &&
          cmd.currentY !== undefined && cmd.lastY !== undefined) {
          onCameraMove({
            movementX: (cmd.currentX - cmd.lastX),
            movementY: (cmd.currentY - cmd.lastY),
            type: 'touchmove',
            stopPropagation: () => { } // No-op function for WebSocket context
          })
        }
        break
      }
      case 'clickElement': {
        try {
          console.log(`[WsCommandClient] Executing clickElement: ${cmd.selector} - ${cmd.action}`)
          const element = document.querySelector(cmd.selector!) as HTMLElement
          if (!element) {
            console.error(`[WsCommandClient] Element not found: ${cmd.selector}`)
            break
          }

          if (cmd.action === 'down') {
            // Trigger pointerdown event (touch interface uses pointer events)
            const event = new PointerEvent('pointerdown', {
              bubbles: true,
              cancelable: true,
              pointerId: 1,
              pointerType: 'mouse',
              isPrimary: true,
              button: 0,
              buttons: 1
            })
            element.dispatchEvent(event)
            console.log(`[WsCommandClient] Dispatched pointerdown on ${cmd.selector}`)
          } else if (cmd.action === 'up') {
            // Trigger pointerup event (touch interface uses pointer events)
            const event = new PointerEvent('pointerup', {
              bubbles: true,
              cancelable: true,
              pointerId: 1,
              pointerType: 'mouse',
              isPrimary: true,
              button: 0,
              buttons: 0
            })
            element.dispatchEvent(event)
            console.log(`[WsCommandClient] Dispatched pointerup on ${cmd.selector}`)
          } else if (cmd.action === 'click') {
            // Trigger click event
            element.click()
            console.log(`[WsCommandClient] Clicked ${cmd.selector}`)
          }
        } catch (error) {
          console.error('[WsCommandClient] Error in clickElement:', error)
        }
        break
      }
      case 'documentMouseEvent': {
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
        break
      }
      case 'setHotbarSlot':
        try {
          console.log(`[WsCommandClient] Setting hotbar slot to ${cmd.slot}`)
          if (cmd.slot !== undefined && cmd.slot >= 0 && cmd.slot <= 8) {
            this.bot.setQuickBarSlot(cmd.slot)
            console.log(`[WsCommandClient] Successfully set hotbar slot to ${cmd.slot}`)
          } else {
            console.error(`[WsCommandClient] Invalid hotbar slot: ${cmd.slot}. Must be 0-8.`)
          }
        } catch (error) {
          console.error('[WsCommandClient] Error setting hotbar slot:', error)
        }
        break
      case 'scrollHotbar':
        try {
          console.log(`[WsCommandClient] Scrolling hotbar in direction: ${cmd.direction}`)
          if (cmd.direction !== undefined && (cmd.direction === 1 || cmd.direction === -1)) {
            const newHotbarSlot = (this.bot.quickBarSlot + cmd.direction + 9) % 9
            this.bot.setQuickBarSlot(newHotbarSlot)
            console.log(`[WsCommandClient] Successfully scrolled hotbar to slot ${newHotbarSlot}`)
          } else {
            console.error(`[WsCommandClient] Invalid hotbar scroll direction: ${cmd.direction}. Must be 1 or -1.`)
          }
        } catch (error) {
          console.error('[WsCommandClient] Error scrolling hotbar:', error)
        }
        break
      case 'dropItem':
        try {
          console.log(`[WsCommandClient] Dropping item in amount: ${cmd.amount}`)
          if (cmd.amount !== undefined && cmd.amount >= 1 && cmd.amount <= 64) {
            // Use the same implementation as controls.ts for dropping items
            this.bot._client.write('block_dig', {
              'status': 4,
              'location': {
                'x': 0,
                'z': 0,
                'y': 0
              },
              'face': 0,
              sequence: 0
            })
            const slot = this.bot.inventory.hotbarStart + this.bot.quickBarSlot
            const item = this.bot.inventory.slots[slot]
            if (item) {
              item.count -= cmd.amount
              this.bot.inventory.updateSlot(slot, item.count > 0 ? item : null!)
            }
            console.log(`[WsCommandClient] Successfully dropped ${cmd.amount} items`)
          } else {
            console.error(`[WsCommandClient] Invalid item drop amount: ${cmd.amount}. Must be 1-64.`)
          }
        } catch (error) {
          console.error('[WsCommandClient] Error dropping item:', error)
        }
        break
      case 'swapHands':
        try {
          console.log(`[WsCommandClient] Swapping hands`)
          // Use the same implementation as controls.ts
          this.bot._client.write('entity_action', {
            entityId: this.bot.entity.id,
            actionId: 6,
            jumpBoost: 0
          })
          console.log(`[WsCommandClient] Successfully swapped hands`)
        } catch (error) {
          console.error('[WsCommandClient] Error swapping hands:', error)
        }
        break
      case 'cursor':
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
        break
    }
  }
}

class Worker {
  private queue: MouseCommand[] = []
  private running = false
  constructor(private evaluator: TouchEvaluator) {}
  start () {
    if (this.running) return
    this.running = true
    void this.processLoop()
  }
  enqueue (cmd: MouseCommand) {
    this.queue.push(cmd)
  }
  private async processLoop () {
    while (this.running) {
      const cmd = this.queue.shift()
      if (cmd) {
        try {
          await this.evaluator.execute(cmd)
        } catch (e) {
          console.error('Worker error', e)
        }
      }
      await new Promise(r => setTimeout(r, 10))
    }
  }
}

export function setupWsCommandClient (bot: any) {
  const evaluator = new TouchEvaluator(bot)
  const worker = new Worker(evaluator)
  worker.start()

  // Get the current port and calculate WebSocket port (HTTP port + 1)
  const currentPort = location.port || (location.protocol === 'https:' ? '443' : '80')
  // const wsPort = parseInt(currentPort) + 1
  const wsPort = 8081
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  const wsUrl = `${protocol}://${location.hostname}:${wsPort}`

  console.log(`[WsCommandClient] Connecting to WebSocket server at: ${wsUrl}`)

  const ws = new WebSocket(wsUrl)

  ws.addEventListener('open', () => {
    console.log(`[WsCommandClient] Connected to WebSocket server, registering as bot client`)
    ws.send(JSON.stringify({ init: 'bot' }))
  })

  ws.addEventListener('message', ev => {
    try {
      const cmd = JSON.parse(ev.data as string) as MouseCommand
      console.log(`[WsCommandClient] Received command:`, cmd)
      worker.enqueue(cmd)
    } catch (err) {
      console.error('[WsCommandClient] Invalid command', err)
    }
  })

  ws.addEventListener('close', (event) => {
    console.log(`[WsCommandClient] WebSocket connection closed:`, event.code, event.reason)
  })

  ws.addEventListener('error', (error) => {
    console.error('[WsCommandClient] WebSocket error:', error)
  })
}

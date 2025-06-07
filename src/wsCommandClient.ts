import { onCameraMove } from './cameraRotationControls'
import { moveWsCursorBy, emitWsMousemove, wsCursorState } from './react/WsCursor'
import { togglePlayerInventory } from './inventoryWindows'
import html2canvas from 'html2canvas'
import * as THREE from 'three'

function createTextSprite(text: string): THREE.Sprite {
  const canvas = document.createElement('canvas')
  const context = canvas.getContext('2d')!
  const fontSize = 20
  context.font = `${fontSize}px Arial`
  const textWidth = context.measureText(text).width + 4
  canvas.width = textWidth
  canvas.height = fontSize * 1.5
  context.font = `${fontSize}px Arial`
  context.fillStyle = 'white'
  context.strokeStyle = 'black'
  context.lineWidth = 4
  context.strokeText(text, 2, fontSize)
  context.fillText(text, 2, fontSize)
  const texture = new THREE.CanvasTexture(canvas)
  const material = new THREE.SpriteMaterial({ map: texture, transparent: true })
  const sprite = new THREE.Sprite(material)
  sprite.scale.set(canvas.width / 20, canvas.height / 20, 1)
  return sprite
}

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

class TouchEvaluator {
  constructor(private bot: any, private ws?: WebSocket) { }

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
      case 'annotate_3d_position': {
        try {
          const scene = (window as any).world?.scene || (window as any).viewer?.scene || (window as any).scene
          if (!scene) {
            console.error('[WsCommandClient] Scene not found for annotation')
            break
          }
          const color = cmd.color || 'red'
          const geometry = new THREE.SphereGeometry(0.5, 16, 12)
          const material = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.8 })
          const marker = new THREE.Mesh(geometry, material)
          marker.position.set((cmd.worldX ?? 0) + 0.5, (cmd.worldY ?? 0) + 0.5, (cmd.worldZ ?? 0) + 0.5)
          const id = cmd.markerId || `marker_${Date.now()}`
          ;(marker as any).userData = { isAnnotationMarker: true, markerId: id }
          if (cmd.label) {
            const sprite = createTextSprite(cmd.label)
            sprite.position.set(0, 1.5, 0)
            marker.add(sprite)
          }
          scene.add(marker)
          console.log(`[WsCommandClient] Added marker ${id} at (${cmd.worldX}, ${cmd.worldY}, ${cmd.worldZ})`)
        } catch (error) {
          console.error('[WsCommandClient] Error handling annotate_3d_position:', error)
        }
        break
      }
      case 'getScreenshot':
        try {
          console.log('[WsCommandClient] Capturing full page screenshot including UI elements')

          // Wait for the next frame to ensure rendering is complete
          await new Promise(resolve => requestAnimationFrame(resolve))

          // Create a timeout promise to prevent hanging
          const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => reject(new Error('Screenshot capture timeout')), 10000)
          })

          // Create the screenshot capture promise
          const capturePromise = new Promise<string>((resolve, reject) => {
            try {
              // Use a small delay to ensure the frame is fully rendered
              setTimeout(async () => {
                try {
                  console.log('[WsCommandClient] Using html2canvas for complete page capture')

                  // Use html2canvas to capture the entire page including all UI elements
                  const canvas = await html2canvas(document.body, {
                    useCORS: true,
                    allowTaint: true,
                    backgroundColor: null,
                    scale: 0.8, // Downscale for smaller file size
                    logging: false,
                    ignoreElements: (element) => {
                      // Optionally ignore certain elements (e.g., debug overlays)
                      return element.classList?.contains('ignore-screenshot') || false
                    },
                    // Capture WebGL canvases properly
                    foreignObjectRendering: true,
                    canvas: undefined
                  })

                  const dataUrl = canvas.toDataURL('image/png', 0.8)
                  const base64Data = dataUrl.split(',')[1]

                  console.log(`[WsCommandClient] Full page screenshot captured successfully: ${canvas.width}x${canvas.height}`)
                  resolve(base64Data)
                } catch (error) {
                  console.warn('[WsCommandClient] html2canvas failed, falling back to canvas-only capture:', error)

                  // Fallback to canvas-only capture if html2canvas fails
                  const gameCanvas = document.getElementById('viewer-canvas') as HTMLCanvasElement
                  if (!gameCanvas) {
                    throw new Error('Game canvas not found and html2canvas failed')
                  }

                  // Create a downscaled version of just the game canvas
                  const originalWidth = gameCanvas.width
                  const originalHeight = gameCanvas.height
                  const scaleFactor = 0.8
                  const scaledWidth = Math.floor(originalWidth * scaleFactor)
                  const scaledHeight = Math.floor(originalHeight * scaleFactor)

                  const fallbackCanvas = document.createElement('canvas')
                  fallbackCanvas.width = scaledWidth
                  fallbackCanvas.height = scaledHeight
                  const ctx = fallbackCanvas.getContext('2d')

                  if (!ctx) {
                    throw new Error('Failed to get 2D context for fallback canvas')
                  }

                  ctx.imageSmoothingEnabled = true
                  ctx.imageSmoothingQuality = 'high'
                  ctx.drawImage(gameCanvas, 0, 0, originalWidth, originalHeight, 0, 0, scaledWidth, scaledHeight)

                  const dataUrl = fallbackCanvas.toDataURL('image/png', 0.8)
                  const base64Data = dataUrl.split(',')[1]

                  console.log(`[WsCommandClient] Fallback screenshot captured: ${scaledWidth}x${scaledHeight} (UI elements not included)`)
                  resolve(base64Data)
                }
              }, 100)
            } catch (error) {
              reject(error)
            }
          })

          // Race between capture and timeout
          const base64Data = await Promise.race([capturePromise, timeoutPromise])

          console.log('[WsCommandClient] Screenshot captured successfully')
          const status = this.collectBotStatus()
          const readableStatus = this.prettyPrintBotStatus(status)
          if (this.ws) {
            this.ws.send(JSON.stringify({
              type: 'screenshot',
              data: base64Data,
              status: readableStatus,
              statusData: status
            }))
          }
        } catch (error) {
          console.error('[WsCommandClient] Error capturing screenshot:', error)
          if (this.ws) {
            this.ws.send(JSON.stringify({
              type: 'screenshot',
              data: 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
              error: error.message
            }))
          }
        }
        break
      case 'getBotStatus':
        try {
          const status = this.collectBotStatus()
          if (this.ws) {
            this.ws.send(JSON.stringify({
              type: 'botStatus',
              data: status
            }))
          }
        } catch (error) {
          console.error('[WsCommandClient] Error getting bot status:', error)
        }
        break
      case 'inventory':
        try {
          console.log('[WsCommandClient] Toggling player inventory')
          // Exit pointer lock and toggle player inventory, same as controls.ts
          document.exitPointerLock?.()
          togglePlayerInventory()
          console.log('[WsCommandClient] Successfully toggled player inventory')
        } catch (error) {
          console.error('[WsCommandClient] Error toggling inventory:', error)
        }
        break
    }
  }

  private getCardinalDirection (yaw: number): string {
    let degrees = (yaw * 180 / Math.PI + 360) % 360
    if (degrees >= 315 || degrees < 45) return 'North'
    else if (degrees >= 45 && degrees < 135) return 'East'
    else if (degrees >= 135 && degrees < 225) return 'South'
    else return 'West'
  }

  private collectBotStatus () {
    const position = this.bot.entity.position.floored()
    const block = this.bot.blockAtCursor()
    const currentBiome = this.bot.blockAt(this.bot.entity.position).biome

    const activeEntityStates: any = {}
    if (this.bot.entity.isFlying) activeEntityStates.isFlying = true
    if (this.bot.entity.isInLava) activeEntityStates.isInLava = true
    if (this.bot.entity.isInWater) activeEntityStates.isInWater = true
    if (this.bot.entity.isInWeb) activeEntityStates.isInWeb = true
    if (this.bot.entity.isInvulnerable) activeEntityStates.isInvulnerable = true
    if (this.bot.entity.isUnderLava) activeEntityStates.isUnderLava = true
    if (this.bot.entity.isUnderWater) activeEntityStates.isUnderWater = true

    const hotbarItems: any = {}
    for (let i = 0; i < 9; i++) {
      const item = this.bot.inventory.slots[this.bot.QUICK_BAR_START + i]
      if (item) {
        hotbarItems[i] = {
          displayName: item.displayName,
          count: item.count
        }
      }
    }

    const timeOfDay = this.bot.time.timeOfDay
    let timeUntilNext: { event: string, minutes: number }
    if (timeOfDay < 12000) {
      const minutesUntilSunset = (12000 - timeOfDay) / 1200
      timeUntilNext = { event: 'sunset', minutes: Math.round(minutesUntilSunset * 100) / 100 }
    } else {
      const minutesUntilSunrise = (24000 - timeOfDay) / 1200
      timeUntilNext = { event: 'sunrise', minutes: Math.round(minutesUntilSunrise * 100) / 100 }
    }

    return {
      position: { x: position.x, y: position.y, z: position.z },
      rotation: {
        yaw: Math.round((this.bot.entity.yaw * 180 / Math.PI) * 100) / 100,
        pitch: Math.round((this.bot.entity.pitch * 180 / Math.PI) * 100) / 100,
        cardinalDirection: this.getCardinalDirection(this.bot.entity.yaw)
      },
      biome: { displayName: currentBiome.displayName },
      inventory: { currentSlot: this.bot.quickBarSlot, hotbarItems },
      time: {
        timeOfDay: this.bot.time.timeOfDay,
        day: this.bot.time.day,
        isDay: this.bot.time.isDay,
        timeUntilNext
      },
      entityState: activeEntityStates,
      targetBlock: block ? {
        displayName: block.displayName,
        canDig: this.bot.canDigBlock(block),
        biome: block.biome,
        position: block.position
      } : {
        message: 'pointing at a block that is too far away'
      }
    }
  }

  private prettyPrintBotStatus (status: any): string {
    const lines: string[] = []
    const pos = status.position
    const rot = status.rotation
    lines.push(`Position: (${pos.x}, ${pos.y}, ${pos.z}) facing ${rot.cardinalDirection} (${rot.yaw}°, ${rot.pitch}°)`)
    lines.push(`Biome: ${status.biome.displayName}`)
    const time = status.time
    const minutes = time.timeUntilNext.minutes.toFixed(2)
    lines.push(`Day ${time.day}, ${minutes} minutes until ${time.timeUntilNext.event}`)
    lines.push(`Selected slot: ${status.inventory.currentSlot}`)
    const hotbarItems = status.inventory.hotbarItems
    if (Object.keys(hotbarItems).length > 0) {
      const itemStrings = Object.entries(hotbarItems).map(([slot, item]: [string, any]) => `[${slot}: ${item.displayName} x${item.count}]`)
      lines.push(`Hotbar: ${itemStrings.join(' ')}`)
    } else {
      lines.push('Hotbar: Empty')
    }
    const entityStates = Object.keys(status.entityState)
    if (entityStates.length > 0) {
      const stateNames = entityStates.map(state => state.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase()))
      lines.push(`Status: ${stateNames.join(', ')}`)
    }
    if (status.targetBlock.message) {
      lines.push(`Looking at: ${status.targetBlock.message}`)
    } else {
      const block = status.targetBlock
      const canDigText = block.canDig ? 'can dig' : 'cannot dig'
      lines.push(`Looking at: ${block.displayName} (${canDigText})`)
    }
    return lines.join('\n')
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

export function setupWsCommandClient(bot: any) {
  // Get the current port and calculate WebSocket port (HTTP port + 1)
  const currentPort = location.port || (location.protocol === 'https:' ? '443' : '80')
  // const wsPort = parseInt(currentPort) + 1
  const wsPort = 8081
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  const wsUrl = `${protocol}://${location.hostname}:${wsPort}`

  console.log(`[WsCommandClient] Connecting to WebSocket server at: ${wsUrl}`)

  const ws = new WebSocket(wsUrl)

  // Create evaluator and worker with WebSocket reference
  const evaluator = new TouchEvaluator(bot, ws)
  const worker = new Worker(evaluator)
  worker.start()

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

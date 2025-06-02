import { onCameraMove } from './cameraRotationControls'

export interface MouseCommand {
  type: 'control' | 'leftDown' | 'leftUp' | 'rightDown' | 'rightUp' | 'chat' | 'move' | 'look' | 'lookTouch' | 'clickElement'
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
}

class TouchEvaluator {
  constructor(private bot: any) {}
  async setup () {
    return !!this.bot
  }
  async execute (cmd: MouseCommand) {
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

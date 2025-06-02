import { onCameraMove } from './cameraRotationControls'

export interface MouseCommand {
  type: 'control' | 'leftDown' | 'leftUp' | 'rightDown' | 'rightUp' | 'chat' | 'move' | 'look' | 'lookTouch'
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
        this.bot.leftClickStart()
        break
      case 'leftUp':
        this.bot.leftClickEnd()
        break
      case 'rightDown':
        this.bot.rightClickStart()
        break
      case 'rightUp':
        this.bot.rightClickEnd()
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

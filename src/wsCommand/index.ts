import { TouchEvaluator } from './TouchEvaluator'
import { Worker } from './Worker'
import type { MouseCommand } from './types'

export function setupWsCommandClient(bot: any) {
  // Get the current port and calculate WebSocket port (HTTP port + 1)
  // const currentPort = location.port || (location.protocol === 'https:' ? '443' : '80')
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

// Re-export types and classes for backwards compatibility
export type { MouseCommand } from './types'
export { TouchEvaluator } from './TouchEvaluator'
export { Worker } from './Worker'
import { MouseCommand } from './types'
import { TouchEvaluator } from './TouchEvaluator'

export class Worker {
  private queue: MouseCommand[] = []
  private running = false
  
  constructor(private evaluator: TouchEvaluator) {}
  
  start() {
    if (this.running) return
    this.running = true
    void this.processLoop()
  }
  
  enqueue(cmd: MouseCommand) {
    this.queue.push(cmd)
  }
  
private async processLoop() {
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
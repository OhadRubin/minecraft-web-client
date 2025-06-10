import { MouseCommand } from '../types'

export class UICommandHandler {
  constructor(private bot: any) {}

  async handleClickElement(cmd: MouseCommand) {
    try {
      const element = document.querySelector(cmd.selector!) as HTMLElement
      if (!element) {
        console.error(`[WsCommandClient] Element not found: ${cmd.selector}`)
        return
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
      } else if (cmd.action === 'click') {
        // Trigger click event
        element.click()
      }
    } catch (error) {
      console.error('[WsCommandClient] Error in clickElement:', error)
    }
  }
}
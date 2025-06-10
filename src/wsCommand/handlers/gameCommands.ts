import { MouseCommand } from '../types'
import { togglePlayerInventory } from '../../inventoryWindows'

export class GameCommandHandler {
  constructor(private bot: any) {}

  async handleChat(cmd: MouseCommand) {
    this.bot.chat(cmd.message!)
  }

  async handleSetHotbarSlot(cmd: MouseCommand) {
    try {
      if (cmd.slot !== undefined && cmd.slot >= 0 && cmd.slot <= 8) {
        this.bot.setQuickBarSlot(cmd.slot)
      } else {
        console.error(`[WsCommandClient] Invalid hotbar slot: ${cmd.slot}. Must be 0-8.`)
      }
    } catch (error) {
      console.error('[WsCommandClient] Error setting hotbar slot:', error)
    }
  }

  async handleScrollHotbar(cmd: MouseCommand) {
    try {
      if (cmd.direction !== undefined && (cmd.direction === 1 || cmd.direction === -1)) {
        const newHotbarSlot = (this.bot.quickBarSlot + cmd.direction + 9) % 9
        this.bot.setQuickBarSlot(newHotbarSlot)
      } else {
        console.error(`[WsCommandClient] Invalid hotbar scroll direction: ${cmd.direction}. Must be 1 or -1.`)
      }
    } catch (error) {
      console.error('[WsCommandClient] Error scrolling hotbar:', error)
    }
  }

  async handleDropItem(cmd: MouseCommand) {
    try {
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
      } else {
        console.error(`[WsCommandClient] Invalid item drop amount: ${cmd.amount}. Must be 1-64.`)
      }
    } catch (error) {
      console.error('[WsCommandClient] Error dropping item:', error)
    }
  }

  async handleSwapHands(cmd: MouseCommand) {
    try {
      // Use the same implementation as controls.ts
      this.bot._client.write('entity_action', {
        entityId: this.bot.entity.id,
        actionId: 6,
        jumpBoost: 0
      })
    } catch (error) {
      console.error('[WsCommandClient] Error swapping hands:', error)
    }
  }

  async handleInventory(cmd: MouseCommand) {
    try {
      // Exit pointer lock and toggle player inventory, same as controls.ts
      document.exitPointerLock?.()
      togglePlayerInventory()
    } catch (error) {
      console.error('[WsCommandClient] Error toggling inventory:', error)
    }
  }
}
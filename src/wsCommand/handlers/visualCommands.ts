import { MouseCommand } from '../types'
import { createTextSprite, resizeImageBase64 } from '../utils'
import html2canvas from 'html2canvas'
import * as THREE from 'three'

export class VisualCommandHandler {
  constructor(private bot: any, private ws?: WebSocket) {}

  async handleAnnotate3dPosition(cmd: MouseCommand) {
    try {
      const scene = (window as any).world?.scene || (window as any).viewer?.scene || (window as any).scene
      if (!scene) {
        console.error('[WsCommandClient] Scene not found for annotation')
        return
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
    } catch (error) {
      console.error('[WsCommandClient] Error handling annotate_3d_position:', error)
    }
  }

  async handleGetScreenshot(cmd: MouseCommand) {
    try {

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

              // Use html2canvas to capture the entire page including all UI elements
              const canvas = await html2canvas(document.body, {
                useCORS: true,
                allowTaint: true,
                backgroundColor: null,
                scale: 1, // Full size capture
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

              // Resize the image to 1080 pixels width while maintaining aspect ratio

              try {
                // Resize the captured image to 1080 width
                const resizedDataUrl = await resizeImageBase64(dataUrl, 1080)
                const resizedBase64Data = resizedDataUrl.split(',')[1]

                resolve(resizedBase64Data)
              } catch (resizeError) {
                console.warn('[WsCommandClient] Failed to resize screenshot, using original:', resizeError)
                resolve(base64Data)
              }
            } catch (error) {
              console.error('[WsCommandClient] html2canvas failed:', error)
              reject(error)
            }
          }, 100)
        } catch (error) {
          reject(error)
        }
      })

      // Race between capture and timeout
      const base64Data = await Promise.race([capturePromise, timeoutPromise])

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
  }

  async handleGetBotStatus(cmd: MouseCommand) {
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
  }

  private getCardinalDirection(yaw: number): string {
    let degrees = (yaw * 180 / Math.PI + 360) % 360
    if (degrees >= 315 || degrees < 45) return 'North'
    else if (degrees >= 45 && degrees < 135) return 'East'
    else if (degrees >= 135 && degrees < 225) return 'South'
    else return 'West'
  }

  private collectBotStatus() {
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

  private prettyPrintBotStatus(status: any): string {
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
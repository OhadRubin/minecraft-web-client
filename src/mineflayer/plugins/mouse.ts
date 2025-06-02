import { createMouse } from 'mineflayer-mouse'
import { Bot } from 'mineflayer'
import { Block } from 'prismarine-block'
import { getThreeJsRendererMethods } from 'renderer/viewer/three/threeJsMethods'
import { isGameActive, showModal } from '../../globalState'

import { isCypress } from '../../standaloneUtils'
import { playerState } from '../playerState'
import { sendVideoInteraction, videoCursorInteraction } from '../../customChannels'

function cursorBlockDisplay (bot: Bot) {
  const updateCursorBlock = (data?: { block: Block }) => {
    if (!data?.block || bot.game.gameMode === 'spectator') {
      playerState.reactive.lookingAtBlock = undefined
      return
    }

    const { block } = data
    playerState.reactive.lookingAtBlock = {
      x: block.position.x,
      y: block.position.y,
      z: block.position.z,
      shapes: bot.mouse.getBlockCursorShapes(block).map(shape => {
        return bot.mouse.getDataFromShape(shape)
      })
    }
  }

  bot.on('highlightCursorBlock', updateCursorBlock)
  bot.on('game', () => {
    const block = bot.mouse.getCursorState().cursorBlock
    updateCursorBlock(block ? { block } : undefined)
  })

  bot.on('blockBreakProgressStage', (block, stage) => {
    const mergedShape = bot.mouse.getMergedCursorShape(block)
    playerState.reactive.diggingBlock = stage === null ? undefined : {
      x: block.position.x,
      y: block.position.y,
      z: block.position.z,
      stage,
      mergedShape: mergedShape ? bot.mouse.getDataFromShape(mergedShape) : undefined
    }
  })
}

export default (bot: Bot) => {
  bot.loadPlugin(createMouse({}))

  domListeners(bot)
  cursorBlockDisplay(bot)

  otherListeners()
}

const otherListeners = () => {
  bot.on('startDigging', (block) => {
    customEvents.emit('digStart')
  })

  bot.on('goingToSleep', () => {
    showModal({ reactType: 'bed' })
  })

  bot.on('botArmSwingStart', (hand) => {
    getThreeJsRendererMethods()?.changeHandSwingingState(true, hand === 'left')
  })

  bot.on('botArmSwingEnd', (hand) => {
    getThreeJsRendererMethods()?.changeHandSwingingState(false, hand === 'left')
  })

  bot.on('startUsingItem', (item, slot, isOffhand, duration) => {
    customEvents.emit('activateItem', item, isOffhand ? 45 : bot.quickBarSlot, isOffhand)
    playerState.startUsingItem()
  })

  bot.on('stopUsingItem', () => {
    playerState.stopUsingItem()
  })
}

const domListeners = (bot: Bot) => {
  const abortController = new AbortController()

  // Track button press timing
  const buttonPressTimestamps = new Map<number, number>()

  document.addEventListener('mousedown', (e) => {
    const timestamp = Date.now()

    // Allow WebSocket synthetic events to bypass validation
    const isWebSocketEvent = (e as any).isWebSocketEvent === true

    if (!isWebSocketEvent) {
    // Normal validation for regular mouse events
      if (e.isTrusted && !document.pointerLockElement && !isCypress()) return
      if (!isGameActive(true)) return
    } else {
      console.log('[Mouse Plugin] Allowing WebSocket synthetic event to bypass validation')
    }

    getThreeJsRendererMethods()?.onPageInteraction()

    const videoInteraction = videoCursorInteraction()
    if (videoInteraction) {
      sendVideoInteraction(videoInteraction.id, videoInteraction.x, videoInteraction.y, e.button === 0)
      return
    }

    if (e.button === 0) {
      buttonPressTimestamps.set(0, timestamp)
      console.log(`[Mouse Plugin] Processing left click start at ${timestamp}`)
      bot.leftClickStart()

      // Manually ensure the button state is set (bypasses beforeUpdateChecks clearing)
      if (bot.mouse?.buttons) {
        bot.mouse.buttons[0] = true
        console.log('[Mouse Plugin] Set left button active, state:', bot.mouse.buttons[0])
      }
    } else if (e.button === 2) {
      buttonPressTimestamps.set(2, timestamp)
      console.log(`[Mouse Plugin] Processing right click start at ${timestamp}`)
      bot.rightClickStart()

      // Manually ensure the button state is set (bypasses beforeUpdateChecks clearing)  
      if (bot.mouse?.buttons) {
        bot.mouse.buttons[2] = true
        console.log('[Mouse Plugin] Set right button active, state:', bot.mouse.buttons[2])
      }
    }
  }, { signal: abortController.signal })

  document.addEventListener('mouseup', (e) => {
    const timestamp = Date.now()

    // Allow WebSocket synthetic events to bypass validation for mouseup too
    const isWebSocketEvent = (e as any).isWebSocketEvent === true

    if (!isWebSocketEvent) {
      // For mouseup, we're less strict but still check if it's a trusted event in normal cases
      // Note: mouseup doesn't have the same validation as mousedown in the original code
    } else {
      console.log('[Mouse Plugin] Allowing WebSocket synthetic mouseup event')
    }

    if (e.button === 0) {
      const startTime = buttonPressTimestamps.get(0)
      const duration = startTime ? timestamp - startTime : 'unknown'
      console.log(`[Mouse Plugin] Processing left click end at ${timestamp} (duration: ${duration}ms)`)

      bot.leftClickEnd()

      // Manually ensure the button state is cleared
      if (bot.mouse?.buttons) {
        bot.mouse.buttons[0] = false
        console.log('[Mouse Plugin] Set left button inactive, state:', bot.mouse.buttons[0])
      }

      buttonPressTimestamps.delete(0)
    } else if (e.button === 2) {
      const startTime = buttonPressTimestamps.get(2)
      const duration = startTime ? timestamp - startTime : 'unknown'
      console.log(`[Mouse Plugin] Processing right click end at ${timestamp} (duration: ${duration}ms)`)

      bot.rightClickEnd()

      // Manually ensure the button state is cleared
      if (bot.mouse?.buttons) {
        bot.mouse.buttons[2] = false
        console.log('[Mouse Plugin] Set right button inactive, state:', bot.mouse.buttons[2])
      }

      buttonPressTimestamps.delete(2)
    }
  }, { signal: abortController.signal })

  bot.mouse.beforeUpdateChecks = () => {
    if (!document.hasFocus()) {
      // deactive all buttons
      bot.mouse.buttons.fill(false)
    }
  }

  bot.on('end', () => {
    abortController.abort()
  })
}

import { MouseCommand } from './types'
import { miscUiState } from '../globalState'
import { MouseCommandHandler } from './handlers/mouseCommands'
import { MovementCommandHandler } from './handlers/movementCommands'
import { GameCommandHandler } from './handlers/gameCommands'
import { UICommandHandler } from './handlers/uiCommands'
import { VisualCommandHandler } from './handlers/visualCommands'
import { GamepadCommandHandler } from './handlers/gamepadCommands'

export class TouchEvaluator {
  private mouseHandler: MouseCommandHandler
  private movementHandler: MovementCommandHandler
  private gameHandler: GameCommandHandler
  private uiHandler: UICommandHandler
  private visualHandler: VisualCommandHandler
  private gamepadHandler: GamepadCommandHandler

  constructor(private bot: any, ws?: WebSocket) {
    this.mouseHandler = new MouseCommandHandler(bot)
    this.movementHandler = new MovementCommandHandler(bot)
    this.gameHandler = new GameCommandHandler(bot)
    this.uiHandler = new UICommandHandler(bot)
    this.visualHandler = new VisualCommandHandler(bot, ws)
    this.gamepadHandler = new GamepadCommandHandler()
  }

  async setup() {
    return !!this.bot
  }

  async execute(cmd: MouseCommand) {
    // Enable WebSocket input mode when any command is received
    miscUiState.usingWsInput = true

    switch (cmd.type) {
      case 'control':
        await this.movementHandler.handleControl(cmd)
        break
      case 'leftDown':
        await this.mouseHandler.handleLeftDown(cmd)
        break
      case 'leftUp':
        await this.mouseHandler.handleLeftUp(cmd)
        break
      case 'rightDown':
        await this.mouseHandler.handleRightDown(cmd)
        break
      case 'rightUp':
        await this.mouseHandler.handleRightUp(cmd)
        break
      case 'contextRightClick':
        await this.mouseHandler.handleContextRightClick(cmd)
        break
      case 'chat':
        await this.gameHandler.handleChat(cmd)
        break
      case 'move':
        await this.movementHandler.handleMove(cmd)
        break
      case 'look':
        await this.movementHandler.handleLook(cmd)
        break
      case 'lookTouch':
        await this.movementHandler.handleLookTouch(cmd)
        break
      case 'clickElement':
        await this.uiHandler.handleClickElement(cmd)
        break
      case 'documentMouseEvent':
        await this.mouseHandler.handleDocumentMouseEvent(cmd)
        break
      case 'setHotbarSlot':
        await this.gameHandler.handleSetHotbarSlot(cmd)
        break
      case 'scrollHotbar':
        await this.gameHandler.handleScrollHotbar(cmd)
        break
      case 'dropItem':
        await this.gameHandler.handleDropItem(cmd)
        break
      case 'swapHands':
        await this.gameHandler.handleSwapHands(cmd)
        break
      case 'cursor':
        await this.mouseHandler.handleCursor(cmd)
        break
      case 'annotate_3d_position':
        await this.visualHandler.handleAnnotate3dPosition(cmd)
        break
      case 'getScreenshot':
        await this.visualHandler.handleGetScreenshot(cmd)
        break
      case 'getBotStatus':
        await this.visualHandler.handleGetBotStatus(cmd)
        break
      case 'inventory':
        await this.gameHandler.handleInventory(cmd)
        break
      case 'gamepadConnect':
        await this.gamepadHandler.handleGamepadConnect(cmd)
        break
      case 'gamepadButtonPressDown':
        await this.gamepadHandler.handleGamepadButtonPressDown(cmd)
        break
      case 'gamepadButtonPressUp':
        await this.gamepadHandler.handleGamepadButtonPressUp(cmd)
        break
      case 'gamepadDestroy':
        await this.gamepadHandler.handleGamepadDestroy(cmd)
        break
      case 'gamepadJoystickMove':
        await this.gamepadHandler.handleGamepadJoystickMove(cmd)
        break
      case 'gamepadJoystickCenter':
        await this.gamepadHandler.handleGamepadJoystickCenter(cmd)
        break
    }
  }
}
import { proxy, useSnapshot } from 'valtio'
import { useEffect } from 'react'
import { activeModalStack, miscUiState } from '../globalState'
import SharedHudVars from './SharedHudVars'
import styles from './GamepadUiCursor.module.css'

export const gamepadUiCursorState = proxy({
  x: 50,
  y: 50,
  multiply: 1,
  display: false
})

export const moveGamepadCursorByPx = (value: number, isX: boolean) => {
  value *= gamepadUiCursorState.multiply * 3
  const valueToPercentage = value / (isX ? window.innerWidth : window.innerHeight) * 100
  gamepadUiCursorState[isX ? 'x' : 'y'] += valueToPercentage
}

export const moveGamepadCursorBy = (dx: number, dy: number) => {
  gamepadUiCursorState.x = Math.min(100, Math.max(0, gamepadUiCursorState.x + dx))
  gamepadUiCursorState.y = Math.min(100, Math.max(0, gamepadUiCursorState.y + dy))
}

export default () => {
  const hasModals = useSnapshot(activeModalStack).length > 0
  const { x, y } = useSnapshot(gamepadUiCursorState)
  const { usingGamepadInput, usingWsInput, gameLoaded } = useSnapshot(miscUiState)

  const doDisplay = (usingGamepadInput || usingWsInput) && (hasModals || !gameLoaded)

  useEffect(() => {
    document.body.style.cursor = gameLoaded && !hasModals && (usingGamepadInput || usingWsInput) ? 'none' : 'auto'
  }, [usingGamepadInput, usingWsInput, hasModals, gameLoaded])

  useEffect(() => {
    gamepadUiCursorState.display = doDisplay
  }, [doDisplay])

  useEffect(() => {
    // Auto-center cursor when modals open
    if (hasModals && doDisplay) {
      gamepadUiCursorState.x = 50
      gamepadUiCursorState.y = 50
    }
  }, [hasModals, doDisplay])

  if (!doDisplay) return null

  return <SharedHudVars>
    <div className={styles.crosshair} style={{ left: `${x}%`, top: `${y}%` }} />
  </SharedHudVars>
}

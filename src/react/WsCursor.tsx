import { proxy, useSnapshot } from 'valtio'
import { useEffect } from 'react'
import { activeModalStack, miscUiState } from '../globalState'
import SharedHudVars from './SharedHudVars'
import styles from './GamepadUiCursor.module.css'

export const wsCursorState = proxy({
  x: 50,
  y: 50,
  display: false,
  usingWsInput: false,
})

export const moveWsCursorBy = (dx: number, dy: number) => {
  wsCursorState.x = Math.min(100, Math.max(0, wsCursorState.x + dx))
  wsCursorState.y = Math.min(100, Math.max(0, wsCursorState.y + dy))
}

export const emitWsMousemove = () => {
  const { x, y } = wsCursorState
  const xAbs = (x / 100) * window.innerWidth
  const yAbs = (y / 100) * window.innerHeight
  const element = document.elementFromPoint(xAbs, yAbs) as HTMLElement | null
  if (element) {
    element.dispatchEvent(new MouseEvent('mousemove', {
      clientX: xAbs,
      clientY: yAbs,
    }))
  }
}

export default function WsCursor () {
  const hasModals = useSnapshot(activeModalStack).length > 0
  const { x, y, usingWsInput } = useSnapshot(wsCursorState)
  const { gameLoaded } = useSnapshot(miscUiState)

  // Show WS cursor when using WebSocket input and (has modals OR game not loaded)
  // This matches the GamepadUiCursor logic for inventory/menu navigation
  const doDisplay = usingWsInput && (hasModals || !gameLoaded)

  useEffect(() => {
    wsCursorState.display = doDisplay
  }, [doDisplay])

  useEffect(() => {
    // Set usingWsInput to true when WsCursor is mounted
    // This assumes that if WsCursor is being used, we're in WebSocket mode
    wsCursorState.usingWsInput = true
    
    return () => {
      wsCursorState.usingWsInput = false
    }
  }, [])

  if (!doDisplay) return null
  
  return (
    <SharedHudVars>
      <div className={styles.crosshair} style={{ left: `${x}%`, top: `${y}%` }} />
    </SharedHudVars>
  )
} 
import { proxy, useSnapshot } from 'valtio'
import SharedHudVars from './SharedHudVars'
import styles from './GamepadUiCursor.module.css'

export const wsCursorState = proxy({
  x: 50,
  y: 50,
  display: true,
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
  const { x, y, display } = useSnapshot(wsCursorState)
  if (!display) return null
  return (
    <SharedHudVars>
      <div className={styles.crosshair} style={{ left: `${x}%`, top: `${y}%` }} />
    </SharedHudVars>
  )
} 
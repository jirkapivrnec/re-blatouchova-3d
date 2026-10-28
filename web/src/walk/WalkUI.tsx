import { useEffect, useRef, useState } from 'react'
import { input, isTouch, useWalk, walkStore } from './store'

const canvas = () => document.querySelector('canvas')

function lock() {
  const c = canvas()
  if (!c) return
  try {
    const r = c.requestPointerLock() as unknown as Promise<void> | undefined
    r?.catch?.(() => walkStore.set({ active: true }))
  } catch {
    walkStore.set({ active: true })
  }
}

/** Cross-fade to black around a mode switch. */
function useFade() {
  const [on, setOn] = useState(false)
  const run = (fn: () => void) => {
    setOn(true)
    setTimeout(() => {
      fn()
      setTimeout(() => setOn(false), 120)
    }, 380)
  }
  return { on, run }
}

export function EnterButton({ onEnter }: { onEnter: () => void }) {
  return (
    <button className="enter" onClick={onEnter}>
      <span className="enter-dot" />
      <span>Vstoupit</span>
      <i>→</i>
    </button>
  )
}

function Joystick() {
  const base = useRef<HTMLDivElement>(null)
  const knob = useRef<HTMLDivElement>(null)
  const id = useRef<number | null>(null)
  const move = (e: React.PointerEvent) => {
    if (id.current !== e.pointerId || !base.current || !knob.current) return
    const r = base.current.getBoundingClientRect()
    const R = r.width / 2
    let x = (e.clientX - (r.left + R)) / R
    let y = (e.clientY - (r.top + R)) / R
    const l = Math.hypot(x, y)
    if (l > 1) { x /= l; y /= l }
    input.joy.x = x
    input.joy.y = y
    knob.current.style.transform = `translate(${x * R * 0.6}px, ${y * R * 0.6}px)`
  }
  const end = (e: React.PointerEvent) => {
    if (id.current !== e.pointerId) return
    id.current = null
    input.joy.x = input.joy.y = 0
    if (knob.current) knob.current.style.transform = ''
  }
  return (
    <div
      ref={base}
      className="joy"
      onPointerDown={(e) => { id.current = e.pointerId; e.currentTarget.setPointerCapture(e.pointerId); move(e) }}
      onPointerMove={move}
      onPointerUp={end}
      onPointerCancel={end}
    >
      <div ref={knob} className="joy-knob" />
    </div>
  )
}

/** Full-screen layer: drag to look (touch, or mouse when pointer lock is unavailable). */
function LookSurface() {
  const last = useRef<{ id: number; x: number; y: number } | null>(null)
  return (
    <div
      className="look"
      onPointerDown={(e) => {
        // try pointer lock; dragging keeps working where the browser refuses it
        if (e.pointerType === 'mouse' && !document.pointerLockElement) lock()
        last.current = { id: e.pointerId, x: e.clientX, y: e.clientY }
        e.currentTarget.setPointerCapture(e.pointerId)
      }}
      onPointerMove={(e) => {
        const l = last.current
        if (!l || l.id !== e.pointerId) return
        const k = e.pointerType === 'touch' ? 1.6 : 1
        input.look.dx += (e.clientX - l.x) * k
        input.look.dy += (e.clientY - l.y) * k
        l.x = e.clientX
        l.y = e.clientY
      }}
      onPointerUp={() => { last.current = null }}
      onPointerCancel={() => { last.current = null }}
    />
  )
}

export function WalkUI({ exit }: { exit: () => void }) {
  const { active, room } = useWalk()
  const touch = isTouch()
  const showCard = !active && !touch

  useEffect(() => {
    if (touch) walkStore.set({ active: true })
  }, [touch])

  return (
    <div className="walk">
      <LookSurface />
      <div className="crosshair" />
      <div className="walk-room"><span className="dot" />{room}</div>
      {!touch && active && (
        <div className="walk-keys">
          <span><kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> chůze</span>
          <span><kbd>Shift</kbd> běh</span>
          <span><kbd>Esc</kbd> pauza</span>
        </div>
      )}
      {touch && <Joystick />}
      <button className="walk-exit" onClick={exit}>Zpět na stavbu <i>✕</i></button>
      {showCard && (
        <div className="walk-card">
          <p className="kicker"><span className="dot" />Prohlídka · Blatouchová 1111</p>
          <h2>Vítejte doma.</h2>
          <p className="lede">Stojíte před hlavními dveřmi. Projděte si přízemí, vyjděte po schodech do podkroví, na balkon nebo na zahradu.</p>
          <ul className="walk-legend">
            <li><kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd><span>nebo šipky — chůze</span></li>
            <li><kbd>Myš</kbd><span>rozhlížení</span></li>
            <li><kbd>Shift</kbd><span>běh</span></li>
            <li><kbd>Esc</kbd><span>pauza</span></li>
          </ul>
          <div className="walk-actions">
            <button className="again primary" onClick={lock}><span>Začít prohlídku</span><i>→</i></button>
            <button className="again" onClick={exit}><span>Zpět na stavbu</span></button>
          </div>
        </div>
      )}
    </div>
  )
}

export function useWalkMode(onEnter: () => void, onExit: () => void) {
  const fade = useFade()
  const enter = () => fade.run(() => { walkStore.set({ walk: true, active: false, room: '' }); onEnter() })
  const exit = () => fade.run(() => {
    if (document.pointerLockElement) document.exitPointerLock()
    walkStore.set({ walk: false, active: false })
    onExit()
  })
  return { enter, exit, fading: fade.on }
}

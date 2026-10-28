import { Html } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import * as THREE from 'three'
import plan from '../data/pudorys.json'
import { progress } from '../store'
import { range01 } from '../timeline'
import { walkStore } from '../walk/store'

// Blueprint of pudorys.json drawn onto the plot. Plan units are cm,
// three.js: x = plan.x / 100, z = plan.y / 100.

type P = { x: number; y: number }
const UF_DX = 1768
const CYAN = new THREE.Color('#7fd6ff')

interface Floor {
  walls: THREE.Mesh[]
  lines: THREE.LineSegments
  group: THREE.Group
}

function nodeOf(id: string, upper: boolean): P {
  const n = (plan.nodes as Record<string, P>)[id]
  if (!upper) return n
  return { x: n.x - UF_DX, y: Math.abs(n.y + 408) < 1 ? -490 : n.y }
}

function buildFloor(upper: boolean, y: number): Floor {
  const group = new THREE.Group()
  group.position.y = y
  const walls: THREE.Mesh[] = []
  const linePts: number[] = []
  const entries = Object.entries(plan.walls).filter(([, w]) => {
    const isUpper = (plan.nodes as Record<string, P>)[w.a].x >= 1000
    return isUpper === upper
  })
  const quad = (pts: THREE.Vector2[]) => {
    for (let i = 0; i < pts.length; i++) {
      const a = pts[i]
      const b = pts[(i + 1) % pts.length]
      linePts.push(a.x, 0.004, a.y, b.x, 0.004, b.y)
    }
  }
  for (const [id, w] of entries) {
    const a = nodeOf(w.a, upper)
    const b = nodeOf(w.b, upper)
    const dx = b.x - a.x
    const dy = b.y - a.y
    const L = Math.hypot(dx, dy)
    const ux = dx / L
    const uy = dy / L
    const ext = w.type === 'exterior' ? w.thickness / 2 : 0
    const h = w.thickness / 2
    const c = (s: number, n: number) =>
      new THREE.Vector2((a.x + ux * s - uy * n) / 100, (a.y + uy * s + ux * n) / 100)
    const pts = [c(-ext, -h), c(L + ext, -h), c(L + ext, h), c(-ext, h)]
    quad(pts)
    const shape = new THREE.Shape(pts)
    const geo = new THREE.ShapeGeometry(shape)
    geo.rotateX(Math.PI / 2)
    const mat = new THREE.MeshBasicMaterial({
      color: CYAN.clone().multiplyScalar(w.type === 'exterior' ? 1.6 : 1.1), transparent: true, opacity: 0,
      toneMapped: false, depthWrite: false, side: THREE.DoubleSide,
    })
    const mesh = new THREE.Mesh(geo, mat)
    mesh.name = id
    mesh.renderOrder = 2
    walls.push(mesh)
    group.add(mesh)
  }
  // door swings
  for (const o of Object.values(plan.openings)) {
    const w = (plan.walls as Record<string, { a: string; b: string; thickness: number }>)[o.wall]
    if (!entries.find(([id]) => id === o.wall)) continue
    const a = nodeOf(w.a, upper)
    const b = nodeOf(w.b, upper)
    const L = Math.hypot(b.x - a.x, b.y - a.y)
    const ux = (b.x - a.x) / L
    const uy = (b.y - a.y) / L
    const side = o.side * (o.flip ? -1 : 1)
    const s0 = o.t - o.width / 2
    const hx = a.x + ux * s0
    const hy = a.y + uy * s0
    const r = o.width
    let prev: [number, number] | null = null
    for (let k = 0; k <= 12; k++) {
      const ang = (k / 12) * (Math.PI / 2)
      const px = hx + (ux * Math.cos(ang) - uy * side * Math.sin(ang)) * r
      const py = hy + (uy * Math.cos(ang) + ux * side * Math.sin(ang)) * r
      if (prev) linePts.push(prev[0] / 100, 0.006, prev[1] / 100, px / 100, 0.006, py / 100)
      prev = [px, py]
    }
    linePts.push(hx / 100, 0.006, hy / 100, prev![0] / 100, 0.006, prev![1] / 100)
  }
  const lg = new THREE.BufferGeometry()
  lg.setAttribute('position', new THREE.Float32BufferAttribute(linePts, 3))
  const lines = new THREE.LineSegments(
    lg,
    new THREE.LineBasicMaterial({ color: CYAN.clone().multiplyScalar(2.2), transparent: true, opacity: 0, toneMapped: false, depthWrite: false }),
  )
  lines.renderOrder = 3
  group.add(lines)
  return { walls, lines, group }
}

function plotOutline() {
  const pts = [[-13, -17], [15, -17], [15, 16], [-13, 16]]
  const arr: number[] = []
  for (let i = 0; i < 4; i++) {
    const a = pts[i]
    const b = pts[(i + 1) % 4]
    arr.push(a[0], 0, a[1], b[0], 0, b[1])
  }
  const g = new THREE.BufferGeometry()
  g.setAttribute('position', new THREE.Float32BufferAttribute(arr, 3))
  const l = new THREE.LineSegments(g, new THREE.LineDashedMaterial({
    color: '#e98a5d', dashSize: 0.6, gapSize: 0.35, transparent: true, opacity: 0, toneMapped: false,
  }))
  l.computeLineDistances()
  l.position.y = -0.13
  return l
}

const GF_LABELS = [
  { name: 'Obývací pokoj · kuchyň', area: '64,98 m²', x: -3.2, z: 1.8 },
  { name: 'Hala', area: '15,72 m²', x: 0.55, z: 0.9 },
  { name: 'Pokoj', area: '11,82 m²', x: 3.0, z: -3.3 },
  { name: 'Koupelna', area: '6,54 m²', x: 5.9, z: -2.6 },
  { name: 'Garáž', area: '3,05 × 5,50 m', x: 5.1, z: 2.0 },
]
const UF_LABELS = [
  { name: 'Pokoj', area: '17,94 m²', x: -2.8, z: 2.7 },
  { name: 'Pokoj', area: '18,09 m²', x: -2.8, z: -2.2 },
  { name: 'Galerie', area: '36,07 m²', x: 0.3, z: 2.5 },
  { name: 'Pracovna', area: '17,83 m²', x: 5.0, z: 2.0 },
  { name: 'Koupelna', area: '', x: 4.8, z: -3.4 },
]

function Labels({ items, y, refEl }: { items: typeof GF_LABELS; y: number; refEl: React.RefObject<HTMLDivElement[]> }) {
  return (
    <>
      {items.map((l, i) => (
        <Html key={i} position={[l.x, y, l.z]} center zIndexRange={[5, 0]} style={{ pointerEvents: 'none' }}>
          <div className="room-label" ref={(el) => { if (el && refEl.current) refEl.current[i] = el }}>
            <span>{l.name}</span>
            {l.area && <b>{l.area}</b>}
          </div>
        </Html>
      ))}
    </>
  )
}

export function PlanOverlay() {
  const gf = useMemo(() => buildFloor(false, 0.035), [])
  const uf = useMemo(() => buildFloor(true, 3.16), [])
  const plot = useMemo(() => plotOutline(), [])
  const gfLabels = useRef<HTMLDivElement[]>([])
  const ufLabels = useRef<HTMLDivElement[]>([])
  const born = useRef<number | null>(null)

  useFrame(({ clock }) => {
    if (born.current === null) born.current = clock.elapsedTime
    const age = clock.elapsedTime - born.current
    const walk = walkStore.get().walk
    const p = walk ? 1 : progress.current

    const gfA = 1 - range01(p, 0.13, 0.24)
    gf.group.visible = gfA > 0.001
    gf.walls.forEach((m, i) => {
      const draw = Math.min(1, Math.max(0, (age - 0.4 - i * 0.045) / 0.5))
      ;(m.material as THREE.MeshBasicMaterial).opacity = 0.55 * draw * gfA
    })
    ;(gf.lines.material as THREE.LineBasicMaterial).opacity = Math.min(1, Math.max(0, (age - 1.4) / 1.2)) * gfA

    const ufA = range01(p, 0.555, 0.585) * (1 - range01(p, 0.62, 0.67))
    uf.group.visible = ufA > 0.001
    uf.walls.forEach((m, i) => {
      const draw = range01(p, 0.555 + i * 0.0012, 0.575 + i * 0.0012)
      ;(m.material as THREE.MeshBasicMaterial).opacity = 0.55 * draw * ufA
    })
    ;(uf.lines.material as THREE.LineBasicMaterial).opacity = ufA

    ;(plot.material as THREE.LineDashedMaterial).opacity = Math.min(1, age / 2) * (1 - range01(p, 0.04, 0.12)) * 0.9

    plot.visible = !walk
    const gfL = Math.min(1, Math.max(0, (age - 1.6) / 1)) * (1 - range01(p, 0.05, 0.12))
    gfLabels.current.forEach((el) => { if (el) el.style.opacity = String(gfL) })
    const ufL = range01(p, 0.565, 0.59) * (1 - range01(p, 0.6, 0.63))
    ufLabels.current.forEach((el) => { if (el) el.style.opacity = String(ufL) })
  })

  return (
    <group>
      <primitive object={gf.group} />
      <primitive object={uf.group} />
      <primitive object={plot} />
      <Labels items={GF_LABELS} y={0.1} refEl={gfLabels} />
      <Labels items={UF_LABELS} y={3.25} refEl={ufLabels} />
    </group>
  )
}

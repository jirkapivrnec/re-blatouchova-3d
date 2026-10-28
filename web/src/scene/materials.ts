import * as THREE from 'three'

// Procedural grayscale detail maps. UVs from Blender are world-space metres,
// so a texture that spans `metres` is repeated 1/metres times per UV unit.

type Painter = (ctx: CanvasRenderingContext2D, s: number, rnd: () => number) => void

function rng(seed: number) {
  let a = seed
  return () => {
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

function canvasTex(paint: Painter, metres: number, size = 512, seed = 7) {
  const c = document.createElement('canvas')
  c.width = c.height = size
  const ctx = c.getContext('2d')!
  paint(ctx, size, rng(seed))
  const tex = new THREE.CanvasTexture(c)
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping
  tex.repeat.set(1 / metres, 1 / metres)
  tex.colorSpace = THREE.SRGBColorSpace
  tex.anisotropy = 8
  return tex
}

const grey = (v: number) => {
  const c = Math.round(Math.max(0, Math.min(1, v)) * 255)
  return `rgb(${c},${c},${c})`
}

function noise(ctx: CanvasRenderingContext2D, s: number, rnd: () => number, n: number, lo: number, hi: number, r = 1.5) {
  for (let i = 0; i < n; i++) {
    ctx.fillStyle = grey(lo + rnd() * (hi - lo))
    ctx.globalAlpha = 0.35
    ctx.fillRect(rnd() * s, rnd() * s, r, r)
  }
  ctx.globalAlpha = 1
}

const roofTiles: Painter = (ctx, s, rnd) => {
  const cols = 4 // 4 tiles per metre
  const w = s / cols
  for (let i = 0; i < cols; i++) {
    const g = ctx.createLinearGradient(i * w, 0, (i + 1) * w, 0)
    const k = 0.9 + rnd() * 0.1
    g.addColorStop(0, grey(0.62 * k))
    g.addColorStop(0.35, grey(1.0 * k))
    g.addColorStop(0.7, grey(0.92 * k))
    g.addColorStop(1, grey(0.55 * k))
    ctx.fillStyle = g
    ctx.fillRect(i * w, 0, w, s)
  }
  noise(ctx, s, rnd, 9000, 0.4, 1, 2)
}

const bricks: Painter = (ctx, s, rnd) => {
  ctx.fillStyle = grey(0.72)
  ctx.fillRect(0, 0, s, s)
  const rows = 14
  const h = s / rows
  const bw = s / 4
  for (let r = 0; r < rows; r++) {
    const off = (r % 2) * bw * 0.5
    for (let c = -1; c < 5; c++) {
      ctx.fillStyle = grey(0.82 + rnd() * 0.18)
      ctx.fillRect(c * bw + off + 2, r * h + 2, bw - 4, h - 4)
    }
  }
  noise(ctx, s, rnd, 6000, 0.5, 1)
}

const tiles = (n: number, joint: number, lo = 0.86): Painter => (ctx, s, rnd) => {
  ctx.fillStyle = grey(0.6)
  ctx.fillRect(0, 0, s, s)
  const w = s / n
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++) {
      ctx.fillStyle = grey(lo + rnd() * (1 - lo))
      ctx.fillRect(i * w + joint, j * w + joint, w - 2 * joint, w - 2 * joint)
    }
  noise(ctx, s, rnd, 5000, 0.6, 1)
}

const pavers: Painter = (ctx, s, rnd) => {
  ctx.fillStyle = grey(0.55)
  ctx.fillRect(0, 0, s, s)
  const rows = 10
  const h = s / rows
  for (let r = 0; r < rows; r++) {
    let x = -rnd() * h
    while (x < s) {
      const w = h * (r % 2 ? 2 : 1)
      ctx.fillStyle = grey(0.75 + rnd() * 0.25)
      ctx.fillRect(x + 2, r * h + 2, w - 4, h - 4)
      x += w
    }
  }
}

const planks: Painter = (ctx, s, rnd) => {
  const rows = 5 // 20 cm wide planks
  const h = s / rows
  for (let r = 0; r < rows; r++) {
    let x = -rnd() * s
    while (x < s) {
      const w = s * (0.6 + rnd() * 0.6)
      ctx.fillStyle = grey(0.8 + rnd() * 0.2)
      ctx.fillRect(x, r * h, w - 2, h - 2)
      for (let k = 0; k < 14; k++) {
        ctx.strokeStyle = grey(0.7 + rnd() * 0.2)
        ctx.globalAlpha = 0.25
        const yy = r * h + rnd() * h
        ctx.beginPath()
        ctx.moveTo(x, yy)
        ctx.lineTo(x + w, yy + (rnd() - 0.5) * 6)
        ctx.stroke()
      }
      ctx.globalAlpha = 1
      x += w
    }
  }
}

const grass: Painter = (ctx, s, rnd) => {
  ctx.fillStyle = grey(0.85)
  ctx.fillRect(0, 0, s, s)
  for (let i = 0; i < 26000; i++) {
    ctx.fillStyle = grey(0.55 + rnd() * 0.45)
    ctx.globalAlpha = 0.5
    ctx.fillRect(rnd() * s, rnd() * s, 1.5, 3 + rnd() * 3)
  }
  ctx.globalAlpha = 1
}

const plaster: Painter = (ctx, s, rnd) => {
  ctx.fillStyle = grey(0.95)
  ctx.fillRect(0, 0, s, s)
  noise(ctx, s, rnd, 30000, 0.75, 1, 1.2)
}

const carpet: Painter = (ctx, s, rnd) => {
  ctx.fillStyle = grey(0.9)
  ctx.fillRect(0, 0, s, s)
  noise(ctx, s, rnd, 40000, 0.7, 1, 1)
}

export interface MaterialSet {
  byName: Map<string, THREE.Material>
  glassGlow: THREE.MeshPhysicalMaterial
  beam: THREE.MeshBasicMaterial
}

export function createMaterials(originals: THREE.Material[]): MaterialSet {
  const maps: Record<string, THREE.Texture> = {
    RoofTile: canvasTex(roofTiles, 1, 512, 3),
    Brick: canvasTex(bricks, 1, 512, 5),
    Lawn: canvasTex(grass, 2.5, 512, 9),
    Pavers: canvasTex(pavers, 1.6, 512, 11),
    Terracotta: canvasTex(tiles(3, 2, 0.8), 1, 256, 13),
    FloorTile: canvasTex(tiles(2, 1.5), 1.2, 256, 17),
    DarkTile: canvasTex(tiles(2, 1.5, 0.8), 1.2, 256, 19),
    StoneTile: canvasTex(tiles(5, 2, 0.75), 1, 256, 23),
    Oak: canvasTex(planks, 1, 512, 29),
    Facade: canvasTex(plaster, 1.5, 256, 31),
    Carpet: canvasTex(carpet, 1, 256, 37),
    CarpetGreen: canvasTex(carpet, 1, 256, 41),
  }

  const byName = new Map<string, THREE.Material>()
  for (const m of originals) {
    if (byName.has(m.name)) continue
    const std = m as THREE.MeshStandardMaterial
    if (m.name === 'Glass') {
      byName.set(m.name, new THREE.MeshPhysicalMaterial({
        name: 'Glass', color: '#9fc3d4', roughness: 0.04, metalness: 0.1, transparent: true,
        opacity: 0.32, envMapIntensity: 1.6, depthWrite: false, side: THREE.DoubleSide,
      }))
      continue
    }
    if (m.name === 'Water') {
      byName.set(m.name, new THREE.MeshPhysicalMaterial({
        name: 'Water', color: '#3f9fc8', roughness: 0.05, metalness: 0, transparent: true,
        opacity: 0.82, envMapIntensity: 1.4,
      }))
      continue
    }
    const map = maps[m.name]
    if (map && std.isMeshStandardMaterial) {
      std.map = map
      std.needsUpdate = true
    }
    if (std.isMeshStandardMaterial) std.envMapIntensity = 0.55
    byName.set(m.name, m)
  }

  const glassGlow = new THREE.MeshPhysicalMaterial({
    name: 'GlassGlow', color: '#9fc3d4', roughness: 0.04, metalness: 0.1, transparent: true,
    opacity: 0.35, envMapIntensity: 1.6, depthWrite: false, side: THREE.DoubleSide,
    emissive: new THREE.Color('#ffb062'), emissiveIntensity: 0,
  })
  const beam = new THREE.MeshBasicMaterial({
    color: new THREE.Color('#7fd6ff').multiplyScalar(3), toneMapped: false, transparent: true, opacity: 0.9,
  })
  return { byName, glassGlow, beam }
}

import { useGLTF } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import { useMemo } from 'react'
import * as THREE from 'three'
import { STAGE_WINDOWS, clamp01, range01 } from '../timeline'
import { progress, stats } from '../store'
import { createMaterials } from './materials'
import { easeOutBack, easeOutBounce, easeOutCubic } from './easing'
import { colliders, walkStore } from '../walk/store'


export const MODEL_URL = `${import.meta.env.BASE_URL}models/house.glb`

type Anim = 'rise' | 'drop' | 'pop' | 'tile' | 'fade' | 'grow' | 'none'

interface Part {
  obj: THREE.Object3D
  anim: Anim
  start: number
  len: number
  pos: THREE.Vector3
  rot: THREE.Euler
  h: number
  dropH: number
  beam: THREE.Mesh | null
  last: number
}

const BEAM_STAGES = new Set(['foundation', 'gf_walls_ext', 'gf_walls_int', 'uf_walls_ext', 'uf_walls_int'])
const NO_CAST = new Set(['Glass', 'Water', 'Lawn', 'Asphalt'])
// stages you can walk through / over (rails inside them still block)
const PASSABLE = new Set(['site', 'foundation', 'gf_floor', 'uf_floor', 'gf_openings', 'uf_openings', 'gf_slab', 'gf_stairs'])
const NOT_GROUND = new Set(['gf_openings', 'uf_openings', 'roof_frame', 'roof_tiles', 'roof_details'])
const LEAF_MATS = new Set(['Oak', 'Glass', 'Metal'])

function prepare(root: THREE.Object3D) {
  root.updateMatrixWorld(true)
  const nodes = [...root.children]

  const originals: THREE.Material[] = []
  root.traverse((o) => {
    const m = (o as THREE.Mesh).material
    if (m) originals.push(...(Array.isArray(m) ? m : [m]))
  })
  const mats = createMaterials(originals)

  const doorLeaves: THREE.Mesh[] = []
  colliders.blockers = []
  colliders.ground = []
  for (const node of nodes) {
    const glow = !!node.userData.glow
    const stage = String(node.userData.stage ?? 'site')
    const solid = !PASSABLE.has(stage) || node.name.includes('Rail')
    const ground = !NOT_GROUND.has(stage)
    const door = node.name.includes('_Door_') && !node.name.includes('w48')
    node.traverse((o) => {
      const mesh = o as THREE.Mesh
      if (!mesh.isMesh) return
      const name = (mesh.material as THREE.Material).name
      mesh.material = glow && name === 'Glass' ? mats.glassGlow : mats.byName.get(name) ?? mesh.material
      mesh.castShadow = !NO_CAST.has(name)
      mesh.receiveShadow = name !== 'Glass'
      if (door && LEAF_MATS.has(name)) doorLeaves.push(mesh)
      if (solid) colliders.blockers.push(mesh)
      if (ground) colliders.ground.push(mesh)
    })
  }

  const byStage = new Map<string, THREE.Object3D[]>()
  for (const n of nodes) {
    const st = String(n.userData.stage ?? 'site')
    if (!byStage.has(st)) byStage.set(st, [])
    byStage.get(st)!.push(n)
  }

  const beamGeo = new THREE.BoxGeometry(1, 1, 1)
  const parts: Part[] = []
  for (const [stage, list] of byStage) {
    const win = STAGE_WINDOWS[stage]
    list.sort((a, b) => (a.userData.order ?? 0) - (b.userData.order ?? 0))
    const N = list.length
    const lf = Math.min(0.45, Math.max(0.07, 4 / N))
    list.forEach((obj, i) => {
      const box = new THREE.Box3().setFromObject(obj)
      const size = box.getSize(new THREE.Vector3())
      let start = -1
      let len = 1
      if (win) {
        const [s, e] = win
        start = s + (e - s) * (1 - lf) * (N > 1 ? i / (N - 1) : 0)
        len = (e - s) * lf
      }
      let beam: THREE.Mesh | null = null
      const anim = (obj.userData.anim ?? 'none') as Anim
      if (BEAM_STAGES.has(stage) && anim === 'rise') {
        beam = new THREE.Mesh(beamGeo, mats.beam)
        beam.scale.set(size.x + 0.08, 0.04, size.z + 0.08)
        beam.position.set((box.min.x + box.max.x) / 2, box.min.y, (box.min.z + box.max.z) / 2)
        beam.visible = false
        beam.userData.baseY = box.min.y
        root.add(beam)
      }
      parts.push({
        obj, anim: win ? anim : 'none', start, len,
        pos: obj.position.clone(), rot: obj.rotation.clone(), h: size.y,
        dropH: stage === 'gf_slab' || stage === 'roof_frame' ? 5 : stage.endsWith('stairs') ? 2.2 : 3.2,
        beam, last: -1,
      })
    })
  }
  return { parts, mats, doorLeaves }
}

function apply(pt: Part, t: number) {
  const o = pt.obj
  o.visible = t > 0.0005
  o.position.copy(pt.pos)
  o.rotation.copy(pt.rot)
  o.scale.set(1, 1, 1)
  if (t >= 1 || !o.visible) {
    if (pt.beam) pt.beam.visible = false
    return
  }
  switch (pt.anim) {
    case 'rise': {
      const e = easeOutCubic(t)
      o.scale.y = Math.max(0.001, e)
      if (pt.beam) {
        pt.beam.visible = true
        pt.beam.position.y = pt.beam.userData.baseY + pt.h * e
        pt.beam.scale.y = 0.02 + 0.05 * (1 - t)
      }
      break
    }
    case 'drop': {
      const e = easeOutBounce(t)
      o.position.y += (1 - e) * pt.dropH
      const s = 0.7 + 0.3 * Math.min(1, t * 3)
      o.scale.set(s, s, s)
      break
    }
    case 'pop': {
      const s = Math.max(0.001, easeOutBack(t, 2.2))
      o.scale.set(s, s, s)
      break
    }
    case 'tile': {
      const e = easeOutCubic(t)
      o.position.y += (1 - e) * 2.4
      o.rotation.x += (1 - e) * 0.35
      break
    }
    case 'fade': {
      const e = easeOutCubic(t)
      o.scale.set(Math.max(0.001, e), 1, Math.max(0.001, e))
      break
    }
    case 'grow': {
      o.scale.set(Math.max(0.001, easeOutCubic(t)), Math.max(0.001, easeOutBack(t, 1.4)), Math.max(0.001, easeOutCubic(t)))
      break
    }
  }
}

export function House() {
  const gltf = useGLTF(MODEL_URL)
  const { parts, mats, doorLeaves } = useMemo(() => prepare(gltf.scene), [gltf])

  useFrame(() => {
    const walk = walkStore.get().walk
    const p = walk ? 1 : progress.current
    // doorways stay open while walking through the house
    for (const m of doorLeaves) m.visible = !walk
    let built = 0
    let total = 0
    for (const pt of parts) {
      if (pt.start < 0) continue
      total++
      const t = clamp01((p - pt.start) / pt.len)
      if (t >= 1) built++
      if (t === pt.last) continue
      pt.last = t
      apply(pt, t)
    }
    stats.built = built
    stats.total = total
    const night = walk ? 0 : range01(p, 0.955, 0.995)
    mats.glassGlow.emissiveIntensity = 3.2 * night
    mats.glassGlow.opacity = 0.32 + 0.6 * night
  })

  return <primitive object={gltf.scene} />
}

useGLTF.preload(MODEL_URL)

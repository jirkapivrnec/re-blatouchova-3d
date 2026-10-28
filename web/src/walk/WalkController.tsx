import { useFrame, useThree } from '@react-three/fiber'
import { useEffect, useMemo } from 'react'
import * as THREE from 'three'
import { colliders, input, walkStore } from './store'
import { roomAt } from './rooms'

interface Collider {
  mesh: THREE.Mesh
  box: THREE.Box3
}

// Spawn on the porch, facing the front door (plan x=121, door wall at y=433).
const SPAWN = new THREE.Vector3(1.21, 0, 6.4)
const EYE = 1.65
const RADIUS = 0.3
const WALK = 2.0
const RUN = 4.2
const RAY_HEIGHTS = [0.35, 1.15, 1.75]
const DIRS = Array.from({ length: 12 }, (_, i) => {
  const a = (i / 12) * Math.PI * 2
  return new THREE.Vector3(Math.cos(a), 0, Math.sin(a))
})
// keep inside the plot (hedges have gaps between the trees)
const BOUNDS = { x0: -12.3, x1: 14.3, z0: -16.3, z1: 15.6 }

export function WalkController() {
  const { camera, size } = useThree()
  const s = useMemo(() => ({
    feet: SPAWN.clone(), eye: EYE, yaw: 0, pitch: -0.04, vy: 0, grounded: true, bob: 0,
    ray: new THREE.Raycaster(),
    origin: new THREE.Vector3(), move: new THREE.Vector3(), down: new THREE.Vector3(0, -1, 0),
    room: '', frames: 0,
    blockers: [] as Collider[], ground: [] as Collider[],
    nearBlock: [] as THREE.Mesh[], nearGround: [] as THREE.Mesh[],
  }), [])

  useEffect(() => {
    const cam = camera as THREE.PerspectiveCamera
    cam.clearViewOffset()
    cam.near = 0.05
    cam.updateProjectionMatrix()
    s.feet.copy(SPAWN)
    s.yaw = 0
    s.pitch = -0.04
    s.vy = 0
    // dev-only test hook: dispatchEvent(new CustomEvent('walkdebug', { detail: '[x,y,z,yaw]' }))
    const onDebug = (e: Event) => {
      const [x, y, z, yaw] = JSON.parse((e as CustomEvent<string>).detail)
      s.feet.set(x, y, z)
      s.yaw = yaw
    }
    if (import.meta.env.DEV) window.addEventListener('walkdebug', onDebug)
    s.frames = 0

    const onMouse = (e: MouseEvent) => {
      if (!document.pointerLockElement) return
      input.look.dx += e.movementX
      input.look.dy += e.movementY
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.type === 'keydown') input.keys.add(e.code)
      else input.keys.delete(e.code)
      if (e.code.startsWith('Arrow') || e.code === 'Space') e.preventDefault()
    }
    const onLock = () => walkStore.set({ active: !!document.pointerLockElement })
    document.addEventListener('mousemove', onMouse)
    window.addEventListener('keydown', onKey)
    window.addEventListener('keyup', onKey)
    document.addEventListener('pointerlockchange', onLock)
    return () => {
      document.removeEventListener('mousemove', onMouse)
      window.removeEventListener('keydown', onKey)
      window.removeEventListener('keyup', onKey)
      document.removeEventListener('pointerlockchange', onLock)
      window.removeEventListener('walkdebug', onDebug)
      input.keys.clear()
      if (document.pointerLockElement) document.exitPointerLock()
      cam.fov = 35
      cam.near = 0.3
      cam.updateProjectionMatrix()
    }
  }, [camera, s])

  // keep roughly the same horizontal field of view on portrait screens
  useEffect(() => {
    const cam = camera as THREE.PerspectiveCamera
    const aspect = size.width / size.height
    cam.fov = aspect >= 1 ? 72 : Math.min(98, THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(34)) / aspect)))
    cam.updateProjectionMatrix()
  }, [camera, size])

  const castH = (dir: THREE.Vector3, h: number, far: number) => {
    s.origin.set(s.feet.x, s.feet.y + h, s.feet.z)
    s.ray.set(s.origin, dir)
    s.ray.far = far
    const hit = s.ray.intersectObjects(s.nearBlock, false)[0]
    return hit ? hit.distance : Infinity
  }

  const pushOut = () => {
    for (const d of DIRS) {
      let pen = 0
      for (const h of RAY_HEIGHTS) {
        const dist = castH(d, h, RADIUS)
        if (dist < RADIUS) pen = Math.max(pen, RADIUS - dist)
      }
      if (pen > 0) s.feet.addScaledVector(d, -pen)
    }
  }

  const groundAt = () => {
    s.origin.set(s.feet.x, s.feet.y + 0.5, s.feet.z)
    s.ray.set(s.origin, s.down)
    s.ray.far = 30
    const hit = s.ray.intersectObjects(s.nearGround, false)[0]
    return hit ? hit.point.y : -0.15
  }

  // world boxes of every collider, taken once the house stands complete
  const snapshot = () => {
    const make = (list: THREE.Mesh[]) => list.map((mesh) => {
      mesh.updateWorldMatrix(true, false)
      return { mesh, box: new THREE.Box3().setFromObject(mesh) }
    })
    s.blockers = make(colliders.blockers)
    s.ground = make(colliders.ground)
  }

  // only raycast against what is around the player
  const gather = () => {
    const { x, y, z } = s.feet
    const m = RADIUS + 0.45
    s.nearBlock.length = 0
    for (const c of s.blockers) {
      const b = c.box
      if (b.max.x > x - m && b.min.x < x + m && b.max.z > z - m && b.min.z < z + m && b.max.y > y && b.min.y < y + 2.2)
        s.nearBlock.push(c.mesh)
    }
    s.nearGround.length = 0
    for (const c of s.ground) {
      const b = c.box
      if (b.max.x >= x && b.min.x <= x && b.max.z >= z && b.min.z <= z && b.min.y < y + 0.5) s.nearGround.push(c.mesh)
    }
  }

  useFrame((_, rawDt) => {
    const dt = Math.min(rawDt, 0.05)
    const st = walkStore.get()
    // House applies the finished state one frame after walk mode starts
    if (s.frames++ === 2) snapshot()
    if (s.frames < 3) return

    // look
    const sens = 0.0022
    s.yaw -= input.look.dx * sens
    s.pitch -= input.look.dy * sens
    s.pitch = Math.max(-1.45, Math.min(1.45, s.pitch))
    input.look.dx = 0
    input.look.dy = 0

    // move intent
    const k = input.keys
    let f = (k.has('KeyW') || k.has('ArrowUp') ? 1 : 0) - (k.has('KeyS') || k.has('ArrowDown') ? 1 : 0)
    let r = (k.has('KeyD') || k.has('ArrowRight') ? 1 : 0) - (k.has('KeyA') || k.has('ArrowLeft') ? 1 : 0)
    f += -input.joy.y
    r += input.joy.x
    const run = k.has('ShiftLeft') || k.has('ShiftRight') || Math.hypot(input.joy.x, input.joy.y) > 0.92
    const sy = Math.sin(s.yaw)
    const cy = Math.cos(s.yaw)
    s.move.set(-sy * f + cy * r, 0, -cy * f - sy * r)
    const len = s.move.length()
    if (len > 1) s.move.divideScalar(len)
    s.move.multiplyScalar((run ? RUN : WALK) * dt * (st.active || input.joy.x || input.joy.y ? 1 : 0))

    // move in small substeps, pushing out of anything solid
    const steps = Math.max(1, Math.ceil(s.move.length() / 0.08))
    for (let i = 0; i < steps; i++) {
      s.feet.x += s.move.x / steps
      s.feet.z += s.move.z / steps
      gather()
      pushOut()
    }
    s.feet.x = Math.max(BOUNDS.x0, Math.min(BOUNDS.x1, s.feet.x))
    s.feet.z = Math.max(BOUNDS.z0, Math.min(BOUNDS.z1, s.feet.z))

    // floor following: step up stairs, snap down small drops, fall otherwise
    gather()
    const g = groundAt()
    if (g >= s.feet.y - 0.32 && s.vy <= 0) {
      s.feet.y = g
      s.vy = 0
    } else {
      s.vy -= 9.81 * dt
      s.feet.y += s.vy * dt
      if (s.feet.y <= g) {
        s.feet.y = g
        s.vy = 0
      }
    }

    // camera
    const moving = len > 0.01
    s.bob += moving ? dt * (run ? 11 : 7.5) : 0
    const bob = moving ? Math.sin(s.bob) * 0.025 : 0
    s.eye += (s.feet.y + EYE - s.eye) * (1 - Math.exp(-dt * 14))
    camera.position.set(s.feet.x, s.eye + bob, s.feet.z)
    camera.rotation.set(s.pitch, s.yaw, 0, 'YXZ')

    if (import.meta.env.DEV) document.body.dataset.walk = `${s.feet.x.toFixed(2)},${s.feet.y.toFixed(2)},${s.feet.z.toFixed(2)}`
    const room = roomAt(s.feet.x, s.feet.z, s.feet.y)
    if (room !== s.room) {
      s.room = room
      walkStore.set({ room })
    }
  })

  return null
}

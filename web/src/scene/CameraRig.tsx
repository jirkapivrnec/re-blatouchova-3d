import { useFrame, useThree } from '@react-three/fiber'
import { useMemo } from 'react'
import * as THREE from 'three'
import { CHAPTERS, range01, smoother } from '../timeline'
import { pointer, progress } from '../store'

// One camera key per chapter, anchored at the chapter's middle. Between keys the
// camera eases (smootherstep) so every chapter "settles" while its parts build.

const KEYS = CHAPTERS.map((c, i) => ({
  p: i === 0 ? 0.02 : i === CHAPTERS.length - 1 ? 0.985 : (c.range[0] + c.range[1]) / 2,
  pos: new THREE.Vector3(...c.cam.pos),
  target: new THREE.Vector3(...c.cam.target),
}))

export function CameraRig() {
  const { camera, size } = useThree()
  const tmp = useMemo(() => ({
    pos: new THREE.Vector3(), target: new THREE.Vector3(), off: new THREE.Vector3(),
    right: new THREE.Vector3(), smoothPos: new THREE.Vector3(...CHAPTERS[0].cam.pos),
    smoothTarget: new THREE.Vector3(...CHAPTERS[0].cam.target), px: 0, py: 0, first: true,
  }), [])

  useFrame(({ clock }, dt) => {
    const k = 1 - Math.exp(-dt * 5)
    progress.current += (progress.target - progress.current) * (1 - Math.exp(-dt * 4.5))
    const p = progress.current

    let i = 0
    while (i < KEYS.length - 2 && p > KEYS[i + 1].p) i++
    const a = KEYS[i]
    const b = KEYS[i + 1]
    const u = smoother(Math.min(1, Math.max(0, (p - a.p) / (b.p - a.p))))
    tmp.pos.lerpVectors(a.pos, b.pos, u)
    tmp.target.lerpVectors(a.target, b.target, u)

    // portrait screens need more distance
    const aspect = size.width / size.height
    const zoom = aspect < 1 ? 1 + (1 - aspect) * 1.5 : 1
    tmp.off.subVectors(tmp.pos, tmp.target).multiplyScalar(zoom)

    // slow orbit once the house is finished
    const fin = range01(p, 0.975, 1)
    const ang = Math.sin(clock.elapsedTime * 0.12) * 0.55 * fin
    tmp.off.applyAxisAngle(THREE.Object3D.DEFAULT_UP, ang)
    tmp.pos.addVectors(tmp.target, tmp.off)

    // pointer parallax
    tmp.px += (pointer.x - tmp.px) * k
    tmp.py += (pointer.y - tmp.py) * k
    tmp.right.crossVectors(tmp.off, THREE.Object3D.DEFAULT_UP).normalize()
    tmp.pos.addScaledVector(tmp.right, -tmp.px * 0.9)
    tmp.pos.y += tmp.py * 0.6

    // (re)mounted, e.g. after leaving walk mode: start on the path instead of gliding to it
    tmp.smoothPos.lerp(tmp.pos, tmp.first ? 1 : k)
    tmp.smoothTarget.lerp(tmp.target, tmp.first ? 1 : k)
    tmp.first = false
    camera.position.copy(tmp.smoothPos)
    camera.lookAt(tmp.smoothTarget)

    // landscape: push the house right of the text column by shifting the frustum
    const cam = camera as THREE.PerspectiveCamera
    const shift = aspect > 1.1 ? Math.min(0.17, (aspect - 1.1) * 0.25) : 0
    // portrait: push it up above the bottom text panel
    if (shift > 0) cam.setViewOffset(size.width, size.height, -size.width * shift, 0, size.width, size.height)
    else if (aspect < 0.9) cam.setViewOffset(size.width, size.height, 0, size.height * 0.17, size.width, size.height)
    else if (cam.view) cam.clearViewOffset()
  })
  return null
}

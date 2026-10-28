import { Environment, Grid, Lightformer } from '@react-three/drei'
import { Canvas, useFrame } from '@react-three/fiber'
import { Bloom, EffectComposer, N8AO, ToneMapping, Vignette } from '@react-three/postprocessing'
import { ToneMappingMode } from 'postprocessing'
import { Suspense, useRef } from 'react'
import * as THREE from 'three'
import { progress } from '../store'
import { range01 } from '../timeline'
import { CameraRig } from './CameraRig'
import { House } from './House'
import { PlanOverlay } from './PlanOverlay'
import { WalkController } from '../walk/WalkController'
import { useWalk, walkStore } from '../walk/store'

const DUSK = new THREE.Color('#0d1013')
const NIGHT = new THREE.Color('#07080b')
// walk-through: overcast daylight like on the reference photos
const SKY = new THREE.Color('#a9b6c2')
const FIELD = new THREE.Color('#4b5741')
const DARK_GROUND = new THREE.Color('#14171a')
const LAMP_NIGHT = new THREE.Color('#ffb067')
const LAMP_DAY = new THREE.Color('#fff0dc')

function Atmosphere() {
  const sun = useRef<THREE.DirectionalLight>(null)
  const hemi = useRef<THREE.HemisphereLight>(null)
  const warm = useRef<THREE.Group>(null)
  const fog = useRef<THREE.Fog>(null)
  const grid = useRef<THREE.Mesh>(null)
  const ground = useRef<THREE.MeshStandardMaterial>(null)
  const bg = useRef<THREE.Color>(DUSK.clone())

  useFrame(({ scene }) => {
    const walk = walkStore.get().walk
    const p = walk ? 1 : progress.current
    const night = walk ? 0 : range01(p, 0.955, 0.995)
    if (sun.current) sun.current.intensity = THREE.MathUtils.lerp(2.6, 0.35, night)
    if (hemi.current) hemi.current.intensity = walk ? 1.05 : THREE.MathUtils.lerp(0.75, 0.18, night)
    // interior lamps: on at night, softly on while walking inside
    warm.current?.children.forEach((l) => {
      const lamp = l as THREE.PointLight
      lamp.intensity = walk ? 2.6 : 9 * night
      lamp.color.copy(walk ? LAMP_DAY : LAMP_NIGHT)
    })
    if (walk) bg.current.copy(SKY)
    else bg.current.copy(DUSK).lerp(NIGHT, night)
    scene.background = bg.current
    if (fog.current) {
      fog.current.color.copy(bg.current)
      fog.current.near = walk ? 25 : 38
      fog.current.far = walk ? 140 : 120
    }
    ground.current?.color.copy(walk ? FIELD : DARK_GROUND)
    if (grid.current) grid.current.visible = !walk
    if (grid.current) {
      const m = grid.current.material as THREE.ShaderMaterial & { uniforms: Record<string, { value: unknown }> }
      const a = 1 - 0.75 * range01(p, 0.05, 0.3)
      if (m.uniforms?.cellColor) (m.uniforms.cellColor.value as THREE.Color).setRGB(0.2 * a, 0.42 * a, 0.52 * a)
      if (m.uniforms?.sectionColor) (m.uniforms.sectionColor.value as THREE.Color).setRGB(0.32 * a, 0.62 * a, 0.78 * a)
    }
  })

  return (
    <>
      <fog ref={fog} attach="fog" args={[DUSK, 38, 120]} />
      <hemisphereLight ref={hemi} args={['#c3d0e0', '#3b2f25', 0.75]} />
      <directionalLight
        ref={sun}
        position={[-16, 24, 18]}
        intensity={2.6}
        color="#ffe0bd"
        castShadow
        shadow-mapSize={[4096, 4096]}
        shadow-bias={-0.0004}
        shadow-normalBias={0.03}
        shadow-camera-left={-20}
        shadow-camera-right={20}
        shadow-camera-top={20}
        shadow-camera-bottom={-20}
        shadow-camera-near={1}
        shadow-camera-far={80}
      />
      <group ref={warm}>
        {[[-3, 1.6, 2], [-1.5, 1.6, -3], [3, 1.6, 0], [0.6, 4.6, 2], [-3, 4.6, 2], [5, 4.6, 2], [-3, 4.6, -2]].map((p, i) => (
          <pointLight key={i} position={p as [number, number, number]} color="#ffb067" intensity={0} distance={7} decay={1.6} />
        ))}
      </group>
      <Environment resolution={128} frames={1}>
        <Lightformer form="rect" intensity={1.4} color="#cfd9e6" position={[0, 12, 0]} rotation-x={Math.PI / 2} scale={[30, 30, 1]} />
        <Lightformer form="rect" intensity={1.6} color="#ffd6ad" position={[-14, 6, 12]} scale={[14, 6, 1]} target={[0, 0, 0]} />
        <Lightformer form="rect" intensity={0.5} color="#7fa3c7" position={[14, 4, -10]} scale={[14, 6, 1]} target={[0, 0, 0]} />
      </Environment>
      <mesh rotation-x={-Math.PI / 2} position={[1, -0.36, 0]} receiveShadow>
        <circleGeometry args={[160, 64]} />
        <meshStandardMaterial ref={ground} color="#14171a" roughness={1} />
      </mesh>
      <Grid
        ref={grid}
        position={[1, -0.345, 0]}
        args={[200, 200]}
        cellSize={1}
        cellThickness={0.6}
        sectionSize={5}
        sectionThickness={1}
        cellColor="#2a6a85"
        sectionColor="#4f9fc7"
        fadeDistance={70}
        fadeStrength={1.6}
        infiniteGrid
      />
    </>
  )
}

export function Experience() {
  const { walk } = useWalk()
  return (
    <Canvas
      className="stage"
      shadows
      dpr={[1, 1.75]}
      camera={{ fov: 35, near: 0.3, far: 400, position: [6, 30, 22] }}
      gl={{ antialias: false, powerPreference: 'high-performance' }}
    >
      <Atmosphere />
      <Suspense fallback={null}>
        <House />
        <PlanOverlay />
      </Suspense>
      {walk ? <WalkController /> : <CameraRig />}
      <EffectComposer multisampling={4}>
        <N8AO aoRadius={1.1} intensity={2.2} distanceFalloff={0.6} halfRes />
        <Bloom luminanceThreshold={1} luminanceSmoothing={0.2} intensity={0.9} mipmapBlur />
        <Vignette offset={0.25} darkness={0.75} />
        <ToneMapping mode={ToneMappingMode.AGX} />
      </EffectComposer>
    </Canvas>
  )
}

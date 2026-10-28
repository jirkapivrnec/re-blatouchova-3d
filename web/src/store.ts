// Tiny mutable stores shared between the scroll driver, the 3D scene and the HUD.
// Deliberately outside React state: they change every frame.

export const progress = { target: 0, current: 0 }
export const stats = { built: 0, total: 0 }
export const scrollApi = {
  toProgress: (_p: number) => {},
  stop: () => {},
  start: () => {},
}
export const pointer = { x: 0, y: 0 }

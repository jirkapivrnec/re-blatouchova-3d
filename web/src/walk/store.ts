import { useSyncExternalStore } from 'react'
import type * as THREE from 'three'

// Walk-through (first person) mode state, shared by the scene and the DOM UI.

export interface WalkState {
  walk: boolean // walk mode is on
  active: boolean // pointer locked (desktop) / started (touch)
  room: string
}

let state: WalkState = { walk: false, active: false, room: '' }
const listeners = new Set<() => void>()

export const walkStore = {
  get: () => state,
  set(patch: Partial<WalkState>) {
    state = { ...state, ...patch }
    listeners.forEach((l) => l())
  },
  subscribe(l: () => void) {
    listeners.add(l)
    return () => listeners.delete(l)
  },
}

export function useWalk() {
  return useSyncExternalStore(walkStore.subscribe, walkStore.get)
}

// raw input, read every frame by the controller
export const input = {
  keys: new Set<string>(),
  joy: { x: 0, y: 0 },
  look: { dx: 0, dy: 0 },
}

// collision sets filled once the model is loaded
export const colliders: { blockers: THREE.Mesh[]; ground: THREE.Mesh[] } = { blockers: [], ground: [] }

export const isTouch = () => typeof window !== 'undefined' && window.matchMedia('(pointer: coarse)').matches

export const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3)

export const easeOutBack = (t: number, s = 1.70158) => {
  const u = t - 1
  return 1 + (s + 1) * u * u * u + s * u * u
}

export const easeOutBounce = (t: number) => {
  const n = 7.5625
  const d = 2.75
  if (t < 1 / d) return n * t * t
  if (t < 2 / d) return n * (t -= 1.5 / d) * t + 0.75
  if (t < 2.5 / d) return n * (t -= 2.25 / d) * t + 0.9375
  return n * (t -= 2.625 / d) * t + 0.984375
}

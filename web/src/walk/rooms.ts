// Room rectangles in plan centimetres (same as blender/build_house.py ROOMS_*).
type Rect = [number, number, number, number]

const GF: [string, Rect[]][] = [
  ['Obývací pokoj', [[-500, -27, -135, 495]]],
  ['Kuchyň a jídelna', [[-500, -490, 99, -27]]],
  ['Hala', [[-135, -27, 350, 252], [99, -169, 350, -27]]],
  ['Zádveří', [[-135, 252, 350, 433]]],
  ['Dětský pokoj', [[99, -490, 501, -169]]],
  ['Technická místnost', [[501, -490, 675, -358]]],
  ['Koupelna', [[350, -169, 675, -39], [501, -358, 675, -169]]],
  ['Garáž', [[350, -39, 675, 433]]],
]
const UF: [string, Rect[]][] = [
  ['Ložnice', [[-500, 45, -62.5, 495]]],
  ['Dětský pokoj', [[-500, -490, -62.5, 45]]],
  ['Galerie', [[-62.5, -185, 324.7, 495], [324.7, -185, 454.7, -65]]],
  ['WC', [[-62.5, -490, 115.9, -185]]],
  ['Šatna', [[115.9, -490, 293.9, -185]]],
  ['Koupelna', [[293.9, -490, 675, -185], [454.7, -185, 675, -65]]],
  ['Pracovna', [[324.7, -65, 675, 495]]],
]

const inside = (x: number, y: number, r: Rect) => x >= r[0] && x <= r[2] && y >= r[1] && y <= r[3]

/** x, z in three.js metres, feet height in metres */
export function roomAt(x: number, z: number, feet: number) {
  const px = x * 100
  const py = z * 100
  if (feet > 2.2) {
    const hit = UF.find(([, rs]) => rs.some((r) => inside(px, py, r)))
    if (hit) return `Podkroví · ${hit[0]}`
    return 'Podkroví · Balkon'
  }
  if (feet > 0.25) return 'Schodiště'
  const hit = GF.find(([, rs]) => rs.some((r) => inside(px, py, r)))
  if (hit) return `Přízemí · ${hit[0]}`
  if (py > 433 && py < 660 && px > -125 && px < 300) return 'Zádveří · Vstup'
  return 'Zahrada'
}

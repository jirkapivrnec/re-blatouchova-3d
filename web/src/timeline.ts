// Scroll timeline: every chapter owns a slice of the global progress [0..1]
// and lists the model stages (from the Blender export) that get built inside it.

export type Vec3 = [number, number, number]

export interface StageWindow {
  stage: string
  from: number // fraction of the chapter slice
  to: number
}

export interface Chapter {
  id: string
  index: string
  title: string
  kicker: string
  text: string
  spec: string[]
  range: [number, number]
  stages: StageWindow[]
  cam: { pos: Vec3; target: Vec3 }
}

export const CHAPTERS: Chapter[] = [
  {
    id: 'site',
    index: '00',
    title: 'Pozemek',
    kicker: 'Obec · 110 00',
    text: 'Rovinatá zahrada na okraji obce. Do trávy je zatím vytyčený jen půdorys — obrys domu, jak ho kreslí architekt.',
    spec: ['půdorys 11,75 × 9,85 m', 'orientace vjezdem do ulice'],
    range: [0, 0.07],
    stages: [],
    cam: { pos: [6, 30, 22], target: [0.9, 0, 1.2] },
  },
  {
    id: 'foundation',
    index: '01',
    title: 'Základová deska',
    kicker: 'Hrubá stavba',
    text: 'Betonová deska přesně podle půdorysu, před vchodem dlážděné zádveří. Na ní se rozprostřou podlahy jednotlivých místností.',
    spec: ['základová deska', '8 podlahových ploch'],
    range: [0.07, 0.15],
    stages: [
      { stage: 'foundation', from: 0, to: 0.55 },
      { stage: 'gf_floor', from: 0.45, to: 1 },
    ],
    cam: { pos: [-11, 15, 19], target: [0.9, 0, 0.5] },
  },
  {
    id: 'walls',
    index: '02',
    title: 'Obvodové zdivo',
    kicker: 'Přízemí',
    text: 'Stěny tloušťky 30 cm vyrůstají po obvodu. Dole cihlový sokl, nahoře žlutá omítka — přesně jako na fotkách.',
    spec: ['16 segmentů', 'tloušťka 300 mm', 'výška 3,13 m'],
    range: [0.15, 0.25],
    stages: [{ stage: 'gf_walls_ext', from: 0, to: 1 }],
    cam: { pos: [-15, 11, 15], target: [0.9, 1, 0.3] },
  },
  {
    id: 'partitions',
    index: '03',
    title: 'Příčky',
    kicker: 'Dispozice přízemí',
    text: 'Velký obývací prostor s kuchyní a jídelnou, hala se schodištěm, dětský pokoj, koupelna, technická místnost a garáž.',
    spec: ['20 příček', 'komínový průduch', 'obytná část 64,98 m²'],
    range: [0.25, 0.31],
    stages: [{ stage: 'gf_walls_int', from: 0, to: 1 }],
    cam: { pos: [-8, 15, 11], target: [0.9, 0.5, 0] },
  },
  {
    id: 'openings',
    index: '04',
    title: 'Okna a dveře',
    kicker: 'Výplně otvorů',
    text: 'Dřevěná okna v tmavém hnědém rámu, francouzská okna na terasu, prosklené vchodové dveře a sekční vrata garáže.',
    spec: ['20 výplní', 'interiérové dveře s pískovaným sklem'],
    range: [0.31, 0.37],
    stages: [{ stage: 'gf_openings', from: 0, to: 1 }],
    cam: { pos: [10, 7, 15], target: [0.9, 1.2, 0] },
  },
  {
    id: 'stairs',
    index: '05',
    title: 'Schodiště',
    kicker: 'Hala',
    text: 'Dubové schodiště se zakřiveným ramenem a skleněným zábradlím. Patnáct stupňů z haly do podkroví.',
    spec: ['15 stupňů', 'výška 3,15 m', 'skleněné zábradlí'],
    range: [0.37, 0.41],
    stages: [{ stage: 'gf_stairs', from: 0, to: 1 }],
    cam: { pos: [7, 11, 9], target: [1.4, 0.6, -0.4] },
  },
  {
    id: 'gf_interior',
    index: '06',
    title: 'Život v přízemí',
    kicker: 'Interiér',
    text: 'Rohová sedačka u oken, krb se žlutým komínovým tělesem, ostrůvková kuchyň s červenou stěnou, jídelní stůl pro šest. A v garáži auto.',
    spec: ['29 kusů nábytku', 'krb', 'kuchyňský ostrůvek'],
    range: [0.41, 0.5],
    stages: [{ stage: 'gf_furniture', from: 0, to: 1 }],
    cam: { pos: [-9.5, 12, 10.5], target: [0, 0.2, -0.2] },
  },
  {
    id: 'slab',
    index: '07',
    title: 'Strop a balkony',
    kicker: 'Hrubá stavba',
    text: 'Stropní panely zakryjí přízemí. Vpředu a na štítu vyrostou sloupy, které nesou dva balkony se skleněným zábradlím.',
    spec: ['10 stropních panelů', '4 sloupy', '2 balkony'],
    range: [0.5, 0.57],
    stages: [
      { stage: 'gf_slab', from: 0, to: 0.65 },
      { stage: 'balcony', from: 0.4, to: 1 },
    ],
    cam: { pos: [-13, 10, 17], target: [0.6, 2, 0.6] },
  },
  {
    id: 'upper',
    index: '08',
    title: 'Podkroví',
    kicker: 'Druhé podlaží',
    text: 'Nízké nadezdívky, vysoké štíty a čelní vikýř s prosklenou stěnou na balkon. Tři pokoje, pracovna, koupelna, šatna a velká galerie.',
    spec: ['11 obvodových stěn', '13 příček', 'galerie 36,07 m²'],
    range: [0.57, 0.68],
    stages: [
      { stage: 'uf_floor', from: 0, to: 0.25 },
      { stage: 'uf_walls_ext', from: 0.15, to: 0.6 },
      { stage: 'uf_walls_int', from: 0.45, to: 0.85 },
      { stage: 'uf_openings', from: 0.7, to: 1 },
    ],
    cam: { pos: [-12, 17, 13], target: [0.9, 3.4, 0] },
  },
  {
    id: 'uf_interior',
    index: '09',
    title: 'Pokoje nahoře',
    kicker: 'Interiér podkroví',
    text: 'Ložnice, dětský pokoj, pracovna s rohovým stolem, koupelna s rohovou vanou. A na galerii posilovací věž s bicí soupravou.',
    spec: ['18 kusů nábytku', 'rohová vana', 'šatna'],
    range: [0.68, 0.75],
    stages: [{ stage: 'uf_furniture', from: 0, to: 1 }],
    cam: { pos: [5, 20, 12.5], target: [0.8, 3, -0.4] },
  },
  {
    id: 'truss',
    index: '10',
    title: 'Krov',
    kicker: 'Tesařské práce',
    text: 'Hřebenová vaznice a krokve se sklonem 40°. Na čelní straně se přidává menší sedlová střecha vikýře.',
    spec: ['sklon 40° / 45°', '20 prvků krovu'],
    range: [0.75, 0.81],
    stages: [{ stage: 'roof_frame', from: 0, to: 1 }],
    cam: { pos: [15, 13, 16], target: [1, 5, 0] },
  },
  {
    id: 'roof',
    index: '11',
    title: 'Střecha',
    kicker: 'Pálená krytina',
    text: 'Řada po řadě se pokládá cihlově červená taška. Následují střešní okna, okapy, hřebenáče, komín i televizní anténa.',
    spec: ['56 řad tašek', '5 střešních oken', 'hřeben 9 m'],
    range: [0.81, 0.92],
    stages: [
      { stage: 'roof_tiles', from: 0, to: 0.78 },
      { stage: 'roof_details', from: 0.65, to: 1 },
    ],
    cam: { pos: [-14, 15, 19], target: [1, 4.5, 0] },
  },
  {
    id: 'garden',
    index: '12',
    title: 'Zahrada',
    kicker: 'Venkovní úpravy',
    text: 'Dlážděný vjezd, terasa za domem, bazén, trampolína a stěna z tújí kolem celého pozemku.',
    spec: ['terasa', 'bazén', 'živý plot'],
    range: [0.92, 0.97],
    stages: [{ stage: 'garden', from: 0, to: 1 }],
    cam: { pos: [-22, 15, 25], target: [1, 2.5, 0] },
  },
  {
    id: 'done',
    index: '13',
    title: 'Hotovo.',
    kicker: 'Blatouchová 1111',
    text: 'Rozsvítí se okna a dům je doma.',
    spec: [],
    range: [0.97, 1],
    stages: [],
    cam: { pos: [-11.5, 4.4, 25], target: [1.4, 3.3, 0] },
  },
]

// stage -> absolute progress window
export const STAGE_WINDOWS: Record<string, [number, number]> = {}
for (const ch of CHAPTERS) {
  const [a, b] = ch.range
  for (const s of ch.stages) STAGE_WINDOWS[s.stage] = [a + (b - a) * s.from, a + (b - a) * s.to]
}

export const clamp01 = (v: number) => (v < 0 ? 0 : v > 1 ? 1 : v)
export const smooth = (v: number) => v * v * (3 - 2 * v)
export const smoother = (v: number) => v * v * v * (v * (v * 6 - 15) + 10)
export const range01 = (p: number, a: number, b: number) => clamp01((p - a) / (b - a))

export function chapterAt(p: number) {
  for (let i = CHAPTERS.length - 1; i >= 0; i--) if (p >= CHAPTERS[i].range[0]) return i
  return 0
}

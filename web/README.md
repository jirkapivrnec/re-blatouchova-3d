# Blatouchová 1111 — scroll-built house

Scroll-driven 3D web page: the plot with the glowing floor plan first, then the house
builds itself part by part as you scroll — foundation, walls, partitions, windows,
stairs, furniture, ceiling slab, upper floor, roof truss, roof tiles, garden.

## Walk-through

The always-visible **Vstoupit** button switches to a first-person tour that starts on
the porch in front of the main door. Desktop: WASD / arrows, mouse look (pointer lock,
drag as fallback), Shift to run, Esc to pause. Touch: joystick + drag to look.
Walls, furniture and railings block (`src/walk/WalkController.tsx`, raycasts against
nearby colliders), doorways are open and the stairs are walkable.

## Run locally

```bash
npm install
npm run dev
```

`npm run build` writes a static site to `dist/` (relative paths, works from any
GitHub Pages sub-path). `npm run preview` serves the build.

## Model

`public/models/house.glb` is generated in Blender by `../blender/build_house.py`
from `../pudorys.json` (floor plan, cm) and the reference photos. Every object carries
glTF extras `stage`, `order` and `anim`; `src/timeline.ts` maps stages to scroll
chapters and `src/scene/House.tsx` animates each part.

To regenerate: open Blender, run the script (it builds scene *Blatouchova*), then export
the scene as GLB with "Include → Custom Properties" enabled to `public/models/house.glb`.

## Deploy (GitHub Pages)

`.github/workflows/deploy.yml` in the repository root builds `web/` and deploys it on
every push to `main` (Pages source: GitHub Actions).

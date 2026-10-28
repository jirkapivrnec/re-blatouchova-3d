import { useProgress } from '@react-three/drei'
import { useEffect, useRef, useState } from 'react'
import { CHAPTERS, chapterAt } from '../timeline'
import { progress, scrollApi, stats } from '../store'
import { useWalk } from '../walk/store'
import { EnterButton, WalkUI, useWalkMode } from '../walk/WalkUI'

const LAST = CHAPTERS.length - 1

function useChapter() {
  const [idx, setIdx] = useState(0)
  useEffect(() => {
    let raf = 0
    let cur = -1
    const tick = () => {
      const i = chapterAt(progress.target)
      if (i !== cur) {
        cur = i
        setIdx(i)
      }
      raf = requestAnimationFrame(tick)
    }
    tick()
    return () => cancelAnimationFrame(raf)
  }, [])
  return idx
}

function Hero() {
  return (
    <div className="hero">
      <p className="kicker"><span className="dot" />Obec · 110 00</p>
      <h1 className="hero-title">
        <span>Blatouchová</span>
        <span className="hero-num">1111</span>
      </h1>
      <p className="lede">
        Rodinný dům s&nbsp;podkrovím, garáží a&nbsp;zahradou. Model složený z&nbsp;315 dílů podle
        skutečného půdorysu&nbsp;a&nbsp;fotografií. Scrollujte a&nbsp;dům se postaví.
      </p>
      <div className="scroll-cue"><i /> Scroll</div>
    </div>
  )
}

function Finale() {
  const facts = [
    ['315', 'dílů modelu'],
    ['2', 'podlaží'],
    ['15', 'místností'],
    ['40°', 'sklon střechy'],
  ]
  return (
    <div className="finale">
      <p className="kicker"><span className="dot warm" />Blatouchová 1111 · Obec</p>
      <h2 className="finale-title">Hotovo.</h2>
      <p className="lede">Rozsvítila se okna. Od vytyčeného půdorysu po anténu na hřebeni.</p>
      <dl className="facts">
        {facts.map(([v, l]) => (
          <div key={l}><dt>{v}</dt><dd>{l}</dd></div>
        ))}
      </dl>
      <button className="again" onClick={() => scrollApi.toProgress(0)}>
        <span>Postavit znovu</span><i>↺</i>
      </button>
    </div>
  )
}

function ChapterPanel({ idx }: { idx: number }) {
  const ch = CHAPTERS[idx]
  if (idx === 0) return <Hero key="hero" />
  if (idx === LAST) return <Finale key="finale" />
  return (
    <article className="chapter" key={ch.id}>
      <p className="kicker">
        <span className="idx">{ch.index}</span>
        <span className="sep" />
        {ch.kicker}
      </p>
      <h2 className="title">{ch.title}</h2>
      <p className="lede">{ch.text}</p>
      <ul className="spec">
        {ch.spec.map((s) => <li key={s}>{s}</li>)}
      </ul>
    </article>
  )
}

function Readout() {
  const parts = useRef<HTMLSpanElement>(null)
  const pct = useRef<HTMLSpanElement>(null)
  const bar = useRef<HTMLDivElement>(null)
  useEffect(() => {
    let raf = 0
    const tick = () => {
      const total = stats.total || 1
      if (parts.current) parts.current.textContent = `${String(stats.built).padStart(3, '0')}/${stats.total}`
      if (pct.current) pct.current.textContent = `${String(Math.round(progress.current * 100)).padStart(2, '0')} %`
      if (bar.current) bar.current.style.transform = `scaleX(${stats.built / total})`
      raf = requestAnimationFrame(tick)
    }
    tick()
    return () => cancelAnimationFrame(raf)
  }, [])
  return (
    <div className="readout">
      <div className="readout-row"><span className="lbl">Postaveno</span><span ref={parts} className="val">000/0</span></div>
      <div className="readout-bar"><div ref={bar} /></div>
      <div className="readout-row"><span className="lbl">Průběh</span><span ref={pct} className="val">00 %</span></div>
    </div>
  )
}

function Rail({ idx }: { idx: number }) {
  const fill = useRef<HTMLDivElement>(null)
  useEffect(() => {
    let raf = 0
    const tick = () => {
      if (fill.current) fill.current.style.transform = `scaleY(${progress.current})`
      raf = requestAnimationFrame(tick)
    }
    tick()
    return () => cancelAnimationFrame(raf)
  }, [])
  return (
    <nav className="rail" aria-label="Fáze stavby">
      <div className="rail-track"><div ref={fill} className="rail-fill" /></div>
      <ol>
        {CHAPTERS.map((c, i) => (
          <li key={c.id} className={i === idx ? 'on' : i < idx ? 'done' : ''}>
            <button
              onClick={() => scrollApi.toProgress(i === 0 ? 0 : i === LAST ? 1 : (c.range[0] + c.range[1]) / 2)}
              aria-label={c.title}
            >
              <span className="rail-name">{c.title}</span>
              <span className="rail-idx">{c.index}</span>
              <i />
            </button>
          </li>
        ))}
      </ol>
    </nav>
  )
}

function Loader() {
  const { progress: p, active } = useProgress()
  const [gone, setGone] = useState(false)
  useEffect(() => {
    if (!active && p >= 100) {
      const t = setTimeout(() => setGone(true), 500)
      return () => clearTimeout(t)
    }
  }, [active, p])
  if (gone) return null
  return (
    <div className={`loader ${!active && p >= 100 ? 'out' : ''}`}>
      <div className="loader-inner">
        <p>Blatouchová 1111</p>
        <div className="loader-bar"><div style={{ transform: `scaleX(${p / 100})` }} /></div>
        <span>{Math.round(p)} % · načítám model</span>
      </div>
    </div>
  )
}

export function Interface() {
  const idx = useChapter()
  const { walk } = useWalk()
  const { enter, exit, fading } = useWalkMode(() => scrollApi.stop(), () => scrollApi.start())
  return (
    <>
      {!walk && (
        <>
          <div className={`scrim ${idx === 0 ? 'hero-scrim' : ''}`} />
          <header className="topbar">
            <a className="brand" href="#" onClick={(e) => { e.preventDefault(); scrollApi.toProgress(0) }}>
              <b>Blatouchová</b> 1111
            </a>
            <div className="topbar-right">
              <span className="where">Obec 110 00 · CZ</span>
              <EnterButton onEnter={enter} />
            </div>
          </header>
          <div className="panel">
            <ChapterPanel idx={idx} />
          </div>
          <Readout />
          <Rail idx={idx} />
        </>
      )}
      {walk && <WalkUI exit={exit} />}
      <div className={`fade ${fading ? 'on' : ''}`} />
      <Loader />
    </>
  )
}

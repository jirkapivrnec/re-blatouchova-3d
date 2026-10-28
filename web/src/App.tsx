import Lenis from 'lenis'
import { useEffect } from 'react'
import { Experience } from './scene/Experience'
import { Interface } from './ui/Interface'
import { CHAPTERS } from './timeline'
import { pointer, progress, scrollApi } from './store'

// Total scroll length; each chapter gets height proportional to its progress slice.
const TOTAL_VH = 1500

export default function App() {
  useEffect(() => {
    const lenis = new Lenis({ lerp: 0.085, wheelMultiplier: 0.9, touchMultiplier: 1.4 })
    const onScroll = () => {
      progress.target = lenis.limit > 0 ? lenis.scroll / lenis.limit : 0
    }
    lenis.on('scroll', onScroll)
    onScroll()
    scrollApi.toProgress = (p) => lenis.scrollTo(p * lenis.limit, { duration: p === 0 ? 2.4 : 1.6 })
    scrollApi.stop = () => {
      lenis.stop()
      document.documentElement.classList.add('walking')
    }
    scrollApi.start = () => {
      document.documentElement.classList.remove('walking')
      lenis.start()
    }
    let raf = requestAnimationFrame(function loop(t) {
      lenis.raf(t)
      raf = requestAnimationFrame(loop)
    })
    const onMove = (e: PointerEvent) => {
      pointer.x = (e.clientX / window.innerWidth) * 2 - 1
      pointer.y = (e.clientY / window.innerHeight) * 2 - 1
    }
    window.addEventListener('pointermove', onMove)
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('pointermove', onMove)
      lenis.destroy()
    }
  }, [])

  return (
    <>
      <Experience />
      <Interface />
      <main className="scroller" aria-hidden>
        {CHAPTERS.map((c) => (
          <section key={c.id} id={c.id} style={{ height: `${(c.range[1] - c.range[0]) * TOTAL_VH}vh` }} />
        ))}
        <section style={{ height: '100vh' }} />
      </main>
    </>
  )
}

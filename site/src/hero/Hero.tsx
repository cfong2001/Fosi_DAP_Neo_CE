import { useEffect, useRef } from 'react'
import { Stage } from '../kit/stage'
import type { Theme } from '../kit/looks'
import type { Act } from '../kit/act'
import './hero.css'
type Scene = { phase: 'idle' | 'flight' | 'impact' | 'ready' }
async function script(a: Act<Scene>) {
  await a.wait(900); a.mark('file'); await a.set({ phase: 'flight' }); await a.wait(1000)
  a.mark('impact'); await a.set({ phase: 'impact' }); await a.wait(1500)
  a.mark('ready'); await a.set({ phase: 'ready' }); await a.wait(2400)
}
export default function Hero({ theme }: { theme: Theme }) {
  const root = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)')
    const reset = () => { root.current?.style.setProperty('--rx', '-9deg'); root.current?.style.setProperty('--ry', '-19deg') }
    const follow = (e: PointerEvent) => {
      if (motion.matches || e.pointerType === 'touch' || !root.current) return
      const b = root.current.getBoundingClientRect()
      const clamp = (v: number) => Math.max(-1, Math.min(1, v))
      root.current.style.setProperty('--rx', `${-clamp((e.clientY-b.top-b.height*.5)/b.height)*20}deg`)
      root.current.style.setProperty('--ry', `${clamp((e.clientX-b.left-b.width*.58)/b.width)*32}deg`)
    }
    window.addEventListener('pointermove', follow, { passive: true })
    document.documentElement.addEventListener('pointerleave', reset)
    motion.addEventListener('change', reset)
    return () => { window.removeEventListener('pointermove', follow); document.documentElement.removeEventListener('pointerleave', reset); motion.removeEventListener('change', reset) }
  }, [])
  return <div ref={root} className="neo-hero"><Stage<Scene> width={720} height={400} compact={{ below: 560, width: 358, height: 340 }} initial={{ phase:'idle' }} poster={{ phase:'ready' }} script={script} play="once" theme={theme} unframed className="neo-stage">
    {s => <div className="neo-scene" data-phase={s.phase}>
      <div className="neo-shadow" />
      <div className="neo-position"><div className="neo-scale"><div className="neo-gaze"><div className="neo-player">
        {Array.from({length:15},(_,i)=><div key={i} className="neo-slice" style={{transform:`translateZ(${i-7}px)`}} />)}
        <div className="neo-back"><span>Fosi Audio</span><div><strong>DAP Neo</strong><small>Portable Digital Music Player</small><small>Made in China</small></div></div>
        <div className="neo-side neo-power" /><div className="neo-side neo-volume" /><div className="neo-side neo-next" />
        <div className="neo-front"><div className="neo-glass"><div className="neo-display"><div className="neo-boot"><strong>CE</strong><span>Community Edition</span><i /></div></div></div><div className="neo-wheel"><div className="neo-center" /></div><div className="neo-ports"><i /><b /><i /></div></div>
      </div></div></div></div>
      <div className="neo-file" aria-hidden="true"><div className="neo-page"><span>IMG</span></div><span>RKNANOFWIMG</span></div>
      <div className="neo-impact" aria-hidden="true" />
      <div className="neo-caption">DAP Neo with Community Edition firmware</div>
      <span className="neo-description">An update file hits the player, spins it, and lights its screen with CE.</span>
    </div>}
  </Stage></div>
}

import { useEffect, useRef, useState } from 'react'
import { Stage } from '../kit/stage'
import { Button } from '../kit/controls/Button'
import type { Act } from '../kit/act'
import type { Theme } from '../kit/looks'
import PlayerModel, { type Display, type DisplayMode } from './PlayerModel'

const INITIAL = { on: false, holding: false, progress: 0, cover: 0 }
const POSTER = { on: true, holding: false, progress: 1, cover: 1 }
type Beat = typeof INITIAL
const scripts = Object.fromEntries(['theater', 'eq', 'bluetooth', 'playlist', 'lockscreen', 'gapless', 'opus', 'system'].map(mode => [mode, async (a: Act<Beat>) => {
  await a.wait(900)
  a.mark('action')
  if (mode === 'bluetooth') {
    await a.set({ holding: true })
    for (let i = 1; i <= 24; i++) { await a.wait(50); a.put({ progress: i / 24 }) }
    a.mark('paired'); await a.set({ on: true, holding: false })
  } else {
    await a.set({ on: true, cover: 1 })
    for (let i = 1; i <= 20; i++) { await a.wait(45); a.put({ progress: i / 20 }) }
    a.mark('result')
  }
  await a.wait(2200)
}])) as Record<DisplayMode, (a: Act<Beat>) => Promise<void>>

function Demo({ mode, scene }: { mode: DisplayMode; scene: Beat }) {
  const [manual, setManual] = useState<Display | null>(null)
  const display: Display = manual ?? { ...scene, mode }
  const current = useRef(display); current.current = display
  const raf = useRef(0)
  const pressing = useRef(false)
  const release = () => {
    if (!pressing.current) return
    pressing.current = false
    cancelAnimationFrame(raf.current)
    setManual(s => s ? { ...s, holding: false, progress: 0 } : s)
  }
  const begin = () => {
    if (pressing.current) return
    pressing.current = true
    const before = current.current
    const started = performance.now()
    const tick = () => {
      const p = Math.min(1, (performance.now() - started) / 1200)
      setManual({ ...before, holding: p < 1, progress: p, on: p === 1 ? !before.on : before.on })
      if (p < 1) raf.current = requestAnimationFrame(tick)
      else pressing.current = false
    }
    tick()
  }
  useEffect(() => {
    const cancel = () => { cancelAnimationFrame(raf.current); pressing.current = false; setManual(s => s ? { ...s, holding: false, progress: 0 } : s) }
    window.addEventListener('blur', cancel)
    return () => { cancelAnimationFrame(raf.current); window.removeEventListener('blur', cancel) }
  }, [])
  const choose = (patch: Partial<Display>) => {
    cancelAnimationFrame(raf.current)
    if (mode !== 'eq') { setManual({ ...current.current, ...patch }); return }
    const before = current.current, target = patch.on ? 1 : 0, started = performance.now()
    const tick = () => {
      const t = Math.min(1, (performance.now() - started) / 650)
      const ease = 1 - Math.pow(1 - t, 3)
      setManual({ ...before, ...patch, progress: before.progress + (target - before.progress) * ease })
      if (t < 1) raf.current = requestAnimationFrame(tick)
    }
    tick()
  }
  return <div className="device-demo" data-mode={mode} data-on={display.on} data-holding={display.holding}>
    <PlayerModel state={display} onHoldStart={mode === 'bluetooth' ? begin : undefined} onHoldEnd={release} />
    {mode === 'bluetooth' && <div className="demo-controls">

      <Button size="large" className="demo-hold" tabIndex={0} aria-label="Hold Power for 1.2 seconds to toggle Bluetooth preview" data-target="power-preview" aria-pressed={display.on}
        onPointerDown={e => { e.currentTarget.setPointerCapture(e.pointerId); begin() }} onPointerUp={release} onPointerCancel={release} onLostPointerCapture={release}
        onKeyDown={e => { if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); if (!e.repeat) begin() } }}
        onKeyUp={e => { if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); release() } }} onBlur={release}>
        Hold Power
      </Button>
      <span className="demo-instruction">Hold the orange side button or this control for 1.2 seconds.</span>
    </div>}
    {mode === 'eq' && <div className="demo-controls">
      <div className="demo-options" role="group" aria-label="EQ curve preview">
        <Button size="large" tabIndex={0} aria-pressed={!display.on} onClick={() => choose({on:false,progress:0})} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose({on:false,progress:0})}}}>Stock preset</Button>
        <Button size="large" tabIndex={0} aria-pressed={display.on} onClick={() => choose({on:true,progress:1})} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose({on:true,progress:1})}}}>HD 600 curve</Button>
      </div>
      <span className="demo-instruction">Compare the preset and fitted curve on the player’s screen.</span>
    </div>}
    {mode === 'theater' && <div className="demo-controls">
      <div className="demo-options" role="group" aria-label="Sample artwork">
        {['Evening light','Open water','Forest floor'].map((label, cover) => <Button key={label} size="large" tabIndex={0} aria-pressed={display.cover===cover} onClick={()=>choose({cover,on:true})} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose({cover,on:true})}}}>{label}</Button>)}
      </div>
      <span className="demo-instruction">Choose artwork to change the playback background.</span>
    </div>}
  </div>
}

export default function DevicePicture({ theme, width, mode }: { theme: Theme; width: number; mode: DisplayMode }) {
  const interactive = ['eq','bluetooth','theater'].includes(mode)
  return <Stage<Beat> width={width} height={interactive ? 540 : 430} initial={INITIAL} poster={POSTER} script={scripts[mode]} play="once" theme={theme} accent="var(--ce-accent)" tokens={{'--ss-font':'var(--ce-font)'}} unframed className="ft-stage device-stage">
    {scene => <Demo mode={mode} scene={scene} />}
  </Stage>
}

import { useRef, useState, useEffect, type ReactNode } from 'react'
import { Bluetooth, LockKeyhole, Play, SkipForward } from 'lucide-react'
import { Stage } from '../kit/stage'
import type { Act } from '../kit/act'
import type { Theme } from '../kit/looks'
import '../hero/hero.css'

type Mode = 'theater' | 'eq' | 'bluetooth' | 'playlist' | 'lockscreen' | 'gapless' | 'opus' | 'system'
type Beat = { on: boolean; holding: boolean }
const start: Beat = { on: false, holding: false }
async function script(a: Act<Beat>) {
  await a.wait(500)
  a.mark('hold'); await a.set({ holding: true }); await a.wait(1200)
  a.mark('result'); await a.set({ on: true, holding: false }); await a.wait(1500)
}

function Player({ children, holding, toggle }: { children: ReactNode; holding: boolean; toggle?: () => void }) {
  return <div className="fp-position"><div className="fp-player">
    {Array.from({ length: 15 }, (_, i) => <div key={i} className="neo-slice" style={{ transform: `translateZ(${i - 7}px)` }} />)}
    <div className="neo-side neo-volume" /><div className="neo-side neo-next" />
    {toggle ? <button type="button" className="fp-power" data-held={holding || undefined} onClick={toggle} aria-label="Hold Power to toggle Bluetooth preview" /> : <div className="neo-side neo-power" />}
    <div className="neo-front"><div className="neo-glass"><div className="neo-display fp-display">{children}</div></div><div className="neo-wheel"><div className="neo-center" /></div><div className="neo-ports"><i /><b /><i /></div></div>
  </div></div>
}

function Content({ mode, on }: { mode: Mode; on: boolean }) {
  if (mode === 'eq') return <div className="fp-eq"><span>EQ / Heavy Metal</span><svg viewBox="0 0 110 65" aria-label="Fitted EQ curve"><path className="fp-eq-grid" d="M0 16H110 M0 33H110 M0 50H110"/><path className="fp-curve" data-on={on} pathLength="1" d="M2 27L6 25L10 25L14 23L18 25L22 25L26 27L30 29L34 31L38 29L42 31L46 28L50 30L54 25L58 25L62 27L66 29L70 27L74 33L78 29L82 23L86 25L90 31L94 27L98 17L102 13L106 53L109 45"/></svg><div className="fp-axis"><span>20 Hz</span><span>20 kHz</span></div><small>Custom build preview</small></div>
  if (mode === 'bluetooth') return <div className="fp-bt-screen"><Bluetooth size={30} className={on ? 'fp-lit' : ''}/><strong>Bluetooth {on ? 'on' : 'off'}</strong><small>Power / long press</small></div>
  if (mode === 'theater') return <div className="fp-music" data-on={on}><div className="ft-cover ft-cover--ember"/><strong>Evening light</strong><small>Sample track</small><div className="fp-progress"><i /></div><Play size={12} fill="currentColor"/></div>
  if (mode === 'playlist') return <div className="fp-list"><strong>Evening.m3u</strong>{['01  Evening light','02  Open water','03  Last train'].map((t,i)=><span key={t} data-selected={i===(on?1:0)}>{t}</span>)}<small>{on ? 'Next / inside playlist' : '3 tracks'}</small></div>
  if (mode === 'lockscreen') return <div className="fp-lock"><LockKeyhole size={18}/><strong>{on ? 'Evening light' : 'Hold enabled'}</strong><span>{on ? '01:24' : '—:—'}</span><small>Playback continues</small></div>
  if (mode === 'gapless') return <div className="fp-lock"><SkipForward size={22}/><strong>{on ? 'Track 02.flac' : 'Track 01.flac'}</strong><div className="fp-wave" data-on={on}>{Array.from({length:19},(_,i)=><i key={i} style={{height:`${8+(i*13)%27}px`}}/>)}</div><small>Same-format transition</small></div>
  if (mode === 'opus') return <div className="fp-lock"><Play size={23} fill="currentColor"/><strong>{on ? 'Playing .opus' : 'Track.opus'}</strong><span>Standard</span><small>Replaces WMA support</small></div>
  return <div className="fp-lock"><strong>Wheel timer</strong><span>{on ? '1,000' : '2,500'}</span><small>wakeups per second</small><small>{on ? 'CE firmware' : 'Stock V137'}</small></div>
}
export default function DevicePicture({ theme, width, mode }: { theme: Theme; width: number; mode: Mode }) {
  const [override, setOverride] = useState<boolean | null>(null)
  const [holding, setHolding] = useState(false)
  const timer = useRef<ReturnType<typeof setTimeout>>()
  useEffect(() => () => clearTimeout(timer.current), [])
  return <Stage<Beat> width={width} height={350} initial={start} poster={{on:true,holding:false}} script={script} play="once" theme={theme} accent="var(--ce-accent)" unframed className="ft-stage fp-stage">
    {s => { const on = override ?? s.on; const toggle = () => { if (holding) return; setHolding(true); timer.current=setTimeout(()=>{setOverride(!on);setHolding(false)},1200) }; return <div className="fp-scene" data-mode={mode}>
      <Player holding={holding || s.holding && mode==='bluetooth'} toggle={mode==='bluetooth' ? toggle : undefined}><Content mode={mode} on={on}/></Player>
      <div className="fp-caption">{mode==='bluetooth' ? (holding || s.holding ? 'Holding the side Power button…' : 'Press the orange button to preview a long press') : ({ theater: 'Album art and background preview', eq: '31 bands / ±12 dB', playlist: 'Next remains within the playlist', lockscreen: 'Title and elapsed time with hold enabled', gapless: 'Same-format decoder fast path', opus: 'Standard image / Opus replaces WMA', system: 'Wheel timer / stock compared with CE' } as const)[mode]}</div>
    </div> }}
  </Stage>
}

import { useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Stage } from '../kit/stage'
import type { Theme } from '../kit/looks'
import { Bar } from '../kit/window'
import { Count } from '../kit/motion'
import { Card } from '../kit/parts/Card'
import { useReducedMotion } from '../kit/reduced-motion'
import type { Act } from '../kit/act'
import './features.css'
import DevicePicture from './DevicePicture'
import DetailPicture from './DetailPictures'

// Each feature picture mounts into its HTML slot at the slot's actual width.
// Physical-player previews share DevicePicture; sorting retains its original
// moving list and the Vorbis figure counts once when it enters view.

const STEP = 110
const LEAD = 450

type Beat = { on: boolean }
const before: Beat = { on: false }
const after: Beat = { on: true }
const beat = (i: number) => async (a: Act<Beat>) => {
  await a.wait(LEAD + i * STEP)
  await a.set({ on: true })
}

// ---- Vorbis: page type, one number that counts up once in view
function VorbisStat() {
  const reduced = useReducedMotion()
  const ref = useRef<HTMLSpanElement>(null)
  const [seen, setSeen] = useState(false)
  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    let t = 0
    const io = new IntersectionObserver(([e]) => {
      if (!e.isIntersecting) return
      io.disconnect()
      t = window.setTimeout(() => setSeen(true), LEAD + STEP)
    }, { threshold: 0.4 })
    io.observe(el)
    return () => { io.disconnect(); clearTimeout(t) }
  }, [])
  return (
    <span ref={ref} className="ft-stat-number">
      <Count value={seen || reduced ? 40 : 0} duration={1100} />
      <span className="ft-stat-unit"> dB</span>
    </span>
  )
}

// ---- Natural sort: stock's order (1, 10, 2) settles into 1, 2, 10
const TRACKS = ['Track 1', 'Track 2', 'Track 10']

function SortPicture({ theme, width }: { theme: Theme; width: number }) {
  const inner = Math.max(200, width - 48)
  return (
    <Stage<Beat> width={width} height={224} initial={before} poster={after} play="once" script={beat(3)} theme={theme} accent="var(--ce-accent)" className="ft-stage">
      {(s) => {
        const order = s.on ? [0, 1, 2] : [0, 2, 1]
        return (
          <Card pad="small" lift className="ft-sort" style={{ width: inner }}>
            <div className="ft-sort-rows">
              {TRACKS.map((t, i) => (
                <div key={t} className="ft-sort-row" data-moving={i === 2 || undefined} style={{ transform: `translateY(${order[i] * 40}px)` }}>
                  <span className="ft-sort-no">{order[i] + 1}</span>
                  <span className="ft-sort-name">{t}</span>
                  <Bar w={[44, 38, 50][i]} h={6} tone={2} />
                </div>
              ))}
              {/* The album goes on below the crop: filler rows */}
              {[0, 1, 2].map((k) => (
                <div key={k} className="ft-sort-row" style={{ transform: `translateY(${(3 + k) * 40}px)` }}>
                  <span className="ft-sort-no">{4 + k}</span>
                  <Bar w={[72, 60, 80][k]} h={7} tone={3} />
                  <Bar w={[40, 46, 36][k]} h={6} tone={2} />
                </div>
              ))}
            </div>
          </Card>
        )
      }}
    </Stage>
  )
}

const device = (mode: Parameters<typeof DevicePicture>[0]['mode']) =>
  (props: { theme: Theme; width: number }) => <DevicePicture {...props} mode={mode} />
const detail = (mode: Parameters<typeof DetailPicture>[0]['mode']) =>
  (props: { theme: Theme; width: number }) => <DetailPicture {...props} mode={mode} />
const PICTURES = {
  theater: device('theater'), eq: device('eq'), sort: SortPicture,
  bluetooth: device('bluetooth'), playlist: detail('playlist'),
  lockscreen: device('lockscreen'), gapless: detail('gapless'),
  opus: detail('opus'), system: detail('system'),
} as const

// One picture per [data-picture] slot, drawn at the slot's own width so the
// tile, not the stage, owns the crop.
function Slot({ node, theme }: { node: HTMLElement; theme: Theme }) {
  const [width, setWidth] = useState(() => Math.max(1, Math.round(node.getBoundingClientRect().width)) || 340)
  useLayoutEffect(() => {
    const measure = () => setWidth(Math.max(1, Math.round(node.getBoundingClientRect().width)))
    measure()
    const observer = new ResizeObserver(measure)
    observer.observe(node)
    return () => observer.disconnect()
  }, [node])
  const Picture = PICTURES[node.dataset.picture as keyof typeof PICTURES]
  return Picture ? createPortal(<Picture theme={theme} width={width} />, node) : null
}

export default function Features({ theme, root }: { theme: Theme; root: HTMLElement }) {
  const slots = [...root.querySelectorAll<HTMLElement>('[data-picture]')]
  const stat = root.querySelector<HTMLElement>('[data-stat="vorbis"]')
  return (
    <>
      {slots.map((node) => <Slot key={node.dataset.picture} node={node} theme={theme} />)}
      {stat && createPortal(<VorbisStat />, stat)}
    </>
  )
}

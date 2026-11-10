import { useLayoutEffect, useRef, useState, type CSSProperties } from 'react'
import { createPortal } from 'react-dom'
import { Power, SkipBack, SkipForward, Play } from 'lucide-react'
import { Stage } from '../kit/stage'
import type { Theme } from '../kit/looks'
import { Bar } from '../kit/window'
import { Count, States } from '../kit/motion'
import { Card } from '../kit/parts/Card'
import { Icon } from '../kit/parts/Icon'
import { Badge } from '../kit/controls/Badge'
import { Chart } from '../kit/chart'
import { useReducedMotion } from '../kit/reduced-motion'
import type { Act } from '../kit/act'
import './features.css'

// "What CE changes", a bento grid (Stageshow references/bento.md, from the
// gold `bento`). The tile copy is page HTML in docs/index.html; each picture
// is its own Stage, mounted into the tile's [data-picture] slot at the slot's
// width. Every tile plays one beat, once, as it scrolls in, 110ms after the
// tile before it in reading order.
//
//   Tile       Span   Kind        The one thing                         Moves
//   Theater    2 x 1  Hero UI     three player screens, three covers   each ground turns from stock to its cover's
//   Vorbis     1 x 1  Stat        "40 dB", on the one dark tile         counts up from 0
//   EQ         1 x 1  Component   Heavy Metal with a fitted curve       the curve draws in
//   Sort       1 x 1  Component   Track 2 above Track 10                Track 10 drops below Track 2
//   Bluetooth  1 x 1  Object      the Power key, held                   Off turns On
//
// Only the theater tile shows player UI; no string repeats between tiles.

const STEP = 110
const LEAD = 450

type Beat = { on: boolean }
const before: Beat = { on: false }
const after: Beat = { on: true }
const beat = (i: number) => async (a: Act<Beat>) => {
  await a.wait(LEAD + i * STEP)
  await a.set({ on: true })
}

// ---- Theater: the firmware's rule (patches/full/build/tests/test_theater_full.py
// port_derived): the top third of the cover averaged, mixed 55% toward black
// in the dark theme, quantized to RGB565. The averages are those of the
// gradients below over their top third.
const rgb565 = (r: number, g: number, b: number) =>
  (Math.floor((r * 31 + 127) / 255) << 11) | (Math.floor((g * 63 + 127) / 255) << 5) | Math.floor((b * 31 + 127) / 255)
const css565 = (w: number) =>
  `rgb(${Math.floor(((w >> 11) & 31) * 255 / 31)}, ${Math.floor(((w >> 5) & 63) * 255 / 63)}, ${Math.floor((w & 31) * 255 / 31)})`
const derived = (avg: [number, number, number]) => css565(rgb565(...(avg.map((a) => Math.floor((a * 45 + 50) / 100)) as [number, number, number])))
const STOCK_GROUND = css565(0x10a2)

const COVERS = [
  { kind: 'ember', avg: [217, 121, 28] as [number, number, number] },
  { kind: 'tide', avg: [22, 135, 177] as [number, number, number] },
  { kind: 'violet', avg: [180, 62, 195] as [number, number, number] },
]

function Screen({ kind, ground, on, delay }: { kind: string; ground: string; on: boolean; delay: number }) {
  return (
    <div className="ft-screen" style={{ background: on ? ground : STOCK_GROUND, transitionDelay: `${delay}ms` }}>
      <div className={`ft-cover ft-cover--${kind}`} />
      <span className="ft-lines">
        <Bar w={92} h={8} r={4} style={{ background: 'rgba(255, 255, 255, 0.82)' }} />
        <Bar w={64} h={6} r={3} style={{ background: 'rgba(255, 255, 255, 0.5)' }} />
      </span>
      <span className="ft-progress"><span /></span>
      <span className="ft-transport" aria-hidden>
        <SkipBack size={16} strokeWidth={2} />
        <Play size={18} strokeWidth={2} fill="currentColor" />
        <SkipForward size={16} strokeWidth={2} />
      </span>
    </div>
  )
}

function TheaterPicture({ theme, width }: { theme: Theme; width: number }) {
  // Three screens where they fit at full size, else two sized to the tile,
  // one gutter (24) from each side.
  const count = width < 600 ? 2 : 3
  const screen = Math.min(176, Math.floor((width - 48 - 16 * (count - 1)) / count))
  const vars = { '--screen': `${screen}px`, '--cover': `${Math.min(116, screen - 32)}px` } as CSSProperties
  return (
    <Stage<Beat> width={width} height={268} initial={before} poster={after} play="once" script={beat(0)} theme={theme} className="ft-stage ft-stage--theater">
      {(s) => (
        <div className="ft-screens" data-count={count} style={vars}>
          {COVERS.slice(0, count).map((c, i) => (
            <Screen key={c.kind} kind={c.kind} ground={derived(c.avg)} on={s.on} delay={i * 160} />
          ))}
        </div>
      )}
    </Stage>
  )
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

// ---- EQ: slot 6's curve from tests/builder.test.mjs (the browser's fit of
// the Sennheiser HD 600 AutoEQ GraphicEQ fixture), 31 bands, shifted by
// +12 dB so the chart's baseline is the -12 dB floor.
const CURVE = [-1, 0, 0, 1, 0, 0, 0, -1, -2, -1, -2, -1, -2, 0, 0, -1, -1, -1, -3, -1, 1, 0, -3, -1, -2, -2, 3, 5, -11, -7, -12]

function EqPicture({ theme, width }: { theme: Theme; width: number }) {
  const inner = Math.max(200, width - 48)
  return (
    <Stage<Beat> width={width} height={224} initial={before} poster={after} play="once" script={beat(2)} theme={theme} className="ft-stage">
      {(s) => (
        <Card pad="medium" lift className="ft-eq" style={{ width: inner }}>
          <span className="ft-eq-head">
            <span className="ft-eq-name">Heavy Metal</span>
            <States value={s.on ? 'custom' : 'stock'} align="end" states={{
              stock: <Badge>Stock</Badge>,
              custom: <Badge tone="accent">Custom</Badge>,
            }} />
          </span>
          <Chart data={CURVE.map((v) => v + 12)} max={18} width={inner - 32} height={84} show={s.on} area dot className="ft-eq-chart" />
          <span className="ft-eq-axis"><span>20 Hz</span><span>20 kHz</span></span>
        </Card>
      )}
    </Stage>
  )
}

// ---- Natural sort: stock's order (1, 10, 2) settles into 1, 2, 10
const TRACKS = ['Track 1', 'Track 2', 'Track 10']

function SortPicture({ theme, width }: { theme: Theme; width: number }) {
  const inner = Math.max(200, width - 48)
  return (
    <Stage<Beat> width={width} height={224} initial={before} poster={after} play="once" script={beat(3)} theme={theme} className="ft-stage">
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

// ---- Bluetooth: the Power key, held; the state beside it turns On
function BluetoothPicture({ theme, width }: { theme: Theme; width: number }) {
  return (
    <Stage<Beat> width={width} height={224} initial={before} poster={after} play="once" script={beat(4)} theme={theme} className="ft-stage">
      {(s) => (
        <div className="ft-bt">
          <span className="ft-key" data-on={s.on || undefined}>
            <Power size={30} strokeWidth={2} />
            <span className="ft-key-label">Hold</span>
          </span>
          <States value={s.on ? 'on' : 'off'} align="start" states={{
            off: <Badge>Bluetooth off</Badge>,
            on: <Badge tone="success" icon={<Icon name="check" size={12} />}>Bluetooth on</Badge>,
          }} />
        </div>
      )}
    </Stage>
  )
}

const PICTURES = {
  theater: TheaterPicture,
  eq: EqPicture,
  sort: SortPicture,
  bluetooth: BluetoothPicture,
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

import { useLayoutEffect, useRef, type ReactNode } from 'react'
import { ChevronLeft, ChevronRight, File, Folder, LayoutGrid, List, Search } from 'lucide-react'
import { Stage } from '../kit/stage'
import type { Theme } from '../kit/looks'
import { Bar } from '../kit/window'
import { Window } from '../kit/window'
import { Collapse, States } from '../kit/motion'
import { Meter } from '../kit/parts/Meter'
import { Icon } from '../kit/parts/Icon'
import { Badge } from '../kit/controls/Badge'
import type { Act } from '../kit/act'
import type { Layout } from '../kit/looks'
import type { Point } from '../kit/measure'
import './hero.css'

// The CE install, as the site's hero (from the Stageshow gold `upload`).
// The player is plugged in and its storage is open in a file window. The
// update file sits on the desktop: it is carried into the player's storage,
// a copy row opens at the top and its bar fills, then the row settles into an
// ordinary file row (Just now) while a satellite card rises over the
// window's left edge: SHA-256 matches, over the Standard image's hash. That
// is what the page's Copy to player reports after it reads the file back.
// Cmd+Z takes the copy back, which is where the loop began.
//
// Real strings: the drive, the file name (on the desktop and in its row),
// its size, Just now, SHA-256 matches and the hash. Everything else is
// placeholder bars: the player's own folders are the user's, not ours to
// name. Compact drops the satellite and says Verified in the row instead.

type Ghost = { on: boolean; dropped: boolean; off: Point; at: Point }
type S = { up: boolean; p: number; done: boolean; ghost: Ghost }

const initial: S = { up: false, p: 0, done: false, ghost: { on: false, dropped: false, off: { x: 0, y: 0 }, at: { x: 0, y: 0 } } }
const poster: S = { up: true, p: 1, done: true, ghost: initial.ghost }

const FILE = 'RKNANOFWIMG'
const SIZE = '13.6 MB'
const HASH = ['9cc86655ddf23bdd', '…', 'bdc98a3']

type Geo = {
  win: { x: number; y: number; w: number; h: number }
  rows: number
  cols: string
  desk: { x: number; y: number }
}

// Wide: one gutter (40) above the window and left of the file; the window
// runs off the right and bottom, its Size column still whole in the crop.
// Compact (a phone column, 358 wide): no desktop. The window sits one
// gutter (20) from the top and left and runs off the right and bottom; the
// status column stays whole and the crop falls on the Size column's filler.
const GEO: Record<Layout, Geo> = {
  wide: { win: { x: 176, y: 40, w: 580, h: 400 }, rows: 9, cols: 'minmax(0, 1fr) 128px 112px', desk: { x: 36, y: 124 } },
  compact: { win: { x: 20, y: 20, w: 384, h: 320 }, rows: 7, cols: 'minmax(0, 1fr) 96px 72px', desk: { x: 0, y: 0 } },
}

type Kind = 'folder' | 'doc'
const ROWS: { kind: Kind; name: number; date: number; size: number }[] = [
  { kind: 'folder', name: 72, date: 84, size: 16 },
  { kind: 'folder', name: 96, date: 76, size: 16 },
  { kind: 'folder', name: 60, date: 88, size: 16 },
  { kind: 'doc', name: 120, date: 80, size: 40 },
  { kind: 'doc', name: 104, date: 72, size: 34 },
  { kind: 'folder', name: 84, date: 86, size: 16 },
  { kind: 'doc', name: 112, date: 78, size: 44 },
  { kind: 'doc', name: 92, date: 74, size: 38 },
  { kind: 'doc', name: 126, date: 82, size: 42 },
]

async function script(a: Act<S>) {
  await a.wait(600)
  if (a.layout === 'compact') return copy(a)

  // 1. Pick the update file up off the desktop by its icon
  a.mark('grab')
  const icon = a.rect('desk-icon')
  const file = a.rect('desk-file')
  const grab = { x: icon.x + icon.width / 2, y: icon.y + icon.height * 0.55 }
  await a.move(grab)
  await a.wait(240)
  const off = { x: grab.x - file.x, y: grab.y - file.y }

  // 2. Carry it into the player's storage; the list lights up under it
  a.mark('drag')
  const list = a.rect('drop')
  await a.drag({ x: list.x + list.width * 0.36, y: list.y + list.height * 0.32 }, (at) => {
    a.put({ ghost: { on: true, dropped: false, off, at } })
  }, { duration: 1300, cursor: 'preserve' })

  // 3. Drop: the copy row opens at the top and its bar fills
  a.mark('drop')
  await a.set((s) => ({ up: true, ghost: { ...s.ghost, dropped: true } }))
  await a.wait(500)
  return copy(a, true)
}

// The copy itself, shared by both designs: the bar fills, the row settles,
// a beat to read it, then Cmd+Z takes it back.
async function copy(a: Act<S>, dropped = false) {
  if (!dropped) {
    a.mark('drop')
    await a.set({ up: true })
    await a.wait(500)
  }
  for (const [p, ms] of [[0.25, 650], [0.5, 650], [0.76, 650], [1, 600]] as const) {
    await a.set({ p })
    await a.wait(ms)
  }

  // 4. Read back and checked: the row settles, the check rises beside it
  a.mark('done')
  await a.set({ done: true })
  await a.wait(3000)

  // 5. Cmd+Z takes the copy back; the row closes: back to the start
  a.mark('undo')
  await a.key('cmd+z')
  await a.set({ up: false, ghost: initial.ghost })
  await a.wait(600)
  await a.set({ done: false })
  await a.wait(300)
  await a.snap({ p: 0 })
  await a.wait(300)
}

export default function Hero({ theme }: { theme: Theme }) {
  return (
    <Stage<S>
      width={720}
      height={400}
      compact={{ below: 560, width: 358, height: 300 }}
      initial={initial}
      poster={poster}
      script={script}
      theme={theme}
      accent="var(--ce-accent)"
      keys={{ wide: 'bottom-left', compact: 'top' }}
      cursor={{ at: { wide: { at: 'drop', x: 0.36, y: 0.32 }, compact: { at: 'drop', x: 0.5, y: 0.5 } } }}
      className="up"
    >
      {(s, _rect, layout) => {
        const g = GEO[layout]
        const lifted = s.ghost.on && !s.ghost.dropped
        return (
          <>
            {layout === 'wide' && (
              <div className="up-desk" data-target="desk-file" data-lifted={lifted || undefined} style={{ left: g.desk.x, top: g.desk.y }}>
                <span data-target="desk-icon">
                  <ImgIcon />
                </span>
                <span className="up-desk__name">{FILE}</span>
              </div>
            )}

            <Window
              className="up-window"
              style={{ left: g.win.x, top: g.win.y, width: g.win.w, height: g.win.h }}
              lead={
                <span className="up-lead">
                  <span className="up-nav">
                    <ChevronLeft size={18} strokeWidth={1.75} />
                    <ChevronRight size={18} strokeWidth={1.75} className="up-nav-off" />
                  </span>
                  <span className="up-heading">DAP Neo</span>
                </span>
              }
              toolbar={
                <span className="up-tools">
                  <span className="up-views">
                    <span className="up-view">
                      <LayoutGrid size={15} strokeWidth={1.75} />
                    </span>
                    <span className="up-view" data-on>
                      <List size={16} strokeWidth={1.75} />
                    </span>
                  </span>
                  <Search size={16} strokeWidth={1.75} />
                </span>
              }
              body={{ className: 'up-body', 'data-crop': true }}
            >
              <div className="up-list" data-compact={layout === 'compact' || undefined} style={{ ['--cols' as string]: g.cols }}>
                <div className="up-head">
                  <span>Name</span>
                  <span>{layout === 'wide' ? 'Date Modified' : 'Modified'}</span>
                  <span>Size</span>
                </div>
                <div className="up-rows" data-target="drop" data-drop>
                  <Collapse open={s.up}>
                    <CopyRow p={s.p} done={s.done} compact={layout === 'compact'} />
                  </Collapse>
                  {ROWS.slice(0, g.rows).map((r, i) => (
                    <Row key={i} r={r} k={layout === 'wide' ? 1 : 0.75} />
                  ))}
                </div>
              </div>
            </Window>

            {layout === 'wide' && (
              <div className="up-check" data-on={(s.done && s.up) || undefined} aria-hidden={!s.done}>
                <Icon name="check" size={16} className="up-check__icon" />
                <span className="up-check__text">
                  <span className="up-check__title">SHA-256 matches</span>
                  <span className="up-check__hash">{HASH[0]}<span className="up-check__gap">{HASH[1]}</span>{HASH[2]}</span>
                </span>
              </div>
            )}

            {layout === 'wide' && (
              <DragImage ghost={s.ghost}>
                <ImgIcon />
                <span className="up-drag__name">{FILE}</span>
              </DragImage>
            )}
          </>
        )
      }}
    </Stage>
  )
}

function CopyRow({ p, done, compact }: { p: number; done: boolean; compact: boolean }) {
  return (
    <div className="up-row up-new" data-done={done || undefined}>
      <span className="up-name">
        <ImgIcon small />
        <span className="up-name__text">{FILE}</span>
      </span>
      <States
        value={done ? 'done' : 'up'}
        align="start"
        states={{
          up: <Meter className="up-track" value={p} />,
          done: compact ? (
            <Badge tone="success" className="up-verified" icon={<Icon name="check" size={12} />}>
              Verified
            </Badge>
          ) : (
            <span>Just now</span>
          ),
        }}
      />
      {compact ? <Bar w={40} h={7} tone={2} /> : <span className="up-size">{SIZE}</span>}
    </div>
  )
}

function Row({ r, k }: { r: (typeof ROWS)[number]; k: number }) {
  return (
    <div className="up-row">
      <span className="up-name">
        {r.kind === 'folder' ? <Folder size={18} strokeWidth={1.25} className="up-folder" /> : <File size={18} strokeWidth={1.25} className="up-doc" />}
        <Bar w={Math.round(r.name * k)} h={7} tone={3} />
      </span>
      <Bar w={Math.round(r.date * k)} h={7} tone={2} />
      {r.kind === 'folder' ? <Bar w={r.size} h={2} tone={3} /> : <Bar w={r.size} h={7} tone={2} />}
    </div>
  )
}

/** A page with a folded corner and a dark IMG band: the firmware image. */
function ImgIcon({ small }: { small?: boolean }) {
  return (
    <span className="up-pdf up-img" data-small={small || undefined}>
      <span className="up-pdf__band">{small ? null : 'IMG'}</span>
    </span>
  )
}

/** The drag image follows the cursor on the drag's own frame callback, and
 *  lights whatever [data-drop] it is over. (From the `upload` gold.) */
function DragImage({ ghost, children }: { ghost: Ghost; children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null)
  const over = useRef<HTMLElement | null>(null)
  const following = ghost.on && !ghost.dropped
  const { x: ox, y: oy } = ghost.off
  const { x, y } = ghost.at
  useLayoutEffect(() => {
    const root = ref.current?.closest<HTMLElement>('.ss-stage')
    let next: HTMLElement | null = null
    if (following && root) {
      const box = root.getBoundingClientRect()
      const scale = box.width / root.offsetWidth || 1
      const hit = document.elementFromPoint(box.left + x * scale, box.top + y * scale)?.closest<HTMLElement>('[data-drop]') ?? null
      if (hit && root.contains(hit)) next = hit
    }
    if (next !== over.current) {
      over.current?.removeAttribute('data-over')
      next?.setAttribute('data-over', '')
      over.current = next
    }
  }, [following, x, y])
  useLayoutEffect(() => () => over.current?.removeAttribute('data-over'), [])
  return (
    <div ref={ref} className="up-drag" data-show={following || undefined} data-dropped={ghost.dropped || undefined} style={{ transform: `translate(${x - ox}px, ${y - oy}px)` }} aria-hidden>
      <div className="up-drag__inner" style={{ transformOrigin: `${ox}px ${oy}px` }}>
        {children}
      </div>
    </div>
  )
}

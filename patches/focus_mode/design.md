# Focus mode (auto-hide controls): design and investigation

> **Rebased on the 676-byte theater payload.** The theater variant's
> portrait-sampling change grew its tail payload by 34 bytes, so every focus
> address below moves up by 0x22 (`focus_reset` is now 0x0307C258) and the
> focus payload is 340 bytes (1,016-byte composed tail). `build_focus.py`
> regenerated the twelve hook patches and `test_focus_mode.py` passes all
> four gates at the new base. The tables below record the original 642-byte
> composition.

Status: experimental patch set on the theater variant, in the same
standing as the title pair. Not in the default manifest. Nothing
here changes the default build or any existing variant: the
composed image differs from the theater variant only in the
twelve hook sites, the tail payload extension, and the image
trailer.

Behaviour: while the player window is up, five seconds without a
key press or wheel movement hides the transport row, the progress
bar, the status icons and the volume readout; the cover art grows
from 144x144 to 190x190 and the title and artist move down into
the vacated space. Any key press wakes the player and is
swallowed (it does not also perform its action). Wheel movement
counts as activity but does not wake (the wheel has no key event;
see the key path section).

## Investigation 1: the tick

The player window is module 27 (WIN data 0x030247C4). Its Service
handler 0x0307DFDA runs a housekeeping tail (around 0x0307E1EE):
when the play-state halfword at 0x03023924 is 0 or 3 (playing or
paused), it reads the OS clock through 0x0306672E, and when more
than 40 ticks have elapsed since the word at 0x0304B4C4 it stores
the new time and posts the progress event 0x40 (the BL at
0x0307E20C). A second cadence (more than 25 ticks) posts 0x19D.
That 0x40 cadence is what the progress segments repaint on.

The clock unit is proven, not assumed: the stock screen-off
checker (around 0x030649D4) indexes a table at 0x03005768 =
{10, 20, 30, 60, 300, 600, 0} seconds by the SAVEINFO+0x15
setting and compares idle ticks against the table value times
100. One tick is 10 ms; the clock runs at 100 Hz.

Chosen hook: the BL at 0x0307E20C is replaced by a call to the
focus tick stub, which performs the displaced post(0x40) first
and then does the idle accounting against the same OS clock. The
threshold therefore counts real time (500 ticks = 5 s, the named
constant HIDE_TICKS in build_focus.py) regardless of cadence, and
the stock cadence logic is untouched. Worst-case hide latency
past the threshold is one 0x40 cadence, about 0.4 s, plus one
Display pass. One limitation: the Service tail only runs its
cadence block while the play state is 0 or 3, so in other states
(stopped, seeking) the idle clock does not advance and the player
does not hide. That is the stock cadence's own reach; widening it
is a hardware question (see the gates at the end).

The wheel is polled, not keyed: the key task maintains direction
bytes at 0x03023178/0x03023179 and a total-steps word at
0x0302317C. The tick stub snapshots the total and treats any
change as activity, so scrolling the wheel keeps the controls up
even though no key event fires.

## Investigation 2: the key path

Every key event for the player passes one point: the Key wrapper
at 0x03080AF4. It pushes {r4, lr}, calls the per-key function
0x03061B16 (module 29 code; it maintains playback-state posts
0x1A2/0x1A3/0x1A4 and the hold behaviour and returns an event
word), then tail-branches to the main key handler 0x030800BE, or
to the alternate handler 0x030809A8 when the sleep-state event
0x1A8 is set. Keys are handled per window with switch statements;
there is no key-map table to hook instead.

Chosen hook: the BL at 0x03080AF6 is replaced by a call to the
focus key stub. The stub:

1. Calls 0x03061B16 first, unchanged. Its side effects are
   load-bearing (state posts), and they are not the key action:
   the action lives in the two handlers.
2. Restamps the activity tick and re-snapshots the wheel total.
3. If visible, returns the function's result in r0, so the
   wrapper continues byte-identically.
4. If hidden, clears the hidden flag, posts 0x39 (full repaint)
   and 0x3B (artwork re-request), and swallows the key: it loads
   the wrapper's saved r4 from [sp, #12] and the wrapper's saved
   lr from [sp, #16] (the wrapper pushed {r4, lr} before the
   hook, and the stub's own frame is 12 bytes), restores its own
   saved r5, drops both frames (sp += 20), and returns directly
   to the framework caller with r0 = the event word. Neither
   handler runs, in either sleep state, because the hook sits
   before the 0x1A8 fork.

Design decision, as briefed: a key press while hidden shows the
controls and is swallowed. The alternative (wake and also act)
makes the first press after idle unpredictable, since the user
cannot see the state the action lands in; every mainstream
auto-hide player swallows the waking press. The cost is one
extra press for the first intended action after idle.

## Investigation 3: art geometry and the layout

The painter (module 27, 0x0307EF4E) requests artwork from the
mode-0 segment on event 0x3B, through the request function
0x0307E8A4. The request writes four globals on every call:
0x0302598C = box width, 0x03025990 = box height, 0x03025994 =
destination X, 0x03025998 = destination Y (stock: 144, 144, 23,
36). Module 18 setup (0x0308389E) scales the source to fit the
box preserving aspect (verified by probe: a 5:3 source into a
16-wide box lands at scaled height 9), with the blit X fixed at
the destination X; the scaled height lands in the picture
context at 0x03026CA0+0x18, and the painter consumer 0x03083B36
redraws from the persistent context, so a geometry change
persists until the next request. Re-issuing the request mid-track
is the stock track-change path: post 0x39 (whose repaint block
re-posts 0x3B and 0x3A) and 0x3B. One gate inside the painter:
the request only runs when the word at 0x03023980+0x44 is 0; if a
hide or wake lands while that word is nonzero, the geometry
switch defers to the next request the stock choreography issues
(next track change or view cycle). The state flag itself flips
immediately either way, so the segments and text follow at once
and only the art resize can lag.

Chosen hook: the BL at 0x0307E8DE (the request's call to the
set-source-0 function 0x03083A90, immediately after the globals
are written) is replaced by the focus geometry stub: while
hidden it overwrites the four globals with the focus geometry,
then tail-calls the displaced function with its stock argument.

Layout, from the painter's own coordinates:

| Element | Stock | Focus (hidden) |
| --- | --- | --- |
| Art box | 144x144 at (23, 36), occupies y 36..179 | 190x190 at (25, 8), occupies y 8..197 |
| Title box | (0, 198)-(239, 213) | (0, 232)-(239, 247) |
| Artist box | (0, 223)-(239, 238) | (0, 257)-(239, 272) |
| Progress | time text, track fill (40, 254)-(201, 268), bar | not drawn |
| Transport row | y 275..307 | not drawn |
| Status icons | y 5..24 | not drawn |
| Volume readout | (20, 8)-(50, 20) | not drawn |

Art width 190 is the round size that leaves a 25 px margin each
side ((240-190)/2 = 25) and keeps the box square; the top margin
shrinks from 36 to 8. The text shift is one constant, +34, for
both lines, preserving the stock 10 px gap between the title
box bottom (213) and the artist box top (223): the pair moves as
a block into the space the progress bar (254..268) and transport
row (275..307) vacated, ending at 272 with a 48 px bottom
margin. A taller art (for example 200x200 at y 4) was rejected:
it pushes the art bottom to 204 and compresses the text block
against the progress zone it is supposed to replace.

Text hooks: the title rect is built on the painter's stack at
[sp+0x10] (left, top, right, bottom halfwords) and consumed by
the measure call at 0x0307F9F0 and by the draw and marquee code
after it, so the title hook replaces that measure call: while
hidden it sets the rect top and bottom to 232 and 247, then
tail-calls the measure function. Set, not add: the stock
suffix-trim path can loop back and measure the same rect twice
in one paint, and an add would shift it twice. The artist hook
replaces the renderer call at 0x0307FAA8: while hidden it sets
the rect fields at [r0+2] and [r0+6] to 257 and 272, then
tail-calls the renderer.

Segment gates: each segment to suppress starts with a
test-and-clear call. One shared gate replaces that call at six
sites: status 0x1F (BL at 0x0307F510), progress 0x41
(0x0307F548), 0x40 (0x0307F598) and 0x4D (0x0307F5EA), transport
0x43 (0x0307F7B6), volume 0x19A (0x0307F8F8). While hidden the
gate returns 0 without consuming the event bit, so the segment
is skipped for this paint and redraws fresh on the wake paint;
while visible it tail-calls the real test-and-clear. The gates
sit at segment tests, never at draw sites, which is what makes
this set compose with design refresh v4 in either order. The
progress block posts 0x43 itself when the bar moves; gating the
chain and the row together keeps that consistent. The mode
indicator erase at the head of the 0x43 segment is inside the
gate, so the hidden paint leaves no erase artefacts; the
transition repaint's full-screen draw (the repaint block fills
from the background cell, or draws image 138 in artwork view)
clears what was on screen.

## Investigation 4: the slide verdict

The owner asked for the controls to drop down. A true slide
needs the transport row drawn at increasing y offsets, clipped
at the screen bottom. The evidence:

- The pixel store 0x03063E60 writes two surfaces (rows 0..239
  into the surface at 0x030065A8, rows 240..319 into the one at
  0x0306F224, selected per row) and contains no clip at row 320:
  a blit running past the display height indexes past the second
  surface into adjacent memory.
- The raw blitter 0x0306333E (mode 0x10 loop) has no bounds
  check; its setup 0x03063F10 clamps only the dirty-region
  bookkeeping fields, not pixel writes.
- The cropped-strip draw 0x03063C74 (id, x, y, skip rows, row
  count) clamps skip+count to the image height and calls the
  engine at y+skip: it crops the source, but the destination is
  still unclipped at the screen bottom.
- The row's y is a movw immediate (#0x113) at about ten sites
  inside the 0x43 segment, the same words design refresh v4
  repoints. A slide would need per-site interception of every
  draw, in both glyph generations.
- The only periodic driver available is the 0x40 cadence
  (about 0.4 s), so a 3-step slide takes about 1.2 s, and each
  intermediate frame needs the exposed strip above the row
  repainted; the only erase primitive is the full repaint,
  which resets every segment.

Verdict: ship the instant hide. The slide is a follow-up with
two named unproven points: (a) no clipped draw path exists for
the row at intermediate y, so a slide build must first prove a
clip in the store or draw the row into the row-buffer surface
and blit only the visible part; (b) the per-step repaint cost
of the exposed strip and the 0.4 s cadence make the animation
slow by construction. The demo renders therefore show the two
resting states only; no animation is faked.

## State home

Twelve bytes at SAVEINFO+0x1E4 (0x03023484), inside the verbatim
block (+0x1C7..+0x2D5, round-tripped by the memcpy at
0x0307E15C), immediately after theater's 28 bytes at
+0x1C8..+0x1E3:

| Offset | Field |
| --- | --- |
| +0x00 | u32 last_activity_tick |
| +0x04 | u32 wheel_seen (total-steps snapshot) |
| +0x08 | u8 hidden |
| +0x09 | u8 reserved (slide step counter, unused in this build) |
| +0x0A..+0x0B | padding |

Census evidence: zero u32 literal references to 0x03023484,
0x03023488 or 0x0302348C in any extracted segment (code or
data), and zero SAVEINFO-base accesses with offsets
0x1E0..0x1F3 in a base-tracking scan of every code segment (the
theater census's method; the nearest used verbatim offsets are
+0x1AD below and the battery profile block at +0x290..
+0x2AF). The semantics are RAM-only in effect: the Init hook
resets the state at every player-window entry before anything
reads it (the same argument theater makes for its flags byte),
so the verbatim round trip can never resurrect a hidden flag
into a live session. The reset hook replaces the BL at
0x0307D1A2 in module 27 Init (the post(0x39) that opens the
window's first repaint): the stub performs that post, stamps
activity with the current clock, snapshots the wheel total,
and clears the flag.

## Payload and patch ledger

Tail cap 2,044 B at exec 0x0307BFB4. Theater's payload is
unchanged at offsets 0..641. The focus payload follows at exec
0x0307C236:

| Routine | Exec | Bytes | Hooked from |
| --- | --- | --- | --- |
| focus_reset | 0x0307C236 | 38 | Init BL 0x0307D1A2 |
| focus_tick | 0x0307C25C | 84 | Service BL 0x0307E20C |
| focus_key | 0x0307C2B0 | 72 | Key wrapper BL 0x03080AF6 |
| focus_gate | 0x0307C2F8 | 24 | six segment test BLs |
| focus_geom | 0x0307C310 | 44 | Request BL 0x0307E8DE |
| focus_title_shift | 0x0307C33C | 40 | Measure BL 0x0307F9F0 |
| focus_artist_shift | 0x0307C364 | 40 | Renderer BL 0x0307FAA8 |

Focus payload 342 B; composed tail 984 B (SHA-256
bff7024c12ad5602cac46963fc7e5209dac1be478b359494435f3b298bc71a47);
headroom 1,060 B. Twelve patches (0200..0211 in this directory),
each a 4-byte BL replacement gated on the stock bytes. Manifest:
default 32 + vorbis75 transplant + theater 5 + focus 12 = 49
patches plus the transplant.

Composed variant (build.py with patches/focus_mode/manifest.txt
and --tail patches/focus_mode/focus_tail.bin): SHA-256
43fb27a1dec217c45f4e2fe3c158a6bbd5717d26616f966866434c2e89719938,
13,631,492 bytes. A control build of the theater variant with
the same invocation reproduces
6ad01b38b66f66bb78eed1b2fd3088457b52c0426aefb668a521b8cca92d34a0
exactly, and the focus image differs from it only in the twelve
hook sites, the tail bytes past offset 642, and the trailer.

## Gates

test_focus_mode.py in this directory builds the composed
variant and runs the real patched code under Unicorn, with the
established leaf models (file-read callback and overlay loader
for module 18, the pixel store real and recorded, the text
renderer and the title measure recorded at their entries: the
measure's glyph metrics come from a boot-loaded font resource
the harness does not stage, and what the gates assert is the
rect the painter hands it). All gates pass:

- Gate 0, wiring: all twelve sites in the variant are BLs to
  the assembled stubs; the stock sites are the displaced calls.
- Gate 1, tick and key: the reset stub performs the displaced
  post and initialises the state; the tick stub hides at
  exactly 500 idle ticks and not at 499, posts the repaint pair
  once, stays frozen while hidden, and restamps on a wheel
  total change; the key stub returns the displaced function's
  own result unchanged while visible, and through the real
  wrapper a hidden-state key wakes, posts 0x39 and 0x3B, enters
  neither handler, and leaves r4 and sp exactly restored,
  while a visible key reaches the main handler as stock.
- Gate 2, painter hidden: all six gated event bits are still
  pending after the paint (not consumed); zero segment fill
  calls; the only draw calls are the repaint block's own two
  frame icons (133 at (10, 7), 282 at (176, 5)); the request
  globals read back (190, 190, 25, 8); the title measure and
  renderer calls carry the rect (0, 232, 239, 247) and the
  artist call (0, 257, 239, 272). The stock control paint
  consumes 0x43, runs the transport erase fill (53, 5, 78, 24)
  and the progress track fill (40, 254, 201, 268), draws the
  transport ids at y=275, and keeps the text at the stock
  tops (198, 223). One harness seam: the request's open/probe
  path needs a mounted card volume, which the established
  harnesses do not model, so inside the painter the request is
  observed up to its geometry write (its head, before the
  open); the drawing side of the grown geometry is gate 4.
- Gate 3, wake restores: after the wake key, the next paint
  re-issues the request at stock geometry (144, 144, 23, 36),
  consumes 0x43, redraws the progress track fill and the
  transport row (16,624 recorded pixel stores in rows
  275..307), and the text rects are back at the stock tops.
- Gate 4, interaction with theater: driving module 18 setup with the
  focus geometry preset (as the geometry stub writes it)
  re-arms theater sampling (flags back to armed, the cell
  restored to the theme default at setup), latches
  rows_needed from the grown scaled height (30x18 source:
  scaled height 114 at the 190 box, rows_needed 38; stock box:
  86 and 29), and the finalize writes the derived cell the
  independent port computes over those rows (0x6801 for the
  test fixture at both geometries). Note the cap honestly: at
  a 190-tall scaled image, ceil(190/3) = 64 exceeds theater's
  48-row cap, so sampling covers the first 48 rows, about the
  top quarter, not the full top third. The cap is theater's
  own constant; its files are not modified. For square covers
  at the stock size the cap does not bind (48 of 144 is the
  full third); it binds exactly when the art grows, which is
  the point of this variant. Follow-up, since landed in one
  place: the everything build's theater reassembly raises the
  cap to 64, the full width of the dedup bitmask, gated by a
  tall case in its lifecycle test; the standalone theater
  variant and this variant keep 48 and their pins.

Demo renders are in work/focus_mode/demo/ (render_demo.py):
controls visible beside controls hidden on the derived ground,
dark theme, at the layout numbers above.

## Composition note for the everything build

Composition with the everything build (patches/full/) was
attempted and does not fit. The twelve patches are not the
problem: they touch module 27 sites that no other set uses (the
title pair ends at 0x0307F9EF; the focus title hook at
0x0307F9F0 is the next instruction and does not overlap; the
focus gates sit at the segment tests and the text calls, so the
set composes with design refresh v4 in either order), and
relocation is a reassembly of build_focus.py with a new
FOCUS_BASE, since every stub reference is to a fixed stock
address and the state cell is fixed. The payload's home is the
problem. The stubs are called only from module 27 code, so they
must be resident whenever the player window is loaded, and no
proven 342-byte home with that residency exists in the composed
build:

- A grown module 27 extension: module 27 is the largest window
  overlay (code_exec 0x0307D164, code_len 0x39F0) and its
  segment ends exactly at resident module 18's base 0x03080B54.
  Growth headroom is 0 bytes; an appended stub would land
  inside module 18's live code and be overwritten by its next
  load, and the module 27 load would overwrite module 18's head
  in return.
- The everything build's merged gap tail has 4 bytes spare, and
  its occupants cannot yield the rest: the Bluetooth blob is
  called from the module 0 key dispatcher and must be resident
  from every window, the resolver hook's callers are module 0
  entries, and the theater payload's context is module 18. A
  staging diet freeing 338 bytes needs caps near 1 run and 25
  entries, against the 6 runs and 59 entries the build already
  dieted to from the reviewed 12 and 144; that deletes the
  playlist capacity the staging exists for.
- The module 31 payload spare (636 bytes) is a window overlay at
  the same base: the player load overwrites the span with its
  own code. The module 39 sort cave spare (about 140 bytes) is
  too small, unproven in player residency, and its span is
  refuted above the cave by the resident-home census.

Focus mode therefore remains a standalone variant on the
theater variant, where the tail accounting is theater 642 +
focus 342 = 984 of 2,044. What would change the verdict: a
staging redesign with a second resolver arena (the resolver
census found none), a measured shrink of at least 338 bytes
across the tail's code occupants, or a future proven resident
home. One piece of the composition did land: the everything
build's theater reassembly raises the sampler cap to 64 rows
(see gate 4), so if a home is ever proven, the derived ground
is already correct at the focus geometry.

Second attempt (slack census): the per-module append census the
first attempt had not run was carried out over all 101 load
segments (the full table and per-span verdicts are in
`patches/full/README.md`, focus section). 96 segments have
exactly zero slack. The only previously unpriced span, the
unbounded span above module 39's code end at 0x0309F4AC, fails
the arrival standard: module 39 activates only in library
scan/sort flows, and the player is reachable in flows where it
has never activated, so grown bytes there are not in RAM when
the player's Init first calls the reset stub. Proven new
capacity: 0 B; the shortfall is the full 342 B, and this variant
stays standalone.

## Hardware gates

First flash (Phase E, on the theater variant's own gates too):

1. Hide latency: confirm the roughly 0.4 s worst-case cadence
   lag past 5 s reads as intended, and confirm the Service
   cadence reach in the stopped and seeking play states (the
   idle clock only advances while the play state is 0 or 3).
2. Wake feel: the swallowed first press, and the framework's
   treatment of the stub's return (r0 = the event word, the
   wrapper's own epilogue bypassed by the frame unwind).
3. Geometry restore when the request gate word
   (0x03023980+0x44) is nonzero at the transition: the art
   resize defers to the next stock request; the text and
   segment states do not.
4. BMP covers (the picture-kind path through the same request
   function) at the grown geometry, and non-square covers,
   whose scaled height is not 190 (a 4:3 cover lands at 190x142,
   dest (25, 8), leaving more ground below the art).
5. The theater cap interaction on real covers: at 190 the
   derived ground comes from the top 48 rows; check the ground
   still tracks the cover's top on photographic art.
6. Marquee titles in the hidden state (the shifted rect feeds
   the marquee setup; gate 2 covered the fit path and the
   measure entry, not a scrolling marquee under emulation).

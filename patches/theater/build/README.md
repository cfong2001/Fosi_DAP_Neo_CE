# Theater mode: device integration

> This README describes the standalone theater variant (theater alone in the
> gap tail). The Standard image ships theater mode composed with the other
> tail features by the full build ([`../../full/README.md`](../../full/README.md)).

Status: built as an opt-in variant and validated under emulation.
Not in the default build, and not flashed. The remaining gate is
hardware: first-flash observation of both draw paths (see
"Hardware gates" below).

The player background cell (struct field at 0x03004400) takes its
colour from the track's cover art. A reset stub hooked into the
module 18 artwork setup restores the theme default and arms
sampling at every picture change; a trampoline on the four
artwork bitmap calls accumulates the top third of the rendered
rows as they are blitted; when the top third is complete it
writes the derived colour to the cell and posts the repaint
event (event bit 0x39) so the painter fills the screen with it.

## Pieces

| Piece | Where | Size |
| --- | --- | --- |
| Reset stub | gap tail 0x0307BFB4 | 84 B |
| Blit trampoline (with accumulate and finalize) | gap tail 0x0307C008 | 592 B |
| Setup hook | module 18 code 0x0308389E, patch 0100 | 4 B |
| Bitmap call hooks | module 18 code 0x03083A72, 0x03083A7E, 0x03083B82, 0x03083B94, patches 0101 to 0104 | 4 B each |
| Accumulator state | SAVEINFO+0x1C8 (0x03023468) | 28 B of RAM |

The tail payload is 676 of the 2,044 census-clean tail bytes (642 before the
portrait-sampling change; see [`CANDIDATE.md`](CANDIDATE.md)).
Tail exclusivity: build.py takes exactly one `--tail` payload, so
this variant cannot silently coexist with the Bluetooth shortcut,
lock-screen or playlist tail payloads; those are different
variants and would need a merged payload before they could share
a build with this one. That merged payload now exists: the
unified build in `patches/full/` relocates this payload into a
shared tail alongside the resolver staging, the resolver hooks
and the Bluetooth blob, with its own regenerated hook patches.

## State census

The accumulator needs 28 contiguous bytes (3 u32 channel sums,
2 u32 of row bitmask for up to 48 rows, u16 width, u16
rows_needed, u8 rows_seen, u8 flags). Three candidates were
censused by scanning every extracted module segment (code and
data, all 82 modules plus the decoder overlays) for u32
little-endian references, and by disassembling every code segment
for literal-pool loads and base-relative accesses. The scan
scripts are kept with the run's working papers
(work/theater_integration/census_scan.py, census_struct.py,
census_bss18.py).

Candidate (a), the player struct at 0x030043FC beyond +8:
module 27 accesses only +0x00, +0x04, +0x08 through the base,
but the struct is a shared display struct. Direct field literals
across the firmware hit +0x1C, +0x20, +0x24, +0x34, +0x36, +0x3C,
+0x40, +0x44, +0x50, +0x54, +0x5C, +0x64, +0x68, +0x6C, +0x70,
+0x74, +0x7C, +0x7E, +0x80, +0x84 and +0x8C. The largest internal
gap is +0x0C..+0x1C, 16 bytes. Rejected: too small, and gaps
inside a shared struct cannot be proven unused.

Candidate (b), the player ctx at 0x03026CA0, offsets +0x30..:
+0x30 (0x03026CD0) is the base of a second module 18 structure
(base loads at 0x03083F08, 0x030847FE, 0x03084810, 0x03084816,
0x03084B1A; field accesses +0x0..+0x12). +0x3A (0x03026CDA) is
the base of the tag structure (base loads at 0x03083E80,
0x030849C6, 0x03084A3C, 0x03084CBE and neighbours, 0x03084F5E,
0x03085784; accesses +0x0, +0x1, +0x2). Module 19 data starts at
+0x48 (0x03026CE8) and is densely referenced by modules 19, 20
and 27. Rejected: the whole range is other structures.

Candidate (c), chosen: SAVEINFO verbatim block +0x1C7..+0x2D5.
The SAVEINFO analysis (analysis/saveinfo_and_lock.md section
1.6) proves this block round-trips verbatim through save and
load (memcpy at 0x0307E15C) and names it as the place for a
custom field if a free sub-range is confirmed. The sub-range
+0x1C8..+0x1E3 (28 bytes, 0x03023468..0x03023483) has zero u32
literal references in any segment and zero base-relative
accesses in the SAVEINFO base-window scan of every code
segment; the nearest used offsets are +0x1AD below and +0x2B1
above. The state is volatile by design: the reset stub
reinitialises it at every artwork setup before anything reads
it, so the block's save and load round-trip can never resurrect
stale sums into a live accumulation.

State layout at 0x03023468: sums at +0x00, +0x04, +0x08; row
bitmask at +0x0C, +0x10; width u16 at +0x14; rows_needed u16 at
+0x16; rows_seen u8 at +0x18; flags u8 at +0x19 (1 armed, 2
done, 4 latched); +0x1A spare.

## Hook design

Setup hook (patch 0100): the first two instructions of the
artwork setup at 0x0308389E (`push {r4, r5, r6, lr}`;
`mov r6, r1`) are replaced by a plain branch to the reset stub.
A branch, not a call: a call would overwrite lr, which is
setup's own return address, and the frame the displaced push
saves would then hold the stub's return address instead, so
setup's epilogue would pop a wrong frame. (Both failure shapes
were hit during development and are recorded in the run's work
log; the branch form is the one the lifecycle test validates.)
The stub re-executes the two displaced instructions exactly,
clears the state, sets the armed flag, restores the background
cell to the theme default (dark: immediate 0x10A2; light: the
halfword at palette cell 0x030235B4, matching the player
constructor at 0x0307D1BA) and branches back to the third setup
instruction. It works only in r2 and r3 behind a balanced save;
r0 and r1 (setup's arguments) are untouched.

Bitmap hooks (patches 0101 to 0104): the four artwork bitmap
calls (sync consumer 0x03083A72 and 0x03083A7E, painter consumer
0x03083B82 and 0x03083B94) are repointed to the trampoline. The
fifth call at 0x03083C10 is a different strip draw and is not
hooked. The trampoline pushes {r4 to r8, lr}, saves the
arguments, replicates the two stack arguments (mode, source
pointer) on its own frame, and calls the stock bitmap function
0x0306333E with the original register and stack contract. It
preserves the bitmap return value. Only then, if the state is
armed and not done, the stack source pointer is the row buffer
0x03026A20, the mode is 0x10 and the height argument is 1, it
samples: on the first accepted row it latches width and
rows_needed = ceil(scaled height / 3), capped at 48, from the
player ctx (0x03026CA0 +0x18). The row index is ctx +0x2C read
after the blit; the cursor increments after the blit on the
nonzero-renderer path and not on the zero path, and the sync
consumer blits the final row twice, so a row is accumulated
only if its bitmask bit is clear. Accumulation is
frame_average.c exactly (little-endian halfwords, per-pixel
(v * 255) / 31 and (v * 255) / 63 sums). When rows_seen reaches
rows_needed, finalize computes the rounded averages, mixes 55
percent toward black (dark) or 75 percent toward paper
[242, 237, 230] (light, theme from SAVEINFO +0x2D8), quantizes
with the theme-core rgb565 rounding, stores the halfword at
0x03004400, sets event bit 0x39 (word 0x03023CFC, bit 0x19,
read-modify-write) and sets done.

Assembly: no ARM toolchain is assumed. build_theater.py
assembles both routines with Keystone (Thumb-2; the V8 feature
flag only widens Keystone's gate so UDIV, a Cortex-M3
instruction, assembles, with all other encodings verified
identical), fixes up the two external branches with a local
encoder, and round-trip checks the payload with Capstone:
instruction counts against the source listing, and every branch
target inside the payload, on the bitmap function, or on the
setup continuation. Any mismatch aborts the build.

## Build

Regenerate the payload and patches (deterministic):

    python3 patches/theater/build/build_theater.py

Variant image (default build plus theater, framework
build.py):

    python3 patches/framework/build.py \
        --manifest patches/theater/build/manifest.txt \
        --tail patches/theater/build/theater_tail.bin \
        --output DP3_V137_theater.img

Variant image SHA-256:
6ad01b38b66f66bb78eed1b2fd3088457b52c0426aefb668a521b8cca92d34a0
(72,131 bytes changed vs stock; the default build is unchanged
at 92c446066e715d74a719671d3ee643ed4b7587c94801eb6dc3893f2271ed944d).

## Validation

verify.py check 12 builds the variant in the verify temp dir
and proves its diff against the default build is confined to
the five hook sites, the tail span, the module 0 code_len
record and the trailer CRC, with the workspace zone zero and
the default build still at its pinned hash. Full suite:
12 of 12 checks pass, including all eleven pre-existing checks
against the unchanged default build.

test_theater_lifecycle.py loads modules 0, 18 and 19 from the
built variant and runs the real patched paths under Unicorn.
Only the bitmap leaf (display hardware access), the file-read
callback and the overlay loader are modeled, as in the research
probes; the loader model performs the loader's documented job
(segment copy plus BSS clear) so a second setup sees a fresh
overlay. Every modeled bitmap call is asserted to arrive from
inside the trampoline. Results:

- Painter, dark, 30x18 JPEG fixture: after setup the cell holds
  the theme default 0x10A2 and the state is armed and zeroed.
  After 18 consumer calls the cell is 0x7000, the value the
  independent Python port computes from the first 6 rows
  (average (255, 0, 0), mixed (115, 0, 0)); device sums
  (45900, 0, 0); event bit set; flags 7 (armed, done, latched).
  A 19th call blits once more and changes nothing.
- Painter, light, 16x16 fixture scaled to 9 rows: setup restores
  the planted palette value; after 9 calls the cell is 0xF595
  (average (255, 0, 0), mixed (245, 178, 173)); 3 rows latched.
- Track change: a second setup restores 0x10A2, zeroes the
  state, and a second accumulation reproduces 0x7000.
- Sync consumer, dark: 21 calls produce 19 blits, rows 0..17
  with row 17 blitted twice; the duplicate is rejected by the
  bitmask and the cell ends at 0x7000 with the same sums.
- No-art (reads fail): setup returns 0, the reset stub has
  already restored 0x10A2, and consumer calls accumulate
  nothing; the default stays.
- Accumulate cross-check: the assembled trampoline alone,
  fed 7 random 37-pixel rows plus a duplicate of each, matches
  frame_average.c compiled for the host after every row
  (final sums (31586, 34574, 33076)); all 14 bitmap calls
  carried the replicated (0x10, row buffer) stack arguments.

## Hardware gates

- First flash: observe both draw paths (painter and sync
  consumer) on a real card, including that the derived colour
  appears on the next flagged repaint after finalize.
- BMP and module 20 covers go through the same module 18 setup
  and the same two consumers by construction, so the hooks cover
  them; that is unproven until a BMP fixture runs through the
  lifecycle test or on hardware.
- Posting event bit 0x39 from the consumer's execution context
  is proven under emulation only; on hardware, confirm the
  painter picks it up without a lost wakeup.
- The reset stub runs at every artwork setup, including setups
  issued for non-player picture uses of module 18; on hardware,
  confirm no other picture consumer depends on the background
  cell keeping a value across a setup.

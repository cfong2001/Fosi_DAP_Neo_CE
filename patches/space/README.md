# Resident space: dead-code census of module 0

New features are limited by resident exec space, not by file size (see
[`../framework/space_budget.md`](../framework/space_budget.md)). Module 0
is the resident image: code there runs from every window. The earlier
census ([`resident_home.md`](../../analysis/resident_home/resident_home.md))
looked for zero runs and stub pockets and found them exhausted. This one
looks for whole stock routines that nothing can reach.

## Result (Standard image)

| | Runs | Bytes |
|---|---|---|
| Module 0 stock code | | 171,028 |
| Reached by recursive descent from all roots | | 156,122 |
| Unreached, nonzero | 301 | 14,338 |
| **Tier 1:** begins with `PUSH {.., lr}` | 80 | **4,150** |
| **Tier 2:** clean leaf code with a return (for example unused DMA register setters) | 70 | **4,358** |
| Data or referenced from inside (not counted) | 151 | 5,830 |

**8,508 bytes in 150 pockets.** They're fragmented:

| Pocket size | Pockets | Bytes |
|---|---|---|
| 8 to 31 | 57 | 1,144 |
| 32 to 63 | 42 | 1,834 |
| 64 to 127 | 39 | 3,310 |
| 128 to 199 | 8 | 1,304 |
| 200 to 256 | 4 | 916 |

`census.json` lists every run; `coverage.json` holds the emulation gate.

## Method

[`census_dead.py`](census_dead.py) works on the built image, so CE's own
hooks count as callers. It runs in about a second.

- **Roots, deliberately liberal:**
  - module 0's vector table;
  - every raw-decoded BL, B.W, B, Bcond and CBZ target in every core-0
    code segment, at that segment's own exec base;
  - every 32-bit value at any 2-byte offset of any core-0 segment that
    lands in module 0 code (literal pools, pointer tables, window structs);
  - MOVW/MOVT pairs and ADR targets.
- **Coverage:** recursive descent that follows branches. It tracks IT
  blocks itself, because one-instruction-at-a-time decoding turns
  `bxeq lr` into `bx lr`; that bug produced three false positives before
  it was fixed. It walks TBB/TBH tables bounded by the preceding `CMP`
  and marks literal-pool words as data.
- **Candidates:** unreached runs with no reference to any address inside
  them.

The emulation gate is [`run_coverage.py`](run_coverage.py). It reruns
the repository's Unicorn suites (BT UART, DAC filter, BT auto-off, EQ,
the gapless transition rig, the screens test, the keyed transport) with
a coverage hook on every Unicorn instance. It fails if any candidate
byte executes.

- **Result:** 3,329 distinct module 0 instruction addresses executed, and
  none inside a candidate.
- **Earlier catch:** the gate is what caught the IT-block bug.

## How strong is this

- **Static.** A routine is missed as live only if it is entered through a
  register value that no literal, table, MOVW/MOVT pair or branch
  anywhere in core-0 code produces, or through a jump table whose bound
  is not the preceding `CMP`. The stock code is compiler output, where
  both are rare.
- **Emulation.** The suites cover a few percent of module 0, so the gate
  catches census bugs on the paths they exercise. It is not a proof of
  deadness.
- **Hardware.** Before any feature lands in a pocket, a tripwire build
  should replace each candidate's first instruction with a branch to a
  small reporter. The reporter stores the address in a spare SAVEINFO
  byte and halts with a visible screen. A day of normal use (browse,
  play every format, USB, settings, Bluetooth, update menu) on that
  build is the proof that matters.

## What it changes

| Need | Bytes | Fits in pockets? |
|---|---|---|
| Text smoothing in the glyph blitter | about 200 | Yes: one 220 to 256 B pocket |
| Focus mode stubs | 340 | Yes, split across pockets (resident everywhere, so the module 27 residency problem goes away) |
| Lock-screen routine (now in module 31) | 406 | Yes, split; frees module 31 window space |
| Bluetooth blob (now in the tail) | 436 | Yes, split; frees 436 B of contiguous tail |
| Browser marquee v5 | 6,992 | No. Larger than all pockets of 64 B or more combined (5,530 B), and it is one linked blob |

The marquee remains a feature trade. Everything else on the waiting
list fits without dropping a shipped feature, once the tripwire build
has run on hardware.

## Rerun

    python patches/space/census_dead.py [IMAGE] [--json patches/space/census.json]
    python patches/space/run_coverage.py [--json patches/space/coverage.json]

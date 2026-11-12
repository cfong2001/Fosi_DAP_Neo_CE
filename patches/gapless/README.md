# Gapless fast path (v2)

Shipped armed in both images. When a FLAC track ends and the next file is
also FLAC, the decoder core stays loaded and running and takes the next
file's open directly. There is no image copy, no core reset and no boot
handshake.

Only FLAC takes this path. Rockchip's RKNanoD SDK restarts the decoder core
for every file (`StartBBSystem` holds it in reset, copies the module and
waits 5 ms), and the core-1 harness has proven only the FLAC decoder
accepts a second file without that reset
([`../harness/milestone2.md`](../harness/milestone2.md)). Every other format
halts and reloads the decoder exactly as stock does. An earlier build
also shortened the DAC bus I2C controller's reset hold from 1 ms to 50 µs
(patch 0019); the SDK's I2C driver holds it for `DelayMs(1)`, as stock
does, so that patch was removed.

This shortens the track change; it does not make it sample-exact. The
decoder still opens the next file after the last buffer of the old one has
played, so a short silence remains.

## Measured in the transition rig

[`rig/test_transition.py`](rig/test_transition.py) runs the system core's
real end-of-track code under Unicorn with a virtual clock. It measures from
the playback task taking the end-of-track event (`0xEC`) to the I2S DMA
restart. The model assumes a 0.05 ms decoder reply, 8 MB/s module loads,
0.11 ms per DAC I2C write and a 120 MHz system clock.

| Transition | Stock | CE v1 (first armed release) | CE v2 |
|---|---|---|---|
| End of track, FLAC to FLAC | 20.5 ms | about 27,500 ms (stall) | 11.4 ms |
| User NEXT, FLAC to FLAC | 23.2 ms | about 27,500 ms (stall) | 23.2 ms (full reload, as stock) |
| End of track, FLAC to APE | 20.3 ms | 20.3 ms | 20.4 ms (full reload) |
| End of track, APE to APE | 20.3 ms | n/a | 20.3 ms (full reload: FLAC-only fast path) |

Where stock spends its 20.5 ms: a 33.7 KB decoder reload, `delay_ms(5)`
and the core-1 boot inside the reset-and-start routine, and seven DAC
register writes. Each of those writes re-initialises the I2C controller
behind a 1 ms reset hold, which CE keeps: that is most of the 11.4 ms
left on the FLAC fast path. The 80 ms settle the v1 design cut runs after
the I2S restart, so it was never part of the gap.

The figures leave out two costs. Core 1 opens the next file and decodes
its first frame in parallel with the waits counted here. The playback task
also takes time to notice the event. Both need hardware.

## The v1 defect

Every track change goes through `0x03089AD6`, and its shutdown step
(`0x030893C4` → `0x0306CB0C`) holds core 1 in reset (CRU soft reset `0x32`)
and gates its clock. The v1 gate skipped the reset-and-start body whenever
the decoder module matched, which left a halted core in place. The next
`0x65` open exchange then ran to its cap (about 5.5 s) and the info wait to
its cap (about 22 s). Load-start then started I2S on a buffer nobody
refilled. This hit every same-format natural advance and user skip. The
core-1 harness ([`../harness/milestone2.md`](../harness/milestone2.md))
could not see it: it runs only the decoder core.

## Patches

| Patch | What it does |
|---|---|
| 0020 | State word: retained decoder module |
| 0021 | Hook at `0x0306CB2C` (reset-and-start) into the gate |
| 0022, 0025 | Gate: skip the body only if core 1 is running (`[0x03004138]`, cleared by every halt) and the module matches |
| 0023 | Literal `0x03004138` for the gate |
| 0024 | Decoder shutdown rewritten in place: on a natural advance (`r5 == 0`) of a FLAC track (codec 6), close the decoder's file but do not halt core 1; every other case halts as stock does |
| 0026 | Arms the gate's module compare |

User skips and stops still halt core 1, and the gate then falls back to the
full stock reload. So does every natural advance from a format other than
FLAC, a codec change, or any other program that halts core 1 (module 61). Bytes and their disassembly come from
[`tools/assemble_v2.py`](tools/assemble_v2.py).

## Verify

    python patches/gapless/rig/test_transition.py [CE_IMAGE]

This runs the three transitions on stock and on the CE image, plus an APE
to APE advance on CE, which must halt and fully reload. It also runs
two mutations of the CE image. Reverting 0024 must fall back to a full
reload. Reverting 0024 and removing the gate's core-1 check (the v1 logic)
must time out. Run time is about one second.

## History

- [`gapless_patch.md`](gapless_patch.md): the v1 design as first delivered.
  Superseded.
- [`../../analysis/gapless.md`](../../analysis/gapless.md): the stock
  track-transition path.
- `verify_gapless.py`: v1's static verifier, kept for the record. It uses
  v1's patch numbering and paths.

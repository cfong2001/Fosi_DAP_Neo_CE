# Row drawing engine

Original CE code informed by the reference SDK's bitmap, text-mode and
resource-read contracts. No SDK implementation is copied. Six resident
entry points try bounded direct framebuffer paths, then resume the exact
stock instructions on rotation, unsupported display bank, unsupported
format, zero dimensions, overflow or off-screen geometry.

- Inclusive foreground and explicit-color rectangle fills write rows.
- RGB565 RAM images copy rows without the pixel setter.
- Transparent images handle both 0x0000 and 0xF800 keys, opaque-black mode,
  and monochrome recoloring exactly as the stock keyed path does.
- The 1-bit path used by glyphs outside the smoothed set writes each row,
  preserving reverse and transparent text modes.
- The screen clear uses a bounded fill.
- Unrotated 240×320 flash backgrounds read directly into the two physical
  framebuffer spans: 240 rows at 0x030065A8 and 80 at 0x0306F224. The
  existing resource reader still performs the RGB565 byte swap. There is
  no full-screen temporary allocation. Partial images retain the stock
  flash reader and benefit from the RAM row blitter.

The display is not one contiguous 240×320 buffer. The implementation and
tests preserve this split, the dirty-row bounds, the final write window,
its cursor and the callee-saved registers. Stock SetWindow clamps a y
endpoint at or above 240 to 319; fast paths preserve the resulting cursor
quirk. Keyed mode 0 leaves the window at its last inked pixel; modes 1 and
2 leave it at the last visited pixel, even if transparent. These details
were found by executing stock code, not assumed from the older SDK.

Unsupported shapes resume stock via saved prologues; the original
routines remain present. The byte patch builder pins every allocation to
stock bytes and bounds each section within an existing unreferenced code
pocket. No new persistent RAM, module growth or audio-path changes.
`build_rows.py` lists the exact homes; `patches/framework/space_budget.md`
records them as allocations.

`test_rows.py` executes stock and fast code in Unicorn and compares every
framebuffer byte and all 40 bytes of display context. It checks split
rows, edges, transparent keys, draw modes, randomized rectangles,
rotation fallbacks, source-buffer preservation, stack/register ABI,
write bounds and direct flash destinations. Instruction counts for the
representative 64×64 / 16×16 cases:

| Case | Stock | CE | Reduction |
|---|---:|---:|---:|
| Rectangle | 189166 | 25818 | 86% |
| RGB565 image | 189179 | 25914 | 86% |
| Keyed image | 279921 | 70973 | 75% |
| 1-bit glyph | 27277 | 6346 | 77% |

These are emulated instruction counts, not measured frame rates or
battery-life claims. Hardware display timing remains untested.

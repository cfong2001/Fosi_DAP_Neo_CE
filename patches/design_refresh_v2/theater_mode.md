# Theater mode: reverse engineering and design

## Status

Built as an opt-in variant: see
[patches/theater/build/](../theater/build/README.md). The design
in part (b) below is the earlier constructor-helper proposal and
is superseded by the integration as built, which follows the
artwork-trace research in patches/theater/research/: a reset stub
hooked into the module 18 artwork setup restores the theme
default and arms sampling, and a trampoline on the four artwork
bitmap calls accumulates the top third of the rendered rows from
the row buffer, writes the derived colour to the background cell
at 0x03004400 and posts the repaint event. The averaging and
colour finish are the ones pinned here (top third, dark mix 55
percent toward black, light mix 75 percent toward paper, RGB565
quantisation). Accumulator state lives at SAVEINFO+0x1C8 inside
the verbatim block, on the census evidence recorded in the build
README. The variant is validated under emulation end to end and has now
booted on hardware. Embedded artwork and the cover-derived black background
were observed during MP3 playback; broader cover and window-path coverage
remains.

One visible artifact on the derived ground is settled, and it is
not the mechanism's fault: the transport glyphs carry their stock
ground baked into their bitmaps, and their draw path has no
transparency. Design refresh v4
([patches/design_refresh_v4/design_v4.md](../design_refresh_v4/design_v4.md))
records the instruction-level evidence and the call-site change
that would unlock transparent glyphs.

## Correction: decoded-image buffer is not pinned

The claim below that the call at `0x03085AA8` fetches picture data and
that `[ctx+0x18, ctx+0x10)` brackets a bitmap is **withdrawn**. The
callee at `0x03080B54` loads two 32-bit values from `0x0302598C` and
`0x03025990`, orders them according to `r2` and `r3`, writes the two
results through `r0` and `r1`, and returns a comparison result. It does
not fetch or decode image data. In module 19 the caller passes addresses
`ctx+0x0C` and `ctx+0x10`; the first is then compared with 320. Later,
`0x030860EA` sign-extends a halfword and `0x030860EC` stores it at
`ctx+0x18`. That last value cannot be a pointer into the device SRAM
range used by the supposed bitmap. The arithmetic at `0x03085ABE` is
therefore insufficient evidence for a bitmap range. Do not use the hook
or averaging loop proposed below until a real pixel buffer, dimensions,
stride, byte order and lifetime have been independently pinned.

`tests/test_dimension_helper.py` executes the helper with synthetic small
values and checks both ordering paths. This is a scalar-contract test, not
an end-to-end cover decode. The instruction and field findings above are
from the hash-pinned stock V137 image.

`patches/theater/frame_average.c` provides a bounded, freestanding RGB565
top-third streaming averaging routine, with explicit byte order, and host
tests. It is an algorithm component only: it has no firmware hook,
does not select pixel geometry, and is not included in a firmware build.
Its callers must not infer those inputs from the invalid context fields.

## Contrast and text revision

The studio now includes a **preview only** theater mode. It averages the
top third of local artwork's rows, rounding up for a partial third, ignores
transparent pixels, mixes the sampled color 55% toward black in dark mode
or 75% toward the v2 paper color in light mode, and quantizes the result
to RGB565. It uses white text in dark mode and black text in light mode,
matching the stock text palette, with a one-pixel edge in the opposite color.
For the sampled RGB565 ground this guarantees at least 4.5:1 contrast
for the text fill; the contrasting edge is 21:1 against the fill. This is
not a guarantee for arbitrary artwork or UI elements underneath the text.
If the entire top third is transparent, the preview falls back to the
current theme background while still displaying the artwork.
The preview's transport symbols use inline vector paths so system emoji
substitution cannot turn the controls into colored boxes. The stock device
font has not been replaced or validated by this browser preview.

The statement below that the traced paths have no alpha blending is still
true, but it must not be read as saying that text needs an opaque box.
The text renderer's mode 1 is a **one-bit transparent glyph mask**: set
bits use the pen color and clear bits leave the destination unchanged
([renderer study](../ui_features/renderer/renderer.md)). This is not
per-pixel alpha. A device implementation could draw the same glyph at
the eight neighboring pixel offsets in the opposite pen color and then at its intended
position in the selected foreground, restoring the pen and mode afterward.
That remains a proposal: clipping, spacing, repaint order, transient text
state, cost and the resulting native-size legibility need to be verified
in the actual player renderer before this can be emitted as a patch.
The offline preview is not an executable firmware feature.

Color contrast and transparency tests run with
`node --test tests/theater-core.test.mjs`. See `docs/theater-core.mjs` for
the preview algorithm and its RGB565 quantization.

Theater mode means the player background takes its colour
from the track's cover art. Part (a)
traces the player background cell the theme census left
unresolved and establishes how cover art reaches the screen
today. Part (b) designs the feature on what part (a)
proves. The mocks are theater_sheet.png (dark and light),
compositions built from a synthesised cover, its measured
average colour, and real v2 asset renders.

## (a) Reverse engineering

### The writer of the player background cell

**Found.** The cell at 0x03004400 is not a lone cell. It is
field +4 of a struct at 0x030043FC in module 0's data
segment (data base 0x03004000, struct offset 0x3FC), which
is why no literal for 0x03004400 exists anywhere: every
access goes through the struct base. Five literal references
to 0x030043FC exist in the whole firmware, all of them in
the player window module (extractor manifest module 27,
code 0x0307D164 to 0x03080B54).

The only store to field +4 is in the player window
constructor at 0x0307D164, at 0x0307D1CA
(`strh r0, [r4, #4]` with r4 = 0x030043FC). What it writes
depends on the theme byte (SAVEINFO +0x2D8):

- Dark theme (byte 0): the immediate 0x10A2, loaded by the
  movw at 0x0307D1C2 (bytes 41 f2 a2 00, file offset
  0x87686). The dark player background is a hard-coded
  constant, the same UI grey as the stock bars.
- Light theme (byte nonzero): the halfword at palette
  cell 0 (0x030235B4), loaded through the pool at
  0x0307D294. The light player background tracks the
  palette background.

The constructor also initialises field +0 to 0 and field
+8 to 0x1F40 (8000). Field +0 is read by the window's main
painter (0x030809B6); its role was not needed here and is
not guessed.

The reader is the background painter at 0x0307EF4E:
`ldrh.w r0, [r8, #4]` at 0x0307EFA8 (r8 = the struct base),
then a full-screen rectangle fill (0, 0) to (239, 319)
through the fill at 0x030632FA with the value as its stack
argument. Two facts about that painter matter for the
design:

- The fill happens only when the SAVEINFO byte at +0x1A is
  nonzero (`ldrb.w r0, [sl, #0x1A]` at 0x0307EFA2, sl =
  SAVEINFO base). When the byte is zero, the painter draws
  image 138, the no-media art, full-screen instead
  (`bl 0x03063700` with id 0x8A at 0x0307EFBE). The byte's
  own writer and its global meaning were not pinned in this
  pass (the census lists +0x1A among screen-off
  candidates); its role in this painter is proven at
  instruction level and is all the design relies on.
- The fill reads the cell on every repaint. Whatever wrote
  the cell most recently is what the next repaint shows.
  There is no caching to defeat.

So the census's open item closes with a useful shape: the
dark value is a constructor immediate (a patchable site,
now in the registry proposal), the light value already
follows the palette, and the cell is rewritten at window
construction and read at every repaint.

### How cover art reaches the screen today

Source: the picture embedded in the audio file. Module 18
is the metadata parser; its strings prove it handles ID3v2
APIC frames, FLAC METADATA_BLOCK_PICTURE blocks and
Vorbis comment PICTURE blocks, and accepts image/jpeg,
image/jpg and image/bmp.

Decode: module 18's data segment holds two entry pointers
into the worker overlay window at 0x03085A4C (0x03085A4D
and 0x03085A67, at module 18 data +0x20 and +0x24). Two
workers share that window with the same dispatcher shape
(command minus 6, table branch): module 19 (10,544 bytes
of code, 64,288 bytes of BSS) and module 20 (2,712 bytes).
Module 19's picture handler (dispatcher case at
0x03085A80):

1. Calls module 18 at `0x03080B54` from `0x03085AA8` to order
   two global scalar values into context fields. It does not fetch
   picture data; see the correction above.
2. Rejects the picture when a dimension field at context
   +0xC exceeds 0x140 (320).
3. Calls its decode routine at 0x03085DAC, which reads
   signed width and height halfwords from the picture
   header, caps them at 0x1F40 (8000), and computes block
   geometry with (n + 7) >> 3 terms: a block decoder with
   a power-of-two downscale ladder, the standard JPEG
   decode shape.
4. On return, calculates `([ctx + 0x10] - [ctx + 0x18]) >> 1`
   and stores it at `ctx + 0x2C`. These operands are not established
   bitmap pointers; the signed-halfword store to `ctx+0x18` refutes
   the prior pointer interpretation.

Module 19 calls file and memory services in module 0 and
no display primitive. Decoded pixels leave through the
buffer, not through a draw.

Display: the earlier identification of `0x030640BC` and `0x0306411A`
as image routines is withdrawn. Their instructions search and modify
lists associated with the playback context; they have not been proven
to draw artwork. The actual player uses a separate module-18 context
and row buffer from the other window's JPEG consumer. The original
bitmap-bracket interpretation is invalid. A later
emulation of the stock JPEG worker with a generated 30 × 18 image found
little-endian RGB565 rows written into a reused buffer at `0x03027DA8`.
The same fixture scaled into a 16 × 16 target exposed different target
and scaled dimensions. A player-path probe draws nine rows for that
fixture and identifies its top three, but other orientations and error
paths remain open. Missing-file and decode-setup failures can leave old
row bytes in memory. The probe, its limits and the outstanding
reset and repaint work are in [`research/README.md`](../theater/research/README.md).
The proposed decode-side hook below is not yet an installable patch.

## (b) Design

### Mechanism

The following remains a proposal, not implemented firmware. A future
averaging step needs a separately verified pixel buffer and lifecycle:

1. Once the actual pixel buffer and geometry are pinned, average every
   pixel in the first `ceil(height / 3)` rendered rows. The current
   proposed `[ctx+0x18, ctx+0x10)` range is invalid; see the correction
   at the top of this document.
2. Theme-adjust the average. Dark theme: mix 55 percent
   toward black, so text in the paper colour keeps its
   contrast. Light theme: mix 75 percent toward the
   scheme paper, so text in the ink colour keeps its
   contrast. Quantise to RGB565.
3. Store the result to the struct field at 0x03004400 and
   set a valid flag (see placement below).

The next repaint of the player background painter fills
the screen with the derived colour, and the cover, title
and controls draw over it in the ordinary stock order.
Nothing about the fill path changes: it already reads the
cell every time.

### The constructor problem, and its fix

The constructor writes the cell at window construction,
which can happen after the decode (open the player on a
track already playing) and would erase the derived colour.
The fix is at the same site the census missed: replace
the constructor's theme block (the cmp/itee sequence at
0x0307D1BA to 0x0307D1C9, 12 bytes) with a branch to a
helper in the player window's own segment extension. The
helper returns the stored derived colour when the valid
flag is set, and otherwise returns exactly what the stock
code would have written (0x10A2, or the registry-approved
panel value, in the dark theme; palette cell 0 in the
light theme). A branch is 4 bytes; the remaining 8 bytes
of the block are the helper's local landing pad. Both
themes take the same path after the fix, which also makes
the light theme's theatre behaviour identical in shape to
the dark theme's.

### Placement and price

| Piece | Size | Home |
| --- | --- | --- |
| Averager (top-row sampling, accumulation, theme mix, quantisation) | Not yet measured | Placement depends on the verified pixel buffer and its lifetime |
| Constructor helper (valid check, default fallback, palette load) | about 40 B, plus the 4 B branch at the site | Grown player segment extension, same class as the module 31 and 32 extensions in the space budget |
| Derived colour cell + valid flag | 3 B of RAM | Placement not yet censused: candidates are padding after the struct at 0x030043FC or a field in module 33's picture descriptor once its layout is pinned |

Nothing is taken from the homes that are already full:
the gap tail has 4 bytes spare, module 0's caves 8, the
sort cave about 140 in the wrong residency. Two grown
overlays are the honest price, and both extensions join
the Phase E window-cycle soak list: the worker overlay
because it is loaded per picture, the player extension
because the constructor runs at every window entry.

### Fallback when there is no cover

The averager writes nothing when there is no picture or
the decode fails, and the valid flag stays clear, so the
constructor helper returns the stock default: the player
looks exactly as it does today. The no-media art keeps
its present role on the other branch of the painter: when
the +0x1A gate is closed the painter draws image 138
full-screen instead of filling, so a track with no cover
on that path is stock behaviour end to end, not a new
screen. The v2 no-media redraw (icon_set_v2 asset 138 and
304) is what that branch shows.

### The layout, and what the painters can express

The stock painters offer flat rectangle fills, image
draws, and text in palette colours. There is no alpha
blending and no gradient fill anywhere in the traced
paths, so the design uses none:

- The derived colour fills the whole screen (the existing
  fill). No scrim is drawn over the cover: a scrim would
  need a second derived colour, and the firmware has one
  cell. Legibility is protected by layout instead: the
  cover sits in the upper area at 160x160 with a 2 px
  frame in the current foreground colour, and the title,
  artist, progress and transport all sit on the flat
  derived ground below it, never over the art.
- Progress is the palette line colour as the track and
  the palette accent as the elapsed part, both existing
  cells, drawn as flat rects exactly as the stock painter
  draws its bars.
- Text takes the palette foreground for its theme. The
  theme-mix percentages in the mechanism are the legibility
  budget: they are chosen so mid-tone covers land at a
  ground the foreground clears comfortably in both themes.

Theater sheet: theater_sheet.png shows the dark and light
forms at 2x. The synthesised cover averages to (57, 67,
72); the mechanism's rule derives cell 0x1925 (24, 36, 41)
for the dark theme and 0xC617 (198, 195, 189) for the
light theme. Both mocks use real v2 keycap renders for the
transport and the v2 battery and lock at their stored
descriptor positions. They are compositions, not captures.

### What would settle the remaining questions

1. Trace a known image through module 19 to locate the actual decoded
   pixel buffer and establish its width, height, stride, pixel format,
   ownership and lifetime. The context pair is not a bitmap bracket.
2. Census 3 bytes of RAM for the derived cell and flag,
   per the placement table.
3. Phase E, on hardware: confirm a repaint follows cover
   decode on a track change. The painter model is
   event-driven (lock-screen work); if no repaint posts,
   the derived colour appears at the next natural repaint,
   one event late, and the hook should also post the
   repaint. That is a hardware observation, not a design
   change.

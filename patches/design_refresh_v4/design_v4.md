# Design refresh v4: transparent player glyphs

## Status: built, experimental and opt-in

The transport glyphs are transparent now, through the route the
earlier negative result pointed at: the painter's transport draw
calls are repointed to the keyed helper, and the glyph family is
redrawn with the key colour as its surround. The eight repoint
patches and the art are an experimental set, not part of the
default manifest, with the same status as the title-copy pair in
patches/theater/text. Everything below the status section keeps
the original evidence (why the stock path cannot key), then gives
the corrected call-site census, the repoint, the emulation gates
and their results, and the art specification.

Files in this folder:

- `patches/`: the eight repoint patches (framework format).
- `manifest-v4.txt`: the default patch set plus the eight
  repoints, for the validation build below.
- `v4-glyphs.json`: the art as theme-config runs for build.py.
- `generate_glyphs.py`: the deterministic glyph generator.
- `icon_set_v4/`: the 54 resources and `mapping.json`.
- `sheets/`: contact sheets (stock vs v4 at 3x; v4 at native size
  over dark and light derived grounds).
- `test_keyed_transport.py`: the emulation gates.
- `prove_keying.py`: the original keying proof, unchanged.

## Why the stock path cannot key (the negative result, kept)

The player painter is module 27, `FUN_0307ef4e` at 0x0307EF4E.
`DrawImageAt` (0x0306354A) and `DrawImage` (0x03063700) both
resolve the resource descriptor and call the blit engine at
0x03063444, which stores the constant mode 0x10 twice on the
stack (0x03063484 and 0x030634F0) and calls the bitmap function
at 0x0306333E with it. Two properties decide the question:

1. The pixels the blitter sees are true RGB565 colour values.
   The staging copy at 0x030640A6 finishes by tail-calling
   0x03056B94, which byte-swaps every halfword of the staged
   buffer in place. Resource pixels are stored big-endian in the
   image file; after staging they are in the colour domain the
   screen uses, so a key colour has to match in that domain.
2. In mode 0x10 the blitter stores every pixel. The inner loop
   at 0x03063390 is `ldrh r0, [r5], #2` followed immediately by
   `bl 0x03063E60`; there is no compare against any value
   anywhere in the loop. The store function at 0x03063E60 writes
   its colour argument unconditionally; its only early return
   tests a display-gate state field, never the colour.

The bitmap function's mode 1 does not help: it is a
one-bit-per-pixel mask path with two pen colours (context at
0x0302385C), which is how text gets its transparency. It cannot
carry a colour icon, and the image engine never selects it.

The stock art bakes its ground in. The dark transport resources
have corner colour 0x10A2, the stock dark player ground they
were authored against: the keycap variants carry 168 such pixels
of 1024 around the cap, the bare variants 821 to 948. On any
other ground (the light palette, a theater-derived colour) the
full 32 by 32 rectangle shows as a chip. No transport resource
contains a 0x0000 or 0xF800 pixel, so no existing key could have
applied even on a keyed path.

## The keyed path the transport row never called

A sibling blitter at 0x0306373C, reached through the staging
wrapper at 0x0306387C, does chroma keying. Its third stack
argument selects a format:

- Format 0 skips a pixel equal to 0x0000 or to 0xF800.
- Format 1 skips 0xF800 only. The pixel-zero test at 0x030637E6
  branches to the store call at 0x030637EE, so black pixels are
  drawn; the 0xF800 compare at 0x030637E8 branches past the
  store.
- Format 2 draws the palette foreground halfword at 0x030235B6
  for every pixel except 0xF800: a one-colour silhouette.

Three helpers resolve a resource id through the same descriptor
table and call the wrapper: 0x03063A08 (format 1, stored on its
stack at 0x03063A18), 0x030639A8 (format 1) and 0x03063C74 (a
cropped-strip variant). Stock precedent: the play-mode indicator
(resources 286 to 289, light 452 to 455) carries a 0xF800
surround (331 of 432 pixels in resource 286) and renders through
helper 0x03063A08 at (53, 5), so the surround never lands.
`prove_keying.py` proves the behaviour on real module 0 code:
eleven cases, including the helper emitting 101 of 432 pixels
for resource 286 with all 331 key-red pixels skipped, and
DrawImageAt emitting 1024 of 1024 pixels for resource 159
including all 168 surround pixels.

## The transport call sites, corrected

An earlier draft of this document tabled seven call sites at
0x0307F426 and nearby addresses. Those bytes are not draw calls
(they are stores, branches and one call to DrawImage 0x03063700
in a different segment); the table was wrong and is replaced.

The transport row is drawn by the event 0x43 segment inside the
painter, entered at 0x0307F7B4. It makes eight DrawImageAt
calls, all at y = 275. Two state bytes drive it: A at 0x0302314A
and B at 0x0302314B; the play state is the halfword at
0x03023924; the play mode is SAVEINFO +0x61.

| Call site | Resource drawn | Position |
| --- | --- | --- |
| 0x0307F806 | B + 0x9B (155 + B) | (0, 275) |
| 0x0307F832 | 168 or 169, by the play cell | (104, 275) |
| 0x0307F840 | 178 (quote) | (154, 275) |
| 0x0307F85A | 179 (info) | (204, 275) |
| 0x0307F874 | 180 (plus) | (104, 275) |
| 0x0307F884 | play mode + 0xAE (174..177) | (54, 275) |
| 0x0307F8A8 | A + 0x9C (156 + A) | (4 + 50 * ((A - 1) mod 5), 275) |
| 0x0307F8F0 | 159 or 167 by the play cell, or play mode + 0xAA (170..173), or 181 | (computed, 275) |

The segment also erases the mode-indicator area with the ground
(fill at 0x0307F7E6, (53, 5), 78 by 24) and draws the mode
indicator through the keyed helper, before the row draws.

One discovery changes what the first site means. Resources 155
and 156 are not icons: they are pre-rendered row composites,
240 by 32. Resource 155 shows chevron, previous, play, next,
chevron; resource 156 shows chevron, a repeat variant, minus,
quote, info (light themes: 321 and 322). When B is 0 or 1 the
segment draws the whole row from the composite; the individual
glyph resources appear when B is 2 or more, and at the centre
slot (site 0x0307F832) in the B = 0 state, where play and pause
overlay the composite. Neither stock composite contains any
0xF800 pixel, so the repoint alone rendered them pixel for
pixel identically. The keyed redraw of the composites is part
of the glyph set below; which of their slots it leaves empty
follows from the overlay behaviour in the segment: on the
B = 0 path the centre overlay always fires (the cbz at
0x0307F80C), and on the B != 0 path the play-mode repeat
family always draws at slot 1 (site 0x0307F884).

## The repoint

`patches/` holds eight framework patches, one per call site.
Each is a same-length branch retarget: the stock BL to
DrawImageAt (0x0306354A) becomes a BL to the keyed helper
0x03063A08, with the stock bytes as the expect precondition.
Only the branch target changes; the helper takes the same
(id, x, y) arguments and resolves the id through the same
descriptor path. Two properties the design relied on are proven
in gate (a2) below: the helper applies the light theme +166
remap exactly like DrawImageAt, and black pixels land through
format 1 (the light set's ink is 0x0000).

## The glyph set

`generate_glyphs.py` redraws the full family (157 to 181 dark,
323 to 347 light) and the two row composites (155, 156 dark;
321, 322 light) from geometric primitives: bare filled shapes,
no container tile, no ring, no keycap. Keycap and bare stock
presentations of one meaning get the same bare glyph. Play is a
triangle with its centroid at the optical centre; pause is two
rounded bars; next and previous are a triangle plus a bar;
repeat is a single arc with an arrowhead, repeat-arrows two
arcs, repeat-one the arc with a digit; shuffle is two crossing
curved strands with arrowheads; chevron, minus, plus, quote
(a speech bubble with two quote marks cut out) and info (a
filled disc with the i cut out) complete the set. Meanings and
state variants are the stock ones, per the stock art and the
design refresh v3 mapping.

Rendering rule: shapes are drawn on an 8x supersampled canvas,
box-downscaled and thresholded at half coverage, so every
output pixel is exactly the ink colour or the key colour
0xF800. No anti-aliasing colours are emitted, because on the
keyed path any non-key pixel lands: a blend fringe would land
as a halo. Ink is the palette foreground (0xFFFF dark, 0x0000
light). The accent is kept only on the two icons the stock bare
row itself draws in the accent: quote and info (dark accent
0xF220, light accent 0xFB20), in both of their presentations.
Every resource keeps its stock byte length and dimensions
(32 by 32, 2048 bytes). `icon_set_v4/mapping.json` records per
id: design, ink, ink pixel count, and the stock and new SHA-256
of the resource bytes.

The composites are assembled from the same designs at the
stock slot positions (slots at x = 4 + 50 * k, y = 0), 240 by
32 at their stock 15360 bytes, every non-glyph pixel 0xF800.
Resource 155 carries chevron-left, previous, next and
chevron-right in the theme ink (551 ink pixels); its centre
slot is empty, because in the B = 0 state the segment always
draws 168/169 over it. The stock composite's baked centre is
pixel-identical to resource 169's play glyph (126 pure-white
pixels at the same positions) and is never visible in stock;
keyed, it would ring the pause bars, so the overlay is the
centre glyph. Resource 156 carries chevron-left, minus, quote
and info (799 ink pixels, quote and info in the accent as in
the singles); its slot 1 is empty, because on the B != 0 path
the segment always draws the play mode's repeat variant
(174 to 177) at x = 54, and the visible glyph is the mode's,
not the baked repeat. The minus is baked: the plus overlay at
the centre site (0x0307F874) fires only when the
playback-context query at 0x030640BC returns zero and A is
not 8, and the v4 minus ink is an exact subset of the v4 plus
ink (60 of 132 pixels), so the overlay composes to a clean
plus and the minus shows alone where the overlay is
suppressed, both as in stock. Slots 3 and 4 of 156 are drawn
over in the media states by 178 and 179 themselves, so those
overlays redraw identical ink. `mapping.json` records the
composites with a slots list naming each slot's design or
null.

The art also ships as `v4-glyphs.json`, a version 1 theme
config whose 177 runs cover every changed resource halfword
(runs of changed words, merging gaps of up to four unchanged
words). It applies through the documented `--theme-config`
mechanism, with expected bytes checked against the stock image
by the builder.

## Build recipe and validation build

The set is opt-in. The validated combination is the default
manifest plus the eight repoint patches plus the art:

```
python3 patches/framework/build.py \
  --input DP3_V137.img --output DP3_V137_v4.img \
  --manifest patches/design_refresh_v4/manifest-v4.txt \
  --theme-config patches/design_refresh_v4/v4-glyphs.json \
  --ecpatch-dir <dir holding HIFIEC52/HIFIEC56.ecpatch>
```

`manifest-v4.txt` lists the 32 default patches followed by the
eight repoints; the default transplant (vorbis75) applies as
usual. A build made this way on 2026-11-05 has SHA-256
`7476ffb4ab8354112db99c0cb760b3d537eaaf23c62c7f4fa7800bc350510407`:
the image validates, all 54 resources in it match the
`icon_set_v4/` files byte for byte, and all eight repoint sites
carry the helper branch. (An earlier build, ce78d149..., carried
a palette bug in the two light composites: the generator's light
test, id >= 323, is right for the single icons but the light
composites are ids 321 and 322, so they were drawn with the dark
ink and accent. The test in the composites loop is now id >= 321;
the light composites carry black ink and the light accent, and
the keyed transport gates pass unchanged, since no pixel position
moved.) The default build is unchanged
(SHA-256 `92c446066e715d74a719671d3ee643ed4b7587c94801eb6dc3893f2271ed944d`);
`patches/framework/verify.py` passes 12/12.

## Emulation gates and results

`test_keyed_transport.py` runs real module 0, 18 and 27 code
from the stock image and from an image it builds in memory with
the recipe above. The pixel store executes for real (it
advances the display cursor, which the mode 0x10 path depends
on) and is recorded at entry; the staging copy is modelled as
in prove_keying.py.

- (a) Chunking. A synthetic 32 by 32 resource (1024 pixels,
  over the wrapper's 600-halfword staging chunk) through the
  helper emits exactly its 820 non-key pixels (204 key pixels
  skipped), each at the correct coordinate, black pixels
  included. The chunked path is exact.
- (a2) Remap parity. With the theme selector set light,
  resource 159 resolves to 325 through the helper exactly as
  through DrawImageAt (checked with distinct patterns staged
  under both ids).
- (b) No surround lands. Stock control: under DrawImageAt the
  centre rect ends as the full resource 169, including its 858
  surround pixels of 0x10A2. Patched, same painter state: the
  row composite (resource 155) emits exactly its 551 ink
  pixels through the keyed path (7129 key pixels skipped,
  none outside the glyph shapes); the centre play draw emits
  exactly its 121 ink pixels and no surround; the mode
  indicator emits its 101 pixels as before; no 0xF800 store
  occurs anywhere in 1293 stores. A second
  state (A = 1, B = 2) draws four glyphs (slot chevron 90 ink
  pixels, repeat 179, plus 132, computed chevron 90) and the
  ink stores in the row match the union of the four glyph
  shapes exactly.
- (c) Ghosting. The framebuffer model was validated first: the
  display is two surfaces (rows 0..239 at 0x030065A8, rows
  240..319 at 0x0306F224, paged by the halfword at 0x030238B8),
  and all 7680 last-store values in the row matched RAM
  readback. Three cycles, over a screen starting at the
  theater-derived ground 0x7222:
  - (c1) B = 0, play to pause at the centre, segment-only
    repaint: the centre rect ends as ground plus the union of
    the two centre glyphs, so 58 play-ink pixels survive
    under the pause glyph. With the stock composite this
    cycle left 0 ghost pixels, because the opaque composite
    redraw erased the centre first; with the keyed composite
    the centre is drawn only by the overlay, so the flip is
    in the same ghosting class as (c2) and is covered by the
    same full repaint cycle.
  - (c2) B = 2, chevron to pause at the computed slot,
    segment-only repaint: 34 ghost pixels survive. They are
    exactly the first glyph's ink positions that the second
    paint's own draws do not cover (the chevron's right edge
    around (18..19, 287..293) and its mirror points). Nothing
    refills the ground under the segment in this cycle.
  - (c3) The same flip under a full repaint cycle: the real
    painter call with event 0x39 set fills the whole screen
    from the ground cell as its first draw (76,800 stores of
    0x7222, traced), and the repaint block at
    0x0307F104..0x0307F132 posts event 0x43 in the same call.
    The segment, run over the filled framebuffer, leaves 0
    ghost pixels. One harness limit: a single end-to-end full
    cycle cannot complete under emulation, because after the
    fill the painter's track-info path reads a null storage
    volume entry (fault at 0x0305DD10, no card mounted). The
    cycle is therefore staged as its row-relevant sequence
    (paint, real fill call, segment over the filled screen);
    the fault is in the info path, not the transport path.

- (d) The composites. The gate runs the patched segment in
  the B = 0 and B = 1 states, dark and light, over a
  framebuffer starting at the theater-derived ground 0x7222,
  with the resources taken from the validation build. B = 0:
  composite 155 (light 321) emits its 551 ink pixels (7129
  key pixels skipped); the row is the composite ink plus the
  centre overlay's 121 ink pixels, ground preserved at 7008
  of 7680 positions. B = 1: composite 156 (light 322) emits
  799 ink pixels (6881 skipped); slot 1 shows the play-mode
  repeat overlay (179 ink pixels), slot 2 the plus overlay
  (132 ink pixels, with the baked minus inside it at its 60
  positions), ground preserved at 6630 of 7680 positions. No
  store anywhere carries the key colour, and every ink pixel
  in the framebuffer matches the generated art exactly.
- Poster census (informational). A byte scan of all module
  code segments for posts (calls to 0x0306723C) finds event
  0x39 posted from 7 sites, one outside the painter (module 33
  at 0x030898EA), and event 0x43 posted from 15 sites, four
  outside the painter, all in module 33 (0x03089858, 0x0308A276,
  0x0308A2A2, 0x0308A366). So the producers of row repaints can
  post the segment alone; whether a given state change posts
  0x43 alone or with 0x39 is a per-flow question the census
  does not settle (one 0x43 site sits 0x92 bytes from the 0x39
  site in module 33, suggesting a shared flow for track
  changes, unproven).

## Demonstration renders

The working papers (work/theater_glyphs2/demo/,
render_demo_v4.py) render the player screen on the
theater-derived grounds. composite_demo_dark.png and
composite_demo_light.png show the B = 0 state in full: on the
left the stock composite is a baked band across the derived
ground (0x10a2 dark, 0xffff light); on the right the keyed v4
composite's row is glyph ink on the ground, with the centre
play overlay drawn as the segment draws it.

## Remaining gates

- Hardware (Phase E). First flash observation of the keyed
  transport draws, including chunked-draw timing on device.
  Nothing here has been flashed.
- Ghosting on device. Gates (c2) and (c1) show ghosts are
  real if a state change repaints the segment without a full
  repaint in between: at the computed slot in B = 2 or higher
  states, and at the centre in B = 0 now that the composite
  no longer erases it (the B = 1 slot overlays redraw
  identical or containing shapes, so that state adds no new
  case). Whether the device's real flows do that is the open
  question the census frames but cannot answer; it is
  observable on hardware by flipping play state and track
  position on a theater-derived ground.

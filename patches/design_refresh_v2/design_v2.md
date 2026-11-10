# CE design refresh v2: design system

The v2 system in one document: the character idea, the
construction tokens, the colour system for both stock themes,
and what changed from v1 and why. The icon set is
icon_set_v2 (127 assets, each at exactly its stock byte
length). The two schemes in schemes/ are defaults in the
--theme-config consumer format of PR #38; colour stays a
build-time concern, so the geometry here is the deliverable
and the schemes are competent starting points, not the point.

## Character

**Soft keys.** Every control on the player is a keycap: a
filled, pixel-rounded square that fills its whole canvas,
with the glyph knocked out of it as a solid marker-weight
silhouette. Nothing in the interface is an outline. State is
the only thing the accent colour is for: the primary
transport keycaps wear it, everything else wears the panel
colour, and a control you can act on always looks like
something you could press.

A reviewer should be able to spot the system from three
marks alone: the orange keycap with a black play triangle
cut out of it, the white padlock with its keyhole knocked
through, and the splash's CE chip, which is the same keycap
shrunk to a badge.

## Construction tokens

### The full-bleed rule (a deliberate override)

Carbon and Material both prescribe a padded safe area inside
the grid (Carbon's keyline padding, Material's 2 px padding
on a 24 grid with a 20 px live area). The project owner's
direction for v2 overrides that practice: **glyphs extend to
the full asset canvas, with only the minimal inset needed to
avoid actual clipping or colour-key collisions.** The reasons,
recorded rather than assumed:

- These assets are small and the panel is 240x320. A padded
  glyph at 32x32 spends a quarter of its pixels on margin the
  UI around it already provides: the player layout, not the
  asset, owns the spacing between controls.
- The stock assets are already full-bleed (the orange disc
  touches the canvas edge; the bare variants sit on full
  tiles), so padding would shrink v2 glyphs relative to every
  stock screen the set does not redraw.
- The key discipline still applies in full: a glyph may touch
  the edge, but it may not spend a transparency key (0x0000,
  0xF800) as paint where the stock asset did not, and keyed
  surrounds keep their key pixels exactly.

Padding tokens therefore collapse to insets: tile inset 0,
glyph inset 2 to 3 px on keycaps (so the silhouette never
merges with the tile corner radius), 0 to 1 px on bare glyphs
and status silhouettes. Optical alignment replaces the safe
area: related glyphs extend to the same edges.

### Grid, stroke, corners

- **Grid**: the asset's own canvas is the grid (32, 24, 20,
  18, 14, 12 classes). All coordinates are integers; shapes
  are rasterised by per-pixel tests; there is no anti-aliasing
  anywhere, because the blitter composites raw RGB565 and a
  soft edge would be a colour no scheme chose.
- **Stroke weights**: 3 px for glyph bodies at 32, 2 px at 24
  and 20, 2 px at 18 and below with solid fills preferred;
  nothing in the set is drawn under 2 px. A glyph that needs
  a thinner stroke to read is the wrong glyph at that size
  (the v1 rule, kept).
- **Solid first**: at 18 and below, glyphs are filled
  silhouettes with detail knocked out (lock keyhole, clock
  hands), never outlines. The v1 ring, disc outlines and the
  arc-drawn clock all failed this rule and are gone.
- **Corners**: outer corners rounded by pixel steps, radius
  5 at 32 (the keycap), 3 at 24, 2 at 20 and below. Inner
  corners and counters are square. Curves exist only where
  the subject is round (disc, arcs, battery shell corners are
  single-pixel steps).
- **Optical corrections** (Material practice): discs and
  triangles overshoot the square by 1 px; the play triangle
  sits 1 px right of centre; chevrons extend 1 px past the
  play glyph's vertical extent so the family weighs evenly.
- **Keyline**: the keycap tile is the keyline shape for the
  32 class; every control occupies the identical rounded
  square, so unlike subjects keep one visual size (Carbon
  practice). For status glyphs the canvas itself is the
  keyline and silhouettes fill it.

### Family notes

- **Transport keycaps (32)**: primary controls (play, pause,
  previous, next) take the accent tile with the glyph knocked
  out in the background ink; secondary controls (repeat,
  shuffle, modes, plus, minus, info, quote, chevrons) take
  the panel tile with an ink glyph. Bare variants keep the
  stock pairing: same glyph, no tile, larger.
- **Repeat**: drawn as two arcs with a gap at each side and a
  free-standing triangular head in each gap, the form the
  uploaded pixel sheets use. Three attempts at generated
  tangent arrowheads merged into the arc ends at this size;
  the gapped form is the fix, and it is documented here so
  the next pass does not retry the generated heads.
- **Battery**: the stock segmented geometry, drawn
  edge-to-edge; state reads from segment count, the low
  segment keeps the stock amber, the rest keep the stock
  green in the baked set. Backdrops standardised exactly as
  v1 (dark 0x10A2, charging key preserved pixel for pixel).
- **Status**: headphones are a filled band and cups; the
  lock is a solid padlock with the keyhole knocked out in
  the tile ground; the clock is a filled disc with hands
  knocked out; the check is a filled accent disc with the
  check knocked out; the bluetooth rune is two open
  chevrons on a full-height stem (filled wedge forms were
  tried and read as a pennant, so the open form stays).
- **Splash CE mark, revised**: v1 carried the census mark
  (bare CE letters in the corner). v2 replaces it with the
  CE chip: a 44x24 keycap in the accent at the same
  bottom-right corner, letters knocked out in the splash
  ground colour. Reason: the mark should be the system's
  own badge, not a watermark, and the chip is recognisable
  at a glance in a way two small letters are not. It ships
  as full splash assets (127, 293) in icon_set_v2; the
  PR #38 runs file (ce-mark.json) remains the lighter
  route to the v1 mark and the two should not be combined.
- **No-media art, redrawn**: a full-canvas vinyl: filled
  disc, two groove rings knocked out in the ground, accent
  label, and the words NO MEDIA in the project pixel font.
  It replaces the stock note-and-disc art in the same ground
  colours (dark 0x10A2, light white).

## Colour system

Colour is applied at build time: the palette cells through
the registry proposal, the resources through the consumer
schemes. Values below are RGB565 (what ships); hex is the
design intent. Both schemes share one structure: an ink and
a paper, an accent and a line per theme, and a panel value
that lives in assets and in the player background site, not
in a palette cell.

### The swap constraint, handled

Background and foreground are one shared ink and one shared
paper: the palette routine loads 0xFFFF and 0x0000 once and
swaps which cell receives which per theme, and the clock
painter repeats the swap (theme census A1). Neither scheme
pretends otherwise. Each scheme picks ink and paper as a
pair; the dark background is the ink, the light background
is the paper, and the two foregrounds are the opposite
members of the pair. A coloured dark background with a
different light foreground is not expressible without
restructuring that code, and v2 does not price it: the
theater mode (theater_mode.md) is where a coloured player
background legitimately comes from, and it uses a different
cell entirely.

### Scheme A: CE Standard v2 (defaults baked into icon_set_v2)

Conservative evolution of v1's CE Standard: the Fosi orange
stays, ink and paper keep v1's softened values, lines keep
v1's raised values. The change from v1 is not the colours
but where they sit: panel is now the keycap colour, so the
panel value had to be one the glyphs could knock out of.

| Slot | Dark RGB565 | Light RGB565 | Notes |
| --- | --- | --- | --- |
| Ink (dark bg, light fg) | 0x0861 | shared | paper pair |
| Paper (light bg, dark fg) | 0xF7BE | shared | paper pair |
| Accent | 0xF220 | 0xFB20 | movw sites |
| Line | 0x2986 | 0xDEFB | movw sites |
| Panel (assets, player bg) | 0x2104 | 0xDEFB | not a palette cell |

### Scheme B: CE Dust

The character scheme, seeded by the mauve pixel sheet the
owner supplied: warm charcoal ink, warm paper, and a dusty
violet accent that collides with nothing else on the screen
(not the battery green or amber, not the bluetooth
blue-grey, not the Fosi orange it replaces).

| Slot | Dark RGB565 | Light RGB565 | Design hex |
| --- | --- | --- | --- |
| Ink | 0x18A2 | shared | #1A1512 |
| Paper | 0xEF7C | shared | #F2EDE6 |
| Accent | 0xA45E | 0x79DD | #A78BFA / #7C3AED |
| Line | 0x3986 | 0xD678 | #3A3230 / #D8CFC8 |
| Panel | 0x2924 | (asset-baked) | #2A2320 |

### The movw sites (registry proposal, summary)

Accent and line are eight movw immediates: four in the
palette routine (0x030655BC) and four in the clock and
status painter (0x03065B62), and they must move together or
the painter reasserts stock. The full proposal, with stock
bytes read from the image and the replacement bytes for
both schemes, is schemes/palette_registry_proposal.json.
Summary (file offsets into DP3_V137.img):

| Site | File offset | Stock bytes | Stock | A bytes | B bytes |
| --- | --- | --- | --- | --- | --- |
| Palette accent, light | 0x3EC86 | 4f f6 20 30 | 0xFB20 | 4f f6 20 30 | 47 f6 dd 10 |
| Palette line, light | 0x3EC8E | 4e f6 7d 70 | 0xEF7D | 4d f6 fb 60 | 4d f2 78 60 |
| Palette accent, dark | 0x3EC9C | 4f f2 20 20 | 0xF220 | 4f f2 20 20 | 4a f2 5e 40 |
| Palette line, dark | 0x3ECA4 | 41 f2 82 00 | 0x1082 | 42 f6 86 10 | 43 f6 86 10 |
| Painter accent, light | 0x3F5F6 | 4f f6 20 30 | 0xFB20 | 4f f6 20 30 | 47 f6 dd 10 |
| Painter line, light | 0x3F5FE | 4e f6 7d 70 | 0xEF7D | 4d f6 fb 60 | 4d f2 78 60 |
| Painter accent, dark | 0x3F63C | 4f f2 20 20 | 0xF220 | 4f f2 20 20 | 4a f2 5e 40 |
| Painter line, dark | 0x3F644 | 41 f2 82 00 | 0x1082 | 42 f6 86 10 | 43 f6 86 10 |

One correction to the census falls out of reading the bytes
back: its table prints the dark accent bytes as 4f f6 20 20;
the image holds 4f f2 20 20, which decodes to the same
0xF220. The image bytes govern and are what the proposal
records.

The proposal also names one extra candidate the census did
not list: the player background movw in the player window
constructor (exec 0x0307D1C2, file offset 0x87686, stock
41 f2 a2 00 = 0x10A2, dark theme only). Approving it lets a
theme set the player background default independently; the
theater design builds on the same cell at runtime.

### Resource recolors (consumer schemes)

- **Scheme A** (17 rules): charging frames 6 to 10 outline
  grey to the accent; the no-media ground (138) and the dark
  function bar ground (155) dissolved into the background
  role colour; the 0x10A2 stretch chips (99, 102 to 110) to
  the background role so stretched panels match.
- **Scheme B** (34 rules): everything in A, with the violet
  accent; plus the splash tagline (127), the pressed dialog
  buttons (136, 302), and the battery segment green
  (0x368B) across the battery frames to the accent, so
  charge segments read in the scheme colour while the low
  segment keeps its amber warning.

Counts in both files were computed from the pinned stock
image under the consumer's word convention (PR #38), and
literal_sites is empty in both: the registry above is the
decision that unlocks them, and it belongs to the owner.

## What changed from v1, and why

- **Ring to keycap.** v1's transport was a 3 px accent ring
  with an ink glyph, chosen to remove the stock filled disc.
  Three bodies of practice point the other way: Material's
  filled silhouettes, the Flaticon solid-rounded catalogue,
  and the Sharpie sheet's filled marker shapes all carry
  small controls as filled forms, and Carbon's rule against
  mixing filled and outline treatments inside a family made
  the ring the odd member once the status family went solid.
  The ring also spent its pixels on the container, leaving
  the glyph the inner 22 px; under the full-bleed rule the
  keycap gives the glyph the whole canvas and moves the
  accent from a border to a surface. The ring's one virtue,
  an accent presence on every primary control, is kept: the
  primary keycaps are accent-filled.
- **Status family to solid silhouettes.** v1 redrew these
  mostly as crisper outlines. At 14 to 19 px, outlines spend
  half the glyph on stroke; solids with knocked-out detail
  (lock, clock) read at native size, which is the u8g2 test
  the set is judged by.
- **Splash mark to the CE chip** (above).
- **Panel dissolved on code-drawn surfaces.** v1 kept a
  distinct panel grey on the bars and no-media ground. v2
  sends those grounds to the background colour in the
  schemes and keeps panel only inside the keycaps, where it
  is a surface a finger would press. Fewer greys, clearer
  job for each.
- **Schemes demoted to defaults.** v1 presented two schemes
  as the colour deliverable in a provisional format. The
  PR #38 consumer now defines the format, and colour
  customisation is a build-time act by whoever builds; v2
  ships two complete defaults in the consumer format and
  spends its effort on geometry and the theater mode.

## Deliberate omissions

- No digit or font redraw, as in v1: the anti-aliased digit
  family is its own project and mixing one new digit set
  into stock text rendering would look worse.
- Nothing the v1 inventory marked unclassified was redrawn
  (263/264, 137/203, 121 to 123, 189/190 and the rest);
  they keep stock bytes here too.
- No wallpaper, banner or screen redraws. The splash
  changes only by the CE chip and, in scheme B, its
  tagline colour.
- No anti-aliasing, gradients or shadows anywhere: the
  blitter cannot express them as palette colours.

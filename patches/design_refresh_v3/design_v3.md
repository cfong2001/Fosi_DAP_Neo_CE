# CE design refresh v3: the soft sketch pass

v3 is a change of hand over v2, not a new system. The v2
character stands: full-canvas keycap tiles, glyphs knocked out
as solid silhouettes, the accent reserved for state, colour
left to the build-time schemes (the v2 schemes stay the
defaults, unchanged). What changes is how every form is drawn.
v2 rasterised like a machine: a square brush, sharp triangle
points, mirrored pairs. v3 draws like the references the owner
pointed at this pass, the Sharpie sheet's bold marker strokes
and the mauve pixel sheet's chunky soft forms: round joins,
blunted points, and a small, deliberate wobble spent where the
eye looks first. The set is icon_set_v3, 127 assets, each at
exactly its stock byte length, both theme variants wherever
stock pairs them.

Nothing was copied from either reference. The Sharpie set is
commercial stock and the pixel sheet is a third-party set;
both are inspiration only, as practice.md recorded for v2.
Every v3 glyph is an original drawing made with the project's
pixel toolkit.

## The hand: a round brush

The mechanical change is one substitution. v2's toolkit drew
thick lines by stamping a square brush along a path, so every
cap and join ended in a flat or a corner. v3 stamps discs.
A stroke drawn that way ends in a round cap, turns through a
round join, and varies by at most a pixel in width the way a
marker line does. Triangle points get the same treatment: each
vertex is pulled toward the centroid by the rounding radius
and the edges are redrawn with the round brush, so the disc at
each vertex reaches back to about the original point. The
silhouette keeps its extent, but the point lands as a round
marker tip. There is no blur and no anti-aliasing anywhere:
softness here is geometry, because the blitter composites raw
RGB565 and a shaded edge would be a colour no scheme chose.

## Token changes from v2

### Radii

| Form | v2 | v3 |
| --- | --- | --- |
| Keycap tile, 32 | 5 | 9 |
| CE splash chip, 44x24 | 5 | 7 |
| Battery shell | single-pixel steps | 3 |
| Battery segments | square | 1 |
| Lock body | square | 3 |
| Headphone cups | square | 2 |
| Ebook cover / pages | angular triangles | 3 / 2 |
| Play, prev, next points | sharp | 3.5 keycap, 4 bare |
| Arrowheads (repeat, shuffle) | sharp | 2 at 32, 1.25 at 24x18 |
| Small play point, 12 | sharp | 1.75 |

The check disc and the no-media vinyl were already round in
v2 and keep their radii; the check itself is redrawn with
round joins and a flicked long arm (below).

### Stroke behaviour

- Caps and joins are discs at every size. Nothing in the set
  ends in a flat cut except where a form runs off the canvas
  edge on purpose (battery shell, bare glyph stems).
- Paired forms are drawn, not mirrored. The two repeat arcs
  differ by 1 px in radius and sit on centres 1 px apart, so
  the mark reads as two strokes of one hand rather than one
  stroke and its reflection.
- Stroke weights hold within 1 px along any stroke. The
  stamped-disc raster steps; it does not wander.

### The wobble budget

Deliberate asymmetry is capped at 1 px anywhere in the set,
and every spent pixel is a named constant in glyphs_v3.py,
never jitter. The budget is spent in seven places:

- Play: the tip sits 1 px above centre and the back edge
  leans 1 px, so the triangle feels pushed, not plotted.
- Pause: the right bar starts and ends 1 px lower than the
  left.
- Plus: the right arm is 1 px longer than the left.
- Headphones: the right cup sits 1 px lower than the left,
  the set's one tilt.
- Check: the long arm overshoots its v2 endpoint by 1 px,
  the flick at the end of a drawn tick.
- Repeat: the lower arc's centre sits 1 px low (above).
- No-media: the grooves and label are cut 1 px off-centre
  from the disc, the way a real record sits on its spindle.

Anything not on this list is symmetric or aligned exactly as
v2 had it.

## What stays firm, and why

- **Battery segments.** Charge state reads from segment
  count, so segments stay even, aligned, and identically
  spaced; only their corners round. A wobbled segment would
  read as a different charge, not as character.
- **Spinner spokes.** The nine frames are an animation; spoke
  angles stay at v2's exact values so rotation does not
  wobble. The spokes gain round caps only.
- **Text.** The 5x7 project font (the CE chip letters, the
  NO MEDIA line) is unchanged. A hand-drawn font at 5x7 is
  noise, and letterforms are identity, not decoration. The
  repeat-one numeral is the exception that proves the rule:
  it is a glyph, not text, so v3 draws it as three soft
  strokes (flag, stem, foot) instead of the block font, and
  it stays upright and centred.
- **The splash chip stays level.** It is a badge sitting on
  a typeset wordmark; tilting the badge would fight the
  splash, not soften it.
- **Keys and grounds.** Key pixels (0x0000, 0xF800) and keyed
  surrounds are preserved exactly as in v2, including the
  charging frames' key handling. Softness never spends a
  transparency key as paint.
- **The full-canvas rule and the accent discipline** are
  untouched. Tiles and glyphs still run to the canvas edge,
  and the accent still appears only where v2 put it.

## Family notes

- **Transport (32).** Play is the test case the pass was
  judged by: a plump rounded triangle, instantly a play
  button, plainly drawn rather than machined. Prev and next
  get the same rounded point and a soft-capped bar. Pause
  bars are round-capped strokes. Chevrons are one round-join
  polyline each.
- **Modes.** Repeat keeps v2's gapped arcs (the proven form
  at this size) with rounded heads and the drawn-not-mirrored
  pair. Shuffle's strands bow 1 px off straight and end in
  rounded heads. Quote is now two marker blobs, a round head
  with a tail sweeping down-left, where v2 had rects and a
  triangle.
- **Status.** The lock's shackle is a soft arc on two legs
  over a rounded body, keyhole knocked through as a dot and
  slot. Headphones are a soft band and two rounded cups.
  The clock's hands are round-capped, the minute hand
  drooping 1 px. Bluetooth keeps v2's open bind rune (the
  filled wedge stays rejected) with its joins rounded.
- **Battery.** Rounded shell, rounded nub, rounded segments;
  the geometry underneath is v2's, standardised backdrops
  included.
- **Ebook.** Redrawn as a form instead of a diagram: a
  rounded cover, two rounded pages knocked out, a 4 px spine
  channel, and the accent fold kept from v2.
- **Splash and no-media.** The chip rounds to radius 7 on
  the stock splash pixels. The vinyl keeps v2's composition
  with its 1 px off-centre cut.

## The legibility gate

Every glyph in the set was judged at native size on
native_sheet.png (the whole set at 1x), with the riskiest
glyphs checked again side by side against v2 at 1x: small
play and pause, bluetooth, mode shuffle, the lock, the ebook,
and the shuffle and repeat keycaps. A glyph that failed was
firmed up, heavier or simpler, until it read. Two glyphs
needed the trade, and are named here as the pass requires:

- **Shuffle (32 keycap and bare, and the 24x18 mode mini).**
  In the first sketch the fully rounded heads melted into
  the strands at 1x and the mark collapsed toward a plain X,
  the v1 failure. The heads were widened by 1 px and lengthened
  by 1 px, keeping their rounded points. It reads as shuffle
  at 1x now, at a small cost in softness.
- **Ebook.** The first sketch, pages knocked out of the
  rounded cover at v2's spacing, read as two blobs at 1x.
  The pages were narrowed to deepen the spine channel to
  4 px, and the book reads at 1x.

Everything else passed the gate in its first soft form,
including the play triangle at 12 px and the lock at 15x17.

One correction carried over from v2's paperwork: its contact
sheet labelled asset 119 "small play"; 119 is the small
pause. The v3 comparison sheet keeps the pairing and fixes
the label.

## Carried over unchanged

The speaker family (assets 132, 133, 298, 299) sits outside
this pass's scope list. Its v2 binaries are carried into
icon_set_v3 byte for byte and appear in mapping.json with
their v2 hashes, so the set stays complete at 127 assets.
Every other asset in the set was redrawn for v3.

## Sheets and binaries

after_sheet.png shows v2 against v3 at 3x in the v2 sheet's
layout and pairings. native_sheet.png shows the whole v3 set
at 1x and is the gate record. The .bin files and the sheets
are local to this work tree; the pull request carries this
document and icon_set_v3/mapping.json, and the binaries ship
as a zip on a GitHub release, the route the v1 and v2 sets
used, once the owner has reacted to the set.

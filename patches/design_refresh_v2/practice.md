# CE design refresh v2: practice notes

The rules the v2 system adopts, each traced to the source it came
from. Four published systems and three uploaded reference sheets
were studied. No artwork was copied from any of them: every glyph
in icon_set_v2 is an original drawing made with the project's
pixel toolkit, informed by the systems below. Where a source's
terms would not allow reuse, the rule records that the source was
used as reference only.

## IBM Carbon iconography (usage guide)

Source: ibm.com/design/language/iconography/ui-icons/usage.

Adopted:

- Icons are drawn on a fixed pixel grid per size and aligned to
  it; nothing sits on a half pixel. Carbon works on 16, 20, 24
  and 32 grids; the Neo asset sizes (32, 24, 18 to 20, 12 to 14)
  map onto the same discipline with the grid set to the asset's
  own canvas.
- One stroke weight across a set at a given size. Carbon uses a
  2 px stroke at its working sizes; v2 scales the same rule:
  glyph strokes are 3 px at 32, 2 px at 24 and below, with solid
  fills preferred wherever a stroke would fall under 2 px.
- Keyline shapes (circle, square, rectangle) keep related icons
  the same visual size even when their subjects differ. In v2 the
  keycap tile is the keyline: every 32x32 control occupies the
  same rounded square, so transport, modes and actions weigh the
  same on the screen.
- Corners are mostly square with minimal radius; v2 uses a
  pixel-stepped radius on the tile only (5 px at 32) and square
  inner corners and counters, which is the part of the Carbon
  treatment that survives hard-pixel rendering.
- Do not mix filled and outline treatments inside one family.
  This rule is what retired the v1 ring (see design_v2.md).

Not adopted: Carbon's padded safe area. The project owner's
direction for v2 is that glyphs run full-bleed to the canvas edge
with only the inset clipping or the colour keys require. The
conflict is recorded in design_v2.md rather than silently
resolved.

## Google Material Design Icons

Source: github.com/google/material-design-icons and the Material
icon system guidelines behind it.

Adopted:

- Filled silhouettes as the default construction. Material's
  system icons are solid shapes because they must read at small
  sizes on varied backgrounds; v2's status family and the
  keycap knockouts follow the same reasoning.
- Optical corrections: circles and triangles overshoot the
  square keyline slightly so they weigh the same, and the play
  triangle is shifted right of geometric centre because a
  centred triangle reads as pointing left of centre. Both
  corrections are in the v2 transport glyphs (1 px overshoot,
  play shifted 1 px).
- A consistent live-area idea even under the full-bleed rule:
  glyphs may touch the canvas edge, but related glyphs extend
  to the same edges, so the set still aligns optically.
- Rounded outer corners on filled shapes (Material uses a 2 px
  radius at 24); v2 steps the radius with size (5 px tile at 32,
  2 px at 20 and below) because a fixed 2 px radius disappears
  at 32 and overwhelms at 12.

Licence: the Material Design Icons are Apache-2.0. Adaptation
would be allowed with attribution recorded in the repo. In the
event, no Material glyph was adapted: the v2 set is original
drawings that follow the system's construction rules. If a later
pass ever does adapt a Material glyph, the attribution record
belongs in icon_set_v2/mapping.json and the Apache-2.0 licence
text must ship with the set.

## Flaticon solid rounded uicons

Source: flaticon.com/icon-fonts-most-downloaded, weight solid,
corner rounded, type uicon (studied as a catalogue, through the
site's listings).

Adopted, as characteristics not artwork:

- Solid fill with generously rounded outer corners is the
  dominant small-size UI treatment in the catalogue, and it is
  the direct model for the keycap tile: a filled rounded square
  carrying a knocked-out glyph reads at 32x32 and survives
  reduction better than any outline treatment tried in v1.
- Bold, even mass: uicon glyphs avoid thin appendages. v2 drops
  every feature under 2 px for the same reason.

Licence position: Flaticon's free tier requires attribution and
its premium assets are per-seat licensed; the terms do not give
this project a reusable right in the glyphs themselves. The
catalogue was used as market evidence for a construction style
only. No Flaticon asset was downloaded into the set, traced, or
adapted.

## The three uploaded reference sheets

Supplied by the project owner as art direction; all three are
third-party commercial or stock sets, used as inspiration only,
nothing copied.

- Sharpie icons for Notion (Getillustrations): bold hand-drawn
  marker strokes, heavy filled shapes, character from weight
  and slight irregularity. What v2 takes: the confidence of the
  weight. Glyphs are drawn at marker weight (3 px at 32) and
  the set does not apologise for being chunky. The hand-drawn
  wobble itself is not taken: the blitter's hard pixels would
  turn wobble into noise, so v2 keeps the weight and drops the
  wobble.
- Pixel UI sheet, muted mauve: chunky pixel type, segmented
  battery bars, blocky progress tracks, a limited dusty
  palette. What v2 takes: the segmented battery geometry is
  already the stock geometry and v2 keeps it; the dusty violet
  in the sheet is the seed for scheme 2 (CE Dust), the one
  place colour leads in v2; and the sheet's cycle arrows,
  drawn as arcs with separate triangular heads, are the model
  for the v2 repeat mark after generated arrowheads failed
  three times at this size (see design_v2.md).
- Pixel UI sheet, blue-grey: the second sheet confirms the same
  construction in a cool palette: filled rounded badges, hard
  pixel type, state read from geometry. What v2 takes: the
  check badge as a filled disc with a knocked-out check, and
  confirmation that a two-colour set (ink plus one accent)
  carries a whole UI.

## u8g2 (prior art carried from v1)

Source: github.com/olikraus/u8g2, named in the v1 brief.

- Monochrome bitmap icon discipline for small displays: a glyph
  either reads at native size or it is the wrong glyph. v2
  keeps the v1 test: every glyph was judged on the contact
  sheet at native size, and three designs (repeat, shuffle,
  bluetooth) were redrawn during this pass because they failed
  that test in their first form.

## Licence summary

- Material Design Icons: Apache-2.0; adaptation permitted with
  attribution. None adapted in v2; rules only.
- IBM Carbon iconography: the guide text is documentation, used
  as practice reference; no IBM asset used. Carbon icons
  themselves are a separate IBM asset set and were not touched.
- Flaticon uicons and the Sharpie set: commercial or
  attribution-bound stock; inspiration only, no reuse, no
  tracing, no adaptation.
- Everything in icon_set_v2 is an original drawing by this
  project, made with its own toolkit, and carries the project's
  own terms.

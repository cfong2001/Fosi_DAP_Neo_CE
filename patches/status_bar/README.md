# Player status bar on the current ground

With theater mode, the player fills its background with a colour taken
from the cover art. Three status bar items still carried a fixed
background in their pixels, so they showed dark surrounds on any other
colour:

- the **volume speaker** at (10, 7), 8 by 14, with black corners;
- the **Bluetooth icon** at (176, 5), 18 by 18, even with Bluetooth off;
- a **blank cell** after the track counter, 9 by 12, whenever the total has
  fewer than four digits.

All three are drawn on the background cell `0x03004400` now. Outside
theater mode that cell holds the theme default, so the dark theme is
unchanged apart from the speaker's corners, which now match the player
ground. Other windows keep their stock drawing.

## Bluetooth icon

The resident status routine `0x03063642` picks the icon by window. In the
music window (window byte 3) with player flag `0x1A8` clear it uses
resources 284 (off) and 285 (on), light 450 and 451, whose surround is the
player ground. Elsewhere it uses 282 and 283 (black surround, black
ground). Stock draws both pairs through the opaque DrawImageAt
(`0x0306354A`).

- `status-key.json` turns every surround-coloured pixel of 284, 285,
  450 and 451 into the key colour `0xF800` (324, 234, 324 and 234 pixels).
  No other code draws these four resources.
- Patch 0279 places a 42-byte wrapper in the census pocket at
  `0x03063C4A` (stock's unreferenced format-2 silhouette helper). It fills
  the 18 by 18 rectangle with the background cell, then tail-calls the
  keyed helper `0x03063A08`, which skips `0xF800`. It is the transport
  ground wrapper (`patches/full/build/src/transport_ground.S`) for this
  icon's size.
- Patch 0280 rebuilds the routine's music-window branch (22 bytes at
  `0x030636B8`) to call the wrapper with the same id, x and y, then store
  the drawn state and return as stock. The fill keeps the opaque draw's
  whole-rectangle replacement, so turning Bluetooth off still erases the
  glyph.

## Volume speaker

The speaker (resource 133, light 299) has a single image for every window,
with a black (light: white) surround, drawn through the opaque DrawImageAt
by the player (module 27, `0x0307F024`) and by the shared status routine
(module 0, `0x03063ACC`).

- `status-key.json` keys the speaker's border-connected surround (28 of
  112 pixels dark, 27 light; no glyph pixel changes).
- Patch 0283 places a 70-byte wrapper in the census pocket at
  `0x0306944E` (72 bytes, an unreferenced stock leaf routine). In the music
  window (window byte 3) it fills the 8 by 14 rectangle with the background
  cell; elsewhere it fills it with the stock surround colour (black dark,
  white light). Then it tail-calls the keyed helper.
- Patch 0285 retargets the shared routine's call to the wrapper. Outside
  the music window the result equals stock pixel for pixel.
- Patch 0284 retargets the player's call straight to the keyed helper. It
  runs only in straight line after the player's full-screen ground fill
  (`0x0307EFB8`), so the icon rectangle already holds the ground, and the
  player's repaint keeps its single fill (as `test_player_ground.py` and
  the focus mode gates require).

## Track counter

The player draws the counter (module 27, call at `0x0307E458`) through the
sprite string routine `0x030639A8`: a character maps to resource
`char - 0x30 + 249`, cells are 9 pixels apart at y = 8, and the draw is
keyed. The total is formatted as four digits. Each stripped leading zero
becomes a trailing `:`, whose resource (259, light 425) is a solid 9 by 12
tile (`0x10A2` dark, `0x2945` light) used to erase what a longer total
left behind. Being solid, it also paints over the theater ground. The
light-theme tile is dark grey in stock too, so stock's light theme shows
the same cell on white.

- Patch 0281 places a 52-byte wrapper in the census pocket at
  `0x03062EB8` (68 bytes). It fills the whole counter field
  (90, 8)..(170, 19) with the background cell, ends the string at its first
  `:` (the blanks only ever trail the digits; the slash is `;`), then calls
  the stock routine with the stock arguments.
- Patch 0282 retargets the player's counter call to the wrapper.

The field fill replaces what the blank cells did, and also erases digits
left of a counter that became shorter. Resource 259 is unchanged, because
other windows still draw it.

## Build and test

```
python3 patches/status_bar/build_status_bar.py
python3 patches/status_bar/test_status_bar.py [CE_IMAGE]
```

The build is deterministic (Keystone) and checks the stock bytes at every
site. The test runs real module 0, 18 and 27 code under Unicorn with real
pixel stores, against the composed standard image and stock:

- Bluetooth icon, both themes, theater ground: off leaves only the ground;
  on draws the glyph's ink over the ground; on then off leaves no ink. On
  the default ground the result equals stock. Other windows, and the music
  window with flag `0x1A8` set, are drawn exactly as stock. No store
  carries the key colour.
- Counter, both themes, theater ground with stale ink across the field:
  the field ends as the ground plus the digits' ink, with and without
  blank cells. On the default dark ground it equals stock; in the light
  theme it differs from stock only in the blank cell, which becomes the
  ground.
- Speaker, both themes: the player's call reaches the keyed helper and the
  shared routine's call the wrapper; through the wrapper, on a theater ground
  the rectangle is the ground plus the speaker's ink; other windows equal
  stock; on the default ground only the surround differs, becoming the
  ground.
- Controls: stock shows the speaker's surround, the 18 by 18 box and the
  blank cell on a theater ground.

Not yet verified on hardware.

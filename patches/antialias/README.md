# Antialiased text and icons

## Shipped: baked antialiasing in the transport sprites

The v4 transport sprites (resources 155 to 181 and their light twins)
carry their antialiasing in the pixels. `generate_glyphs.py` keeps
coverage under 1/16 as the transparent key 0xF800 and full coverage as
the ink. Edge pixels are the ink pre-blended toward a neutral grey as
bright as the theme ground (0x4A69 dark, 0xD69A light). The keyed path
lands pixels as they are and cannot blend at run time, and in theater
mode the ground comes from the cover. `grounds.py`
(`mock/grounds.png`) shows why the target is grey: a fringe tinted to
the default ground shows as a brown outline on other covers. No draw
code changed. The keyed-transport emulation gates check every landed
pixel against the sprites.

## Shipped: baked antialiasing in the status and browser icons

`../design_refresh_v4/browser_icons/generate_browser_icons.py` bakes the
same way. These icons are drawn opaque, so edges blend exactly into each
icon's own ground. Battery shells and terminals are rounded. Five stock
two-colour keyed sprites (189, 190, 355, 356, 298) are redrawn inside
their stock footprints. `compare.py` writes `mock/icons_before_after.png`
from the stock and release images: every changed icon at 6x.

## Shipped: full-screen art, dialogs and the progress bar

`generate_screens.py` bakes the rest of the stored art the same way:

- **Dialog cards** (137, 193, 203, 303, 359, 369): exact radius-16 corners,
  blended toward the screen behind them.
- **Low-battery icon** in 137/303: a rounded shell and terminal, and a
  smooth bolt.
- **"Powering off…"** in 294: smooth text in Barlow, the site's typeface
  (vendored in `docs/fonts`, so every machine renders the same pixels).
- **CE splash mark** in 127/293: smooth bold text. The generator writes
  `../theme_editor/ce-mark.json`.
- **Progress bar columns** (187, 188, 353, 354): softened top and bottom
  rows. These are the 1x6 columns module 27 repeats along the bar.
- **Progress knob** (220, 386): a keyed disc. Patch
  `../full/patches/0118` draws it through the keyed helper, so it no longer
  sits in its stock dark square over a theater ground.

`test_screens.py` checks the art in the Standard image. It confirms the
repoint and runs the keyed knob draw in emulation. Menu and list text is
drawn by the firmware's 1-bit font, which cannot hold antialiasing; its
Latin glyphs are redrawn instead (below). The README renders and the site simulator draw the progress
bar from these resources at module 27's coordinates.

## Shipped: the list and menu font

[`generate_font.py`](generate_font.py) redraws the Latin glyphs of Font B
(the 8 x 16 font used by lists, menus and titles) as data. 314 records
change: ASCII, Latin-1 and Latin Extended-A. The firmware's glyphs are
1-bit, so this is not antialiasing. The glyphs come from Barlow SemiBold
at 16 px, rasterised by FreeType with hinting, so stems are 2 pixels and
spacing is even. Other scripts keep their stock glyphs.

Fitting the firmware's layout rules (`0x030627BE`, `0x03063E06`):

- **Letter advance.** For ASCII letters the firmware measures the ink in
  rows 0 to 9 only (leftmost + rightmost column + 2). Records are read
  through a halfword byte swap (`0x03056B94`), so rows are big-endian
  and the tail is byte 32.
- **The stock `L` bug.** With its bar below row 9, stock's `L` advances
  2 px and overlaps the next letter by 5. The redrawn `L` trims its bar
  to 6 columns and shifts right until the measure clears it. `K` shifts
  one column for the same reason.
- **Other glyphs** get explicit tail advances: the space is 4, digits
  share one width, and punctuation gets a column on each side.
- **Vertical fit.** The baseline is row 12, one row above stock, so
  descenders get rows 13 to 15. Marks on capitals sit in the rows above
  the cap, as in stock. U+00B2, U+00B3 and U+0140 do not fit and keep
  their stock glyphs.

Font A, the 6 x 12 font for status and small text, gets the same
treatment from the same generator (`generate_font.py a`): Barlow SemiBold
at 11 px, caps on rows 2 to 9 and descenders on rows 10 and 11 as in
stock. Its records are 32 bytes with the tail at byte 24, and the
firmware measures its letters over rows 0 to 7. Digits keep their natural
widths and punctuation gets no extra padding, since the 6-pixel cell has
no room for either. Every Latin-1 and Latin Extended-A glyph fits, so
none keeps a stock record; 314 of the 317 redrawn records differ from
stock.

`test_font.py` checks both fonts: reproducibility, that the Standard image
carries every record, and the advance rules.

## Mockups: text options (not built)

Nothing here changes firmware. `mock.py` renders the theater now-playing
screen and a file list three ways, from the device's own 1-bit fonts (read
from `DP3_V137.img`, laid out with the firmware's width rule from
`0x030627BE`) and the v4 transport glyphs. Every pixel is quantized to
RGB565, the panel's format:

- **Today:** 1-bit text and hard-edged icons, as shipped.
- **Option A:** the same 1-bit fonts, plus half-tone pixels at the inside
  corners of diagonal steps, and antialiased icons.
- **Option B:** a grayscale Latin font at 16 levels (DejaVu Sans stands in
  here), with other scripts still 1-bit, and antialiased icons.

The panel's pixels go through a RAM framebuffer (`0x03063E60` stores into
SRAM at `0x030065A8`), so a blitter can read the ground and blend. That is
what makes both options buildable.

    python patches/antialias/mock.py   # -> mock/antialias_sheet.png

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

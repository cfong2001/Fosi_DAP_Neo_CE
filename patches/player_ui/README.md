# Player typography and labels

Standard CE draws elapsed and total time with the same text renderer and
font as the player title. The existing 148-byte time routine now formats
`MM:SS` into a bounded stack buffer. Its 14-pixel text line at y=240 ends
before the progress bar at y=254; the total counter starts at x=191.
A helper clears each rectangle with the current ground before drawing, so
changing digits leave no stale ink. The actual Font B digit and colon
records have ink only through row 12 and fit the line without clipping.
The stock 99-minute display limit and total-time state reset are preserved.
The sprite-digit resources are no longer used by this routine. The
52-byte clear-and-draw helper occupies a separate tier-1 resident pocket
at `0x030513C0`; it preserves the renderer arguments across the fill.

The shared marquee registrar starts with a 150-tick pause (1.5 seconds).
Only after an actual scroll draw does the stepper select 50 ticks between
steps (0.5 seconds, versus stock's 0.3). Registration resets the pause;
the existing 16-bit tick arithmetic handles wrap. This timing also applies
to scrolling browser rows and track information using the shared engine.
No new persistent state is allocated. The stamp helper occupies 10 bytes
of the census's unused 20-byte routine at `0x03053114`; its two original
instructions and the new interval store execute under Unicorn.

English resources 82 and 83 read **Artists** and **Albums**. The album
list's inline action reads **Play All Albums**, fitting its original
32-byte slot, including the terminator. Other languages retain their labels.

Build with the reference ARM toolchain:

```
python patches/player_ui/build_typography.py
python patches/player_ui/test_typography.py
```

The generator verifies the pinned stock SHA and emits expected-byte patches
and label runs. `patches/full/manifest.txt` and `build_theme.py` compose them
into Standard CE; Minimal and recovery retain their existing behavior.
The SDK mirror documented in `research/patch_technique_and_sdk.md` was used
only to identify text-rendering and scrolling semantics. These routines are
original CE code. The first physical CE boot confirmed the player, custom
settings and music playback; broader timing and window-cycle checks remain.

## Playback metadata

`build_metadata.py` compiles the seven-row information painter into the old
painter's code at `0x0307E988` and helpers at `0x0307ED60`. The shared literal
pool at `0x0307ECA4..0x0307ED60` stays intact: the artwork setup uses it too.
The original entry at `0x0307E986` branches across the alignment halfword.
No module, BSS or image growth is needed.

The real playback tag dispatcher (`0x03088D42`) receives `0x0304AF24` as
its output. Its title, artist and album fields are at offsets `0x60`,
`0x15E` and `0x25C`, confirmed by the resident parser and playback artist
fallback. `player_title` copies at most 127 UTF-16 units into the existing
128-unit title buffer. A tag such as `Tagged.wav` stays intact. An absent
title uses the filename at `0x0304ADF4`, including its extension. This
supersedes the old filename suffix-trimming pair in Standard CE only.

The info painter clears its own area, then draws Title, Artist, Album,
Format, Resolution, Bitrate and Size. Values are left aligned in clipped
rectangles; the prior drawing color is restored. Resolution reads the
stock codec structure's bit depth and sample rate; bitrate converts bits
per second to kbps; size uses decimal MB rounded to one decimal. Null codec
state and missing tags use Unknown. The codec labels retain the Standard
image's WMA-to-Opus mapping.

```
python patches/player_ui/build_metadata.py
python patches/player_ui/test_metadata.py
```

The tests execute both the patched title call site and the assembled info
painter with synthetic playback state, intercepting only LCD calls and the
file-size query. They verify all seven rows, empty fields, long titles,
suffix preservation, fractional sample rates, maximum 32-bit file size,
register preservation and stack balance. Actual tag files and the device
remain outside this test's scope.

## Artwork compositor

`build_artwork.py` emits expected-byte patches for a row compositor in
module 0 census pockets, plus a placeholder and codec-label data in the
unused parts of the old info painter. The normal box starts at (48,36),
centered on a 240-pixel screen; focus retains its centered 190-pixel box.
The scaled image is centered vertically inside the requested box. Padding
uses the theater ground, with a symmetric radius-10 corner mask.

Contrast is applied to each RGB565 component around its midpoint with a
factor of 1.20 and saturation (1.18 before 2026-11-12). The compositor builds a temporary 190-pixel
stack row, then calls the original bitmap function. It preserves that
function's return value. The decoder's buffer is never edited, so the
stock duplicate final-row blit cannot apply contrast twice. The theater
sampler still consumes the original decoder row. Requests outside the
player boxes keep the original bitmap arguments and pointer.

The no-art exits restore the background, then draw an outline tile and
music note inside the normal or focus box. The file type appears in a
rounded tile on the cover's lower-right corner. A badge is also drawn after
the final decoded row, so progressive decode cannot erase it. Battery and
status icons keep their existing draw paths. The record is removed from
the two player backgrounds; the placeholder is drawn only when needed.

```
python patches/player_ui/build_artwork.py
python patches/player_ui/test_artwork.py
```

## Progress bar in the inverse of the ground

When the player opens, module 27 stages resources 187 and 188 (light 353
and 354) as 1x6 RGB565 columns at `0x03024904` (played) and `0x0302491C`
(unplayed). Each bar draw fills (40,254)..(201,268) with the ground and
blits one column per position. Patch 0182 sends that fill's BL at
`0x0307F6AE` to `bar_fill` (0183, a 28-byte stub in a tier-1 pocket at
`0x03053EF4`). The stub saves r0-r4 and lr, calls `bar_recolor` (0179,
`0x0305DE20`) with the ground cell `0x03004400`, restores them and tail
calls the original fill with its stack argument in place.

`bar_recolor` writes the played column as the inverse of the ground and
the unplayed column 3/8 of the way from the ground to the inverse, with
rows 0 and 5 halved into the ground as the antialiased stock columns are.
Averages use the packed RGB565 halving `((a & 0xF7DE) >> 1) + ((b &
0xF7DE) >> 1)`. Recolouring before every draw follows each theater
ground and theme change without new state. The CE knob is an orange-filled
selector with a contrasting, antialiased theme-aware stroke. A mid-grey
ground (around `0x8410`) inverts to nearly the same
grey, so the bar has little contrast there.

The tests execute the stub and routine for seven grounds, including
black, white and mid-grey: the fill still runs with its original
arguments, stack word, r4 and return address, both columns hold the
expected words, and nothing past the 1x6 column changes.

The tests execute the emitted Thumb routines and check row geometry,
independent contrast values, aspect padding, corner symmetry, bitmap
return preservation, registers, stack and unchanged source pixels. Full
JPEG/theater, focus and no-art suites cover the combined paths. The new
stack row adds at most 380 bytes of pixel storage; it allocates no BSS or
persistent state. Pocket residency retains the project's existing
hardware-validation limitation.

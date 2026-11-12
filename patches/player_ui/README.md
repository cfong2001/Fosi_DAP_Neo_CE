# Player typography and labels

Standard CE draws elapsed and total time with the same text renderer and
font as the player title. The existing 148-byte time routine now formats
`MM:SS` into a bounded stack buffer and draws in a 66 by 16 pixel rectangle.
The stock 99-minute display limit and total-time state reset are preserved.
The sprite-digit resources are no longer used by this routine.

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
original CE code. Device rendering and timing remain untested on hardware.

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
factor of 1.18 and saturation. The compositor builds a temporary 190-pixel
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

The tests execute the emitted Thumb routines and check row geometry,
independent contrast values, aspect padding, corner symmetry, bitmap
return preservation, registers, stack and unchanged source pixels. Full
JPEG/theater, focus and no-art suites cover the combined paths. The new
stack row adds at most 380 bytes of pixel storage; it allocates no BSS or
persistent state. Pocket residency retains the project's existing
hardware-validation limitation.

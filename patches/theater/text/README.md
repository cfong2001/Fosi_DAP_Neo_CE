# Player title copy: bounds repair

The stock player painter's flag-0x4A path copies the UTF-16 title from
`0x0304ADF4` to `0x03024804`. At `0x0307F9D0` it copies up to 128
code units; when all 128 are nonzero, it reaches the text measurement
call without writing a terminating zero. The NUL path at `0x0307FA3A`
also probes and, if either happens to be a dot, clears words 8 and 10
bytes before the end of the copied title. An empty or short title can
therefore read and write before the destination. These are stock V137
behaviors, reproduced by `emu_title_copy.py` using synthetic inputs.

The paired same-length module-27 patches replace only those two blocks.
They copy at most 127 code units and always write the terminator inside
the 128-code-unit destination. A title truncated at the limit bypasses
extension removal; a NUL-terminated title of at least five code units
keeps the stock fourth/fifth-from-end dot checks. For shorter titles the
checks are skipped so they cannot touch preceding memory. A suffix-only
name such as `.mp3` is consequently displayed intact. No segment is grown
and no persistent data or additional RAM is claimed.

The code runs in the stock painter context: `r0` is the destination,
`r3` is the source, and `r7` is the zero value set at `0x0307EF8C` and
used as zero by the stock copy. The existing stack loop counter is not
read later in this painter; the replacement uses `r1` instead. At the
continuation `0x0307F9EE`, stock reloads `r0` and calls the text measure
routine, which may clobber `r0`–`r3` and flags. The replacement leaves
callee-saved registers and stack untouched.

Both `.patch` files are required as a matched set; the framework rejects
partial or modified pairs. They are not in the default manifest, but the
browser builder offers the pair as an experimental option. They are not
a text-outline or theater-mode implementation. Device operation and real
metadata still require testing.

With the pinned stock image and Unicorn available:

```
python3 patches/theater/text/emu_title_copy.py
```

The test reproduces both stock defects, checks that no patched write
escapes the 128-code-unit buffer for empty, short, long and extension
cases, and compares ordinary names with the stock path. The assembly and
linker script document the replacement instructions and exact placement;
the build must be checked against both replacement byte strings before
using another toolchain.

To reassemble with GNU Arm Embedded GCC and binutils:

```
arm-none-eabi-gcc -mcpu=cortex-m3 -mthumb -c \
  patches/theater/text/title-copy.S -o /tmp/title-copy.o
arm-none-eabi-ld -T patches/theater/text/title-copy.ld \
  /tmp/title-copy.o -o /tmp/title-copy.elf
arm-none-eabi-objcopy -O binary --only-section=.text.loop \
  /tmp/title-copy.elf /tmp/title-loop.bin
arm-none-eabi-objcopy -O binary --only-section=.text.finish \
  /tmp/title-copy.elf /tmp/title-finish.bin
```

Compare those files with the corresponding `replace` fields. A framework
build with the default manifest plus both patches passed stock package
validation; a separate build also passed the grown-image validator with a
1,000-byte module-31 insertion and both replacements present in module 27.
Those structural checks do not validate a real player or the semantics of
any inserted module-31 payload.

## Theater contrast and repaint evidence

The player painter enters stock text mode 1 at `0x0307EF60` and restores
the previous mode at exit. In that mode set glyph bits use the foreground
and clear bits leave the destination untouched. At `0x0307FA6C`, the
title setup loads the stock foreground from `0x030235B6` into the text
pen at `0x0302385C`. Stock palette initialization at `0x030655BC` writes
white (`0xFFFF`) there for dark mode and black (`0x0000`) for light mode.

For a flat theater ground, an alternative to changing the shared pen or
adding an outline is to constrain the ground. The test below runs both
stock instruction paths in Unicorn and computes bounds after RGB565
quantization. If each averaged RGB888 channel is mixed 55% toward black
for dark mode, the lightest ground is `[115, 113, 115]` and white has at
least 4.84:1 contrast. If mixed 75% toward white in light mode, the
darkest is `[189, 190, 189]` and black has at least 11.26:1. The proposed
warm paper `[242, 237, 230]` instead yields `[180, 178, 172]` at the
darkest, at least 9.90:1 with black. The test checks that every possible
channel input preserves the monotonic quantization bound.

```
python3 patches/theater/text/contrast_bound.py
```

This covers the stock title pen on a flat ground; it does not prove the
contrast of muted text, icons, antialiasing, artwork underneath a glyph,
or modified palettes. It assumes the final output is interpreted as
RGB565; the picture buffer and its pixel order remain unpinned.

The player checks event `0x24` and test-clears `0x39` and `0x2F` at
`0x0307EF7A`–`0x0307EFA0`. When a full repaint is requested and
`SAVEINFO+0x1A` is nonzero, it reads the current ground from `0x03004400`
and fills the screen at `0x0307EFA8`–`0x0307EFB8`. The same full-paint
path posts event `0x3A`; the subsequent handler posts title event `0x4A`.
When `SAVEINFO+0x1A` is zero, the player draws stock no-media image 138
instead. Partial redraws use rectangle fills to erase old text, so
removing those fills without a replacement dirty-region strategy leaves
stale pixels. Merely writing the ground cell does not itself establish
that a player repaint is scheduled.

`emu_player_redraw.py` exercises this control flow with the stock event-bit
routines and intercepted display calls. It posts `0x39`, checks that two
different values in `0x03004400` reach the fill and that title event
`0x4A` is set, and checks the no-media and no-event paths. It does not
model task scheduling, the physical panel, or concurrency:

```
python3 patches/theater/text/emu_player_redraw.py
```

An outline cannot safely be implemented by blindly calling the text
routine at shifted rectangles: its descriptor also controls clip, wrap,
and alignment; player text can start at screen x=0; and its text
conversion has a one-shot flag. The monochrome glyph blitter does not
call the rectangular clipping helper. A proposed outline needs verified
clipping and redraw costs on the actual path before integration.

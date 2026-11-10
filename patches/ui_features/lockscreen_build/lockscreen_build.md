# Lock-screen title routine: build report

## Reproduce the standalone build and checks

From the repository root, with `arm-none-eabi-gcc`, binutils, Python 3,
Unicorn, and the pinned V137 image available:

```sh
sh patches/ui_features/lockscreen_build/build.sh
python3 patches/ui_features/lockscreen_build/emu/emu_lock.py
cc -std=c99 -O2 -Wall -Wextra -Werror \
  patches/ui_features/lockscreen_build/test_time.c -o /tmp/lockscreen-time-test
/tmp/lockscreen-time-test
```

Set `FOSI_STOCK_IMAGE` when the stock image is not at the repository root.
The emulator verifies its SHA-256 and reads the three required segments
directly, without a separate extracted directory. The linker rejects `.bss`
and out-of-room payloads; the build checks the standalone branch bytes.
GCC 14.2.1 produces a 408-byte blob that passes the emulator; the size
reported below is the GCC 13.2.1 build. The builder page embeds the
GCC 13.2.1 build (the reference toolchain from
`ci/install_reference_toolchain.sh`), 406 bytes, SHA-256
`9610d8d7995d821b4289c18e720c21c848494633d2af097e160101a23e2c92d2`,
which passes every `emu_lock.py` gate. These standalone bytes and
branch target differ from a module 31 composition, which must be built and
tested with its own derived offsets. No device test is implied by emulation.

Scope: the lock-screen information feature from `work/ui_features/ui_features.md`, built to the specification pinned in `work/ui_features/renderer/renderer.md`. Stage 1 (track title) and stage 2 (elapsed and total time) are both built, in one routine, and emulation-verified. All work is in scratch trees under `work/ui_features/lockscreen_build/`. The live framework and manifest were never edited, nothing was pushed, and the stock image still hashes to the pin `fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef` (verified after the build and after the emulation runs).

Result in one line: patch 0033 plus a 406-byte routine, linked at the module 31 segment extension base, draw the stock hold icon exactly as stock, then the title when SAVEINFO +0x60 is 1, then a segment-relative elapsed / total line under its own gate.

## What was built

- `src/lockscreen.c`: the routine in freestanding C (arm-none-eabi-gcc 13.2.1, `-mcpu=cortex-m3 -mthumb -Os -ffreestanding -fno-builtin -nostdlib`). Division compiles to the hardware UDIV and MLS instructions; the blob has no undefined symbols and pulls in no libgcc routines.
- `src/lockscreen.ld`: link at the extension base, entry section first. The writable time buffer sits in .data inside the blob image (40 bytes), because the extension payload is a plain byte copy and carries no .bss.
- `0033-ui-lockscreen-title.patch`: module 31, code, site 0x0307E89E, expect `e4f72fbf`, replace `00f0d3ba` (B.W to the routine entry). The branch bytes were assembled at the site address from `src/site33.S`, the same method the Bluetooth build used for patch 0032.
- `build.sh`: builds the blob and the patch bytes, prints sizes and symbols.

Routine size: **406 bytes total** (366 bytes of code including literal pools, 40 bytes of .data for the stage 2 text buffer). Entry symbol `ui_lockscreen_paint` sits exactly at the link base.

## Placement requirement

The routine is position-dependent only on its link base. For this scratch build the base is **0x0307EE48**, the first byte past module 31's stock code segment (the segment ends at 0x0307EE48 exactly) and the start of the extension room the resident-home census measured (0x0307EE48..0x03080B54, 7,436 bytes, shared with the M3U parser and bridge). Final placement is the module 31 segment extension at that base. If the extension base ever moves, the link script base and the patch 0033 branch target are regenerated together; nothing else in the routine changes. The branch from the site reaches the base with offset +0x5A6, far inside B.W range.

## The routine, step by step

Entry state, pinned by the renderer trace: the painter has test-cleared flag 0x2E, loaded the byte at 0x030230EC, and popped {r4, lr}. At the patched instruction r0 holds 0x26 plus bit 2 of that byte, and lr holds the painter caller's return address. The displaced stock instruction is the tail call B.W DrawImage.

1. Call DrawImage (0x03063700) with r0 unchanged. The stock hold icon (image 0x26 or 0x27) is drawn first, exactly as stock.
2. Read SAVEINFO +0x60 (0x03023300). If it is not 1, return. Nothing else has been touched.
3. If it is 1: save the two pen colour halfwords of the display context (0x0302385C +0 and +2), load them from the cells Display uses (0x030235B6 and 0x03023144), then open the display-mode bracket with saved = 0x0306316E(1).
4. Build the 8-byte descriptor {11, 24, 231, 39} on the stack (halfwords x_left, y_top, x_right, y_bottom: Display's proven x extent and 16 px strip height) and call 0x03062CEE(desc, desc, 0x030235CE, 0). The name buffer is UTF-16, NUL-halfword terminated, and is the buffer snapshotted under the same +0x60 gate.
5. Stage 2, under its own gate (below): format the time text and call 0x03062CEE again with descriptor {11, 40, 231, 55}.
6. Close the bracket with 0x0306316E(saved), restore the saved pen colours, and return to the painter caller's address. Callee-saved registers and the stack pointer are exactly as at entry (checked in emulation, case (a) against an unpatched stock run).

The compiler's prologue saves and restores r4 to r9, sl, and lr around the body; the only registers the caller can observe changed are the call-clobbered r0 to r3 and ip, which the stock tail call exposes to DrawImage in the same way.

## Stage 2: elapsed and total

Built, and reported separately as the brief requires. Gate: file-info state field +0x44 == 1, total +0x4C greater than the latched start +0x48, and the codec object pointer at 0x0304AD78 non-null. If any condition fails, stage 2 draws nothing and stage 1 is unaffected.

Both values are segment-relative, matching module 27's own arithmetic (the progress bar fraction and the remaining-time segment in its player Display):

- Elapsed = codec object word +4 (live position, ms) minus +0x48 (latched segment start, ms), clamped at zero. +0x48 is latched, so the readout is elapsed-from-segment-start; no other meaning is claimed for it.
- Total = +0x4C minus +0x48 (the segment length; on a fresh track +0x48 is 0 and this is the full track duration).

The routine formats m:ss / m:ss (seconds from whole milliseconds divided by 1000, as module 27 does) into its UTF-16 buffer with its own digit code and draws it in the same mode bracket and pen colours as the title. One honest limit from the design phase stands: painter cadence is event-only, so the line refreshes when the 0x2E segment repaints (track and state changes), not once a second.

## Emulation

Harness: `emu/emu_lock.py`, output in `emu/emu_lock_output.txt`. It maps module 0 code and data and module 31 code from the stock extracted segments, writes the blob at 0x0307EE48 and the patch bytes at the site, and enters at 0x0307E89E with the pinned entry state. Two tiers:

- Tier 1 intercepts DrawImage and the text routine at entry and records their arguments. The display-mode function 0x0306316E is only observed; it runs for real (ten instructions, touches only the display context struct).
- Tier 2 runs the real text routine, glyph routine, and blitter against a synthetic class-0 font seeded at the font base cell 0x03023280. The framebuffer store 0x03063E60 is intercepted and plotted points are counted there. One further intercept needs stating plainly: the glyph path's copy primitive (0x03064314, class-1 sibling 0x030642FE) delegates in the firmware to the copy engine at 0x03067510, which dispatches through the device table at 0x03005674. That table is all zeros until boot-time registration, so the engine cannot run in a bare map (traced: engine to device dispatch 0x0305E020 to the null table entry). The harness performs the primitive's call-site contract directly (a synchronous copy of r2 bytes from r0 to r1). The sources read are the real font records, and everything downstream of the copy (measure, glyph layout, blit, point plotting) runs as stock code.

Cases, all pass:

| Case | What it proves |
|---|---|
| (a) +0x60 == 0 | DrawImage called once with r0 = 0x26; text and mode functions never called; pen colours and stored mode untouched; callee-saved registers and stack pointer identical to an unpatched stock run entered the same way |
| (b1) +0x60 == 1, bit 2 clear | One text call: r0 == r1 == descriptor pointer holding {11, 24, 231, 39}, r2 = 0x030235CE, r3 = 0; pen colours are Display's values during the call; stored mode is 1 during the call; bracket is set(1) then set(saved 5); colours, mode, registers, and stack restored after |
| (b2) +0x60 == 1, bit 2 set | Same as (b1) with DrawImage called with r0 = 0x27 |
| (c) tier 2, title "Ab3" | The glyph routine is entered once per character in order; the record copies read exactly the three seeded records; one mode-1 blit per glyph at y = 24, height 16, x = 11, 22, 33 with widths 11, 11, 8 (ink width for the letters, width code for the digit); the framebuffer store plots 368 points, exactly the set bits inside the three blit boxes (128 + 128 + 112). The string renders, not just fires |
| (d) stage 2 formatting | Seeded latched 60,000 ms, live 814,000 ms, total 3,427,000 ms: second text call with descriptor {11, 40, 231, 55} and buffer text "12:34 / 56:07" |
| (d2) stage 2 gates | No second call when the state field is 0 or the codec pointer is null; a live position behind the latch clamps the elapsed half to "0:00" |

The first tier 2 run expected 336 plotted points and measured 368. The difference is the seeded pattern, not the renderer: the bitmap halfword 0x7F80 sets bits at mask columns 1 to 8 (8 bits, not 7), the ink-width helper returns min + max + 2 = 11 for the two letters, and 128 + 128 + 112 = 368 is the exact set-bit count of the three blit boxes. The assertion now uses the derived value.

## Open items

- The two y positions (24 for the title strip, 40 for the time strip) are placement choices, as the renderer document flags: the x extent and strip height are Display's proven values, the y is the one number to confirm on hardware.
- The painter has a second copy in module 0; this patch extends module 31's copy only, so a screen painted outside module 31 keeps the stock lock display (same scope as the design).
- Nothing here is stacked in the live framework. Stacking waits for the module 31 segment extension build (the insertion rebuild) that delivers the blob to its base.

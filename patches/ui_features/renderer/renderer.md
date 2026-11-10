# Lock-screen renderer trace

Scope: the two blockers named in `work/ui_features/build/ui_build.md`, Feature 2. Blocker 1 is the renderer contract for drawing the track title inside module 31's painter. Blocker 2 is the source of elapsed and total time. Method: Ghidra 12.2 decompiles of the FosiNeo project (Display in mod31.elf, the text engine in mod0.elf, the player Display in mod27.elf, the playback functions in mod33.elf), Ghidra listing dumps for the frame setup the linear disassembler desyncs on, and capstone traces over the extracted module binaries. Decompile and listing evidence is saved beside this file (display_decomp.txt, display_frame_listing.txt, mod0_string_decomp.txt, mod0_sibling_decomp.txt, glyph_mod17_decomp.txt, mod27_decomp.txt, mod33_task_decomp.txt). No code was built and no patch was emitted. Verdicts: blocker 1 is pinned on candidate (a). Candidate (b) is pinned as a mechanism and excluded as a text path. Blocker 2 is pinned, with three named gaps at the end.

## Blocker 1: the renderer contract

### Candidate (a): 0x03062CEE is pinned

0x03062CEE in module 0 is the firmware's text draw routine. Two stock callers prove the contract: module 31's Display (FUN_0307e8f2, calls at 0x0307EB36 and 0x0307EC7A) and module 27's player Display (FUN_0307ef4e, one call with flags 2). Every stock call passes the same pointer in r0 and r1.

Entry contract:

| Argument | Content |
|---|---|
| r0 | Pointer to an 8-byte rectangle descriptor |
| r1 | The same descriptor pointer (r0 == r1 at every stock call site) |
| r2 | UTF-16 string, one code unit per halfword, NUL-halfword terminated |
| r3 | Flags; bits 0 to 1 are the alignment: 0 = left, 1 = right, 2 = centered. Higher bits are masked off in the body (`param_4 & 3`) |

The descriptor is four halfwords:

| Offset | Field | Proven role in the body |
|---|---|---|
| +0 | x_left | Pen X start for alignment 0; left edge of the line-fit width |
| +2 | y_top | Pen Y at entry; first line's top |
| +4 | x_right | Pen X start for alignment 1; center basis for alignment 2; line-fit width is +4 minus +0 |
| +6 | y_bottom | Carried with the other three halfwords into the glyph clip (below); Display always sets it to y_top + 15 |

Display's values for one list row are {11, row_offset + 53, 231, row_offset + 68}: a 16 px high strip, x from 11 to 231. The strip width, 221 px, is the same 0xDD threshold Display's measure call (0x0306295A) tests before registering a string for marquee scrolling, which cross-checks the field reading. The Ghidra listing of the frame setup (display_frame_listing.txt) shows the descriptor built on the stack at sp+8 (halfwords at sp+8, sp+0xA, sp+0xC, sp+0xE), a second copy at sp+0x10 for the marquee registrar 0x0306302A, then `mov r0, r1` with r1 = sp+8, r2 = node+0x70, r3 = 0, and the call at 0x0307EB36.

What the body does, in order (mod0_string_decomp.txt):

1. It copies the descriptor's two words into the draw state at 0x03023868 and 0x0302386C (fields +0x14 and +0x18 of the state struct at 0x03023854). It saves the previous values on entry and restores them before returning, through the copy helper at 0x0306D910 with destination 0x03023868. Those two words are the clip rectangle the glyph rasterizer works against.
2. It sets the pen in the display context struct at 0x0302385C: pen Y (+0x16) from descriptor +2, pen X (+0x14) from the alignment rule above.
3. It classifies the string with 0x03056910. If that returns 1 and the one-shot byte at 0x030237D0 is 0, the string is first converted into a stack buffer by 0x030569F0 and the copy is drawn. The title buffer takes the same path as the node names Display draws, with no special casing.
4. Per line, it measures characters with 0x030627BE, wraps at the descriptor width, and draws each character with 0x03062582. Line breaks are the halfword values 0x0A and 0x0D. The line advance is the context field +0x1A plus 12 when the font class field (+0x24) is 1, else plus 16. The loop stops when pen Y passes the context field +0x12; the first line is always drawn, so a one-line title does not depend on the +0x12 value.
5. If the byte at SAVEINFO+0x10 equals 0x0A, the draw loop takes the wide-character branch and composes adjacent characters through 0x03056B52 before rasterizing. A caller inherits this; it is not an argument.

The glyph path (glyph_mod17_decomp.txt): 0x03062582 fetches each character's record from the current font base (a pointer cell the mode pair maintains) with stride 0x20 in font class 1 and 0x21 in class 0, then rasterizes through 0x0306333E in mode 1 at the pen position. Nominal glyph cells are 8 by 16 px (class 0) and 6 by 12 px (class 1); 0x030627BE reads the per-glyph width from the record and applies the same special cases. After each glyph the pen advances by the glyph width plus the tracking field (context +0x18).

State interaction, the part the painter chain depends on after the hook returns:

- The clip words the routine writes (0x03023868, 0x0302386C) are saved and restored by the routine itself. Nothing outside keeps a value there across calls.
- Pen X is restored after every line. Pen Y is left advanced past the last line, but every call resets it from its own descriptor, and no painter-chain function reads it.
- The glyph rasterizer temporarily copies the mode A field (context +0x20) into the flags field (context +4) and restores +4 after each glyph.
- DrawImage (0x03063700) and the rectangle fill (0x030632FA) do not consume the text pen or the text clip. They set their own window clip on a different struct, 0x030238B8, through 0x03063F10 on every call.
- The one precondition stock callers create is the display-mode bracket. Display wraps each text call as: save = 0x0306316E(1); call 0x03062CEE; 0x0306316E(save). Mode A = 1 also matters inside the rasterizer: with the flags field holding 1, set glyph bits are plotted in the foreground color (context +0) and clear bits are not plotted at all, so text draws transparently over whatever is beneath it.
- Display also loads the two pen color halfwords at window entry, context +0 from the cell at 0x030235B6 and context +2 from the cell at 0x03023144, and restores the saved pair at exit. The specification below repeats that handling so the title takes the same foreground color as the browser's own text.

### Candidate (b): 0x0306333E and 0x03063444 are pinned, and they are not a text path

0x0306333E is a bitmap blitter. Its contract, from its prologue (it loads the stack pair with `ldrd r0, r5, [sp, #0x28]` after a 10-register push) and body (mod0_sibling_decomp.txt):

| Argument | Content |
|---|---|
| r0, r1 | x, y of the top-left corner, in pixels |
| r2, r3 | width, height, in pixels |
| [sp+0] | mode: 1 or 0x10; any other value returns immediately |
| [sp+4] | source pointer: a 1bpp bitmap in mode 1, raw halfword pixels in mode 0x10 |

The rectangle arguments are pixels, not cells. In mode 0x10 the routine calls the clip setup 0x03063F10(x, y, x + width - 1, y + height - 1), which clamps against 239 and 319, then walks single pixels and writes each source halfword through the framebuffer store 0x03063E60. In mode 1 it plots points through 0x030631F0, one per set bit, choosing between the two pen colors in the display context (halfwords +0 and +2) by the flags halfword at +4, with no clip call.

0x03063444 is the engine behind DrawImage. It takes (x, y, width, height) in r0 to r3 and a source offset as its stack argument. It stages raw pixels from `*(0x0302328C) + offset` through the copy step 0x030640A6 into a 1200-byte stack buffer, at most 600 halfwords per chunk, and after each chunk calls 0x0306333E with the mode fixed at 0x10 (`strd` of the constant 0x10 and the buffer pointer at 0x03063484). The copy step 0x030640A6 is a plain transfer primitive (it chains 0x03053F5E and 0x03056B94); the format it consumes is raw 16-bit framebuffer pixels, width * height halfwords, no header. The header for an image lives in the descriptor table that 0x03063526 reads for DrawImage.

Call-site evidence for how the pair is used in practice:

- Module 29, function at 0x0307D200: a per-character glyph blit. Stack pair = mode 1 and a record pointer computed as 0x0307DF0C + code * 64 from a table inside module 29's own segment; width and height are 8 and 16 when the font class field (context +0x24) is not 1, and 6 and 12 when it is 1 (calls at 0x0307D224 and 0x0307D238). The caller passes one character code per call; there is no string handling.
- Module 17, function FUN_0307d546 (flag segments 0x15B, 0x15D, 0x15E): mode 0x10, held in r4 from the assignment at 0x0307D56E and stored as the stack pair at each call; height is 1 and width, position, and source pointer come from window state halfwords (calls at 0x0307D5F0, 0x0307D60E, 0x0307D660, 0x0307D67E). One-pixel-high raw strips.
- Module 27's player Display draws its progress bar as repeated mode 0x10 blits of a small segment graphic, one call per filled segment.
- The text engine itself: 0x03062582 calls 0x0306333E in mode 1 for every glyph, which is the actual relationship between the two candidates. Candidate (b) is the rasterizer underneath candidate (a).

Verdict on (b): pinned to the standard the Bluetooth work met, and excluded. It draws bitmaps, not strings; there is no mode in which it accepts a UTF-16 string. Drawing the title through (b) would require rasterizing glyphs into a pixel buffer in the extension first, which reimplements the font engine that candidate (a) already is. The brief's description of the stack pair as "mode + string pointer" is corrected by the traces: the second stack word is a halfword buffer pointer, pixels in mode 0x10 and a 1bpp bitmap in mode 1. Recommendation: build on candidate (a).

### Build-ready specification: hold icon, then title

Hook: patch 0033 as pre-computed in the build report. Module 31, code, site 0x0307E89E, expect `e4f72fbf`, replace `fbf7b9bb` (B.W to the extension's lock-screen entry).

Entry state at the hook, from the segment disassembly (module 31 code at 0x0307E884 to 0x0307E89E): the painter has already test-cleared flag 0x2E, loaded the byte at 0x030230EC, and popped {r4, lr}. At the replaced instruction, r0 holds the image index (0x26 plus bit 2 of the byte at 0x030230EC), lr holds the painter's return address, and the stack is the painter's caller's stack. The displaced instruction is the tail call to DrawImage.

The extension routine performs, in this order:

1. Push the registers it will use, including lr.
2. Call DrawImage, 0x03063700, with r0 unchanged. This reproduces the displaced tail call as an ordinary call and draws the stock hold icon (image 0x26 or 0x27).
3. Load the byte at SAVEINFO+0x60 (0x030232A0 + 0x60). If it is not 1, pop and return. No text is drawn. This is the same gate the name buffer's snapshot uses.
4. Build the 8-byte descriptor on the stack: halfwords {11, 24, 231, 39}. The x extent (11 to 231) and the 16 px strip height (+6 = +2 + 15) are Display's proven values. The y position is the one free parameter: 24 places the strip directly below the status icon row. It is a placement choice, not a stock fact, and is the one number to confirm on hardware.
5. Save the display context pen colors (halfwords at 0x0302385C +0 and +2), then load context +0 from the cell at 0x030235B6 and context +2 from the cell at 0x03023144, matching Display's window-entry handling.
6. saved_mode = 0x0306316E(1).
7. Call 0x03062CEE(descriptor, descriptor, 0x030235CE, 0). Flags 0, left-aligned, as in Display. The string is the name buffer at 0x030235CE, UTF-16, already snapshotted from SAVEINFO+0x87 under the same +0x60 gate.
8. 0x0306316E(saved_mode). Restore the saved pen colors. Pop and return.

A title drawn this way appears when the 0x2E segment repaints, which is the event-only cadence the build report established (track and state changes). The title does not change during a track, so that cadence is sufficient for it. An elapsed-time readout would go stale between repaints for the same reason the build report named; blocker 2 below supplies its fields if a future revision adds a self-supplied repost.

## Blocker 2: position and total source

The candidate fields in the file-info struct at 0x03023980 are pinned. All three are words. Two structures frame every access: the codec object, whose pointer sits at 0x0304AD78 (control block 0x0304AD70, field +8), and the SAVEINFO mirror inside the struct at 0x030232A0.

| Field | Meaning | Units |
|---|---|---|
| +0x44 | Playback state: 1 while a track is active, 0 when none is | n/a |
| +0x48 | Position at which the current play segment was latched (track start or resume point) | milliseconds |
| +0x4C | Total duration of the current track | milliseconds |

### Field +0x44: playback state

Writer: the module 0 copy function at 0x030544A8 stores SAVEINFO+0x195 into +0x44 (`str r0, [r5, #0x44]` at 0x030544E0, with r5 = 0x03023980 and r3 = 0x030232A0, both from its literal pool). Readers test exactly two values. The module 0 playback monitor (0x03064F7E) reads +0x44 at 0x03064FB8 and takes its end-of-track path only when it equals 1. The module 33 resume handler at 0x030886B8 branches on == 0 (saved-position path) versus == 1 (active path). Module 27's player Display gates its time and progress segments on == 1. No reader was found testing any other value. (Module 33's codec-open and playback-task code also writes fields at +0x44 and +0x48, but on a different struct, its play-control block; the register bases there do not trace to 0x03023980, and those accesses are excluded.)

### Field +0x48: latched position, milliseconds

Writer: the same module 0 copy stores SAVEINFO+0x199 into +0x48 (0x030544E6). No other writer was found in modules 0, 27, 31, or 33, so during one play segment the value is constant. The live position is not here; it is the codec object's word +4, reached through the pointer at 0x0304AD78, and module 27's Display reads it from there directly.

Reader arithmetic, from module 27's player Display (FUN_0307ef4e, mod27_decomp.txt; in that decompile the struct is a halfword pointer, so +0x24 and +0x26 there are byte offsets +0x48 and +0x4C):

- Elapsed text (flag 0x40 segment): elapsed_seconds = live_position / 1000 minus +0x48 / 1000, clamped so it never goes negative, then split for display by 0x03056BE0 and rendered by the local helper FUN_0307e72c. The division by 1000 proves the millisecond unit.
- Progress bar (flag 0x4D segment): fill = ((live_position - +0x48) * 0x93) / (+0x4C - +0x48), a fraction of a 147 px bar. Both the elapsed text and the bar treat +0x48 as the zero point of the current segment.
- The module 33 resume handler reads +0x48 on its already-active path and seeks to +0x48 + 5000 (the constant 0x1388 loaded at 0x03088720, the store into the codec object's +4 field at 0x0308872E, the seek call 0x0308AAF4), i.e. 5 s past the latched position in the same millisecond domain.

### Field +0x4C: total duration, milliseconds

Writers: the module 0 copy stores SAVEINFO+0x19D into +0x4C (0x030544EC). The resume handler refreshes it from the codec object when it finds it zero: `+0x4C = *(pointer at 0x0304AD78)` at 0x03088716 to 0x0308871A, a verbatim copy of the codec object's word +0.

Unit proof: the codec object's word +0 is formatted by module 33's info helper at 0x0308875A, which divides it by 1000 for seconds (remainder kept as the millisecond part) and by 60000 (0xEA60) for minutes, and passes the parts to a printf-style call (0x0306D8F0 at 0x030887CC). The module 0 monitor's end-of-track test compares the codec object's live position (+4) against +0x4C and finalizes the track when position >= +0x4C (0x03065018 to 0x03065020), which puts +0x4C and the live position in the same unit. Module 27's Display uses +0x4C as the end point of the progress fraction above, and its remaining-time segment (flag 0x41) renders (+0x4C - +0x48) / 1000.

### The SAVEINFO side

The module 0 copy at 0x030544A8 mirrors a three-word record out of SAVEINFO (+0x195, +0x199, +0x19D) into the file-info fields, alongside the track name and index fields it also copies. SAVEINFO carries a second resume pair next to the flag the UI design already pinned: a word at +0x5C and the byte at +0x60. The resume handler (called from one site, module 33's status handler FUN_03088d9c at 0x03088E84) reads +0x5C as the saved position when the flag byte +0x60 is 1 and the state field +0x44 is 0; its seek value is +0x5C + 1, computed as (1000 * x + 1000) / 1000 at 0x030886F6 to 0x03088706, an exact +1 in the seek unit. It clears +0x60 itself after use (0x03088710, 0x03088754). On the consuming side, module 31's browser Service clears the pair together when the user selects a track: `strb.w sb, [r5, #0x60]` and `str.w sb, [r5, #0x5c]` at 0x0307E2D0 and 0x0307E2D4, with sb = 0 (set at 0x0307DF12) and r5 = 0x030232A0.

### Still open, named exactly

1. The save-side writer of the SAVEINFO record was not located: no store to +0x195, +0x199, or +0x19D, and no set-side store of the +0x5C/+0x60 pair, appears in the offset census over modules 0, 27, 31, and 33. The copy direction into the file-info struct is proven; the store that fills the SAVEINFO side, likely on a stop or power-down path and possibly moving the record through the copy engine at 0x03067510 (which a fixed-offset census cannot see), is the remaining gap. It does not affect the field meanings or units, which rest on the latch, the resume handler, and the player Display.
2. The trigger rate of the module 0 copy at 0x030544A8 was not pinned. It sits among module 0's message-unit callback registrations for channel 0x1B, but whether it runs per decoder status update or per track change was not established. That is why +0x48 is stated as a latched segment-start position rather than a live position: if the copy ran continuously, module 27's elapsed arithmetic (live minus +0x48) would sit at zero, and it is written as a running readout.
3. The intent of the resume handler's +5000 ms is inferred, not documented by any comment or string: on the already-active path it seeks 5 s past the latched position. The arithmetic and the millisecond unit are proven; the product reason is not visible in the code.

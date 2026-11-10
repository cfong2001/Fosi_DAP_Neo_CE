# Battery profiles: apply routine and selector hook, built

Scope: build the battery-profile feature designed in
`patches/power/power.md` (job 2 storage and apply path, job 3
selector hook). Offline only, scratch only: the live framework tree
and manifest were not touched, nothing was pushed, and the stock
image DP3_V137.img (SHA-256
`fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`)
was re-verified after the work.

**Verdict: experimental; not ready for selection or release.** The apply routine, the
defaults writer, the selector entry, and the two dispatch cave stubs
compile to a 540-byte blob with no undefined symbols. The selector
hook is two framework patch files, 0051 and 0052 (one per dispatch
copy), unstacked. A scratch framework build composes the whole
feature (grown module 32 plus both patches) and validates. The
emulation suite passes 33 of 33 checks. A new review found that the
proposed item ID 197 is already the stock brightness option "20%", the
timer and clock-table effects have no boot reapply path, and the clock
restore code assumes clock v1 was included in the build. Bounds for
persisted brightness, EQ and Bluetooth bytes are now checked before
passing values to stock code. The selector record, safe ID/labels and
boot behavior remain unresolved.

## Placement

The design left the apply routine's home open between a module 0
code cave and the module 0 region extension. Both are closed now,
on evidence recorded after the design was written:

- Module 0 dead space is exhausted. The resident-home census
  (analysis/resident_home, PR #24) found 8 bytes in three scraps.
- The module 0 package gap is live FAT workspace except its tail at
  0x0307BFB4..0x0307C7B0, and the tail composition (PR #28) fills
  2,040 of those 2,044 bytes with the M3U staging, the resolver
  hooks, and the Bluetooth blob.

So the routine lives in **module 32's own segment extension**, the
same mechanism the lock-screen routine uses in module 31 (insertion
rebuild, framework `--grow`, PR #27). Module 32's stock code segment
is exec 0x0307D164, length 0x3348, so the extension starts at
0x030804AC. The room ceiling is 0x03080B54, the first base in a
different residency class (modules 18 and 61, sub-overlays loaded by
other windows), which gives 1,704 bytes; the blob uses 540. The
mutual-exclusion argument is the census's: module 32 is a
window-manager window, only one window module is resident at a
time, and loading a window overwrites the shared VMA from its own
package bytes, so bytes past a window's stock end are exactly as
safe as the census found module 31's. Two supporting checks from
this pass: a byte-find over every extracted code segment finds no
absolute word pointing into the extension range
0x030804AC..0x03080B54, and module 32's only call to the generic
loader wrapper is the clear-slot thunk at exec 0x0307D1A4, which
loads the empty module 2; the settings window loads no sub-overlay
that could collide with its own extension.

Costs, stated plainly:

- The routine exists only while the settings window is resident.
  That is sufficient by construction: its only caller is module
  32's apply dispatch. There is no boot apply: the timer and clock
  table are RAM state and cannot be restored from the stored profile
  by the existing hook. Persistent profile behavior needs a verified
  resident boot path or a different design.
- The build gains one more grown module, and the Phase E
  window-cycle soak list gains module 32 (cycle settings in and
  out, confirm the extension bytes survive).

Every dependency of the routine is module 0 resident (the four
callees, the SAVEINFO struct, the clock table), so an overlay home
reaches all of it.

## The blob

Linked at 0x030804AC by `src/profiles.ld`; built by `build.sh`.
Payload is code and constants only, no .data and no .bss, which is
what the `--grow` byte copy expects.

| Part | Exec address | Bytes |
|---|---|---|
| `profile_area_valid` (static helper) | 0x030804AC | 40 |
| `profiles_write_defaults` | 0x030804D4 | 84 |
| `profiles_apply` | 0x03080528 | 260 |
| `profile_select` | 0x0308062C | 56 |
| `hook_dispatch_a` | 0x03080664 | 22 |
| `hook_dispatch_b` | 0x0308067A | 22 |
| Code section total (literal pools included) | | 484 |
| `profile_defaults` (3 entries of 8 bytes) | 0x03080690 | 24 |
| `clock_base_b` (8 rows of 4 bytes) | 0x030806A8 | 32 |
| Blob total | 0x030804AC..0x030806C8 | 540 |

The compiled code was audited by disassembly against the design
before emulation: the SAVEINFO offsets (active id read at struct
+0x293, Bluetooth write at +0x2D4, EQ compare and write at +0x68),
the TimerPeriodSet argument setup (timer 0, period in r2, zero in
r3, zero stack argument), the flag post argument 0xFB, the clock
loop's row stride of 0x1C with both B words written per row, and
the saver tail call with argument 1.

## Stock dependencies, each re-verified in the extracted segments

| Dependency | Address | Evidence |
|---|---|---|
| SAVEINFO live struct base | 0x030232A0 | Module 32's dispatch uses it as r6: item 173 writes [r6, 0x68], item 196 writes [r6, 0x14]; the literal sits in module 32's pools, first at exec 0x0307DEF8 |
| TimerPeriodSet | 0x030510A2 | Body stores r2:r3 as the 64-bit microsecond period and the first stack argument as the nanosecond part, then reprograms the timer. Key init's call (module 1, exec 0x0307D2DE) passes timer 0 in r0, 400 in r2, 0 in r3. r1 is not read |
| Backlight apply | 0x03064964 | The argument is the level: the body indexes its duty table with r0, and module 32's item 196 path calls it at exec 0x0307DF88 with r0 still holding the level byte it just wrote to +0x14. The apply routine passes the level the same way |
| Event flag post | 0x0306723C | r0 is the flag id; the body sets bit (id and 0x1F) in word (id div 32) of the flag bitmap |
| SAVEINFO saver | 0x0306CA10 | Argument nonzero writes the 0x55AA commit marker at struct +0x2F4; checksum 0x0306CAA6 runs over 0x17E0 bits and lands at +0x2FC; the struct is then written out |
| RAM clock table | 0x03079824 | 36 rows of 7 words, read from the extracted module 0 segment. Rows 18..22 stock B fields are 480 MHz; framework patches 0014..0018 (clock v1) set them to 288 MHz. Rows 23..25 are 36, 72, 140 MHz in every field, untouched by clock v1 |

## The apply routine

`profiles_apply` performs the design's steps in the design's
order. The order is not arbitrary: the magic and version check
comes first because it is the migration fail-safe (absent magic
means stock behaviour, byte for byte, with no writes and no
calls); the middle steps are independent, each writing a different
stock field through the same call the settings window itself uses;
and the saver runs last so the profile area and stock fields are
included in the save. Atomicity of the storage write has not been proven.

1. Validate the area (magic "PF", version 1, active id below 3).
   Any failure returns with no side effects.
2. Wheel: TimerPeriodSet with (0, period, 0, ns 0), period 400 or
   1000 by the entry's wheel code. An out-of-domain code skips the
   step.
3. Brightness: if the entry byte is in 0..5, write it to +0x14
   and call the backlight apply with the level as the argument.
   Module 1 bounds +0x14 to 0..5 at 0x0307DEA8–0x0307DEB2;
   the backlight call itself indexes a table without a bound check.
4. EQ: if the entry byte is in 0..6, post flag 0xFB only when
   the value differs from +0x68, then write +0x68. This is module
   32's item 173 shape; module 1 bounds +0x68 to 0..6 at
   0x0307DF92–0x0307DFA2.
5. Bluetooth: if the entry byte is 0 or 1, write it to +0x2D4.
   No call; module 81 reads the byte at its own init.
6. Clock cap: write the B core and B bus words of rows 18..25 to
   the active policy's values, computed from a base table the
   routine carries (clock v1 values: 288 MHz for rows 18..22, the
   stock 36, 72, 140 MHz for rows 23..25). Cap A takes the
   lossless rows to 240 MHz; cap B also takes the EQ rows to the
   72 MHz tier (36 and 72 stay, 140 becomes 72). Writing the full
   managed set on every apply makes policies order-independent:
   switching from cap B back to cap A restores the EQ rows, and
   policy 0 restores clock v1 exactly. An out-of-domain policy
   byte is treated as policy 0, converging the table to the known
   clock v1 state. Row id words, PLL fields, and A fields are
   never written.
7. Persist: saver with argument 1.

Two defaults in the design's table ship as the leave value 0xFF,
by the design's own rules, and are named constants in
`src/profiles.c` so each is a one-line change when its evidence
lands: `PROFILE_BRIGHTNESS_ENDURANCE` (the design's "lowest level
item 196 offers" cannot be read offline, since the descriptor is
built at runtime; no number is invented) and
`PROFILE_EQ_ENDURANCE` (the design ships selector 0 only after
preset 0 is confirmed to be the flat preset, and states the
default becomes 0xFF if it is not; the confirmation is
outstanding).

## Defaults writer and selector entry

`profiles_write_defaults` writes the full 32-byte area (magic,
version 1, flags bit 0 set, reserved zeros, the default entries)
with the chosen id as the active id. It writes the struct only;
the apply routine's saver call persists it.

`profile_select` is the entry the caves call with the chosen
option index. On a bad magic it writes the defaults first (the
migration path: first selection initializes the area, no boot
patch is needed); on a good magic it stores the id at +0x293 and
sets flags bit 0. Both paths end in `profiles_apply`. An id above
2 is ignored.

## The selector hook

Module 32's apply dispatch was disassembled from the extracted
segment (module 32 code, exec 0x0307DEC0..0x0307E01E). Shape: the
item record is in r4 (descriptor pointer at +8, value byte at +5,
already updated by the stock value editor before the dispatch
runs), SAVEINFO is in r6, and the item id is the descriptor
halfword at [record + 8]. The dispatch runs twice, once per edit
direction, and both copies need the special case:

- Dispatch A (after the decrement path), exec 0x0307DEE4: id 173
  branches to the EQ path at 0x0307DF6C, id 196 to the brightness
  path at 0x0307DF84, everything else to the generic post at
  0x0307DF8C.
- Dispatch B (after the increment path), exec 0x0307DFE0: id 173
  to 0x0307DFF8, id 196 to 0x0307E010, everything else to the
  function epilogue at 0x0307E198 (add sp, 0x1C; pop r4..fp, pc).

Both patch sites are clean: the 6 bytes at the second compare are
a self-contained compare, branch, branch sequence, and the cave
stub re-executes the displaced compare and branch before testing
the profile id, so non-profile items are behaviour-identical. The
stubs exit the way each copy's own special cases exit: dispatch
A's fall into the generic settings-changed post, dispatch B's go
straight to the epilogue. Calling through bl from the stubs is
safe because the enclosing function's prologue has saved lr, as
its own calls on these paths show (for example exec 0x0307DEDA).

The framework format is one address per patch file, so the single
change is two files, both unstacked:

- `0051-profile-selector-dispatch-a.patch`: site 0x0307DEEC,
  expect `c42849d04ce0`, replace `02f0babb00bf` (B.W to
  `hook_dispatch_a`, NOP).
- `0052-profile-selector-dispatch-b.patch`: site 0x0307DFE8,
  expect `c42811d0d4e0`, replace `02f047bb00bf` (B.W to
  `hook_dispatch_b`, NOP).

The branch bytes were produced by linking `src/sites.S` at the
site addresses, so the displacements are the linker's, and were
verified by decode-back. Both files pass the framework's
`check_patch_files.py`.

The profile item id 0xC5 (197) is a placeholder in `src/hooks.S`,
not a free profile label. In the pinned stock English language table,
196 is "Screen Brightness" and 197 is its "20%" option (see
`tools/rknano_image.py DP3_V137.img lang 2`). A complete selector needs
a proven record, non-conflicting labels in all languages, initialization,
and a reviewed identifier. The current hook must not be presented as a
finished feature.

Every one of the 266 stock string slots has a nonblank value in at
least one of the 21 language tables; no slot is blank across all
languages. A replacement requires a proven unused reference or a
validated language-table extension and new labels. No existing string
is repurposed here.

The boot apply cannot call this blob: it lives in module 32, which is
loaded as a settings window, while module 1 initializes the wheel timer
before that window is loaded. The resident-home census found only 8
bytes in module 0's verified dead stubs and the M3U/Bluetooth tail
composition leaves 4 bytes; neither holds this routine. A boot design
therefore needs a verified resident placement and ordering, rather than
a branch into this transient overlay. A clock-v1-off build also needs a
separate proven restore policy before profiles can be composed with it.

## Packaging proof

A scratch copy of the framework (in `scratch/framework`) took the
blob through the real build path: manifest plus 0051 and 0052,
`--grow 32:code:out/blob.bin`, `--no-transplants`. The build
passed the grown-image validator, and inspection of the composed
image shows module 32's code length at 0x3564 (stock 0x3348 plus
the 540-byte blob), the extension bytes equal to the blob byte for
byte, and both patch sites carrying the replacement bytes. The
live framework tree was not used for this and is unmodified.

## Emulation

`emu/emu_power.py` loads
the blob at its link base in a bare RAM map, seeds the clock table
from the stock segment with the clock v1 B values applied, and
intercepts the four callees with recording stubs. Memory-write
hooks watch the SAVEINFO struct and the clock table. 33 checks,
all passing:

- Case (a), magic absent: apply records no calls and no writes,
  and the struct stays all zero.
- Case (b), three profiles with distinct entries: the call
  sequence is exactly TimerPeriodSet, backlight (when the byte is
  not 0xFF), flag post (only when the EQ value changes), saver
  last with argument 1. Timer arguments are (timer 0, period 400
  or 1000, high word 0, stack argument 0); the backlight argument
  is the level. Leave bytes leave +0x14 and +0x2D4 untouched.
  Cap A writes 240 MHz to rows 18..22 and leaves the EQ rows at
  base; cap B also caps row 25 from 140 to 72 MHz; policy 0
  restores 288 MHz and 36/72/140 MHz over a deliberately dirtied
  table, with row ids, PLL fields, A fields, and all other rows
  byte-identical to stock.
- Case (c), selector cycle through the caves: selections presented
  as record value bytes 1, 2, 0 move the active id 0 to 1 to 2 to
  0, each persisted by exactly one saver call and each applying
  its profile (the seeded brightness byte lands at +0x14). The
  dispatch B cave selects and exits via the epilogue. Presented
  with items 196 and 173, each cave takes exactly the stock
  continuation (brightness branch or generic exit) with no calls
  and no writes.
- Case (d), first selection with the magic absent: the 32-byte
  area equals the defaults block with the chosen id, every byte
  of the area is written exactly once, the saver runs once, and a
  later selection preserves a hand-edited entry byte while
  updating the active id.
- Case (e), invalid stored brightness, EQ and Bluetooth values are
  left untouched and do not reach the stock backlight or flag functions.

## What stays unproven until hardware

The design's open items, kept exact:

1. Clock cap values (240 MHz lossless, 72 MHz EQ tier) are
   proposed, pending a hardware listening test for underruns.
   The Performance profile (policy 0) is unaffected.
2. The brightness level range and the EQ preset 0 identity are
   unread: item 196's descriptor is built at runtime, and preset
   0's flatness is unconfirmed. Until both land, the two
   Endurance defaults ship as the leave value (see the named
   constants above).
3. The verbatim-block string extent: the +0x290 placement rests
   on a census with no observed stock access in +0x1C7..+0x2B0,
   and only a hardware SAVEINFO dump after long-path playback
   proves the string never reaches +0x290. The magic check on
   every use is the mitigation if it ever does.

Separate from the hardware list, two offline follow-ons remain
before the patches can stack: the selector item record must be
authored with safe labels and an ID; timer and clock policies need a
verified boot reapply path. Clock-v1 restore values must also match the
chosen build. The module 32 window-cycle soak joins the Phase E list.

### Rebuilding the existing experiment

Run `sh patches/power/build/build.sh` with the ARM GNU toolchain on PATH,
then `python patches/power/build/emu/emu_power.py` with Unicorn installed
and the pinned image at `DP3_V137.img` or `FOSI_STOCK_IMAGE`. The build
refuses unresolved symbols, changed hook addresses, blob size, or patch
site bytes. The emulator obtains module 0 directly from that image rather
than requiring an undocumented extracted workspace. These checks exercise
the existing dispatch prototype; they do not create a reachable selector.

## Files in this directory

- `power_build.md`: this report.
- `src/profiles.c`: the defaults writer, the selector entry, and
  the apply routine.
- `src/hooks.S`: the two dispatch cave stubs.
- `src/sites.S`, `src/profiles.ld`: patch-site stubs and the link
  layout.
- `build.sh`: builds `out/profiles.elf`, `out/blob.bin`, and the
  two site byte strings.
- `0051-profile-selector-dispatch-a.patch`,
  `0052-profile-selector-dispatch-b.patch`: the selector hook,
  unstacked.
- `emu/emu_power.py`, `emu/emu_power_output.txt`: the emulation
  suite and its recorded output.
- `scratch/`: the framework copy used for the packaging proof and
  the composed image.

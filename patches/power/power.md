# Power workstream: idle patch and battery profiles

Scope: port nanitecfw's `power_idle` concept to the Neo (job 1), design the
battery-saving profiles settings bundle (job 2), and note where a profile
selector would hook into the settings UI (job 3). Offline only. Stock image
DP3_V137.img, SHA-256
`fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`,
verified before and after this work; the image was not modified.

## Job 1a: the input poll interval

### The Neo input architecture (all addresses are exec addresses)

The Neo does not poll input in a window loop. Input runs on two interrupt
and callback paths, both pinned by disassembly this pass:

1. Wheel: a hardware timer. Module 1 key init (exec 0x0307D2BA region)
   registers exception 0x23 (IRQ 19) with handler 0x03061ACC via the
   vector installer 0x030664E8, then programs Timer0. The handler at
   0x03061ACC does exactly two things: calls the timer interrupt clear
   0x03051240(0) (writes 1 to Timer0 EOI at 0x400E0018), then tail-calls
   the wheel quadrature decoder 0x03061936. Nothing else runs in this IRQ.
2. Keys and the ADC buttons: a SysTick callback. The key device node at
   module 0 data 0x030056A0 is a SYSTICK_LIST (layout per the SDK header:
   next, Counter, Reload, Times, pHandler) with Reload = 2 and
   pHandler = 0x03061AB3, the input task (key state machine 0x030617FE,
   ADC scan 0x0305FE0E, merge 0x03061686). Key init registers the node
   with the list insert at 0x03066754. The list head at data 0x030057C8
   holds pHandler 0x03066725, the tick incrementer 0x03066724, matching
   the SDK's SysTickHead initializer. The SysTick exception (0x0F) handler
   installed at module 1 exec 0x0307D3AA is the callback dispatcher
   0x03066844. Tick length is 10 ms by SDK design (Service.c in
   refs/rknanod-sdk equates 50 ticks with 500 ms); the Neo's own SysTick
   reload write was not isolated (no 0xE000E014 literal exists in the
   binary), so the 10 ms figure is SDK-corroborated, not binary-proven.
   At 10 ms per tick the input task runs every 20 ms, which makes the key
   state machine thresholds in ui_controls.md read correctly (debounce 2
   runs, long press 20 runs = 400 ms, power hold 100 runs = 2 s).

The playback window has no poll constant of its own. Module 31's window
and module 33's playback task consume the same input pipeline (event
flags posted by the dispatcher at 0x03061B16); module 33's task blocks on
event flags (its wait for event 0xEC at exec 0x0308A504), it does not
spin on a delay. `delay_ms` 0x03064944 is a busy wait (spin loop scaled
by the millisecond argument) used for hardware settle delays; it is not
an idle lever.

### The patch

TimerPeriodSet 0x030510A2 (SDK signature: timer number, 64-bit period in
microseconds in r2:r3, nanoseconds on the stack) has exactly one caller
in all 82 modules: module 1 key init, at exec 0x0307D2DE. The call site:

```
0307d2d4  movs     r3, #0              ; usTick high word = 0
0307d2d6  mov.w    r2, #0x190          ; usTick low word = 400
0307d2da  mov      r0, r3              ; timer number 0
0307d2dc  str      r4, [sp]            ; nsTick stack argument
0307d2de  bl       #0x30510a2          ; TimerPeriodSet
```

The Neo's wheel poll is therefore already at the Nano's stock value,
400 µs, and a single immediate raises it to nanitecfw's patched value:

- **Patch 0050-power-wheel-period-1000us** (in this directory): module 1,
  code, address 0x307d2d6, expect `4ff4c872`, replace `4ff47a72`
  (`mov.w r2, #0x190` to `mov.w r2, #0x3e8`). The replacement encoding was
  assembled with rz-asm and verified by capstone decode-back. Only one
  of the four bytes changes value (0xC8 to 0x7A).

### Scratch build proof

The framework was copied to work/power/scratch/framework (the copy is the
stock framework plus patch 0050 and one manifest line), and two
framework-only builds (`--no-transplants`, default build date) were run:

- Without 0050: 1,383 bytes differ from stock. This reproduces the
  merged framework diff exactly, which cross-checks the scratch setup.
  SHA-256 `679accbbe8eed9e900c5094ed0be97fc5fc305a1123a662cef66ce4ff664235f`.
- With 0050: 1,384 bytes differ from stock. SHA-256
  `797a8d7af02fe9a7c789e63077f44a00701e2e03fa274880e42f41b8dd2176b8`.
- Diff between the two builds: **5 bytes total**. One byte at image
  offset 0x59910 (the patch site; the instruction starts at 0x5990E and
  the changed immediate byte is the third), and the four trailer CRC
  bytes at 0xD00000..0xD00003, recomputed over the changed content. No
  date, header or mirror differences. Both builds passed the framework's
  own `firmware_patch.validate()`.

The transplant build was not used for the proof because the scratch copy
cannot resolve the vorbis transplant path; the transplant is a disjoint
module 75 replacement and cannot interact with a module 1 immediate.

### Responsiveness trade-off

- **Key latency added: 0 ms.** Keys are not sampled by the wheel timer.
  They run on the 20 ms SysTick callback path above, which the patch
  does not touch.
- Wheel latency: the decoder at 0x03061936 confirms a step only after a
  consistent three-sample phase sequence (ui_controls.md section 1.1).
  Raising the sample period from 400 µs to 1000 µs adds at most
  (3 − 1) × 600 µs = **1.2 ms** to a wheel step event.
- Max trackable wheel speed falls by the same ratio: a step needs three
  samples inside one phase dwell, so the ceiling drops from about
  833 steps/s to about 333 steps/s. Normal flicks are far below either.
- Gain: Timer0 IRQ wakes fall from 2,500/s to 1,000/s (−60%). This IRQ
  fires for the life of the device, including screen-off playback and
  idle, so it is the dominant periodic wake source after SysTick
  (100/s). Each wake runs the interrupt clear plus a full quadrature
  decode pass.

## Job 1b: WFI in idle

**Verdict: design only. The Nano's premise does not exist on the Neo.**

On the Nano, stock firmware already had a main loop WFI that was gated
off while the screen was on; nanitecfw's patch removed the gate. On the
Neo there is no idle WFI to ungate:

- Module 0 contains exactly one WFI instruction, the stub at 0x03055B70
  (`wfi; bx lr`). Its only module 0 caller is at 0x030564E0, inside a
  serial/DMA transfer wait that polls a channel status byte between
  WFIs. The same stub pattern appears in the codec overlay modules
  (41–57, 61, and module 3), always in transfer waits. The decoder
  modules 71–80 have their own WFI stubs in the core 1 runtime. No
  main-loop, window-loop or idle caller exists anywhere in the image.
- The SDK's designed idle path (Common/System/Os/OsHook.c `Os_idle()`:
  codec suspend, FREQ_IDLE clock request, `__WFI`, resume on play-key
  GPIO) has no counterpart in the binary. Nothing requests clock id 0;
  clock_table.md records row 0 (IDLE) as solver-internal only.
- Apparent extra WFI/WFE hits at 0x0306E224 and 0x0306E6FC are data
  tables inside the code segment (desynchronised linear decode), not
  instructions.

What a WFI patch would need: an insertion of the form "if no event flags
pending, execute WFI" at the window manager's run loop, so the CPU sleeps
between the work the flags describe. WFI wakes on any enabled interrupt,
and the wake sources are all interrupt driven (SysTick, wheel timer,
SARADC IRQ 20, DMA completions), so the pattern is safe in principle.

Blocker: the window manager's run loop was not isolated to an address in
this pass. Window dispatch is table driven, and the event flag helpers
(test 0x0306729C, test-and-clear 0x03067258) have dozens of call sites
across module 0, so no single spin point can be named from call sites
alone. Pinning it needs a Ghidra decompile pass over the window manager
(the FUN_03065FD4 region is the largest flag consumer and the first
place to look), or a hardware trace. Until the loop is pinned, any WFI
patch would be speculative bytes, so none is shipped.

Note the interaction: even with a correct WFI loop, the CPU still wakes
every SysTick (100/s) and every wheel IRQ. Patch 0050 cuts the wheel
wake rate by 60% and ships now; the WFI work is worth doing after, and
its remaining win is bounded by the SysTick rate.

## Job 2: battery profiles design

### Storage

Profiles live in the SAVEINFO verbatim block, struct offsets
+0x1C7..+0x2D4 (270 bytes, restored by the memcpy at module 1 exec
0x0307E15C on every boot; see saveinfo_lock.md section 1.6 for why
nothing outside this block survives).

Stock use of the block, from the direct-literal struct xref census and
the load pass disassembly:

- +0x2B1, +0x2B2: read by module 81 (Bluetooth). Off limits.
- +0x2D1: gate byte for the block copy itself. The load pass copies it
  first; values 0–5 take the verbatim memcpy branch, values 6 and above
  take a branch that memsets the whole block to zero (call at module 1
  exec 0x0307E14A to the memset wrapper 0x03054E66). Off limits, and the
  design must never write it.
- +0x2D2: overwritten by the load pass when +0x2D3 is nonzero
  (module 1 exec 0x0307E168). Off limits.
- +0x2D3: read by module 81. Off limits.
- +0x2D4: Bluetooth state byte. This is a profile lever (below), owned
  by stock code; the profile area must not alias it.
- +0x1C7..+0x2B0 (234 bytes): no stock access appears in the census. The
  block is the record's string and large-field area, so an uncensused
  string writer growing from +0x1C7 is the residual collision risk.
  Mitigations: place the profile area late in the free span, keep it
  small, and validate a magic on every use (below). Verifying the
  string's real extent needs a SAVEINFO dump from hardware after
  playing a long-path file; that is a hardware-phase check.

Profile area: **+0x290..+0x2AF, 32 bytes.** A string would need at least
202 characters to reach it. +0x2B0 stays untouched as a guard byte
before the Bluetooth cluster.

| Offset | Size | Field |
|---|---|---|
| +0x290 | 2 | Magic `0x50 0x46` ("PF") |
| +0x292 | 1 | Layout version = 1 |
| +0x293 | 1 | Active profile id (0, 1, 2) |
| +0x294 | 1 | Flags; bit 0 = profiles written by user selection; rest 0 |
| +0x295 | 3 | Reserved, zero |
| +0x298 | 8 | Profile 0 entry (Performance) |
| +0x2A0 | 8 | Profile 1 entry (Balanced) |
| +0x2A8 | 8 | Profile 2 entry (Endurance) |

Entry layout (8 bytes each). Every field uses a stock value domain;
0xFF in a byte field means "leave the stock field unchanged".

| Byte | Field | Domain |
|---|---|---|
| +0 | Wheel period code | 0 = 400 µs, 1 = 1000 µs (patch 0050 values) |
| +1 | Brightness | SAVEINFO +0x14 level byte, or 0xFF = leave |
| +2 | Bluetooth | +0x2D4 byte value (0 = off, 1 = on), or 0xFF = leave |
| +3 | EQ selector | +0x68 selector byte, or 0xFF = leave |
| +4 | Clock cap policy | 0 = none, 1 = cap A, 2 = cap B (below) |
| +5..+7 | Reserved | zero |

Clock cap policies act on the RAM copy of the clock table at module 0
exec 0x03079824 (the firmware executes module 0 from SRAM, and the
solver 0x03066EFC reads the table on every request/release, so runtime
writes take effect at the next request or release; a profile switch
during steady playback shows its clock effect at the next track or
feature transition):

- Cap A: rows 18–22 (FLAC, ALAC, APE, DSD-DFF, DSD-DSF) B core/bus
  fields capped at 240 MHz, the tier clock v1 proved for OGG.
- Cap B: cap A plus rows 23–25 (EQ) capped at the 72 MHz tier.

Both caps are **proposed values**. Clock v1's 288 MHz for the lossless
rows was a conservative choice, and the decoder harness does not model
time, so only a hardware listening test can clear 240 MHz for FLAC.
Performance (policy 0) is exactly the shipped clock v1 behaviour and
needs no validation.

### The three profiles (defaults written on first selection)

| Field | Performance | Balanced | Endurance |
|---|---|---|---|
| Wheel | 400 µs | 1000 µs | 1000 µs |
| Brightness | leave | leave | lowest UI level (note 1) |
| Bluetooth | leave | leave | off (0) |
| EQ selector | leave | leave | 0 (note 2) |
| Clock cap | none | none | cap A |

Note 1: the brightness level range is set by settings item 196's
descriptor, which is built at runtime and was not read in this pass.
The apply mechanism (below) is fully specified; the Endurance default
is "the lowest level item 196 offers", a build-phase constant to fill
in from that descriptor, not a number invented here.
Note 2: selector value 0 is the first EQ preset position. The build
phase must confirm preset 0 is the flat/off preset before shipping the
Endurance default; if it is not, the default becomes 0xFF (leave).

### Apply path

This is the core of the feature. Two halves:

**Runtime apply (the only new code).** A single apply routine, invoked
when the active profile changes, performing these steps in order. Every
call target is proven above or in the cited workstream docs:

1. Read the active entry from the live struct's profile area. If the
   magic or version does not match, do nothing (stock behaviour).
2. Wheel: call TimerPeriodSet 0x030510A2 with (0, 400 or 1000, 0)
   according to entry byte +0. This is the same call key init makes;
   it reprograms Timer0 LOAD_COUNT and re-enables it (disassembly of
   0x030510A2 this pass).
3. Brightness: if entry byte +1 is not 0xFF, write it to struct +0x14
   and call the backlight apply 0x03064964, the same pair module 32's
   item 196 path executes at exec 0x0307DF86.
4. EQ: if entry byte +3 is not 0xFF and differs from struct +0x68,
   write +0x68 and post flag 0xFB via 0x0306723C, mirroring module 32's
   item 173 path at exec 0x0307DF6C.
5. Bluetooth: if entry byte +2 is not 0xFF, write it to struct +0x2D4.
   Module 81 reads +0x2D4 at its init and state paths (xref census), so
   the stored value takes effect at the next Bluetooth init or mode
   load; the apply routine does not drive the radio itself.
6. Clock cap: if entry byte +4 is nonzero, write the capped B fields
   into the RAM clock table rows named by the policy. If zero, restore
   the clock v1 field values (the apply routine carries both value
   sets as constants; they are the clock_v1 patch values).
7. Persist: call saver 0x0306CA10(1). The profile area and stock
   fields are included in the saved struct. Timer configuration and
   the clock table are separate RAM state and do not automatically
   follow the saved profile after reboot; the save's atomicity has
   not been proven.

The later prototype is built in module 32's segment extension; see
`build/power_build.md`. Its hooks have no reachable selector item.

**Boot apply: still needed.** The selected ID and certain stock fields
are saved, but the timer period and clock-table changes require an
explicit reapply after their stock initialization. Patch 0050 provides
a fixed wheel default, not the active profile's setting. A suitable
resident hook and its ordering are not yet proven.

### Migration

- Feature built, user has never selected a profile: the block holds
  stock data, the magic is absent, apply is never invoked, and nothing
  is written. Behaviour is byte-for-byte stock. This is the default
  state and the failure state for every error path.
- First selection (via the job 3 selector): the selector writes the
  full 32-byte area (magic, version 1, flags bit 0 set, the default
  table above, the chosen active id), then calls apply, which ends in
  the saver. From then on the area round-trips in the verbatim block.
- Corrupt or foreign record: if +0x2D1 is 6 or above, stock boot zeroes
  the whole block before the profile area is ever read (load pass
  branch at module 1 exec 0x0307E142), so profiles revert to defaults
  in the safe direction. A block whose magic fails (for example the
  string-collision case) is treated the same: no apply, no writes.
- Downgrade to stock firmware: stock ignores the area. It sits inside
  the verbatim block and is checksummed and restored like any other
  byte there. The only interaction is the string caveat under Storage.

The prototype also assumes clock v1's values when restoring the table;
it is incompatible with a build that turns clock v1 off unless its
restore logic is redesigned. The placeholder item ID 197 is already
the stock brightness option "20%" and cannot serve as a new label.

### Checksum interaction

No patch needed. Verified against the saver disassembly recorded in
saveinfo_lock.md sections 1.1 to 1.3: the checksum routine 0x0306CAA6
takes its length in bits; save and load both pass 0x17E0, covering
struct bytes [0, +0x2FC), which contains the whole verbatim block. The
saver 0x0306CA10 recomputes the checksum over the live struct and
stores it at +0x2FC before copying the struct into the stored image,
and module 1's boot write-back recomputes it again. Any profile bytes
in the block are therefore checksummed correctly by stock code on
every save.

### What the profiles deliberately do not claim

Screen-off and lock behaviour. The brief's candidate offsets for the
lock-disable byte (+0x13, +0x1A, +0x1C, +0x2E7) are still candidates
after this pass. The settings save path was traced: module 32's apply
dispatch special-cases only item 173 (EQ) and item 196 (brightness);
every other item, including whichever one owns the lock setting, flows
through the generic path where the value-to-SAVEINFO-offset binding
lives in descriptor fields built at runtime (menu struct at data
0x03024834). Pinning the offset needs that runtime descriptor table
decoded, which is the named next step. Until then no profile field
touches screen-off or lock timing.

## Job 3: selector hook site (follow-on, not built)

The settings window is module 32 (not the module 5 or 21 family; those
are the mode applet and its relatives per saveinfo_lock.md section 2).
A profile selector fits module 32's existing item machinery:

- Add a settings item whose record follows the 12-byte item layout
  (descriptor string id at [desc+0], option count at [desc+0xE], value
  byte at record+5), with three options naming the profiles.
- In module 32's apply dispatch (the compare chain at exec
  0x0307DEE4–0x0307DF92, where items 173 and 196 are special-cased
  before the generic flag 0xC6 post at 0x0307DF8C), special-case the
  new item the same way: write the chosen id to profile area byte
  +0x293 (writing the full default area first if the magic is absent)
  and call the apply routine from job 2, instead of posting the
  generic settings-changed flag.

That is UI workstream territory (same techniques as its custom
controls work) and is recorded here as a follow-on only.

## Blockers and open items

1. **WFI patch: blocked** on pinning the window manager run loop
   (job 1b). No speculative bytes shipped.
2. **Screen-off/lock SAVEINFO offset: not pinned.** Profiles exclude
   the lever. Next step: decode module 32's runtime-built item
   descriptors, or dump the menu struct from hardware.
3. **Clock cap values (240 MHz lossless, 72 MHz EQ): proposed,**
   pending a hardware listening test for underruns. Performance
   profile is unaffected.
4. **Brightness level range and EQ preset 0 identity:** build-phase
   constants to read from item 196's descriptor and the EQ preset
   table before the Endurance defaults ship.
5. **Verbatim block string extent:** the +0x290 placement is argued
   from a census with no observed stock access in +0x1C7..+0x2B0, but
   only a hardware SAVEINFO dump after long-path playback proves the
   string never reaches +0x290.
6. **SysTick period (10 ms):** SDK-corroborated, not binary-proven.
   It affects only the stated 20 ms input task cadence, not the
   patch (which is in microseconds at the Timer0 register level).

## Deliverables in this directory

- `power.md`: this document.
- `0050-power-wheel-period-1000us.patch`: the one built patch.
- `scratch/`: the framework copy used for the proof builds, both
  proof images and their build reports (`report_with.json`,
  `report_without.json`).
- `callsites.py`: BL/BLX call-site sweep used for the TimerPeriodSet
  and WFI stub caller censuses.

# UI features build report

Scope: the two features designed in `work/ui_features/ui_features.md`, built
offline in `work/ui_features/build/`. All work happened in scratch trees.
The live manifest and framework were never edited, nothing was pushed, and
the stock image still hashes to the pin
`fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`
(verified after the builds).

Result in one line: the Bluetooth shortcut is built and emulation-verified.
The lock-screen information feature is design-only: two of the design doc's
load-bearing identifications were refuted by trace evidence, and the
remaining renderer contract is named below as the blocking trace.

## Feature 1: Bluetooth shortcut (built)

### Side-effect resolution

Each module 21 handler extra was traced to its consumers before the
replica was written. Full evidence: `evidence/bt_side_effects.md`.

| Item | Verdict | In the replica |
|---|---|---|
| Post flag 0x123 | Needed. The resident BT poll (0x030657AC) answers it with the "CL" + device-name frame, status byte 2, flags 0x1B8/0x1B4 | Yes |
| Call 0x03053242 | Needed. UART channel 3 re-init at 115200, driver state reset, channel enable, RX IRQ registration | Yes |
| Write 0x0300416C = 1 | Needed. One-shot enable the poll tests before sending the CL frame | Yes |
| Write 0x0300416E = 0 | Bookkeeping. Resets a re-run countdown no nonzero writer exists for | Yes, for stock parity |
| Write 0x0300416F = 0 | Bookkeeping. The supervisor re-syncs this SAVEINFO +0x2D3 shadow itself | Yes, for stock parity |
| Call 0x03065772(0x53) | Needed. Queues the "CS00" command frame to the BT module (posts flag 0x1B8) | Yes |
| Copy tick [0x03023298] to [0x03004174] | Needed. Starts the poll's 300/400-tick debounce intervals | Yes |
| Flag 0x1B2 producer | Window-armed. The RX interrupt handler (0x030512C4) is registered only inside UART configure 0x0305654E, reached from BT-family overlays; it persists once armed | Resolved by the 0x03053242 call above, which the replica makes before the banner poll, in the stock cycle's own order |

The window-armed producer was the feature's main functional risk: toggled
from the player with no BT window visited since boot, a replica that
skipped the UART re-init would poll a banner flag nobody can set. The
replica arms the receiver itself. After power-on, the resident supervisor
(0x03065FD4, called from the main dispatch loop) runs the BT poll whenever
SAVEINFO +0x2D4 == 1, so the CL handshake and TX drain proceed from the
player context with no window involved.

One deliberate deviation from module 21's letter: module 21 runs its
post-on writes unconditionally because its cycle restarts a module that
was live 200 ms earlier. The replica runs the post-on envelope only when
the power-on routine reports success, so a banner timeout leaves the
state byte at the 0 the routine itself wrote instead of claiming on.

### What was built

- `src/hooks.S`: dispatcher hook, entered by branch from the patched
  site. Compares r4 against 0x20000001; on match calls the toggle and
  returns 0 through the stock epilogue (`pop.w {r4-r11, ip, pc}`); on any
  other word it performs the stock `mov r0, r4` plus the identical
  epilogue. No other register or stack state changes.
- `src/bt_toggle.c`: the toggle in freestanding C. Power-on is a
  transcription of the module 81 build at 0x0307D1A8 (pin 7 raise, 5000 ms
  banner poll on flag 0x1B2 against buffer 0x0300642C, result byte
  0x03023124, status byte 0x0300411C, timeout power-down), wrapped in the
  module 21 cycle envelope in stock order. Power-off is the GPIO low
  sequence all three stock paths agree on, state bytes +0x2D4/+0x2D3
  cleared, 200 ms settle. Only module-0 resident helpers are called.
- `scratch/framework/patches/0032-ui-bt-dispatcher-hook.patch`: module 0,
  code, 0x03061E5E, expect `2046bde8f09f`, replace `17f0d9be00bf`
  (B.W to the extension base plus a NOP). Added to the scratch manifest
  copy `patches/manifest_ui_scratch.txt` only.
- Build note: the first generated branch encoding targeted a linker
  veneer instead of the hook (the linker had placed the patch section at
  a default address and inserted a long-branch stub). Emulation caught it
  executing literal-pool bytes. The shipped bytes were regenerated with
  an explicit linker script and disassembly-verified as
  `b.w 0x03079C14`.

### Blob layout and size

Standalone link at the extension base 0x03079C14 (`src/ext.ld`,
`build_ext.sh`), 436 bytes total:

| Offset | Content |
|---|---|
| +0x00 | `ui_dispatcher_hook` (28 B), the patch 0032 target |
| +0x1C | `bt_gpio_low_all` |
| +0x80 | `bt_toggle` (power-on routine inlined) |
| +0x400 | Reserved for the lock-screen entry; unpopulated in this build |

Against the shared 11,164-byte extension cap, assuming the M3U parser's
composed footprint of 3,729 bytes is also present: 436 + 3,729 = 4,165
bytes used, 6,999 bytes of headroom. The blob is linked at the extension
base; if the coordinator composes it at a different offset, the link
script base and the two branch targets (patches 0032, and 0033 when it
lands) must be regenerated, which the site-patch snippets under
`scratch/` do mechanically.

### Scratch build

`scratch/out_bt.img`, SHA-256
`2cf872c2f7d87100501368bf3188ea88c3ac2f9b2ca8d62aee5d90e10ba0373b`.
The build applied all 33 manifest patches plus the extension step;
`firmware_patch.validate()` passed (header mirror, trailer CRC, V137
layout). Module 0 code_len grew 0x29C14 to 0x29DC8.

Incremental diff against a base scratch build (same manifest, no 0032,
no extension): 425 changed bytes in 27 ranges, confined to four places:
the code_len record at file 0x210 (2 B), the patch site at file 0x3B50A
(6 B), the extension blob span at file 0x532C0 to 0x53473, and the package
CRC at file 0xD00000 (4 B). Nothing else moved.

### Emulation

`emu/emu_bt.py` maps module 0 code and data from the scratch-built image
at their load addresses, plus the peripheral windows the code touches,
and enters at the patched site 0x03061E5E with the dispatcher's register
and stack state at its generic return. `delay_ms` is intercepted and
recorded rather than executed (its busy loop derives its count from a
clock word that reads 0 in a bare map and would underflow); every other
instruction runs for real, including the flag helpers, the stock UART
re-init chain, the banner poll loop and the command queue. Full output:
`evidence/emu_bt_output.txt`. Six cases, all pass:

| Case | Result |
|---|---|
| 0x20000001, BT off, banner "CV15" pre-set | Return 0; +0x2D4 = 1; result byte = 5; status = 0; GPIO port 2 level bit 7 set (level register 0x50030000, from the firmware's own port table); 0x0300416C = 1; tick copy written; flags 0x123 and 0x1B8 posted; delays 100 + 10 ms plus 1 ms inside the stock UART init chain |
| 0x20000001, BT on | Return 0; +0x2D4 = 0; +0x2D3 = 0; port 2 level bits 7/17/16 all 0; one 200 ms delay; no 0x123 post |
| 0x20000001, BT off, banner never arrives | Poll runs the full 5000 x 1 ms; timeout path powers back down; status byte = 7; +0x2D4 back to 0; no post-on writes |
| 0x10000001 (short-press Power) | Pass-through: return value equals the event word, zero peripheral writes, zero delays |
| 0x20000010 (type 2, other key) | Pass-through, same as above |
| 0x40004000 (type 4, OK release) | Pass-through, same as above |

In every case the saved register frame was restored exactly and control
reached the return address.

## Feature 2: lock-screen information (design-only)

### Resolved by the traces

Full evidence: `evidence/lockscreen_unknowns.md`.

- Cadence is event-only. No periodic poster of painter flags 0x27 to 0x2E
  exists in any module; posters are the painter template's arg-1
  self-repost, the invalidate helper 0x03063A32(1) on draw transitions,
  and change-only state handlers. The dispatcher's countdown path posts
  only 0x95/0x24, which the painter does not consume. A title drawn at
  hold engagement is compatible with this; a ticking elapsed readout is
  not, and would need a self-supplied periodic repost that does not exist
  yet.
- The name buffer 0x030235CE is a UTF-16 wide string (one code unit per
  halfword, NUL-halfword terminated), snapshotted from the track-name
  field at SAVEINFO +0x87 by module 31's Service, gated on SAVEINFO +0x60
  == 1: the same gate the design chose, and the buffer's intended use.
- The hook site stands: module 31 painter flag-0x2E segment tail, the
  B.W at 0x0307E89E. Patch 0033 is pre-computed and ready to file once a
  renderer lands: module 31, code, 0x0307E89E, expect `e4f72fbf`,
  replace `fbf7b9bb` (B.W to the reserved lock entry at extension
  +0x400). The extension routine must first perform the stock hold-icon
  draw (DrawImage 0x03063700 with image 0x26 plus bit 2 of the byte at
  0x030230EC) and only then add text.

### Refuted premises

- 0x030632FA is not a text draw. It is a rectangle fill: its stack
  argument is a 16-bit pixel value passed by value into the framebuffer
  store at 0x03063E60, proven from the function body and 87 call sites
  (the traced provenance is the contents of the halfword color cell
  0x030235B4). The design doc's section 1.7/2.8 identification is wrong.
- 0x0306316E and 0x0306314A are not position getters in any unit. They
  are a get-and-set pair for two display-mode halfwords of struct
  0x0302385C (+0x20 and +0x24), returning previous values in the 0/1/2
  class. Callers use them to bracket rendering with mode save/restore.
  No playback position comes out of them.

### Blockers, named

1. Renderer contract. Two candidates, neither pinned to the standard the
   BT work met. (a) 0x03062CEE, the string routine module 31's Display
   itself calls: entry is r0 = r1 = pointer to a caller-built struct,
   r2 = UTF-16 string, r3 = flags; the struct's halfword fields at +0,
   +2, +4 and its first two words are consumed as draw state, but the
   field semantics live in module 31 Display's frame setup
   (0x0307E9A0 to 0x0307EB24), a region linear disassembly desyncs on.
   The missing trace is a skipdata-aware disassembly or a Ghidra
   decompile of Display 0x0307E8F2 plus the 0x03062CEE body, read
   together. (b) The sibling renderer 0x0306333E and its wrapper
   0x03063444 (mode 0x10, stack pair mode + string pointer): the missing
   traces are concrete argument values at the module 17/29 call sites,
   whether the rectangle arguments are cells or pixels, and the source
   format the wrapper's copy step 0x030640A6 consumes. Drawing through a
   half-read layout engine also risks the shared clip and cursor state
   (set by 0x03063F10) that the stock painter chain uses immediately
   after the hook returns.
2. Position and total source. Untouched by this pass: the candidate is
   the file-info struct 0x03023980 fields +0x44/+0x48/+0x4C as used by
   module 33 around 0x030886B8. Field meanings and units are unproven.

What ships when blocker 1 clears: the 0033 patch above, an extension
routine at +0x400 that draws the stock icon, tests SAVEINFO +0x60, and
renders the title from 0x030235CE. Elapsed and total wait on blocker 2.

## Files

- `src/hooks.S`, `src/bt_toggle.c`, `src/ext.ld`, `build_ext.sh`: blob
  sources and build.
- `scratch/framework/patches/0032-ui-bt-dispatcher-hook.patch`,
  `scratch/framework/patches/manifest_ui_scratch.txt`: the hook patch
  and the scratch-only manifest.
- `scratch/ext.bin` (436 B), `scratch/out_bt.img`,
  `scratch/out_base.img`: built blob and images.
- `emu/emu_bt.py`, `evidence/emu_bt_output.txt`: emulation harness and
  its recorded run.
- `evidence/bt_side_effects.md`, `evidence/lockscreen_unknowns.md`:
  the two trace reports this build rests on.

# Round 2: stub family, module 21, Bluetooth window, module 35, and the remaining unknowns

Image: `DP3_V137.img`, SHA-256 `fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`.
All findings are from offline disassembly (Capstone, per-module, the 0x0307d164 and
0x0308c694 windows are shared, so every disassembly below is module-pinned).
Confidence labels: **proven** = instruction-level evidence; **likely** = converging
structural evidence; **unknown** = not established.
Helper scripts in this folder: `tbbdis.py` (TBB-aware disassembler), `rawdis.py`,
`family_diff.py`, `family_summary.py`, `mod33_table.py`, `scan_refs.py`,
`win_scan.py`, `bl_hist.py`, `bt_hunt.py`, `launch_scan.py`.

Headline results

1. The 0x0308c694 family (modules 41–57) is the per-codec system-core interface
   driver, one codec-agnostic command handler, instantiated once per codec slot
   (10 populated, 7 empty reserved slots). Mechanism fully traced (§1).
2. **Bluetooth window: found.** The BT power/response machinery lives in window
   modules 81 (primary candidate for the Bluetooth settings window) and 21,
   which link the same BT power routine. The BT state byte is SAVEINFO +0x2D4,
   and the toggle routine is a concrete callable at a fixed window address (§3).
   This supersedes round 1's "no callable toggle" conclusion: there is no
   module-0-resident toggle, but the window-linked routine is callable whenever
   module 21 or 81 is loaded.
3. Module 21 is the system/playback service window: it hosts the complete
   firmware-update flow (the only module that calls the updater), BT power
   management, and playback-resume messaging (§2).
4. Module 35 is the DSP/EQ coefficient master-table payload; module 36 is its
   consumer, expanding preset descriptors into runtime coefficient RAM (§4).
5. Of the 28 round-1 unknowns: 11 proven, 13 likely, 3 identified as window
   applets with purpose unresolved, 1 still unknown (module 7).

---

## 1. The 0x0308c694 stub family (modules 41–57): per-codec interface driver

### 1.1 Layout

All populated members (41, 42, 50, 51, 52, 53, 54, 55, 56, 57) execute at
0x0308c694 and share one template with two entry points:

- +0x00 (optional), completion callback stub (8 bytes):
  `*(u16*)<flag> = 1; bx lr`. The flag address is a literal pointing into the
  module's own data window at 0x0304de34 (offset varies by build, see §1.4).
  Modules 41 and 51 lack this stub (their dispatcher sits at +0x00).
- +0x08 (or +0x00), command dispatcher:
  `int handle(int cmd, void *arg)`, a TBB jump table over the command number.

Modules 43–49 are zero-length records: the family occupies module slots
41–57 = 17 codec slots, of which 10 are populated, exactly matching the
10 second-core decoder programs (modules 71–80).

### 1.2 How module 33 dispatches into the family (proven)

Module 33 (codec dispatcher) holds:

- a current-codec index word at 0x0304b4d4 (module 34's log string
  'ERROR!!! CurrentCodec == 0x%02x' reads the same global; 0xFF = no codec),
- a 10-entry function-pointer table at 0x030489a4 in its data:
  `{0x0308c695, 0x0308c6a1, 0x0308c69d, 0x0308c695, 0x0308c69d ×6}`, i.e. the
  callback stub (+0), the dispatcher post-prologue entry (+0xC), and the
  dispatcher entry (+8), repeated per codec; all entries point into the shared
  window because only one stub module is resident at a time,
- a halfword-pair table at 0x030489cc (mostly (12,12) pairs) indexed by a
  sample-rate code byte in module 33's rate-mapping function at 0x0308ac54
  (compares against 44100/22050/16000/8000 Hz constants).

A series of small wrappers in module 33 (e.g. at 0x0308ab8a, 0x0308aba8,
0x0308abc6, 0x0308abe4, 0x0308ac02, 0x0308ac20) all follow one pattern:

```
idx = [0x0304b4d4];  if (idx == 0xff) return -1;
ip  = table[idx];                       // table at 0x030489a4
r0  = <command>;  r1 = <arg>;  r2 = 0;  bx ip;   // tail-call the loaded stub
```

Commands observed at these wrappers: 5, 6, 10, 11, 13, 15, 17.
Separately, module 33 loads the stub modules itself: its per-codec branch
blocks at 0x0308888c–0x0308ca2 call the segment loader `0x03067870(module_id, 7)`
with module_id = 41, 42, 43, 50, 51, 52, 53, 54, 55, 56, 57 (43 included;
loading the empty record is part of the table-driven sequence). So codec
selection in module 33 picks both the second-core decoder (71–80) and the
matching system-core stub (41–57).

### 1.3 The dispatcher: command map (proven from module 54; identical in all members)

Signature `handle(cmd, arg)`; return 1 = success/handled, 0 = unsupported,
2 = special state (cmd 10). Variant A (41, 50–57) normalises with
`subs r0, r0, #3` and accepts commands 3–18; variant B (module 42) takes
raw commands 0–18 with 0–2 falling to the default block. All state references
are to module 33's codec structures, not to per-stub state:

- codec info struct at 0x0304b47c (module 33 BSS),
- completion words at 0x0304adc8 / 0x0304adcc / 0x0304add8 / 0x0304addc
  (module 33 BSS, beside the decoder control block at 0x0304ad70),
- config-selector byte at 0x030489a0 (module 33 data).

| cmd | behaviour |
|----:|-----------|
| 3 | `*arg = [0x0304b47c + 8]`; return 1 (getter) |
| 4 | `*arg = [0x0304b47c + 0x10]`; return 1 (getter) |
| 5 | `*arg = [0x0304b47c + 0x14]`; return 1 (getter) |
| 6 | `*arg = [0x0304b47c + 4]`; return 1 (getter) |
| 7 | `*arg = [0x0304b47c + 0]`; return 1 (getter) |
| 8 | mailbox send (1, 0); poll [0x0304adcc] up to 20,000,000 iterations (loop body calls 0x030611e0, 0x030531f6, delay 0x03064920(1)); then require [0x0304addc] == 0 |
| 9 | return 0 (unsupported) |
| 10 | **DMA playback start.** Reads play-state fields of 0x0304b47c (+0x24 state, +0x28 flag, +0x2c repeat-one, if state==1 and +0x2c==1, fail; if +0x28==1, return 2; if +0x28==0, set it and mailbox-send (4, 0)). Builds a DMA descriptor on the stack from an **embedded 2-entry config table** in its own code (module 54: at 0x0308c930, two identical 16-byte records `{0x00812024, 0x00000c00, 7, 0}`; entry selected by byte [0x030489a0]), registers **its own +0 callback stub (0x0308c695) as the DMA completion callback**, calls 0x0305ff48 (DMA setup) and 0x0305ff74 (DMA start, the same function the gapless trace found programming DMA channel 5 → I2S TX 0x40030024), then WFI-polls (0x0305b70) until the callback sets the flag halfword, and writes the active buffer pointer (0x0303f9a0 or 0x030369a0, both module 33 data) to `*arg` |
| 11 | return 0 (unsupported) |
| 12 | mailbox send (4, 0); return 1 (no wait) |
| 13 | return 0 (unsupported) |
| 14 | mailbox send (11, arg); poll [0x0304adc8], timeout 200,000 |
| 15 | mailbox send (13, arg); poll [0x0304add8], timeout 48,000,000 |
| 16 | return 0 (unsupported) |
| 17 | `*arg = [0x0304b47c + 0xc]`; return 1 (getter) |
| 18 | reserved, its TBB target lands inside the jump table itself |

The "mailbox send" pair is two module-0 register-block writers:
`0x0306d0d8(value, index, field)` writes `0x40110000 + index*0x50 + {8,0x10,0x18,0x20}[field]`
and `0x0306d0ac(value, index, field)` writes the adjacent fields
`{0xc,0x14,0x1c,0x24}[field]`. The stub calls them as
`0x0306d0d8(cmd_word, 0, 1)` then `0x0306d0ac(0, 0, 1)`, a (command, arg=0)
pair into block 0 of the 0x40110000 inter-core register block, followed by
polling a shared-SRAM completion word. The getters (fields +0, +4, +8, +0xc,
+0x10, +0x14 of the info struct) are the codec-info values module 33's UI
side consumes (duration/position/bitrate-class fields; exact field semantics
belong to module 33's struct, not to the stub).

### 1.4 Member differences: no codec-specific data (proven)

The hypothesis that members differ by an embedded codec id or table pointer
is disproven. Byte-level comparison shows all ten members reference the
*same* state addresses (0x0304b47c, 0x0304adc8–dc, 0x030489a0), the *same*
mailbox command words (1, 4, 11, 13), the *same* timeouts
(20,000,000 / 200,000 / 48,000,000), and the same output buffers. Differences
are only:

- presence of the 8-byte callback stub (absent in 41, 51),
- command-base convention (module 42 takes raw 0–18; the rest subtract 3),
- the completion-flag halfword address in the module's own data window:
  0x0304de34 (42, 50, 52, 54, 56, 57), 0x0304de38 (53), 0x0304de48 (55);
  modules 41/51 poll a word in module 0's data area instead (literals
  0x03004478 / 0x0300447a),
- TBB case-block layout order and literal-pool placement (linker variation),
  hence the differing code lengths (0x2a0–0x2e4). Modules 54, 56, 57 are
  byte-identical; 53 and 55 differ from them by exactly one byte, the low
  byte of the flag-pointer literal.

Conclusion: the per-codec differentiation lives entirely in the
second-core decoder program (71–80) and in module 33's selection logic. The
stubs are one codec-agnostic system-core glue driver, the codec's
open/close/play/pause/seek + info interface to the calculation core,
replicated per slot by the SDK's module system.

---

## 2. Module 21: the system/playback service window (and firmware-update host)

### 2.1 WIN struct (proven)

Module 21 data at 0x030247c4 is a framework WIN struct:

| field | address |
|-------|---------|
| +0x08 Service | **0x0307d2c5** |
| +0x0C Key | **0x0307dac1** |
| +0x10 Display | **0x0307e525** |
| +0x14 Init | 0x0307d165 (shared framework stub) |
| +0x18 DeInit | 0x0307d1b5 (empty `bx lr` stub at 0x0307d1b4) |

The Key handler's volume actions use the same resident audio functions as
modules 31/32 (volume up/down helpers at 0x0307d628 / 0x0307d658 operate on
SAVEINFO +0x12, clamp 120, call 0x030570e8, post flag 0x19a). Display
(0x0307e524) was not decoded instruction-by-instruction.

### 2.2 Service handler (0x0307d2c4): full flow (proven)

Prologue saves the framework frame; `sl` = SAVEINFO base 0x030232a0
throughout. Branches, in order:

1. Sentinel branch. If SAVEINFO +0x2E2 == 0x55: send message
   (type 0xa, payload halfword 3) via 0x03067452 and return 1
   (path at 0x0307d41e).
2. Update block, entered when event flag 0x18c is pending
   (test-and-clear 0x03067258 at 0x0307d2d8; if clear, skip to step 3).
   The block at 0x0307d2ec is a shared block: Service falls into it from
   the 0x18c test, and the 0x18b branch (step 3) calls it with BL. It does:
   - *Display refresh:* saves two state halfwords at 0x0302385c, reads the
     playback time getters 0x0306316e(1) / 0x0306314a(2) (elapsed/total,
     the same getters the UI applets use), draws images 0x93 and 0x94 via
     the GUI blit 0x03063242 (after a 0x03063700(0) draw call), restores the
     saved halfwords, re-reads the getters, calls 0x0306448a (GUI flush).
   - *Settings prep:* if SAVEINFO +0x29 != 2: set +0x29 = 2, +0x3E
     (halfword) = 1, +0x0F = 2, +0x0E = 2; call mode-set 0x0305791a(2).
   - *Save + update:* call 0x0306ca8c (the settings load helper; the saver is 0x0306ca10); delay 200 ms
     (0x03064944(0xc8)); load module 8 via 0x03067870(8, 7); call
     updater-main 0x0307e64c.
   - Result == 0 → success branch at 0x0307d434 (see §2.3).
   - Result != 0 → set SAVEINFO +0x3E = 1 and continue to step 3.
3. Confirmation / commit gate (0x0307d392). Test-and-clear event flag
   0x18b. If set: call the update block (0x0307d2ec) again, reload
   module 8 (0x03067870(8, 7)), call slot-sync 0x0307e5b0, then reset
   with 0x030536a6(0, 0). If clear: fall through.
4. Post-update state branch (0x0307d3b4). If SAVEINFO +0x3E == 1:
   apply audio state via 0x030570e8 / 0x03057040 (args from 0x03023d38 and
   module 33's table at 0x03036988), clear SAVEINFO +0x60 (hold state),
   call 0x030570a4, send message type 0xd (payload 0), return 1.
5. Flag 0x16c branch (0x0307d3be). If test-and-clear 0x16c succeeds:
   volume-apply via 0x030570e8; on result 1, send message type 3
   (0x0307d478) and post flag 0x17d / 0x16a (paths at 0x0307d480/0x0307d4ba).
6. Playback-resume branch (0x0307d3da). Reads SAVEINFO +0x3E, +0x85
   (current-track halfword), +0x2A, +0x60 (hold). If +0x85 == 0x63 (source
   code 99) or hold is on: clear the word at 0x03023924 and take the
   0x0307d4ec / 0x0307d52c paths (the latter re-checks SAVEINFO +0x29 == 4
   and builds a play context with source code 0x63 written to
   [fileinfo + 0xf2], the same play-context construction module 24 does).
   Otherwise, if +0x2A != 0 and hold is off, it builds a type-2 message
   {0x51, track index fields} and sends it via 0x03067452, the playback
   request for the selected track.
7. Flag 0xdd (0x0307d50a). If test-and-clear 0xdd succeeds, post flag
   0x32.
8. Bluetooth restart branch (0x0307d51a). Test (non-clearing,
   0x0306729c) flag 0x1bd; if it reads 1 and the local state word r4
   is 0, run the BT power-cycle at 0x0307d574 (§3.3).

### 2.3 Success branch at 0x0307d434 (proven)

When updater-main returns 0:

```
r0 = [0x03023d38];  bl 0x030570a4        ; audio-path stop/teardown
r0 = 0;             bl 0x0306ca10        ; the settings saver (its sibling
                                         ; 0x0306ca8c is the load helper)
str r5(=0), [0x40120004]                 ; write 0 to the 0x40120000
                                         ; inter-core block, register +4
b .                                      ; infinite loop, halt
```

So a successful updater-main leaves the device in a deliberate halt loop
after zeroing an inter-core register, the running firmware does not
reboot itself on this path; it waits for an external reset/power cycle
(the boot/slot machinery then takes over). The contrasting nonzero path
commits via slot-sync and a software reset (0x030536a6(0,0)) under the
0x18b gate.

### 2.4 What launches module 21 (proven negative + boot evidence)

- No module loads module 21 by an immediate loader call. An exhaustive
  scan of all 82 modules for `0x03067870` / `0x0306777a` calls with tracked
  r0 immediates finds loader calls for modules 2, 8, 10, 11, 12, 18, 19,
  20, 24, 25, 26, 33, 34, 36, 37, 38, 39, 41, 42, 43, 50–57, 61, 62,
  never 21 (and never 3, 4, 5, 6, 7, 9, 17, 21, 29, 30, 32, 81: the other
  window applets are likewise never loaded by immediate). Loader calls
  always pass r1 = 7.
- Module 21 itself is a *loader client* only for module 8
  (0x03067870(8, 7) at 0x0307d380 and 0x0307d3a4). Module 21 is the only
  module in the image that calls the updater.
- Activation is therefore by the framework window manager (module 0),
  which loads window modules from its registration data, the generic
  computed-id loader call sits at module 0 @0x0306743e (r0 not an
  immediate), and dispatches Service callbacks on event flags.
- Boot connection (proven): module 0's startup thread (from the reset
  handler 0x03061f8a) directly calls module 1's functions in the shared
  window (0x0307d4d0, 0x0307d3fe, 0x0307d550, 0x0307d5cc at
  0x03061f94–0x03061fba), then tests flags 0x18b and 0x18c
  (0x03061fc2–0x03061fd6, non-clearing test 0x0306729c): if 0x18c is
  set, it sends window-manager message type 0 (0x03067452 at
  0x03061fe6 / 0x03062002), the activation path that brings up the first
  window with the update flag pending, which module 21's Service then
  consumes. If 0x18b is clear it calls 0x0305434e; if set, it skips that
  call. The flag bitmap lives at 0x03023cf8, inside the persistent SRAM
  region (≈0x03022800–0x03024400) whose RTC bytes the reset handler
  explicitly preserves, consistent with 0x18b/0x18c surviving the warm
  reset 0x030536a6(0,0) so a two-boot update sequence can work.

**Verdict:** module 21 is not launched by any peer applet or by
update-file detection inside another module; it is a window-manager
window whose Service handler is the firmware's update/BT/playback-state
service. Nothing in the image "detects an update file and starts 21".
The trigger state is the 0x18c flag, tested at boot by module 0 and
consumed by 21's Service.

### 2.5 Event flag 0x18b: poster not found (proven negative)

- Consumers: module 21 Service, test-and-clear @0x0307d396 (gates
  slot-sync + reset); module 0 boot thread, test @0x03061fc6.
- An exhaustive scan for a poster, `mov/movw r0, #0x18b` (or #0x18c)
  feeding the post function 0x0306723c in any of the 82 modules, finds
  zero posters for either flag. No data table (u16 or u32) anywhere
  contains 0x18b/0x18c as an entry (the only u16 hits are coefficient
  noise inside modules 35 and 71 data).
- The flags belong to the 0x18x system family (0x189 = settings-dirty,
  posted by module 1 per round 1). Because module 0 tests both flags at
  startup, before any window runs, and the bitmap sits in
  reset-preserved SRAM, 0x18b is best explained as a boot/update state
  flag set by an earlier boot stage or a previous session (module 1's
  validator stage is the natural candidate for the 0x18c "update
  pending" setter, but no setter instruction was located for either).
- The dialog-confirmation theory is weakened: a live dialog result
  would be posted from window code with an immediate flag id, and none
  exists. Within a running session, 0x18b *functions* as the commit gate
  for the destructive slot-sync + reset step, but its producer is
  outside the traced immediate-call graph, stated plainly: **who posts
  0x18b is not established; that it is not posted by any immediate call
  in the image is proven.**

---

## 3. Bluetooth: found (window modules 81 and 21; state byte SAVEINFO +0x2D4)

Round 1 established that no module contains Bluetooth stack/driver strings
and that the menu strings 10, 130–132, 166–171 belong to module 32's
settings menu. Round 2 hunted the hardware side: GPIO helper calls
(mux 0x030526f8, direction 0x03056098, level 0x030560d2) with recovered
(port, pin) arguments, and UART register-base literals, across all modules.

### 3.1 Where the BT hardware is touched (proven)

The (port 2, pin 7) BT-power triplet, mux → direction-out → level,
appears in exactly five modules: 0, 1, 21, 32, 81. No overlay
references a UART register base directly; module 0's peripheral table
holds the candidate UART bases 0x40130000–0x40170000, and the BT UART
traffic runs through module 0's serial code (the BT response buffer is in
module 0's BSS at 0x0300642c).

**SAVEINFO +0x2D4 is the Bluetooth on/off state byte (proven by
consumers):** the power-on routine writes 1 to it, power-off/timeout
paths write 0, and module 32's settings code reads/writes it at
0x0307d87c, 0x0307dc96, 0x0307e5d8, it is the settings menu's BT switch
value. (Round 1's SAVEINFO map left +0x2D4 unassigned; this resolves it.
Byte +0x2D3 is a companion BT state byte read/written by module 21's
Service at 0x0307d580 / 0x0307d612.)

### 3.2 The BT power routine (proven; linked into 21, 32, 81)

Entry 0x0307d1a8 in module 81's build, 0x0307d1b6 in module 21's
build (same source, window-relative addresses). Behaviour, from full
disassembly of both builds:

1. Initialise a timeout counter to 0x1388 (5000).
2. mux(2,7,0), dir(2,7,1), level(2,7,1), GPIO2.7 high = BT power on;
   write 1 to SAVEINFO +0x2D4.
3. Poll up to 5000 times: call 0x030611e0, test-and-clear event flag
   0x1B2 (0x03067258). On the flag, read the response buffer at
   0x0300642c and compare its first bytes against 'C', 'V', '1'
   (0x43/0x56/0x31, the BT module's boot banner). On a match, byte
   [buffer+3] is compared with 0x35 ('5') and a derived value (5 if
   equal, else 0) is stored to byte 0x03023124 (BT version/state byte).
   Failing iterations delay 1 ms (0x03064944(1)).
4. On timeout: mux/dir/level(2,7,0) (power off), mux/dir/level
   (2,17,0) and (2,16,0) (UART pins GPIO2.16/2.17 driven low), write 0
   to SAVEINFO +0x2D4, delay 10 ms, return 0.

Module 81's build also posts event 0x1B4 when the 0x1B2
event fires, and on timeout writes 7 to byte 0x0300411c (module 0 data).

### 3.3 Which window owns Bluetooth

- Module 81, strongest candidate for the dedicated Bluetooth window
  (likely). Its data holds a WIN struct at data+0x10 (link fields
  zero): Service 0x0307de3f, Key 0x0307d91f, Display 0x0307d8ab,
  Init 0x0307dd03 (own), DeInit 0x0307ddd9. It has five literal
  references to the BT response buffer 0x0300642c (pools at 0x0307d5d0,
  0x0307deec, 0x0307e310, 0x0307e724), repeated response-parse 'C'
  compares (0x0307e0e2, 0x0307e0ec, 0x0307e10a, 0x0307e3a2), two internal
  callers of the power-on routine (0x0307d30e, 0x0307dc6c), and the
  largest applet data section (0x31c). No BT strings exist anywhere, so
  the identification rests on the response-buffer and power-routine
  density, which no other unexamined module approaches.
- Module 21, a second BT-aware window (likely BT audio/player
  applet). Its Service handler, on event flag 0x1BD, runs a complete
  BT power cycle inline (§2.2 step 8): read SAVEINFO +0x2D3; drive
  (2,7), (2,17), (2,16) low; write SAVEINFO +0x2D4; delay 200 ms; post
  event 0x123; call module 0 fn 0x03053242; delay 100 ms; call the BT
  power-on routine (its build at 0x0307d1b6); write state bytes at
  0x0300416c/0x0300416e/0x0300416f; call 0x03065772(0x53); write SAVEINFO
  +0x2D4 and +0x2D3; copy [0x03023298] → [0x03004174]. Module 0 posts
  flag 0x1BD itself at 0x0306587c (and 0x1B4 at 0x03065836), the BT
  event family (0x1B2 response-ready, 0x1B4 ack, 0x1BD restart-request)
  is serviced by module 0's serial/input code and consumed by windows
  21 and 81.
- Module 32 (settings menu) carries its own linked copies of the BT
  GPIO triplet blocks (0x0307d886, 0x0307e5ea, 0x0307fc4e) and the +0x2D4
  accesses above: flipping the Bluetooth item in Settings drives the
  hardware directly rather than delegating to window 81.

### 3.4 Toggle callability: revised verdict

Round 1 concluded there was no global BT on/off function a shortcut
could call. That holds for module 0 (no resident exported toggle), but
it is no longer the whole story:

- A concrete callable routine exists at a fixed window address whenever
  the owning overlay is resident: 0x0307d1a8 with module 81 loaded,
  0x0307d1b6 with module 21 loaded (power-on with banner handshake;
  the power-off path is the routine's timeout branch and the explicit
  GPIO-low sequences in module 21's 0x1BD handler and module 32's switch
  blocks).
- The state any shortcut must keep consistent is SAVEINFO +0x2D4
  (1 = on), with +0x2D3 as a companion state byte in module 21's flow.
- A BT shortcut patch therefore needs the target window loaded (or must
  load it via 0x03067870 first), a real constraint, but "nothing to
  call" is retracted.

**Established later (2026-11-08):** the UART is UART1 at `0x400B0000`,
pin group A (GPIO2.16/2.17), 115200 baud with divisor 13, set by
module 0's serial driver. Every Bluetooth power-on path calls the
generic configure routine `0x0305654E` with channel 3 and 115200
(`patches/ui_features/build/evidence/bt_side_effects.md` item 2). That
routine maps channel 3 to UART index 3 / 3 = 1 (`r0 * 0xAB >> 9` at
`0x03056554`), writes `0x02000000` to GRF `+0xBC` and muxes GPIO2.16 and
2.17, then calls the hardware init `0x0305134C`, which looks the base up
in the table at `0x0306DD94` (index 1 = `0x400B0000`) and writes the
divisor `1,500,000 / baud` (integer division) into the divisor latch.
`tools/emu_bt_uart.py` runs this stock code under Unicorn and logs
divisor 13. With the TRM's formula, baud = sclk / (16 x divisor), and
the 24 MHz clock the driver's constant assumes (1,500,000 = 24 MHz / 16),
the line runs at 115,385 baud, 0.16% fast. NeoPod v1.7.0 programs the
same controller with the same register sequence and plays Bluetooth
audio on the Neo.

**Not established:** whether the scan/pair screens belong to 81 or to a
state of 21/32 (strings 166–171 are module 32 menu items; 81 is inferred
from buffer references); the 'CV1' banner protocol beyond the version
byte check at [buffer+3]; the identity of module-0 call 0x03065772(0x53)
in module 21's cycle (plausibly a UART send/init).

---

## 4. Module 35 (data) + module 36 (code): DSP/EQ coefficient machinery

### 4.1 Pairing (proven)

Modules 34, 35, 36 share one slot: code window 0x0308bed4 (34 and 36),
data window 0x0304b604 (35's payload; 36 declares data_len 0 because the
payload is a separate module record). Only one of 34/36 is resident at a
time; 36 is the consumer designed for 35's data, its code references
0x0304b604 (×4), 0x0304b624 (= 35 data +0x20, ×2) and 0x0304caa8
(= 35 data +0x14a4, ×2), plus module 33's EQ coefficient table at
0x0304aef4, and module 33 loads module 36 from its codec-setup path
(0x03067870(36, 7) at 0x0308ae1a and 0x0308ae96, beside the biquad-scale
function 0x0308aec8). Module 36 also calls module 33 functions
0x0308ac48 (×2, a repacking thunk that tail-branches to
0x0306780a(0x23, …), a framework service call), 0x0308bbac and 0x0308bcc8.

### 4.2 Module 36's main function (0x0308bed4) (proven mechanics)

1. Copies a 62-byte input descriptor from its argument pointer to a
   stack buffer (memcpy 0x03054e34, length 0x3e) and logs it via
   0x0306d8f0 with a format string inside its code tail.
2. A TBB on the descriptor's selector value (0–8) collapses to five
   categories (0–4); per category it normalises a pattern of halfword
   fields inside the descriptor (category 0 fills slots 0x18–0x1e with
   the value 12; category 1 fills 0x1a–0x1e; categories 2–4 clamp the
   halfword at +0x3c, with 3/4 also byte-truncating it).
3. Two service calls through thunk 0x0308ac48 with computed offsets into
   a ~51,250-unit destination space:
   - src 0x0304b624 (35 data +0x20), offset = 25000 + category × 5250,
     length = 5250;
   - src 0x0304caa8 (35 data +0x14a4), offset = category × 5000,
     length = 5000.
   The arithmetic closes: 5 categories × 5000 = 25000 and
   25000 + 5 × 5250 = 51250 = module 35's payload size − 2. (Units,
   bytes vs halfwords, and the direction of the 0x0306780a(0x23, …)
   service call are not established; do not quote the mapping beyond
   the arithmetic.)
4. A loop over 21 entries: reads signed halfwords from the
   descriptor at +0x14, compares each against 12, sets/clears a flag
   byte at record +0xa, computes record addresses into the table at
   35 data +0x20 with a stride pattern ((i × 125) + value × 10 + 8)
   halfwords, scales a record halfword (+8) by ×0x2000 >> 13, and
   writes result halfwords into a runtime DSP-state struct at
   0x03022ac0 at offsets +0x2a0, +0x2a2, +0x2f4, +0x2f6, and finally
   +0x348/+0x34a. (0x03022ac0 is in the persistent runtime region.)
5. A second loop over 10 entries copies 5-word (20-byte) records
   from the table at 35 data +0x14a4, indexed by descriptor values, into
   destination 0x03022e10 + entry × 16 + 0x140…+0x150, clearing
   bytes in a parallel array.

### 4.3 Module 35 semantics (likely)

The payload (51,252 bytes, entropy 7.23, head = 32-bit word pairs such
as 001f7dcf / fff081ab) is a set of master coefficient/curve tables
for the audio DSP/EQ path, organised in (at least) two regions: a
halfword curve region from +0x20 addressed by (band, value) strides,
and a 20-byte-record region from +0x14a4. Module 36 expands a compact
preset descriptor (62 bytes; per-category patterns; the recurring
constant 12 matches the ±12 dB EQ range and the 21-entry loop matches
a 21-point curve/band structure, both consistent with, but not proven
by, the EQ context: the 0x0304aef4 coefficient-table reference and the
0x0308aec8 biquad-scale call) into the runtime structures at
0x03022ac0 / 0x03022e10.

**Not established:** the exact DSP feature (graphic-EQ preset curves vs
a spatial/bass effect), the Q-format of the stored words, and the unit
semantics of the two service-call regions. The word-pair head structure
is consistent with interleaved fixed-point coefficient pairs; it is not
(address, value) pairs, the addresses module 36 computes are pure
arithmetic on category/value indices, never read from the payload.

---

## 5. Remaining modules: verdicts and the loader graph

### 5.1 Loader relationships (proven; underpins several verdicts)

Segment-loader calls 0x03067870(id, 7) found by scan (site lists in
`launch_scan.py` output): module 0 → computed id (window manager,
@0x0306743e); 1 → 2; 5 → 38, 39; 9 → 10; 10 → 11, 12, 2; 17 → 18;
18 → 19, 20; 21 → 8; 23 → 24, 25, 26; 27 → 18, 33; 29 → 61; 30 → 2 (×5);
31 → 2; 33 → 34, 36, and stubs 41, 42, 43, 50–57; 38 → 37, 2; 39 → 2 (×3);
61 → 62, 2. Loading module 2 (an empty record) recurs as an idiom,
plausibly "no sub-overlay / clear slot". Window applets (5, 6, 9, 17,
21, 29, 30, 32, 81) are never loaded by a peer, the window manager
(module 0) activates them, as established for module 21 in §2.4.

### 5.2 Per-module verdicts

- 3: display blit/fill worker (likely). No data, no WIN. Shares the
  two-entry stub shape with the codec family: entry +0 writes halfword 1
  to the shared word at 0x030247c0; main fn at 0x0307c7b8 takes rectangle
  arguments (computes (x2−x1+1) × (y2−y1+1)), loads a 16-byte config from
  0x0306e1a4, calls 0x0306d77e, 0x0306d2a0(0, 6) and the DMA setup
  0x0305ff48. A DMA rectangle-transfer (fill/blit) primitive for the
  display path.
- 4: LCD panel init / display-controller config (likely; the panel
  command sequence at 0x0307ce68–0x0307d05e was proven in round 1).
  Same stub shape as 3 (flag word 0x030247c0); its early functions write
  the 0x40110000 register block via the 0x0306d124 / 0x0306d2ec /
  0x0306d2a0 writer family (args (0, 0x800), (0, 0x28), (0, 0x10), …)
  before the panel init sequence. Not a window.
- 5: settings-save / library service window (likely). WIN struct:
  Service 0x0307d3f7, Key 0x0307d5f7, Display 0x0307d5fb (terminal stub,
  effectively no paint), Init 0x0307d38d (own), DeInit 0x0307d3f5. Code
  contains the string 'save ok' and loads modules 38 (media enumeration)
  and 39 (sort engine) at 0x0307d278 / 0x0307d28a, consistent with a
  headless service applet that persists settings and triggers
  library-rescan work rather than a user-facing screen.
- 6: window applet, purpose unknown. Textbook WIN: Service
  0x0307d18f, Key 0x0307d1ed, Display 0x0307d23b, Init = shared stub
  0x0307d165, DeInit 0x0307d17f. No strings, 0x17c bytes of code. Too
  small to name.
- 7: still unknown. No data, no WIN; BSS 0x10000 (64 KiB). Calls
  only the device-read wrapper 0x030678ca (×5) and a small pointer table
  at 0x0307a024–0x0307a060; contains the fixed-point constant
  0x51eb851f. A sector-loading worker (resource/font-class loading is a
  guess only). Role not established.
- 9: USB-mode window (likely). WIN: Service 0x03080529, Key
  0x030805ad, Display 0x030806cd, Init 0x03080323 (own), DeInit
  0x030804b3; own window base 0x0307ffdc, data at 0x030475d0. It loads
  module 10 (USB device core) at 0x03080480, the only window that does,
  which makes it the applet that owns the USB connection screens and
  brings up the USB stack (modules 11/12 are then loaded by 10).
- 17: metadata-using window (likely). WIN: Service 0x0307d1f3, Key
  0x0307d3e1, Display 0x0307d547, Init 0x0307d199 (own), DeInit
  0x0307d1d5. Loads module 18 (metadata/cover parser) at 0x0307d17c.
  Which screen (track-info vs library detail) is not established.
- 19: cover-art decode worker for module 18 (likely). No WIN.
  Shares window 0x03085a4c with 20; BSS 0xfb20. Loaded by module 18 at
  0x030838de. Heavy internal call graph (own fn 0x0308792a ×48), logging
  calls 0x0306d8ce ×24, memcpy ×7, a compute-heavy transform of the
  class an image decoder (JPEG being the largest-format candidate)
  needs. Exact format not established.
- 20: second media worker for module 18 (likely). No WIN; BSS
  0x8444; loaded by module 18 at 0x03080c80; its one external call into
  the shared window is to 0x03080b54 (module 18's entry). A companion
  decode/resize worker; exact role not established.
- 25, 26: scan/list helper objects of module 23 (likely). Both are
  loaded by module 23 (0x0307e318 / 0x0307e33a) and share module 24's
  data base 0x0302585c. Their data is a small vtable of the
  0x0307e9c0-family shape (module 25: code pointers at +0x0c…+0x1c,
  targets 0x0307e9e1 / 0x0307e9e5 / 0x0307eb6d; module 26: the same
  pointers shifted by one word), category list providers for the
  scan/sort bookkeeping, siblings of module 24 (play-context builder),
  not windows.
- 29: window applet, purpose unresolved. WIN: Service 0x0307d32d,
  Key 0x0307d903, Display 0x0307d5ed, Init 0x0307d241 (own), DeInit
  0x0307d2c1. Code 0x10b0 but sparse (48% zeros; only the first 0x918
  nonzero). Loads module 61 at 0x0307d2fa, it launches or embeds the
  module-61 function (§ below).
- 30: window applet with a sub-vtable, purpose unresolved. WIN:
  Service 0x0307d193, Key 0x0307d731, Display 0x0307db1d, Init = shared
  stub, DeInit 0x0307d17f; plus a second five-pointer table at data+0x24
  (0x0307e045, 0x0307e985, 0x0307ed45, 0x0307df23, 0x0307dfe1). At
  0x2060 bytes it is the largest 0x0307d164 applet after 27/32. It loads
  only module 2 (the empty idiom) at five sites.
- 61: recording window (likely). Loaded by module 29. Data holds a
  partial WIN-like struct: three code pointers at +0x08/+0x0c/+0x10
  (0x030820b1, 0x0308214d, 0x03082165, Service/Key/Display-shaped, with
  Init/DeInit absent or zero). Its sparse code head contains the strings
  'RECORD' and 'U:\RECORD ' and it loads modules 62 and 2. The SDK
  ships recording UI as residue in several modules, but a window struct
  plus a record-path string plus a parent window that loads it is
  stronger evidence than the residue cases; still short of proof that
  the Neo exposes recording.
- 81: Bluetooth window (likely). See §3.3. WIN at data+0x10:
  Service 0x0307de3f, Key 0x0307d91f, Display 0x0307d8ab, Init
  0x0307dd03 (own), DeInit 0x0307ddd9; all data words past +0x2c are
  zero (zero-filled state, not additional tables).

---

## 6. What remains unknown after round 2

- Module 7's role (sector-loading worker; target data unidentified).
- The specific screens/purposes of windows 6, 29, 30; module 5's exact
  service contract; module 17's exact screen.
- Module 61's recording function: exposed feature vs dormant SDK path.
- The poster of event flags 0x18b / 0x18c (§2.5, proven absent as an
  immediate call; the boot-stage setter was not located).
- Module 35/36: exact DSP feature name, Q-format, and the unit/direction
  semantics of the 0x0306780a(0x23, …) service call (§4.2).
- The scan/pair window assignment (§3.4; the BT UART baud is now
  established there);
  module 21's Display (0x0307e524) and the tail of its Key handler were
  not decoded instruction-by-instruction.
- Module 19/20's exact decode formats.

### Resolution count

Of the 28 round-1 unknowns (3, 4, 5, 6, 7, 9, 17, 19, 20, 21, 25, 26,
29, 30, 35, 36, 41, 42, 50–57, 61, 81):

- **Proven (11):** 21 (window + update host + BT/service functions),
  41, 42, 50, 51, 52, 53, 54, 55, 56, 57 (stub-family mechanism).
- **Likely (13):** 3, 4, 5, 9, 17, 19, 20, 25, 26, 35, 36, 61, 81.
- **Window proven, purpose unknown (3):** 6, 29, 30.
- **Still unknown (1):** 7.

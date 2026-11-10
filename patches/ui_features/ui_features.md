# UI features workstream: lock-screen information and Bluetooth shortcut

Fosi DAP Neo (DP3_V137), offline analysis only. Nothing in this document was
flashed; the stock image is untouched (SHA-256 verified before and after this
workstream, see §7). Companion evidence: disassembly dumps in
`work/ui_features/disasm/`, scanners in `work/ui_features/scan2.py` and
`work/ui_features/prov.py`. Background: `work/ui-controls/ui_controls.md`,
`work/saveinfo/saveinfo_lock.md`, `work/modules2/modules_round2.md`,
`stage2/updates/analysis/feature_feasibility.md`.

## Verdicts up front

| Feature | Verdict | One-line reason |
|---|---|---|
| Lock-screen information | **Design-complete, not built** | Every hook and data source is pinned (§3), but the draw code needs a resident home: the module-0 code-region extension (11,164 B) plus a framework record-edit step that is specified in the M3U design but **not implemented**. Refresh cadence for the position readout is also unproven (§3.5). |
| Bluetooth shortcut | **Design-complete, not built** | Gesture and detection are pinned and free in the player window (§4.1–4.2); the stock power routine is **provably not callable** from the playback window (overlay residency, §4.3). The honest route, a hook in module 0's dispatcher plus an inline replica of the power sequence in the extension, is fully specified (§4.4–4.5) but depends on the same unbuilt extension step, and the replica carries three unpinned stock side effects (§4.6). |
| Full key remapping | **Addendum delivered** (§5) | No key-map table exists; the sane route is event-word rewriting at the single dispatcher choke point. |

Patch numbers 0032–0039 are unspent. No patch files were generated and the
live framework under `work/patches/framework/` was not modified: with no
resident code home, any patch byte written today would be a branch to code
that cannot exist yet, which makes it a speculative byte, and this program
does not ship those (contrast the M3U gate patch, whose callee already
existed and was host-tested).

---

## 1. New RE findings (these close or correct earlier open items)

### 1.1 The SAVEINFO +0x60 writer census: exhaustive, tool-validated

A capstone register-tracking scanner (`scan2.py`: literal/`movw`/`movt` seeds,
`mov`/`add`/`sub` propagation, 800-instruction window) was first validated
against every +0x60 access already known from `saveinfo_lock.md`. It
reproduced all of them (module 5 Service clear, module 26 conditional clear,
module 31 reads/clears, module 33 read), and it was then run over all 82
modules.
Result: 23 write sites in 13 modules. Every writer stores 0, with one
exception (§1.2). Provenance of each stored register was confirmed by backward
scan (`prov.py`) or by reading the enclosing function:

| Site | Module | Stored value | Context |
|---|---|---|---|
| 0x0307D612 | 1 | 0 | boot defaults routine (known) |
| 0x0307D40C | 5 | 0 | mode applet Service (known) |
| 0x0307F0B8 | 12 | 0 (`movs r0,#0` @0x0307F0B6) | previously "unresolved value", now resolved |
| 0x0307D45A, 0x0307D49A | 21 | 0 (`movs r5,#0` @0x0307D2E0) | settings-family mode load |
| 0x0307D2F6, 0x0307D318, 0x0307D462 | 22 | 0 (r6≡0 from entry) | context/mode switch service |
| 0x0307E9FC, 0x0307EA72 | 24 | 0 (`movs r7,#0` @0x0307E9D4) | none |
| 0x0307EA9A, 0x0307EAC6 | 25 | **1** | **the engage write (§1.2)** |
| 0x0307EA78 | 26 | 0 (conditional) | (known) |
| 0x0307E17A | 27 | 0 (`movs r5,#0` @0x0307DFF2) | none |
| 0x0307D7F6, 0x0307D9A4, 0x0307E0A2, 0x0307E2D0, 0x0307E2E0 | 31 | 0 (r4 at Init; sb≡0 in fn 0x0307DEB8) | DeInit, node actions, track transitions |
| 0x0307DAA2 | 32 | 0 (`movs r5,#0` @0x0307D814) | settings Service apply path (also writes +0x3E, broadcasts message type 0xD); **not** a user hold switch |
| 0x03088710, 0x03088754 | 33 | 0 (r7≡0 from fn entry 0x030886B8) | position/resume consumption, §1.4 |

Module 0 contains **no** write to +0x60 at all (validated scanner, EA exactly
0x03023300, plus a full read of the input region, §1.3).

### 1.2 The hold-engage write: found (module 25 Key)

`saveinfo_lock.md` left the +0x60 = 1 write unlocated. It is in **module 25's
Key proc at 0x0307E9E4** (dump: `disasm/mod25_engage.txt`). Module 25 is a
small applet (880 B of code at 0x0307E9C0, state in the shared 0x030258xx
window area) whose Key polls the dispatcher directly, like module 31's.

Mechanics, instruction by instruction:

- Entry: `bl 0x03061B16` (dispatcher) → r0 = event word; r5 := 1, r3 := 0.
- Event **0x40004000 (type 4 · OK, i.e. short release of OK)** reaches
  0x0307EA5C (via the T4 ladder: r0 − 0x40000040 == 0x3FC0).
- Gate 1: byte [0x03024800+3] (this window's state byte) must be 0; if 1, the
  case exits without writing.
- Gate 2: current top-window index halfword [0x030235C0] ∈ {1, 2, 3, 4, 0x64}.
- Gate 3 (both sub-paths, 0x0307EA8E and 0x0307EABA): predicate call
  `0x030570E8([0x03023D38], 0x03036988)` must return 1, the same
  mode predicate the player and browser code test before acting on the
  file-info struct (its exact meaning is not pinned; it returns 1 in the
  normal playable-file state).
- Then: `strbeq r5, [r8, #0x60]` at 0x0307EA9A / 0x0307EAC6 with
  r8 = SAVEINFO (0x030232A0) and r5 ≡ 1 on every path (set at 0x0307E9F6,
  never rewritten before either store, verified by reading the full
  function). The surrounding code then opens the selected node via
  0x0307ED04 using the node tables at 0x03024F78 / 0x03024808.

So the engage action is: **short-press OK to enter/open the selected item in
module 25's window** (a list/browser-type applet), with gates 1–3 satisfied.
No other code in any module writes 1 to +0x60, and no settings-menu "hold"
toggle exists. The module 21 and module 32 apply paths that touch +0x60
write 0 (§1.1). Two honest caveats:

- This reframes what +0x60 means on this firmware. It is set when a track
  context is entered from the browser applet and is consumed/cleared by the
  player and codec service on transitions (§1.4). The stock "locked screen"
  behaviour is keyed to this byte by the module 31 snapshot logic
  (`saveinfo_lock.md` §2.6: flag-0x14E branch requires +0x60 == 1), so
  gating a lock overlay on +0x60 == 1 follows the stock semantics as far as
  they are pinned. But a dedicated user-facing "hold switch" gesture, if
  one exists, was not found in any module.
- The painter's hold icon is driven by bit 2 of state byte 0x030230EC,
  not by +0x60 directly. The writer of that bit was **not** found: the
  validated scanner sees no write to 0x030230EC in module 0 within its
  tracking window and only the painter's own read in module 31
  (0x0307E892). The design in §3 therefore gates on +0x60 (read directly),
  which is the better-grounded signal, and does not touch the icon bit.

### 1.3 The wheel region does not contain the engage write or an unlock threshold

The earlier belief (in the task brief, from `saveinfo_lock.md`) that the
engage write and a wheel-unlock threshold live in module 0
0x03061936–0x03061E58 is **refuted by direct read** (dump:
`disasm/mod0_input_region.txt`, 524 lines). That region contains the wheel
decoder (0x03061936–0x03061AAE), the input task (0x03061AB2), and the event
dispatcher (0x03061B16, §1.5). Its only SAVEINFO access is a read of
+0x2D5 at 0x03061DAA (in the dispatcher's double-press bookkeeping). There is
no +0x60 access and no threshold counter against +0x60 anywhere in it. The
unlock side of stock hold remains unexplained by this region; the known
+0x60 clears happen on window/context transitions (§1.1), which is
consistent with "changing context drops the lock byte" rather than a
dedicated unlock gesture.

### 1.4 Module 33 consumes +0x60 as a one-shot

Function 0x030886B8 (module 33, dump `disasm/mod33_hold.txt`): if +0x60 == 1
and file-info [0x03023980+0x44] == 0 it posts flag 0x121; when the resume
word SAVEINFO +0x5C is nonzero it converts it (×127-ish scaling, /1000),
calls the seek/position function 0x0308AAF4, and clears +0x60
(0x03088710); a second path at 0x03088746–0x03088754 does the same after
adding the 0x1388 (5000) timeout base to file-info +0x48. So module 33
treats +0x60 as a one-shot "resume pending" marker tied to the position
fields, a useful corroboration that +0x60 == 1 is the stock "locked into a
track" state, and a warning that any patch must not disturb the +0x5C/+0x60
consumption timing.

### 1.5 The dispatcher is the single event choke point (module 0, resident)

Function 0x03061B16 translates raw state-machine event words into what
windows actually consume, including synthetic events (it can return
0x40004000 for a timed double-press sequence; its internal bookkeeping uses
SAVEINFO +0x2D5 and bytes at struct+0/+2). **Every window Key proc read in
full calls it**: module 31 Key at 0x0307E5C0, module 25 Key at 0x0307E9EC,
plus module 0's own two call sites (0x030557A6,
0x030559EA, beside the module-0 status painter). It lives in module 0,
which is always resident. This is the hook point §4 and §5 build on.

Also pinned here: the input state machines generate the full event-type
ladder natively: T1 press (2-tick debounce), T2 long-press at 20
ticks, T3 repeat (every 4 ticks past 20), T4 short release, T5 long
release (GetKeyMask 0x030617A0 + SM 0x030617FE; second ADC-channel ladder
in the merge function 0x03061686 for masks 0x800/0x1000/0x2000). A second
key state machine for ADC channel 2 exists and was not previously
documented as such. Power held > 100 ticks posts flag 0x1A (power-off)
from inside the SM.

### 1.6 Module 31 (player) Key: full decode

Dump: `disasm/mod31_key_a.txt`, `disasm/mod31_key_b.txt`. The proc calls the
dispatcher, then overrides the event with a synthetic 0x40004000 if flag
0x131 is set. Consumed events (event = (type<<28)|mask):

| Event | Action (site) |
|---|---|
| T3/T4 · 0x10 (Vol+) | volume byte SAVEINFO +0x12 ++ (cap 0x78), module 33 volume fn 0x03088540(0xF8, 0), post flag 0x19A (0x0307E688) |
| T3/T4 · 0x20 (Vol−) | symmetric decrement path via 0x0307E664 |
| T1 · 0x4 / T1 · 0x8 | playlist index +/− at [0x030228A8+0x1EE], post flag 0x144 (0x0307E6B0 / 0x0307E6DA) |
| T4 · 0x200 / T4 · 0x400 | same index navigation pair |
| T2 · 0x40 | clear flag 1, SendMessage type 0 payload 5, consumed (0x0307E77C) |
| T2 · OK (0x4000) | flag-1 test: set → post 0x2F + set flag 1; clear → player-state dispatch (0x0307E700) |
| T4 · OK | play/pause + play-mode dispatch over byte [0x03025928] (0x0307E72E) |
| T4 · 0x40 | stop/back-style dispatch sharing the flag-1 prologue (0x0307E792) |
| **T2 · power (0x1)** | **ignored, falls through to the 0x0307E7FC return** |
| **T2 · Vol+ / Vol−** | **ignored** (the T3 repeats do the volume work) |
| **T5 · anything** | **ignored; no 0x5xxxxxxx comparisons exist in the proc** |

Flags 0x1A2/0x1A3/0x1A4 (the dispatcher's mode-byte timeout posts) are
consumed by module 9 (test+clear at 0x030805C6/D4/E4); flag 0x14E is
**never posted** through the flag APIs by any module (exhaustive scan).
Module 31's snapshot branch tests+clears it at 0x0307DC0E, so its poster
either writes the flag bitmap directly (0x14E → word 0x03023D20, bit 14;
not observed) or the branch is dead in stock. Open item, recorded as such.

### 1.7 Drawing primitives: observed signatures

- `DrawImage` = 0x03063700 (hold icon call proven in `saveinfo_lock.md`).
- Text draw = 0x030632FA, observed at two module 5 painter call sites
  (0x0307D1F0, 0x0307D3D2): r0 = 0, r1 = 185 (0xB9), r2 = 239 (0xEF),
  r3 = 319 (0x13F), and a stack argument loaded from halfword cell
  0x030235B4. Read plainly: (mode/flags = 0, x1, y, x2, [sp] = string or
  string-id). It is a one-line text draw clipped to a horizontal span. The
  exact nature of the stack argument (pointer vs resource id, the value
  is itself loaded from a halfword cell, which argues for an id/index)
  is **not** pinned; §3 treats it as a build-time unknown.
- Position getters 0x0306316E / 0x0306314A each take a context argument in
  r0 (module 5 painter: `mov r0, sb; bl 0x0306316E`; `ldr r0, [sp,#0xC];
  bl 0x0306314A`) and return a scalar the painters store as halfwords,
  consistent with elapsed/total, but **units are unproven**.
- Now-playing name source: the snapshot buffer at 0x030235CE is an
  array of halfwords (0x80 of them copied by module 31 Service;
  module 24 reads it at 0x0307ECE4). Character encoding (UTF-16 vs
  ASCII-in-halfword) is unproven from static evidence alone.

---

## 2. Shared prerequisite: the module-0 code-region extension

Both builds need resident code. There are no feature-scale caves
(M3U design §2). The sanctioned home is the module-0 code-region
extension: exec 0x03079C14..0x0307C7B0 = **11,164 B** of package-gap
headroom, reachable by extending `code_len` in module 0's header record
(file offset 0x210). That record-edit build step is **specified but not
implemented** in the framework. It is the same step the M3U device bridge
is waiting on. Budget against the shared 11,164 B (estimates are
estimates, stated so the coordinator can plan):

| Consumer | Bytes | Basis |
|---|---|---|
| M3U parser core | 5,426 | measured host object at −Os (M3U work) |
| Lock-screen draw routine (§3) | ~350–600 | gate check, two text draws, mm:ss formatting (two divisions), one B.W tail |
| BT dispatcher hook stub (§4) | ~40 | compare + suppress + tail into replica |
| BT power replica (§4.5) | ~250–450 | GPIO sequences + ≤5000×1 ms banner poll loop |
| M3U bridge + misc hooks | unbudgeted | not yet designed |
| **Known total** | **≈ 6,100–6,550** | leaves ≈ 4,600 B headroom |

Building either UI feature before the extension step exists would mean
inventing a second, incompatible way to place code. That is why both
verdicts are design-only, and why the first build task for whoever picks
this up is the extension step itself (in a scratch framework copy, per
this workstream's constraints), after which §3 and §4 are build-ready
modulo their named unknowns.

---

## 3. Feature 1: lock-screen information

### 3.1 Goal and stock behaviour

Stock: with the lock byte set, the player's display is the shared status
painter plus a 15×17 hold icon at (135,4). No track information. Goal:
while locked, show current track title/artist and playback position.

### 3.2 Hook site (pinned)

Module 31's copy of the shared status painter, flag-0x2E segment:
0x0307E804–0x0307E898, whose tail calls the hold-icon painter at
0x0307E898 (`DrawImage(0x26 + ((byte[0x030230EC]>>2)&1))` → image 38/39).
Module 31's Display entry 0x0307ED40 is a one-instruction veneer
(`b 0x0307E8F2`) into the painter body that contains this segment,
confirming this copy is the
player's display path. The patch replaces the segment's tail call with a
B.W into the extension routine, which (a) performs the stock hold-icon
draw, and (b) if SAVEINFO +0x60 == 1, draws the lock-screen text. Gating
on +0x60 directly (not on the icon bit) follows §1.2: +0x60 is the byte
whose setter, readers, and consumers are all pinned; the icon bit's
setter is not.

Why this site and not Display 0x0307ED40: the painter segment already
runs in the locked repaint path (it is what draws the hold icon), so no
new refresh trigger is needed for the static text (title/artist). The
position readout is the exception (§3.5).

### 3.3 What to draw, from which sources (all pinned)

- **Title/artist**: the snapshot name buffer at 0x030235CE (0x80
  halfwords), populated by module 31 Service whenever the track context
  is established (copies from the browser struct, `saveinfo_lock.md`
  §2.6), and the file-info struct at 0x03023980 (+0xF2 = file index,
  +0x5A halfword, +0x44/+0x48/+0x4C = state/position fields module 33
  uses). Draw with the text primitive 0x030632FA using the geometry
  pattern observed in module 5 (y and span arguments; exact y for the
  lock layout is a design choice, not an RE unknown, and the painter's own
  status lines sit in the same coordinate space).
- **Position**: getters 0x0306316E (ctx) / 0x0306314A, the same pair the
  module 5 progress painter and the module-0 shutdown painter call,
  formatted mm:ss by the new routine. Cross-check source: module 33's
  own position fields in file-info (+0x48 base, +0x44 state) as read at
  0x030886B8 ff.

### 3.4 Refresh behaviour

Title/artist: drawn on every painter pass that reaches the flag-0x2E
segment while +0x60 == 1, i.e., whenever the stock locked screen
repaints (window entry, track change, flag-driven repaints). No new
timers.

### 3.5 Named unknowns blocking the build (beyond §2)

1. **Position refresh cadence.** Who posts the painter flags 0x27–0x2E
   during playback, and therefore how often the painter reruns while
   locked, was not isolated in this pass. If repaints are
   event-driven only, a position readout would go stale between track
   changes. Mitigation exists in-design (the input task's 80-tick timer
   path at 0x03061C10 ff. posts periodic flags), but tying the readout
   to it is unproven. This must be pinned, by one more static pass or
   on hardware, before the position half of the feature can be called
   correct. The title/artist half does not depend on it.
2. **Text-draw stack argument** (pointer vs id, §1.7) and **name-buffer
   encoding** (§1.7): if 0x030235CE is not in the format 0x030632FA
   expects, the routine needs a conversion loop (budget +~100 B) or a
   different source (file-info fields). Resolvable by emulating one
   painter pass in the harness. The harness already executes module 33
   and the decoders bit-exact; a painter pass is the natural M3 task.
3. **Getter units** (§1.7): if the getters return frames/ticks rather
   than seconds, mm:ss needs the sample-rate divisor from file-info.
   Same harness pass resolves it.

### 3.6 Verdict

**Design-complete, not built.** Hook, gate, sources, and budget are
pinned; the build waits on (a) the §2 extension step and (b) unknowns
3.5.1–3.5.3, each with a named resolution path. No speculative bytes.

---

## 4. Feature 2: Bluetooth shortcut

### 4.1 Gesture choice (pinned by §1.6)

Requirement: a long-press or combo on an existing control, least
destructive, detectable in the polled model. The player Key decode
(§1.6) gives a complete consumption map. Candidates:

| Gesture | Event | Stock player behaviour | Side effects | Rank |
|---|---|---|---|---|
| **Long-press Power** | T2·0x1 = 0x20000001 | **ignored** | Power-off posts only at >100 ticks held (flag 0x1A, from the SM itself); T2 fires at 20 ticks, a 5× margin, and users already know a long power hold switches the unit off | **primary** |
| Long-press Vol+ / Vol− | T2·0x10 / 0x20000010, 0x20000020 | ignored | T3 repeats fire from tick 24 while held and **do** change volume (0x0307E688); holding to trigger BT also ramps volume | alternate, documented cost |
| Long-release OK | T5·0x4000 | ignored | T2·OK fires first at 20 ticks and performs its stock action (flag-1 dispatch); the gesture compounds two actions | rejected |
| Long-press OK | T2·0x4000 | **consumed** (flag-1 dispatch) | would fight stock behaviour | rejected |
| Long-press 0x40 | T2·0x40 | **consumed** (message type 0 payload 5) | none | rejected |

### 4.2 Detection needs no new code in the input path

The task asked whether press-duration tracking exists or a counter hook
must be designed. It exists: the key state machines emit T2 natively at
20 ticks (§1.5). The shortcut consumes the T2·power event word itself.
No counter, no timer hook, no input-loop patch.

### 4.3 The residency problem: the stock routine is not callable from playback (proven)

The BT power routine's entry points (0x0307D1A8 in module 81's build,
0x0307D1B6 in module 21's build, per `modules_round2.md` §3) are
window-overlay addresses. The overlay region is occupied by whichever
window family is loaded; during playback that is module 31, whose own
code occupies the same exec range (its Init is at 0x0307D6A0, its Key at
0x0307E5B8, and its bytes fill the region the BT entry would need).
Calling 0x0307D1B6 from the player lands inside module 31's own image,
not in BT code. Module 21 is resident in settings contexts, module 81 in
the BT window. Neither is resident during playback. Loading one via the
window loader (0x03067870) would evict the playback window, a window
switch, not a shortcut. **Any design that "calls the proven routine"
from the player is therefore wrong on this firmware**, however attractive
it looked in the feasibility pass; the callable-routine verdict in
`modules_round2.md` §3.4 holds only within the settings/BT window family.

### 4.4 Architecture that works: dispatcher hook + resident replica

- **Hook**: inside module 0's dispatcher 0x03061B16 (resident; called by
  every window's Key, §1.5), on its event-return path. When the event
  word equals 0x20000001 (T2·power), run the toggle (§4.5) and return 0
  ("no event") to the caller. 0 matches no case in any decoded Key
  ladder, so the active window simply sees nothing, exactly as it does
  today for events it ignores. This makes the shortcut work from any
  window, not only playback, and costs one hook site total. (Exact
  epilogue bytes to patch are a build-time pin. The dispatcher has a
  single r5-mediated return convention, but the precise instruction to
  replace must be chosen against the final disassembly when the
  extension lands. The site region is 0x03061B16–0x03061E58, fully
  dumped in `disasm/mod0_input_region.txt`.)
- **Why not hook module 31's Key instead**: one site per window, and
  the feature brief says "from any window (or at minimum from the
  playback window)". The dispatcher hook is strictly better and no
  harder. A player-only variant (hook at module 31 Key's fall-through,
  0x0307E7FC) remains a fallback if the dispatcher epilogue resists
  pinning.

### 4.5 The toggle replica (specified from disassembly; all callees module-0 resident)

Transcribed from module 81's power routine and module 21's Service
flag-0x1BD handler (`modules_round2.md` §3; every helper named there is
a module-0 function, hence resident and callable from the extension):

State: BT on/off = SAVEINFO +0x2D4; result byte 0x03023124.

- **If +0x2D4 == 1 (turn off)**: drive GPIO (2,7), (2,17), (2,16) low
  via mux 0x030526F8 / dir 0x03056098 / level 0x030560D2; write +0x2D4
  := 0. Module 21's handler also reads +0x2D3 on entry and writes both
  +0x2D4 and +0x2D3 by the end; +0x2D3's exact role is unpinned, so the
  replica mirrors both writes to stay stock-identical. Delay 200 ms
  (0x03064944).
- **If +0x2D4 == 0 (turn on)**: mux(2,7,0), dir(2,7,1), level(2,7,1)
  (GPIO2.7 high); write +0x2D4 := 1; poll up to 5000 × { test+clear flag
  0x1B2 (0x03067258); if set, read response buffer 0x0300642C, require
  'C','V','1' at [0..2], store 5 (if [buf+3] == 0x35) else 0 into
  0x03023124, done; else delay_ms(1) }; on timeout: GPIO2.7 low,
  GPIO2.17/2.16 low, +0x2D4 := 0, delay 10 ms, report failure.
- Persist via the normal SAVEINFO saver path on the next stock save
  (+0x2D4 lies in the verbatim-surviving block, `saveinfo_lock.md` §1).

### 4.6 Named unknowns blocking the build (beyond §2)

1. **Module 21 handler side effects.** The stock 0x1BD handler does
   more than the power cycle: posts 0x123, calls 0x03053242, writes
   0x0300416C/6E/6F, copies [0x03023298] → [0x03004174], calls
   0x03065772(0x53). Which of these the BT stack needs for a clean
   toggle (vs settings-window bookkeeping) is unpinned. Shipping the
   replica without them risks a half-initialised BT state; copying them
   blindly risks corrupting settings state from the wrong context.
2. **Flag 0x1B2's producer.** The banner flag is set by a UART receive
   path in module 0 (buffer 0x0300642C) that this pass did not trace; the
   replica assumes it is always serviced, as it is when module 81 polls
   it. If the receiver is only armed from the BT window, the poll times
   out and the replica must arm it first. One more fact to pin.
3. Both resolve the same way as §3.5: a harness pass or hardware. The
   dispatcher hook and gesture (§4.1–4.4) have **no** unknowns.

### 4.7 Verdict

**Design-complete, not built.** The two facts the feature turned on are
settled: a free gesture exists (T2·power, natively detected), and the
stock routine is not callable from playback (overlay residency, proven).
The build waits on the §2 extension step and unknowns 4.6.1–4.6.2.

---

## 5. Addendum: what full key remapping would take

Stock has **no key-map table**: each window's Key proc is a hand-written
compare ladder over dispatcher event words (two decoded in full this
pass: modules 25 and 31; module 26's follows the same shape, and the
ADC-channel-2 ladder adds masks 0x800/0x1000/0x2000 with their own
dispatcher-level meanings (mode-byte posts 0x1A2/0x1A3/0x1A4, consumed
by module 9). Remapping therefore has two honest routes:

1. **Per-window patching**: rewrite each ladder's comparisons. Cost:
   one patch set per window (a dozen-plus Key procs), each with its own
   ladder arithmetic (the subtract-and-compare chains in §1.6 are not
   uniform), and every future window change re-opens the work. Rejected
   except for single-window tweaks.
2. **Dispatcher-level rewriting (the sane route)**: the dispatcher
   (0x03061B16) is the single choke point every Key proc consumes.
   A remapping layer in the extension holds a small table of
   {stock event word → replacement event word} entries (~8–16 B each;
   a 16-entry table ≈ 256 B) and rewrites r0 on the return path before
   the window sees it. Per-window exceptions are still expressible
   (the table can key on the current-window halfword [0x030235C0]).
   This is the same hook §4.4 needs, so the BT shortcut is effectively
   remapping's first entry. Build the hook once; both features use it.

Costs and risks, stated plainly: the dispatcher also *generates*
synthetic events (double-press 0x40004000, mode timeouts), so the table
must apply only to genuine SM events or the synthetic paths get remapped
too, distinguishable, since the synthetics are produced inside the
dispatcher after the SM read; T3 repeats and T5 releases are separate
event words, so remapping a press without its repeat/release produces a
half-remapped key (the table should rewrite by mask across types
T1/T2/T3/T4/T5 together); and any window that bypasses the dispatcher
(none found; both Key procs read in full, modules 25 and 31, call it)
would silently keep stock
bindings. Estimated incremental cost over §4.4: table + mask-matching
loop ≈ 150–250 B of extension code. Feasible; not built, for the same
§2 reason.

---

## 6. What was NOT done, deliberately

- No framework patches 0032–0039: nothing to stack that isn't
  speculative today (§2). The scratch-framework build test the brief
  calls for applies to built patches; with none built, there was
  nothing to test, and the live manifest was left untouched.
- The flag-0x14E poster, the 0x030230EC bit-2 writer, and module 21's
  side-effect semantics remain open RE items, named, not papered over.

## 7. Verification

- Stock image SHA-256 checked at the end of this workstream against
  fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef
  (result in the workstream report; the image was only ever read).
- Scanner validation: `scan2.py` reproduced every previously known
  +0x60 access before its negative results (module 0) were trusted
  (§1.1).
- All addresses above are from the dumps in `work/ui_features/disasm/`
  (`mod0_input_region.txt`, `mod0_keysm.txt`, `mod0_merge.txt`,
  `mod25_engage.txt`, `mod31_key_a.txt`, `mod31_key_b.txt`,
  `mod31_hold2.txt`, `mod31_svc_*.txt`, `mod32_service_head.txt`,
  `mod33_hold.txt`) or the cited prior documents.

## Errata from the build pass (2026-10-31)

The build workstream (`patches/ui_features/build/ui_build.md`) traced the
items this document left unproven. Two identifications above are refuted,
two open items are resolved:

- **0x030632FA is not a text draw.** It is a rectangle fill: its stack
  argument is a 16-bit pixel value passed by value into the framebuffer
  store at 0x03063E60, proven from the function body and 87 call sites.
  Every use of it as a text primitive in sections 1.7 and 2 is wrong.
  The renderer candidates are now 0x03062CEE (the string routine module
  31's Display itself calls) and 0x0306333E with its wrapper 0x03063444;
  neither contract is pinned yet.
- **0x0306316E and 0x0306314A are not position getters.** They are a
  get-and-set pair for two display-mode halfwords of struct 0x0302385C
  (+0x20 and +0x24), returning previous values in the 0/1/2 class.
  Callers bracket rendering with them as mode save/restore. No playback
  position comes out of them; the position source is now the file-info
  fields +0x44/+0x48/+0x4C, unproven.
- **Refresh cadence is resolved: event-only.** No periodic poster of
  painter flags 0x27 to 0x2E exists in any module. A title drawn at hold
  engagement is compatible with this; a ticking elapsed readout is not,
  without a self-supplied periodic repost.
- **Name buffer resolved:** 0x030235CE is a UTF-16 wide string
  snapshotted from the track-name field at SAVEINFO +0x87 by module 31's
  Service, gated on SAVEINFO +0x60 == 1, the gate this design chose.

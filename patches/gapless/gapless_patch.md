# Gapless playback patch set: DP3_V137 (stock SHA fcc1cd3e…)

> Current status: superseded by gapless v2 (see [`README.md`](README.md)).
> This document describes v1 as first delivered. v1's premise that a
> same-module load could skip the reset-and-start body was wrong: the stock
> stop path halts core 1 on every track change, so v1 skipped the reboot
> of a halted core (the transition rig in [`rig/`](rig/) shows the open
> exchange timing out and a ~27 s stall). Its 80 ms delay cut is retired
> because that delay runs after the I2S restart. The v1 cost budget in §6
> is also superseded by the rig's measurements.

Status: **built and statically verified, shipped DISARMED.** The set installs
the complete same-codec fast-path machinery (loader gate, wait cut, state)
in a form that is behaviour-identical to stock. One further 2-byte patch
(0016, delivered but deliberately not stacked) arms it. Arming is gated on a
single named Phase D observation (§7, R1). Everything below is offline
analysis of the stock image; nothing has been flashed (no unit exists yet).

Design inputs: `analysis/gapless.md` (+ Phase 2 addendum), `analysis/
ec_poster.md`, `analysis/core1_loader_protocol.md`,
`stage3/research/performance_maximization.md` §3.2/§6, and Phase D harness
milestone 1 (`work/harness/command_semantics.md`). Coordinator updates
folded in: there are no feature-scale code caves in this image (every large
zero tail is referenced runtime workspace, independently re-confirmed for
module 0's 42 KB run, which carries literal references), and the HifiFile
open send is 0x66, not 0x68.

---

## 1. As-designed vs as-built

| Design element (brief) | Verdict | Where |
|---|---|---|
| Same-codec fast path: retain the loaded decoder, skip image re-copy + core-1 reset, issue only a new open | **Built** (disarmed). Single choke point: the gate sits inside reset-and-start `0x0306CB2C`, the only loader entry all ten decoder cases call, not at the state byte `[0x03023151]`, which is written before the load in the same open and cannot carry the retention decision | 0011 + 0012 |
| Fixed-wait cut: `delay_ms(100)` at `0x03089F16` | **No patch needed.** Disassembly (§4.4) proves it is cold-open only: the DAC-guard branch at `0x03089E52` skips over it on every warm/natural advance. The brief's premise that it is a per-track cost is wrong on this image | none |
| Fixed-wait cut: `delay_ms(80)` at `0x03088FEA` | **Built** (disarmed via the gate flag). Cut only when the gate skipped the load AND the sample rate is unchanged | 0013 + 0014 + 0015 |
| Fixed-wait cut: position-sync loop at `0x0308A0EE` | **Design-only** (§5.2). Semantics of `SAVEINFO+0x63` during a natural advance are unobserved; cutting blind risks breaking resume/seek state | none |
| Monitor hook + next-track pre-staging into a shadow file-info struct | **Design-only** (§5.1). Three independent blockers, each named with the observation that clears it | none |
| Preserve DAC guard `[0x03023125]`, output state `[0x0302314C]`, volume `SAVEINFO+0x12`, EQ bytes `SAVEINFO+0x61..0x6B` | **Preserved by construction.** The fast path skips only the body of `0x0306CB2C`; the codec-open path that owns all of that state runs stock, before and after the gate | none |

## 2. The mechanism (armed form)

Stock per-track sequence on a natural advance, from the traced evidence:
the playback monitor `0x03064F7E` confirms end-of-stream via the stub status
query, finalizes (state=4, silences the PCM ring, zeroes position), and
posts event `0xEC`; the playback task `0x0308A1CA` wakes, runs open-prep and
codec open (`0x03089E2E`), which rebuilds the decoder info struct, then
self-dispatches message `0xE5` to load-and-start (`0x03088D9C`). That routine
loads decoder module 34, registers the monitor, then tail-calls the
per-codec dispatcher `0x0308886E`; each codec case loads its stub overlay
and calls reset-and-start `0x0306CB2C(decoder_module)`, which pulses the
core-1 reset line, re-copies the whole decoder image (33–117 KB depending on
codec), re-copies the 144-byte parameter page, and polls for the decoder's
boot handshake, before the case tail-calls `0x03088824`, which sends the
MU channel-2 `0x65` exchange that actually opens the new file on the
resident decoder (the decoder's HifiFile open leg is send `0x66`,
execution-proven by the Phase D harness). Load-start then re-arms I2S/DMA,
waits `delay_ms(80)`, and audio resumes.

The fast path changes exactly one thing: **when the requested decoder
module equals the retained one, `0x0306CB2C`'s body does not run.** The
decoder image is already resident and was never reset, so the `0x65`
exchange in `0x03088824` (stock code, unmodified) opens the next file on
it. Everything upstream (monitor finalize, codec open, info-struct rebuild)
and downstream (the exchange, ring/DMA re-arm in `0x03088D9C`) is stock.

Two supporting pieces:

- **The gate maintains the retained id itself.** Every gate invocation that
  takes the stock path records the module it is about to load; a skip
  records `module|0x80`. The value cannot go stale: any real load (browser
  pick, codec change, cold start) passes through the same gate and
  rewrites it. Boot staleness is impossible because the state lives in
  module 0's code segment, re-copied from the image at every boot (§3).
- **The delay cut is downstream of the gate's flag, not of a second
  comparison.** The cave at the `delay_ms(80)` site tests the flag bit the
  gate set *this open*, plus rate equality against a prev-rate word it
  maintains itself on every invocation. Same-codec-but-rate-changed
  transitions keep the stock 80 ms.

## 3. Where the code and state live, and why

There are no caves at feature scale in this image. What exists is the
module-0 `bx lr` stub farm (an SDK table of weak no-op handlers) around
`0x030514F0–0x0305168C`. Slots were admitted only after an exhaustive scan
of all 82 modules for BL/B.W targets (raw halfword decode), literal words
in every code and data region, and MOVW/MOVT constant pairs, **plus** a
fall-through check of the instruction preceding each range (the scan alone
missed that `0x030515AC` is a live function's return and that `0x030515BA`
is live code; both are excluded). Tools: `tools/refscan.py`.

| Chunk | Range | Contents | Size |
|---|---|---|---|
| P3 | `0x03051664–0x03051683` | Gate cave | 32 B |
| P3 tail | `0x03051684–0x03051687` | Delay cave's literal pool (`0x030368D8`) | 4 B |
| P1 | `0x030514FE–0x03051517` | Delay cave | 26 B |
| P2′ | `0x030515B0–0x030515B7` | State pair {retained, prev_rate} | 8 B |

Deliberately untouched neighbours, each verified referenced or live:
stubs at `0x0305151A/1C/1E` (called from module 61), `0x0305168A` (called
from modules 33 and 61), `0x030514F2/F8`, the live guard at `0x030515BA`,
and the slots at `0x03051518`, `0x03051688`. Total patch footprint in the
farm: 70 bytes.

State placement is the key choice. The two state words sit
**inside the code segment** (`0x030515B0`), not in BSS and not in SAVEINFO:

- The loader writes module 0's code segment from the image at boot, so the
  pair's boot value is its image value (0, 0) on every boot. The gate can
  never skip the first load of a session. No boot witness byte is needed.
- The code segment is SRAM the loader itself writes when loading overlays;
  the gate/delay caves update the pair in place. (Sibling-build precedent:
  nanitecfw's runtime self-patch of `fread` on the same SDK family.)
- SAVEINFO's verbatim block `+0x1C7..+0x2D5` was rejected: the save/load
  research shows it is the record's string/large-field area with live stock
  occupants (e.g. BT state at `+0x2D4`), and no free sub-range could be
  confirmed. BSS candidates were rejected: every candidate window remained
  reachable by base+offset from a documented struct base, so freedom could
  not be proven to the standard the DAC fix set.

**Extension-region accounting (coordinator update #1).** The shipped set
uses 0 bytes of the module-0 extension region (`0x03079C14..0x0307C7B0`,
11,164 B). The design-only pre-staging construction (§5.1) is the only
gapless element that would need it: estimated ≤1 KB (a shadow-copy routine
+ finalize-block trampolines), against the M3U parser's 5,426 B, combined
≈6.5 KB, no conflict with the 11,164 B budget. It also needs the framework
region-extension build step the M3U design specifies (a `code_len` record
edit), which does not exist yet; the shipped set needs no build step beyond
length-preserving patches.

## 4. Patch list and disassembly evidence

Stacking: after `0000–0002` (DAC set). All sites are disjoint from the DAC
sites (`0x03060D14`, `0x03060D8E`) and from the clock table
(`0x03079824..`), so every `expect` below is checked against stock bytes.
**Numbering collision, flagged for the coordinator:** the clock set as
landed occupies `0003–0018`, so these filenames collide with clock files
`0010–0018` if copied into the framework `patches/` dir as-is. Renumber at
merge (contents don't embed their numbers); verification below stacks them
after `0000–0002` as briefed, and also proves they stack after the
full `0000–0018` manifest when renumbered `0020–0025` in a scratch tree.

### 0010: state pair, module 0 code @ `0x030515B0`, 8 B
`7047704770477047` → `0000000000000000`. Data, not code: {retained=0,
prev_rate=0}. Justification in §3.

### 0011: gate hook, module 0 code @ `0x0306CB2C`, 4 B
```
before: 70 b5 05 46   push {r4,r5,r6,lr}; mov r5, r0      (reset-and-start entry)
after:  e4 f7 9a bd   b.w  0x03051664                     (gate cave)
```
Site justification: BL-target scan of all 82 modules found exactly ten callers
of `0x0306CB2C`, all module-33 codec cases (`0x030888B2, 0x0308890E,
0x030889E0, 0x03088A34, 0x03088AC2, 0x03088B16, 0x03088B6A, 0x03088BBE,
0x03088C3E, 0x03088CA8`). One hook covers every codec.

### 0012: gate cave, module 0 code @ `0x03051664`, 32 B
```
03051664  70b5       push {r4, r5, r6, lr}     ; displaced stock instruction
03051666  0546       mov  r5, r0               ; displaced stock instruction
03051668  aff1bc06   sub.w r6, pc, #0xbc       ; r6 = 0x030515B0 (state pair)
0305166c  3068       ldr  r0, [r6]             ; retained word
0305166e  4006       lsls r0, r0, #0x19        ; mask off the 0x80 flag
03051670  400e       lsrs r0, r0, #0x19
03051672  a842       cmp  r0, r5               ; retained == requested?
03051674  ffe7       b    #0x3051676           ; DISARMED: always stock.
                                               ; 0016 turns this into beq 0x0305167c
03051676  3560       str  r5, [r6]             ; retained = requested
03051678  1bf05aba   b.w  #0x306cb30           ; stock body, from its 2nd instruction
0305167c  8024       movs r4, #0x80            ; -- skip block (armed only) --
0305167e  2543       orrs r5, r4               ; retained = module | 0x80
03051680  3560       str  r5, [r6]
03051682  70bd       pop  {r4, r5, r6, pc}     ; return to the codec case
```
Contract check against the stock body it rejoins: `0x0306CB30` reloads
`r4` itself (`ldr r4, [pc, #0xac]`), `r5` already holds the module id
exactly as stock's displaced `mov` left it, and `r6` is only pushed/popped
by the stock body, never read. The cave's scratch use is safe on both
paths, and the skip path's pop matches the caller's expectation of the
stock epilogue.

### 0013: delay cave, module 0 code @ `0x030514FE`, 26 B
```
030514fe  2ca1       adr  r1, #0xb0            ; r1 = 0x030515B0 (state pair)
03051500  604b       ldr  r3, [pc, #0x180]     ; pool @0x03051684 -> 0x030368D8
03051502  9b68       ldr  r3, [r3, #8]         ; new rate = [info+8]
03051504  4a68       ldr  r2, [r1, #4]         ; prev rate
03051506  4b60       str  r3, [r1, #4]         ; prev = new (every invocation)
03051508  9342       cmp  r3, r2
0305150a  03d1       bne  #0x3051514           ; rate changed -> stock delay
0305150c  0a68       ldr  r2, [r1]             ; retained word
0305150e  802a       cmp  r2, #0x80
03051510  00d3       blo  #0x3051514           ; not a fast-path open -> stock delay
03051512  7047       bx   lr                   ; SKIP: return to load-start
03051514  13f016ba   b.w  #0x3064944           ; stock: tail-call delay_ms(80)
```
Register safety at the hook site: the cave clobbers only `r1–r3`, which
the stock `BL delay_ms` at that site already exposes to clobbering; `r0`
(the delay argument) and `lr` pass through untouched on both paths.

### 0014: delay hook, module 33 code @ `0x03088FEA`, 4 B
```
before: db f7 ab fc   bl 0x03064944   (delay_ms)
after:  c8 f7 88 fa   bl 0x030514fe   (delay cave, resident module 0)
```

### 0015: delay pool, module 0 code @ `0x03051684`, 4 B
`70477047` → `d8680303` (the word `0x030368D8`, the decoder info struct).
Data, not code; same stub-slot justification as 0010.

### 0016: ARM, module 0 code @ `0x03051674`, 2 B, **not stacked**
`ffe7` → `02d0` (`beq 0x0305167c`). Turns the gate's compare into the skip
decision and thereby makes the delay cut live. Everything else in the set
is inert without it: with the disarmed branch, every load runs the stock
body and the only writes are to patch-owned state.

### 4.4 Why `delay_ms(100)` needs no cut (evidence)
Codec open `0x03089E2E`: at `0x03089E52` it loads the DAC guard byte
`[0x03023125]` and branches to `0x03089F2A` when non-zero, **past** the
`delay_ms(100)` call at `0x03089F16`. The guard is set by the first open's
DAC init and cleared only by the stop/close path (`0x0308A94C`). So the
100 ms is paid once per play session, never per track. Cutting it would
add risk for zero benefit.

## 5. Design-only elements

### 5.1 Monitor pre-staging / shadow file-info
Goal: at the monitor's finalize blocks (`0x03064FFC`, `0x03065022`, and the
`0x03064FEA` variant, the three sites that call the ring-silence helper
`0x03054E66` before posting `0xEC`), start the next track's preparation
before the ring is silenced.

Construction, when unblocked: two B.W trampolines in the finalize blocks
(the blocks are 4-byte branch sites like the DAC fix's) detouring to a
routine in the module-0 extension region that (a) type-probes index+1 via
the pure probe `0x03059D58` (the only side-effect-free step of open-prep),
(b) copies the live file-info struct (`0x03023980`, 0xF4 B) to a shadow,
(c) runs the metadata pre-parse against the shadow, and rejoins the stock
finalize. On the subsequent open, codec open consumes the shadow when the
armed index matches. Estimated extension footprint ≤1 KB.

Three blockers, each with its clearing observation:
1. **Open-prep is not callable from monitor context.** The full helper
   behind open-prep (`0x03089DA6`'s caller chain) branches on play state
   and posts event `0xEE`; only the type probe is pure. *Clearing
   observation:* a Phase D trace of a natural transition showing which
   open-prep steps are state-safe to run early, or a decomposition of the
   helper into its pure prefix.
2. **No proven home for the ≥0xF4-byte shadow.** No BSS/data window passed
   the free-space standard (§3); the extension region is code space, and
   using overlay SRAM for it needs the allocation map of the transition
   window. *Clearing observation:* a Phase D shared-memory trace
   (writes watched over `0x03004000–0x0304B604` across a transition)
   identifying a window nothing touches between finalize and open.
3. **Which file-info fields the decoder-open path consumes is unpinned.**
   Pre-parsing the wrong subset saves nothing. *Clearing observation:*
   the same trace, read for which of `0x03023980`'s fields are read (vs
   written) by `0x03089E2E`/`0x03088D9C`.

Note the dependency direction: the shipped fast path does not need
pre-staging. Pre-staging attacks the residual transition cost (the `0x65`
exchange and decoder-side open), which §6 shows is the part only Phase D
can size. Build it after that measurement, if it still matters.

### 5.2 Position-sync loop cut
The loop at `0x0308A0EE–0x0308A11A` (15 ms polls, cap 200) is entered only
when `[info+0x20] == 1`, and `info+0x20` is rebuilt from `SAVEINFO+0x63`
on every open (`0x03089FE8–0x03089FF2`). What `+0x63` means during a
*natural advance* (as opposed to a seek or a resume) is unobserved; the
loop waits for the saved position word to reach the track target, which
may be load-bearing for exactly the transitions gapless cares about.
*Clearing observation:* Phase D trace of a natural advance recording
`SAVEINFO+0x61/+0x63/+0x64` and the loop's iteration count. If it exits in
0–1 iterations on natural advances, no cut is needed at all (the loop is
already free); if it spins, the cut is a gate-flag test at `0x0308A0C4`
of the same shape as 0013.

## 6. Static transition-cost budget

Per warm same-codec transition. "Fixed" = statically countable from the
disassembly; "dynamic" = bounded only by a timeout constant in stock code
and assigned to Phase D for measurement.

| Cost element | Stock | Fast path (armed) | Saving |
|---|---|---|---|
| Decoder image re-copy via `0x03067870` flags 7 | MP3 87,460 B · WMA 117,376 · AAC 83,784 · WAV 55,036 · Vorbis 116,572 · FLAC 33,692 · ALAC 36,584 · APE 32,136 · DFF 33,712 · DSF 32,888 (≈3–4 cycles/word ≈ 0.06–0.5 ms at each codec's stock B-core clock) | 0 | full copy |
| `delay_ms(5)` inside `0x0306CB2C` | 5 ms fixed | 0 | 5 ms |
| Parameter-page copy (144 B) | ~36 word copies | 0 (page persists, see R3) | ~0 ms |
| Core-1 reset pulse + boot ready poll | dynamic: poll cap 200,000 iterations with an MU pump per iteration; typical = decoder boot time | 0 (core never reset) | dynamic |
| `0x65` info exchange (`0x03088824`) | dynamic: poll cap 0x4C4B40 iterations | unchanged (stock, required, it *is* the open) | none |
| Task-5 state poll in `0x03088D9C` | ≤200 × `delay_ms(1)` cap, dynamic | unchanged | none |
| `delay_ms(80)` settle at `0x03088FEA` | 80 ms fixed | 0 (same rate only) | 80 ms |
| Gate + delay caves | none | ~26 instructions total, <1 µs | none |

**Fixed saving: 85 ms + the image copy, per transition.** The dynamic
saving (decoder reboot and pipeline refill after a reset) is expected to
dominate but is not statically countable; claiming a number for it without
the harness would be fabrication.

**Pre-roll statement.** The transition is sample-exact iff the new
decoder's first PCM reaches the ring before the ring drains. The monitor
finalizes at end-of-stream, so the available pre-roll is whatever audio
the outgoing decoder had buffered in the ring (ring base `[0x03023928]`,
length `[0x03023938]`, runtime values, not image constants) minus drain
during the residual work. Stock residual work carries ≥85 ms of fixed
delay alone, so stock needs ≥85 ms of buffered audio at finalize to be
gapless. That is consistent with stock not being gapless. The fast path removes
all statically-known fixed cost; the residual is the `0x65` exchange plus
decoder-side open latency, which is exactly the warm-start quantity the
performance report's finish line caps at <30 ms. **The design therefore
needs a pre-roll of (exchange + decoder-open) and nothing else; Phase D
measures that number, and if it exceeds the ring's typical buffered
remainder at finalize, §5.1's pre-staging is the follow-on that buys it
down.** Same-rate transitions are the 0-sample target; a rate change
keeps the 80 ms settle (the I2S/DAC path was reconfigured) and falls
under the ≤1 ms offset line only if the residual still fits the pre-roll
That is also a Phase D/E measurement.

## 7. Risk register

- **R1: Resident decoder may not accept the open exchange after
  end-of-stream. [THE ARM GATE]** The fast path assumes the stock `0x65`
  exchange in `0x03088824` restarts a decoder that finished a track,
  was never reset, and whose file was closed by its own EOF path.
  Nothing in the static evidence contradicts it. The exchange is the
  only open trigger the firmware has, the decoder dispatches format
  through its image table (harness: module 76, FLAC = format 6), and
  the HifiFile open leg is the proven send `0x66`. But no execution
  has yet driven a resident decoder through EOF → `0x65`. *Clearing
  observation (Phase D, before 0016 ships):* emulate or trace one
  stock same-codec transition, then the same transition with the load
  skipped, and show the decoder accepts `0x65`, issues its `0x66`
  HifiFile open, and produces PCM for the new file. Failure mode if
  wrong: the exchange poll spins to its cap. That is a stall, not
  corruption; the disarmed build is unaffected.
  *Status (2026-10-31, Phase D milestone 2): cleared on the decoder
  side.* The load-skipped transition was executed in the core-1
  harness: after file A (44.1 kHz FLAC) reached end of stream, the
  resident decoder accepted file B's `0x65` push, issued `0x66`,
  reported B's stream info, and decoded B (48 kHz) bit-exact,
  48,000/48,000 samples per channel, identical to the fresh-boot
  baseline (`patches/harness/milestone2.md`,
  `run_log_m2_transition.txt`). What remains unobserved is the
  system side of the exchange (module 33's poll, the R5 bus
  release), which this harness does not execute; that observation
  belongs to the hardware phase. Arming 0026 is therefore a
  decision for the project owner, not an open technical unknown on
  the decoder side.
  *Armed 2026-10-31:* under the owner's direction to continue the
  phased plan, 0026 is stacked in the framework manifest (31
  patches; the ARM bytes land inside the 0022 cave range, so the
  framework diff stays 1,383 bytes). The unified build from this
  state is pinned in `patches/framework/README.md`. The disarmed
  configuration remains one manifest line away.
- **R2: Stop → replay of the same codec.** The gate's retained word
  survives a user stop (`0x0308A94C` clears the DAC guard, not the
  pair). If stop parks the decoder (its cmd-4 path), a same-codec
  replay would skip a needed reload. The stock stop path does not call
  `0x0306CB2C`, and no static evidence shows the decoder unloading on
  stop. *Phase D must include stop→replay-same-codec in the R1 test.*
  Mitigation if it fails: also hook the stop path to zero the pair
  (one 4-byte site, same pattern as 0011). It is not built now because the
  failure is unproven.
  *Status (2026-10-31): cleared in emulation.* Stop mid-file, then
  re-open on the resident decoder produced PCM byte-identical to
  the fresh-boot baseline (`run_log_m2_stop_replay.txt`). The
  mitigation hook is not needed.
- **R3: Parameter page is not refreshed on the fast path.** Skipping
  `0x0306CB2C` skips the 144-byte page copy from `0x030064E0`. Harness
  finding: page fields `+0x20/+0x24` are Hz dividers for decoder delay
  loops. A zeroed page spins ~4×10⁹ iterations; the fast path never
  writes the page, so the loaded values persist (safe by omission).
  The residual risk is the opposite direction: if any page field is
  per-track, the resident decoder would run the new track with stale
  values. *Phase D: diff the page (source `0x030064E0` and the shared
  copy at `0x01020000`) across two different tracks' opens.* If a
  per-track field exists, the gate grows a page-only refresh (copy
  without reset). The cave has room in the farm's remaining slots,
  or the refresh moves to the extension region.
  *Status (2026-10-31): cleared for the decoder-visible copy.* The
  144-byte page at `0x01020000` is byte-identical between the stock
  reload and load-skipped opens, and the decoder never writes it
  in-session; no per-track field was observed (`run_log_m2_diff.txt`).
  The system-side source page at `0x030064E0` is not observable from
  core 1, so a per-track field written only there remains formally
  possible and is a hardware-phase check.
- **R4: Command word discipline.** The system core never writes the
  decoder command word `0x0102221C` directly (harness exhaustive
  negative); the decoder's MU receivers own it. The fast path
  conforms: it writes no shared-memory cell except its own pair. Any
  future variant that pokes decoder state directly is out of design.
- **R5: Bus release skipped.** `0x0306CB2C` begins with a bus release
  (`0x030525AC(2,1)`); the fast path skips it. Between tracks of a
  session nothing else acquires that bus (the DAC path's guard byte
  proves the session model), but this is inference, not trace.
  *Phase D/E: confirm no bus transaction errors on skipped transitions.*
- **R6: Format-3 opens skip the delay site.** When the file-info type
  word is 3, load-start branches around the DMA config and the delay
  site entirely, so the delay cave does not run and prev-rate goes
  stale by one track. A later fast transition could then compare
  against a two-tracks-ago rate and cut the 80 ms wrongly (rates
  coincide). Impact is bounded (a settle wait shortened on a
  same-codec transition), and the gate flag still requires a skipped
  load. *Phase E: identify which format/source class type 3 is and
  whether it can sit between two same-codec tracks.*
- **R7: Stub-farm occupancy.** The caves rely on the reference scan's
  negative over branch targets, literals, and MOVW/MOVT pairs, plus
  fall-through checks. A computed call (function pointer built
  arithmetically, or a TBH table entry) into the used slots would
  break. That is the same residual the accepted DAC pad carries, narrowed
  here by the fall-through analysis that caught two live neighbours
  the raw scan missed. *Phase E first-boot test on the disarmed build
  exercises this:* the disarmed set is behaviour-identical, so any
  farm-occupancy error shows up as a stock-behaviour regression
  before arming is ever attempted.
- **R8: State records "load attempted".** On the stock path the gate
  writes the retained word before the load runs (mirroring stock's own
  convention for `[0x03023151]`). If a load itself failed, the pair
  would claim a module that is not resident. Stock's own error path
  for a failed load is the cmd-10 status query in load-start, which
  still runs on the next open before the dispatcher, and a failed
  load leaves the decoder not-ready, which R1's test must also cover.
- **R9: Code-segment writability.** The pair's in-place updates assume
  module 0's code segment is writable SRAM at runtime (loader mechanics
  + sibling-build self-patch precedent). If an MPU made it read-only,
  the gate's first store would fault. That is visible immediately in the
  Phase D harness (which executes module 0 code) and on first
  disarmed boot in Phase E. No MPU use appears anywhere in the traced
  firmware.

### Phase D measurement list (consolidated)
1. R1 trace: stock vs load-skipped same-codec transition; decoder
   accepts `0x65`, sends `0x66`, produces PCM. **(Arms 0016.)**
2. R2: stop → replay same codec under the skip.
3. R3: parameter-page diff across tracks (source + shared copy).
4. §5.2: `SAVEINFO+0x61/+0x63/+0x64` + position-loop iteration count
   on natural advances.
5. §5.1: shared-memory write trace over a transition (shadow window
   hunt) + file-info field read map.
6. §6: exchange + decoder-open latency (the residual pre-roll), and
   ring buffered-remainder at finalize.

### Phase E measurement list
1. Disarmed build boots and plays indistinguishably from stock (R7).
2. Armed: sample-offset measurement at transitions: 0 samples
   same-codec/same-rate; ≤1 ms otherwise (finish lines).
3. R5 bus behaviour; R6 type-3 identification; warm-start latency
   <30 ms confirmation.

## 8. Verification

`verify_gapless.py` (output: `verify_output.txt`) builds three images
through the framework and checks: input pinned to stock SHA and the
stock file untouched afterwards; builds A (0000–0002), B (A + 0010–0015),
C (B + 0016) all pass `firmware_patch.validate()`; the B-vs-A whole-file
diff is confined to the six named sites and every site changed; the
C-vs-B diff is exactly the ARM byte pair; the gapless set also stacks
after the full production manifest `0000–0018` (scratch-renumbered
0020–0025) and validates; before/after disassembly of every site is
printed. Assembly provenance: `tools/assemble.py` (rz-asm at final
addresses, capstone re-disassembly in place); site-justification scan:
`tools/refscan.py`.

Results (`verify_output.txt`, exit 0, ALL CHECKS PASSED):

- Input pinned to stock SHA `fcc1cd3e35b46f1f…`; stock file byte-identical
  after the run.
- Build A (0000–0002) validates, SHA `66936a58f019b5e7…`
- Build B (A + 0010–0015, the shipped disarmed set) validates, SHA
  `66ce046900564ca0…`
- Build C (B + 0016 ARM) validates, SHA `0e32397dc02c8a68…`
- Diff B-vs-A: 9 runs, 77 bytes, confined to the six named sites plus the
  trailer CRC (which `finalize()` rewrites on any content change). The
  sites hold 78 patch bytes; the shortfall is bytes that coincidentally
  equal the stock stub bytes (the gate cave's displaced `push` halfword,
  the delay cave's embedded `bx lr`) and therefore do not diff. Every
  named site changed (6/6).
- Diff C-vs-B: exactly the ARM byte pair at file offset 175392
  (`0x03051674`) plus the trailer CRC.
- The gapless set also stacks after the full production manifest
  `0000–0018` (clock set included; scratch-renumbered 0020–0025) and
  validates, SHA `9d2d6503f5416793…`
- Before/after disassembly of all six sites plus the ARM site is printed
  in the output and reproduced in §4.

# Gapless playback analysis: Fosi Audio DAP Neo, stock firmware DP3_V137

Scope: reconstruct the track-transition path from binary evidence, locate the
inter-track gap, and define what a gapless patch must change. Every claim is
labelled **proven** (instruction bytes cited), **likely** (strong structural
inference), or **speculative**. All addresses are system-core (Cortex-M3 #0)
execution addresses unless marked core-1 (decoder core, `0x01000000` window).

Tools used: `mdis.py` (per-module Capstone disassembler with literal-pool
resolution; the shared `work/main/disasm.py` mis-maps overlapping overlays),
`scan.py` (BL-target and literal scans across all 82 modules). Both are in
this directory.

Key modules:

| Module | Role (evidence) |
|---|---|
| 0 | Resident system core: OS services, DAC configure `0x0305175e`, DMA config `0x0305ff74`, file system |
| 11 | USB Audio overlay, contains a byte-level copy of the DAC power sequence (`0x0307ea46..0x0307ead4`) |
| 27 | Player UI/task overlay, polls the codec service, holds `TotalFiles`/`CurrentFileNum` strings |
| 33 | Audio codec service overlay, codec open/stop, playback task, seek, next/end handling |
| 71–80 | Core-1 decoder programs, one per format, all executing in the same window `0x01000000` / data `0x01020000` |

Decoder program map (proven from embedded source-path strings / format strings
in each module; sizes are code+data bytes that must occupy the shared window):

| Module | Format | Evidence | Bytes (code+data) |
|---|---|---|---|
| 71 | MP3 | `Common\Codec\Audio\Mp3\libMad\mp3_decinternal.c` | 0x8f5c+0xc648 = 87,428 |
| 72 | WMA | `Common\Codec\Audio\Wma\wmalib\wmaudio_parse.c` | 0x162c0+0x67c0 = 117,376 |
| 73 | AAC/M4A | `Common\Codec\Audio\AAC\lib\aac_aacdec.c` | 0x12258+0x24f0 = 83,912 |
| 74 | WAV | `Common\Codec\Audio\Wav\WAV_LIB\pWAV_lib.c` | 0x88cc+0x4e30 = 55,036 |
| 75 | OGG Vorbis | `vorbis`, `floormemo need %d` | 0xf5d8+0xd184 = 116,700 |
| 76 | FLAC | `FLAC_frame_decode: flac_decode_frame returned %d` | 0x5ee0+0x24bc = 33,692 |
| 77 | ALAC in MP4 | `ftyppdinmoofmfra…`, `rice_history_mult` (likely) | 0x6b44+0x23a4 = 36,584 |
| 78 | APE | `ape open FAIL!` / `ape open OK` | 0x5924+0x2464 = 32,136 |
| 79 | DSD-DFF | `NO.%d frame dsdiff read frame err!` | 0x60a8+0x2308 = 33,712 |
| 80 | DSD-DSF | `NO.%d frame dsf read frame err` | 0x5d70+0x2308 = 32,888 |

Load sources are in flash at `code_load` `0x03125f28…0x031bd618+`
(module table), exec at `0x01000000`, so each program must be copied (or
remapped) into the one shared core-1 window. **Proven:** the windows overlap
completely; two decoder programs can never be resident at once.

## 1. The transition sequence

### 1.1 Steady-state playback and the PCM path

- The decoder core opens and reads the file itself through an RPC file
  service: every decoder module contains `HifiFileOpen/Seek/Read/Write/Close:
  timeout!!` and `FreqChange timeout!!!` strings. **Proven** (strings in
  modules 71–80). The system core is the file server; the decoder is the
  client.
- PCM reaches the DAC through a DMA channel programmed by module 0's
  `0x0305ff74` (channel-indexed DMAC setup; indexes `r0 < 6`, touches
  `0x600003a0/0x600003a4`). The playback-start code in module 33 calls it at
  `0x0308a8f6` with channel 5, source = pointer stored at `[0x03023928]`,
  destination = `0x40030024` (I2S TX data register), length =
  `[0x03023938]`. **Proven** (instruction operands). The USB-audio overlay
  (module 11) uses the same destination register, so local playback and USB
  audio share one DMA→I2S feed. **Likely:** `[0x03023928]/[0x03023938]` are
  the PCM ring-buffer pointer/length the decoder core fills via shared SRAM;
  no decoder module contains the I2S register literal, i.e. core 1 does not
  touch the I2S FIFO directly. The system core owns the DMA. **Proven**
  (literal scan of modules 71–80: zero hits for `0x40030024`/`0x60030024`).

### 1.2 End-of-track detection

- Module 33 registers a three-entry driver vtable in its data segment at
  `0x03036990`: `{ 0x03089e2f (open), 0x0308a1cb (playback task), 0x0308a927
  (stop/close) }`. **Proven** (data words at `0x03036990/94/98`).
- The playback task (`0x0308a1ca`) is an event loop over OS service
  `0x03067258` (wait-event) / `0x0306723c` (post-event). It waits for event
  **`0xec`** at `0x0308a504` (the decode-finished event) and handles it
  inline (repeat/advance logic below). **Proven** (event id immediate +
  handler flow). Who posts `0xec` (decoder-core monitor vs DMA interrupt)
  was not pinned down; **likely** posted when the decoder task reports EOF
  through the shared control block at `0x0304ad70`.
- The UI overlay (module 27) independently polls the codec dispatcher
  `0x03089c86` with message `0xea` at `0x0307e188` and then reads the
  halfword flag at `[0x03023926]`, looping with event `0x39` posts and a
  wait on `0x106` at `0x0307e19a..0x0307e1a4`. **Proven.** `[0x03023926]` is
  module 33's play-state/end flag for UI consumption (module 33 references
  it at `0x0308922c`, `0x03089b38`, `0x03089f74`).
- A separate "wait for decoder idle" idiom exists in the dispatcher's
  message-`0xe8` handler at `0x03089d5e`: it polls `0x03055be0(5)` (task-5
  state query) with `delay_ms(1)` steps and a 20,000-iteration cap at
  `0x03089d60..0x03089d94`, then clears the position words
  `[0x0302392c]`/`[0x03023930]`. **Proven.** This is a blocking
  synchronisation on the decoder task, used on the stop path.

### 1.3 Next-track selection

All inside the playback task `0x0308a1ca` and its helpers:

- Current index: halfword at `[0x030232a0+2]` in the global play-state
  struct. The NEXT-command branch (event `0x56`, waited on at
  `0x0308a4d4`) increments it at `0x0308a4dc..0x0308a4e2` and bounds-checks
  it against the total at `[0x0304ad70+0]` (decoder control block) at
  `0x0308a4e4..0x0308a4ea`. **Proven.**
- Play mode: word at `[[0x030232a0+8]+0x1c]`; values 6, 2 and 4 are
  special-cased at `0x0308a4ec..0x0308a4fe` (repeat / folder-repeat class
  modes) and skip the plain advance. **Proven** (compares); exact mode-name
  mapping is **likely** (2/4/6 = repeat-one / repeat-folder / shuffle-class
  modes is not provable from these bytes alone).
- On the end event (`0xec`, `0x0308a504`): repeat-one is tested via the word
  at `[0x0304b47c+0x2c]` (`0x0308a50e..0x0308a514`); folder bounds come from
  a per-folder table at `0x0307ab68` indexed by `[0x03004458]`, comparing
  entry fields `+0x10` and `+0x20` at `0x0308a532..0x0308a54c`. If no repeat
  applies it falls through to the open-prep helper `0x03089da6(0)` at
  `0x0308a500`/`0x0308a55a`, or posts `0xeb` at `0x0308a550`. **Proven.**

### 1.4 Open-prep helper `0x03089da6`

Called on every track start (from the dispatcher message `0x106` handler at
`0x03089c6a`/`0x03089d46`, from dispatcher case `0xea` at `0x03089ce6`, and
from the playback task at `0x0308a500`/`0x0308a55a`). It:

- probes the file type via `0x03059d58(0x03005714, idx)` (extension/type
  table in module 0 data) and stores the codec id halfword into the
  file-info struct at `0x03023980` (`0x03089dc0..0x03089dca`);
- branches on the play-state byte `[0x030232a0+0xe]` (values 2 and 4) at
  `0x03089dd2..0x03089de2`;
- calls `0x030535b0`, `0x03065332`, `0x0305791a`, re-probes, calls
  `0x03065336`, and posts event `0xee` via `0x0306723c` (`0x03089e16..
  0x03089e26`). **Proven** (call sequence). The exact semantics of the
  module-0 helpers are **likely** decoder-task stop/start and file-service
  calls; they were not individually reversed.

### 1.5 Codec open `0x03089e2e` (vtable entry 0)

Instruction-level sequence:

1. `0x03089e36`: `0x030670e0(0x23)`; `0x03089e3e`: post `0x2b`.
2. `0x03089e4a`: byte `[0x03023151] ← 0xff`.
3. DAC guard: `0x03089e52..0x03089e58`. If byte `[0x03023125] != 0`,
   branch to `0x03089f2a` and skip steps 4–5 entirely. If it is 0, set it
   to 1 and continue.
4. GPIO power-pin sequence `0x03089e5c..0x03089ec4` (helpers `0x030526f8`
   config / `0x03056098` set / `0x030560d2` clear): pins (port 2, pin 1),
   (1, 4), (2, 2), with `delay_ms` (`0x03064944`) arguments 2, 1, 8,
   then pin (2,1) again, then byte `[0x0302314c] ← 1`. Per the NeoPod pin
   map for this board: GPIO2.1 = DAC RESET, GPIO1.4 = AMP, GPIO2.2 =
   ENABLE_B. **Proven** (instructions; pin naming from NeoPod's replay of
   the identical sequence).
5. `0x03089ee6`: clock-gate helper `0x030611e0`; `0x03089ef0`:
   `bl 0x03051a46`, the common DAC start (see §2).
6. Per-open audio setup (runs every open, DAC guard or not):
   `0x03089f06`: I2S config `0x03055dcc(r0=1, r1=2, r3=0xbb80 = 48000, …)`;
   `0x03089f0e`: `0x0305094e(1,4)`; `0x03089f16`: `delay_ms(100)`;
   `0x03089f1e`: `0x03050a00(1,4)`; post `0x2b` again at `0x03089f2c`.
   (The 48000 here is an initialisation constant; the real rate change is
   pushed to the decoder core through its `FreqChange` RPC, whose timeout
   string is present in every decoder module. **Likely.**)
7. Decoder control block setup: `0x03089f36`: halfword
   `[0x0304ad70+2] ← 0`; `0x03089f3a`: state halfword `[0x03023922] ← 4`;
   post `0x10a`; filename/info fields copied from the caller's struct
   (`0x03089f62..0x03089fa0`).
8. Codec dispatch on the type halfword at `[fileinfo+0xf2]`
   (`0x03089fac`): `0x63` → `0x03089da6(3)`; `6` → `0x03059d58(·, 1)`;
   then the decoder-info struct at `0x030368d8` (module 33 data) is rebuilt
   from global state fields `[0x030232a0+0x61]`, `+0x63`, `+0x68`, and the
   EQ/biquad coefficient table is refilled via `0x0304aef4`
   (`0x03089fc0..0x0308a08a`). **Proven.**
9. Position-sync wait: a loop at `0x0308a0ee..0x0308a118` polls the
   decoder-reported position (`[0x030232a0+0x64]`) against the computed
   target, calling `delay_ms(15)` per iteration, capped at 200 iterations
   (up to 3 s worst case; normally exits on match). **Proven.**
10. `0x0308a126`: play-enable `[0x0304ad70+0x48] ← 1`; `0x0308a12a`:
    `0x0306712c(0x23)`; `delay_ms(15)`; start calls `0x030651cc`,
    `0x030514f8`, `0x030514f2`, `0x0306ccdc`; per-channel service config
    for ids `0x1a`/`0x1b`; finally the open function re-enters its own
    dispatcher with message `0xe5` at `0x0308a196`. **Proven.**

### 1.6 Stop/close `0x0308a926` (vtable entry 2): the only DAC power-down

- `0x0308a92e`: clears `[0x030235a8]`; returns early if the file-info
  halfword `[0x03023980] == 0`.
- DAC power-down, gated on `[0x03023125] == 1` and `[0x03023131] == 0`
  (`0x0308a93c..0x0308a94a`): clears `[0x03023125]` at `0x0308a94c`, then
  GPIO sequences for (2, 8) [DAC MUTE per NeoPod], (1, 4) [AMP], calls the
  DAC power-down I2C script `0x03051736` at `0x0308a98a`, then (2, 1)
  [RESET] and (2, 2) [ENABLE_B] sequences (`0x0308a98e..0x0308a9be+`).
  **Proven.**
- Tail at `0x0308a9d2`: self-dispatch message `0xea`; if decoder state
  `[0x03023922] != 3` call `0x03065188`; set state `← 4`; further GPIO
  (2,2) handling and service teardown for ids `0x1a`/`0x1b`
  (`0x0308aa0a..0x0308aa3a`). **Proven.**

The natural end-of-track path (§1.3) calls only the open-prep
helper `0x03089da6` and the codec-open chain. It never calls the stop
function `0x0308a926`. A BL scan of all 82 modules confirms `0x0308a926` is
reachable only through the vtable. **Proven** (scan + handler flow).

## 2. DAC init: per-track or per-session?

The full DAC sequence = GPIO pin phase (delays 2+1+8 = 11 ms) +
`0x03051a46`, which writes CS43198 map `0x0B0000 = 0x1F`, waits
`delay_ms(80)`, raises AMP GPIO1.4, then calls `0x0305175e`, the complete
CS43198 configure: ~50 I2C register writes (device address byte `0x66`),
including PCM volume registers `0x090001/0x090002` written muted
(0xFF), a second `delay_ms(80)` at `0x03051894`, two `delay_us(100)`
power-bit release waits, and a final `delay_ms(10)` at `0x0305197e`.
Staged-delay total: 11 + 80 + 80 + 10 = 181 ms, plus I2C transfer time.
Delay units are milliseconds: proven from the body of `0x03064944`
(loop count = arg × timer/0xbb8) and from NeoPod's replay of the same
constants. The configure write sequence matches NeoPod's `dac_configure`
write-for-write. **Proven.**

Verdict: **the DAC power/configure sequence is per playback session, not
per track** (proven). It runs only when the guard byte `[0x03023125]` is 0
(`0x03089e52`), and that byte is cleared only by the stop/close function
(`0x0308a94c`), which the natural track-advance path does not call. It runs
again after any full stop (user stop, USB-DAC mode switch; module 11 has
its own copy of the sequence and shares the same flag at `0x0307ec10`), and
on the first play after boot. If a gapless patch does nothing else, the DAC
is already not the per-track problem.

What *does* run per track, unconditionally, inside codec open: the fixed
`delay_ms(100)` at `0x03089f16`, the I2S/DMA re-setup, the decoder
control-block reset, the decoder-info struct rebuild, and the
position-sync polling loop (§1.5 steps 6–9).

## 3. Decoder reload and prefetch

- Reload: all ten decoder programs share one exec window, so a codec
  change forces a full image copy (32,888–117,376 bytes from the flash
  load window) plus a core-1 restart. **Proven** (module table). For a
  same-codec transition, no skip path is visible: codec open rebuilds the
  control block at `0x0304ad70`, the info struct at `0x030368d8`, resets
  the state halfword `[0x03023922]`, and re-runs its wait loops on every
  call, and the end-of-track handler goes through the same open-prep
  helper as a cold start. **Likely:** the decoder image is re-copied or at
  least fully re-initialised per track even for the same codec. (The core-1
  loader routine itself, in module 0, was not isolated in this pass;
  that is the one unproven link. The loader's existence and per-open
  re-setup around it are proven.)
- Prefetch / double-buffering: none. Proven as far as static evidence
  reaches: there is exactly one file-info struct (`0x03023980`), one
  decoder control block (`0x0304ad70`), one codec-info struct
  (`0x030368d8`), one PCM ring pointer pair (`0x03023928`/`0x03023938`),
  and one current-index halfword. The next file is first touched inside
  the end-event handler, after the current decoder has finished. No code
  path opens, parses, or stages the next track during playback of the
  current one.

## 4. Gap-source ranking

1. Sequential, post-EOF open pipeline (no prefetch). End event →
   repeat/index logic → type probe → file open + metadata parse (decoder
   core's own `HifiFileOpen` RPC + format preparse, e.g. libMad's
   `mp3_preparse.c`) → decoder start. All of it happens in the silence
   after the track ends. Structural, **proven**.
2. Per-open fixed waits in codec open. `delay_ms(100)` at
   `0x03089f16`, plus the position-sync loop (15 ms polls, up to 200
   iterations) at `0x0308a10e`, plus decoder-idle polling on paths that
   pass through stop (1 ms polls, 20,000 cap, `0x03089d60`). **Proven**
   code; typical-case duration is data-dependent and unmeasured.
3. Decoder image reload on codec change (32–117 KB flash→SRAM copy +
   core restart), and full decoder re-initialisation even when the codec
   is unchanged. Window sharing **proven**; per-track reload **likely**.
4. File open + tag/metadata parse latency on the system core's file
   service (SD/eMMC reads through the `HifiFile*` RPC). **Likely** tens of
   ms for typical files; not separately measurable statically.
5. DAC full re-init (181 ms staged + ~50 I2C writes, PCM starting
   muted). Only when a stop/close intervened (user stop, mode switch),
   not on natural track advance. **Proven** conditional.
6. Sample-rate change handling. Codec open initialises I2S at a fixed
   48000 (`0x03089f06`) and rate changes go through the decoder's
   `FreqChange` RPC; a rate change between tracks likely re-syncs the
   I2S/DAC clocking mid-transition. **Speculative** as a gap contributor;
   the fixed-48000 init constant is proven.

## 5. Gapless design that fits this architecture

Constraints imposed by the evidence: one decoder window, one file-info
struct, one PCM DMA feed, a message-driven codec task. True crossfade is
not achievable without a second decoder instance and a mixer; the
achievable target is zero/near-zero dead air on same-album transitions.

1. Pre-open the next track during the current one's last seconds.
   The playback task already tracks position (`[0x0302392c]` words; total
   in the file-info struct). When remaining time < ~5 s, run the open-prep
   probe `0x03089da6` equivalent for index+1 and pre-parse its metadata
   into a **shadow copy** of the file-info struct. The patch must allocate
   the shadow (≥ 0xf4 bytes) itself. Stock code has exactly one instance,
   at `0x03023980`. *Likely feasible; the probe is read-mostly.*
2. Same-codec fast path. Compare the next file's codec-id halfword
   (`[fileinfo+0xf2]` semantics) with the current one. If equal, skip the
   decoder image copy and core restart entirely and reuse the resident
   program, issuing only a new `HifiFileOpen` on core 1. This removes gap
   source 3 for the common album case. *Likely the single biggest win
   after prefetch; needs the loader identified to patch precisely.*
3. Never route a natural transition through stop/close. Keep the DAC
   guard byte `[0x03023125]` set across transitions (stock already does
   this; preserve it), and preserve the output-state byte
   `[0x0302314c]`, the volume byte `[0x030232a0+0x12]`, and the EQ source
   bytes at `[0x030232a0+0x61..0x6b]` that codec open re-expands into
   `0x0304aef4`. *Proven necessary state.*
4. Cut the fixed waits on the fast path. When codec and sample rate
   are unchanged, the `delay_ms(100)` at `0x03089f16` and the
   position-sync loop at `0x0308a0ee` guard hardware that never changed;
   shorten or skip them on the same-codec/same-rate branch. *Speculative
   on safety margins. Validate on hardware; the delays may cover I2S
   FIFO drain.*
5. Start the next decoder in the EOF tick, not after it. Move the
   advance decision earlier: precompute the next index (repeat/mode logic
   of §1.3 is cheap and depends only on state at `0x030232a0`,
   `0x0304b47c+0x2c`, and the folder table `0x0307ab68`) so the end event
   `0xec` handler only has to flip the pre-staged file into the decoder
   and re-arm DMA channel 5 (the `0x0305ff74` call at `0x0308a8f6`).
   Residual gap then ≈ one file-open RPC + DMA re-arm. *Design proposal;
   consistent with all traced control flow.*
6. Codec-change transitions cannot avoid the image copy; overlap it
   with the tail of the current track only if the copy target is staged
   in unused SRAM and flipped at EOF (the window itself is busy until the
   current decoder stops, so a straight pre-copy into `0x01000000` is
   impossible). *Proven constraint; staging area availability
   speculative.*

## 6. What was not resolved

- The core-1 loader routine in module 0 (which function copies modules
  71–80, and whether it compares against the resident image), the one
  link needed to convert finding 3 from "likely" to "proven".
- Exact semantics of module-0 helpers `0x030535b0`, `0x03065332`,
  `0x0305791a`, `0x03065336`, `0x030670e0`, `0x0306712c` (OS/decoder-task
  primitives, inferred from call sites).
- Who posts the decode-finished event `0xec`.
- Play-mode enum names for values 2/4/6 at `[[0x030232a0+8]+0x1c]`.
- Module 77's format (ALAC) rests on MP4 atom strings + ALAC rice-coding
  debug strings, labelled likely.

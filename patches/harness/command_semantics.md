# Core-1 decoder command semantics: pinned values and evidence

Phase D, milestone 1. Derived from module 76 (FLAC) under the Unicorn harness
in this directory (`harness.py`, `run_log.txt`), cross-checked against
`analysis/core1_loader_protocol.md` and the module-33 server code. All
decoder-side addresses are module 76's; the runtime is shared across decoder
modules 71–80 but data addresses and the format id must be re-derived per
module (precedent: the file-size word sits at a different offset in module 74).

## 1. Execution model (corrects the loader doc's framing)

- Decoders are **complete core-1 programs**, not plug-ins: own vector table,
  C startup (zeroes its own BSS; the module record's `bss_len` is 0), own
  main loop. The Echo-lineage `emu74.py` direct-call design does not transfer.
- **Core-1 code view is 0-based.** The table-1 vector word at code+4 is
  0x00002849 and the reset trampoline branches to raw 0-based addresses
  (table-2 reset = 0x000014E3). The harness maps the code image at both
  0x00000000 (execution) and 0x01000000 (the VA view data pointers use).
  Data addresses (0x0102xxxx) are absolute in both views.
- The system never writes the decoder's command word directly (negative
  search: the literals 0x0102221C / 0x01022290 / 0x01022224 / 0x0102222C /
  0x01022298 occur only inside decoder modules). **All system→decoder
  control flows through MU messages**; the decoder's own receive handlers
  translate them into the shared-memory cells below. This settles
  core1_loader_protocol.md §7.4's open question.

## 2. Boot sequence (module 76, executed in the harness)

Entry 0x010014E2 (reset): zeroes BSS 0x010224BC len 0x23550 (window must
reach 0x01045A0C) → init fn 0x010008AE → registers vector slots
**0x1A → ch1 receiver 0x010012FC**, **0x1B → ch2 receiver 0x01001390** → MU
control-set fn 0x01004EC4 (mask 2, mask 4) → clears flag 0x0102222C →
event-init fn 0x01004BB2(0x115) → **sends MU ch0 cmd 1, param 0, the READY
signal** → zeroes info structs → main loop at 0x0100156C.

Boot + READY reproduced in the harness (run_log.txt slice 3).

## 3. Message unit (base 0x40110000, unit stride 0x50)

Decoder-side driver at 0x01004E80–0x0100505E. Send args are (value, unit,
channel). Register map, per channel `ch`:

| Operation | Function | Address |
|---|---|---|
| write cmd | 0x01004FB0 | `[unit + 0x30 + 8*ch]` |
| write param | 0x01004FDC | `[unit + 0x34 + 8*ch]` |
| read cmd | 0x01004F80 | `[unit + 0x08 + 8*ch]` |
| read param | 0x01004F54 | `[unit + 0x0C + 8*ch]` |
| service/ack write | 0x01004EDC(unit, mask) | writes mask to `[unit + 0x04]` |

Channel masks for 0x01004EDC: ch0=1, ch1=2, ch2=4, ch3=8 (this is a write,
not a poll; an earlier reading of it as a status poll was wrong).

- **ch0 (boot)**: handler fn 0x01000820, no BL callers (polled/ISR). On cmd 2
  (query) it replies cmd 3 + param 0, then polls ≤1000×delay(5) for cmd 4
  (stop-class); timeout sets [0x0102229C]=1.
- **ch3 (value query)**: handler fn 0x01000884: on cmd 6 it tail-calls
  0x01000B16 with the param. System side answers cmd 5 with a param value
  (module 0 receiver). Not yet exercised by the harness; see §9.

## 4. ch1 (system → decoder commands) and the command word

Receiver fn 0x010012FC reads (cmd, param) and writes the decoder's command
word at **0x0102221C**; the argument word is at **0x01022220** (one `strd`).
Translation (instruction-verified):

| sys ch1 cmd | cmd word | arg |
|---|---|---|
| 0x01 | 1 (AUDIO_DECODE_OPEN) | – |
| 0x04 | 2 (position/status report) | – |
| 0x07 | 4 | – |
| 0x09 | 5 | – |
| 0x0B | 3 | param → arg word |
| 0x0D | 6 | param → arg word |
| 0xCB | 14 | param → arg word |
| 0xCD | 13 | param → arg word |

Unknown ch1 cmds are ignored. Decoder → system ch1 sends observed: **cmd 2**
= open error (with the `###AUDIO_DECODE_OPEN error!###` printf), **cmd 3 +
param = info struct 0x010227F4** = stream info ready, **cmd 5 + param =
info struct** = position/status reply, **cmd 6 + param 0** = status query
failed / end-of-stream, **cmd 0xC** = reply to cmd word 3, **cmd 0xE** =
reply to cmd word 6.

## 5. Command-word dispatch (main loop 0x0100156C, TBB at 0x0100159A)

| Value | Target | Meaning (evidence) |
|---|---|---|
| 0 | none | idle (loop sleeps via `wfi` fn 0x010028DC when cmd word and ctrl[0] are both 0) |
| 1 | 0x010015AE | **AUDIO_DECODE_OPEN**: calls engine-open dispatcher 0x01004D08; on result 1 parses the info struct (helpers 0x01004D9E/0x01004DBC/0x01004D80) and **sends ch1 cmd 3, param = 0x010227F4**; on failure prints `###AUDIO_DECODE_OPEN error!###` and sends ch1 cmd 2. Executed end-to-end in the harness. |
| 2 | 0x0100172C | **Position/status report**: calls engine fn 0x01004D26; success → sends ch1 cmd 5 + info struct; failure → sends ch1 cmd 6 + 0 (this is the end-of-stream signal: observed at EOF). |
| 3 | 0x0100178E | **Arg command** (seek-shaped): calls engine fn 0x01004D44(arg from 0x01022220), replies ch1 cmd 0xC. Exact param split not fully resolved. |
| 4, 5, 8–12 | 0x0100175C | Shared case: calls the buffer pump fn 0x0100232E with [0x01022118], falls into the loop tail. No engine call, in FLAC these are pump/idle-class commands. |
| 6 | 0x010017C0 | Calls engine fn 0x01004E0C, replies ch1 cmd 0xE + info struct. |
| 7 | 0x010017DC | Buffer (re)setup: fn 0x0100264A with size 0x15C00 (the 89,856-byte file buffer). Shared with 13. |
| 13 | 0x010017DC | Same as 7 (arrives via ch1 0xCD with an arg). |
| 14 | 0x010017EC | Clear + tail only (arrives via ch1 0xCB). |

The loop tail (0x010017EE, every iteration) also tests **event 0x115**
(test-and-clear fn 0x01004B8C over the bitmap at **0x010459D0**; event 0x115
= word 8, bit 21) and calls the pump fn 0x0100232E when set. Setting that
bit from the harness demonstrably drives file-buffer refills.
ctrl[+0xC] == 1 prints `FreqChange timeout!!!` once and clears. It is a
one-shot notification field written by the FreqChange machinery, not by
the loop.

## 6. ch2 (HifiFile RPC): receiver, control struct, reply states

Control struct at **0x01022290**: +0 state byte, +4 last received cmd,
+8 last received param (its low byte is the "status byte" 0x01022298 of the
loader doc). Receiver fn 0x01001390 stores cmd→ctrl+4, param→ctrl+8, then:

| rx cmd | Effect |
|---|---|
| 0x65 | **File-info push** (the system's answer to decoder init): generic path copies byte[struct+0]→[0x01022218+…] (handle), word[struct+4]→[0x01022230], word[struct+8]→handle table, word[struct+0x14]→**format word 0x01022224**; then **ctrl[0] = 1**. Struct formats {2,7} take an extended path with extra fields. |
| 0x67 | Ignored (0x66 is a no-reply notification on the server side). |
| 0x6A | Seek reply → ctrl[0] = 2, flag 0x0102222C = 1 |
| 0x6C | Read reply → ctrl[0] = 3, flag = 1; first-reply bookkeeping copies the Read block's result word into the handle table and sets 0x0102222D |
| 0x6E | Write reply → ctrl[0] = 4, flag = 1 |
| 0x70 | Info reply (to 0x6F) → ctrl[0] = 5, flag = 1 |
| 0x72 | Info reply (to 0x71) → ctrl[0] = 6, flag = 1 |
| 0x74 | Close reply → if param ≠ 0: ctrl[0] = 7; flag = 1 either way |
| 0xD1 | If param ≠ 0: ctrl[0] = 9; flag = 1 either way |

ctrl[0] states (second TBB at 0x01001808): **1 = OPEN** (installs nothing;
reads the format word, {2,7} take path B, then **sends ch2 cmd 0x66,
param 0**, the open notification the server treats as a sink); 2–6 = "last
RPC completed" markers (cleared, no action); 7 = sends ch2 cmd 0x75;
**8 = installs the file-ops vtable at 0x010220F4 via fn 0x01000456 and
sends ch2 cmd 0x68**; 9 = sends ch2 cmd 0xD3.

Open questions inside this table: nothing traced yet *sets* ctrl[0] = 8 in
module 76 (the vtable install); observed HifiFile reads work without it.
The runtime file layer calls the stubs directly. And the decoder **sends
0x66, not 0x68, at open** (harness trace), which settles the loader doc's
"0x66 or 0x68" unknown for the open path: 0x68 belongs to state 8.

## 7. HifiFile client stubs and server semantics

Stubs: Seek 0x010002F4, Read 0x01000350, Write 0x010003B6, Close
0x0100040E; Open has only a wait fn 0x010002A8 (the open itself is the 0x65
push + 0x66 notify exchange; there is no Open *request*). Blocks: Seek
0x01022254, Read 0x01022260, Write 0x0102226C. Common pattern: fill the
block, clear flag 0x0102222C, send cmd (0x69/0x6B/0x6D) + block address as
param on ch2, poll the flag with delay(1), timeout 0x2DC6C0 iterations
(printfs `HifiFileXxx: timeout!!`). Seek block: [0]=offset (s32),
[+4]=whence, [+8]=handle byte; on completion the stub copies [blk+0] into
`handle_table[handle]`. Read block: [0]=buffer VA, [+4]=count,
[+8]=handle; pre-check: returns immediately if 0x0102222D == 0 (that flag
is set by the receiver's first-Read-reply bookkeeping and by fn
0x01000456). Read returns the status byte at 0x01022298; the byte count
comes from the block.

Server (module 33 fn 0x030895DA) mirrors this: TBB on cmd−0x66 (valid
0x66–0x75), performs the FS call, writes a result word into the block,
replies cmd+1. Seek result [blk+0] ← folder-table word (harness substitutes
the host file size; flagged as a semantic guess). Read result word at
[blk+4] is "folder-derived" per the server trace (harness substitutes
bytes-read; the decoder's subsequent behaviour, buffer fills of exactly
the requested sizes, is consistent with it).

**Harness serving model**: synchronous at the param-send hook. On a ch2
request the harness performs the host-file operation immediately and
replicates the receiver's reply effects (ctrl+4/+8, ctrl[0] per §6, flag),
so the stub's first poll succeeds. Close replies with param 0 by design
(a nonzero param would force the ctrl[0]=7 → 0x75 flow). 0x6F replies
param = file size; 0x71 replies param 0 (server returns folder[ idx ]+0x10
/ +0x20 words; field meanings unproven).

## 8. Format word and the engine dispatcher table

[0x01022224] is set only from the 0x65 struct's +0x14 field. The engine
entry points (0x01004D08 open, 0x01004D26 position, 0x01004D44,
0x01004E0C, …) are **dispatchers**: `ip = table[fmt]` at **0x01022494**
(image-initialised data), then `bx ip` with r0 = a subfunction selector
(open used r0 = 8). If fmt == 0xFF they return −1.

Module 76's table has exactly one nonzero slot: **fmt 6 → dispatcher
0x00002ADD. FLAC's format id is 6** (proven. With fmt 5 the open branched
to table[5] = 0 and faulted at PC 0; with 6 the full open/decode ran.)
The {2,7} special-case branches in the open path and 0x65 receiver, and
the {8,9} check in the open case, are this id space's other members; the
full id↔codec mapping is not yet pinned (the table offset differs per
module: module 71's data at +0x2494 is constants, module 80's data image
is too short, so each module's table must be located individually).

## 9. Parameter page (144 bytes at 0x01020000)

Written by the system before reset release; contents runtime-built and
undecoded. Two fields are now identified because the decoder's delay loops
divide by them:

- **[page+0x20]**: read as Hz by delay fn 0x01000B54 (count ≈
  arg × (Hz/1e6) / 10).
- **[page+0x24]**: read as Hz by delay fn 0x01000B78 (count =
  arg × (Hz/3000) − 1 loop).

With a zero page the second underflows into a ~4×10⁹-iteration spin (this
was the harness's first post-open stall; the open path was inside a
FreqChange delay with CRU base 0x40180000 in a register). The harness
writes plausible rates (96 MHz / 24 MHz). Timing fidelity is not claimed;
the values only need to be nonzero and sane. All other page fields remain
undecoded; the decoder ran a full open with zeros elsewhere.

## 10. Demonstrated run (run_log.txt, module 76 + test44.flac)

Boot → READY (ch0 cmd 1) → harness delivers the 0x65 info push → decoder
prefills its double buffer with HifiFile Reads → sends ch2 0x66 (open
accepted) → system ch1 cmd 1 → engine open: Seek/Read header parse,
`FLAC init: samplerate=%d, channels=%d, …` printf, register writes to the
decoder-local MMIO at 0x0106xxxx (DMA/audio setup), 8192-byte frame-data
reads → **ch1 cmd 3 stream-info report** → position polls drive the engine
through the file → `decode_frame: end of file` → **ch1 cmd 6**
(end-of-stream). 14 reads, 36,656 bytes served (includes header re-reads).

## 11. Fidelity limits and the PCM open item

- The harness **replicates** the ch1/ch2 receive handlers' effects rather
  than executing them via interrupt injection (the handlers are polled/ISR
  entry points with no BL callers; snapshot/restore IRQ injection is the
  upgrade path). All other decoder code (boot, main loop, stubs, engine)
  executes for real.
- MMIO is absorbed as RAM (MU excepted, which is fully modelled). Writes
  during open to 0x0106xxxx register addresses are logged in the trace's
  fault-free run only implicitly; UC_HOOK_MEM_INVALID does not fire on
  this Unicorn build, so unknown-MMIO discovery relied on emu_start errors.
- **PCM (stretch) was not captured.** The decoder provably runs its frame
  loop to EOF, but across event-pumped refills, position polls, and every
  candidate start command (cmd words 3–6, 13, 14), write-censuses over RAM
  and the 0x0106xxxx–0x0108xxxx MMIO show **no sample data written
  anywhere**. The FLAC library's internal channel buffers (its large BSS)
  are never touched, i.e. the engine frame loop is running in a
  scan/discard mode. The missing trigger is structural. Candidates, in
  order: (a) the ch3 FreqChange-completion handshake (decoder-side ch3 cmd
  6 → fn 0x01000B16 has never been delivered by the harness); (b) a
  DMA-buffer state machine the system arms via the stub family's cmd 8
  (DMA start) on the system side; (c) an engine enable flag inside the
  FLAC dispatcher's state that only a specific subfunction selector sets.
  Closing it is milestone 2 work; the §6 protocol sample-precision test
  (work/perf/vorbis_test.md) can already run its *protocol* half against
  this harness with module 75 once that module's addresses are re-derived.

---

## Milestone-2 addendum (Phase D, 2026-10-31): §11 resolved, PCM captured

The §11 open item is closed; its central claim is **corrected**. There is
no scan/discard mode. Full detail: `milestone2.md` (this folder);
code `harness2.py`, driver `run_m2.py`, logs `run_log_m2_*.txt`.

- **The frame loop starved because of the harness, not the decoder.**
  §7's Read stub returns the MU reply param word [0x01022298]; milestone
  1's server sent that reply with param = 0, so every refilled FS slot
  registered 0 valid bytes and the buffered reader reported EOF on a
  full file. Module 33's real server (Read case at 0x030895DA) sends the
  0x6C reply with param = bytes read and writes folder+0x20 into blk+4
  (Seek: into blk+0, post-call). The milestone-2 server replicates this;
  the §10 run's zero-filled input buffer and untouched channel buffers
  follow from the defect alone.
- **Candidate (a), the ch3 FreqChange completion, is disproven.** Its
  only decoder-side effect is clearing the byte at 0x01022130 (fn
  0xB16); the flag stayed 0 through every successful decode.
- **Candidate (b) is confirmed in decoder-local form.** After the first
  frame's subframes, the decoder WFI-waits inside the audio-output fn
  0x524A for the DMA-complete flags at [0x010220E4+0/+4] (set by the
  interrupt handlers 0x5174/0x518A via walker 0x5198) and then spins on
  the DMA status read fn 0x50A8 (bit 0x8000 at [0x01060008 − 0x3C·ch]).
  Modelling zero-latency DMA completion unblocked the full decode. No
  system-side stub-cmd-8 effect reaches the decoder in this path;
  candidate (c) (an extra enable selector) was not needed and is
  disproven as a separate blocker.
- **PCM location.** For LPC subframes of order ≥ 3, `decode_subframe_lpc`
  (fn 0x423E) never reconstructs on the CPU: coefficients are uploaded
  to 0x0106B000, order/shift go through fn 0x2AC4, and the residual plane
  is handed to the DMA output fn 0x524A. The audio block restores the
  signal in hardware. CPU-side planes hold warm-up + residual only.
  CONSTANT/VERBATIM/FIXED subframes (and the fn 0x2E9A interleave +
  channel-assignment conversion) do complete on the CPU. The harness
  models the restore in Python at the 0x2E9A point.
- **Measured result.** test48.flac decodes **bit-exact** against ffmpeg
  (48,000/48,000 samples per channel, whole file). test44.flac: L
  87,552/87,552 bit-exact, R exact except the final full frame (side
  constant read as 1 vs 0, R uniformly −1 LSB), and the final
  648-sample frame is not decoded by the stock flow; the decoder's
  total_samples is STREAMINFO − 128 in both files. Residuals are
  itemised in milestone2.md.
- **Gapless R1 (decoder side): cleared.** After file A reached EOS, the
  resident decoder accepted a 0x65 push for file B (different rate,
  size, total), issued 0x66, reported B's stream info, and decoded B
  bit-exact with no reload, no reset trampoline and no parameter-page
  rewrite. Stop (cmd word 6 → sel 15) → re-open of the same file
  reproduces the fresh-boot PCM byte-for-byte. Parameter page (144 B)
  is byte-identical between load-skipped and stock-reload opens and is
  never written by the decoder in-session; the only stale fields found
  are the DMA-complete flag [0x010220E4+4] and one stream-state word
  [0x010222D4], both behaviour-neutral in the traces
  (`run_log_m2_diff.txt`).

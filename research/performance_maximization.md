# Maximum performance from the DAP Neo hardware: test results, finish lines, and the implementation plan

Compiled 2026-10-31. Companion to `README.md` (easiest paths) and the
Phase 1/2 analysis in `../analysis/`. This document does three things:
reports the three confirmation tests commissioned with it, defines
measurable finish lines for "maximum performance" on each axis with
the instrument that settles each one, and lays out the phased
implementation plan those tests unlocked.

Standing rule for this project, applied throughout: **a claim that
something is impossible is a hypothesis, not a boundary.** §5 is the
register of such claims and how each was or will be settled, by
measurement or by building the thing, not by citation.

## 1. The hardware ceiling (what "maximum" means here)

From the Cirrus Logic CS43198 datasheet: 32-bit DAC, PCM sample rates
32–384 kHz, DSD to DSD256, 130 dB dynamic range (A-weighted),
−115 dB THD+N, 110 dB interchannel isolation, non-decimating volume
control in 0.5 dB steps. The DAC is not the bottleneck for anything
this device plays; every loss below that ceiling is firmware's.

From the firmware itself (this round, `../analysis/clock_table.md`):
the RKnanoD's two cores are clocked by a request solver
(`FREQSetFreq`, module 0 `0x03066EFC`) over a 36-row table at
`0x03079824`. The decode core (B) caps at 480 MHz, the system core
(A) at 200 MHz in playback rows, with a 96 MHz floor row. Core 1's
parameter and status window at `0x01020000` is 128 KiB
(`0x01020000–0x01042000`), but a decoder's full data footprint is larger:
the Vorbis module's BSS alone runs to `0x0105e9d4`, about 251 KiB from the
data base, and the extent varies per decoder. Decoder programs are
32,888–117,376 bytes each and share one exec window.

So the performance problem is never raw silicon. It is: decoder
arithmetic precision, transition latency, wasted clock, and unmeasured
headroom. All four are firmware properties.

## 2. Test results

### 2.1 Vorbis decode precision: the bug is real, and proven

Full evidence: `../analysis/vorbis_precision_test.md`.

**Verdict: proven.** Module 75 is Xiph Tremor (lowmem branch) built
with `_LOW_ACCURACY_`, the identical configuration berettavexee
documented for the Echo Mini. All 11 signature tables are present in
low form only, byte-for-byte, at the same offsets reported for the
Echo module (combined code‖data `0x1BE5C` / `0x1C25E`); module sizes
match exactly (62,936 code / 53,636 data); the multiply census matches
(one `smull`, zero `smlal`; the 64-bit path is compiled out); the
leaked SDK's own Vorbis header carries `#define _LOW_ACCURACY_`.

Mechanism: the IMDCT/windowing stage. `_LOW_ACCURACY_` stores the
twiddle and window constants as bytes (≈ their top 8 bits) and removes
the wide multiply path. Output is still 16-bit samples; the loss is
arithmetic noise inside the transform.

Measured effect (the patch author's A/B of the identical build mode,
PC-side): 38–43 dB SNR against a reference decode, ≈ 7 effective
bits, versus 60.4 dB for full-accuracy Tremor and 66.6 dB for
floating-point libvorbis on the same file. On a 130 dB DAC, the Vorbis
decoder is the weakest link in the entire chain by ~90 dB. The
full-accuracy rebuild costs +2.8% CPU and +30.6 KB of constant
tables (13.7 KB → 44.3 KB).

Not yet done: measuring module 75's own PCM output. The decoder is a
full core-1 program driven by the message-unit/HifiFile RPC. There
is no self-contained decode entry to call. The harness specification
and the full test protocol (pinned encodes at q5/q8, a quiet-fade
file, a 96 kHz file; ffmpeg and PC Tremor ±`_LOW_ACCURACY_` as
references; SNR/ENOB scoring; acceptance criteria) are written in
§6 of the evidence doc and become Phase D below. The verdict does not
depend on it: build identity is byte-proven, and the A/B numbers are
for the identical build mode.

### 2.2 The clock table: stock runs the decode core at its cap

Full evidence: `../analysis/clock_table.md`. The table sits at module
0 exec `0x03079824` (image offset `0x52ED0`, exactly one copy), 36
rows × 0x1C bytes in the SDK's struct format (id word, then Hz fields:
PLL, A-core, A-bus fields, B-core, B-bus). Proven live, not just
present: the sole referencing function decompiles to the SDK's
`FREQSetFreq` solver. It sums the six fields over the active-request
bitmap, floors each at row 1, caps at row 35, and programs the clock
unit. Callers use the request/release pair `0x030670E0` / `0x0306712C`
(the same pair visible all over the Phase 1 codec-open chain). Codec
row assignments, derived from module 33's dispatch plus a call-site
sweep, match nanitecfw's published Echo Nano row comments row-for-row.

What stock actually runs (solver output, codec row alone):

| Stream | Decode core (B) | Note |
|---|---|---|
| MP3 ≤128 kbps / 44.1 kHz tier | 96 MHz | the only lean row |
| MP3 high tier | 200 MHz | |
| WMA, AAC | 300 MHz | |
| WAV (PCM) | **450 MHz** | for a decoder that is essentially a copy |
| OGG tiers 1–3 | 400 MHz | |
| OGG top tier, FLAC, ALAC, APE, DSD-DFF/DSF | **480 MHz (the cap)** | one row for everything hi-res |

System core sits at 150–200 MHz during playback. Rows 23–25 are the
EQ rows (36/72/140 MHz, EQ already has its own clock budget, relevant
to the EQ insertion work). Row 30 is library update; row 35 doubles
as the full-speed burst row.

Read on this: the rows are set by format family, not by measured
need. WAV at 450 MHz gives that away. nanitecfw shipped, on the
sibling build with the same solver, solver outputs of 144 MHz
(MP3-class), 240 MHz (OGG), 288 MHz (FLAC-class) with the system core
parked at the 96 MHz floor, and the Neo's headroom is equal or larger
on every format. Two consequences, one per direction:

- Power: most of the battery-profile win is a data-only edit of
  this table (plain Hz values, no per-module checksum; the patcher
  already handles the package CRC). No code required.
- Latency/quality: clocks are not the constraint anywhere. At
  480 MHz the decode core has enormous slack, which is what makes
  transition-overlap decode and a +2.8% Vorbis rebuild free in
  practice.

### 2.3 Event 0xEC: poster found; the gapless hook moves earlier

Full evidence: `../analysis/ec_poster.md`.

**Verdict: proven.** 0xEC is posted by a playback monitor in module 0
(`0x03064F7E`), from exactly two sites (`0x0306500C`, `0x03065032`).
Module 33 registers it as the message-unit channel-14 callback during
codec open (`0x03088D8A`, `0x03088E08`); nothing calls it directly,
which is why earlier passes missed it. The monitor polls the codec
through the stub dispatcher, and on confirming end-of-stream it
sets the state word to 4, silences the PCM ring (`0x03054E66`),
zeroes the position word, and only then posts 0xEC to the playback
task (bitmap word 7, bit 12; post `0x0306723C`, test-and-clear
`0x03067258`; the task at `0x0308A504` is the only tester). The search
was exhaustive: every post call site in all 82 modules had its
argument provenance resolved.

Design consequence: the Phase 1 gapless plan hooked the consumer
(the task's 0xEC handler). That is too late. The ring is already
muted and position already destroyed when the event fires. The
hooks are the monitor's finalize blocks (`0x03064FFC`, `0x03065022`)
or its registration sites, so the next track is staged before the
current stream is finalized. This is a better hook, not a worse one:
the monitor is also where end-confirmation timing lives (including a
deferral state and a stall watchdog), so transition lead time is
controllable at exactly one point.

Erratum appended to `../analysis/modules_round2.md` with this push:
in the generic stub's dispatch table (`0x0308C694`), command 10 is a
status query over the codec struct, the body the monitor calls,
and the DMA-playback-start profile is command 8. Phase 2's
command table conflated a per-module variant's body with the generic
numbering.

## 3. Finish lines: metrics, instruments, pass marks

Each axis: the metric, how it is measured offline now (emulation and
static evidence) and on hardware later, and the finish line. Numbers
marked *(baseline)* are stock values established by the RE; a finish
line is only meaningful against them.

### 3.1 Decode fidelity

- Lossy arithmetic precision. Decode the pinned corpus (per
  codec: full-scale sine, quiet fade, dense music) and score
  SNR of (stock decode − reference decode), reference = the best
  host decoder (ffmpeg/libvorbis float, libmad, etc.). This isolates
  decoder arithmetic from codec loss, which is the part firmware
  controls. *Baselines:* Vorbis ≈ 38–43 dB (proven build, §2.1);
  other codecs unmeasured: MP3 is libMad (24-bit internal, expected
  clean), AAC/WMA unknown until the Phase D harness runs.
  **Finish line: ≥ 96 dB for every codec**: 16-bit-transparent
  arithmetic, below CD resolution and ~35 dB clear of the DAC's own
  noise contribution at real listening levels. Stretch: agreement
  with the reference within measurement noise (≥ 110 dB).
- Lossless bit-exactness. FLAC/ALAC/WAV/DSD: decoded PCM must be
  bit-identical (hash equality) to the host reference at every
  supported rate, including 192 kHz FLAC. Any deviation is a bug by
  definition. *Baseline:* unmeasured (harness).
- No hidden resampling. PCM sample-count identity between a
  native-rate file's host decode and the device-path capture at
  44.1/48/88.2/96/176.4/192 kHz. Stock codec open initializes I2S at
  a fixed 48 kHz and the real rate is decoder-internal (Phase 2), so
  whether an SRC hides in the path is an open measurement, not an
  assumption. **Finish line: zero SRC, native rate end to end**;
  the CS43198 accepts every rate natively, so any SRC found is
  removable in principle.
- EQ off = bit-exact. With EQ disabled, output must equal the
  no-EQ decode bit-for-bit (the EQ rows in the clock table prove EQ
  is a separately-clocked stage; bypass must be a true bypass).

### 3.2 Latency

- Gapless transition offset, in samples, measured by
  cross-correlating the rendered transition against the expected
  concatenation of the two reference decodes. **Finish line: 0
  samples** for same-codec/same-rate transitions; **≤ 1 ms** across
  codec or rate changes. *Baselines (stock cost stack, all proven):*
  the whole open pipeline runs after EOF: decoder image re-copy
  (32,888–117,376 bytes, every open, no cache check), the fixed
  `delay_ms(100)` in codec open (`0x03089F16`), and a position-sync
  loop polling at 15 ms for up to 200 iterations. The DAC's 181 ms
  staged init is not in the per-track path (per-session guard,
  Phase 1) and must stay out of it. Lower latency compounds: every
  millisecond cut from open/init is a millisecond less pre-roll the
  transition needs, which is what makes sample-exactness achievable
  on short fades and tightly-sequenced tracks.
- Track-start latency (command → first PCM out). **Finish line:
  < 100 ms cold, < 30 ms same-codec.** The stock fixed costs above
  (100 ms delay + re-copy + sync loop) already exceed both, which is
  the point of measuring them individually in Phase D: each is a
  separate patch decision.
- **Seek latency < 100 ms** to first correct PCM after a seek within
  a file, worst-case format (APE/FLAC-192).
- **Input latency < 20 ms** from key/wheel actuation to action,
  bounded by the input poll structure; stock poll periods to be
  counted in emulation.

### 3.3 Throughput and headroom

- Decode CPU headroom. Cycles per decoded second (emulation
  instruction counts at the decoded clock) for the heaviest streams:
  192 kHz FLAC, DSD128, top-tier OGG. **Finish line: ≤ 70% of the
  decode core at that codec's *tuned* clock** (§3.4), leaving ≥ 30%
  for the transition overlap, the second decode that gapless
  pre-open runs while the current track finishes.
- Sustained read margin. Worst-case stream bitrate is DSD128
  ≈ 11.3 Mbps; **finish line: sustained card read ≥ 4× that**,
  measured on the reference card, so the file service is never the
  transition bottleneck.
- Library scan. **Finish line: ≤ 30 s** full scan of the
  reference corpus (256 GB card, mixed formats), **≤ 5 s**
  incremental. Precedent: nanitecfw took the sibling build from
  148 s → 28 s with walk-hook sort keys; the Neo's library-update
  clock row (row 30) and key builders are already located.
- SRAM headroom. Peak usage of the core-1 data footprint
  (about 251 KiB from the data base in the largest measured module;
  the 128 KiB figure sometimes quoted is only the parameter window
  at its base) under the heaviest stream, measured in emulation by
  watermarking.
  **Finish line: ≥ 16 KiB free at peak.** Open question this
  settles: a sibling firmware (ReChord) budgets ~143 KB for its
  192 kHz FLAC decode window, larger than this window. Either
  stock FLAC's real peak fits (their number is their decoder's, not
  a law) or max-rate FLAC is living closer to the edge than anyone
  has measured. Measure, don't assume (§5).

### 3.4 Power (performance per watt)

- Tuned clock table v1: per-codec solver outputs at or below
  nanitecfw's shipped values for the same solver (B-core 144 MHz
  MP3-class / 240 OGG / 288 FLAC-class; A-core at the 96 MHz floor
  outside bursts), gated on zero underruns across the corpus at
  those clocks. WAV's row drops from 450 MHz to the floor class.
  This is a data-only patch (§2.2), the cheapest large win in the
  whole program.
- Playtime is the on-hardware confirmation (Phase E): hours at
  fixed volume/load, stock table vs tuned table. Emulation can
  predict cycle counts; it cannot measure current.

## 4. What is still unmeasured (honest list)

Every PCM-level number for every codec (needs the Phase D harness);
stock FLAC's SRAM peak; card read throughput on the Neo; stock scan
time on the Neo; input poll periods; anything analog-domain. The
report's baselines are byte-proven where they are stated as proven,
and labelled as inherited or unmeasured where they are not.

## 5. Claims register: "impossible" treated as a hypothesis

| Claim | Source | Status |
|---|---|---|
| "M3U isn't possible on this hardware" | FiiO representative | **Disproven**: two firmwares run M3U on this SoC |
| "Gapless can't be patched into stock firmware" | echo-mini-newfw author, about the Echo Mini stock build | **Open on the Neo**: a different image; the hooks are now identified (§2.3). Settled by building it (Phase C), not by argument |
| "No callable Bluetooth toggle exists" | Our own round-1 verdict | **Disproven**: by our own Phase 2 (module 81); the model case for re-testing our own negatives |
| "Stock Vorbis is ~7 effective bits" | echo-mini-opus author | **Confirmed**: byte-proven build identity (§2.1); the claim survived testing, which is also a result |
| "A rate change forces a DAC re-init (and a gap)" | Implicit in stock design readings | **Disproven as stated**: DAC init is per-session (Phase 1); RECHO does gapless across rate changes on this SoC |
| "The decoder must be re-copied on every open" | Stock behaviour, easily mistaken for a constraint | **Not a constraint**: no cache check exists; adding one is a patch |
| "Rockbox-class firmware is blocked by ~960 KiB SRAM" | Our Phase 2 assessment, from a datasheet figure | **Unmeasured**: §3.3's peak-usage test comes first; and even a real wall binds Rockbox, not the purpose-built path |

## 6. Implementation plan: next steps, in order

Phases are gated by the metrics in §3, not by effort estimates.
Offline phases produce patch artifacts + emulation evidence; nothing
is flashed until Phase E, and then only via the dual-slot plan
(stock preserved in slot 1).

Phase A: Patch framework + data-only patches (offline).
Adopt nanitecfw's authoring layer (patch grammar, hooks manifest,
SHA gate, date+1 build discipline, MIT). First artifacts: clock
table v1 (§3.4 targets), the DAC error-counter fix (the Phase 1
finding: the byte at `0x0300411E` permanently disables DAC control
after two errors), natural-sort keys for the library. *Gate:*
patcher round-trip byte-exactness on DP3_V137; every patch
reversible to the stock SHA.

Phase B: Vorbis full-precision swap (offline, image-rebuild
class). Rebuild module 75 from full-accuracy Tremor, following
echo-mini-opus's validated Echo procedure; the +30.6 KB of tables
means this is an image rebuild (NeoPod's `make_image.py` route), not
an in-place byte patch. *Gate:* the rebuilt module passes the §6
protocol in the evidence doc once Phase D exists; until then it
ships as a built artifact with static verification only, clearly
labelled as such.

Phase C: Gapless + M3U (offline construction). Gapless per the
revised design: hooks at the monitor finalize blocks (§2.3), shadow
file-info struct, same-codec fast path with the loader cache check
that stock lacks, fixed waits cut on the fast branch only. M3U per
`README.md` (ported parser/resolver + the (cluster, index) bridge).
*Gate:* transition offset and start/seek latencies measured in
emulation against §3.2 lines on the pinned corpus.

Phase D: Core-1 emulation harness (offline; can start in
parallel with B). Stand up the message-unit + HifiFile server per
the specification in `../analysis/vorbis_precision_test.md` §6. The
main unknown is the decoder command word's semantics (values 0–14,
Phase 2). This harness is the validation backbone: it unlocks every
PCM-level metric in §3 for every codec, not just Vorbis.

Phase E: Hardware (when a unit is in hand). Rockusb read-back
test (slot geometry, the standing first task from the dual-slot
plan), dual-slot flash of Phase A artifacts, then re-baseline: I2S
logic-analyzer captures for the rate audit (§3.1) and the analog
transition offset (§3.2), current measurement for the clock table
(§3.4), underrun corpus at tuned clocks. Every emulation estimate in
this document gets a measured counterpart or a correction.

Order note: A is first because it is all data-only and reversible;
D is the infrastructure that unblocks the most work and should not wait for C;
B's validation depends on D; E validates everything and is the only
phase that touches a device.

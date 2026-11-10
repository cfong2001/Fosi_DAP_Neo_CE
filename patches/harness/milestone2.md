# Phase D, milestone 2: FLAC PCM capture + gapless R1 transition trace

Module 76 (stock FLAC decoder) in the core-1 emulation harness. All work
offline; the stock image was not modified (SHA-256 verified before/after:
fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef).
Code: `harness2.py` (classes H2/H3, extends milestone-1 `harness.py`,
which is untouched) and `run_m2.py` (the driver that produced every log
cited here).

## Job 1: PCM capture (solved)

Milestone 1's "scan/discard mode" was not a decoder mode. It was two
harness defects, and behind them one hardware-offload design that keeps
real PCM off the CPU for the common subframe type. All three findings are
execution-proven.

### Finding 1: the milestone-1 file layer starved the decoder (defect in the harness)

Milestone 1's `_serve_rpc` delivered HifiFile Read replies with param =
0. In the decoder's runtime file layer, the value a slot producer stores
as the slot's valid-byte count is the Read stub's return value, and stub
0x350 returns the word at 0x01022298, the MU reply param. Every
refilled slot therefore registered 0 valid bytes, the buffered reader
(fn 0x237C) returned EOF on a full file, and the frame loop scanned
headers over an input buffer that stayed zero-filled. That is the whole
of milestone 1's "channel buffers are never written."

Server-side proof (module 33, the real file server): its Read case at
0x030895DA (module_33_code_0308837c.bin + 0x125E) sends the 0x6C reply
with param = the FS read return value (bytes read), and writes the
folder+0x20 word into blk+4. Its Seek case likewise writes folder+0x20
into blk+0 after the FS call (the handle's FS-side position).
`H2._serve_rpc` replicates exactly that (Seek blk+0 := post-seek host
position, Read blk+4 := post-read host position, Read reply param :=
bytes read). With the fix, the open runs the full FLAC_FileGetSeekInfo
pass and reports test44.flac's total as 88,200 samples' neighbour (see
residuals), and real frames decode.

### Finding 2: the decoder parks on unmodelled DMA completion (candidate (b), decoder-local form)

With data flowing, the first frame's subframes decode, then the decoder
parks forever at PC 0x28DE (the `wfi` helper 0x28DC) inside fn 0x524A,
the audio-output function (sole caller site 0x432C, inside
decode_subframe_lpc). Fn 0x524A programs two decoder-local DMA transfers
via fn 0xD5E (LLI builder over the table at 0x010224BC, config registers
in the 0x0106xxxx block) and WFI-waits for [0x010220E4+4] != 0; its
sibling fn 0x51F4 waits on [0x010220E4+0]. The setters are the
DMA-complete interrupt handlers fn 0x518A (sets +4) and fn 0x5174
(sets +0), dispatched by the interrupt walker fn 0x5198 (status at
[0x60000000+0x2E8], handler table 0x010225DC). The harness models no
interrupt source, so the wait never completed. This, not a missing
message, was milestone 1's residual stall. After the wait, the caller
also spins on fn 0x50A8(0, 0x8000) == 0x8000, a DMA channel-status
read at [0x01060008 − 0x3C·ch] (bit 15 = transfer complete; bit 0 =
FIFO-ready, also polled by the software FIFO-feed loop at 0x50BA).

Model (class H3): zero-latency DMA. At the two `wfi` sites the matching
completion flag is set; DMA channel-status registers read back
complete+ready whenever fn 0x50A8 reads them or fn 0xD5E programs a
transfer. The model is disclosed in the code and in the trace (`DMA`
lines).

Candidate verdicts from milestone 1 §11:

- **(a) ch3 FreqChange completion: DISPROVEN.** The ch3 handler path
  (0x884 → fn 0xB16) only clears the byte at 0x01022130. That flag stayed
  0 in every run, including all successful decodes; nothing in the open
  or decode path waits on it.
- **(b) DMA-start arming: CONFIRMED, in decoder-local form.** The
  missing machinery was the decoder's own audio DMA completion, not a
  system-side message: the system-side stub cmd 8 has no decoder-side
  counterpart in the executed path. Once completion is modelled, frames
  complete end-to-end.
- **(c) engine enable selector: DISPROVEN as a separate blocker.** The
  existing command-word-2 (DECODE) path drives everything once (b) is
  modelled; no additional selector was needed or found.

### Finding 3: LPC reconstruction is a hardware offload; the CPU never holds PCM for LPC subframes

`decode_subframe_lpc` (fn 0x423E) is rewritten relative to stock libFLAC.
For predictor order ≥ 3 it does not run `FLAC__lpc_restore_signal`
on the CPU. It decodes warm-up + residual into the channel plane
(residual via fn 0x3FDC), then:

- uploads the coefficient array to the audio block at 0x0106B000
  (memcpy fn 0x5090, call site 0x4312; coefficients are stored on the
  stack in reverse stream order and uploaded in that order),
- programs order and shift via fn 0x2AC4 (call site 0x4308),
- hands the residual plane to the DMA output fn 0x524A and waits for the
  hardware (Finding 2's waits).

The RKnano audio block reconstructs the signal while it plays it. (Later identified: the block is HIFIACC, the RKNanoD's fixed-point LPC/FFT accelerator, TRM chapter 26; echo-mini-newfw's `docs/HIFIACC.md` maps its registers at `0x01060000`. See `analysis/rknanod_trm.md`.) A
write census over both channel planes for one frame shows exactly
9,216 word writes: warm-up (8, PC 0x427E) + residual (4,600, PC 0x40FE)
on the LPC channel, constant-fill (4,608, PC 0x4440) on the other, and
no reconstruction writes anywhere; a full data-window scan after a
decode finds the first 8 samples (the warm-up) and no other
reference-matching samples. Order 1–2 LPC takes a descriptor-based path
via fn 0x3034 (call site 0x4366); CONSTANT (0x436C case 0), VERBATIM
(case 1) and FIXED (fn 0x4116) subframes are completed on the CPU, so
their planes are final.

The harness therefore reconstructs LPC frames in Python (standard FLAC
LPC restore, coefficients reversed back to stream order, arithmetic
shift, int32 wrap) at the fn 0x2E9A interleave point, where both planes
are final, and applies the frame's channel-assignment conversion
(left+side for both test files) that fn 0x2E9A performs on hardware.

### Numbers (ffmpeg s16le reference, `run_log_m2_pcm.txt`, `run_log_m2_pcm48.txt`)

| File | Result |
|---|---|
| test48.flac (48 kHz, 1.00 s, 48,000 samples/ch) | **48,000/48,000 samples, both channels, bit-exact**, the complete file, including the final 1,920-sample partial frame |
| test44.flac (44.1 kHz, 2.00 s, 88,200 samples/ch) | L **87,552/87,552 bit-exact**; R exact for frames 0–17 (82,944/87,552); 19 of 20 frames produced |

Cross-checks: the decoder's per-frame byte consumption matches ffprobe
(frame 0: 1,287 bytes both ways); every frame's subframe types were
traced (L = LPC order 8, side = CONSTANT in all 20 frames of test44).

### Job 1 residuals (honest)

- **test44 frame 18 side channel reads back as constant 1, not 0.** L is
  bit-exact; the side subframe is CONSTANT in the file and decodes as 0
  in frames 0–17, but as 1 in the last full frame, making that frame's R
  uniformly 1 LSB low. Localised to the constant-value bit read in the
  final full frame; the mechanism (end-of-stream refill boundary in the
  harness file layer vs a decoder edge) is not pinned down. test48
  (same subframe structure) shows no such error.
- **test44's final 648-sample frame is never decoded** by the stock
  flow: the decoder reports EOS after 87,552 samples. test48's final
  partial frame (1,920 samples) *does* decode, so this is file-specific,
  not a hard decoder limit. Unexplained.
- **The decoder's own total_samples is STREAMINFO − 128 in both files**
  (88,072 vs 88,200; 47,872 vs 48,000), measured from its seek-info
  pass. Consistent, unexplained, and it does not cap decoding (test48
  decoded the full 48,000).
- Polling the position command past the decoder's EOS notify makes
  the stock engine run one further spurious decode (decoded_samples
  overshoots the file length). The driver stops at the EOS notify
  (ch1 cmd 6); the behaviour is the decoder's, recorded here so nobody
  mistakes it for a harness artifact.

## Job 2: gapless R1 (pass on the decoder side)

Traces: `run_log_m2_transition.txt` (load-skipped), `run_log_m2_stockB.txt`
(stock baseline), `run_log_m2_stop_replay.txt` (R2), `run_log_m2_diff.txt`
(R3). File A = test44.flac (44.1 kHz), file B = test48.flac (48 kHz,
different size/total), a harder transition than same-rate.

### (a) Stock baseline

Fresh boot → 0x65 → 0x66 → ch1 open → B decodes to EOS: 48,000 samples,
bit-exact (the Job 1 test48 run is the same flow).

### (b) Load-skipped transition: the R1 clearing observation

A decoded to EOS on the resident decoder (87,552 samples, EOS notify
sent). Then, without reloading the module image, re-running the reset
trampoline, or rewriting the parameter page, the driver delivered B's
0x65 file-info push (transition log lines 1029–1036):

- decoder accepted the exchange and issued its 0x66 open-accepted;
- ch1 open produced B's stream-info report (total_samples updated to
  B's 47,872; file_size cell = 21,934 = B's size);
- B decoded to EOS: **48,000/48,000 samples, both channels, bit-exact
  vs ffmpeg, byte-identical outcome to the fresh-boot baseline.**

**R1 verdict: the resident FLAC decoder accepts the 0x65 open exchange
after end-of-stream and produces correct PCM for the new file with the
load skipped.** This is the decoder-side half of gapless_patch.md §7
R1's clearing observation. Scope limit, stated plainly: the harness
executes the decoder core and models the MU/HifiFile layer; the
system-side legs (module 33's 0x03088824 exchange poll, the task-5
state poll, the R5 bus release) do not execute here, so a system-side
stall of the kind §7 names ("the exchange poll spins to its cap") is
not excluded by this trace. It is excluded only for the decoder's part
of the exchange, which is the part that was unproven.

### (c) Stop → replay (R2)

Mid-file (3 frames decoded), the stop-class command (ch1 cmd 0x0D →
command word 6 → selector 15 CLOSE) was delivered; the same file was
then re-opened on the resident decoder with the 0x65 exchange. Result:
the replay decoded the file and its PCM is **byte-identical to the
fresh-boot baseline**, including the deterministic frame-18 side quirk.
The decoder-side stop does not park the engine in a way that needs a
reload. (The system stop path in §7 R2, 0x0308A94C clearing the DAC
guard, is system-side and outside this harness, same scope limit as
R1.)

### (d) Parameter page and state diff (R3)

Snapshots at post-open of file B, load-skipped instance vs fresh
stock-reload instance (`run_log_m2_diff.txt`):

| Field | Load-skipped | Stock reload | Judgement |
|---|---|---|---|
| Parameter page (144 B @ 0x01020000) | none | none | **Identical.** Also identical within the skipped instance across boot → A-EOS → B-open: the decoder never writes its parameter page during a session, and the open sequence doesn't either. No per-track field was observed to change across two tracks that differ in rate, size and total. R3's feared direction (stale per-track values) has no instance in the executed paths. The system-side source page at 0x030064E0 is not observable from the core-1 harness. |
| fmt_word / file_size / total_samples / decoded_samples | 6 / 21,934 / 47,872 / 0 | same | The new open fully re-registers the new file; nothing stale. |
| FLAC state fields (+0x30 blocksize, +0x34 bps, +0x40) | 0 / 0 / 0 | 0 / 0 / 0 | Reset by B's open in both paths. |
| ctrl block, FS struct head, fill table, event bitmap, freq flag, out_idx, out_cell | none | none | Equal. |
| DMA completion flags @ 0x010220E4 | +4 = 1 | +4 = 0 | Left set in the skipped instance; it is the previous track's DMA-complete flag (set by handler fn 0x518A). In the emulator it persists because the completion model sets it and no consumer clears it; on hardware the same flag is set by the previous track's last transfer as well. B's decode was bit-exact with it set. Judged benign; it is also exactly the state a real warm transition would carry. |
| Stream-state word @ 0x010222D4 (+0xC) | 1 | 0 | One flag word left set from file A's stream. Cursor/remaining fields beside it were correctly re-initialised by B's open (INBUF / 0x4000 in both). No behavioural effect observed (B bit-exact); flagged here as the one unexplained stale word for the record. |
| Data window overall | 27 of 64 4-KiB regions differ (29,012 B) | none | The differing regions are content residue, not control state: PCM double buffers (hold A's last frame vs B's probe frame), FLAC channel planes and bitreader workspace (residual data), FS data buffers and stacks. Every curated control field above was compared individually. |

**R3 verdict:** the 144-byte page needs no refresh for the fields the
decoder actually reads (the +0x20/+0x24 Hz dividers persist loaded,
safe by omission, as §7 predicted, and no per-track page field
appeared). Two one-word/one-flag deltas exist outside the page (DMA
completion flag, stream-state +0xC); both are recorded above with their
evidence, and neither affected the traced transitions.

## Files

- `harness2.py`: H2 (fixed HifiFile server semantics, probes, direct
  codec calls) and H3 (DMA-completion model, LPC-offload model, PCM
  assembly, snapshots, media switching). Milestone-1 `harness.py` is
  unmodified; `command_semantics.md` gained a marked milestone-2
  addendum correcting §11.
- `run_m2.py`: end-to-end driver for both jobs.
- Logs: `run_log_m2_pcm.txt` (test44), `run_log_m2_pcm48.txt` (test48),
  `run_log_m2_transition.txt`, `run_log_m2_stockB.txt`,
  `run_log_m2_stop_replay.txt`, `run_log_m2_diff.txt`. Earlier
  exploration logs: `run_log_m2a.txt`, `run_log_m2b.txt`.
- Captures: `pcm44_final.bin`, `pcm48_final.bin` (assembled s16le PCM).

## What remains open

- The test44 tail quirks (frame-18 side constant, dropped 648-sample
  frame, −128 total) are characterised but not mechanised; they are
  file-specific and do not appear in test48. A third test file with a
  different encoder/blocking would narrow whether they track the file
  or the harness's end-of-stream refill.
- LPC orders 1–2 (fn 0x3034 path) and mid+side / side+right channel
  assignments were not exercised. No test file produced them. The LPC
  model covers order ≥ 3 (the path both test files use throughout).
- System-side R1/R5 observations (module 33's exchange poll behaviour
  on a skipped load, bus release) still require executing module 0/33
  code or hardware, Phase E territory, unchanged by this milestone.

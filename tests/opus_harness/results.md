# Opus transplant harness validation

This document records the offline harness validation of the Opus transplant candidate for decoder module 72, run against the validation plan in `work/opus_transplant/route.md`. The candidate under test is `work/opus_transplant/module72_opus.bin`, 117,376 bytes, SHA-256 `abc98c1163985de677dc0d9da200e8c1986d769b57fa594e2e066b6ed4707a5d`, built by `transplant.py` from the donor plug-in diff `HIFIEC52.ecpatch`.

**Headline result: the shipped candidate FAILS.** It cannot open any file. The failure is in the candidate's construction, not in the splice design: `transplant.py` zeroes the freed regions of the stock module and then writes only the bytes present in the sparse ECPATCH diff, so every byte where the plug-in coincides with the Echo stock library is replaced by 0x00. 630 bytes are corrupted this way (600 in code, 30 in data). A control build that applies the same diff without the zeroing step passes every step of the plan, so the route itself is sound and the fix is in the build tool.

## Verdicts

| Step | Shipped candidate | Control build (corrected construction) |
| --- | --- | --- |
| 1. Stock module 72 control | **PASS** (harness control, candidate not involved) | n/a |
| 2. Opus decode matrix | **FAIL** (faults on open, any file) | **PASS** |
| 3. Seek | Blocked by step 2 | **PASS** |
| 4. Efficiency count | Blocked by step 2 | Measured: Opus 34.1M vs WMA 17.5M instructions per audio second, ratio 1.95 |
| 5. Gapless miniature | Blocked by step 2 | **PASS** |
| 6. Canaries | Blocked by step 2 | **PASS** |

## Rig and method

The rig is `harness72.py` in this directory, a module 72 parameterisation of the Phase D harness (`work/harness/`). It boots a core-1 decoder module from reset under Unicorn, models the MU at 0x40110000 with block hooks on the module's send functions, serves HifiFile RPC on channel 2 synchronously using the module 33 server contract (Read replies carry param equal to bytes read; Seek writes the post-seek position at block+0; Read writes the post-read position at block+4), and drives the stock open exchange: the 0x65 info push on channel 2, the channel 2 open notification, then channel 1 commands for open, decode polls, seek, and close. PCM is captured from the info block after the open (the runtime primes the first buffer during open) and after every decode reply. Instruction counting uses block hooks with a cached Capstone instruction count per block, the method used for the Vorbis decode cost work. Counts were cross-checked with a second independent block hook; the two agreed within 0.3 percent on a 3 second file (98,332,332 vs 98,605,265 instructions).

One modelling note. The module's runtime prints through a console port at 0x400B0000 and waits for the transmitter-ready bit at +0x7C before each write. The harness seeds that status word ready, the same category of hardware modelling as the MU server. Without it, any code path that prints appears to hang in emulation; on hardware the peripheral raises the bit. The candidate's failure below was diagnosed with the console modelled, and the fault dump quoted there is the module's own output through that port.

Test media were generated with ffmpeg (libopus and wmav2) from synthetic stereo sources; references are ffmpeg decodes of the same files (libopus on the input side for Opus, native wmav2 for WMA). PCM comparison (`compare.py`) finds the signed integer frame lag by normalised cross-correlation, then reports per-sample error statistics at that lag. No offset correction is applied anywhere: the plug-in discards the encoder pre-skip internally during open, and ffmpeg trims it as well, so a correct decode aligns at lag 0 with an exact frame count.

## Step 1: stock module 72 control

**PASS.** Stock module 72 booted, completed the handshake (READY in 2 slices), and decoded `wma_small.wma` (3 s, wmav2, 96 kbps) through the stock exchange: open reported 48000 Hz, 2 channels, 96000 bitrate, length 3000 ms; 71 decode polls reached end of stream; close replied. Against the ffmpeg reference, the captured PCM aligns at lag -4096 frames. The two leading blocks are accounted for: the first is the open-primed buffer slot captured before the decoder had filled it (2048 zero frames), and the second is the WMA decoder's priming frame, which ffmpeg's decoder trims. Over the remaining 141,312 compared frames the maximum absolute error is 1 LSB and the SNR is 80.0 dB, so the harness drives the stock module correctly and its PCM path is trustworthy.

Side observation: the stock module fed an Opus file fails the open cleanly (channel 1 command 2, no hang), which is the expected behaviour for an unsupported format word.

## Step 2: the shipped candidate

**FAIL.** The candidate boots and completes the handshake. The 0x65 push, the buffer setup (two 512 byte reads), and the channel 2 open notification all happen exactly as with the stock module. The open then never returns. With the console modelled, the module's runtime fault handler prints its dump and parks:

```
PC:00002E77
LR:0000009B
MSP:01022024
PSP:00000000
```

### Where it breaks

A differential block trace of the open path (stock vs candidate, same session) is identical until block index 5, where the stock codec dispatcher branches to its OPEN case at 0x2F9C and the candidate branches to a shared epilogue at 0x2F68. Single-stepping the candidate's dispatcher at 0x2EC4 with subfunction 8 shows why: the function's first bytes are zeros, execution slides through them and through the switch table as if they were instructions, and the call frame is short by exactly the dispatcher's register push, so the epilogue pops the data-image vector table (0x01022000, 0x15B7, then 0x9B placeholders) into the registers and returns through 0x9B, landing in the fault dump handler at 0x9A.

Two corrupted instructions are proven byte for byte, each by a surviving byte:

| Site | Candidate bytes | Correct bytes | Evidence |
| --- | --- | --- | --- |
| Dispatcher prologue, 0x2EC4 | `00 00 00 4F` | `2D E9 F0 4F` (`push.w {r4-r8, sb, sl, fp, lr}`) | The shared epilogue at 0x2F68 pops exactly that register set; only the last byte differs from the Echo stock module's prologue, so only it is in the diff. |
| Dispatcher switch, 0x2ECE | `00 00 10 00` | `DF E8 10 F0` (`tbh [pc, r0, lsl #1]`) | The table at 0x2ED2 holds halfword offsets (18 entries); stock module 72's analogue is `tbb` (`DF E8 00 F0`), differing only in byte 2, which is the byte the candidate keeps. |

A third site is proven by behaviour. Restoring just those two instructions in a scratch copy makes the dispatcher route subfunction 8 correctly; the open then runs into `open_stream`, passes its file-size check, and fails cleanly (channel 1 command 2) in the helper at 0x37A8, the plug-in's seek-to-start step. As present in the candidate, that function loads the FILE_OPS seek pointer but contains no call instruction at all: bytes `98 00` sit at 0x37B8 where the compiled function needs `blx r3` (`98 47`), and it returns failure whenever the seek pointer is installed. The corruption is therefore not confined to one site.

### Root cause

`transplant.py` builds the candidate by zeroing the freed code and data regions of the Neo stock module, then writing the bytes listed in `HIFIEC52.ecpatch`. An ECPATCH is a sparse diff against the Echo stock module: any byte where the plug-in's output equals the Echo stock byte at the same offset is absent from the diff. Those bytes are exactly the ones the zeroing destroys. The donor's own tool (`rknanofw.py patch-opus`) does not work this way: it wipes the freed regions and writes the complete plug-in ELF sections, so coincident bytes survive because they come from the ELF, not from a diff.

Byte comparison against the corrected construction (below) sizes the damage: the candidate differs from it in 630 bytes, 600 in the code region and 30 in the data region, and every one of the 630 bytes is 0x00 in the candidate. The corruption is densest where compiled plug-in code shares encodings with the stock library (push and pop patterns, table branches, calls, literal pool words), which is why the codec dies in its first instructions.

### Steps 3 to 6 on the shipped candidate

Not runnable. The codec faults before any file is opened, so seek, efficiency, gapless, and canary measurements on the candidate itself would measure nothing. They were run on the control build instead, as follows.

## The control build

To separate the splice design from the construction defect, a control build was made in this directory (`module72_opus_onstock.bin`, SHA-256 `6a7d50d2647c6623181e3cbbc16a13d2bd9a8724559d62c84f25b83ae8cbb07d`): the stock module 72 bytes with the same HIFIEC52 diff applied and no zeroing step. This works as a reconstruction because the Neo and Echo stock modules are the same SDK build with byte-identical kept regions, so a byte the plug-in shares with Echo stock is, at the same offset, the byte already present in Neo stock. The control build is a diagnostic, not a deliverable; the build fix is described at the end.

## Step 2 rerun: decode matrix on the control build

**PASS** on all five files. Every file opens through the stock exchange, decodes to end of stream, and closes. Frame counts match the ffmpeg references exactly and the alignment lag is 0 in every case, which confirms the pre-skip accounting on both sides. The output is not bit-identical to ffmpeg: the plug-in's libopus is fixed-point and ffmpeg decodes in floating point, so samples differ by a few LSB (maximum 18, RMS about 2, SNR 68 to 72 dB). That is the expected fixed-point versus float difference, not a decoding error.

| File | Shape | Frames (harness vs reference) | Lag | SNR dB | Max abs err |
| --- | --- | --- | --- | --- | --- |
| opus_b.opus | 48 kHz stereo, 96 kbps nominal, 3 s | 144,000 vs 144,000 | 0 | 71.6 | 13 |
| opus48.opus | 48 kHz stereo, 128 kbps nominal, 10 s | 480,000 vs 480,000 | 0 | 70.9 | 15 |
| opus44.opus | 44.1 kHz source, 128 kbps nominal, 5 s | 240,000 vs 240,000 | 0 | 71.2 | 13 |
| opus_tags.opus | 48 kHz stereo, 56,000 byte OpusTags comment, 5 s | 240,000 vs 240,000 | 0 | 71.0 | 18 |
| opus_worst.opus | 48 kHz stereo, 2.5 ms frames, 256 kbps nominal, 4 s | 192,000 vs 192,000 | 0 | 68.3 | 17 |

Notes on individual files. The 44.1 kHz file is decoded at 48 kHz like every Opus stream (240,000 frames for 5 s), matching ffmpeg's libopus output frame for frame. The large OpusTags packet (the file carries a comment field of 56,000 bytes, taking the tags packet past 50 KB) opens and decodes without disturbing the audio. The 2.5 ms frame file, the plan's worst case, decodes with the lowest but still clean SNR of the set. Bitrates in the open replies (121,000 to 312,000) are the plug-in's file-size based estimates, consistently above the encoder's nominal settings because they include Ogg overhead; the durations and sample counts are exact.

## Step 3: seek on the control build

**PASS.** On the 90 s file `opus_long.opus`, after roughly 3 decode polls, a seek to 60,000 ms through the stock exchange (channel 1 command 0x0B) replied with parameter 0 (success). Decoding resumed at the seek point: the captured post-seek PCM matches the ffmpeg reference starting at frame 2,880,000 at lag 0, with maximum absolute error 10 and SNR 73.2 dB over 240,648 compared frames. The runtime's own position readout after about 5 further seconds of decoding was 65,013 ms. The seek is sample-exact against the reference, with no offset compensation.

One finding from this file: it is a mono stream, and the plug-in decodes it as dual mono, reporting 2 channels with identical left and right samples. Harmless on its face, but the runtime and everything downstream will treat mono Opus files as stereo.

## Step 4: efficiency

Measured on the control build and the stock module over the identical session path (open, decode to end of stream, close; counting enabled after boot), decoding the same 10 s stereo excerpt at a comparable bitrate (128 kbps nominal each):

| Decoder | File | Instructions | Blocks | Instructions per audio second |
| --- | --- | --- | --- | --- |
| Opus (control build) | opus48.opus | 341,072,921 | 49,834,382 | 34,107,292 |
| WMA (stock module 72) | wma48.wma | 174,958,503 | 19,379,939 | 17,495,850 |

Ratio: **1.95**. On instruction count, the transplanted Opus decoder costs about twice the stock WMA decoder per second of audio. Both counts include the shared runtime and buffered-reader path, which favours neither side. Two cautions before this is read as a hardware verdict: instruction count is not cycle count (multi-cycle instructions and memory waits are invisible to this method, and the WMA library's dual-MAC DSP instructions do more work per counted instruction), and an emulator cannot measure cache or bus effects. What the numbers do settle is the direction of the comparison on this rig: the efficiency claim behind the transplant, that Opus decode is the cheaper decode and buys headroom, is not supported. Opus is the more expensive decoder here by roughly a factor of two in instructions, and any gapless headroom argument has to be made on cycle counts from hardware.

## Step 5: gapless miniature on the control build

**PASS.** With the decoder resident (no reload, no reset), `opus_b.opus` was decoded to end of stream, then `opus44.opus` was opened through the same stock exchange (0x65 push and open command) on the same module instance. The second file decoded from its first frame: 240,000 frames, lag 0 against its reference, SNR 71.2 dB, maximum absolute error 13. The first file's output was likewise exact (144,000 frames, lag 0). This is the R1 miniature from the plan: the resident decoder takes a second Opus stream after EOS without a reload. It says nothing about the armed gapless fast path's sample trimming, which is a system-side feature and out of scope here.

## Step 6: canaries on the control build

**PASS**, all three.

- **Stack watermark.** The window 0x01020090 to 0x01022000 (8,048 bytes, the parameter page end to the stack top) was filled with 0x5A before boot. After an open, full decode, and close of `opus_b.opus`, 3,748 bytes at the top of the window had been overwritten, so the deepest stack reach stayed 4,300 bytes above the bottom of the window.
- **Parameter page.** The 144 bytes at 0x01020000 were byte-identical after the session to their state after boot. The plug-in does not write its parameter page.
- **Runtime event-flag region.** The region 0x0103CB18 to 0x0103CB54, which the donor's HIFIEC42 build once corrupted by an over-wide BSS clear, read as all zeros after boot and was still all zeros after the decode. This build's BSS clear starts at 0x0103CB58 (the plug-in's .bss), clear of the region, and no plug-in data lands there. The HIFIEC42 regression is absent.

## Negative test

A Vorbis file (`.ogg`, libvorbis) fed to the control build fails the open cleanly: the runtime prints its open error and sends channel 1 command 2, with no hang and no fault. Rejecting non-Opus content in the renamed slot is the intended behaviour, since the slot's extension rename means only Opus files should ever reach it.

## What has to change in the build

1. `transplant.py` must not zero the freed regions before applying the ECPATCH diff. Two correct constructions exist: apply the diff onto the stock module bytes (what the control build does; valid while the Neo and Echo stock libraries are the same build, which the route already establishes), or follow the donor's method and write the plug-in ELF sections into the wiped regions. The first is a small change to the existing tool; the second matches upstream exactly but needs the built ELF, which is not in the tree.
2. The candidate hash pinned in the route (`abc98c11...`) must not ship, and the transplant's verify check should pin whatever hash the corrected construction produces.
3. With those done, the route's gating recommendation is met by the control build's results above: harness steps 2 and 3 pass, so an opt-in `opus72` built the corrected way has its harness evidence. Nothing in this validation speaks to on-hardware behaviour; there is still no unit to flash.

## Files and reproducibility

- `harness72.py`: the module 72 rig (boot, exchange, PCM capture, counting, canaries).
- `gen_tests.py`: media and reference generation.
- `compare.py`: lag search and error statistics.
- `run_validation.py`: the staged driver (A candidate, B stock control, C control build, D efficiency); `validation_results.json` holds the machine-readable results.
- `logs/`: per-run traces.
- `module72_opus_onstock.bin`: the control build. `module72_opus_repaired.bin`: the scratch copy with the two dispatcher instructions restored, used for the third-site evidence.

Stock image SHA-256, re-verified at the end of this work: `fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef` (DP3_V137.img, unchanged). Candidate SHA-256 as tested: `abc98c1163985de677dc0d9da200e8c1986d769b57fa594e2e066b6ed4707a5d`.

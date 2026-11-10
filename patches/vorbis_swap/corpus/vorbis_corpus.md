# Vorbis finish-line measurement: transplanted module 75 vs the ≥ 96 dB line

**Verdict: the transplant does not meet the ≥ 96 dB finish line as the
line is specified, and the shortfall is entirely the 16-bit output
interface, not decoder arithmetic.** Delivered SNR of the transplanted
module 75 against the ffmpeg floating-point reference, measured on a
pinned 40-file corpus under the Unicorn harness, is **79.1 to 91.4 dB**
(median 81.2 dB) on every file, at every quality, at both sample rates.
Decomposition shows the delivered error is, to within 0.03 dB on all 40
files, exactly the error of the module's own float→s16 output
conversion, which **floors** instead of rounding to nearest and so
costs a fixed 6.02 dB against the round-to-nearest s16 ceiling (itself
only 85.1 to 97.4 dB for these signal levels). The decoder arithmetic
underneath that conversion agrees with the float reference to a
maximum deviation of 1 LSB after the conversion is modelled, matches
the converted reference exactly on 96.4–98.8 % of samples, and carries
an estimated arithmetic-only SNR of **102 to 123 dB (median ≈ 107
dB)**: the arithmetic clears the 96 dB line with margin. No
16-bit-output decoder can pass the line as literally written on
typical-level content, because the s16 quantization ceiling itself
sits below 96 dB unless the signal RMS is within a few dB of full
scale. Stock module 75, same corpus: 38.1 to 42.1 dB, and it fails to
decode two corpus files at all (§5). The transplant's improvement over
stock is +37 to +50 dB (median +42 dB) per file.

All work offline against `DP3_V137.img` (SHA-256
`fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`,
verified before and after). Nothing pushed. Artifacts in
`work/vorbis_corpus/`: `gen_corpus.py`, `run_emu.py`, `measure.py`,
`floor_analysis.py`, `decode_cost.py`, `manifest.json`,
`results.json` / `results.csv`, `floor_results.json`, `emu_runs.json`.

---

## 1. What was asked, and what the line actually measures

`stage3/research/performance_maximization.md` §3.1 sets the decode
fidelity finish line: decode the pinned corpus and score SNR of the
device-path decode against the best host reference (ffmpeg/libvorbis
float), which "isolates decoder arithmetic from codec loss".
**Finish line: ≥ 96 dB**, "16-bit-transparent arithmetic". The prior
single-file datum (PR #4) was 85.5 dB for the transplant on one
generated q5 file, against stock's 45.1 dB, and it was left open
whether a pinned corpus would reach the line.

That framing contains a trap this run was designed to expose: the
module's delivered output is 16-bit PCM (the module self-reports
GETBPS = 16; GETBUFFER returns frames × 4 bytes = 2 channels × 16
bit; there is no wider format anywhere in the delivered path). An
SNR against a *float* reference therefore always includes the output
quantization. Whether a sub-96 result means "decoder math is
imprecise" or "the interface is 16-bit" is exactly the question, and
§4 answers it with measurements, not by assertion.

## 2. Protocol as run

**Corpus** (`gen_corpus.py`, deterministic). Four synthesized stereo
sources, 6.0 s each, peak-normalised to 0.92 FS, 3 ms / 30 ms edge
fades, generated at each sample rate:

- `sweep`: exponential sine sweeps, 20 Hz → 0.46·fs (L) and
  30 Hz → 0.40·fs (R). RMS ≈ −3.7 dBFS.
- `tones`: 15 fixed sinusoids, 50 Hz–9,960 Hz, golden-angle phases,
  R channel detuned ×1.003. RMS ≈ −12.9 dBFS.
- `pink`: pink noise, FFT-shaped, numpy PCG64 seed 20261031+100
  (independent L/R streams). RMS ≈ −14.9 dBFS.
- `music`: music-like composite (additive decaying plucks on a
  C–G–Am–F progression at 120 BPM, bass, detuned pad, seeded
  noise-burst percussion; seed 20261031+200). RMS ≈ −15.8 dBFS.

Each source encoded with libvorbis 1.3.7 (ffmpeg 8.1.2 `-c:a
libvorbis -q:a`) at q0, q3, q5, q7, q9, at 44.1 kHz and 48 kHz:
**40 files**. Full manifest with per-file SHA-256 in `manifest.json`
and Appendix B.

**Decoders.** (i) Transplanted module 75 (`module75_patched_code.bin`
/ `_data.bin`; the combined `module75_patched.bin` hashes to the
DEPENDENCY.md pin `42c42796…`) and (iii) stock module 75 (segment
hashes match `vorbis_test.md` §3: code `4ec93d97…`, data
`32db67e0…`), both under `work/patches/vorbis_swap/emu75.py` with the
runtime's own file layer (80 runs, 78 clean; §5 for the two
exceptions). (ii) Reference: ffmpeg float decode (`-f f32le`) of the
same file. The encoder floor, SNR of the float decode against the
lossless source, was also recorded per file (6.9 to 41.2 dB across the
corpus): it is large, as expected for a lossy codec, and identical for
every decoder of the same file, which is why all scoring is
decoder-against-decoder.

**Alignment.** Per file and decoder, measured, not assumed:
full-signal FFT cross-correlation on the mixdown, lag search
±4,096 samples, top candidate lags disambiguated by measured SNR.
Result: transplant lag **0 on 40/40 files**; stock lag **−512 samples
on 38/38** successful decodes (the stock build emits 512 leading
samples before reference sample 0; sign convention: test[i] ≈
ref[i + lag]). SNR is computed over the aligned intersection, both
channels pooled, in float64. Harness validation: the same pipeline
reproduces the swap program's published figures on its own
`test.ogg` (stock 45.0 dB vs published 45.1; transplant 85.2 dB vs
published 85.5 against an s16 reference; 87.0 dB against the float
reference).

**Metrics** per file and decoder (definitions in `measure.py`):

- `total`: SNR of the s16 output (÷32768) against the float
  reference. This is the finish-line metric as specified.
- `ceil`: SNR of round-to-nearest-s16(float reference) against the
  float reference: the best any correctly rounding 16-bit output can
  do on this signal.
- `grid`: SNR of the output against round-to-nearest-s16(float
  reference): decoder differences as delivered on the 16-bit grid.
- In-range variants (`total_ir`, `ceil_ir`): the same, restricted to
  samples with |ref| ≤ 1.0, needed because of the overshoot finding
  below. Headline totals in this report are the in-range ones;
  `results.csv` carries both.

**Overshoot finding.** On 12 corpus files (the loud sweep and music
sources at q0–q5), the ffmpeg *float* decode exceeds 0 dBFS (peaks
1.00–1.39, up to 0.61 % of samples): the low-quality encode of a
0.92-peak source reconstructs above full scale. Every 16-bit output
necessarily clips those samples, so the raw `total` on those files
(40.6 to 70.3 dB for the transplant) measures clipping of an
out-of-range reference, not decoder error. The in-range metric
excludes those samples; on the 28 files whose references stay in
range, raw and in-range totals agree to ≤ 0.25 dB, and §4's identity
holds on the in-range numbers for all 40.

**Protocol deviations** (against `vorbis_test.md` §6.2 and the
performance plan, declared per instructions): the corpus is the
task-specified synthesized set (adds q0/q3/q7, tones and pink
classes, 6 s files; §6.2's 96 kHz case and 30 s music files were not
run, the task protocol specified 44.1/48 kHz); the encoder is
ffmpeg's binding of libvorbis 1.3.7, the library version §6.2 names,
rather than `oggenc`; the PC Tremor reference builds of §6.2 step 2
were not built, because the conversion identification in §4 performs
the same separation of arithmetic from output quantization directly
against the float reference; the in-range metric was added after the
overshoot finding.

## 3. Results

Delivered totals for the transplant sit in a narrow band set by
source level, nearly independent of quality (medians per quality:
81.1, 81.2, 81.2, 81.2, 81.3 dB for q0…q9), which is already the
signature of a level-dependent output floor rather than codec or
arithmetic behaviour:

| Source | RMS (dBFS) | Transplant total_ir: min / med / max | s16 ceiling (ceil_ir) | Stock total: min / med / max |
|---|---|---|---|---|
| sweep | -3.9 | 91.2 / 91.4 / 91.4 | 97.2–97.4 | 38.9 / 41.8 / 42.1 |
| tones | -13.0 | 82.1 / 82.2 / 82.3 | 88.1–88.3 | 40.1 / 40.2 / 40.2 |
| pink | -14.9 | 80.1 / 80.2 / 80.3 | 86.1–86.3 | 38.1 / 38.2 / 38.3 |
| music | -15.9 | 79.0 / 79.3 / 79.4 | 85.1–85.4 | 38.3 / 40.7 / 42.1 |

Stock module 75 on the same corpus: totals 38.12 to 42.14 dB
(median 40.17 dB, n = 38), which closes the one outstanding item in
`vorbis_test.md`: its claim 5 predicted ~38–43 dB from berettavexee's
PC measurements of the identical mode and was rated "strongly
indicated" pending a direct PCM measurement. It is now **proven by
direct measurement** of the Neo module's own output (and the same
corpus reproduces the PC A/B band almost exactly). Per-file gain of
the transplant over stock, on the 26 files where both decoded and
the reference stayed in range: **+37.2 to +49.6 dB, median +42.0
dB**. Full per-file numbers in Appendix A.

## 4. Loss decomposition: where the 15 dB went

Three measured facts, each checkable from `results.json` and
`floor_results.json`, account for the entire gap between the
delivered totals (79.1–91.4 dB) and the finish line:

**Fact 1: the s16 ceiling is below the line for most content.**
Round-to-nearest quantization of the float reference gives ceilings
(`ceil_ir`) of 97.2–97.4 dB for the sweep (RMS −3.7 dBFS), 88.1–88.3
for tones (−12.9), 86.1–86.3 for pink (−14.9), and 85.1–85.4 for
music (−15.8). Quantization SNR scales with signal level, so only
near-full-scale material can even theoretically reach 96 dB through
a 16-bit interface. This part of the shortfall is irreducible at
16 bits and has nothing to do with the decoder.

**Fact 2: the module's conversion floors, costing exactly 6.02 dB
more.** For every file, the transplant's delivered total obeys

    total_ir = ceil_ir − 6.02 dB   (within 0.03 dB, 40/40 files)

6.02 dB is the exact power ratio between the two quantization error
distributions: a floor (round toward −∞) conversion has error
uniform on a full LSB, E[e²] = LSB²/3; round-to-nearest has
E[e²] = LSB²/12. The sample-level evidence agrees: the output minus
round-to-nearest(reference) is in {−1, 0} LSB for both signs of the
reference, on ~50 % of samples each, which is the fingerprint of
floor: the module's conversion is `floor(x · 32768)`, not rounding.
(The stock module's output error, 40–174 LSB RMS, swamps any
conversion signature; its convention is not determinable and does
not matter at 40 dB.)

**Fact 3: under the conversion, the arithmetic is clean.**
Modelling the conversion out (`floor_analysis.py`): the transplant
output equals `floor(ref · 32768)` **exactly on 96.4–98.8 % of
samples** per file, and **never deviates by more than 1 LSB** on any
sample of any file. The residual 1.2–3.6 % single-LSB deviations are
boundary flips: the fixed-point decoder's pre-conversion value
differs from libvorbis float by a fraction of an LSB, which flips
the floored result only where the value sits within that fraction
of an integer boundary. From the flip rate (ε ≈ zero-mean,
p(flip) ≈ E|ε| ≈ 0.798σ) the implied arithmetic error is
σ ≈ 0.015–0.045 LSB, an arithmetic-only SNR of **102.4 to 123.1 dB,
median 106.9 dB**, across the corpus (per-file values in
`floor_results.json`). Corroboration: if any arithmetic noise above
~−100 dB relative to signal were present and independent, the
Fact 2 identity would break upward by more than the observed
0.03 dB.

**Conclusion of the decomposition.** The delivered shortfall
against 96 dB decomposes as: the signal-level-dependent s16 ceiling
(which by itself leaves the line anywhere from 1.4 dB of headroom,
for the loudest content, to 10.9 dB short, for the quietest), plus
floor-instead-of-round conversion (−6.02 dB, exactly). Decoder
arithmetic contributes nothing measurable at these levels and
independently estimates at ≥ 102 dB. So:

- **As specified, the finish line is not met**, and cannot be met
  by any build that delivers 16-bit PCM: on this corpus even a
  perfect decoder with a rounding output scores 85.1–97.4 dB.
- **The line's intent is met**: the decoder arithmetic is
  transparent at 16-bit resolution and roughly 10 dB better than
  the line's threshold; the decoder is no longer the weak link in
  the chain. The weak link is the delivered word length and its
  conversion rule.
- **A concrete 6.02 dB is recoverable in principle**: an output
  conversion that rounds to nearest instead of flooring would lift
  every delivered total by exactly that amount (to 85.1–97.4 dB on
  this corpus). The conversion lives in the transplanted library's
  output path; the exact instruction was not isolated (the
  identification here is statistical, from output behaviour, and
  is stated as such). Whether to pursue it is a patch-program
  decision, not part of this measurement.
- Recommended restatement of the finish line for future codecs:
  score arithmetic the way this run did (model the delivered
  conversion, report the implied arithmetic SNR) with the ≥ 96 dB
  threshold on the arithmetic, and treat the delivered total as an
  interface property reported alongside.

## 5. Stock decode failures on pink q9 (both rates)

The stock module failed on `pink_q9_44100.ogg` and
`pink_q9_48000.ogg` (353 kbps at 48 kHz; the largest-packet files in
the corpus); the transplant decoded both fully. Characterisation,
bounded to what was tested:

- Deterministic: identical on retry, and independent of the
  harness RAM fill byte (EMU_FILL 0xa5 vs 0x00).
- Path-dependent in form, not in outcome: through the runtime file
  layer, the 48 kHz file fails OPEN outright and the 44.1 kHz file
  returns success with empty stream info (rate 0, length −1) and
  one 512-frame buffer of output; through `--stub-io` it opens
  with corrupt info and stalls after 512 frames.
- Content, not encoder or duration: a 1 s libvorbis excerpt and a
  full-length encode from ffmpeg's native Vorbis encoder show the
  same signature (at most the first 512-frame buffer decodes, then
  the stream breaks). All 38 other corpus files, including pink q7
  (233 kbps) and music q9, decode fully under stock.
- Working hypothesis, not isolated to instruction level: the stock
  Ogg/vorbisfile layer mishandles the refill path for the large
  audio packets dense noise at q9 produces (first audio packet
  ≈ 1.1 KB, sustained); the transplant replaces precisely that
  layer (berettavexee's streaming Ogg reader), which fits its
  immunity. On-hardware behaviour is unknown: the harness file
  layer is a model of the runtime, and the real system core may
  serve the file differently. Recorded here as a harness-observed
  stock failure with a stated locus hypothesis; it does not affect
  any transplant number in this report.

## 6. Decode cost

Dynamic instruction counts (Unicorn block hooks + Capstone
disassembly of each unique block; whole session: prepare, open,
full decode, close; identical path for both modules;
`decode_cost.py`):

| File | Stock insn/s of audio | Transplant insn/s of audio | Ratio |
|---|---|---|---|
| music_q5_48000.ogg | 17,890,570 (107,438,837 insn / 6.005 s) | 19,525,010 (117,254,194 insn) | 1.091 (+9.1 %) |
| sweep_q9_48000.ogg | 16,137,915 (96,913,561 insn / 6.005 s) | 17,542,876 (105,350,819 insn) | 1.087 (+8.7 %) |

The transplant costs **+8.7 to +9.1 %** instructions over stock in
this harness. That is higher than berettavexee's +2.8 % PC figure
for the library swap alone; the difference is plausibly the
replacement Ogg layer and runtime mix here (the transplant executes
more, smaller blocks: 16.6 M vs 12.1 M block executions on the music
file), and the two numbers measure different scopes. Instruction
counts are not cycles, but the clock-v1 headroom question is not
close either way: at the tuned OGG clock row of 240 MHz, ~19.5 M
instructions per second of audio is on the order of 8 % of the
instruction budget before any cycles-per-instruction allowance, and
the ≤ 70 % headroom finish line (§3.3) is met with a wide margin
under any realistic CPI. The transplant does not endanger the
clock v1 OGG rows.

## 7. Reproduce

```sh
venv/bin/python work/vorbis_corpus/gen_corpus.py     # corpus + manifest.json
venv/bin/python work/vorbis_corpus/run_emu.py        # 80 harness decodes
venv/bin/python work/vorbis_corpus/measure.py        # results.json / .csv
venv/bin/python work/vorbis_corpus/floor_analysis.py # floor_results.json
venv/bin/python work/vorbis_corpus/decode_cost.py music_q5_48000.ogg
```

## Appendix A: per-file results

SNR in dB. `total_ir` is the headline delivered total (in-range);
`ceil_ir` is the round-to-nearest s16 ceiling on the same samples;
`floor match` is the transplant's exact-match rate against
floor(ref·32768); `arith est` is the implied arithmetic-only SNR
(§4, Fact 3). Stock failures are the §5 files.

| File | Stock total | Transplant total_ir | ceil_ir | Transplant grid | Floor match % | Arith est |
|---|---|---|---|---|---|---|
| sweep_q0_44100.ogg | 38.85 | 91.18 | 97.21 | 89.50 | 98.8 | 123.1 |
| sweep_q3_44100.ogg | 42.07 | 91.31 | 97.33 | 89.55 | 98.7 | 122.3 |
| sweep_q5_44100.ogg | 42.11 | 91.38 | 97.39 | 89.62 | 98.6 | 121.8 |
| sweep_q7_44100.ogg | 42.12 | 91.39 | 97.39 | 89.63 | 98.5 | 121.4 |
| sweep_q9_44100.ogg | 42.12 | 91.40 | 97.41 | 89.64 | 98.4 | 120.8 |
| sweep_q0_48000.ogg | 39.17 | 91.18 | 97.19 | 89.49 | 98.8 | 123.0 |
| sweep_q3_48000.ogg | 41.69 | 91.31 | 97.33 | 89.55 | 98.7 | 122.4 |
| sweep_q5_48000.ogg | 41.77 | 91.38 | 97.38 | 89.62 | 98.6 | 121.9 |
| sweep_q7_48000.ogg | 41.80 | 91.40 | 97.41 | 89.64 | 98.5 | 121.4 |
| sweep_q9_48000.ogg | 41.82 | 91.43 | 97.43 | 89.66 | 98.4 | 120.5 |
| tones_q0_44100.ogg | 40.12 | 82.10 | 88.13 | 80.35 | 97.7 | 108.0 |
| tones_q3_44100.ogg | 40.16 | 82.17 | 88.18 | 80.42 | 97.5 | 107.6 |
| tones_q5_44100.ogg | 40.16 | 82.21 | 88.23 | 80.46 | 97.5 | 107.5 |
| tones_q7_44100.ogg | 40.15 | 82.24 | 88.24 | 80.49 | 97.5 | 107.6 |
| tones_q9_44100.ogg | 40.15 | 82.25 | 88.24 | 80.50 | 97.5 | 107.4 |
| tones_q0_48000.ogg | 40.18 | 82.06 | 88.09 | 80.31 | 97.7 | 108.0 |
| tones_q3_48000.ogg | 40.20 | 82.16 | 88.18 | 80.41 | 97.6 | 107.8 |
| tones_q5_48000.ogg | 40.22 | 82.22 | 88.23 | 80.47 | 97.6 | 107.8 |
| tones_q7_48000.ogg | 40.22 | 82.24 | 88.24 | 80.48 | 97.5 | 107.6 |
| tones_q9_48000.ogg | 40.21 | 82.26 | 88.27 | 80.51 | 97.5 | 107.5 |
| pink_q0_44100.ogg | 38.29 | 80.19 | 86.18 | 78.44 | 96.7 | 103.2 |
| pink_q3_44100.ogg | 38.24 | 80.13 | 86.13 | 78.38 | 96.6 | 102.7 |
| pink_q5_44100.ogg | 38.23 | 80.14 | 86.14 | 78.40 | 96.5 | 102.5 |
| pink_q7_44100.ogg | 38.22 | 80.15 | 86.16 | 78.41 | 96.4 | 102.4 |
| pink_q9_44100.ogg | **decode failed** | 80.18 | 86.19 | 78.44 | 96.5 | 102.6 |
| pink_q0_48000.ogg | 38.18 | 80.18 | 86.19 | 78.43 | 96.8 | 103.2 |
| pink_q3_48000.ogg | 38.13 | 80.14 | 86.14 | 78.40 | 96.6 | 102.8 |
| pink_q5_48000.ogg | 38.12 | 80.18 | 86.18 | 78.44 | 96.5 | 102.7 |
| pink_q7_48000.ogg | 38.15 | 80.21 | 86.23 | 78.48 | 96.4 | 102.5 |
| pink_q9_48000.ogg | **decode failed** | 80.26 | 86.27 | 78.52 | 96.5 | 102.6 |
| music_q0_44100.ogg | 38.29 | 79.10 | 85.14 | 77.37 | 97.8 | 105.7 |
| music_q3_44100.ogg | 39.50 | 79.18 | 85.19 | 77.44 | 97.9 | 105.9 |
| music_q5_44100.ogg | 39.29 | 79.29 | 85.29 | 77.56 | 97.8 | 105.9 |
| music_q7_44100.ogg | 42.14 | 79.38 | 85.39 | 77.63 | 97.9 | 106.3 |
| music_q9_44100.ogg | 42.13 | 79.39 | 85.41 | 77.64 | 97.9 | 106.3 |
| music_q0_48000.ogg | 40.85 | 79.05 | 85.08 | 77.31 | 97.9 | 105.7 |
| music_q3_48000.ogg | 40.62 | 79.13 | 85.15 | 77.39 | 97.8 | 105.4 |
| music_q5_48000.ogg | 39.66 | 79.23 | 85.24 | 77.50 | 97.7 | 105.3 |
| music_q7_48000.ogg | 42.10 | 79.40 | 85.40 | 77.65 | 97.8 | 105.9 |
| music_q9_48000.ogg | 42.09 | 79.41 | 85.42 | 77.65 | 97.8 | 105.7 |

## Appendix B: corpus manifest (ogg SHA-256)

Generator settings and source hashes: `manifest.json`. Encoder:
ffmpeg 8.1.2, libvorbis 1.3.7, `-q:a` as listed.

| File | Source | q | Rate | Bytes | SHA-256 |
|---|---|---|---|---|---|
| sweep_q0_44100.ogg | sweep | 0 | 44100 | 19677 | `6c9f5e35d5b6933abdaa7ac06ae49cd5a2310c2f06de1941b532b99e8afd4e96` |
| sweep_q3_44100.ogg | sweep | 3 | 44100 | 24120 | `e0f1ce7276758c62dcdecca06677e1139c9c5211dbe41722370ab7e355dd5071` |
| sweep_q5_44100.ogg | sweep | 5 | 44100 | 26598 | `18324e9b4f232b7b8ca2671b8ca29c86b35397ef487978f282b0e910d96bcf6a` |
| sweep_q7_44100.ogg | sweep | 7 | 44100 | 29004 | `823079fc2186630bdbfa87f3db0f5fe84252584703d296787076f494f833304f` |
| sweep_q9_44100.ogg | sweep | 9 | 44100 | 35637 | `a401ded84364d8492b2e74924894b31b758c86533a289b7796ae1ec542087226` |
| sweep_q0_48000.ogg | sweep | 0 | 48000 | 21623 | `e046db256cde5ecfe8a94e007ea56cf5a335c495f937ea316e3fbe7efe653fc2` |
| sweep_q3_48000.ogg | sweep | 3 | 48000 | 26167 | `49829119d7a9c7186d17d95a2b8b1f731e3d51b061a460700026a2d4070c4ab4` |
| sweep_q5_48000.ogg | sweep | 5 | 48000 | 28906 | `3786dffb351747a7cabd198c323164dedacd565f2bd860d6cc8e56014a4c1977` |
| sweep_q7_48000.ogg | sweep | 7 | 48000 | 32443 | `9117d19cc0f1a44656b2fc3e956e01b99705c08d3792dcf8b55d42f74170d2b2` |
| sweep_q9_48000.ogg | sweep | 9 | 48000 | 42086 | `96da6b604d845ea9a812c307547735beb3696289d67c46946acd35ec0576fea9` |
| tones_q0_44100.ogg | tones | 0 | 44100 | 42182 | `c9e397cbaa8d4c68e31840b8b1fc1ba8e20cb1404b32a1171ebe7fe13223ef0d` |
| tones_q3_44100.ogg | tones | 3 | 44100 | 59335 | `d7e6a73a3b76b3b2320a89db98d2de3852ecdcc8d64942feff6305e27a682362` |
| tones_q5_44100.ogg | tones | 5 | 44100 | 70229 | `f97914f743a396aabd2139c9a1ff0e0a598894d89e56259d74591f4eb6b9c61c` |
| tones_q7_44100.ogg | tones | 7 | 44100 | 74774 | `a45addda2c82bcaa94815ccce57f10b69d91cbf7075572eef1d006f57d9ea647` |
| tones_q9_44100.ogg | tones | 9 | 44100 | 86652 | `3507d55ea1dddfdb37d492707f629c72ae2243c8c4174b89c7eedadf628fefce` |
| tones_q0_48000.ogg | tones | 0 | 48000 | 44613 | `20f6afa54edcb16f526ffac9795a22229b771659ef7804703dd187ae6c2c9956` |
| tones_q3_48000.ogg | tones | 3 | 48000 | 63223 | `21d95b191663239edd19dd73697eaabf3708be91d2507073e90c11e06a9af6af` |
| tones_q5_48000.ogg | tones | 5 | 48000 | 73979 | `f0cd70c76b9c84373d4c00a6ff436f76e49323cf396eb7fdab01d555c9676003` |
| tones_q7_48000.ogg | tones | 7 | 48000 | 81910 | `f61e477af3eac19b10ba8f8cb2d98985b0459bfc23a7a601fa06ada014dcb1ec` |
| tones_q9_48000.ogg | tones | 9 | 48000 | 92606 | `ec6e88f2918237df860aaadc73ade20363f381a2c36d31198f05092d06724e62` |
| pink_q0_44100.ogg | pink | 0 | 44100 | 52958 | `47493fe1dc26c49914fa5ac2e9a204202857be4045f7354ff8103ba9efd67876` |
| pink_q3_44100.ogg | pink | 3 | 44100 | 85738 | `7605d1a01376cc174aa208abc13bdff1ca1903c7ab6515b004181f0590bfb53f` |
| pink_q5_44100.ogg | pink | 5 | 44100 | 124817 | `46893d868c5f91439c1baa762629031e943821789a9509168e0e5c06704d580e` |
| pink_q7_44100.ogg | pink | 7 | 44100 | 169464 | `63f7ceb9a8f454d397eeb8a1a4496548274b39ae7d38d256075db0066e39cf82` |
| pink_q9_44100.ogg | pink | 9 | 44100 | 251307 | `9751175022dbeec860d3e36ada696b5293fb9945675f31a2381825eee8345999` |
| pink_q0_48000.ogg | pink | 0 | 48000 | 52415 | `e1dec207acb2a9d94b82780ca462afe6ca6d562e59c8ca5fb1bc64beeca756c5` |
| pink_q3_48000.ogg | pink | 3 | 48000 | 85736 | `c46d16ea5b84ed75bed50e33a468771f9d6682273a36ab00b9cb16f0cf7d1c09` |
| pink_q5_48000.ogg | pink | 5 | 48000 | 123150 | `70088048ab8b00507bac91619834758db3f100a5c9ea53f7ca73502ae0256df9` |
| pink_q7_48000.ogg | pink | 7 | 48000 | 174950 | `2b8c7393e2d677838835d56738f50cf486d01c31c72da3cd056e873cf4938e0e` |
| pink_q9_48000.ogg | pink | 9 | 48000 | 264440 | `7800926a099079b1c9ca4ee35e3964badcfc0e1c544bc61f0a8cab5f13c51a2e` |
| music_q0_44100.ogg | music | 0 | 44100 | 38395 | `f695bc1b68be4c6a5b6b59c017b6dc4e0342061212d12497e8e5691d6fb119b1` |
| music_q3_44100.ogg | music | 3 | 44100 | 55466 | `8cf8414867e8dc2fad9ec9b76b083d5dbc50c81d87464cde09cc581c82cb3379` |
| music_q5_44100.ogg | music | 5 | 44100 | 67732 | `f846231cd7d8a2dff9266569f8213d598b6dfbde274c941ddfc0046da39aba2e` |
| music_q7_44100.ogg | music | 7 | 44100 | 95672 | `69cecadab89dee7c99d5f4250233ff8a97766fc67a5a31f6c668660f8ba001ce` |
| music_q9_44100.ogg | music | 9 | 44100 | 113932 | `c815db8a6def97d0310965b210194db2a879e4964551c712a829df7ba06e39c4` |
| music_q0_48000.ogg | music | 0 | 48000 | 38625 | `ac899fe3a56ac3c4480c70e394c76bb52d90e9bf82fdd450701f062439011c6d` |
| music_q3_48000.ogg | music | 3 | 48000 | 53595 | `24fa782cf96baf8b9c6f1ea87796aab1668f96e87d2b693e5ea935946ca61b7d` |
| music_q5_48000.ogg | music | 5 | 48000 | 64027 | `ee52817d1da73ab91c35904c7ca2f89bc53ddcce5c2d57b6fdb00f05c26c0161` |
| music_q7_48000.ogg | music | 7 | 48000 | 89857 | `34b28135d4fa16296e54f4a78423383c714ddefd51f304df130d2ae0b106af71` |
| music_q9_48000.ogg | music | 9 | 48000 | 110004 | `e3d4e5cc6626101b14ca3ba726ef8ee36cbe0ae8df1b998b0dbd944d3a398f85` |

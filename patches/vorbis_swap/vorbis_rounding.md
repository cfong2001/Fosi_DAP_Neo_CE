# Vorbis rounding: conversion isolated, fix proven in the harness, production mechanism designed

Scope: the transplanted module 75 only (berettavexee full-precision Tremor, spliced by work/patches/vorbis_swap/transplant.py). All work is offline, in work/vorbis_rounding/, against the Unicorn harness emu75.py. Nothing in the live framework, manifest, or transplant pins was touched. Stock image DP3_V137.img re-verified at the end of the session: SHA-256 fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef, unchanged.

## The conversion site

### How it was found

The PCM output buffers sit at 0x103F4DC and 0x10414DC in the data segment (512 frames each, filled on alternate DECODE calls). Filling both with a 0x5A sentinel and single-stepping a DECODE while watching for the first changed byte puts the first output store at PC 0x58DA. A census pass over three files (tones_q5_44100, music_q0_44100, sweep_q9_48000), single-stepping one whole steady-state DECODE per file (22,161 to 23,697 steps) and recording every store PC that touches either buffer, finds exactly two output-writing sites per decode, partitioning the buffer at a block-geometry-dependent offset (768 bytes for tones and music at 44.1 kHz, 1280 bytes for the sweep at 48 kHz). A census of the first DECODE after OPEN finds a third site writing the leading region of the buffer that decode fills. A census of the first DECODE after a SEEK to 3000 ms finds only the two steady-state sites. A fourth conversion-shaped store exists in the same function and never fired in any census; it is covered below.

One harness note: Unicorn 2.1 silently ignores the instruction count of emu_start for translation blocks cached by earlier calls, which makes naive single-stepping run to the end of the call. Calling ctl_remove_cache(0, 0x20000) after setting up the stepped call makes the count exact; coarse and fine stepping then agree on the write step.

### The four sequences

All addresses are code-segment offsets in module75_patched_code.bin. All four sites sit inside the transplanted code region (0x29D0 to 0xE054), in the library's overlap-add output stage of its synthesis code. The conversion is pure fixed-point integer work. There is no float anywhere in the path and no FPU on this core. The floor is produced by arithmetic shift and bit-field extraction, not by any float-to-int truncation.

Site A, steady state, first overlap region. Two window products are accumulated as 64-bit smull results and only their high words are kept:

- 0x58B0: smull r0, fp, r3, r7 (product P1; high word to fp, stored to [sp, 0x1C] at 0x58B6)
- 0x58C8: smull r0, r3, r7, fp (product P2; high word to r3; the low word of P1 is overwritten here and never used)
- 0x58CC: ldr r7, [sp, #0x1c] (bytes 07 9f), reload high word of P1
- 0x58CE: ldr r0, [sp, #4] (01 98), output pointer
- 0x58D0: add r3, r7 (3b 44), V = hi(P1) + hi(P2)
- 0x58D2: sbfx r3, r3, #8, #0x17 (43 f3 16 23), extract bits 8 to 30, sign-extended: floor(V / 256)
- 0x58D6: ssat r3, #0x10, r3 (03 f3 0f 03), saturate to s16
- 0x58DA: strh r3, [r0] (03 80), the store

Site B, steady state, second overlap region. Same shape, with a subtraction (the window symmetry makes the second product subtract) and the output pointer in r8:

- 0x58EC: smull fp, r0, sl, sb (P1; high word to r0, stored to [sp, 0x18] at 0x58FC)
- 0x5902: smull r0, sl, fp, sb (P2; high word to sl)
- 0x5906: ldr r0, [sp, #0x18] (06 98), reload high word of P1
- 0x5908: sub.w r0, r0, sl (a0 eb 0a 00), V = hi(P1) - hi(P2)
- 0x590C: sbfx r0, r0, #8, #0x17 (40 f3 16 20), floor(V / 256)
- 0x5910: ssat r0, #0x10, r0 (00 f3 0f 00)
- 0x5914: strh.w r0, [r8] (a8 f8 00 00), the store

Site D, first DECODE after OPEN only, the leading region of the buffer that decode fills (offsets 0 to 767 in the observed decode; frames 512 to 703 of the stream, since the OPEN-primed buffer ahead of it holds frames 0 to 511). No overlap partner exists yet, so the path converts a single Q24 sample word; the rsbs negates it because the loaded word holds the sample with the sign convention of the mirrored window half:

- 0x591C: ldr r2, [r0], #8 (50 f8 08 2b)
- 0x5920: rsbs r2, r2, #0 (52 42), W = -s
- 0x5922: asrs r2, r2, #9 (52 12), floor(W / 512)
- 0x5924: ssat r2, #0x10, r2 (02 f3 0f 02)
- 0x5928: strh r2, [r3] (1a 80), the store

Site C, same function, never observed firing in any census (steady state on three files across both rates and three sources, plus first-decode and post-seek passes):

- 0x588E: ldr r3, [r2, #-0x4]! (52 f8 04 3d)
- 0x5892: asrs r3, r3, #9 (5b 12), floor(s / 512)
- 0x5894: ssat r3, #0x10, r3 (03 f3 0f 03)
- 0x5898: strh.w r3, [fp] (ab f8 00 30), the store

Scale check. A sample is Q24 and a window coefficient is Q31, so a product is Q55 and the s16 result is the product divided by 2^40. Sites A and B take the high word (division by 2^32) and extract from bit 8 (another 2^8), landing on the same 2^40. Sites C and D shift a Q24 word right by 9, which is multiplication by 2^15 in Q24 terms. All four compute floor(x * 32768), then saturate. Saturation is applied after the floor at every site.

The low words dropped at sites A and B cost at most 2 high-word units of pre-conversion value, under 0.008 LSB. That is two orders of magnitude below the effects measured in the corpus work and is not part of the 6.02 dB story.

### Register-level proof

verify_sites.py replays the same stepped decodes and, at each store execution, reconstructs the pre-extraction value from the trace window, then checks three things: the extraction rule (sbfx or asrs, then ssat) reproduces the stored halfword; the stored halfword equals the corpus harness output tones_q5_44100__patched.s16 at the same frame and channel; and the pre-extraction value, in s16 units, sits close to the ffmpeg float reference sample computed independently. 42 samples captured (14 per site at A, B, D), all checks pass on all 42. Discriminating samples, where floor and round-to-nearest disagree:

- Site A, frame 2052 ch0: V = -192,567, which is -752.215 s16 units. Stored -753 (floor). Round-to-nearest would give -752. Reference -752.186.
- Site A, frame 2048 ch0 (the first sample traced in this work): V/256 = 3164.883 against a reference of 3164.891, a pre-conversion error of -0.008 LSB. Stored 3164.
- Site B, frame 2248 ch0: V = -427,104, which is -1668.375 s16 units. Stored -1669 (floor). Round-to-nearest would give -1668. Reference -1668.460.
- Site D, frame 513 ch0: W/512 = -6740.234 s16 units. Stored -6741 (floor). Round-to-nearest would give -6740. Reference -6740.253.

Pre-conversion values track the reference to within 0.04 LSB at sites A and D, and within 0.22 LSB at site B, whose subtraction path carries the larger share of the module's arithmetic error. That spread is the arithmetic term the corpus document estimated at 102 to 123 dB; the conversion rule itself is exact on every captured sample.

## The harness proof

### The modification

The extraction points have no spare bytes inline (site A's add plus sbfx occupy 6 bytes where a biased add plus sbfx needs 8; sites C and D have a 2-byte shift). The fix therefore detours each site through a small code cave. The caves sit in the zero tail of the transplanted code region: bytes 0xDEE0 to 0xE054 of the code segment are all zero (372 bytes, checked byte by byte), and the four caves use 52 of them, ending at 0xDF1E. Each cave adds half an output LSB to the pre-extraction value, runs the site's original extraction and saturation, and branches back:

- Site A: bytes at 0x58D2 replaced by b.w to cave A at 0xDEE0: add.w r3, r3, #0x80; sbfx r3, r3, #8, #0x17; b.w 0x58D6. The bias is 0x80 because the extraction step is 256 high-word units per output LSB.
- Site B: bytes at 0x590C replaced by b.w to cave B at 0xDEF0: add.w r0, r0, #0x80; sbfx r0, r0, #8, #0x17; b.w 0x5910.
- Site C: bytes at 0x5892 to 0x5897 replaced by b.w to cave C at 0xDF00 plus a nop: add.w r3, r3, #0x100; asrs r3, r3, #9; ssat r3, #0x10, r3; b.w 0x5898. The bias is 0x100 because the shift step is 512 Q24 units per output LSB.
- Site D: bytes at 0x5922 to 0x5927 replaced by b.w to cave D at 0xDF10 plus a nop: add.w r2, r2, #0x100; asrs r2, r2, #9; ssat r2, #0x10, r2; b.w 0x5928. The bias is applied after the rsbs, to the value that is actually shifted, so the negated path rounds correctly instead of flooring away from the intended value.

Total change: 70 bytes (20 at the four detour sites, 50 in the caves; two cave bytes coincide with the zeros they replace). Branch encodings were produced by rz-asm at the correct addresses and every changed instruction was re-decoded with capstone; the sbfx, ssat, and asrs encodings inside the caves are byte-identical to the ones the sites already used. build_round.py asserts the expect-bytes at every site and the all-zero precondition in every cave before writing module75_round_code.bin (SHA-256 bfea243bcc56b854555a093cd3a2f25a12e5f2d5b6312c56e10efe1a449917c5). The data segment is the unmodified transplanted one. The combined module (code plus data) hashes to dd8f772fb5c7fa128ed5bdfde99401cff66798847eb6c993feea89a0997ab695, against the current pin 42c42796ad8f2e931c82db470cdaf754ca101a192834c11259a8bf05e787a3ca.

Overflow is not a concern: the biased value stays within the headroom the sbfx field already tolerates (inputs are bounded by the window sums, and ssat still clips at the s16 rails exactly as before; a value within half an LSB of the positive rail now rounds up into the rail instead of flooring one below it, which is the correct round-to-nearest behavior).

### Results on the primary seven files

Decoded with emu75.py using the modified code segment, scored with the corpus's own measure.py analyse() and its in-range metric (samples with |ref| <= 1.0). Before and ceiling are the published transplanted-module figures from results.json.

| File | Before (dB) | After (dB) | Ceiling (dB) | Delta (dB) | Round-exact % |
|---|---|---|---|---|---|
| sweep_q0_44100 | 91.18 | 97.19 | 97.21 | +6.01 | 98.82 |
| sweep_q5_44100 | 91.38 | 97.37 | 97.39 | +5.99 | 98.61 |
| tones_q5_44100 | 82.21 | 88.16 | 88.23 | +5.95 | 97.52 |
| pink_q7_44100 | 80.15 | 85.97 | 86.16 | +5.82 | 96.39 |
| music_q0_44100 | 79.10 | 85.08 | 85.14 | +5.98 | 97.85 |
| sweep_q9_48000 | 91.43 | 97.40 | 97.43 | +5.97 | 98.37 |
| music_q9_48000 | 79.41 | 85.34 | 85.42 | +5.93 | 97.79 |

The fix was then run over the full 40-file corpus with the same result shape on every file. Delivered delta by source: sweep 5.98 to 6.01 dB, tones 5.91 to 5.97 dB, music 5.93 to 5.98 dB, pink 5.80 to 5.88 dB. After-fix delivered SNR sits 0.01 to 0.21 dB under the published per-file ceilings.

### Why the delivered delta is 5.80 to 6.01 and not a flat 6.02

The conversion's own noise term falls by exactly the factor the corpus document predicts: floor error power is LSB^2/3, round-to-nearest error power is LSB^2/12, a ratio of 4, which is 6.02 dB. The delivered SNR, however, is measured against total noise, which is the conversion term plus the module's arithmetic noise, and the fix does not touch the arithmetic term. The expected delivered delta is 10*log10((1/3 + s^2)/(1/12 + s^2)) with s the arithmetic RMS error in LSB. For s = 0.02 (sweep files) that is 6.00 dB; for s = 0.037 (tones) 5.94 dB; for s = 0.061 (pink) 5.83 dB. Those match the measured deltas file family by file family. The s values quoted here are implied by the measured gap between the after-fix SNR and the ceiling, and they sit modestly above the corpus document's floor-flip estimates (0.045 LSB for pink_q7 against 0.061 here), because the flip estimator assumes a symmetric zero-mean error and the subtraction path at site B is neither. The residual gap to the ceiling is the arithmetic term standing against the smaller quantization term; before the fix it was buried under the floor term, which was four times larger.

Two sample-level checks show the implementation itself adds nothing and removes nothing beyond the intended half-LSB bias:

- On all 40 files, fixed output minus original output is in {0, +1} for every sample. No sample moves down, no sample moves by 2. The +1 share is 48.7 to 50.1 percent, the expected signature of adding half an LSB before the same floor.
- The new match rate, computed on the same basis as the corpus document's floor analysis (module output against a direct conversion of the float reference, aligned by the measured lag of 0), is 96.39 to 98.86 percent exact against round-to-nearest across the 40 files, with a maximum deviation of 1 LSB everywhere. That is the same band as the published floor-exact rates of 96.4 to 98.8 percent, with the residuals explained by the same sub-LSB arithmetic boundary flips. The match basis uses rint (round-half-even), as measure.py's ceiling does; the hardware fix rounds half up on the module's own pre-conversion value. Rates computed against a half-up reference differ by at most 0.008 percentage points (exact .5 ties are 0.04 to 0.17 percent of reference samples, and the module value lands on a tie only when its arithmetic error is exactly zero there), so the distinction does not move any figure in this report.

Site C is patched but, as noted, was never observed firing. If it is dead code the patch is inert; if it serves a path the harness does not reach (a different block geometry or channel count), the full-corpus runs cannot distinguish the two cases, because a correctly patched site and a never-executed site produce identical output. It is patched on structural grounds: it is the same conversion in the same function, and leaving one flooring path in place would leave the fix incomplete on hardware.

## The stock module

Stock module 75 uses the same conversion pattern in its own library build, at different addresses with a different instruction sequence. Its two output loops accumulate with 32-bit mul, mla, and mls against byte-table coefficients (the low-precision build's multiply path), then convert with asrs r0, r0, #9 at 0xB03A (store strh r0, [r5] at 0xB07C) for the first buffer region and asrs r0, r0, #9 at 0xAF44 (store strh r0, [r2] at 0xAF86) for the second, the same 768-byte split the transplant shows on the file both censuses used. Where the transplant saturates with a single ssat, stock runs a branchless clamp built from cmp and cmn against 0x8000, ite, movlt and movge, and a mask-and-subtract pair, which is the same CLIP_TO_15 source compiled without an ssat idiom. So the lineage is shared (Tremor framing code, arithmetic-shift floor immediately before the clamp, one loop per overlap region) but nothing byte-level is: not the addresses, not the accumulation, not the clamp, not the register allocation. A single patch pattern could not serve both modules. It would also be pointless to try: stock's 38 to 42 dB is set by its arithmetic (about 7 effective bits), and stock stays unpatched regardless.

## Production mechanism (design only, not integrated)

The change lives entirely inside the transplanted library: all four sites and all four caves are inside the code region the transplant owns (0x29D0 to 0xE054). That fact decides the mechanism.

Option (a), a post-transplant patch class in the framework, works but costs the most machinery. build.py would need a second manifest pass ordered after apply_transplants, with expect-bytes taken against the post-transplant image and the disjointness rule relaxed only for module 75 ranges and only for that class. verify.py check 7 currently pins one hash for module 75; it would need two (the transplant output and the post-patch result) plus reworded confinement tests. The real weakness is the standalone build: build_image.py in work/patches/vorbis_swap/ calls transplant.apply_transplant() directly and never reads the framework manifest, so a framework-side post class would leave the standalone image silently unpatched unless the same step were duplicated there. Two implementations of one 70-byte edit is how the two builds drift apart.

Option (b), folding the change into the transplant inputs, is not viable. The .ecpatch files are upstream artifacts from berettavexee/echo-mini-opus at a pinned commit, held outside the git repo and pinned by SHA-256 in DEPENDENCY.md precisely so the transplant's provenance is auditable. The transplant derives its surgery positions by diffing HIFIEC52.ecpatch against HIFIEC56.ecpatch and asserting that they land inside the freed regions. Editing either file falsifies its pin, breaks those assertions in uncontrolled ways (the cave addresses are not positions where the two files differ, so a diff-derived transplant has no way to express them), and hides a first-party change inside a third-party binary that other work also consumes. The change has to live in code this repo owns.

Option (c), a post-step inside transplant.py, is the recommendation. patched_module75() gains a final step, after the splice and before the hash is taken: a table of edits in the same expect-and-replace style the transplant already uses, each entry an offset inside the transplanted code region, the pinned transplant bytes expected there, and the detour or cave bytes to write. The step asserts the all-zero precondition in the cave range the same way it asserts the freed regions today, and the returned stats gain a line recording the edit count so build reports show it. Because both build paths call this one function (the framework's apply_transplants and the standalone build_image.py), the standalone and unified builds cannot diverge: they receive the same module bytes from the same code path, which is exactly the invariant check 7 already relies on.

Pin consequences under (c), all in one change:

- DEPENDENCY.md: the module75_patched.bin pin moves from 42c42796ad8f2e931c82db470cdaf754ca101a192834c11259a8bf05e787a3ca to dd8f772fb5c7fa128ed5bdfde99401cff66798847eb6c993feea89a0997ab695, the hash of the harness-built module in this report, provided the production post-step writes byte-identical edits (same sites, same caves at 0xDEE0, 0xDEF0, 0xDF00, 0xDF10, same encodings). If production chooses a different cave layout, the pin is whatever that build produces, re-measured at integration time; the harness number is the expected value, not a substitute for measuring the production artifact.
- DEPENDENCY.md also carries the standalone image pin (DP3_V137_vorbis.img, edfa4752...). That image changes because its module changes; it must be rebuilt and re-pinned in the same change. The two upstream .ecpatch pins do not change; the inputs are untouched, which is the point of this option.
- verify.py check 7: the pinned transplanted-module hash constant is replaced by the new module hash. Every other assertion in check 7 is unaffected: the edits are inside module 75, so the tests that the unified image equals the framework-only build outside module 75 and that the total diff is confined to the union of the parts both still hold, and the framework's disjointness refusal needs no relaxation because the manifest still never enters module 75.
- Framework README and root README unified-image pins change with the new build and are updated in the same change, as with every previous integration.
- The manifest does not change. build.py does not change.

Cost on device, for the record: three extra instructions per converted sample in the conversion loops (branch out, the bias add, branch back; the extraction itself is the original instruction moved, not duplicated), against a decode that spends thousands of instructions per sample elsewhere. Nothing in the harness suggests a timing risk; the armed-gapless work's warning stands that system-side behavior is only observable on hardware.

## Files in work/vorbis_rounding/

- probe.py, trace_conv.py: buffer discovery and the first-write trace.
- census.py, census_r.py, census_r0.py, census_seek.py: store-site censuses (steady state, first decode, post-seek, stock). census_patched_*.json, census_stock.json hold the results.
- verify_sites.py, verify_sites.json: the 42-sample register-level validation.
- build_round.py: builds module75_round_code.bin from module75_patched_code.bin with assertions.
- round_run.py: the primary seven-file proof. round_results.json and round_results_all.json hold the seven-file and 40-file numbers; outputs/ holds the fixed decodes.
- module75_round_code.bin: the modified code segment, harness scratch only.

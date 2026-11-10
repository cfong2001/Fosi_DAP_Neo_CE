# Is the Neo's stock Vorbis decoder (module 75) the low-precision build?

**Short answer: yes, proven, statically, byte for byte.** Module 75 is Xiph
Tremor (lowmem branch) built with `_LOW_ACCURACY_`, the same build
configuration berettavexee documented for the Snowsky Echo Mini's stock
firmware in `refs/echo-mini-opus` (docs/REPORT.md §19, docs/TREMOR_PORTING.md
§1). The precision is lost in the IMDCT: every trigonometric twiddle factor
and every window coefficient is stored as an 8-bit table entry instead of
a 32-bit one, so the transform multiplies 32-bit audio data by ~8-bit
coefficients. Measured effect (berettavexee's PC A/B of the identical mode):
38–43 dB SNR vs a floating-point decoder, roughly 7 effective bits,
where the same decoder at full accuracy reaches 60–84 dB.

All work offline against `DP3_V137.img`
(SHA-256 `fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`).
Reference tables were generated from Tremor lowmem @ `89a7534` (the exact
commit echo-mini-opus uses), cloned to `work/perf/tremor-lowmem/`; the search
script is `work/perf/table_search.py`.

---

## 1. What echo-mini-opus claims for the Echo Mini (step 1)

From `refs/echo-mini-opus/README.md`, "Full-precision Ogg Vorbis":

> "The stock Vorbis decoder is built in a **low-accuracy** mode: its output
> has roughly 7 effective bits, and the added noise may be audible in quiet
> passages and fade-outs. This project replaces it with the same decoder
> (Xiph's Tremor) at **full accuracy**…"

From `docs/REPORT.md` §19 ("The stock Ogg Vorbis decoder: Tremor 'lowmem' at
low accuracy"):

- Identification: Echo Mini module 77 (`codec_ogg`, 62.9 KB of code and
  53.6 KB of data) is Rockchip's Ogg Vorbis library; its 13 source files
  (`bitwise`, `codebook`, `dsp`, `floor0`, `floor1`, `floor_lookup`,
  `framing`, `info`, `mapping0`, `mdct`, `misc`, `res012`, `vorbisfile`) are
  exactly those of the lowmem branch of Tremor.
- Claimed build flag and claimed proof: "It is built with
  **`_LOW_ACCURACY_`**. Proof in the firmware: the 8-bit tables
  `sincos_lookup0` (1,026 B) and `sincos_lookup1` (1,024 B), which Tremor
  only produces in that mode, are present byte for byte in module 77's data
  (`0x1be5c` and `0x1c25e`)."
- Measured quality (Tremor lowmem built on PC both ways, vs ffmpeg's
  floating-point decoder, 16-bit PCM):

  | File | libvorbis (float) | Tremor full accuracy | Tremor `_LOW_ACCURACY_` |
  |---|---|---|---|
  | music, q5, 30 s | 84.6 dB | 78.5 dB | **43.3 dB** |
  | music, q8, 30 s | 66.6 dB | 60.4 dB | **38.4 dB** |
  | real album track, full | 89.8 dB | 83.9 dB | **41.4 dB** |

  "Low accuracy costs **20 to 40 dB of SNR**, i.e. about 7 effective bits
  instead of 13 to 14."
- Cost of the fix (their QEMU bench, REPORT §19 / TREMOR_PORTING §1): full
  accuracy is only +2.8 % instructions (27.1 M → 27.9 M per second of
  48 kHz audio) but the constants grow 13.7 KB → 44.3 KB ("Memory is the
  real constraint, not CPU").
- A second fingerprint (REPORT §25): the low-accuracy module contains "a
  single [smull/smlal]", the wide multiplies disappear in this mode, while
  the sibling AAC module (Helix) contains 88.

`docs/TREMOR_PORTING.md` §1 states the recognition method used below, in the
author's words: "Build Tremor once in each mode on a PC, dump these tables,
and search the firmware for them byte for byte."

## 2. The mechanism, from the Tremor lowmem source

`_LOW_ACCURACY_` is a compile-time switch in Tremor's `os_types.h`
(lowmem @ 89a7534):

```c
#ifdef _LOW_ACCURACY_
#  define X(n) (((((n)>>22)+1)>>1) - ((((n)>>22)+1)>>9))
#  define LOOKUP_T const unsigned char
#else
#  define X(n) (n)
#  define LOOKUP_T const ogg_int32_t
#endif
```

Consequences, stage by stage:

1. IMDCT twiddle factors: the main loss. `mdct_lookup.h` defines
   `sincos_lookup0[1026]` and `sincos_lookup1[1024]`, the {sin, cos} pairs
   the inverse MDCT butterflies multiply by, as `LOOKUP_T`. At full
   accuracy each entry is a 32-bit constant (4,104 B / 4,096 B); under
   `_LOW_ACCURACY_`, `X()` compresses each to ≈ its top 8 bits and the
   tables shrink to 1,026 B / 1,024 B of bytes. `mdct.c`'s butterflies
   (`presymmetry`, `mdct_butterfly_generic/first/8/16/32`,
   `mdct_bitreverse`) then compute the `XPROD31`/`XNPROD31` complex
   multiplies with those 8-bit coefficients. Twiddle quantization is
   multiplicative, signal-dependent noise at roughly −40 dB. This is the
   stage that produces the ~7-effective-bit output.
2. Window coefficients. `window_lookup.h`'s `vwin64`…`vwin8192`
   (the Vorbis overlap-add windows) are also `LOOKUP_T`, so they too are
   stored at 8-bit resolution (4,096 B total for `vwin8192` instead of
   16 KB).
3. Wide multiplies compiled out. `misc.h`/`asm_arm.h` guard the 64-bit
   `_V_WIDE_MATH` multiply path with `#if !defined(_LOW_ACCURACY_)`; in
   low-accuracy mode the hot path uses plain 32×32→32 `mul`/`mla` with the
   byte coefficients, hence the collapsed `smull`/`smlal` census (§3.3).
4. Secondary quantizations. `mdct.h`: the bit-reverse rotation
   constants `cPI1_8/2_8/3_8` become `0x00ed/0x00b5/0x0062` instead of
   `0x7641af3d/0x5a82799a/0x30fbc54d`. `floor_lookup.c`:
   `FLOOR_fromdB_LOOKUP[256]` is stored pre-divided via
   `XdB(n) = (((n)>>8)+1)>>1` and re-shifted `<<9` at use
   (`floor0.c: vorbis_fromdBlook_i`), quantizing floor-curve amplitudes to
   2⁻⁹ steps. `floor0.c`'s LSP/bark math uses narrowed multiplies
   (`((lsp[i]>>10)*0x517d)>>14` instead of `MULT32(lsp[i],0x517cc2)`).

Note what the loss is not: the PCM output interface stays 16-bit. The
noise is arithmetic, injected inside the IMDCT/windowing stage, which is
why berettavexee locates the audibility "in quiet passages and fade-outs"
(fixed-level quantization noise under a falling signal).

## 3. Fingerprint of the Neo's module 75 (step 2)

Module record (Phase 1 catalog, `work/catalog/module_catalog.json`):
code 62,936 B (0xF5D8) at exec 0x01000000, data 53,636 B (0xD184) at exec
0x01020000, reset vector 0x2749, initial SP 0x01022000.
Code SHA-256 `4ec93d972cbdd25e20d88f0125136d563ea028849bb6554161c57f01c9b5707a`;
data SHA-256 `32db67e0e8fd7825c545fdac310015b94370820d03602ed6905cb4a3401e87b2`.
Image file offsets: code 1,220,496; data 1,283,432.

Two size facts before any table work: 62,936 B code / 53,636 B data are
exactly the Echo Mini stock OGG module's sizes as reported by
berettavexee ("62.9 KB of code and 53.6 KB of data").

### 3.1 Table search: every Tremor table is present in its LOW form only

Reference tables were parsed from the Tremor lowmem @ 89a7534 source
initializers and expanded both ways (`X()`-quantized bytes for low mode,
32-bit LE for full mode; `XdB()` variant for the floor table). Searched
against all decoder modules 71–80, code and data. All eleven hits are in
module 75's data, all in LOW form, and no full-accuracy form of any of them
exists anywhere in module 75:

| Table | Form | Size | Data offset | VA | Image file offset |
|---|---|---|---|---|---|
| `vwin64` | LOW (8-bit) | 32 B | 0x9940 | 0x01029940 | 1,322,664 |
| `vwin128` | LOW | 64 B | 0x9960 | 0x01029960 | 1,322,696 |
| `vwin256` | LOW | 128 B | 0x99A0 | 0x010299A0 | 1,322,760 |
| `vwin512` | LOW | 256 B | 0x9A20 | 0x01029A20 | 1,322,888 |
| `vwin1024` | LOW | 512 B | 0x9B20 | 0x01029B20 | 1,323,144 |
| `vwin2048` | LOW | 1,024 B | 0x9D20 | 0x01029D20 | 1,323,656 |
| `vwin4096` | LOW | 2,048 B | 0xA120 | 0x0102A120 | 1,324,680 |
| `vwin8192` | LOW | 4,096 B | 0xA920 | 0x0102A920 | 1,326,728 |
| `FLOOR_fromdB_LOOKUP` | LOW (XdB) | 1,024 B | 0xB9A4 | 0x0102B9A4 | 1,330,948 |
| `sincos_lookup0` | LOW | 1,026 B | 0xC884 | 0x0102C884 | 1,334,764 |
| `sincos_lookup1` | LOW | 1,024 B | 0xCC86 | 0x0102CC86 | 1,335,686 |

The matched tables total 11,234 B in low form vs 41,864 B for their
full-accuracy equivalents, consistent with berettavexee's whole-library
constant totals (13.7 KB low / 44.3 KB full; the remainder is other const
tables not individually verified here).

Cross-check against the Echo Mini offsets: berettavexee places
`sincos_lookup0/1` at combined (code‖data) offsets `0x1be5c` / `0x1c25e` in
the Echo module. In Neo module 75: 0xF5D8 + 0xC884 = 0x1BE5C and
0xF5D8 + 0xCC86 = 0x1C25E. Identical to the byte.

Control result: the search does detect 32-bit tables when they exist.
Module 73 (AAC) contains a full-width 4,096 B trig table at code offset
0xD220 (a Helix table whose values coincide with `sincos_lookup1`'s full
form). Module 75 simply has no such full-width copy of any Tremor table.

### 3.2 The tables are live code inputs, consumed as bytes

Literal-pool words in module 75's code reference the table VAs:
`sincos_lookup0` from code offsets 0xA5A8 and 0xAAD8; `sincos_lookup1` from
0xAAE4; `vwin8192` from 0x4FE8; `FLOOR_fromdB_LOOKUP` from 0x5604, 0x6BB0,
0x6F88. Disassembling the block between the two sincos pools
(0xA5AC–0xAAD8, an MDCT butterfly cluster) shows the low-accuracy
`XPROD31` pattern directly: coefficients fetched with byte loads and
multiplied with narrow multiplies, no `smull`:

```
0x0100a5b2: ldrb.w r6, [ip]        ; T[0], trig coefficient, one byte
0x0100a5ba: ldrb.w r7, [ip, #1]    ; T[1]
0x0100a5be: mul    sl, sb, r6      ; x * T[0]
0x0100a5c6: mla    sl, r8, r7, sl  ; + y * T[1]
0x0100a5ca: mul    r6, r8, r6      ; y * T[0]
0x0100a5ce: mls    r6, sb, r7, r6  ; - x * T[1]
```

(`ip` walks the table; 26 `ldrb` in 455 instructions in this window,
5.7 % vs 2.0 % module-wide.)

### 3.3 Instruction-mix census

Capstone linear sweep (Thumb, skip-data) over each module's code image.
Counts are sweep approximations, but the contrast is the signal:

| Module | Decoder | `smull` | `smlal` | `umull` | `mul` | `mla` |
|---|---|---|---|---|---|---|
| 71 | MP3 (libMad) | 8 | 2 | 33 | 30 | 33 |
| 73 | AAC (Helix) | **85** | **3** | 14 | 15 | 42 |
| 75 | **OGG Vorbis** | **1** | **0** | 14 | 104 | 63 |
| 76 | FLAC | 2 | 0 | 17 | 4 | 29 |

Module 75 has exactly one `smull` and no `smlal`, the same census
berettavexee reports for the Echo Mini's low-accuracy Tremor ("a single one
in module 77"). And the Neo's AAC module sums to 88 `smull`+`smlal`,
exactly berettavexee's count for the sibling AAC module (their §25). Two
independent census coincidences across the two firmwares.

### 3.4 Strings / identity

Module 75's code contains `vorbis` (0x9998) and the Tremor/Rockchip debug
strings `floormemo need %d ` (0xA068) and ` partword_used size %d`
(0xBCE9); the Phase 1 catalog rated the identification "likely" only
because, unlike modules 71–73, it carries no source path or `Lib:` name.
The table evidence in §3.1 supersedes that: the identification as Tremor
is now proven (§5).

## 4. Comparison with the RKnanoD SDK (step 2, second half)

`refs/rknanod-sdk/Common/Codec/Audio/Ogg/` ships Rockchip's Vorbis decoder
as closed libraries plus headers. Three findings:

1. The SDK headers turn the mode on. `lib/ivorbiscodec.h` line 21 and
   `lib/os_types.h` line 20 both contain a literal
   `#define _LOW_ACCURACY_`. Rockchip distributes this decoder
   low-accuracy by default.
2. Both dated libraries contain the LOW tables byte for byte (same
   search as §3.1): `RkNanoD_BOGG_20151223.lib` (SHA-256
   `2ef4df56…`, `sincos_lookup0` LOW at file offset 0x8AD3A) and
   `RkNanoD_BOGG_20160901.lib` (SHA-256 `661c1b9b…`, at 0x90D8E), plus
   `sincos_lookup1`, `vwin2048`, `vwin8192`, `FLOOR_fromdB_LOOKUP`, all
   LOW, no FULL forms. Both also contain the `floormemo need` /
   `partword_used` strings found in module 75.
3. The member list is the Tremor lowmem file set:
   `ogg_bitwise.o, ogg_codebook.o, ogg_dsp.o, ogg_floor_lookup.o,
   ogg_floor0.o, ogg_floor1.o, ogg_framing.o, ogg_info.o, ogg_mapping0.o,
   ogg_mdct.o, ogg_misc.o, ogg_res012.o, ogg_vorbisfile.o`, the same 13
   files berettavexee lists for the Echo Mini module.

(The prebuilt `ogg_code.bin`/`ogg_data.bin` in the same folder, 378,249 B
/ 324,365 B, are not plain module-layout images; no Tremor table
signature was found in them and they are not used as evidence either way.)

So the Neo's module 75, the Echo Mini's module 77, and the SDK's BOGG
libraries are the same Rockchip Tremor build family, configured
`_LOW_ACCURACY_` at the source. This also explains *why*: the SDK ships
that way (TREMOR_PORTING §1: "vendors like to build it with
`_LOW_ACCURACY_` to save RAM and cycles", 30 KB of constants saved, at
~3 % CPU).

## 5. Verdict (step 4)

| # | Claim | Level | Basis |
|---|---|---|---|
| 1 | Module 75 is the OGG Vorbis decoder, and the library is Xiph Tremor (lowmem file set) | **proven** | 11 Tremor tables byte-for-byte (§3.1); Tremor-internal strings (§3.4); SDK lib member list identical to the identified file set (§4.3) |
| 2 | Module 75 is built with `_LOW_ACCURACY_`, the low-precision build | **proven** | All 11 signature tables present **only** in their 8-bit/XdB low forms (§3.1); the 1,026 B and 1,024 B byte sequences cannot be emitted by a full-accuracy build, whose tables are 32-bit; code consumes them via byte loads in the MDCT butterfly (§3.2); `smull` census = 1 (§3.3); SDK headers literally `#define _LOW_ACCURACY_` for this library (§4.1) |
| 3 | Mechanism: precision is lost in the IMDCT/windowing stage: 8-bit twiddle (`sincos_lookup0/1`) and window (`vwin*`) coefficients, wide multiplies compiled out, floor dB table pre-shifted | **proven** | Tremor lowmem source (§2) mapped onto the binary evidence (§3.1–3.3) |
| 4 | Same Rockchip library build as the Echo Mini's stock module 77 and the SDK BOGG libs | **strongly indicated** | Identical code/data sizes (62,936/53,636 B), identical sincos offsets (0x1BE5C/0x1C25E), identical `smull` censuses (1 for OGG; 88 for the AAC sibling), but the Echo stock image itself is not in `refs/` (only its patch diffs), so no direct byte diff was possible, and SDK `.o` sections were matched on tables/strings, not disassembled |
| 5 | Module 75's actual output measures ~38–43 dB SNR (≈ 7 effective bits) | **strongly indicated** | Berettavexee measured that range on PC builds of the identical mode and treated the sibling stock module as that mode (REPORT §19); not yet measured from the Neo module's own PCM output: §6 specifies the test that closes this |

Nothing material is left unproven except the direct PCM measurement in
claim 5. Claim 2, the question this task was asked to close, does not
depend on it: the author's own stated proof standard ("present byte for
byte") is met, at the author's own reported offsets.

Consequence for the fix (per echo-mini-opus's validated method):
replace the library inside module 75 with full-accuracy Tremor lowmem,
keeping the module runtime byte-for-byte. Budget from §3.1: the eleven
tables alone grow 11,234 B → 41,864 B (+30.6 KB); berettavexee fit the
sibling module by letting `.rodata` spill into the freed code area
(`ld --enable-non-contiguous-regions`). Echo-side validation showed the
full-accuracy build is bit-identical to PC Tremor and slightly *cheaper*
in instructions than the stock-like build once their Ogg layer replaced
`vorbisfile`.

## 6. Emulation: why it was not run, and the exact harness + protocol (step 3)

No tractable self-contained entry point exists. Module 75 is a
complete core-1 program, not a callable library: vector table at
0x01000000 (reset 0x01002749), its own runtime owns the main loop, file
access goes through the runtime's HifiFile client stubs over message-unit
channel 2, and decode commands arrive through the runtime mailbox. There
is no exported `ov_read`-style function that can be called without the
runtime, the parameter page, and a serving system core. Per the task's
bounding rule, the full harness was not stood up; the verdict in §5 does
not need it. What follows is the precise specification for running it
later (it remains the way to close claim 5 and to validate any
replacement decoder in-place, as echo-mini-opus did with its
`tools/emu77.py`).

### 6.1 Harness requirements

- CPU/memory map (Unicorn, ARMv7-M / Cortex-M3, Thumb): module code at
  0x01000000 (62,936 B); module data image at 0x01020000 (53,636 B);
  zero-filled BSS/work SRAM from 0x0102D184 to the end of the shared
  decoder window 0x01042000 (Phase 2); initial SP 0x01022000 (inside the
  runtime's data area, as on hardware).
- Boot: start at reset 0x01002748; first reproduce the system core's
  start sequence (Phase 2, `core1_loader_protocol.md`): the 144-byte
  parameter page written at 0x01020000 by reset-and-start `0x0306CB2C`,
  then the message-unit boot handshake on channel 0 (cmd 1 = ready,
  2 = query, 3 = reply, 4 = stop-class).
- Message unit @ 0x40110000: implement channel 2 (HifiFile RPC)
  server-side against a host file. Client blocks in the data window:
  Seek 0x01022254, Read 0x01022260, Write 0x0102226C; ready flag
  0x0102222C; status byte 0x01022298; commands Seek 0x69, Read 0x6B,
  Write 0x6D, Close 0x73, info 0x6F/0x71, reply = cmd + 1 (Phase 2).
  Sink channel 1 decoder-status messages; answer channel 3 value
  queries.
- Command path: drive the decoder command word 0x0102221C and control
  struct 0x01022290 through the OPEN → DECODE sequence. The command
  values (0–14) are mapped but their names/semantics are unproven.
  Recovering the exact OPEN sequence (from module 33's system-side
  sender) is the main remaining RE task for this harness.
- Peripheral stubs: DMAC2 @ 0x01070000, audio MMIO view @
  0x60082xxx, CRU @ 0x40180000 (FreqChange), UART/log output: accept
  writes, return quiescent status.
- PCM capture: the runtime reserves two 8 KB PCM buffers at the end
  of its file buffer and publishes their addresses through a small
  runtime structure inside the module's data (on the Echo sibling:
  struct at data VA 0x01029888–0x010298A0, buffers inside
  0x0102D4DC–0x010434DC). Every such address must be re-derived for
  Neo module 75. TREMOR_PORTING §2 documents a sibling-module trap
  (file-size word at 0x01022228 in their OGG module vs 0x01022224 in
  their WMA module). Find the Neo struct by locating runtime stores,
  then snapshot both buffers on each DECODE-complete event (512 stereo
  frames per call on the sibling) and append to an s16le stream.
- Adaptable reference: `refs/echo-mini-opus/tools/emu77.py` (and
  `emu74.py`), a Unicorn harness for the same runtime lineage on the
  sibling player; expect the mailbox/RPC plumbing to transfer and every
  runtime variable address to need re-derivation.

### 6.2 Test protocol (once the harness runs)

1. Test files (pinned encoder, e.g. libvorbis 1.3.7 via `oggenc`;
   record SHA-256 of each): (a) 48 kHz stereo music, q5, 30 s;
   (b) same source, q8; (c) a quiet-passage/fade-out file (where the
   noise is most audible); (d) a 96 kHz file (exercises `vwin8192`).
2. References on host: (a) ffmpeg floating-point decode → s16;
   (b) PC build of Tremor lowmem @ 89a7534 with `_LOW_ACCURACY_`;
   (c) same without, via a small `ivorbisfile` driver, s16 out.
3. Run module 75 under the harness on each file; capture the PCM
   stream per §6.1.
4. Score: align by cross-correlation (berettavexee's method used no
   offset), compute SNR = 10·log10( Σref² / Σ(ref−test)² ) against the
   ffmpeg reference over matched samples; report ENOB both as SNR/6.02
   and (SNR−1.76)/6.02.
5. Acceptance criteria: stock module 75 lands within ~1 dB of the PC
   low-accuracy build (expected 38–43 dB), closing claim 5 as proven;
   after a future full-accuracy library swap, the patched module must be
   bit-identical to reference (c) with `_ARM_ASSEM_` off (the
   sibling project's validation standard), landing in the 60–84 dB
   range against ffmpeg.

## Appendix: artifacts

- `work/perf/table_search.py`: table generation + search (rerunnable).
- `work/perf/tremor-lowmem/`: Tremor lowmem @ 89a7534 (gitlab.xiph.org).
- `work/perf/m75_code_strings.txt`, `work/perf/m75_data_strings.txt`:
  string dumps of module 75.
- `refs/echo-mini-opus/`: cloned for this task (BSD-3): README.md,
  docs/REPORT.md §19–§22/§25, docs/TREMOR_PORTING.md.
- Module binaries: `extracted/module_75_code_01000000.bin`,
  `extracted/module_75_data_01020000.bin`.

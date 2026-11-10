# Vorbis swap: full-precision Tremor in module 75 (transplant route, built and verified)

**Result: `DP3_V137_vorbis.img` is built** (this directory), via a module-level
transplant of berettavexee's validated Echo Mini surgery onto the Neo's module 75.
No source build was needed. In Unicorn emulation of the actual module bytes, the
stock decoder measures **45.1 dB SNR (~7.5 effective bits)** against a float
reference decode; the transplanted decoder measures **85.5 dB (~14.2 effective
bits)**, sample-accurate from the first frame. All offline verification passed;
the residual risks are hardware-only and listed in §6.

| Artifact | SHA-256 |
|---|---|
| Stock `DP3_V137.img` (unmodified) | `fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef` |
| **`DP3_V137_vorbis.img`** (this build, dated 2026-10-23) | `aed16842d8daa569d06efdc18cd9e7eb298a0129fd38fdb2cdabaa7ec72cd10a` |
| Stock module 75 (code+data) | `f8f68283eb2f3cd71f03f6d30d18f4cb2e7c55ac83c284ca39c6036e5e41d32e` |
| Patched module 75 (`module75_patched.bin`) | `42c42796ad8f2e931c82db470cdaf754ca101a192834c11259a8bf05e787a3ca` |

Sizes are unchanged by construction: module 75 stays 62,936 B code + 53,636 B data
(116,572 B), the image stays 13,631,492 B, the module table is untouched.

Credits/licences: the decoder surgery originates from
`refs/echo-mini-opus` (project code BSD-3-Clause; Tremor © Xiph.Org, BSD-style;
see its `LICENSES/tremor-COPYING`). This build redistributes nothing; it is an
offline analysis artifact like the rest of the patch program.

---

## 1. What the .ecpatch actually is (decision step 1)

`patch/*.ecpatch` is not a module and not a whole-module replacement. Format
`ECPATCH1` (their `apply_patch.py`): SHA-256 of the input image, SHA-256 of the
output image, output size, then records *(offset u32, length u32, new bytes)*,
a sparse binary diff against the **Echo Mini stock image `HIFIEC39.IMG`**
(33,554,436 B), which we do not have and did not need.

Per `docs/TREMOR_PORTING.md`, the Echo Vorbis change is in-module surgery:
the module's runtime (reset, mailbox ISRs, file layer, main loop) is kept byte
for byte; only the Tremor library inside it is replaced by a full-accuracy
Tremor build (lowmem @ 89a7534, no `_LOW_ACCURACY_`, `ECHO_NO_FLOOR0`,
`ECHO_HEAP_ALLOCA`, Tremor ARM asm + `ssat` clip in the HIFIEC56 build) plus a
streaming Ogg reader, linked into the regions the old library vacated
(`vorbis/port77/echomini77.ld`).

Isolating the surgery without the Echo image: `HIFIEC52` is "Opus only, stock
Vorbis"; `HIFIEC56` is "same Opus + full-precision Vorbis". Diffing the two
patches' byte maps, the positions attributable to the Vorbis surgery are:

- one contiguous region of 70,131 changed bytes: the module (below);
- 25 single bytes at ~0x1C880 stride in the resource area: the build marker
  digit (`[6]`→`[8]`) in each language copy of the "Format Not Supported!"
  string. Not module content; not transplanted;
- the header date byte and the trailer CRC. Not transplanted (we set our own).

Cross-check with `HIFIEC58` (56 + Ogg clock change): its additional diff vs 56
is 98 bytes: the date, the marker digits, the CRC, and one 104-byte cluster at
`0x4FBD8` (clock-profile table, main firmware). Nothing in the module. The
attribution is exact.

## 2. Why the transplant is clean: the two modules are the same build

The Echo's module 77 occupies image `[0x142284, 0x15E9E0)`. That base is not
assumed. It is solved from four independent anchors in the patch data, all
mutually consistent to the byte:

| Anchor | Observation | Implied base |
|---|---|---|
| First changed byte `0x144C54` | LD: library code starts at module offset `0x29D0` | code base `0x142284` |
| First data cluster `0x154CDC` | LD: data area D1 starts at data offset `0x3480` | data base `0x15185C` |
| Cluster start `0x15B0FC` | LD: data area D2 starts at data offset `0x98A0` | data base `0x15185C` |
| Contiguity | `0x142284 + 62,936 (code) = 0x15185C` | ✔ identical |

Against the Neo's module 75, every ABI element the surgery depends on matches:

- **Sizes**: 62,936 B code / 53,636 B data, identical (established earlier).
- **CodecFunc[CODEC_OGG]** at data offset `0xD16C` holds `0x000029D1` in the
  stock Neo module, the library entry at code offset `0x29D0` (Thumb bit set),
  exactly where the plug-in links its `VorbisCodec` (`.text.VorbisCodec` first
  in region T1). The pointer needs no change, and indeed the Echo patch has no
  record there.
- **The 24-byte runtime struct** at data `0x9888–0x98A0` (PCM buffer pointers,
  written by runtime code) is all-zero in the Neo image, sits untouched between
  the two freed data areas, and the surgery has no record inside it.
- **BSS anchors**: stock Neo code contains literal references to `0x010434E0`
  (the plug-in's BSS base in the Echo linker script) and `0x0105E998` (its BSS
  end / runtime event-flags boundary). The Neo stock library's BSS footprint is
  the same range.
- **Splice audit**: all 70,131 surgery bytes land inside the freed regions
  (code `[0x29D0, 0xE054)`; data `[0x3480, 0x9888)` ∪ `[0x98A0, 0xD148)`),
  with **zero violations**. Nothing touches runtime code `[0, 0x29D0)`, the struct,
  or the runtime variables at data `[0xD148, 0xD184)`. The Opus-only patch
  touches the module region zero times, confirming the region attribution.

The splice keeps **the Neo's own runtime bytes**. Only the library
regions are taken from the Echo build, and those were linked against the
documented per-module ABI (`opus/codec_abi.h` + port77 addresses), every point
of which checks out on the Neo module. Module numbering (75 vs 77) is a
main-core table entry, not module content, so it does not enter into this.

One deliberate non-goal: this build does not add Opus and does not
remove WMA (the Echo build sacrificed WMA to make room for Opus).
The Neo build keeps every stock codec; the only bytes that change
are inside module 75.

*Reconstructed 2026-10-31: the original text from this point to the
end of the document was lost to a truncation in this document's first
commit. Sections 3 to 6 are rewritten from the build artifacts in
this directory (`transplant.py`, `build_image.py`, `emu75.py`,
`splice_stats.json`, `DEPENDENCY.md`) and the recorded measurements.*

## 3. The splice

`transplant.py` does the work. `splice.py` is the exploratory original
that produced `splice_stats.json`; both implement the same audit.

1. Parse `HIFIEC52.ecpatch` and `HIFIEC56.ecpatch` into byte maps
   (absolute Echo image offset, new byte).
2. The surgery set is every position inside the Echo module 77 region
   `[0x142284, 0x142284 + 116,572)` where the two maps disagree.
   Positions where 56 matches 52 are Opus changes or shared build
   noise and drop out; the marker digits, header date, and CRC of §1
   fall outside the module region and drop out on the range test.
3. Each surgery position becomes a module offset and is checked
   against the freed regions (code `[0x29D0, 0xE054)`; data
   `[0x3480, 0x9888)` and `[0x98A0, 0xD148)`). The check is an
   assertion in the code, not a report after the fact. A byte outside
   the freed regions aborts the build.
4. The byte is written into the Neo module 75 segment at the same
   module offset. Runtime bytes are never a source or a target. They
   stay the Neo's own.

Result: 70,131 surgery positions, 0 violations (`splice_stats.json`).

Space accounting: the full-precision build's tables occupy 41,864 B
against 11,234 B of low-precision tables in the stock library. The
growth of 30,630 B fits because the regions the old library vacated
are larger than the library that replaces it. The module's total
size does not change (62,936 B code + 53,636 B data), and neither
does the image's.

## 4. Build and offline verification

`build_image.py` builds the standalone image (the pinned output in
the table at the top of this document):

1. It refuses any input whose SHA-256 is not the pinned stock hash.
2. It applies the transplant to module 75's code and data segments
   in place.
3. It stamps the header date 2026-10-23 (stock + 1, the framework's
   date discipline), mirrors the header, and regenerates the
   package CRC.
4. It runs `firmware_patch.validate()` on the result (layout,
   mirror, CRC).
5. It asserts diff confinement. Every byte that differs from stock
   lies in module 75's two regions, the header date and its mirror,
   or the trailer CRC. The count is 70,137 bytes: 70,131 surgery
   bytes plus 6 shared date, mirror, and CRC bytes. Zero outside.

Rebuilds are deterministic. `DEPENDENCY.md` pins the two input
patches and both output hashes, and the framework's verify suite
(check 7) reproduces the pinned patched-module hash `42c42796...`
inside the unified build, where the same transplant runs as a build
step alongside the framework patches.

## 5. Emulation: method and results

`emu75.py` runs the module bytes themselves under Unicorn, through
the module's own runtime file layer. It reproduces the decoder-core
memory map: code at 0, data at `0x01020000` copied from the image,
the runtime's BSS range zeroed, other RAM filled with garbage, an
8 KB stack watched by a watermark. Only the runtime's requests to
the main core are served from the host, out of a generated q5 Vorbis
test file. `CodecFunc[CODEC_OGG]` is called the way the runtime
calls it. The captured PCM is compared against an ffmpeg float
reference decode of the same file.

| Measurement | Stock module 75 | Transplanted |
|---|---|---|
| SNR vs float reference | 45.1 dB (~7.5 effective bits) | 85.5 dB (~14.2 effective bits) |
| Frame alignment | +512 samples | +0, sample-accurate from the first frame |

The transplanted decoder also passed the seek test sample-accurate,
and its stack high-water was 876 B of the 8 KB stack.

One bound, stated so the headline number is not overread: 85.5 dB
does not meet the 96 dB finish line in
`research/performance_maximization.md`. That line is defined
against a pinned corpus under the Phase D protocol, and one
generated file does not discharge it. What this test establishes is
the mechanism and the size of the gap. The stock module is the
low-precision build, the transplant is not, and the difference is
about 40 dB.

## 6. Residual risks (Phase E)

The remaining risks are hardware-only, as the introduction states.
Emulation cannot retire any of them.

- The real message-unit and DMA hand-off is unexercised, and so is
  interrupt timing. The harness serves the decoder's main-core
  requests itself and calls the codec the way the runtime does, but
  the hand-off, the DMA completion interrupts, and their timing on
  the Neo have never run this code. The mitigation is that the
  plug-in bytes are the same ones berettavexee validated on Echo
  hardware, and the Neo side of the interface is the stock runtime,
  kept byte for byte.
- Real-time margin under SD latency is unmeasured. Emulation says
  nothing about speed. On the Echo bench the plug-in measured about
  7% cheaper than the stock library it replaced, and the Neo runs
  OGG at 400-480 MHz stock (240 MHz with clock table v1), so
  headroom should exist. A slow card on real hardware is the test
  that settles it.
- Floor-0 files are rejected. The plug-in is built with
  `ECHO_NO_FLOOR0` (§1) and refuses Vorbis files that use floor 0,
  which stock accepts. No encoder since 2001 produces floor-0
  files, so the practical exposure is near zero, but the
  difference from stock is real and deliberate.
- Very long files and real albums are untested. The emulation ran
  one generated q5 file. Long files, chained Ogg streams, and real
  tag and cover albums from a real library have not been through
  the transplanted decoder, in emulation or otherwise.
- BSS clearing is inferred. The harness zeroes the BSS range the
  runtime clears (`0x0102D184-0x0105E9D4`). That the Neo loader
  clears exactly this range for module 75 follows from the loader
  RE (load flags 7 = code + data + BSS zero), not from watching
  module 75 load on hardware.
- A premise correction, recorded so later work does not inherit
  it: early notes sized the decoder data window at about 128 KiB.
  The observed map spans about 251 KiB from the data base
  (`0x01020000` to the BSS end at `0x0105E9D4`). The transplant
  reuses stock's exact code, data, and BSS windows, so its SRAM
  requirement is unchanged from stock. The correction matters for
  future decoder work that budgets SRAM from the old figure, not
  for this swap.
# Natural sort for the stock library: characterization, design, evidence

Target: DP3_V137.img (SHA-256 fcc1cd3e…), module 39 (library), exec base
0x0307d5fc, code length 138,928 (span ends 0x0309f4ac). All findings below
are from direct disassembly of the extracted module
(`extracted/module_39_code_0307d5fc.bin`) this session unless marked
otherwise.

## 1. What stock does today

**Records and the comparator.** The library's sorted insert (function
0x0307d6ea) is the *only* caller of the comparator at 0x0307d620 (BL
sites 0x0307d6fe, 0x0307d720, 0x0307d738) and always passes
`record_pointer + 4`. The comparator returns 0 (less) / 1 (equal) /
2 (greater). Relative to that +4 pointer it reads:

- four inline key units at +0x0/+0x2/+0x4/+0x6 (record offsets
  +0x4..+0xa), compared in order;
- if those tie and unit 3 is nonzero, both full strings, read as
  0x100 bytes (128 UTF-16 units) through module-0 function 0x03067510
  into the cached buffers at 0x0307f28c / 0x0307f38c (cache slots in the
  state struct at 0x0307e1ec, +8/+0xc; list heads at +0/+4), compared
  **raw**: no case fold, no accent fold at compare time.

String address formula, from the comparator's own code:
`(([0x0302329c] + data[1]) << 9) + (idx << 11) + data[0]`, where `data`
is the 8 bytes at 0x030247ec and `idx` is the string index stored at
record offset +0xc.

> **Correction to `analysis/library_m3u.md`:** the fields it describes at
> comparator offsets +0/+2 as category fields are key units 0 and 1.
> The comparator compares no category fields anywhere: four key units,
> then the full strings.

**The key builders.** Two builder functions write the inline prefix:
A = 0x0307d80a and B = 0x0307d8c4 (B has two scan paths, hence three
fold loops in total). Each builder first stores the full-string index
at record+0xc, then runs a 4-character loop that stores units at
record +4/+6/+8/+0xa, folding **ASCII a–z → A–Z only**, inline per
character. The three loops are each exactly 0x30 bytes:

| loop | address | record reg | loop exit |
|---|---|---|---|
| A | 0x0307d87e | r5 | 0x0307d8ae |
| B main | 0x0307d954 | r4 | 0x0307d984 |
| B alt | 0x0307d9f2 | r4 | 0x0307da22 |

**Net stock ordering.** Prefix = first 4 characters, ASCII-uppercased.
Beyond that: the full-string tiebreak is case- and accent-sensitive raw
code points. No leading-"The " handling. Numbers compare as raw code
points, so "Track 10" sorts before "Track 2". Accented initials sort by
their raw code point (É after Z).

## 2. Design

**Transform T** (the ordering, defined once in `host_ref.py` and shared
verbatim with the device build): over the name's UTF-16 units:

1. trim leading/trailing U+0020;
2. strip one leading article "The " (matched on folded units T,H,E plus
   a space, requires further content; further spaces are skipped);
3. fold each unit: ASCII a–z → A–Z; Latin-1 letters (U+00C0–U+00FF) →
   base uppercase via a 64-entry table generated from the same mapping
   as the host reference, including expansions Æ→AE, ß→SS, Œ/œ→OE;
   combining marks U+0300–U+036F are dropped; everything else is
   identity (Ð/Þ stay, matching NFKD);
4. a run of ASCII digits becomes a token `[0x0001, n, d1…dn]` where
   n = significant-digit count (leading zeros stripped; an all-zero
   run is one '0'). The marker unit 0x0001 sorts digit tokens after
   end-of-string and before every letter, shorter-n first (numeric
   order), then digit by digit.

T's rules are EchoPod's library sort (casefold + accent-strip +
leading-"The ") plus the natural-number tokens, which EchoPod does not
have. Those are ours. One brief-supplied example vector was backwards
under these rules and the suite asserts the correct direction:
"The Beatles" vs "Beach House" → keys BEATLES vs BEACH HOUSE differ
first at unit 3, 'T' (0x54) > 'C' (0x43), so **Beach House sorts
first**.

**Why both builders and comparator are patched.** A 4-unit prefix
transform alone cannot be self-consistent: whether "The " is stripped,
and how a digit run tokenizes, can depend on characters past the
window, so a prefix-only comparator would order some pairs differently
from the full-string order it falls back to. Instead:

- **Builders** (patches 0027–0029) replace each 0x30-byte fold loop
  with `mov r0, <record reg>` / `bl cave_pfx` / `b.w <stock loop exit>`
  / NOP padding. `cave_pfx` reads the record's *full* name (index at
  record+0xc, the comparator's own address formula and 0x03067510 read)
  and writes the true first 4 T units to record+4..+0xa. It uses
  comparator buffer A (0x0307f28c) as scratch and invalidates both
  comparator cache slots (state+8/+0xc ← 0xFFFFFFFF) before
  returning, so the comparator can never serve a stale string out of
  the borrowed buffer.
- **Comparator** (patch 0026) replaces the 4-byte entry at 0x0307d620
  with `b.w cave_cmp`, preserving the exact 0/1/2 contract.
  `cave_cmp` walks the 4 inline units with token awareness: a plain
  unit difference decides immediately; end-of-string decides; but a
  digit MARK unit on either side, or a 4-unit tie, defers to the full
  phase: stock-identical string reads and cache, ending in
  `sk_tcmp`, a generator-based compare of the two full T sequences.

Because the prefix is a true prefix of T and the comparator defers in
exactly the ambiguous cases, the device order is identical to ordering
by T alone. That equality is a fuzz-proven property of the host model
(4,000 random pairs, seed 20261031) and is what the Unicorn
differential test checks on the device side (emulated prefix +
emulated `sk_tcmp` == host `device_cmp`).

**Code cave.** Module 39's real code ends at 0x0307e1ec; the rest of
its span is zeros in the image. The region at 0x0307e28c is referenced
by module 39 itself (unsafe). Chosen cave: **0x0309f000..0x0309f4ac
(1,196 bytes)**. An overlap scan over all 82 modules' code/data/bss
spans showed only module 39's own code covers it, and the stock bytes
are all zero (pinned by patch 0030's `expect`). The blob is 1,052
bytes: cave_cmp 0x0309f000, cave_pfx 0x0309f0b6, sk_str_addr
0x0309f102, sk_tcmp 0x0309f126, sk_pfx4 0x0309f17c, gen_init
0x0309f1a6, gen_next 0x0309f25a, sk_fold 0x0309f32a, fold table
0x0309f39c (128 bytes). Technique (hook + cave discipline) follows the
nanitecfw library rewrite; the transform rules follow EchoPod's sort
key, reimplemented here for UTF-16.

## 3. Implementation

- `host_ref.py` is the semantic source of truth: `fold_unit()`, `gen_units()`
  (= T), `tcmp()`, `pfx4()`, and `device_cmp()`, the composition the
  device implements. `FOLD_TABLE_BYTES` is generated from the same
  mapping the device table uses. One mapping, two consumers.
- `sortkey_asm.py` is a two-pass mini-assembler producing `cave.bin` +
  `cave_listing.txt`. No arm-none-eabi-gcc or keystone exists in this
  environment; it shells out per instruction to rz-asm
  (tools-local/bin/rz-asm) and iterates label addresses to convergence.
- `gen_patches.py` emits the five `.patch` files; `expect` bytes are
  sliced from the extracted stock module (no hand transcription),
  hook branch encodings are assembled at the exact site addresses.
- `test_vectors.py` is the host suite. `unicorn_diff_test.py` is the device
  differential test.

**Toolchain gotcha worth keeping:** this rz-asm build silently encodes
`cmp r12, #imm` (and `cmp ip, #imm`) as `cmp r4, #imm` (the register
number is truncated to 3 bits, r12→r4, r8→r0) instead of erroring or
choosing the wide encoding. Every r12 immediate compare in the cave is
therefore written `cmp.w r12, #imm`. A full-blob audit (capstone
decode vs source, checking every named high register survives)
reports 0 issues.

**Bugs the Unicorn test caught and fixed, in order:**

1. gen_init/gen_next are non-leaf (both call sk_fold) but returned with
   `bx lr` → infinite loop. Fixed with push {lr} / pop {pc}.
2. gen_init kept its string base in r12 across `bl sk_fold`, which
   clobbers r12 → unmapped read at 0xffffff96. Fixed by reloading the
   base from the state struct before each article peek.
3. The rz-asm `cmp r12, #imm` truncation above → wrong range check in
   every fold path (sk_fold returned É for é and never folded in
   situ). Fixed with `cmp.w` at all seven sites.

## 4. Verification

- **Host suite** (`test_vectors.py`): all vectors pass, 0 failures:
  named cases (article, case variants equal-fold, é→e, leading zeros,
  mixed), antisymmetry over the corpus, and the 4,000-pair
  prefix/full consistency fuzz.
- **Unicorn differential** (`unicorn_diff_test.py`): emulated
  `sk_tcmp` and `sk_pfx4` vs the host model over 349 names (named
  vectors + 300 random, buffers garbage-filled past the NUL like real
  flash slots): **0 failures** (final run, 1,052-byte blob).
- **Encoding audit**: full-blob capstone-vs-source high-register
  audit, 0 issues.
- **Framework builds** (scratch copy at `build_test/framework/`; the
  real framework tree was not modified):
  - Isolated (0000 + 0026–0030, --no-transplants): build OK,
    validate() passes, image SHA-256
    d02ded2c8560ba77fc07bc21b23ee1b64098f6d2455b83e1247b43dd25243c2d.
    Independent byte diff vs stock: 1,049 bytes in 148 ranges, **zero
    stray ranges**. The diff is exactly the five patch sites plus
    header date (0x2), its mirror (0xc94002) and the trailer CRC
    (0xd00000..0xd00003). All four hook sites and the cave entry
    disassemble from the built image as designed.
  - Unified (live manifest incl. DAC fix, clock v1, gapless 0020–0025,
    plus 0026–0030, with the Vorbis transplant): build OK, 30 patches
    applied, no transplant/byte-patch overlap; all five sort-keys
    payloads present at their exec addresses in the output image.
  - `tools/check_patch_files.py`: 31 patch files parse, 30 manifest
    entries OK.
  - `verify.py` (scratch copy; logs at `build_test/verify_run2.log`
    and `control_test/verify_control.log`): **6/7 checks pass**,
    including check 7 (unified == framework-only outside module 75,
    module 75 == pinned transplant hash, diff confined to the union
    of parts, two builds byte-identical; unified diff 71,514 bytes =
    70,471 control + 1,049 sort-keys − 6 shared). The one failure is
    verify.py's own bookkeeping: the "shipped manifest build" check
    hard-codes the pre-sort-keys manifest (25 patches, known
    340-byte diff) and now correctly observes 30 patches and 1,383
    framework-only bytes. And 340 + 1,049 − 6 shared = 1,383
    exactly, i.e. the combined diff is precisely the disjoint union
    it should be; the check's constants need the same update they
    got when the gapless series landed, which is the coordinator's
    integration step. A pristine-framework control under identical
    scratch conditions passes 7/7 and reproduces the coordinator's
    current unified image (SHA-256 8a2de9b3…) byte-for-byte, which
    pins the scratch setup itself as sound. (Two earlier scratch
    runs showed transient check-7 anomalies, a sub-build crash,
    then a missing intermediate file; neither reproduced in the
    control or the clean rerun.)
- **Original image untouched**: SHA-256 re-verified after all builds,
  still fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef.

Patch numbering: the series is filed as **0026–0030** to follow the
live manifest tail. The gapless series took 0020–0025 while this work
was in flight (the first draft used 0019–0023; content is unchanged,
the isolated build is byte-identical under both numberings).

## 5. Residual risks

- `cave_cmp` / `cave_pfx` were not executed end-to-end under Unicorn:
  they call the module-0 read (0x03067510) and touch live library
  state. Their decision logic is the differentially-tested host model,
  every routine they call internally is differentially tested, and
  the stock paths they mirror were verified by disassembly. But the
  first on-device smoke test should still page through a library with
  articles, accents and numbered tracks.
- Comparator stack usage grows by roughly 104 bytes (two 28-byte
  generator states plus saved registers). Bounded and small, but the
  real task stack headroom is only measurable on hardware.
- A digit run with more than ~125 significant digits inside the
  128-unit read window compares on its visible prefix, the same
  bound stock's own buffer imposes on its full-string compare.
- Buffer-A scratch reuse is safe only because every builder hook
  invalidates the comparator cache. The three hooked loops are the
  only prefix writers found in module 39; a future patch that writes
  prefixes elsewhere must keep the same discipline.

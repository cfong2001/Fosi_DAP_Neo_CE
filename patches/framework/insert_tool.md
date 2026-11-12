# Insertion rebuild tool: growing a module segment inside the package

`insert_rebuild.py` is the package insertion-rebuild tool named as the
missing proof for overlay segment extension in
`analysis/resident_home/resident_home.md` (Candidate 2). The loader
(0x0306777A) copies exactly `code_len` / `data_len` bytes from each module
record's storage offset, so growing a segment is mechanically safe for the
loader. What stock tooling could not do is the file side: every module
payload in DP3_V137.img sits back to back, so a longer segment requires
inserting bytes into the package and shifting every later payload. This
tool performs that rebuild and recomputes every dependent offset. It is
offline, standard library only, and never writes to its input.

Usage:

```
insert_rebuild.py DP3_V137.img --output out.img --module 31 \
    --segment code --payload blob.bin
```

The Python API (`apply_insertions`) accepts a list of
`(module, segment, payload)` tuples and applies them in order. The
tool was developed and gated against a scratch copy of the patch
framework, then integrated into the framework itself as the `--grow`
step (`tools/insert_rebuild.py`, with `tools/validate_grown.py` for
validation); verify.py check 9 carries the gate-2 isolation battery
as a standing check.

## Layout facts the rebuild rests on

* 82 module records of 32 bytes start at file 0x208. The record fields are
  `code_load, code_exec, code_len, data_load, data_exec, data_len,
  bss_exec, bss_len` (all u32 LE).
* Storage address and file offset differ by a constant:
  `load - file_offset = 50,658,816` for every segment, verified against
  all entries in the repo extractor's own manifest
  (`extracted/manifest.json`). Equivalently, file offset =
  `load - load_base + 0x200` with `load_base = 0x03050000` stored at file
  0x200. This matches the format documentation in nanitecfw's
  `rknano_fw.py` (MIT).
* Payloads are back to back from file 0xE6C to 0x16FB20, with occasional
  1 to 3 byte gaps and one 16,384-byte gap after module 0's code segment.
  The tool treats gap bytes as ordinary stream bytes: an insertion at the
  end of a segment goes before the gap that followed it, and all later
  bytes, gaps included, shift by the payload size.
* Resource sections (sysdefault, font_a, font_b, codepage, lang, images)
  follow the payload area. Their header offset fields are absolute file
  offsets; offsets inside the sections are section-relative (the repo
  inspector reads image-resource and language offsets relative to the
  section start), so section contents need no edits.
* A copy of the first 0x200 header bytes sits at the offset stored in the
  u32 at file 0x1F4 (0xC94000 in stock). The copy is exactly 0x200 bytes,
  so it contains no module records: the first record is at 0x208, past the
  end of the copied range. What must stay consistent inside the copy is
  the section offset fields and the 0x1F4 field itself, which the tool
  guarantees by updating the primary header first and then re-syncing the
  copy from it, the same order `firmware_patch.py` uses.
* The trailer is the last 4 bytes: Rockchip CRC-32 (poly 0x04C10DB7,
  MSB-first, init 0, no final XOR) over everything before it. The zeroed
  regions after the images section (0xC92E10 to 0xC94000 and 0xC94200 to
  0xD00000 in stock) hold no offsets and shift positionally.

## Mirror alignment (added after the gates)

`apply_insertions` ends with `align_mirror`: it pads zeros before the
duplicate header until its offset is a multiple of 512, because the boot
validator (module 1, `0x0307E2CA`) reads the mirror at sector
`(u32 @ 0x1F4) >> 9` and compares the whole sector. The gate results
below predate this step and describe unpadded images; a 1,000-byte
growth now adds 1,024 bytes. `tools/validate_grown.py` refuses an
unaligned mirror or one past `0xCFBE00`.

## Dependent-offset map

For an insertion of `n` bytes at the end of segment S, with storage
insertion address `A = S.load + S.len` and file insertion position
`p = A - load_base + 0x200`:

| Field | Location | Rule |
|---|---|---|
| Grown segment length | record of S, `code_len` or `data_len` word | `+= n` |
| Any segment storage address | `code_load` / `data_load` words of all 82 records | `+= n` if the value is `>= A`, except S's own grown-segment start, which does not move. This includes S's other segment (it sits after the grown one when back to back) and zero-length records whose load value aliases moved content |
| Section offsets | header words at 0x70, 0x78, 0x80, 0xCC, 0xF8, 0x14C | `+= n` if the value is `>= p` |
| Section lengths | header words at 0x7C, 0x84, 0xD0, 0xFC, 0x150 | unchanged; content lengths do not change |
| Sysdefault length word | header word at 0x74 | unchanged; it is a sector count (2 in stock), not a byte length. (The repo inspector derives a byte length as font_a offset minus sysdefault offset; for an insertion into module 80's data, which starts after sysdefault's offset, that derived span grows while the stored sector count and the section's own 0x200 bytes do not move) |
| Duplicate-header offset | header word at 0x1F4 | `+= n` (every module insertion point is before it) |
| Duplicate header contents | 0x200 bytes at the new 0x1F4 value | overwritten with the updated first 0x200 header bytes |
| Trailer CRC | last 4 bytes of the file | regenerated over the whole rebuilt image |
| Header date bytes | file 0x00 to 0x04 | never written by this tool. Date stamping belongs to the framework build, with its slot policy |
| Exec and BSS fields | `code_exec`, `data_exec`, `bss_exec`, `bss_len` in all records | unchanged. Appended bytes land at exec address (old exec + old len) of the grown segment, and every pre-existing byte keeps its exec address |
| Load base and module count | header words at 0x200, 0x204 | unchanged |
| Header words holding 0x200 | file 0x54, 0x5C, 0x64, 0x6C | unchanged. They behave as size constants; under an offset reading they would point at 0x200, before every insertion position, so they would not shift either way |
| Section contents, inter-segment gaps, trailing zero regions | rest of the file | no field edits; they shift positionally with the byte stream |

One refusal: a segment whose load value is 0 has no storage position
(modules 63 to 69 carry `data_load = 0` with `data_len = 0`) and cannot
be grown. Growing a zero-length segment that does carry a load value is
allowed; its payload is inserted at that storage address and the
positional rules above keep every record consistent.

## Gate results

All gates are scripted in `run_gates.py` and were run against the stock
image (SHA-256
`fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`,
re-verified unchanged after the runs). Results are recorded in
`out/gate_results.json`; rebuilt images are in `out/`.

### Gate 1: zero-length insertion is the identity

Zero-length insertions into module 0 code, module 31 code, module 81
code, module 31 data, and module 63 code each reproduce the stock image
byte for byte, including the trailer CRC. The header-copy re-sync and CRC
regeneration are identities on a well-formed input, so no byte needed an
exception and there is no field that cannot be reproduced.

### Gate 2: 1,000-byte insertion into module 31 code

The payload is a deterministic 1,000-byte pattern. Re-extracting all 82
modules from the rebuilt image with the repo extractor
(`rknano_image.Image.extract`) and comparing against the stock extraction
shows 81 modules byte-identical; module 31's code is the stock bytes plus
the pattern at the tail, and its record's `code_len` grew by exactly
1,000 (7,396 to 8,396). All exec and BSS record fields in all 82 records
are unchanged, the header date bytes are preserved, and the header mirror
and trailer CRC validate. Rebuilt image SHA-256:
`5bc467d280e588f714746699f2e4e721638d6d476f367815c579fa2c055ffca8`.

One result needs stating precisely. `firmware_patch.validate()` passes on
the stock image and refuses the rebuilt image with
"input is not a V137-layout update package". The refusal comes from two
hard-coded stock-layout constants in `repo/tools/firmware_patch.py`
(`len(raw) != 0xd00004` and `im.u32(0x1f4) != 0xc94000`): any correctly
grown image violates both by construction. The structural checks that
`validate()` performs before that line, header mirror and trailer CRC via
`Image.summary()`, pass on the rebuilt image. To show the full validator
shape passes, `tools/validate_grown.py` (beside the tool in the framework) keeps every
structural check in `validate()` (mirror, CRC, module count, all module
regions and sections inside the image) and derives the length
expectations from the image itself; it passes on every rebuilt image in
these gates. As an independent cross-check, nanitecfw's `rknano_fw.py`
also parses the gate 2 image and reports header copy OK, CRC OK,
`fw_len = 0xC943E8` (stock 0xC94000 plus 1,000), and module 31
`code_len = 8,396`.

### Gate 3: late and early modules, and a data segment

The same check battery (all segments compared, all record fields
accounted for, mirror and CRC valid, generalized validator passing,
header date preserved) passes for:

* module 81 code, +777 bytes (a late module, near the end of the record
  order but mid-package in storage order);
* module 0 code, +1,000 bytes, where module 0's own data segment shifts
  across the 16,384-byte gap that follows its code;
* module 31 data, +333 bytes (a data segment, not code).

The shifting logic works from the storage layout, not from the module's
position in the table, and is not special-cased.

### Gate 4: composition

Two sequential insertions (module 31 code +1,000, then module 81 code
+700) equal one combined insertion byte for byte. The result is also
independent of insertion order, and two insertions into the same segment
equal one insertion of the concatenated payload. `apply_insertions`
recomputes the layout after each insertion, so composition holds by
construction and is now also demonstrated.

## Framework integration (as built)

Add a growth step to `patches/framework/build.py`:

* New options: `--grow MODULE:SEGMENT:PATH`, repeatable (for example
  `--grow 31:code:parser_blob.bin`). The step runs first after the input
  SHA-256 gate, on the pristine stock image, and reuses
  `insert_rebuild.apply_insertions`. The existing byte patches and the
  transplant then address the grown image through `Image.module_region`,
  which already resolves file offsets from the records, so no patch file
  changes are needed. Date stamping, header mirror sync, and CRC
  regeneration stay where they are, at the end of the build.
* `firmware_patch.validate()` needs the generalization demonstrated in
  `tools/validate_grown.py`: keep the mirror, CRC, and
  count checks, drop the two stock-size constants, and check that the
  duplicate-header offset and every module region lie inside the image.
  Until that lands, a growth build cannot pass the framework's own final
  validation, which is the correct failure mode.
* The build report gains a `growth` list (module, segment, payload size,
  payload SHA-256) alongside `patches_applied` and
  `transplants_applied`.
* New verify check, grown-segment isolation: for a build with growth,
  rebuild with growth alone and extract every segment from the stock and
  grown images; assert byte equality outside the grown modules, tail
  equality (stock bytes plus exactly the blob) inside them, and
  `code_len`/`data_len` deltas equal to the blob sizes. This is the
  `check_insertion` battery in `run_gates.py`, promoted into the suite.

With this tool, Candidate 2's first missing proof (the insertion rebuild)
is supplied. The second missing proof is unchanged: one hardware soak of
a grown module 31 across the window cycle, as specified in
`resident_home.md`.

## Files

* `insert_rebuild.py`: the tool (CLI and `apply_insertions` API).
* `run_gates.py`: the four gates, self-checking, writes
  `out/gate_results.json`.
* `out/`: rebuilt gate images and the gate 2 payload pattern.
* The development scratch tree (not in the repo): a copy of the patch framework, plus
  `tools/validate_grown.py`, the layout-generalized validator used by
  gates 2 and 3.

# M3U completion workstream: walker trace, region-extension build step, parser placement, device bridge

Worked offline against stock `DP3_V137.img` (SHA-256
`fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`,
verified before and after; the image and the live framework files
were not modified; everything here lives under
`work/m3u_bridge/`). Evidence disassemblies are in `evidence/`
(`mod31_full.txt`, `mod37_full.txt`, `mod38_scan_main.txt`,
`mod33_full.txt`). The disassembly helper is `scratch/fwdis2.py`.

Status per job: **Job 1 proven** (the drafted gate patch is refuted;
v2 scan-time recognition needs a different mechanism, named).
**Job 2 built and verified** (scratch framework check 8 passes).
**Job 3 blocked on the toolchain** (no ARM C compiler on the box;
host-section estimate reproduced). **Job 4: the hook is fully pinned
and patch 0040 is emitted with scratch-build evidence; the bridge
source is written against the pinned primitives, with five named
blockers (B1–B5) where the evidence stops.**

---

## Job 1: walker trace: how the extension-gate tables are consumed

### The bound is the content: zero-entry termination, no count anywhere

The extension classifier is a separate module 0 function,
**0x0305A15C**, called once from the walker at 0x0305A752. Its loop,
from the disassembly:

- r0 = pointer to the current entry name's extension (3 bytes at
  the dirent), r1 = table pointer, r2 = dirent attribute flags.
- First table byte `0x2A` (`*`) → immediate match (return 1),
  skipping even the attribute test.
- First table byte `0` → no match (return 0).
- Compare 3 bytes; on mismatch, `ldrb ip, [r1, #3]!` advances
  exactly 3 bytes and tests the next entry's first byte.

So the tables are arrays of 3-byte codes **terminated by an entry
whose first byte is 0**. There is no count, length, or end pointer
in the classifier, the walker (0x0305A2F0), or the wrapper
(0x0305A970). The wrapper builds a stack parameter block
(`strd` at 0x0305A98C: {param_block_ptr, 3, mode}), passes the table
pointer through to the walker in r3, and calls the walker with
r1 = 1. In the walker, stack arguments are the parameter block
(r7), the class 3 (sb), and a mode/source selector (sl; values 1/2
take special dereferenced paths, other values including 6 fall
through to the enumeration path at 0x0305A682 that calls the
classifier). Every consumer therefore trusts table memory to
contain a zero-first-byte entry at or after the last real code.
Whoever copies a table to the stack owns the bytes after it.

### Module 38's copy: contiguous, and the byte after it is a live pointer

The scan main is module 38's function at 0x0307E53A
(`evidence/mod38_scan_main.txt`). The table at exec 0x0307E6CC
holds the 14 stock codes plus `CUE` (15 entries, 45 bytes), then 3
NUL bytes at 0x0307E6F9..0x0307E6FB, then the literal pool (first
word 0x0302329C, verified in the image). The copy at
0x0307E55E..0x0307E594 is an LDM/STM sequence storing **exactly 48
bytes** to sp+0x5D8..sp+0x607; fp is set to sp+0x5D8 (0x0307E5F2)
and the wrapper calls at 0x0307E63E and 0x0307E7B6 pass r2 = fp.

The word at **sp+0x608** (the first word past the copy) is a
**live runtime pointer**: stored at 0x0307E5FA from [0x0302329C],
with derivatives (+0x8000, +0x10000, +0x12000) stored at sp+0x620,
sp+0x5B4, sp+0x63C, and the word itself **read at 0x0307E7E4** as r1
into a call to 0x03067912 with r2 = 8. Its low byte is not
statically provable as 0.

### Verdict on the drafted gate patch pair: REFUTED as drafted

- Drafted patch (i) (module 38 @0x0307E6F9: `000000` → `4D3355`
  "M3U") would make "M3U" the 16th entry, and the walker would
  then test a 17th entry starting at sp+0x608, the live pointer
  word. Unless that word's low byte happens to be 0 at runtime,
  the classifier compares garbage and can false-match or walk
  further into stack memory. Unsafe, unconditionally.
- The one-byte rescue (make the 0x0307E5FA store write 0 instead,
  r6 is the function's zero register there) is **unsafe**: sp+0x608
  is genuinely read at 0x0307E7E4, and r6 is rewritten at 0x0307E6C4
  before the wrapper calls anyway.
- Drafted patch (ii) (extend the copy 48 → 52 bytes) is
  **impossible at this destination**: destination bytes +48..+51
  are that same live word, and the source bytes at table+48.. are
  literal pool (`9C 32 02 03` = 0x0302329C), copying them would
  corrupt the live variable and still not terminate the table.

**v2 scan-time recognition is therefore blocked on a frame-layout
change**, not on a byte patch: relocate the table copy to a frame
slot with 4 provably dead bytes after it (or build the table
somewhere with room for M3U + terminator), which requires a full
frame audit of the scan main plus a trace of 0x03059F58 (the
node-array/dir-context initializer with 56-byte stride arithmetic
that receives the table pointer in sb, called by module 38 at
0x0307E618 with r0 = fp, r1 = 6; in the range examined it does not
walk 3-byte entries, so the classifier remains the only table
walker, but its full contract is part of the same audit). **No
gate patch files were emitted. That is the finding, not an
omission.**

### The v1 browser path: why .m3u lists, and the hook sees it

Module 31's enumerator calls the same wrapper at 0x0307D2B2, and
module 31 carries its own 44-byte copy of the 14-code table (inside
the node-action function itself, 0x0307DEBC..0x0307DEE2: 42 bytes of
codes + 2 NULs, it cannot take M3U + terminator under any bound
either). The folder browser nevertheless lists non-audio files:
the design's §3.1 evidence (TEXT/OTHER classes in the stock icon
set, nodes carrying a class byte at +0x4E that is not an audio
class) stands, and this session's trace of the node-action
function confirms the rest of the chain: the function classifies
the **selected** node via the byte at node +0x4E (read at
0x0307DF06) and dispatches at 0x0307DF1A regardless of which class
the node has. A `.m3u` node selected in the browser reaches the
hook site with its 8.3 name at node +0x4F. The hook tests the name,
not the class, which is why v1 does not need the browser gate
opened.

---

## Job 2: region-extension build step (built, verified)

Implemented in the scratch framework at `framework_ext/` (full
replacement `build.py` + `verify.py`; the `patches/` copy is
unchanged from the live framework). Live files were not touched.

`build.py` changes:

- New constants: `EXT_FILE_OFF = 0x532C0`, `EXT_EXEC =
  0x03079C14`, `EXT_MAX = 0x2B9C` (11,164), `EXT_RECORD_OFF =
  0x210`, `MOD0_CODE_LEN_STOCK = 0x29C14`. Mechanics pre-verified
  against `extracted/manifest.json` and the image: module 0 code at
  file 0x296AC, len 0x29C14; data at file 0x572C0; the gap is
  exactly 0x4000 zero bytes at 0x532C0; the header record's u32 at
  file 0x210 is 0x29C14; the header mirror at 0xC94000 duplicates
  only the first 0x202 bytes, so the module table (record at
  0x210) exists exactly once. The edit needs no mirror twin.
- `apply_extension(raw, blob, claimed_ranges)` refuses, with a
  named error in each case: empty blob; blob larger than EXT_MAX;
  overlap of the blob's file range or of the [0x210, 0x214) record
  range with any claimed patch/transplant range; current code_len
  not equal to stock 0x29C14; any nonzero byte in the gap where the
  blob would land. On success it writes the blob at 0x532C0 and
  `code_len = 0x29C14 + len(blob)` at 0x210, and returns the
  extension record.
- `build_image(..., extension_blob=None)`: after manifest patches
  and transplants, the claimed ranges (patch ranges + transplant
  records' ranges) are passed to `apply_extension`; the extension
  is applied before finalize (date stamp, mirror, CRC), so all
  existing invariants cover it. The report gains one additive key,
  `extension` (null, or {exec, file_offset, bytes, code_len_old,
  code_len_new, code_len_record_file_offset}). SHA gate,
  `validate()`, date stamping, `--recovery` (extension refused in
  recovery mode) are unchanged.
- CLI: `--extension FILE`, with a summary line on build.

`verify.py` gains **check 8** (extension build): builds the
default framework-only image and an extension build carrying a
deterministic 6,000-byte pattern blob; asserts the extension build
equals the default at every byte outside [0x532C0, +6000) ∪
[0x210, 0x214) ∪ the trailer CRC; asserts
`Image.module_region(0, 'code')` returns length 0x29C14 + 6000;
asserts the blob bytes are present verbatim; asserts the report's
`extension.code_len_new`; calls `validate()` explicitly. Plus
three refusal unit tests (oversize blob, overlapping claimed
range, dirty gap byte).

**Result (scratch verify run, 2026-10-31): check 8 PASS**.
"outside-diff vs default build: 0 bytes; module 0 code region
0x296ac len 0x2b384; validate() passed; oversize refused: True;
overlap refused". Checks 1–6 PASS unchanged (31 patches, 1,383-byte
diff). So `validate()` accepts the extended module: the package
validator's own checks (header, per-module regions per the header
records, CRC) are satisfied by construction.

**Check 7 caveat, diagnosed:** check 7 (unified build) FAILs in the
scratch location only. The traceback ends in `load_transplant` →
`FileNotFoundError: .../work/m3u_bridge/vorbis_swap/transplant.py`:
the transplant loader resolves `../vorbis_swap/transplant.py`
relative to the framework directory, and the scratch copy has no
such sibling. Control: the identical build command with the
pristine live `build.py` in its real location reproduces the
pinned unified image SHA-256
`7d9d6b3035eb174e0dbe96ebc3fc820d14ab67fab848760813ffb8412f58ed8e`.
The extension edits do not touch the transplant path; after
integration into `patches/framework/` (where the sibling exists),
check 7 runs in its normal layout. The coordinator should re-run
the full verify post-integration to confirm 8/8 in place.

Residual risk carried from the design, unchanged: if the
on-device validator checks module lengths beyond header +
package CRC, the extension would be rejected at flash time. That
is a Phase E check; nothing offline can settle it.

---

## Job 3: parser placement (blocked on the toolchain)

No ARM C compiler exists in this environment: no
`arm-none-eabi-gcc` anywhere on the filesystem, no clang/LLVM;
`tools-local/bin` holds only the Rizin suite; host gcc is x86-64
only. (This matches the design's §2.4 open item.) Full detail in
`parser_build/SIZE_REPORT.md`; the host reproduction from this
session (`parser_build/m3u_host.o`, `gcc -Os -std=c99
-ffreestanding -fno-builtin`): .text 4,430 B, .rodata 352 B,
.rodata.str1.1 31 B → 4,813 B of code+const (whole object
5,339 B incl. .eh_frame and metadata; the design's 5,426 B was the
whole object under a slightly different host build). `m3u_import`
is 2,744 B of the .text. No .data/.bss.

Pinned despite the gap: placement (exec 0x03079C14; trampoline at
+0x00, bridge entry at +0x80), the build command (in

**Placement erratum (2026-10-31): the 0x03079C14 placement is withdrawn.** That region is live runtime workspace (descriptor table at 0x0307AB68, directory stack at 0x0307A8DC, FAT fields from 0x0307A024), per the census in `resolver_design.md`. The framework extension step and check 8 verify packaging mechanics only. The hook patch 0040 and the trampoline design are placement-independent in structure, but their target address must be re-pinned to a proven home before anything is stacked.
`bridge/m3u_bridge.c`'s header), and budget enforcement (check 8
refuses an 11,165-byte blob). **Unproven: the true Thumb-2 size**. The host sum leaves ~6.3 KB of headroom for the bridge on top of
the parser, but no target number is claimed until the compiler
exists and the link runs.

---

## Job 4: device bridge

### The hook: fully pinned; patch 0040 emitted

Site and mechanics (all byte-verified against the image;
disassembly in `evidence/mod31_full.txt`):

- Module 31's node-action function **0x0307DEB8** (module exec
  base 0x0307D164): `push.w {r4,r5,r6,r7,r8,sb,sl,fp,lr}` at DEB8
  (bytes `2de9f04f`), ADR to its table copy at DEBC, `sub sp,
  #0x4C`, the 44-byte table copy, then a linked-list walk over the
  browser state (r7) to the selected node r4; class byte
  `ldrb r5, [r4, #0x4E]` at DF06; r8 = play context 0x03023980;
  `cbz r5 → 0x0307DF4E` at DF16; `mov r0, r5` at DF18; **`bl
  0x0307D1F8` at 0x0307DF1A, stock bytes `fff76df9`**. No BL
  executes between DEB8 and DF1A, so at DF1A lr still holds the
  function caller's return address. 0x0307D1F8 is AAPCS-conformant
  from the caller's perspective (early-return path clobbers only
  r0–r2; the main path pushes {r4,r5,r6,lr} and itself calls the
  classifier 0x0305A15C at 0x0307D234).
- **Hook: replace the 4-byte BL at 0x0307DF1A with B.W to the
  extension trampoline** (`patches/0040-m3u-browser-hook.patch`:
  expect `fff76df9`, replace `fbf77bbe`). No-match path: the
  trampoline reproduces the displaced call exactly
  (`mov r0, r5; bl 0x0307D1F8`, result in r0) and resumes at
  **0x0307DF1E** (`mov fp, r0`). Handled path: the stock function's
  own common epilogue at **0x0307E0C8** (`add sp, #0x4C`; branch;
  `pop.w {r4,r5,r6,r7,r8,sb,sl,fp,pc}` at E0CE, bytes
  `E8BD 8FF0` verified) with r0 = 1, the same value the stock
  folder-play success path sets at 0x0307E0C6 before falling into
  E0C8. sp is balanced (the trampoline's push/pop pairs cancel;
  the +0x4C frame is released by the stock epilogue).
- The trampoline (64 bytes at extension +0x00; NOP pad; bridge
  entry at +0x80) was assembled instruction-by-instruction with
  rz-asm at its target address and every instruction audited
  against its Capstone decode (`scratch/asm_trampoline.py`;
  blob at `scratch/extension_blob.bin`, 132 bytes total including
  the bridge stub `movs r0, #0; bx lr`). It tests node +0x57/+0x58/
  +0x59 (the 8.3 extension field) for `M`,`3`,`U` and calls
  `m3u_bridge_node_action(node=r4, state=r7, ctx=r8)`. With the
  stub in place, patch 0040 + extension compose to exact stock
  behaviour; the compiled bridge replaces the stub at the known
  offset when the toolchain exists.
- `.m3u8` is not matched by the SFN test (its 8.3 alias
  extension is implementation-defined). A missed `.m3u8` falls
  through to stock behaviour, safe, and it stays that way until
  the LFN/display-name field in walker nodes is pinned.

**Scratch-build evidence for 0040:** framework_ext build with the
manifest extended by 0040 and `--extension extension_blob.bin`
(and the 31-patch framework-only build as the comparison):
resulting image SHA-256
`fa20405b59fda86130f43bfbcb4d68d4b54878246971018382eaed4803b879e8`;
the diff between the two builds is 102 bytes, all inside
{file 0x210..0x213 (code_len record), file 0x532C0..0x532C0+132
(blob), file 0x908F6..0x908F9 (the hook: module 31 code file offset
+ (0x0307DF1A − 0x0307D164); bytes `fff76df9` → `fbf77bbe`), the
CRC trailer}. Report extension record: code_len 0x29C14 →
0x29C98 for the 132-byte blob. (Build tree preserved at
`scratch/build_test/`.)

### Play-context fill and source 6: partially verified, one design point corrected by the trace

What module 31's class-byte-0 (folder-play) path does after the
dispatch (0x0307DF4E..0x0307E0C6): calls 0x0307D1F8 with r0 = 1,
0x0305B2C2 (entry count → halfword at [sp,#4]), validation via
0x030570E8 and conditionally 0x03057040, then at 0x0307E088
`movs r0, #6; strh.w r0, [r8, #0xF2]` (source code 6), and at
0x0307E08E..0x0307E09E copies the current record's +0x14 dword
into a global reached through the literal at 0x0307E09C. Record
fields around it: node +0x63/+0x69 (u16 pair) combine into record
+0x14/+0x18 (both orderings stored, 0x0307DF96..0x0307DFCC);
node +0x5C byte → record +0x24; node +0x6B word → record +0x1C.
Note for the design doc: the display node in this function is a
larger structure than the 56-byte array element (fields past
+0x38 are used); the 56-byte-stride array element's record sits at
element +0xC in the browser state's layout.

Module 33 (playback task advance, 0x0308A480..0x0308A55x): the
index at ctx+2 is incremented **uniformly** and bounds-checked
against the total at [sb]; the format-class special cases read
the file-info type at [ctx+8]+0x1C (values 6/2/4), not the
+0xF2 source code; on event 0xEC the index resets. Open-prep
0x03089DA6 takes the file-info pointer in r0, calls the type probe
0x03059D58, and stores the result halfword to a global. So the
design's claim "the player iterates source-6 lists" is supported
at the task level: nothing in the advance path discriminates on
the source code. **Still open (B3): the exact index→record fetch**. The chain
from the open path (0x03089DA6) to the array base the
fetch reads was not traced to its source in this session (the
function at 0x03089AD6 turned out to be a state/wait helper, and a
full linear disassembly of module 33 is not possible: the sweep
dies on embedded data at ~513 lines; windowed disassembly is the
working method). The bridge's context fill mirrors module 31's own
stores exactly, including the +0x14/global store shape, which is
the strongest available evidence; B3 is the trace (or harness run)
that remains.

### File primitives: the stock model is whole-file (module 37 precedent)

Module 37's CUE parse entry 0x0307D73A (evidence/mod37_full.txt)
shows the overlay file model end to end: FS acquire 0x030611E0
(called inside the parse loop at 0x0307D804), then
`0x030545D4(path)` → a count used as read cap and parse bound,
`0x030693EA(path, buf, cap, 0)` → ≥ 0 on success (negative return
takes the error branch), and the parser then works on the RAM
buffer (BOM sniff at 0x0307D772 reads the buffer directly).
0x0306D8F0 is the error/log call (ADR string pointers on every
error path). Semantics are labelled [inferred from call sites] in
the bridge header; the call patterns themselves are proven.
Module 37's heaviest module-0 callees are the copy/string pair
0x03054E34 (11×) / 0x03054EBE (13×), matching the design's note.

### Bridge source and its blockers

`bridge/m3u_bridge.h` / `bridge/m3u_bridge.c`: freestanding C99,
compiles clean on host gcc (syntax/type check; the device build is
blocked by job 3's toolchain gap, and by design the file refuses
to compile for device without STAGE_BASE defined). Implemented:
the whole-file `M3uFs` open/read/size/close over the pinned
primitives; the staging loop in playlist order; the play-context
fill mirroring module 31. Named blockers where the code stops:

- **B1: current-directory path.** The bridge entry needs the
  playlist's absolute path (current directory + node name). The
  node's 8.3 name decodes mechanically; module 31's state layout
  for "current directory" is not traced (candidates exist around
  [r7, #0x1F4] but nothing is proven). `bridge_playlist_path()`
  returns 0 until pinned, the only missing piece between the
  hook and a running import.
- **B2: staging arena.** No RAM slice is proven free against the
  SAVEINFO/BSS map (the design's §5.3 open item, unchanged). The
  bridge takes STAGE_BASE as a build-time parameter and
  `#error`s without it rather than inventing an address.
- **B3: module 33 index→record fetch** (above).
- **B4: LFN field** for `.m3u8` and long names in walker/browser
  nodes (the design's open item; v1 is SFN-only by construction).
- **B5: walker param-block +0x08 producer** (the directory entry
  count the walker bounds against) and the name-field offset in
  the walker's ctx record: stat()'s algorithm is fully specified
  in the bridge source (component walk with the classifier's
  proven `*` accept-all entry, first byte 0x2A matches every
  entry unconditionally, returning the final entry's start
  cluster from ctx +0x00 and its enumeration ordinal, which is
  definitionally the scan's index), and the vtable slot is wired
  behind those two pins. lib_count/lib_nth currently report an
  empty library, a stated degradation: resolution stages 1–2
  (folder-relative, root-relative) work; stage 3 (library suffix
  match) finds nothing rather than guessing.

No patches 0041–0049 were emitted: the only other candidate (the
scan gate pair) is refuted in job 1, and nothing else is fully
pinned. Emitting speculative bytes was explicitly out of scope.

---

## Deliverables in this directory

- `m3u_bridge.md`: this report.
- `framework_ext/`: scratch framework with the region-extension
  build step (build.py/verify.py full replacements + the unchanged
  patches/ copy). Integration: drop build.py/verify.py into
  `patches/framework/`, re-run verify (expect 8/8 in the real
  layout).
- `patches/0040-m3u-browser-hook.patch`: the one pinned hook
  patch, gated on the extension build.
- `bridge/m3u_bridge.h`, `bridge/m3u_bridge.c`: bridge source.
- `parser_build/`: host object + `SIZE_REPORT.md` (job 3).
- `scratch/`: `asm_trampoline.py` (trampoline source + audit),
  `extension_blob.bin` (132 B), `hook_replace.bin`,
  `fwdis2.py`, `build_test/` (the 0040 scratch-build tree).
- `evidence/`: disassembly listings cited above.

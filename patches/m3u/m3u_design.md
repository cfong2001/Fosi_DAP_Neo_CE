# M3U playlist support for stock DP3_V137: integration design + parser/resolver core

Scope: stock firmware image `DP3_V137.img` (SHA-256
`fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`), 82 overlay
modules. All evidence below is from the image itself (byte search + capstone
disassembly of the extracted module bins); established prior analysis is in
`analysis/library_m3u.md`. Claims are marked **[proven]** (bytes/instructions
observed in this pass) or **[open]** (named trace still to do).

The parser/resolver core is implemented and host-tested in this directory
(`src/m3u.c`, `src/m3u.h`, `tests/`; 26 checks, 0 failures, ASan/UBSan clean).
Its logic follows EchoPod's `playlist_reader.c` / `builder_resolve_entry()`
(BasilSkyWalk/echopod, GPL-3.0) and the NeoPod port (danielNZ27, GPL-3.0),
re-implemented in a different structure for the stock environment; see §6.

---

## 1. Verdict summary

- **Home for the parser: an extension of module 0's code region**: resident,
  callable from any overlay by direct branch, 11,164 bytes of verified headroom
  (§2). The core compiles to 5,426 bytes (host −Os object, tables included), so
  core + device bridge + hook trampolines fit with roughly half the space spare.
  No existing module contains usable cave space: every large zero tail in the
  image is referenced runtime workspace (§2.1).
- **Invocation v1: browser-open hook, by name test. No extension-gate edits
  needed.** The folder browser lists non-audio files (TEXT/OTHER classes exist
  in the stock icon set), so a `.m3u` file is visible and selectable today;
  module 31's node-action function `0x0307DEB8` is the hook point (§3).
- **Invocation v2: scan-time, following the CUE pattern exactly** (module 38
  loads a parser module and diverts to it). It is blocked on one trace: how the
  directory walker bounds its extension-table walk (§4.3). The drafted gate
  bytes are recorded there; **no gate `.patch` files are emitted in this
  deliverable**, because which patch set is correct depends on that trace
  (the task's condition, verified space *and* a clean invocation path, is
  met for §2/§3, not yet for the scan gate).
- **Bridge: reuse the stock directory walker** (module 0 `0x0305A2F0` via
  wrapper `0x0305A970`) to turn each resolved absolute path into the
  (clus, index) pair the scan itself stores in playback records (§5).
  Playlist order is preserved by staging records in playlist order and
  pointing the play context at them with the folder-play source code.
  The database and its insertion sort are never involved.

---

## 2. Where the parser lives: module 0 code-region extension

**Erratum (2026-10-31): the placement premise of this section is withdrawn.** The region at exec 0x03079C14..0x0307C7B0 is a gap in the package file, but it is live runtime workspace: the file descriptor table (0x0307AB68, 8 slots of 638 bytes), the directory stack (0x0307A8DC), FAT driver fields (from 0x0307A024) and the cluster bitmap cache (0x0307A6D8) all live there, written by resident code (registrar 0x0305C514 confirmed from disassembly). The original analysis validated the region as a package gap and never censused runtime references into it. Code placed there would collide with filesystem state on hardware. The framework's extension step is packaging mechanics only; it must not be used with this region. A replacement home is being censused (overlay-hosted code is the leading candidate: the parser's only caller context is the browser, module 31). See `resolver_design.md` for the SRAM census that surfaced the overlap.

### 2.1 No caves exist in any loaded module [proven]

Zero runs were inventoried across all extracted module code bins, and every
candidate was then checked for absolute-address references from all bins:

| region | size | references | verdict |
|---|---|---|---|
| module 0 code, exec `0x0306F1E8..0x03079824` | 42,556 B | 26 word refs from module 0 itself (e.g. literals `0x0306F1E8`, `0x0306F224` in pools at bin `0x14268..0x155A0`) | workspace, the SAVEINFO mirror buffer at `0x03078824` (Phase 2) sits inside it; the preceding bytes are compressed data |
| module 39 code tail, exec `0x0307E1EC..` | 135,872 B | 248 refs | the sort engine's BSS arena (state `0x0307E1EC`, string buffers `0x0307F28C`/`0x0307F38C`) |
| module 61 code tail | 73,740 B | 116 refs | workspace |
| module 29 code tail | 1,944 B | 23 refs | workspace |
| module 30 code tail | 380 B | 10 refs | workspace |
| modules 31 / 37 / 38 code | dense (`last_nonzero == len`) | none | no tail at all |

So a code cave in an existing module is out. What does exist:

### 2.2 The package gap after module 0's code [proven]

Module regions in the package are packed back to back with exactly one gap
≥ 1 KB: **file `0x532C0..0x572C0`, 16,384 zero bytes**, between module 0's code
region (file `0x296AC`, length `0x29C14`, ends `0x532C0`) and module 0's data
region (file `0x572C0`). The bytes are unreferenced package slack.

Execution-side headroom: module 0's code exec range ends at `0x03079C14`; the
lowest overlay exec base in the load map is `0x0307C7B0` (modules 3/4). The
range `0x03079C14..0x0307C7B0`, **11,164 bytes (0x2B9C)**, is assigned to no
module, decoder, data or BSS region. The flash side allows 16,384; the exec
side binds at **11,164**.

### 2.3 Mechanism: one record field [proven]

Module 0's record in the package header (records at file `0x208`, 32 bytes
each) is:

```
0x208  code_load 0x030794AC   code_exec 0x03050000   code_len 0x00029C14
       data_load 0x030A70C0   data_exec 0x03004000   data_len 0x000019A9 …
```

Extending the parser into the gap = setting **`code_len` at file `0x210`** from
`0x29C14` to at most `0x2C7B0`. Supporting facts:

- The header mirror at file `0xC94000` duplicates only the first **0x202
  bytes** of the header (measured: byte-identical for exactly 0x202 bytes).
  It does not cover the module table, and no second copy of the module table
  exists anywhere in the image (byte search for the table's first 64 bytes:
  one hit). One edit site, not two.
- The generic loader (`0x03067870` → `0x0306777A`, Phase 2) takes lengths
  from these records; the package CRC is recomputed by the existing patcher
  finalize, which already syncs the 0x202-byte mirror for date stamps.
- Precedent in the stock build itself: module 0's declared code region
  already ends with data-like content (the clock table at `0x03079824`) and
  contains RAM workspace (the SAVEINFO buffer). The region is "resident
  stuff", and the extension continues that pattern.

**Framework consequence [proven]:** this is *not* expressible as a framework
module patch. `firmware_patch.py` requires length-preserving edits inside a
module's declared region (`rel + len ≤ region_len`). The framework needs one
new build step ("region extension": edit file `0x210`, write the extension
bytes at file `0x532C0`, then the normal date/CRC finalize). Residual risk,
stated plainly: if the on-device validator checks module lengths against
anything beyond the header + package CRC (nothing in the Phase 2 validator
trace suggests it does; slot validation was magic + mirrored-header compare
+ date), the extension would be rejected at flash time; that is a Phase E
(hardware) check.

### 2.4 Fit

`src/m3u.c` at −Os: **5,426 bytes** (host x86-64 object, constant tables
included; no data/BSS). Thumb-2 confirmation needs `arm-none-eabi-gcc`
(nanitecfw's toolchain; not installed on this box) **[open]**, low risk:
the budget is 11,164 and the remaining ~5.7 KB covers the device FS bridge
(§5) plus two hook trampolines with room to spare. Stack: the core's worst
frame is ≈ 7 KB (reader chunk 512 B + line 1 KB + path buffers); module 38's
scan function already runs with a 0x2E44-byte (≈ 11.8 KB) frame, so calling
the core from scan/browser contexts is within stock precedent.

---

## 3. Invocation

### 3.1 v1: browser-open hook (no gate edits)

The folder browser is not audio-only: the resource table contains
`A_BROWSER_FILETYPE_{FOLDER,MUSIC,VIDEO,TEXT,PICTURE,OTHER}` icons
(`analysis/library_m3u.md` §1), so `.m3u` files are listed today, classified
OTHER/TEXT. Selecting one reaches **module 31's node-action function
`0x0307DEB8`** [proven: it builds the play context at `0x03023980`, writes the
source code at `+0xF2` (`movs r0,#6; strh [r8,#0xF2]` at `0x0307E088`) and
classifies the node via the byte at node `+0x4E` (read at `0x0307DF06`) with
the 11-byte name at node `+0x4F`].

Hook design: a trampoline at the head of `0x0307DEB8` (or immediately before
its classification call at `0x0307DF1A`) into the module-0 extension:

1. Test the selected node's name extension: last 3 chars `M3U`, or last 4
   `M3U8` (the 3-char world of the stock gates can never spell M3U8; the
   name test is ours, so both work; §7).
2. On match: call the device bridge's `m3u_import()` on the file's absolute
   path (reconstructed from the browser's current directory + node name,
   the same components module 31 itself uses), stage the resulting records
   (§5.3), fill the play context exactly as the folder-play path in this
   function does (source code 6 at `+0xF2`, total at `+0`, index at `+2`),
   and return "handled". On no match: execute the displaced instructions
   and continue stock flow.

Cost: one small code patch in module 31 (2–4 bytes for the branch, using the
framework's existing module-patch kind, expect = stock bytes at the chosen
site) plus the extension. The exact instruction overwritten is the follow-up
step's choice, not this document's. It needs the same liveness care as the
DAC-fix trampoline.

### 3.2 v2: scan-time (Playlists view), the CUE pattern

How CUE works today [proven]:

- Module 38's scan main function loads module 37 at init:
  `movs r1,#7; movs r0,#0x25; bl 0x03067870` at `0x0307E58A..0x0307E59A`
  (loader, module 37, flags 7), then clears slot 2 the same way.
- When the walk meets a `.cue`, module 38 calls **module 37's parse entry
  `0x0307D73A`** exactly once (`bl` at `0x0307EAAC`), passing a file handle
  produced by its own helper `0x0307E43C` and a work buffer at `0x0302D394`.
- Module 37 fills a sub-track array at `sp+0x640` with a count at
  `[sp,#0x610]` (capped at 0x28); module 38 consumes it record by record
  (0x100-byte stride) into the database.

M3U in the same mould: module 38 diverts `.m3u` files to the (resident)
parser instead of loading an overlay; the parser's staged records are
consumed the same way into a Playlists database list. The diversion needs
the walker to hand `.m3u` files to module 38 as *interesting*. That is the
extension gate, §4.

---

## 4. The extension gates, byte by byte

### 4.1 The five copies [proven, byte search over the whole image]

The accept-list is 14 dotless 3-char codes
`MP1 MP2 MP3 WMA WAV APE FLA AAC M4A OGG MP4 3GP DFF DSF` (note `FLA`):

| copy | location | layout after last code |
|---|---|---|
| module 0 data #1 | exec `0x030056BE`, image `0x5897E` | 1 NUL, then copy #2 (stride 43 B) |
| module 0 data #2 | exec `0x030056E9`, image `0x589A9` | 1 NUL, then copy #3 |
| module 0 data #3 | exec `0x03005714`, image `0x589D4` | 1 NUL, then `WAV\0 TXT\0 AVI\0 JPGJPEBMP` tables |
| module 31 code | exec `0x0307E110`, image `0x90AEC` | 2 NULs, then a literal pool (`0x030228A8`…) |
| module 38 code | exec `0x0307E6CC`, image `0x7E4CC` | **`CUE` appended (15 codes)**, then 3 NULs, then a literal pool (first literal `0x0302329C`) |

### 4.2 Why a naive append cannot work [proven]

Consumers do not read these tables in place; they **copy a fixed number of
bytes to the stack** and work on the copy:

- Module 31 (`0x0307DEB8`): ADR to `0x0307E110`, then an LDM/STM sequence
  (`0x0307DEBC..0x0307DEE2`) copies exactly **44 bytes**: 14 codes + the
  2 NULs. A 15th code appended in the image would never be copied.
- Module 38 (scan main): ADR to `0x0307E6CC` at `0x0307E54C`, then
  LDM×2 + LDRD×2 (`0x0307E55E..0x0307E582`) copies exactly **48 bytes**
  (15 codes + the 3 NULs) to `sp+0x5D8`, and passes that copy to the
  module-0 enumeration wrapper `0x0305A970` (calls at `0x0307E74E`,
  `0x0307E7A6`).

And no copy has four spare bytes: module 38's 3 NUL pad bytes (exec
`0x0307E6F9..0x0307E6FB`) are the closest: enough for `M3U` but not for
`M3U` *plus* a zero terminator entry inside the copied range.

### 4.3 What remains open, and the drafted patch

The enumeration wrapper `0x0305A970` passes the table pointer in `r3` to the
core walker **`0x0305A2F0`** with a parameter block
`{path, 3, class}` (`strd` at `0x0305A98C`; the `3` reads as the entry size).
Neither call site passes a count, so the walker's bound is either
content-derived (scan entries until a zero entry) or fixed internally.
**Tracing that bound inside `0x0305A2F0` is the one remaining RE step for
the scan gate.** Depending on the answer:

- *Zero-entry bound:* the module-38 gate is a two-patch set:
  (i) `M3U` over the pad: module 38, region `code`, address `0x0307E6F9`,
  expect `000000`, replace `4D3355`; and
  (ii) extend module 38's stack copy from 48 to 52 bytes so a zero entry
  follows `M3U`: rewrite the LDM/LDRD sequence at `0x0307E55E` as a
  bounded-copy call of the `0x03054E34` class (the helper module 38 itself
  calls with `(dst, src, 0x2A)` at `0x0307E630`), which requires a
  register-liveness check on `r2/r3/sb/ip` across `0x0307E586..0x0307E63E`.
- *Fixed bound (15):* the count inside `0x0305A2F0` must be patched as
  well/instead.

Because the correct set depends on the trace, **no `.patch` files are
emitted here**; patch (i)'s bytes are recorded above so the follow-up is
mechanical. Module 31's copy (44 B, 2 NULs) cannot take `M3U` + terminator
under any bound. The browser gate stays closed, which v1 (§3.1) is
designed to not need. Module 0's three data copies are untouched: their
individual consumers were not all traced in this pass (one address,
`0x03005714`, is dereferenced by module 24 for the play-context `+0x10`
field; flagged, not resolved).

---

## 5. The bridge: resolved path → (clus, index)

### 5.1 What stock offers [proven]

- FS acquisition: module 0 `0x030611E0`, called by every overlay before
  file work (module 37 calls it twice; module 38 likewise).
- Enumeration: wrapper `0x0305A970` → walker `0x0305A2F0` (module 0),
  which walks a directory by cluster and classifies each entry against
  the caller's extension table, producing the node structures the
  browser and scan share: list rooted at `0x030228A8`, node array at
  `0x0307A8DC` with 56-byte stride (index arithmetic
  `(i<<6) − (i<<3)` in the node constructor `0x03059B10`), 11-byte 8.3
  name at node `+0x4F`.
- The playback record the whole library resolves to (module 24's fetch,
  `0x0306C7AC`; log string `st.clus = %d, st.index = %d` at `0x0307EDB4`):
  `+0x00` u32 `clus`, `+0x04` u32 `index`, then fields copied to the play
  context at `+0x10/+0x14/+0x18`. Browser-built records mirror the layout:
  module 31 stores node cluster data into record fields `+0x14`/`+0x18`
  at `0x0307DFB2`/`0x0307DFCC`.

### 5.2 Device implementation of the M3uFs vtable

- `open/read/size/close`: the playlist file itself, via the same module-0
  file path the CUE parser uses (FS acquire `0x030611E0`, then the file
  helpers module 37 calls. Its heaviest module-0 callees are the
  `0x03054E34`/`0x03054EBE` copy/string class; the exact open/read entry
  points are pinned when the bridge is written, from module 37's call
  graph).
- `stat(path)`: walk the path component by component from the volume
  root with the walker, matching each component against the dirent
  names; return the final entry's start cluster as `clus` and its
  ordinal within its parent directory's enumeration as `index`,
  definitionally the pair the scan stores, because the scan's records
  are built from the same enumeration.
- `lib_count/lib_nth`: iterate the scan's node array (post-scan state),
  yielding each file's absolute path (reconstructed from the node
  chain, as the browser does) and its (clus, index). At browser-open
  time (v1) the arrays are populated; that is what makes open-time
  resolution possible without a rescan.
- Case behaviour: FAT matching is case-insensitive; the vtable contract
  in `m3u.h` says so explicitly, and stage 3's fold (§6) covers the
  accent/case residue the FS itself won't.

### 5.3 Staging and playback

`m3u_import()` already returns the ordered (clus, index) list with
EXTINF metadata attached. The bridge writes those into a staging array
of playback-record-shaped entries **in playlist order** and fills the
play context (`0x03023980`) with source code 6 (the folder-play code
module 31 itself uses), so the player iterates the staged array and the
module-39 insertion sort (which would alphabetise a database list) is
never involved. Two items are **[open]** for the bridge step: the
staging arena (record count × 0x1C+ bytes of RAM; candidates are a slice
of module 0's data BSS or module 39's arena when not scanning; it must be
pinned against the SAVEINFO/BSS map), and the exact iteration contract
for source-6 lists inside module 33's open-prep (the category 8/9
validation path through `0x030570E8`/`0x03057040` noted in the
feasibility analysis suggests not all sources iterate alike).

---

## 6. The core that was built

`src/m3u.h` / `src/m3u.c`, freestanding C99: no heap, no libc calls (the
only helpers are local loops the device port maps onto stock routines).
External surface = the `M3uFs` vtable only.

- **Reader**: 512-byte chunked reads; whole-file UTF-8 sniff; any
  invalid sequence switches the file to Windows-1252 (bytes
  0x80..0x9F through the standard CP1252 table, undefined slots →
  U+FFFD); UTF-8 BOM skipped; lines split on CR/LF/CRLF plus, in UTF-8
  mode, NEL/LS/PS; leading/trailing whitespace trimmed; blank lines and
  `#` lines skipped.
- **#EXTINF**: `duration,Artist - Title` parsed per entry; duration
  defaults to −1; a comment or blank line does not consume the pending
  metadata; the next entry line (including a URL line, which is then
  skipped) does.
- **Resolver** (three stages, in order): (1) join with the playlist's
  folder, dot-components collapsed; (2) volume-root relative (drive
  designator and leading separators stripped. This is what makes
  MusicBee-style `D:\Music\...` exports resolve); (3) case-folded
  component-suffix match across the whole library, longest suffix wins,
  **a tie counts as not found**. Backslashes are normalised before all
  stages. Unresolvable entries are counted and skipped, never fatal;
  duplicates and playlist order are preserved.
- **Fold**: ASCII case + Latin-1 accent stripping (À–ÿ range mapped to
  base letters, Æ→ae, ß→ss, Þ→th), a deliberate subset of EchoPod's
  generated full-Unicode tables; both sides of every comparison use the
  same function, so the fold only needs internal consistency.
- **Limits**: paths 512 B, lines 1,024 B (decoded), 16 path components
  in suffix matching, caller-sized output array with overflow counted
  in `M3uStats`.

### Host tests (`tests/test_m3u.c`, mock = the `M3uFs` vtable over an
in-memory library of (path → clus, index) entries)

**26 checks, 0 failures** (also clean under ASan/UBSan; log in
`tests/test_output.txt`, build via `tests/Makefile`). Corpus:

- Windows-authored list: CRLF, backslash paths, a `D:\...` absolute
  entry, a `..\` relative entry, `#EXTINF` with durations 342 and −1;
  all resolve with correct (clus, index) and artist/title split.
- UTF-8 `.m3u8` with BOM and a non-ASCII filename (Björk).
- Windows-1252 playlist whose Latin-1 filename (`Café...`, byte 0xE9)
  resolves the library's UTF-8 name.
- Missing entry, `http://` entry, and a directory entry: skipped and
  counted; duplicates kept, in order.
- Suffix rules: bare filename present twice in the library → tie →
  unresolved; deeper suffix (`Dup/Same Name.mp3`) → unique winner;
  unaccented entry (`Bjork - ...`) resolves the accented file by fold.
- EXTINF association across intervening comments/blanks; title-only
  EXTINF; following entry carries no metadata.
- 500-entry generated playlist: all resolve, order and every
  (clus, index) pair verified.
- Output-capacity overflow is counted, and an unreadable playlist
  returns −1.

---

## 7. Remaining open items (each with its next step)

1. **Walker table bound** (`0x0305A2F0`): trace how the entry walk
  terminates → selects the §4.3 patch set; then the copy-extension
  liveness check in module 38 (`0x0307E586..0x0307E63E`) if needed.
2. **Hook site in module 31**: choose the exact instruction to
  trampoline in/near `0x0307DEB8` with a liveness check; emit as a
  framework module patch (kind `module`, module 31, region `code`).
3. **Framework region-extension step**: teach `build.py` the
  file-`0x210` record edit + extension-byte write before finalize;
  round-trip/tamper tests analogous to the existing six.
4. **Device FS bridge**: pin module 37's open/read callees, the LFN
  field in walker nodes (the 11-byte name at `+0x4F` is the 8.3 form;
  long-name playlists entries need the display-name field the browser
  uses), the staging arena, and module 33's source-6 iteration
  contract (§5.3).
5. **Thumb-2 size confirmation** with `arm-none-eabi-gcc −Os`
  (budget 11,164 B; host object is 5,426 B).
6. **Module 0 data-copy consumers**: resolve what reads the three
  accept-list copies (`0x030056BE`/`0x030056E9`/`0x03005714`) before
  any future change there; not needed for v1/v2 as designed.

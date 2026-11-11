# Patching RKnano stock firmware: technique research

Research date: 2026-10-31. Purpose: prep for adding features to the Fosi Audio
DAP Neo stock firmware (`DP3_V137.img`, Rockchip RKnanoD, dual Cortex-M3) by
binary patching the stock update image. The approach our completed RE
(`stage/analysis/`, `stage2/analysis/`) already assumes: an offline patcher
edits the package, mirrors the header, regenerates the package CRC; overlays
load from the package at runtime; module 0 is resident, modules 1–81 are
overlays in shared windows; persistent new config must live in the SAVEINFO
verbatim block `+0x1C7..+0x2D5`.

Three primary sources were deep-read locally, plus a survey of the surrounding
community landscape (§4) and a per-goal easiest-path assessment (§6).

Local clones:

- `refs/nanitecfw/`: HEAD `e0b2221` (2026-10-22)
- `refs/echo-mini-fw/`: HEAD `e321a5e` (2026-10-21)
- `refs/rknanod-sdk/`: cloned for this research (see §3)
- `refs/echopod-upstream/`, `refs/NeoPod-Fosi-DAP-Neo-Custom-Firmware/`:
  pre-existing clones, used in §4

---

## 1. nanitecfw: patch-based custom firmware for the FiiO Echo Nano

The single most relevant reference for our project: a working, shipped
example of adding real features (new library views, faster sorting, power
savings) to a stock RKnano firmware purely by patching the vendor update
image. Same container family, same SDK lineage, same overlay architecture.

### 1.1 Identity, target, license

- Author Marek Pleskac, MIT License (© 2026), the only one of the three
  primary sources we may freely copy code and tooling from.
- Target: FiiO Echo Nano stock V1.7.0, file `NANOV170.IMG`, SHA-256
  `54a45d233a23c3ce142d1da9c093cc40c46eba417aa91fe915ee867726f4a116`.
  The repo ships only patches and tools; the user supplies the stock image.
- The patch tool refuses any input whose SHA-256 is not in its known-stock
  table (`tools/rknano_fw.py`, `STOCK` dict) unless `--any-input` is passed.
  Consequence (their README is explicit): every address is V1.7.0-specific,
  and a new stock release means re-doing the RE. This fragility is inherent
  to the technique, not a flaw of this project.

### 1.2 Build flow

`make` (GNU make ≥ 4.3, python3 stdlib only, arm-none-eabi-gcc/binutils
≥ 2.39; a `shell.nix` pins the toolchain) produces `out/NANOV170.IMG`:

1. Assemble every `patches/*.S` into a hex patch line (`tools/asm2patch.sh`).
2. Build the C blob in `src/` (`tools/build_blob.sh`) and generate its hook
   patch (`tools/hooks.py`).
3. Apply all `patches/*.patch` + generated patches to the stock image with
   `tools/rknano_fw.py patch`.
4. Finalize: mirror the header, regenerate the CRC, bump the image date.

Two date details matter and match our own phase-2 boot findings on the Neo
(validator boots the newest-dated valid slot):

- Output date defaults to 20260825, one day after stock (2026-08-24),
  because the loader boots the newest-dated valid image.
- `make recovery` emits unmodified stock with date 20260826. Recovery
  is "stock, but newer", and each successive reflash needs date+1 again.

### 1.3 The three patch kinds

(a) Data patches: `patches/*.patch`. One patch per line, grammar:

```
MOD:EXECADDR:hexbytes          # raw bytes at an execution address
MOD:ADDR:u"text"                # UTF-16LE string + NUL
lang:ID:langcode:u"text"        # localized string by string-table ID
```

`rknano_fw.py region(mod, addr)` resolves an execution address to a file
offset through the module table's code/data regions and rejects overruns,
i.e. patches are addressed the way the CPU sees them, not by file offset.
Localized strings are written into the stock string table: layout is a u16
count followed by u32 block offsets; each entry is a 258-byte slot
(`LANG_SLOT=258`) with a 58-byte header (`LANG_HDR=58`) and text at slot+58,
zero-padded; the table holds 431 slots (`LANG_SLOTS=431`).

(b) Assembled code patches: `patches/*.S`. Each file starts with a
header line `@ patch MOD ADDR`. `tools/asm2patch.sh` assembles it *at the
target address*:

```
gcc -c -mthumb -mcpu=cortex-m3 -x assembler-with-cpp -DPATCH_BASE=0xADDR
ld -Ttext=ADDR; objcopy -O binary   →  one hex patch line
```

`patches/fw.inc` (43 lines) is the shared include: `.equ` definitions of
known stock symbols (these are Echo Nano V1.7.0 addresses:
`dbg_printf 0x03071e28`, `msg_post 0x0306b040`, `msg_test 0x0306b05c`,
`load_module 0x0306b6bc`) plus macros `fbl`/`fb`/`fbeq`/`fbne` that
hand-encode Thumb-2 T4/T3 branches relative to `PATCH_BASE`, because the
linker cannot relocate a `bl`/`b.w` to an absolute stock address. This is
the key authoring trick: patches are written as readable assembly with
named stock symbols, and the branch encodings are computed by macro.

(c) A freestanding C blob: `src/`. For features too large for caves:

- `src/cfw.c` (683 lines, the library rebuild), `src/fw.h`,
  `src/libc.c` (minimal memcpy/memset family), `src/prof.c/.h` (a call
  profiler), `src/start.S` (blob entry/stub).
- `src/link.ld`: the blob's load region `STAGE` is module 40's first
  64 KB sort buffer at `0x0307b674`, length `0x10000`. Zeros in stock.
  Its RAM region is `0x0309b694..0x0309fff0`, annotated "above every module,
  below the reboot flag at `0x0309fff0`; nothing else uses it", with a
  linker ASSERT on fit. A stub (`cfw_stub` in `start.S`) copies
  `.text`/`.data` from STAGE to RAM and clears `.bss` on first call.
- Exported blob symbols are emitted as `.equ` lines into
  `out/gen/syms.inc`, which the `.S` patches consume, the same include
  mechanism as `fw.inc`, so cave code can call C functions by name.
- Build flags: `-Os -ffreestanding -nostdlib`, Cortex-M3.

### 1.4 Hooking stock code

Four distinct hook patterns are used; all four transfer to the Neo.

1. One-instruction route patches. Cave entry is often a single branch
   instruction overwriting a stock dispatcher instruction. Examples:
   `shuffle_11` is one `fb` over the stock dispatcher at `0x03079b8c`;
   `library_menu_41` is one `fbne` replacing a fall-through at `0x03079640`;
   the `*_call.S` files are each a single `fbl` replacing a stock `bl`.
2. Hook manifest: `src/hooks.txt` + `tools/hooks.py` (87 lines).
   Lines are `MOD ADDR OP SYMBOL [TAG]` with OP ∈ {`bl`, `b`, `wrap`}.
   The tool decodes the original Thumb-2 branch at the site (and fails if
   it is not a `bl`), encodes a replacement branch to the blob symbol
   (addresses from `nm` output), and emits `out/gen/cfw_hooks.patch`.
   `wrap` sites route through `prof_thunk` (`start.S`), which saves
   r0–r3/lr and calls the original via a generated `wraps.h`. Hook with
   the original preserved, at zero stack disturbance.
3. Literal-pool pointer redirection. Rather than patching code, point
   stock code at new data: `library_menu.patch` writes
   `22:03079e74:08e70003` and `22:0307a2f4:08e70003` so the stock draw and
   dispatch routines consume a brand-new 10-entry menu table placed in
   module 22's unused data space (§1.5). Companion data patches fix the
   menu count immediate in place (`22:030794f4:0a21` = `movs r1,#10`) and
   a TBB table entry (`21:03079b39:0b`).
4. Runtime self-patching. `cfw.c`'s `fread_hook(on)` overwrites the
   first instruction of the stock `fread` (`FREAD_ADDR 0x0305c3fa`) with a
   hand-encoded `b.w` to `cfw_fread` for the duration of the library walk,
   then restores the saved halfwords (PRIMASK off + DSB/ISB around the
   write). `fread_orig` (`start.S`) replays the displaced `push.w` and
   continues at `0x0305c3ff`. Purpose: serve the tag parser's many small
   reads from a 4 KB window buffer (`WIN_BUF`) instead of one sector read
   per byte-range, a large share of the refresh speedup.

The blob calls *into* stock code through typed function pointers
(`src/fw.h`):

```c
#define FW(addr, ret, ...) ((ret (*)(__VA_ARGS__))((addr) | 1))
```

with stock entry points (`fw_read 0x0306b36c`, `fw_write 0x0306b75e`,
`fw_load_module 0x0306b6bc`, `fw_lock`/`fw_unlock`, `fw_ticks`, the file
API, `fw_tags 0x03071178`, the stock tag parser) and stock structures
mapped in C (`struct file`: table `FILES 0x03077668`, record size `0x27e`,
`NFILES 8`; `DB_BASE = *(u32*)0x0300d148`; library counters at
`0x0300d164`).

The flagship integration is the refresh driver hook:
`patches/recent_albums_10_mod05_driver.S` replaces module 05's stock
refresh-driver sequence with `load_module(0x28=40, 7)` → `cfw_stub` →
`cfw_scan(...)` → resume into stock at `0x030794ca`. `cfw_scan` re-implements
the refresh pipeline while reusing stock stages as subroutines
(`fw_load_module(39,7)`, `mod39_walk`, `mod39_record`,
`mod05_progress(1)`, `fw_load_module(40,7)`, `mod40_sort`) and adding its
own `build_artists`/`build_recent`. It also writes a `CFWLOG.TXT` debug log
to the card root, field debugging without a console.

### 1.5 Code caves and free space

All cave space is *dead stock code or provably unused data*, found by the
same xref discipline we used:

- Module 21: a never-called "UNICODEXDIC" writer,
  `0x03079502..0x03079639`: hosts the icon table, `shuffle_icon`,
  `shuffle_route`, `strip_extra`.
- Module 22: an unreferenced function `0x03079490..0x030794f1`: hosts the
  `library_menu` dispatcher; module 22's zero-filled data
  `0x0300e708..0x0300e8a7` hosts the new 10-entry menu table, and
  `menu_restore` code is placed in data space at `0x0300e744`.
- Module 23: an unreferenced function `0x03079d78..0x03079ef5`: hosts
  `shuffle_key`, `recent_setup`, `artist_setup`, `artist_count`.
- The 64 KB zero sort buffer (module 40) as the blob STAGE region (§1.3c).

New UI is added without new string resources: the Echo Nano has no
Bluetooth hardware, so its stock firmware's Bluetooth strings, IDs
`0x82` "Bluetooth Connecting...", `0x85`, `0x86`, `0x87` "Bluetooth Not
Paired", are repurposed via `lang:` patches in all 21 languages to
"Shuffle", "Artists", "Album Artists", "Recent Albums". New menu entries
reuse stock dispatcher types 7 and 9, which stock never emits.

### 1.6 Persistence

nanitecfw never touches SAVEINFO. Its new data lives in the media-library
database's spare space on the device: dedicated sectors
(`SEC_SONGS_BY_ALBUM 0x52140`, `SEC_ALBUM_GROUPS 0x52160`,
`SEC_RECENT_GROUPS 0x52380`, `SEC_ARTIST_SONGS 0x52800`,
`SEC_ARTIST_GROUPS 0x52820`, `SEC_ARTIST_ALBUMS 0x528a0`, `SEC_KEYS 0x52a00`,
`SEC_HASHES 0x52d00`, `SEC_DATES 0x52e80`; `MAX_SONGS 8192`) and spare
record fields (`REC_TRACK_ARTIST +0x100`, `REC_DATE +0x2F8`; stock keeps
album-artist at `+0x500`). This works because the DB layout is theirs to
extend once the refresh pipeline is hooked. For the Neo, our SAVEINFO
verbatim block `+0x1C7..+0x2D5` (phase-2 finding: gap fields do *not*
survive a save) is the equivalent config home; DB-sector extension remains
available for library data if we hook the Neo's refresh the same way.

### 1.7 Feature inventory, mapped to our targets

- Library / sorting: the flagship, and the best worked example in any
  of these sources. Stock refresh of 2,000 FLAC files drops from ~148 s
  to ~28 s. Method: during the walk, hooks at the stock record-build sites
  (module 39: `0x0307aade`, `0x0307ae46`, `0x0307b086`) write a compact
  8-byte sort key plus an FNV-1a hash of the full key into spare DB space;
  `cfw_keyread` replaces the stock key reads (hooks at `0x03079a48`,
  `0x03079a62`); `cfw_cmp` wholesale-replaces the stock comparator
  (`hook: 40 03079810 b cfw_cmp`), settling ties by hash so ordering is
  unchanged but comparisons are O(1)-ish. Plus the `fread` window hook
  (§1.4.4).
- Recent Albums: folder FAT creation dates are captured in a directory
  hook, stored at record `+0x2F8`, and a shellsort builds a group table at
  `SEC_RECENT_GROUPS`; setup patches keyed on title string `0x87` point the
  stock browser at it.
- Artists vs Album Artists: a second sort pass reuses the stock
  `mod40_levels` machinery with its `SORT_TABLES`/`SORT_FIELDS` globals
  rewritten; the artist count is smuggled to the UI through group entry 0's
  `u16[3]`.
- Shuffle (control change): implemented as a control-change model:
  repurposed menu slot + cave route (§1.5), plus a module-23 key-handler
  cave that rewrites the fetched key into "select" (`0x40000040`) with the
  cursor randomized from ticks XOR SysTick (`0xe000e018`). This is the
  concrete template for key-remapping work: intercept the key after fetch,
  rewrite it, let stock dispatch run.
- Bug fix (`skip_unsupported.patch`): `33:03082ef2:00bf` (nop) +
  `33:03082f04:0a2845d200bf00bf` makes playback stop after 10 consecutive
  unplayable files instead of grinding through a folder of unsupported
  tracks. Two data patches; a stock edge case fixed at the symptom site.
- Power: two patch files that map directly onto our battery-profiles
  goal:
  - `power_clocks.patch` is a *pure data patch* rewriting the clock
    manager's request table (module 00, table at `0x03076324`, 36 rows ×
    `0x1C`; requests via `FUN_0306aee4`, summed by `FUN_0306ad00`; floor
    row 1 = 96 MHz, cap row 35). Per-codec rows zero their A fields and
    cut the B core: MP3/WMA/AAC/WAV 348–450 MHz → 144 MHz, OGG → 240,
    FLAC/ALAC → 288; APE/OGG-hi/DSD untouched. No voltage scaling exists
    to worry about.
  - `power_idle.patch` is two one-instruction patches. Module 00 main
    loop at `0x0306a16c`: message id `0x18`→`0x1f` plus a `beq`/`bne`
    inversion so WFI runs even with the screen on, plus a wheel-poll
    period change 400→1000 µs (`4ff47a72` = `mov.w r2,#1000`) at four
    sites (mod00 `0x0306b2cc`, mod01 `0x03079f9c`, mod09 `0x0307c4a8`,
    mod33 `0x03082b7c`).
- Cosmetic: `about_version.patch` = `32:0307cf14:u"6.0.6"`, proof the
  data-patch grammar handles one-off string swaps trivially.
- Absent: no gapless work, no lock-screen work, no playlist-file (M3U)
  support, no EQ work, no SAVEINFO use. Its known-issues list includes
  shuffle order not surviving a power cycle.

### 1.8 Usefulness and limits for the Neo

Usefulness: maximal for method. The patch grammar, the SHA gate, the
date-bump finalize, the cave discipline, the hooks manifest, the wrap
profiler, runtime self-patching, and the power patches are all directly
adoptable; MIT licensing allows copying the tooling outright. Our existing
offline patcher already implements the container half (mirror + CRC); what
nanitecfw adds is the *authoring layer*, and that layer is what our
patcher lacks. Patch files in a text grammar, `.S` patches assembled
at the target address against a shared symbols include, a hooks
manifest that generates the route patches, and a C blob whose exports
flow back into the assembly patches as symbols (§1.3, §1.4). §5 point 1
adopts it wholesale; the rest of this section is about what adoption
does not give us.

*Reconstructed 2026-10-31: the original text from this point to the end
of §1.8 was lost to a truncation in this document's first commit. The
text that follows is rewritten from the project's source material (the
nanitecfw clone at `refs/nanitecfw` and the surviving sections of this
document).*

Limits, in roughly the order they will bite:

- Every address is V1.7.0-only, and the project says so itself. Its
  README states that other firmware versions are not supported, because
  the patches are written for the exact code addresses of V1.7.0. The
  same holds for us with the devices swapped: our framework keys on the
  `DP3_V137` SHA for the same reason, and a Fosi point release means
  re-deriving the sites in every module that changed. That is the
  technique's standing cost, not a defect in either project.
- The Echo Nano has no Bluetooth hardware, which is why its stock
  Bluetooth strings were free to repurpose as labels for new menu
  entries (§1.5). The Neo has a working Bluetooth module (module 81)
  and its Bluetooth strings are live. String repurposing still works
  on the Neo, but it needs a different set of dead strings, and
  finding them is its own small RE task.
- Residency is stricter on the Neo. nanitecfw stages its blob in
  module 40's sort buffer and hooks the refresh driver to load module
  40 around the library work (§1.3c, §1.4). On the Neo, module 0 is
  the only always-resident home; a blob staged in an overlay window
  exists only while that overlay is loaded. Whether the Neo has a
  dead region comparable to their 64 KB sort buffer is a question for
  our own xref pass over its 82 modules, using the three cave classes
  of §1.5 as the search pattern.
- Persistence runs the other way. nanitecfw never touches SAVEINFO;
  everything new lives in spare DB sectors and record fields (§1.6),
  which works because all of its features are library features. Our
  goals include settings (battery profiles, control maps), and for
  those the Neo's SAVEINFO verbatim block is the home. The DB-sector
  route stays available for library data if we hook the Neo refresh
  the same way.
- Coverage is the hard limit. Of the six feature goals, nanitecfw
  ships a finished implementation for one (library views and
  sorting), a near-complete design for one (battery profiles, as two
  patch files against the same clock and idle architecture the Neo
  runs), and a working template for one (control changes, via the
  shuffle key cave of §1.7). For gapless, M3U playlists, and
  lock-screen info it has nothing, because the Echo Nano work never
  needed them (§1.7, §6). The method transfers to those goals. No
  code does.
- Its known-issues list marks the approach's maturity honestly.
  Shuffle order is not kept across power cycles. Playback can freeze
  on some files that show "Format Not Supported!", cause not found.
  The 6.0.5 power saving is untested on hi-res files (FLAC 24/192).
  A shipped, daily-used patch firmware still carries bugs of exactly
  the classes we would inherit: state that does not survive a power
  cycle, and stock edge cases that only real files expose.
- Adopting the tooling also adopts its toolchain floor: GNU make
  4.3 or newer and arm-none-eabi binutils 2.39 or newer, or the
  repo's nix shell (§1.2). Minor next to the RE, but it is a real
  prerequisite for anyone rebuilding the patches from source.

None of this argues against adopting it. It argues for adopting it
with the RE budget stated up front: the method is proven, the
addresses are ours to earn, and half the feature goals still start
from a blank page.
## 2. echo-mini-fw: resource modding for the SNOWSKY ECHO (not the Mini)

### 2.1 Correction to the brief

Despite the repo name, this tool targets the full-size SNOWSKY ECHO
(stock `ECHOV190.IMG`, V1.9.0, the 480×222 cassette-style player with dual
CS43198, 91 segments, 819 images, 453 strings per language). It explicitly
does not support the Echo Mini (`HIFIECxx.IMG`). There is no LICENSE
file in the repo. Treat as all-rights-reserved: read for facts and
formats, do not copy code into our repo.

### 2.2 What the tool does

`echofw.py` (365 lines, Python 3 + Pillow; subcommands `info`/`unpack`/`pack`)
is a resource editor only. It makes no code patches at all.

`unpack` produces, alongside a `base.img` copy:

- `images/NNN_NAME.png`: images stored as big-endian RGB565; the `NAME`s
  are recovered from 108-byte packer leftover records sitting after the
  image data (a vendor build artifact the tool exploits).
- `strings/NN_lang.tsv`: string records of 258 bytes: a 58-byte header
  (29 u16 tree fields) + 200 bytes of text, ≤ 99 chars.
- `code/segNN` binaries + `segments.tsv`: execution addresses, laid out
  for Ghidra/IDA import; the author did his RE from these exports.
- `raw/` blobs and `manifest.json`.

`pack` rewrites only changed bytes, in place: PNG dimensions must match
the original exactly, so no size or offset in the image ever moves. Text
changes can be supplied as repeatable `--text-patch` TSVs
(`lang ⇥ index ⇥ text`, `*` = all languages, later files win) and image
changes as `--images` override directories. It then refreshes the mirrored
tail header and the RK CRC32. An unedited unpack→pack round trip reproduces
stock byte-for-byte; the README publishes expected CRCs for its example
builds (mod `0x2a747924`, retro theme `0x2f55370c`), which is a good
determinism check to imitate.

### 2.3 The mods that ship with it

- `mods/text-fixes.tsv` (21 lines): the only text mod. Fixes the
  language-picker names in all languages (IDs 359/440 "Español", 366/447
  "Nederlands", 368/449 "Čeština") and a set of English labels: 97
  Recordings, 102 Resume Playback, 236 Cassette Style, 238 VU Meter Style,
  239 Rhythm Style, 247 Cross-Folder Skip, 259 Digital Filter, 268 Button
  Mode, 272 Swap Volume Buttons, 275 Lyrics, 342 "1 Minute", 349 "Midnight
  Black", 372 UAC Charging Mode, 381 Text Settings, 386 Background. Note
  IDs 259/268/272: the full-size Echo's stock already exposes a digital
  filter setting and button-mode options, vendor features, not mods.
- `mods/images/667_BKEY44.png`: a single badge image fix ("NON-OC" →
  "NON-OS"), done by transplanting a glyph from another badge.
- `themes/retro/make_retro.py` (numpy/Pillow, Windows fonts): generates
  two full themes, "Retro White" (iPod 2005) and "Retro Black" (Walkman
  2007), including boot/shutdown animations and a `text.tsv`.

### 2.4 Device-behaviour findings (cross-checks for our container rules)

From the author's RE, all consistent with our own Neo findings:

- Image header magic `0x76543210` at offset `0xC`; the device checks the
  `RKnanoFW` tag and the tail header copy, and never reads the
  trailing CRC (only PC tools do).
- The updater scans `\ECHOECHO.IMG`, then `\ECHOV100.IMG`–`\ECHOV498.IMG`,
  with no version comparison; install writes the backup slot in 8 KB
  chunks, header last, then copies over the primary and deletes the .IMG.
  (The Neo differs in detail, our validator compares BCD dates, but the
  write order and slot structure are the same family pattern.)
- Theme system: images ≥ 093 are themed; the black theme adds +363 to the
  image index, selected by a setting byte at `+0x349`; pure red
  (255,0,0) is the transparency key.
- Recovery is via FiiO's kit: BlackVllad's ECHO-Firmware-Tool plus
  RKDevelopTool/Rockusb in MASKROM mode.

The author's own README "Ideas" section names code patches (volume curve,
3-second prev-track threshold, button modes) as *future* work requiring
more RE and a brick-recovery path, independent validation that resource
modding is where this tool stops and patch projects like nanitecfw begin.
His longer RE write-up (im.not.ci, "The Story Behind Reverse Engineering
the Snowsky Echo Mini Firmware") independently found the firmware's 8-bit
CRC function, the SAVEINFO crc8 of §3.3, and confirmed by experiment that
flashing a modified image works, which matches the no-device-side-CRC
finding above.

### 2.5 Usefulness and limits for the Neo

Directly useful for the lowest-risk class of Neo changes: string and image
edits, using the same record formats (258-byte string slots with 58-byte
headers match the format nanitecfw patches, and our Neo string table is
the same family). Its unpack→segments export is also a decent second
opinion for Ghidra import. Limits: no code patching, no hooks, no feature
work; no license; target is a different device, so every offset must be
re-derived (as with §1).

---

## 3. The leaked Rockchip RKNanoD SDK (V1.3, 2016-11-02)

### 3.1 Provenance and license

Cloned shallow for this research to `refs/rknanod-sdk/` from
`github.com/EACHAN-YIN/RKNanoD_MP3_V1.3_20161102` (uploader commit
`6c96571`, 2019-07-22; tree ≈ 99 MB). A second mirror exists under
`xinghuaman` (same tree; referenced from Head-Fi and confirmed in search
results). This is Rockchip's RKNanoD MP3 SDK V1.3, released
2016-11-02. Every source file carries "Copyright (C), 2004-2015, Fuzhou
Rockchip Electronics Co., Ltd. All rights reserved": proprietary, no
open license. Reference only: do not copy SDK code into our repo. Its
value is as a naming/semantics Rosetta stone for the binary we already
have, and it is a genuinely good one: several of our hardest-won binary
findings are confirmed verbatim in source.

### 3.2 Tree inventory

293 `.h`, 229 `.c`, 32 `.lib`, 5 `.sct`.

- `Common/`: the framework: `BBSystem`, `BootLoader`, `Codec`, `Display`,
  `Driver`, `FileSys`, `FwUpdate/FwUpdate.c` (the on-device updater, in
  source), `Include`, `Plug`, `SortFileInfo`, `System`.
- `Documents/RKNanoD Software Development Kit Guide-V1.3.pdf`: listed,
  not deep-read for this report.
- `SDK_160_128/`: a complete sample project: `main.c`, `SysConfig.h`,
  `UI/` applets, `Build/` (Keil `RkNano.uvproj`, per-codec .bat files,
  `bin_generate.exe`), `Firmware/` (`GenUFw.exe` package builder +
  `GenUpdateFw.bat`), `Scatter/`, `Development/` (FactoryTool,
  firmware generators for eMMC/SPI, Rockusb drivers), `Resource/`.
- `ReadMeFirst.txt` (Chinese): supported formats mp3/wav/aac/ogg/ALAC/APE/
  FLAC/DSF/DFF, DSD64/128/256, APE ≤ 96 kHz caveat, Bluetooth transmit,
  USB host; requires Keil ≥ V4.72.1; package macros `RKNANOD_L/G/N`; the
  SPI-NOR variant has no media library.

### 3.3 Confirmations of our binary findings

Module/overlay flags. `Common/System/ModuleOverlay/ModuleOverlay.h:43-46`:

```c
#define MODULE_OVERLAY_CODE 0x01
#define MODULE_OVERLAY_DATA 0x02
#define MODULE_OVERLAY_BSS  0x04
#define MODULE_OVERLAY_ALL  0x07
```

Exactly our binary finding that loader flags 7 = code+data+BSS.
`ModuleOverlayLoadData(SrcAddr, DestAddr, Length)` is implemented in
`ModuleOverlay.c`. The module-info table structure and the `MODULE_ID`
enum live in `SDK_160_128/Scatter/ModuleInfoTab.h`, generated by the
scatter files (`Scatter/*.sct`, `ScatterLoader.c`). Numbering is
build-config-dependent and differs from Fosi's (sample: SYSCODE 0,
SYSINIT 1, USB 2, MAINMENU 3, MEDIALIBWIN 6, MEDIABRO 9, SETMENU 24,
AUDIO_CONTROL 31, AUDIO_EQ 34, FILEINFO_SAVE 38, FILEINFO_SORT 39,
MP3_DECODE 36, WAV 43, FLASH_PROG 50, FW_UPGRADE …). Use it to understand
the mechanism, never to guess a Neo module number.

SAVEINFO is `SYSCONFIG`. `Common/Include/global.h` (~lines 226–311)
defines the packed struct: `FirmwareFlag` "SAVE" (`0x45564153`),
`FirmwareYear`/`Date`, version fields marked "don't change", then the
settings body: `Memory`, `SysLanguage`, `ImageIndex`, `OutputVolume`,
`BLmode`, `BLevel` (backlight level), `BLtime`, `LockTime`, `ShutTime`,
`SDEnable`, `FMEnable`, `KeyNum`, `dwTotalMem`/`dwFreeMem`, `EQEnable`,
`AudioOutputMode`, `MEDIALIB_CONFIG`, directory-tree structs, and
`#ifdef`-gated sub-configs (MUSIC/VIDEO/RADIO/RECORD/TEXT/PICTURE, and
`BLUETOOTH_CONFIG` with `BtConfig.btOpened`, cf. the `gbBTSwitchOn`
macro at `global.h:381`; compare our phase-2 finding of BT state at Neo
SAVEINFO `+0x2D4`), closing with `DemoMode`, `ProuctionTestMode`,
`FMmodule`, `FindFileType`, `SafePoweroff`, `FirmwareCheck` "INFO"
(`0x4F464E49`), and `crc`. Because sub-configs are `#ifdef`-gated, the
layout is build-config-dependent: the struct is a field-naming key for
our binary SAVEINFO map, not an offset table.

The save path, step for step. `Common/System/ModuleOverlay/SysReservedOperation.c`
(793 lines):

- `sbc_crc8` (line 85): comment "len in bits", init `0x0F`, table-driven
  with a bit tail, polynomial `0x1D`, an exact match to the checksum our
  RE traced at `0x0306CAA6` (length `0x17E0` in bits, init `0xF`, table at
  `0x030058A9`).
- `LoadSysInformation` (line 109).
- `SaveSysInformation(int flag)` (line 726): zero a 2048-byte `TempBuffer`
  with `0xFF`; set `SafePoweroff = 0x55AA` if flag else 0;
  `crc = sbc_crc8(struct, (sizeof(SYSCONFIG)-4)*8)`; memcpy the whole
  struct; `ModuleOverlay(MODULE_ID_FLASH_PROG, MODULE_OVERLAY_ALL)`;
  `WriteReservedData(SYSDATA_BLK, TempBuffer, 2048)`. This is our binary
  saver `0x0306CA10(arg)` step for step, including the module load
  immediately before the write (the Neo loads its module 2; the SDK sample
  loads FLASH_PROG, same pattern, config-specific ID). It also explains
  *why* only the verbatim block survives (§0): the saver serializes the
  struct it has, and anything outside the struct definition is not in the
  buffer.
- `BackupSysInformation` (line 768) writes the ASCII magic `FWUP` at
  `TempBuffer[2044..2047]`, the FWUP magic our boot-path RE saw in
  settings reads.

Window framework. Each applet header `SDK_160_128/UI/<Win>/<Win>.h`
defines a global struct, e.g. `WIN MusicWin = { NULL, NULL, Service,
KeyProc, Paint, Init, DeInit }` (`MusicWin.h` ~lines 110–132), matching
our binary WIN layout (+0x08 Service, +0x0C Key, +0x10 Paint/Display,
+0x14 Init, +0x18 DeInit). Applets: Browser, CharegeWin, MainMenu,
MusicWin, PicWin, RadioWin, RecordWin, SetMenu, TextWin, USB, VideoWin,
dialog, medialib. Applets run on a thread system (e.g.
`MusicWinInterface.c`: `MusicWinSvcStart` does ThreadCheck/
ThreadDeleteAll, `ModuleOverlay(MODULE_ID_AUDIO_CONTROL, ALL)`,
ThreadCreat), the same Service-thread model our RE inferred.

### 3.4 What's in the box, by subsystem

- Codecs (`Common/Codec/Audio/<fmt>/`): glue source (`pMP3.c`,
  `p_hifi_flac.c`, …) plus closed `.lib` decoder libraries
  (`RkNanoD_BMP3_20161031.lib`, `RkNanoD_BHFLAC_20160807.lib`) and
  prebuilt `*_code.bin`/`*_data.bin` second-core images, the same
  core-1 image pattern our phase-2 RE found being re-copied on every
  codec open. Also `RkEQ/` (EQ and effects), an SSRC resampler, Spectrum,
  ShuffleAll, sbc. `Common/Codec/BlueTooth/lwbt` is A2DP source aimed at
  a Realtek RTK8761A; the Neo's BT module speaks a different ('CV1'
  banner) protocol, so the SDK BT code is framework reference only.
- Library (`Common/SortFileInfo/`): the media-library machinery in
  source: `FileInfoSave.c` (scan/save), `FileInfoSort.c`, `SortInfoGet.c`,
  `FavoOperate.c` (favourites / "Playlist A–D" operations, internal
  playlists, not M3U files), and `AddrSaveMacro.h` with the DB
  sector-layout macros (e.g. `MUSIC_SAVE_INFO_SECTOR_START 0`). This is
  the source counterpart of the modules nanitecfw hooks (§1.7) and of our
  Neo modules in the same lineage.
- Drivers (`Common/Driver/`): SDMMC, MemDev/SD_MMC, I2C, IIS, DMA,
  GPIO, LCD, PMU, CRU, mailbox (the MU our phase-2 RE mapped), hifi, USB
  device/host, WatchDog. DAC drivers exist only for ALC5633 / wm8987 /
  rockcodec, not the Neo's CS43198, so driver source is pattern
  reference, not reusable code, for the one chip that matters most.
- Update/boot: `Common/FwUpdate/FwUpdate.c` and `Common/BootLoader/`
  in source; `GenUFw.exe` is how stock-class packages are built.

### 3.5 Usefulness and limits for the Neo

Usefulness: naming and semantics. When a Neo SAVEINFO offset, module flag,
or saver step is ambiguous in the binary, the SDK source settles what the
code *means* (the crc8 parameters and the FWUP magic are the two cleanest
examples). `SortFileInfo` and the WIN/applet sources shorten RE of any
library or UI patch site. Limits: the toolchain is Windows/Keil V4.72
(commercial), the decoders are closed libs, the sample UI project is
160×128 against the Neo's 240×320, and Fosi's build is a later, customized
configuration. §3.3's warning applies everywhere: structure transfers,
offsets and IDs do not. As a standalone-firmware base it is the *hardest*
of the available routes (see §4.1, §6), not the easiest.

---

## 4. Community landscape: what else exists

Surveyed 2026-10-31 (GitHub/web). The RKnano modding scene is small and
concentrated in the FiiO/Snowsky Echo family; almost everything reusable
is within one device-generation of the Neo.

### 4.1 Whole-firmware replacements: EchoPod and NeoPod

The only from-scratch firmware lineage for RKnanoD devices is
EchoPod by BasilSkyWalk (`github.com/BasilSkyWalk/echopod`, GPLv3;
local clone `refs/echopod-upstream/`, at release 0.6.0), a replacement
firmware for the Echo Mini (not a patch of stock): iPod-style Cover Flow
browser, on-device library, album favorites, M3U/M3U8 playlists, an
Up Next queue, and, inherited by its port, gapless MP3 (LAME-tag
encoder-delay/padding trim, with DAC fades around play/pause/seek/skip).
It is developed against a PC simulator that reproduces the player's
library/scan behaviour. EchoPod implements Bluetooth itself (its commit
history includes BT connection fixes) rather than reusing stock BT.

NeoPod (`github.com/danielNZ27/NeoPod-Fosi-DAP-Neo-Custom-Firmware`,
GPLv3; local clone `refs/NeoPod-…/`) is a direct hardware port of EchoPod
to our exact device, at v1.5.2: dual-core playback with per-format
decoder payloads (`neo_flac.bin`, `neo_mp3.bin`, Helix AAC `neo_aac.bin`,
libopus `neo_opus.bin`, WAV on the system core), a background library
scanner (`neo_scan.bin`), embedded/folder artwork, a 5-band custom EQ
(100/300/1k/3k/10k, ±12 dB, user presets) and ReplayGain (track/album,
peak anti-clip). It installs from stock and documents a path back
(accepts FiiO-format images for return-to-stock on the sibling; the local
`refs/Fosi-Dap-Neo-firmware-restore-tool/` covers Neo recovery).

The catch, for our purposes: NeoPod has no Bluetooth audio. Its
README feature list omits BT entirely and `docs/known-issues.md` lists
"No Bluetooth audio" under "Not there yet". BT transmit is a headline
stock feature of the Neo; adopting NeoPod wholesale trades it away.
NeoPod's gapless is likewise MP3-proven (LAME-tag dependent; files
without a LAME tag keep a short gap, per its known-issues) rather than a
general sample-accurate engine.

### 4.2 Rockbox: no RKnano port, and the closest Rockchip port is a dead end

- There is no Rockbox port to any RKnano target, and none was ever
  started in earnest. The only Rockchip entry in Rockbox's port list is
  "Rockchip RK27XX (generic)", classified unusable since ~2014
  ("Work has begun on porting Rockbox to these players, but much remains
  before they are usable", Marcin Bukat/wodz's early work; a hobbyist
  status report from that era shows it booting to a UI on Ramos
  RM970-class players with broken audio/video edges, and it never
  progressed further). RK27xx is a different, larger SoC family
  (application-processor class) than the RKnanoD microcontroller.
- Rockbox's tree does still carry host tools from that era:
  `utils/rknanoutils/` contains `rkboottool` and `rkload` (verified on
  GitHub, 2026-10-31), image/boot utilities, not a target port. A Head-Fi
  poster used `rkboottool` to extract `stage3.bin` from Echo Mini
  firmware, so the tooling does read this package family.
- Community assessment on Head-Fi is blunt: the SoC "has kilobytes of
  memory, not even megabytes like popular cheap SoC like Ingenic
  X1000/1600, so … you could never port anything like simple Rockbox to
  it". Our own RE agrees with the substance: the Neo's total SRAM is on
  the order of ~960 KiB across both cores, while Rockbox's smallest real
  targets assume megabytes. **Verdict: a literal Rockbox port is not a
  realistic path; "Rockbox-style" features reach this hardware only via
  the EchoPod-lineage firmware (§4.1), which was clearly designed in that
  spirit.**

### 4.3 Other tooling and write-ups

- BlackVllad's ECHO-Firmware-Tool + RKDevelopTool/Rockusb: the
  standard recovery/flashing route for the Echo family (MASKROM),
  the brick-recovery prerequisite every code-patch project in this
  family relies on (see §2.4).
- intelarc's RE blog (im.not.ci/echo-mini-rse/): an independent
  from-scratch RE narrative for the Echo Mini, useful chiefly as
  corroboration (§2.4) that modified images boot and that device-side
  verification is minimal.
- The Rockbox `rknanoutils` (§4.2) and the SDK mirrors
  (EACHAN-YIN and xinghuaman, §3.1) round out the public material.
  No other patch frameworks, mod projects, or SDK-family patch
  collections surfaced in the survey: for patching (as opposed to
  replacing) RKnano stock firmware, nanitecfw is the only published
  worked example.

### 4.4 Known stock-family bugs and edge cases

Fixed or documented by patch projects:

- Unsupported-file grind (Echo Nano stock): playback chews through
  folders of unplayable files; fixed by nanitecfw's `skip_unsupported`
  two-patch change (stop after 10 consecutive failures) (§1.7).
- Slow library refresh (Echo Nano stock): ~148 s for 2,000 FLAC;
  nanitecfw's key/hash redesign brings it to ~28 s (§1.7).
- Clock over-provisioning (Echo Nano stock): per-codec clock rows run
  the B core at 348–450 MHz where 144–288 MHz suffices; no voltage
  scaling. nanitecfw `power_clocks` (§1.7).
- No WFI with screen on (Echo Nano stock idle loop): fixed by
  `power_idle`'s message-id swap (§1.7).
- nanitecfw's own known issue worth knowing before copying its shuffle:
  shuffle order does not persist across power cycles.

Reported against Echo Mini stock on Head-Fi and fixed by *vendor* updates
(not patch projects), listed because the same SDK tag/sort code lineage
runs on the Neo, so the bug classes are the ones to probe for:

- Firmware 3.3.0 broke FLAC playback (MP3 unaffected).
- 3.x media library shows artists as "Unknown" or with corrupted
  characters for some libraries.
- M4A files sorted incorrectly (FiiO shipped a fix build).
- On 3.0/3.1, some tracks start a few seconds in.
- Long-running confusion over ID3v2.4 support and track-number sorting
  (zero-padding, "n/m" forms).

And one from our own RE that no community source documents: the Neo's
stock DAC error counter (phase-1 analysis), a reminder that this
codebase's edge cases are still being found, and patch projects should
expect to find Neo-specific ones of their own.

---

## 5. Combined lessons for our patch project

1. Adopt nanitecfw's authoring layer wholesale (MIT). Patch grammar
   (`MOD:ADDR:bytes`, `u"text"`, `lang:` lines), one patch file per
   change, `.S` patches assembled at their target address with a shared
   symbols include, hand-encoded branch macros, a hooks manifest with a
   `wrap` mode, and a generated symbols file for blob exports. Our
   existing offline patcher already does the container half (edit →
   mirror header → regenerate CRC); what it lacks is exactly this layer.
2. Keep the SHA gate and the date discipline. Refuse unknown stock
   builds; bump the image date past stock so the validator boots the
   patched slot (our phase-2 mechanics agree with nanitecfw's), and
   produce a `make recovery` equivalent, stock with a newer date, in
   the same build.
3. Cave discipline transfers; cave addresses don't. Dead functions,
   zero-filled data, and one very large scratch region (their 64 KB sort
   buffer) are the three cave classes to hunt in the Neo's 82 modules,
   using the same never-called/unreferenced xref tests. Anything placed
   in an overlay module must respect the shared-window loading model.
   Resident module 0 is the only always-present home, which is stricter
   than the Echo Nano's layout in one respect: a blob staged in an
   overlay is only resident while that overlay is.
4. Hook like they do. Prefer one-instruction route patches and
   literal-pool redirection over rewriting stock logic; reuse stock
   subroutines from cave/blob code through typed `FW()`-style pointers;
   use runtime self-patching (their `fread` window) only with the
   save/restore + DSB/ISB discipline they demonstrate, and keep a
   card-written debug log, it's the only console this class of device
   offers.
5. Persistence: our SAVEINFO block is the config home; DB sectors are
   the data home. nanitecfw proves spare DB sectors/record fields
   survive and are safe to extend once refresh is hooked. For settings,
   the Neo equivalent of a safe write is the SAVEINFO verbatim block
   `+0x1C7..+0x2D5` (phase 2), and §3.3's source explains the mechanism:
   the saver serializes only its struct into a 0xFF-filled 2048-byte
   buffer, so anything outside the saved span is silently dropped.
6. Use the SDK as a dictionary, not a donor. Field names
   (SYSCONFIG), flag semantics (overlay 7 = code+data+BSS), the crc8
   parameters, the FWUP backup magic, the WIN struct layout: all
   confirmed against source. Offsets, module IDs, and sample-project
   configuration do not transfer, and its code is proprietary: cite
   semantics, write our own.
7. Resource edits are the free wins. String/image changes via the
   §2 formats carry near-zero brick risk (in-place, size-preserving,
   CRC refreshed) and can ship before any code patch does.
8. Plan recovery before the first flash. Every project in this
   family treats a proven restore path (stock-with-newer-date image,
   Rockusb/MASKROM tooling) as a precondition for code patching, not an
   afterthought. Our phase-2 dual-slot findings (stock update flow
   converges the slots; keep update files off a dual-boot unit) slot
   into the same discipline.

## 6. Easiest path per goal

For each of the project's goals: the easiest known path, and what existing
work it rests on. "Nothing found" means the survey (§4) and the three
primary sources contain no implementation to reuse.

- Gapless playback. *Nothing found as a patch.* No RKnano patch
  project implements gapless. The only working implementation on this
  hardware family is EchoPod/NeoPod's (LAME-tag trim + fades, MP3-only,
  inside a replacement firmware). Easiest path keeping stock: our own
  phase-1 design (patch the track-transition path on stock): designed,
  with nothing to copy. Easiest path overall, if losing BT and the stock
  UI is acceptable: run NeoPod, which already ships gapless MP3 on this
  exact device.
- Lock-screen info. *Nothing found.* No project, patch or
  replacement, touches the lock-screen readouts on any device in this
  family. Easiest path: our own patch (phase-1 verdict: a moderate code
  patch against the lock window's Paint path, whose struct layout §3.3
  now confirms). Nothing to reuse beyond the WIN framework semantics.
- Bluetooth shortcut. *Nothing found.* nanitecfw's device has no BT;
  EchoPod reimplements BT inside a replacement; nobody has published a
  stock-BT control hook. The only concrete foothold is our own phase-2
  finding: module 81's callable toggle (`0x0307D1A8`/`0x0307D1B6`) with
  state at SAVEINFO `+0x2D4` (and §3.3's `BtConfig.btOpened` corroborates
  the state byte's meaning). Easiest path: a nanitecfw-style key-handler
  cave (§1.7 shuffle pattern) that calls the stock toggle, our work,
  their technique.
- M3U playlists. *Nothing found as a patch.* The SDK's `FavoOperate`
  is internal favourites (Playlist A–D), not files; nanitecfw has none.
  Real M3U/M3U8 support exists only in EchoPod/NeoPod. Easiest path
  keeping stock: our phase-1 design (feed M3U entries through the stock
  CUE parser path). Easiest overall: NeoPod.
- Library sorting / views. *The strongest reusable work of any
  goal.* nanitecfw's design, spare-field sort keys + FNV-1a hashes
  written from walk hooks, a replaced comparator, a windowed `fread`,
  spare-sector group tables for Recent/Artists views, is a complete,
  measured (5×) blueprint, and the SDK's `SortFileInfo` sources name the
  stock stages it hooks. Easiest path: port that design to the Neo's
  corresponding modules; every address must be re-derived, no design
  work remains.
- Battery profiles. *Easiest goal overall.* nanitecfw's
  `power_clocks` (pure data patch on the module-0 clock table) and
  `power_idle` (one-instruction WFI change + poll-period constants) are
  written against the same SDK clock/idle architecture the Neo runs.
  Easiest path: locate the Neo's clock-request table and main-loop
  message check (module 0, resident, no overlay complications) and
  apply the same edits, exposed as profiles via SAVEINFO
  `+0x1C7..+0x2D5`.
- Control remapping. *Technique found, no finished implementation
  for our case.* nanitecfw's `shuffle_key` cave is the working template
  (intercept the fetched key in a cave handler, rewrite it, let stock
  dispatch proceed), and the Echo family's stock history shows button
  modes are a normal firmware-level feature in this codebase. Easiest
  path: that template on the Neo's key path (phase-1 verdict stands:
  simple remaps are cave-sized; a general remapping UI is not).
- Standalone firmware. *Easiest path: fork, don't found.* NeoPod
  already runs on this exact device under GPLv3, with EchoPod upstream
  behind it. Forking it (and re-adding Bluetooth, its one big gap) is
  orders of magnitude less work than any alternative. The SDK route
  (Keil, closed decoder libs, 160×128 sample UI) is the hardest option
  despite being "official", and a literal Rockbox port is *nothing
  found/feasible*: the only Rockchip Rockbox work ever done (RK27XX,
  unusable, abandoned ~2014) targets a different SoC class, and the
  Neo's ~960 KiB SRAM sits far below Rockbox's floor. Our phase-2
  dual-slot plan (stock in one slot, custom in the other) composes with
  the NeoPod fork route: it is the safe way to run a fork on hardware
  while keeping a stock fallback.

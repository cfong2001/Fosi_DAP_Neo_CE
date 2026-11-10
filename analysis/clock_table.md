# Clock-configuration table in module 0: DP3_V137.img (Fosi DAP Neo)

**Verdict: found and fully decoded.** The clock manager's request table
(`g_CruAPPTabel` in SDK terms) sits at the very tail of module 0:

| | |
|---|---|
| Exec address | **0x03079824** |
| Module 0 code-bin offset | 0x29824 |
| Image file offset | **0x52ED0** (verified by byte search; exactly one copy in the image) |
| Size | **36 rows × 0x1C = 1008 bytes**, ending at 0x03079C14 = end of module 0's code segment |
| Solver | module 0 **FUN_03066EFC** (decompiled, §3) |
| Request/release | **0x030670E0** / **0x0306712C** (disable-aware pair, used by all callers found); secondary pair 0x03067064 / 0x030670A6 (no call sites found) |

A data-only patch on this table is viable (§6). This is the table a
Neo `power_clocks` patch would edit, with *more* headroom than the
Echo Nano original (§7).

---

## 1. How the row format was established (precedent first)

nanitecfw (`refs/nanitecfw/patches/power_clocks.patch`, MIT) patches
the same table on the FiiO Echo Nano stock firmware. Its header states:
table of 36 rows × 0x1C, fields *(id, PLL, A core, A hclk, A pclk,
B core, B bus)*, values in Hz; a solver sums the rows of all active ids,
floors each field at row 1, caps at row 35. Its patch lines rewrite
bytes +4..+27 of a row (24 bytes = fields 1–6), preserving word 0.
Decoding its patch bytes numerically confirms the encoding (LE u32 Hz):
MP3-class rows get B core/B bus = 96,000,000; OGG rows 192,000,000;
FLAC/ALAC rows 240,000,000 (solver outputs 144/240/288 MHz after the
base rows are summed in).

Leaked RKnanoD SDK (`refs/rknanod-sdk/Common/System/SysService/
PowerManager.{c,h}`, proprietary, naming/semantics reference only)
gives the source of the same design:

```c
typedef struct tagFREQ_APP_TABLE {
    uint8  scuAppId;   // +0x00
    uint8  counter;    // +0x01 (runtime refcount in the SDK build)
    uint32 PllFreq;    // +0x04
    uint32 syshclk;    // +0x08  "A core"
    uint32 sysstclk;   // +0x0C  "A hclk"
    uint32 syspclk;    // +0x10  "A pclk"
    uint32 calhclk;    // +0x14  "B core"  (calculation/decode core)
    uint32 calstclk;   // +0x18  "B bus"
} FREQ_APP_TABLE;      // sizeof = 0x1C with padding
```

and `FREQSetFreq(appList)` sums the six clock fields over all set bits
of a 64-bit app list, then clamps each field to the build's MIN row
(floor) and MAX row (cap). `FREQStartAPP(id)` / `FREQStopAPP(id)` set
and clear bits. The Neo's binary matches this design exactly (§3).

## 2. How the Neo table was located

Signature scan over module 0's code and data bins for stride-0x1C
records whose word 0 equals the row index (0,1,2,…) and whose six
clock fields are each 0 or a plausible Hz value. One hit:

- 0x03079824, 36 rows, 190 nonzero clock fields (code bin; the
  data bin had no hit).

Corroboration that this is the live table, not a lookalike:

- The pointer literal 0x03079824 is stored at 0x03066F9C in
  module 0 and referenced (Ghidra) from exactly one function,
  FUN_03066EFC, the solver (§3).
- Row 1 and row 35 contain exactly the floor/cap patterns the solver
  reads (offsets verified in §3).
- Rows 23–25 hold 36/72/140 MHz in all fields, the SDK's EQ_L/EQ/
  EQ_H values to the digit.
- Module 33's per-codec requests (§4) land on rows whose values form
  a coherent per-format ladder.

Not the DAC-brushed region: the records Phase 1 met near exec
0x030519C8 / file 0x47458 are the CS43198 register-init table at exec
0x0306DDAC, a different structure at a different address. The
clock-manager table is unrelated to it.

Hex excerpt (first 3 rows, from image offset 0x52ED0):

```
03079824: 00000000 00000000 00000000 00000000 00000000 00000000 00000000   row 0
03079840: 01000000 00d8b805 00d8b805 00d8b805 00d8b805 00000000 00000000   row 1
0307985c: 02000000 00d8b805 00d8b805 00d8b805 006cdc02 00000000 00000000   row 2
```
(0x05B8D800 = 96 MHz, 0x02DC6C00 = 48 MHz.)

## 3. The solver, decompiled from the Neo binary (FUN_03066EFC)

Ghidra decompilation, condensed to the load-bearing lines:

```c
undefined4 FUN_03066efc(uint appListLo, uint appListHi) {
    iVar2 = DAT_03066f9c;                    // = 0x03079824, the table
    // bit0 (IDLE) set  -> list = 1, floor disabled
    // list == 0        -> list = 2           (bit 1 = row 1)
    for (u = 0; u < 0x24; u++) {             // 36 rows
        if (bit u of appList set) {
            row = iVar2 + u * 0x1c;
            acc.pll += row[+4];  acc.syshclk += row[+8];
            acc.sysstclk += row[+0xc]; acc.syspclk += row[+0x10];
            acc.calhclk += row[+0x14]; acc.calstclk += row[+0x18];
        }
    }
    // floor: each field raised to ROW 1's field (base+0x20..+0x34)
    // cap:   each field clamped to ROW 35's field (base+0x3d8..+0x3ec)
    FUN_03066c36(&acc, DAT_03067230);        // apply: CRU divider programming
}
```

Verified against the bytes: table+0x20.. = row 1 fields
(96/96/96/96/0/0 MHz); table+0x3D8.. = row 35 fields
(480/200/200/80/480/480 MHz). So in this build floor row = 1,
cap row = 35, 36 rows, the same product-line layout nanitecfw
documented for the Nano, and the same sum-then-clamp semantics as the
SDK source. FUN_03066C36 and the divider code after it (udiv loops
around 0x03066D80) program the CRU (TRM chapter 3: every divider is `clk_src / (div_con + 1)`, `CRU_CLKSEL0_CON` at CRU offset `0x14`; see `rknanod_trm.md`); no voltage scaling appears
anywhere in the path (inference, matching nanitecfw's note for the
sibling build: savings from a clock patch are dynamic-power only).

Callers of the solver: FUN_03067064, FUN_030670A6, FUN_030670E0,
FUN_0306712C (start/stop pairs over a 64-bit app-list at 0x03067234's
target) and FUN_03067192 (re-enable path). All cross-module call
sites found use the 0x030670E0 / 0x0306712C pair.

## 4. Who requests which row (call-site evidence)

Capstone sweep of every module's code bin for branches to the
request/release pair, with the id recovered from the preceding
`mov r0, #imm`:

| Caller | Rows | Notes |
|---|---|---|
| mod33 @0x03088588 (TBB switch on CurrentCodec [0x0304B4D4]) | 5–22 | the codec rows, §5 |
| mod34 (playback teardown) | stops 5–22 | mirror of mod33 |
| mod11 | start/stop 4 | audio-init path |
| mod01 (validator/boot) | start 3 ×2 | boot-time request |
| mod10 | start 3, stop 31 | |
| mod18 (metadata/cover parser) | start/stop 26 | parse bursts |
| mod05 (settings/library service) | start/stop 30; start/stop 35 | library work at full speed |
| mod31 (player window) | start/stop 35 ×2 | full-speed bursts |
| mod61 (recording window) | start/stop 28 | record/encode |
| mod12 | start 3 | |

Rows never requested by an immediate call site: 0, 1, 2, 12, 13,
23, 24, 25, 27, 29, 32, 33, 34. Rows 0/1 are solver-internal
(IDLE/MIN). The rest are either requested through computed ids
(not seen) or vestigial in this build, labeled as inference in §5
where assigned at all.

Module 33 switch detail (TBB at 0x03088592, table bytes at
0x03088596; index = CurrentCodec, 0–9, same order as decoder modules
71–80). The switch reads the current file-info struct (control block
0x0304AD70 → [+8]; +8 = sample rate, +0xC = bitrate, +0x10 = a
1/2-valued field) to pick tiers:

- case 0 (MP3): bitrate ≤ 128,000 and rate ≤ 44,100 → row 5,
  else row 6
- case 1 (WMA): tier tests on rate (32,000 special-cased; 44,100 /
  ~48,000 windows) and bitrate → row 7 or 8
- case 2 (AAC): bitrate ≤ 128,000 and rate ≤ 44,100 → row 11,
  else row 10
- case 3 (WAV): unconditional → row 9
- case 4 (OGG): bitrate/field tiers → rows 14, 15, 16 (equal
  clocks) or 17 (top tier)
- case 5 (FLAC) → 18; case 6 (ALAC) → 19; case 7 (APE) →
  20; case 8 (DSD-DFF) → 21; case 9 (DSD-DSF) → 22
  (direct, no tier test)

Cross-check: nanitecfw's published Nano row comments, rows 5,6 MP3
(row 5 "≤128k/44.1k"), 7,8 WMA, 9 WAV, 10,11 AAC, 14–16 "type 4"
(OGG), match this assignment row for row. (Evidence grade: codec
assignment is *proven* for the switch structure and tier conditions;
the codec-name↔case mapping rests on the decoder-module order from
Phases 1/2 plus the Nano cross-check. Strong, but the names are
inference, not strings in the binary.)

## 5. The decoded table (all values MHz)

Columns: PLL, A core (syshclk), A stclk, A pclk, B core (calhclk),
B bus (calstclk). Row = id.

| Row | PLL | A core | A stclk | A pclk | B core | B bus | Assignment (evidence) |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 | 0 | 0 | IDLE: solver-internal |
| 1 | 96 | 96 | 96 | 96 | 0 | 0 | **MIN: solver floor** (proven, §3) |
| 2 | 96 | 96 | 96 | 48 | 0 | 0 | unassigned; INIT/BLON-class (inference) |
| 3 | 200 | 96 | 96 | 48 | 0 | 0 | boot/init row: started by mod01, mod10, mod12 |
| 4 | 48 | 48 | 48 | 48 | 48 | 48 | audio init: mod11; SDK AUDIO_INIT values |
| 5 | 96 | 48 | 48 | 48 | 96 | 96 | **MP3** ≤128 kbps, ≤44.1 kHz |
| 6 | 200 | 100 | 100 | 75 | 200 | 200 | **MP3** high |
| 7 | 200 | 150 | 150 | 75 | 300 | 300 | **WMA** tier |
| 8 | 200 | 150 | 150 | 75 | 300 | 300 | **WMA** tier |
| 9 | 450 | 200 | 200 | 75 | 450 | 450 | **WAV** (unconditional) |
| 10 | 200 | 150 | 150 | 75 | 300 | 300 | **AAC** high |
| 11 | 200 | 150 | 150 | 75 | 300 | 300 | **AAC** low |
| 12 | 200 | 150 | 150 | 75 | 300 | 300 | unrequested; duplicates AAC-tier values (inference: spare/vestigial) |
| 13 | 200 | 150 | 150 | 75 | 300 | 300 | unrequested; same |
| 14 | 300 | 80 | 80 | 80 | 400 | 400 | **OGG** tier 1 |
| 15 | 300 | 80 | 80 | 80 | 400 | 400 | **OGG** tier 2 |
| 16 | 300 | 80 | 80 | 80 | 400 | 400 | **OGG** tier 3 |
| 17 | 480 | 200 | 200 | 80 | 480 | 480 | **OGG** top tier |
| 18 | 480 | 200 | 200 | 80 | 480 | 480 | **FLAC** |
| 19 | 480 | 200 | 200 | 80 | 480 | 480 | **ALAC** |
| 20 | 480 | 200 | 200 | 80 | 480 | 480 | **APE** |
| 21 | 480 | 200 | 200 | 80 | 480 | 480 | **DSD-DFF** |
| 22 | 480 | 200 | 200 | 80 | 480 | 480 | **DSD-DSF** |
| 23 | 36 | 36 | 36 | 36 | 36 | 36 | EQ_L (SDK value match) |
| 24 | 72 | 72 | 72 | 72 | 72 | 72 | EQ (SDK value match) |
| 25 | 140 | 140 | 140 | 140 | 140 | 140 | EQ_H (SDK value match) |
| 26 | 450 | 200 | 200 | 75 | 0 | 0 | metadata/cover parse bursts: mod18 |
| 27 | 24 | 24 | 24 | 24 | 0 | 0 | utility, 24 MHz class (BLON/BEEP/search); no caller found |
| 28 | 300 | 200 | 200 | 75 | 400 | 400 | record/encode: mod61 |
| 29 | 24 | 24 | 24 | 24 | 0 | 0 | utility, 24 MHz class; no caller found |
| 30 | 400 | 200 | 200 | 75 | 0 | 0 | library/media update: mod05 (SDK MEDIAUPDATA pattern) |
| 31 | 400 | 200 | 200 | 75 | 400 | 400 | USB-class (SDK USB pattern); stop call in mod10 |
| 32 | 24 | 24 | 24 | 24 | 0 | 0 | utility, 24 MHz class; no caller found |
| 33 | 100 | 100 | 100 | 75 | 0 | 0 | media-init class (SDK MEDIA_INIT/AVI pattern); no caller found |
| 34 | 400 | 120 | 120 | 75 | 0 | 0 | unassigned A-only row; no caller found |
| 35 | 480 | 200 | 200 | 80 | 480 | 480 | **MAX: solver cap** (proven, §3); also requested directly by mod05/mod31 for full-speed bursts |

## 6. What stock actually runs during playback

Solver output for the codec row alone (sum → floor row 1 → cap
row 35). Concurrent rows from other services add on top before
clamping (e.g. if row 4 is also held, add 48 MHz to every field.
The Nano's music service held base rows during playback; which base
rows the Neo holds at runtime is not proven offline).

| Playback | PLL | A core/stclk/pclk | **B core (decode)** |
|---|---|---|---|
| MP3 ≤128k/44.1k | 96 | 96/96/96 (floored) | **96** |
| MP3 high | 200 | 100/100/96 | **200** |
| WMA / AAC | 200 | 150/150/96 | **300** |
| WAV | 450 | 200/200/96 | **450** |
| OGG tiers 1–3 | 300 | 96/96/96 (floored) | **400** |
| OGG top / FLAC / ALAC / APE / DSD | 480 | 200/200/96 | **480** (at cap) |

Headline: the decode core runs at 300–480 MHz for nearly every
format, plain WAV included, and the system core at 150–200 MHz.
Only low-bitrate MP3 drops to 96 MHz.

## 7. Patchability and headroom

**Data-only edit: viable.** The values are plain LE u32 Hz in the
image; there is no per-module checksum and no integrity check over
module 0's data beyond the update package's CRC-32 + mirrored header,
both of which the existing offline patcher already recomputes.
Rules that apply (same as any image patch): preserve word 0 of each
row (id/counter), write fields at +4..+27 exactly as nanitecfw
does, and keep the patched image's header date newer than stock
for the slot-2 boot rule.

Interactions to respect:

- *Floor:* A-field values below row 1's are clamped up (A floor =
  96/96/96/96). Zeroing a codec row's A fields, nanitecfw's approach,
  parks the A core at the 96 MHz floor during playback instead of
  150–200. B fields have floor 0, so B cuts are unclamped below.
- *Cap:* nothing can exceed row 35 (480/200/200/80/480/480) no
  matter what a codec row says.
- *PLL:* summed like the other fields; nanitecfw zeroed it and let
  the solver/CRU code pick. Same solver here, but the Neo's apply
  path is unverified on hardware. Keep PLL edits conservative
  until a unit can confirm.
- *EQ rows 23–25 add on top* during EQ playback, as on the Nano.

Headroom vs the Nano precedent: nanitecfw shipped (Echo Nano)
solver outputs of B = 144 MHz (MP3/WMA/AAC/WAV), 240 (OGG),
288 (FLAC/ALAC), A at the 96 floor, from stock B of 348–450. Neo
stock B is equal or hotter (300 WMA/AAC, 450 WAV, 400–480 OGG,
480 lossless/DSD), so at least the same cuts are available on
every format, and larger ones on WAV and the hi-res tier. A Neo
patch mirroring theirs would write, per codec row: PLL 0, A fields
0, B core/B bus = 96 MHz (rows 5–13), 192 MHz (rows 14–17),
240 MHz (rows 18–20), leaving DSD rows 21–22 and the record row 28
unchanged until their decode load is measured (DSD was left
unchanged on the Nano too). Expected solver outputs then match
theirs (144/240/288) if row 4 is concurrently held, or 96/192/240
from the codec row alone. This is a proposal, not an applied patch;
nothing has been flashed and no unit exists yet to validate it.

## 8. Method / reproducibility

- Format precedent: `refs/nanitecfw/patches/power_clocks.patch`
  (bytes decoded numerically); SDK struct + solver source in
  `refs/rknanod-sdk/Common/System/SysService/PowerManager.{h,c}`
  (reference only, proprietary).
- Location: Python signature scan (stride 0x1C, sequential ids,
  Hz-plausible fields) over `extracted/module_00_code_03050000.bin`
  and `module_00_data_03004000.bin`; file offset verified by
  searching the full image for the table bytes (one copy).
- Referencing code: Ghidra 12.2 (JDK 25) scratch project on
  `ghidra-input/mod0.elf` / `mod33.elf`: RefsTo + DecompileAt
  scripts in `ghidra-scripts/`; Rizin 0.9.1 for the mod33 TBB switch
  (Ghidra's jump-table recovery failed on this overlay, as before);
  Capstone (venv) for the cross-module call-site sweep.

# Clock table v1: tuned per-codec clocks for DP3_V137 (data-only patch)

**Status: built and verified offline. Nothing flashed; no unit exists yet.**
Stock SHA-256 `fcc1cd3e…deef` → patched `e4eb34d4…0d0a` (revision 2026-11-12; first release `f5a31274…ac3`)
(`DP3_V137_clock_v1.img` in this directory, produced by
`build_clock_v1.py`, independently reproduced and checked by
`verify_clock_v1.py` → `verify_clock_v1_output.txt`: **all checks passed**).

Target: the 36-row clock-request table in module 0, exec `0x03079824`,
image offset `0x52ED0` (evidence: `work/perf/clock_table.md`). The
solver `FREQSetFreq` (0x03066EFC) sums each Hz field over the active
request bitmap, floors each field at row 1, caps at row 35. One spec
per codec row edits fields +4..+27 (24 bytes); word 0 (id/counter) is
never touched; the header date is unchanged (the stock+1 date
discipline is applied at framework image-assembly time, deliberately
excluded here so this patch composes and stays byte-identical to
stock outside the table + trailer CRC).

Per-row edit pattern, mirroring nanitecfw's `power_clocks.patch` field
choices: A core / A stclk / A pclk → 0 (the solver's row-1 floor then
parks every A output at 96 MHz during playback); B core / B bus → the
class target from `research/performance_maximization.md` §3.4
(144 MP3-class / 240 OGG / 288 hi-res). PLL is the one deliberate
deviation. See Flag 2.

## Row-by-row changes (values in MHz, row contents, stock → new)

| Row | Format | Field changes |
|---|---|---|
| 5 | MP3 <=128k, <=44.1k | PLL 96 (=); A core 48->0; A stclk 48->0; A pclk 48->0; B core 96->144; B bus 96->144 |
| 6 | MP3 high | PLL 200 (=); A core 100->0; A stclk 100->0; A pclk 75->0; B core 200->144; B bus 200->144 |
| 7 | WMA tier A | PLL 200 (=); A core 150->0; A stclk 150->0; A pclk 75->0; B core 300->144; B bus 300->144 |
| 8 | WMA tier B | PLL 200 (=); A core 150->0; A stclk 150->0; A pclk 75->0; B core 300->144; B bus 300->144 |
| 9 | WAV | PLL 450 (=); A core 200->0; A stclk 200->0; A pclk 75->0; B core 450->144; B bus 450->144 |
| 10 | AAC high | PLL 200 (=); A core 150->0; A stclk 150->0; A pclk 75->0; B core 300->144; B bus 300->144 |
| 11 | AAC low | PLL 200 (=); A core 150->0; A stclk 150->0; A pclk 75->0; B core 300->144; B bus 300->144 |
| 14 | OGG tier 1 | PLL 300 (=); A core 80->0; A stclk 80->0; A pclk 80->0; B core 400->240; B bus 400->240 |
| 15 | OGG tier 2 | PLL 300 (=); A core 80->0; A stclk 80->0; A pclk 80->0; B core 400->240; B bus 400->240 |
| 16 | OGG tier 3 | PLL 300 (=); A core 80->0; A stclk 80->0; A pclk 80->0; B core 400->240; B bus 400->240 |
| 17 | OGG top tier | PLL 480 (=); A core 200->0; A stclk 200->0; A pclk 80->0; B core 480 (=); B bus 480 (=) |
| 18 | APE | PLL 480 (=); A core 200->0; A stclk 200->0; A pclk 80->0; B core 480 (=); B bus 480 (=) |
| 19 | FLAC | PLL 480 (=); A core 200->0; A stclk 200->0; A pclk 80->0; B core 480->288; B bus 480->288 |
| 20 | ALAC | PLL 480 (=); A core 200->0; A stclk 200->0; A pclk 80->0; B core 480 (=); B bus 480 (=) |
| 21 | DSD-DFF | PLL 480 (=); A core 200->0; A stclk 200->0; A pclk 80->0; B core 480 (=); B bus 480 (=) |
| 22 | DSD-DSF | PLL 480 (=); A core 200->0; A stclk 200->0; A pclk 80->0; B core 480 (=); B bus 480 (=) |

## Solver outputs, codec row alone (MHz): headline rows

Full 16-state × 6-field table is in `verify_clock_v1_output.txt`; the
replica was first validated by reproducing all 16 published stock
outputs in clock_table.md §6 exactly.

| Playback state | B core stock → v1 | A core/stclk/pclk stock → v1 | PLL stock → v1 |
|---|---|---|---|
| MP3 ≤128k/44.1k (row 5) | 96 → **144** | 96/96/96 → 96/96/96 | 96 → 96 |
| MP3 high (row 6) | 200 → **144** | 100/100/96 → 96/96/96 | 200 → 200 |
| WMA / AAC (rows 7,8,10,11) | 300 → **144** | 150/150/96 → 96/96/96 | 200 → 200 |
| WAV (row 9) | 450 → **144** | 200/200/96 → 96/96/96 | 450 → 450 |
| OGG tiers 1–3 (rows 14–16) | 400 → **240** | 96/96/96 → 96/96/96 | 300 → 300 |
| OGG top (row 17) | 480 → 480 | 200/200/96 → 96/96/96 | 480 → 480 |
| FLAC (row 19) | 480 → **288** | 200/200/96 → 96/96/96 | 480 → 480 |
| APE / ALAC / DSD (rows 18, 20–22) | 480 → 480 | 200/200/96 → 96/96/96 | 480 → 480 |

## Verification (verify_clock_v1.py: all passed)

- Solver replica reproduces clock_table.md §6 stock outputs for all
  16 codec rows before being trusted for v1 numbers.
- (a) Every in-scope codec-alone state hits its target B core **and**
  B bus output (144 / 240 / 288 by class).
- (b) A core, A stclk, A pclk outputs are at the 96 MHz row-1 floor
  for every in-scope codec-alone state.
- (c) 260 bytes differ from stock in total: 256 inside the table +
  the 4-byte trailer CRC (recomputed, verified = `rk_crc32` of the
  body). Header mirror region byte-identical. Nothing else differs.
- (d) Word 0 of all 36 rows untouched; all 20 out-of-scope rows
  byte-identical (rows 0–4, 12, 13, 23–35, including EQ 23–25,
  record 28, library 30, floor 1, cap 35).
- (e) `firmware_patch.validate()` passes on the patched image; each
  of the 16 specs was also run individually through
  `firmware_patch.patch()` against stock during the build, and the
  verify script's from-spec rebuild is byte-identical to the build
  script's image.
- Each spec is one `firmware_patch.patch()` call:
  `{module: 0, region: "code", address: <row exec +4>, expect, replace}`
  in `clock_v1.patch.json`; `clock_v1.patch` carries the same edits
  in nanitecfw grammar for the framework.

## Revision 2026-11-12: Rockchip's own figures as a floor

Two corrections, both checked against Rockchip's RKNanoD SDK
(`Common/System/SysService/PowerManager.c`, the `g_CruAPPTabel` table;
reference only, not copied here):

- **Rows 18 and 19 were mislabelled.** Running the firmware's extension
  classifier under emulation shows `.APE` is codec 5 and `.FLA` codec 6,
  so the module 33 switch sends APE to row 18 and FLAC to row 19
  (`analysis/clock_table.md` §4, correction). v1 as first written ran APE
  at 288 MHz and called it FLAC.
- **No decoder runs below the SDK's figure for its class.** The SDK
  clocks the decoder core at 400 MHz for high-rate APE, ALAC and DSD
  (`FREQ_HAPE`, `FREQ_HALAC`, `FREQ_DSDIFF`, `FREQ_DSF`) and at 260 MHz
  for the top Vorbis tier (`FREQ_EHOGG`), above the 288 and 240 v1 first
  wrote, and CE also runs a heavier full-precision Vorbis decoder. With
  the decode loads unmeasured, rows 17, 18, 20, 21 and 22 keep stock's
  480 MHz decoder clock. FLAC (row 19) stays at 288, above the SDK's
  220 MHz for high-rate FLAC (`FREQ_HFLAC`); MP3, WMA, AAC and WAV at 144
  and the lower Vorbis tiers at 240 are also above the SDK's figures (36
  to 180 MHz). The system-core floor of 96 MHz is above the 80 MHz the
  SDK uses for these classes.

The SDK's solver resolves a request whose PLL field does not divide
evenly (row 5: decoder 144 MHz over a 96 MHz PLL field) by searching for
a PLL that does, and caps the system bus at 300 MHz and every divider
at 8. Every v1 row stays inside those limits.

## Flags and conflicts (read before flashing)

1. **Written values vs nanitecfw's written values.** nanitecfw wrote
   B = 96/192/240 MHz into the Nano's rows and reached solver outputs
   of 144/240/288 because the Nano music service holds row 4
   (+48 MHz in every field) concurrently with the codec row. Which
   base rows the Neo holds during playback is **not proven offline**
   (clock_table.md §6). v1 therefore writes the §3.4 targets
   (144/240/288) directly into the codec rows, so the outputs are
   exact under the proven codec-row-alone model. Sensitivity, from
   the verify script: if the Neo does hold row 4 during playback,
   runtime B outputs become 192 / 288 / 336, +48 over target, still
   below the 480 cap and 108–144 MHz below stock per class. The
   failure direction is "slightly less saving", never "slower than
   planned-minimum". Phase E should measure the held set on hardware
   and, if row 4 is held, v1.1 can subtract 48 from each row value.
2. **PLL preserved, not zeroed (deviation from nanitecfw).**
   nanitecfw zeroed the PLL field; clock_table.md §7 advises keeping
   Neo PLL edits conservative because the Neo's CRU apply path
   (FUN_03066C36) is unverified on hardware. v1 carries each row's
   stock PLL bytes through unchanged (the spec still spans +4..+27;
   the PLL word's expect == replace). Cost: codec-alone PLL solver
   outputs stay at stock (96–480) instead of dropping toward the
   floor, so v1 leaves some dynamic-power saving on the table.
   Zeroing PLL is the first v1.1 candidate once the apply path is
   confirmed on a unit.
3. **Superseded by the 2026-11-12 revision above:** rows 17, 18, 20, 21
   and 22 now keep stock clocks. The original flag read: **Scope is broader than the precedent on four rows.** nanitecfw
   left its OGG-high, APE and DSD rows unchanged, and clock_table.md
   §7 likewise proposed leaving DSD rows 21–22 unchanged until their
   decode load is measured. The performance plan's §3.4 targets put
   all hi-res rows in one 288 class, and this patch follows the plan:
   rows 17 (OGG top), 20 (APE), 21 (DSD-DFF), 22 (DSD-DSF) are cut to
   240/288. APE and DSD decode loads are unmeasured offline; both are
   still 40–50% below stock, but Phase E's zero-underrun gate
   (§3.4) must exercise APE and DSD128 first, and these four rows
   are the first suspects if any underrun appears. The RKNanoD TRM
   (26.1.1) rates HIFIACC's APE path at "192k * 24bit sample rate,
   under clock 300MHZ", so Rockchip's own worst-case APE figure sits
   above row 20's 288 MHz. That is a vendor claim about the
   accelerator, not a measurement of the Neo's decoder, but it makes
   192/24 APE the first file to play in that gate
   (`analysis/rknanod_trm.md`).
4. **Row 5 rises.** Stock row 5 already ran B at 96 codec-alone,
   below the 144 class target (nanitecfw's shipped *output* for the
   class). v1 sets it to 144 for a uniform class target, so this one
   row is a codec-alone increase, not a cut. Dropping row 5 from the
   patch is a one-line spec change if the uniform target is not
   wanted.
5. **Rows 12/13 left at stock.** They duplicate the AAC-tier values
   but are never requested by any immediate call site and are labeled
   inference/vestigial in the evidence doc, so they are out of scope
   per the build rules. If a computed-id request ever lands on them,
   they run at stock 300 MHz, the safe direction.
6. **Row numbering vs nanitecfw.** The Nano patch numbers its
   FLAC/ALAC rows 19/20; the Neo evidence doc proves FLAC=18,
   ALAC=19, APE=20 on this image (module 33 TBB switch + call-site
   sweep). This patch follows the Neo evidence doc throughout.
7. **No voltage scaling exists** in the solver/apply path (evidence
   doc §3), so the saving is dynamic power only; playtime gain is a
   Phase E measurement, not an offline number.

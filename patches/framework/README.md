# DAP Neo patch framework

The build system every Fosi DAP Neo CE (Community Edition) patch plugs into. It
takes the stock `DP3_V137.img` update package (SHA-256
`fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`;
any other input is refused), applies the patches listed in
`patches/manifest.txt` in order plus the transplants listed in
`patches/transplants.txt`, stamps a new header date, and emits a
validated image plus a JSON build report. Modelled on nanitecfw's
layout (per-change patch files, SHA-gated input, date discipline,
separate recovery image); built on the existing offline patcher in
`tools/`.

Offline only. Nothing here talks to a device, and a passing offline
CRC/mirror check does not prove a device will accept or boot the
image. That is the hardware phase's question.

## Layout

```
build.py               the build (CLI; see --help)
verify.py              round-trip + tamper + unified-build verification (11 checks)
tools/
  insert_rebuild.py    segment insertion rebuild (the --grow step)
  validate_grown.py    layout-generalized validator for grown builds
  check_patch_files.py patch-format checker (run locally pre-merge)
patches/
  manifest.txt         enabled byte patches, in apply order
  transplants.txt      enabled whole-module transplants (vorbis75)
  0000-noop-selftest.patch   framework self-test fixture (no-op bytes)
out/                   built images + <image>.report.json (generated)
```

The default build is the unified build: every approved
modification in one reproducible image. It combines the manifest's 32 byte patches
(DAC error-counter fix, clock table v1, the armed gapless fast path, natural-sort keys,
the wheel timer period patch, and the 0000 no-op self-test fixture) plus the transplants in
`transplants.txt` (the full-precision Vorbis module 75, from
`../vorbis_swap/transplant.py`). The build refuses if a transplant's
ranges overlap a byte patch's, and verify.py check 7 proves the
combined image equals the disjoint union of its parts. The current
unified image (dated 2026-10-23) has SHA-256
`92c446066e715d74a719671d3ee643ed4b7587c94801eb6dc3893f2271ed944d`
and a 71,547-byte diff vs stock (1,414 framework + 70,139 Vorbis, minus
6 shared date/mirror/CRC bytes).

Paths are portable. No tool hard-codes a workspace. Resolution order
is CLI flag > environment > discovery (see `tools/fosi_paths.py`):
`FOSI_REPO_ROOT`, `FOSI_STOCK_IMAGE`, `FOSI_ECPATCH_DIR`,
`FOSI_WORKSPACE`.

## Build

```sh
PY=python3   # any interpreter with the repo tools importable

# unified image: stock + manifest patches + transplants, dated stock+1
$PY build.py --output out/DP3_V137_cfw.img

# framework-only comparison build (byte patches, no transplants)
$PY build.py --no-transplants --output out/DP3_V137_framework.img

# pin a different date (YYYYMMDD) if a build series needs one
$PY build.py --date 20261025 --output out/DP3_V137_cfw.img

# recovery image: unmodified stock bytes, dated build date + 1
$PY build.py --recovery --output out/recovery/DP3_V137_recovery.img

# grown build: insert a payload at the end of a module segment,
# growing its declared length and shifting later payloads. Applied
# to the pristine stock image before patching, so byte patches and
# transplants resolve through the grown records unchanged. The
# report gains a growth list; validation uses tools/validate_grown.py
# (the stock validator pins the stock length and header offset).
$PY build.py --grow 31:code:payload.bin --output out/DP3_V137_grown.img

# tail build: deliver a resident payload (max 2,044 bytes) into the
# census-clean tail of the package gap. The build zero-fills the
# gap's workspace zone itself; the payload can only land at exec
# 0x0307BFB4 or later. There is no step that places code at the gap
# base: the resident-home census proved that range is live runtime
# workspace, and the old --extension step was removed for it.
$PY build.py --tail tail_payload.bin --output out/DP3_V137_tail.img

# DAC filter option: one of the CS43198's other four interpolation
# filters (fast-linear-phase, slow-low-latency, slow-linear-phase,
# nos). One byte; see patches/dac_filter/README.md
$PY build.py --dac-filter nos --output out/DP3_V137_nos.img

# Bluetooth auto-off: stock turns Bluetooth off after 5 minutes without
# a connection; 10min or never. See patches/bt_auto_off/README.md
$PY build.py --bt-auto-off never --output out/DP3_V137_bt.img

# EQ presets: AutoEQ GraphicEQ files or custom curves for the six EQ
# menu presets, fitted to the firmware's band filters; also fixes the
# stock preset selector. See patches/eq_presets/README.md
$PY build.py --eq-presets ../eq_presets/example.json --output out/DP3_V137_eq.img

# prove the framework round-trips, refuses tampered inputs, and that
# the unified build combines its parts correctly
$PY verify.py
```

Outputs are written exclusive-create: an existing output path, or the
input path itself, is refused. The input image is never modified.

## Theme builds

`--theme-config` is the build consumer for the theme studio's
export (`patches/theme_editor/`). It runs after the byte patches
and the transplants, before the single finalize, under the same
discipline as the rest of the framework:

- Resource rules recolor one exact source word per named ROCK26
  resource to the palette colour of the rule's role. The palette
  must define exactly the studio's five roles (background, text,
  highlight, icons, progress_bar) as `#RRGGBB`, converted with the
  studio's own `rgb565()` rounding.
- The pixel count found in the image being built must equal the
  rule's `expected_count` exactly, or the build refuses. The
  guard words `0x0000` and `0x00F8` are refused as sources, as in
  the studio. No theme range may overlap a byte patch, a
  transplant, or an earlier theme edit.
- A config may also carry a top-level `runs` list of
  `{offset, expect, replace}` hex-string edits, an extension
  beyond the studio format for changes that are not exact-colour
  replacements. Each run's expected bytes must match the image
  state left by the earlier steps. `patches/theme_editor/ce-mark.json`
  ships the CE splash mark this way: 64 runs, 496 bytes across
  splash resources 127 and 293, no palette and no resource rules.
- `literal_sites` are refused: the `APPROVED_LITERAL_SITES`
  registry in `tools/ui_theme.py` is empty at this revision.
- `--theme-config` cannot be combined with `--recovery`, and a
  build without it is byte-identical to the build before this
  step existed (verify check 10 pins the unified hash).

One open question rides with this step. The studio reads resource
words little-endian, and its expected counts reproduce on the
stock image only under that reading, so the consumer matches the
studio byte for byte. The theme census proved from decoded
renders that the panel path displays the same stored bytes as
big-endian RGB565. Which stored bytes a recoloured pixel finally
shows as on the panel is a hardware-phase question; nothing in
this project has been flashed.

## Adding a patch

One file per change in `patches/`, named `NNNN-short-name.patch`
(numbered in the order the series is meant to be read). Format:
`key: value` header lines, `#` comments, indented lines continue the
previous value:

```
# One-line summary comment.
name: clock-table-v1            # unique, stable; used in reports/errors
kind: module                    # module | string
module: 0                       # module patches: module index
region: code                    # code | data
address: 0x03079824             # CPU exec address of the first byte
gate: build refuses unless the stock bytes at the target equal
  `expect`; the finished image must pass firmware_patch.validate()
rationale: Why this change, what evidence pins the address and the
  original bytes, and what proves the replacement is safe. This is
  the review surface: write it like the next reader has to decide
  whether to ship it.
expect: <hex, the exact stock bytes>
replace: <hex, same length as expect>
```

String (UI text) patches use `kind: string` with `language`,
`string_id`, `expect_text`, `replace_text` instead of
module/region/address/expect/replace.

Rules:

- **Replacements are size-preserving** (the patcher class this builds
  on requires equal-length expect/replace; growing a module is the
  image-rebuild class of change, a different tool).
- **`expect` is checked at apply time**, against the image state left
  by the patches above yours in the manifest. If you stack on another
  patch's bytes, your `expect` is *its* output, and the manifest order
  is part of your patch's meaning. A mismatch aborts the build with
  the patch name, address and the bytes actually found.
- **Enable by listing the file in `patches/manifest.txt`.** A patch
  file that is not listed is not applied. Order in the manifest is
  apply order.
- Rebuild and re-run `verify.py` after adding a patch; then read the
  build report's `diff_vs_stock` ranges and confirm the diff is
  exactly the bytes your series intends to change, plus date/mirror/
  CRC.

`0000-noop-selftest.patch` is the reference example and a permanent
fixture: its replacement equals its original (module 0's vector-table
head), so it smoke-tests the apply path on every build while changing
no behaviour.

## Date discipline: why stock+1, why slot 2, why recovery is newer

Proven in Phase 2 (`analysis/boot_slots.md`,
`analysis/dual_slot_and_standalone_plan.md`): the boot validator boots
the slot whose image has the strictly newer BCD header date; on a
tie it boots slot 1. Two consequences:

- **Custom images are dated stock+1** (stock is 2026-10-22, so builds
  default to 2026-10-23) and are destined for slot 2 only, with
  stock left intact in slot 1 as the fallback. A custom image dated
  the same as stock would lose the tie and never boot; one in slot 1
  would destroy the fallback.
- **The stock update flow must never run on a dual-boot unit.** The
  stock installer writes the update to slot 2 and then copies slot 2
  over slot 1. It converges the slots by design. Running it (which
  means: letting an update file sit on the card where stock firmware
  will find it) erases the stock/custom split. Keep update files off
  the card.

**Recovery image** = unmodified stock bytes, dated one day *after*
the custom build (default 2026-10-24). Because the validator prefers
the strictly newer date, the recovery image out-dates the custom
build and takes over when installed in its place; plain stock
(2026-10-22) is *older* than the custom build and would not replace
it. `--recovery` produces exactly that: zero patches, later date,
same validation. If you pin a custom build date with `--date`, the
recovery default follows it (+1 day); pass `--date` to `--recovery`
only if you deliberately want a different recovery date.

## Relationship to `repo/tools/firmware_patch.py`: gaps found

The repo copy was not edited. Three gaps made it unusable as the
build engine as-is; `build.py` covers each by reusing the patcher's
own components (`STOCK_SHA256`, `validate()`, `bcd_date()` from
`firmware_patch`; `Image`, `rk_crc32` from `rknano_image`):

1. **No multi-patch application.** `patch()` asserts
   `sha256(raw) == STOCK_SHA256` on every call, so its output can
   never be fed back in. It applies exactly one patch to pristine
   stock, ever. `build.py` implements the ordered apply loop; the
   per-patch step replicates `patch()`'s offset resolution
   (`Image.module_region`), module-boundary check and expected-bytes
   precondition, and finalization replicates its mirror sync and CRC
   rewrite.
2. **No date-only builds.** `patch()` requires exactly one patch
   target (module XOR string), so it cannot produce the zero-patch
   round-trip image or the recovery image. `build.py`'s `finalize()`
   (date stamp + mirror + CRC + `validate()`) covers both.
3. **No manifest, report or diff.** The CLI prints a single proof
   JSON per patch. The framework adds the manifest, the per-build
   JSON report (patches applied with file offsets and old/new bytes;
   byte-diff summary vs stock as coalesced ranges) and `verify.py`.

One behaviour worth knowing: `firmware_patch.validate()` runs on the
input, on every intermediate design point that matters (it is called
on the final image inside `finalize()`), and the SHA gate runs before
any patch is applied. A wrong or already-patched image is refused
before a single byte is interpreted as a patch target.

## What verify.py proves (11/11)

1. Zero-patch build differs from stock only at offsets `0x2`
   (date low byte), `0xC94002` (its header-mirror copy) and
   `0xD00000 to 0xD00003` (trailer CRC). 6 bytes total.
2. The shipped manifest builds with the pinned patch count and
   framework-only diff, and its report is internally consistent.
3. A one-byte tamper of the input makes the CLI build refuse
   (SHA gate), writing no output.
4. The apply step itself raises the expected-bytes precondition
   error, naming the patch, when run against the tampered image.
5. A build output fed back as input is refused (it is not stock).
6. The recovery build validates, carries the build+1 date, and
   stays inside the same allowed diff regions.
7. The unified build combines its parts correctly: outside module
   75 it equals the framework-only build, module 75 equals the
   pinned transplant hash, the diff is confined to the union of the
   parts, and two consecutive builds are byte-identical.
8. The `--tail` build's diff is confined to the gap span, the
   module 0 code_len record and the CRC; the span's workspace zone
   is all zero in the output and the payload lands only in the
   census-clean tail; oversize payloads, overlaps, and dirty gaps
   are refused. (This step replaces the removed `--extension` step,
   which placed caller code at the gap base, inside live runtime
   workspace; see the build.py comment and
   analysis/resident_home/.)
9. The `--grow` build isolates: a 1,000-byte growth of module 31
   code leaves every other module's extracted segments
   byte-identical, grows module 31's code by exactly the payload at
   its tail, passes the layout-generalized validator, and composes
   with the full shipped build (33 patches plus the transplant)
   unchanged.
10. The `--theme-config` build: the default unified build still
    reproduces its pinned whole-image hash; the studio example
    theme's diff against it is confined to resources 6 to 10 and
    changes exactly 32,760 bytes (twice the summed expected
    counts); the CE mark build changes exactly the 496 census
    bytes of `ce-mark.json`; and a tampered expected count, a
    guard-word source, a run with wrong expected bytes, and
    `--theme-config` with `--recovery` are all refused.
11. The opt-in OPUS variant build (patches/opus_swap/): its
    module 72 equals the pinned transplant hash, its diff against
    the unified build is confined to module 72, the five
    WMA-to-OPU rename sites and the trailer CRC, and the default
    unified build still reproduces its pinned whole-image hash.

# Flash review and recovery plan

**Status: first physical flash, full slot readback, boot and music playback pass.**
Standard CE has booted on a physical DAP Neo, played music, displayed embedded
album artwork and exposed the custom settings. Both written 13 MiB slot regions
matched the intended payload byte for byte before reset. Longer-duration,
format, USB-mode and recovery-boot checks remain listed below.

For newer model-specific evidence, see the [NeoPod flashing comparison](../analysis/neopod_flash_comparison.md). NeoPod reports working custom firmware and normal reset on a DAP Neo; this supports the flashing mechanism, while CE still needs its own hardware qualification. The comparison also corrects the visible stock-update filename to `RKNANOFW.IMG`.

## Findings from this review

| Area | Finding | Disposition |
|---|---|---|
| Firmware dates | CE is dated 2026-10-23; official V155 is 2026-11-02. The bundled V137 recovery date, 2026-10-24, is also older than V155. | Prepare a matched-date pair from the official image matching the device; do not assume the bundled recovery can replace V155. |
| Package integrity | Both headers agree; mirror is sector aligned; outer Rockchip CRC passes; all 82 module records and six resource sections are in bounds. | Rechecked by `tools/prepare_flash.py` for every input and prepared output. |
| Stored module overlap | Code and initialized-data payloads do not overlap in the file. | Checked separately from intentional runtime overlay reuse. |
| Update transfer | The Standard image is 6,656 bytes longer than stock, but its rounded updater transfer remains 13 MiB. The mirror and all nonzero payload bytes are inside that transfer; omitted bytes before the outer CRC are zero padding. | This resolves the payload-truncation question at package level, not physical slot capacity or first-stage boot acceptance. |
| Runtime placement | Row code uses bounded, censused resident pockets; no new persistent RAM or overlay growth. Stock framebuffer spans and fallback remain in use. | Stock/fast pixels, display context, ABI and write bounds pass emulation. Hardware tripwire/normal-use testing remains required for computed callers missed by static analysis. |
| Resource reading | The stock reader takes a 32-bit byte count and breaks aligned runs into sectors. Its byte-swap loop uses a 16-bit halfword counter. | Largest direct read is 115,200 bytes / 57,600 halfwords, below counter wrap; row split prevents crossing the SRAM gap. |
| Boot/updater changes | These PRs do not modify module 1 or the module 8 installer. | No new bootloader or flash-writing path is introduced. |
| Recovery geometry | The stock updater writes slot 2 and then copies it over slot 1. On the qualified unit, Rockusb slot bases are LBA 0 and 30720; both 13 MiB CE writes matched on full readback. A second stock fallback is still lost. | Preserve the complete device backup and the measured trailing 2 MiB of each slot. Full stock-recovery boot remains to be exercised. Never corrupt a header as a recovery technique. |
| V155 migration | V155 moves shared globals, changes settings/menu state, adds library slots and changes decoder modules. | No wholesale transplant. Library migration and battery/decoder policy remain unqualified until ABI, persistence, decode vectors and device behavior are established. |

## Prepare a dated pair offline

Use the verified official image for the **same DP3 model and firmware
currently installed**, retained unchanged. The tool accepts only the
known V137 or user-supplied V155 SHA-256 and a pinned CE release image.
`flash-review.json` is an offline example against the supplied V155 reference,
not confirmation that V155 is installed on a device. For a player still on
V137 or an earlier stock release, identify the actual installed version
and obtain its matching official recovery source first. A verified full
internal-flash backup is the primary way back when that source is unknown.
Do not flash an unknown version just to discover whether recovery works.

Example using the supplied V155 reference:

```sh
python tools/prepare_flash.py \
  --candidate release/DP3_V137_CE.img \
  --official /path/to/DP3_V155.img \
  --date 20261113 \
  --output /path/to/new-review-directory
```

The date must be newer than both input headers. If omitted, the tool uses
the day after the newer input. If the device has newer firmware than the
source you supplied, stop and obtain that exact official image first.
The output directory must not exist.

Outputs: `DP3_CE_candidate.img`, `DP3_official_recovery.img`, `SHA256SUMS`
and `REVIEW.json`. The recovery date is one day after the candidate.
Only the two date fields and outer CRC change in each image. The recovery
contains the supplied official code and resources, with no CE patches.
The report explicitly leaves hardware boot, slot geometry and recovery
verification false. This command never enumerates, connects to, writes or
flashes a device. Keep the files on the host until the gates below pass.

## Establish recovery before first flash

1. Back up the music card separately. Keep the original official update,
   its SHA-256, the prepared recovery and the exact tested CE candidate.
2. Using Fosi's documented service/recovery method for this model, verify
   that this physical unit can enter Rockusb recovery and enumerate on
   the host, then return to its working firmware. Record the actual key
   sequence, USB identity, tool version and driver. Do not substitute an
   unverified key sequence from a different Rockchip player.
3. Use a read-only recovery operation to capture the **entire internal
   flash**, including ID/partition blocks, both firmware slots and settings.
   Read twice and compare hashes; retain two independent host copies.
   An update `.img` is not this backup.
4. Identify both slot headers and their mirrors in that backup, plus their
   boundaries and units. Confirm the tool's read addresses by matching
   actual bytes. Do not write guessed LBAs such as 0x6800 or 30720 just
   because they appear in an analysis document or another device's tool.
5. Establish a supported restore operation for that same device and map,
   ideally first on a spare unit. A full-flash restore must use that unit's
   own backup; do not replace its ID/calibration/partition data with an
   unrelated dump. If the supported tool cannot read/restore the unit,
   first-flash qualification remains blocked.
6. For a first controlled trial, retain a working stock slot only if the
   verified tool and measured map support updating the inactive slot
   alone. The normal stock updater cannot preserve that arrangement.
   Do not trigger the stock updater or slot-sync on a dual-image setup.

## Community restore tool review

A model-specific community tool exists:
[danielNZ27/Fosi-Dap-Neo-firmware-restore-tool](https://github.com/danielNZ27/Fosi-Dap-Neo-firmware-restore-tool).
It is not a Fosi-supported or locally hardware-qualified recovery path.
Its README reports holding Vol+, Vol− and OK while connecting USB and a
Rockusb identity of 2207:262D. Treat those as community instructions to
verify by enumeration, not proof that a black screen means recovery.
Do not run the restore script merely to test detection.

The reviewed `restore-stock.py` (Git blob
`ae5627283a2f80c445b8f15155cf12c6a38c283d`) immediately writes both fixed
slot addresses after its initial read. It does **not** make a full backup,
validate the input package SHA/CRC or read back the complete written
images. Despite the README's broad verification description, the script
checks only the first 512 bytes of slot 1 after writing both slots. It
also slices the input to 13 MiB. Consequently, it is useful protocol
reference, not a ready backup/verified-restore solution for this unit.
A qualified restore must verify the full written firmware regions,
including their mirrors, against the intended bytes, and preserve the
unit's own non-firmware data. These gaps must be closed before relying
on it for a first experimental flash.

## Read-only backup helper

`tools/backup_stock.py` uses only chip info (0x1B), flash info (0x1A) and
bounded LBA reads (0x14). It has no erase, flash-write, reset or loader
command. It imports only the exact reviewed community transport blob,
with CRLF line endings normalized before checking; it never runs that
file as a script. The transport currently requires Windows and the
community Rockusb driver. The helper completed two matching reads of the
qualified unit's full accessible LBA range; its fake-device tests remain in CI.

After recovery enumeration has been independently established, read raw
information without changing firmware:

```sh
python tools/backup_stock.py --transport /path/to/restore-stock.py --info
```

The tool does not guess the capacity or flash-info units. Once the whole
internal device capacity in 512-byte sectors is confirmed using
model-specific documentation or a qualified read tool:

```sh
python tools/backup_stock.py --transport /path/to/restore-stock.py \
  --sectors VERIFIED_SECTOR_COUNT --output /path/to/new-stock-backup
```

Replace `VERIFIED_SECTOR_COUNT` with that confirmed integer. Two separate
read passes produce `stock-read-1.bin`, `stock-read-2.bin` and `BACKUP.json`.
The hashes must match; a short read or disagreement leaves an INCOMPLETE
manifest and aborts. Existing paths and unknown transport versions are
refused. Keep both copies independently. Matching reads prove the supplied
range was repeatable; they do not prove that the supplied sector count
covers all internal storage or that a restore succeeds. The manifest
keeps both capacity and restore qualification false until independently
established. Do not use a guessed “13 MiB” or “15 MiB” firmware size as the
whole-device capacity.

## First trial and rollback

Start at low volume with expendable media and stable power. Confirm cold
boot, menus, both themes, every screen edge, cover/no-cover transitions,
long Unicode titles, pause/resume, wheel/key response, screen timeout,
USB data and DAC modes, charging, and the supported audio formats. Check
for visual corruption, lockups, audio dropouts, excessive heat or settings
loss across reboots. Hardware endurance and USB protocol tests follow.

- If CE boots and the official update screen remains usable, restore via
  the **prepared official recovery**, using Fosi's documented procedure,
  then remove update files. Check the resulting official version and
  settings. A higher header date alone is not a guarantee of acceptance.
- If CE does not boot or USB playback prevents access to the update UI,
  use the recovery entry and verified restore procedure established above.
  Restore the firmware region or full backup according to the supported
  tool and the measured map. Verify readback before rebooting.
- If recovery does not enumerate, stop repeated writes and use the
  manufacturer's service route. No proven unbrick procedure is available
  from the update image alone.

Record the outcome and backup identifiers before changing the hardware
status from “not run.” Passing CI does not waive these device gates.

# First physical-device qualification

**Status: backup, physical geometry and full CE write/readback verified; CE boot and recovery boot remain pending.**

This record contains only model-level findings that can be reproduced on another
DAP Neo. It intentionally excludes USB instance paths, disk identifiers, host
paths, raw full-device hashes, filesystem contents, settings and other
unit-specific data.

## Test scope

- Device model: Fosi Audio DAP Neo / DP3
- Installed firmware shown by the device: V1.3.2
- Recovery USB identity: Rockusb `2207:262D`
- Rockusb driver version: 5.14
- Rockchip family reported by the recovery protocol: C262
- Community transport reviewed at Git blob
  `ae5627283a2f80c445b8f15155cf12c6a38c283d`
- Backup helper: `tools/backup_stock.py`

No erase or loader-download command was used. Read-only findings were completed
before the controlled CE write described below.

## Read-only backup result

The flash-info command reports `0x78000` 512-byte sectors (240 MiB), while
bounded reads establish this interface's accessible range as LBAs
`0x00000` through `0x75fff`: `0x76000` sectors (236 MiB). LBA
`0x76000` is the first rejected address. The 4 MiB difference is therefore
not exposed through the tested LBA read command and must not be guessed or
written.

Two independent reads of the complete accessible range matched byte for byte.
The raw images are private recovery material and are not committed.

The real device also exposed a backup-helper defect: opcode `0x1A` returns
the requested 11-byte flash-info structure, while the helper incorrectly
required a 512-byte response. The helper and test fake are corrected in this
PR. The opcode allowlist and all read bounds remain unchanged.

## Measured layout

All addresses below are 512-byte Rockusb LBAs measured by matching bytes from
the two independent reads.

| Region | Start LBA | Size | Finding |
|---|---:|---:|---|
| Firmware slot 1 | `0x0000` | 15 MiB reserved | 13 MiB updater payload followed by 2 MiB of slot-local data |
| Firmware slot 2 | `0x7800` | 15 MiB reserved | 13 MiB updater payload followed by 2 MiB of slot-local data |
| Internal user-storage disk | `0x30000` | 146,800,640 bytes | MBR disk matching the normal USB mass-storage size |
| FAT32 partition | `0x30040` | 146,767,872 bytes | Partition begins 64 sectors into the internal disk |

Both installed firmware slots contain the same 13 MiB V1.3.2 updater payload.
Each slot's mirrored header is at relative byte offset `0xC94000`, or
relative LBA `0x64A0`. The complete 15 MiB slot regions differ after the
13 MiB updater payload, so a recovery writer must preserve the trailing 2 MiB
unless its contents and purpose are independently qualified.

## Controlled CE write and readback

After the two-pass backup and slot mapping completed, the prepared Standard CE
candidate was written through Rockusb to the measured 13 MiB payload region of
both firmware slots. The slot-local trailing 2 MiB regions were not touched.

- Prepared package SHA-256: `244b904fb50cec8b4bf5758d4c725507c07e26196e446c3c4abbddaa0ab139f8`
- Written 13 MiB payload SHA-256: `a1ebb27008c56ff0b4d4c33ecd5ca70c61cbdb24f287e6443f8fc8f28b8c1562`
- Slot 1 full payload readback: matched
- Slot 2 full payload readback: matched
- Reset command sent only after both comparisons passed
- Normal CE boot: pending physical confirmation

## Sanitized device-derived recovery image

The identical installed slot payloads were reconstructed into a standard
Rockchip update package by appending the outer CRC expected by the updater.
This package contains only the installed firmware payload; it omits the raw
device map, user-storage partition, settings, identifiers and slot-local
trailing data.

- Installed header date: 2026-09-20
- Package size: 13,631,492 bytes
- SHA-256: `2e8167df18c6c49d0e734647f7169d986a373f97d4d77de66d649b10650db6af`
- Mirrored header: `0xC94000`
- Stored segments audited: 108
- Header, bounds, mirror and outer CRC checks: passed
- Recovery write/readback: pending
- Recovery boot: pending

This is a device-derived V1.3.2 recovery package, not a vendor-distributed
download. Its code and resources have not been changed. It must remain labeled
unqualified until a full firmware-region write, full readback comparison and
successful stock boot complete.

## Remaining qualification gates

1. Confirm a normal CE boot, key response and USB mass storage.
2. Run the hardware checklist in `release/FLASH_REVIEW.md`.
3. Exercise the device-derived recovery package with a full write/readback and
   confirm stock boot before presenting it as a proven recovery route.

Warnings about an entirely untested physical device should be removed only
after the corresponding gates pass. Unfinished gates remain explicit in this
draft.

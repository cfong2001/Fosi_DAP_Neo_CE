# NeoPod and CE flashing comparison

Reviewed 2026-11-13. **NeoPod provides positive evidence that custom V137-based
firmware can be installed and run on a DAP Neo. It does not establish that CE's
runtime changes boot or behave correctly on hardware.** No physical device was
accessed in this comparison.

## Sources and strength of evidence

Sources in [NeoPod](https://github.com/danielNZ27/NeoPod-Fosi-DAP-Neo-Custom-Firmware):

- [README](https://github.com/danielNZ27/NeoPod-Fosi-DAP-Neo-Custom-Firmware/blob/main/README.md),
  blob `ea5ce4f14ab94ac2482d914246f241386396b7a4`: describes stock installation
  and reports an owner-confirmed wired-jack fix.
- [Flash guide](https://github.com/danielNZ27/NeoPod-Fosi-DAP-Neo-Custom-Firmware/blob/main/docs/flash-neopod.md),
  blob `70595cb27497b077211e57ebb28d76901496c211`: reports owner-confirmed
  normal reset (subcode 0), with MSC boot unsuccessful. Windows is the production
  path; macOS is explicitly alpha without a maintainer hardware flash test.
- [Owner issue #3](https://github.com/danielNZ27/NeoPod-Fosi-DAP-Neo-Custom-Firmware/issues/3)
  reports FLAC playback skipping, consistent with firmware running on a device.
  This is an owner report, not an independently reproduced qualification log.
- [Builder](https://github.com/danielNZ27/NeoPod-Fosi-DAP-Neo-Custom-Firmware/blob/main/tools/build_neo_image.py),
  blob `38f046db1359925899f8b2f9e3290e3c4e133a1d`.
- [Flasher](https://github.com/danielNZ27/NeoPod-Fosi-DAP-Neo-Custom-Firmware/blob/main/flash-neo.py),
  blob `b6be807bec3f0a3eab2418db676b00a244064b9a`.

These reports support prior NeoPod builds working; they do not establish that
every feature of the latest v1.8.2 package has been hardware tested.

## Shared foundation and differences

| Area | NeoPod | CE | Implication |
|---|---|---|---|
| Stock template | Pinned V137 SHA-256 `fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef` | Same exact template | Strong evidence for a shared container and boot foundation. |
| Packaging | Replaces module 0, changes its BSS, preserves stock file length and mirror location, recalculates mirror/CRC | Patches stock modules, grows some payloads and relocates the mirror | NeoPod's success does not by itself validate CE's relocation; CE needs its own bounds and mirror checks. |
| First installation | README describes `DP3_V182.IMG` in internal-storage root, eject/unplug to update | Uses stock updater with generic `RKNANOFW.IMG` | Both can use the device's stock file-update mechanism; exact automatic triggering remains a reported NeoPod procedure, not a CE hardware test. |
| Recovery flashing | Rockusb 2207:262D; write first 13 MiB to LBAs 0 and 30720 | CE has offline preparation and read-only backup helpers, no newly qualified writer | NeoPod supplies a concrete model-specific flashing reference. Its addresses still need confirmation on the user's unit. |
| Runtime dependencies | Six matching `.echo` SD companions | No NeoPod companions | Default NeoPod package workflow cannot be used unchanged as a CE installer. |
| Boot and installer | Custom runtime on stock-derived container | Module 8 byte-identical to stock; module 1 differs only in the wheel timer period immediate (400 to 1000 us) | CE keeps stock boot-slot selection and installer code, but this is not proof of runtime stability. |

## Offline execution of NeoPod's writer against CE

AST-extracted only `checked_firmware_bytes` and `flash` from the pinned flasher;
all transport, device discovery and reset dependencies were mocks. The native
transport module was never imported. Called the firmware-only path, recorded
all writes, and hashed each simulated slot's full payload.

For CE SHA-256
`0f795253f0ec88372d02e9923c29e04dbf2b9081239e91194716d593e93bd0fa`:

- File length: 13,638,148 bytes. Transferred prefix: 13,631,488 bytes (13 MiB).
- Omitted tail: 6,656 zero padding bytes and the four-byte outer CRC. No nonzero
  firmware payload was lost. The outer CRC is a package trailer, not part of
  the stock updater's rounded 13 MiB transfer either.
- CE mirror at `0xC95A00` is sector-aligned, matches the primary header, and
  remains inside the transferred prefix.
- 3,328 simulated writes, 16 sectors each, across two slots. Both slot payload
  hashes matched the CE prefix exactly.

This establishes compatibility with that writer's slicing and write schedule.
It does not validate USB transport, actual flash geometry, ROM acceptance or a
CE boot. The flasher itself reads back **only slot 1's first 512 bytes** after
writing both slots. Companion verification is fuller, but must not be confused
with full firmware readback. A qualified CE writer should compare both complete
written regions, including the mirrors.

## Installer filename correction

The stock constants `DP3_V100IMG` and `RKNANOFWIMG` are **raw FAT short directory
names**, not visible filenames without extensions. Stock lookup at
`0x0305822e` compares exactly 11 bytes against the directory entry
(`0x03058294`–`0x030582a8`). Thus the eight basename bytes `RKNANOFW` plus the
three extension bytes `IMG` correspond to **`RKNANOFW.IMG`** on the mounted drive.
An eleven-character extensionless name instead requires a long-name entry and
an alias, so the former CE installation instructions could prevent detection.

The SDK corroborates this contract: `Common/FwUpdate/FwUpdate.c` passes
`"RKNANOFWIMG"` to `FileOpenA`; `Common/FileSys/file.c:FileOpenA` passes the
11-byte directory name to `FindFDTInfo` and copies exactly 11 name bytes.
SDK reference: [EACHAN-YIN/RKNanoD_MP3_V1.3_20161102](https://github.com/EACHAN-YIN/RKNanoD_MP3_V1.3_20161102) commit
`6c9657140305a91bedc5602e3822d1904056a635`. This older SDK supports the filesystem
interpretation; the matching stock binary supplies device-specific evidence.
NeoPod's builder independently emits `RKNANOFW.IMG`.

CE's browser copy/download filename, manual instructions and browser regression
expectations now use the visible `.IMG` name. Firmware bytes are unchanged.

## Assessment for the user's stock device

**The evidence makes CE installation and boot plausible, with substantially
stronger support for the flashing mechanism than CE runtime correctness.** It
removes the premise that the model cannot run custom firmware. It does not
remove CE's first-device qualification requirement.

For the user's unmodified V137-or-earlier device without a backup, first record
the exact installed version, confirm read-only Rockusb enumeration, and capture
and compare two full internal-flash reads. Confirm slot mapping from those
bytes and retain the unit's own backup plus matching official recovery image.
Then use a writer with complete readback and test CE boot/playback/display on
hardware. See [the recovery plan](../release/FLASH_REVIEW.md).

Date precedence applies to selecting packages through the stock boot/update
path. A raw writer replacing both slot headers is a different path; NeoPod's
success with it is not evidence that any older recovery image will be accepted
through an already running newer firmware's update flow. Neither stock-path
installation nor NeoPod's default two-slot writer preserves a stock fallback.

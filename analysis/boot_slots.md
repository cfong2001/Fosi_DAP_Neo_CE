# Boot, slot selection and the update flow (DP3_V137)

> **Correction:** Later instruction-level review found errors in the slot-scan, updater mirror-seek, and device-3 subdevice-offset descriptions. See [the slot capacity investigation](slot_reclamation/report.md) before relying on this document. The first qualified device measured Rockusb slot bases at LBA 0 and 30720 and completed full CE readback; stock-recovery boot remains to be exercised.

All addresses are CPU addresses in `DP3_V137.img` (SHA-256
`fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`).
"Proven" means read directly from the disassembly cited. The persistent
RAM region (~0x03022800-0x030243xx, not covered by any module-table
data segment) holds the state every stage below shares.

## The pieces

| Piece | Where | Role |
| --- | --- | --- |
| Device-3 init | module 0 `0x0305ebe4` | Scans drive 1 for the IDB/NANO block; derives the partition globals |
| Slot validator | module 1 `0x0307e26c` | Decides which firmware image boots; writes the decision to globals |
| Boot/settings loader | module 1, big function spanning ~`0x0307d850`-`0x0307e26c` | Reads the FWUP block, sets the active-package pointer `[0x0302327c]`, loads SAVEINFO |
| Segment loaders | module 0 `0x03064d40` (info), `0x0306777a`, `0x0306780a`, wrapper `0x03067870`; byte reader `0x0306771e` | Load overlay code/data from the **active** package on demand |
| Update applet | module 21 (see `modules_round2.md`) | UI flow that invokes the installer and the slot sync |
| Installer | module 8 `0x0307e64c` | Writes a new image to the fw2 area, then copies it over fw1 |
| Chunk writer | module 8 `0x0307e53c` | 16-sector write + read-back + memcmp |
| Image copy | module 8 `0x0307e880` | Verified image copy between slots, header chunk written last |
| Slot sync | module 8 `0x0307e5b0` | Mirrors the booted image into the other slot |

## Partition globals from the NANO scan (proven)

Device-3 init (`0x0305ebe4`) probes up to five positions on drive 1
(byte offset `(i<<10) + 0x40`, `i` = 0..4, raw drive-1 reads via
`0x0305dd32`) for the Rockchip ID-block magic `0xFCDC8C3B` at buffer
+0 and `NANO` (`0x4F4E414E`) at buffer +0x20A. On a match it parses:

- `[0x0302433c]` (subdevice-0 size used to offset later subdevices, sectors) = `u16 @ buf+0x202` << 11
- `[0x03024340]` (fw2 base, validator-relative sectors) = that value >> 1
- `[0x03024350]` = `u16 @ buf+0x220`; `[0x03024352]` = `u16 @ buf+0x216`
- subdevice-1 and subdevice-3 offsets (`[0x03024348]`, `[0x0302434c]`)
  start at 0 here; the subdevice offset helper is `0x0305df72`
  (0 → `[0x0302433c]`, 1 → `[0x03024348]`, 3 → `[0x0302434c]`,
  2 → drive size − 0x2000 − (sum of the other three), 0xFF → drive
  size − 0x2000).

The initial fw2 base is half the decoded subdevice-0 size. The NANO
field represents 1 MiB per unit when shifted left by 11 sectors.
The validator may overwrite both values.

## The validator (module 1, `0x0307e26c`): proven

Reads go through the device-3 read wrapper `0x030678ca` with selector
`0x00030000` (subdevice 0), one 512-byte sector at a time, into two
stack buffers. Sector numbers below are validator-relative (device-3
logical; subdevice 0 skips the offsets for later subdevices and the
read path adds 0x2000 sectors before the drive-1 read). At entry it clears the decision
byte: `[0x03024354] = 0`.

1. fw1 check. Read sector 0. Compare 8 bytes at +0x1F8 against the
   embedded constant `RKnanoFW` (comparator `0x03054ebe`). Mismatch →
   log `fw1 Sign error!`, fw1 invalid, scan base becomes
   `[0x03024340]`. Match → read the mirror header at sector
   `(u32 @ +0x1F4) >> 9` and compare all 0x200 bytes. Mismatch → log
   `fw1 compare error!`, fw1 invalid, same fallback. Match → fw1
   valid; first fw2 candidate = `((len + 0x104000) >> 9) & 0xFFFFF800`
   = 0x6800 (13 MiB) for V137.
2. fw2 scan. From the candidate base, read the header, check the
   magic, then the mirror the same way. A magic mismatch steps by
   0x800 sectors and loops without reaching the comparison against
   0x14. A mirror mismatch exits the scan rather than trying the next
   candidate. Execution-level validation remains necessary; see
   `slot_reclamation/report.md`. A passing header sets fw2 valid.
3. Decision. If neither is valid → log `fw1 && fw2 error!`, return
   −1. If fw2 is valid, store its sector to `[0x03024340]`, then
   enforce the layout invariant: if `[0x0302433c]` < 2 × fw2 base,
   set `[0x0302433c]` = 0x2000 + 2 × fw2 base. If only fw1 is valid →
   log `fw2 error!`, reset `[0x03024340]` to the nominal candidate
   base, same invariant fix.
4. Choice. Only fw2 valid → set `[0x03024354] = 1`. Both valid →
   re-read sector 0 and byte-compare the two 512-byte headers: if
   identical, return 0 (nothing to decide). If they differ, compare
   the u32 at header +0 (the packed BCD build date): fw2 boots only
   if its date is strictly newer; then `[0x03024354] = 1` and
   fw1's valid flag is cleared. Otherwise fw1 boots. Every path ends
   by logging `fw1valid = %d fw2valid = %d`. Return value is 0 only
   for the identical-headers case, −1 otherwise; the durable outputs
   are the globals, not the return value.

Selection semantics, stated plainly: boot fw1 unless fw2 exists,
validates, and carries a strictly newer build date, or fw1 is
broken. The date is four bytes in an unsigned, user-editable header.
This validator compares that date word; signature and anti-rollback
behavior in earlier boot stages remain unproven.

## The active-package pointer (proven mechanism)

The boot/settings loader in module 1 stores `[0x0302327c]` (from a
stack value computed out of the FWUP block it reads first; the exact
field arithmetic is shared with the SAVEINFO load and is covered in
`saveinfo_lock.md`). The segment loaders interpret it as the device-3
byte offset of the running package + 0x200:

- Loader info fn (~`0x03064d40`): reads 0x200 bytes at
  `[0x0302327c]`, word 0 is the header field at package +0x200, the
  module load base `0x03050000`. A module record sits at
  `[0x0302327c] + 8 + 32·index` (= package +0x208 + 32·index, the
  module table). Segment source = `record_field − 0x03050000 +
  [0x0302327c]`, length from the paired record field (code: +0x0/+0x8;
  data: +0xC/+0x14 in the `0x0306780a` variant, which also takes a
  caller destination and extra offset).
- `0x0306771e` performs the byte-granular read from device-3 space
  (0x200-byte block reads via `0x03067510` plus a memcpy for unaligned
  spans).
- Overlay code calls the wrapper `0x03067870` (→ `0x0306777a`) with
  (module index, 7) before using another overlay. Module 21 does
  exactly this with (8, 7) before calling module 8's entries. The
  second argument 7 is consistent with a code|data|bss load mask;
  that reading is likely, not proven.

Consequence: every overlay load in the running system reads from
the package the validator selected. If fw2 boots, the whole system,
not just a kernel, comes from fw2. The two slots hold complete,
independent firmware images.

## The installer (module 8, `0x0307e64c`): proven

Entry points are called by module 21 (at its `0x0307d384` /
`0x0307d3a8`), which first loads module 8 via the segment loader.

1. Find the file. The update filename template lives in module 0
   data at `0x030041a6`: `DP3_V100IMG` followed by `RKNANOFWIMG`
   (both NUL-terminated FAT short directory names). The visible names
   are `DP3_V100.IMG` and `RKNANOFW.IMG`: the dot separates the eight-byte
   basename from the three-byte extension. The lookup at `0x0305822e`,
   called through `0x03058cc6`, compares exactly 11 bytes against the raw
   FAT directory entry (`0x03058294`–`0x030582a8`). The SDK
   `Common/FileSys/file.c:FileOpenA` likewise passes the 11-byte name to
   `FindFDTInfo`. Digits at template
   offsets 5-7 are overwritten with a 3-digit version derived from
   the halfword at SAVEINFO +0x2DB (the running firmware's version;
   +0x2D9 holds a related copy the installer updates). The installer
   searches for the versioned name first, then the generic
   `RKNANOFWIMG` (file-search fn `0x03058cc6`). No file → return −1,
   nothing written.
2. Validate the header. Read 512 bytes (`0x03058fa8`), require
   `RKnanoFW` at +0x1F8, compute the rounded total
   `len = (u32 @ +0x1F4 + 0x104000) & ~0xFFFFF` (0xD00000 for V137).
   Seek to the mirror offset, read 512 bytes into the scratch buffer,
   and compare them to the first header. Short-read behavior remains
   unverified. This is a byte-offset file read; the boot validator
   above reads the mirror by sector (`len >> 9`), so an image whose
   mirror is not 512-byte aligned passes here and fails at boot. The
   CE build pads grown images to keep it aligned.
3. Write to the fw2 area first. Fill the 16 KiB scratch
   (module 8 BSS at `0x030249d0`) with 0xFF and write one 16-sector
   chunk at `[0x03024340]` (chunk writer `0x0307e53c`: write via
   `0x03067912`, read back via `0x030678ca`, memcmp; the medium-type
   word is forced to `NAND` for the duration via `0x03067ad2`). This
   erases fw2's header chunk first, so a half-written fw2 can never
   validate. Then stream the file in 0x2000-byte reads, writing
   16-sector chunks starting at fw2 base + 0x10. The header chunk
   is written last, at the fw2 base itself.
4. Copy fw2 → fw1. Call the image copy `0x0307e880`(dest 0,
   src fw2 base, total bytes): 16-sector chunks with the same
   write-verify writer, header chunk copied last again. After this
   step both slots hold the new image.
5. Bookkeeping. Update the stored version halfword and rebuild
   the filename template (same code as the slot sync's tail).
   Returns 0 on success, −1 on any failure before completion.

The chunk writer forces the device-3 medium-type word to `NAND`
(0x444E414E) around its writes (the geometry branch inside the
device-3 write path, `storage_stack.md`) and restores it after.

## The slot sync (module 8, `0x0307e5b0`): proven

Reads the boot decision byte `[0x03024354]` and the fw2 base
`[0x03024340]`, then calls the image copy with the booted image
as source and the other slot as destination, length = fw2 base << 9
bytes:

- booted fw2 (flag = 1): copy(0 ← fw2 base)
- booted fw1 (flag = 0): copy(fw2 base ← 0)

Then the same version-string bookkeeping as the installer. Net
effect: after a sync, both slots are byte-identical (at least
over the first fw2-base bytes), and the next boot takes the
identical-headers path in the validator.

## The update applet flow (module 21, partial)

From its calls (full characterisation in `modules_round2.md`):
module 21 draws a UI, sets SAVEINFO fields (+0x0E, +0x0F, +0x29,
+0x3E), calls the installer. Installer returns 0 → branch to
`0x0307d434` (success path, not yet decoded). Installer returns
nonzero → module 21 waits on OS event flag 0x18B (`0x03067258`),
calls a local helper `0x0307d2ec`, reloads module 8, runs the slot
sync, and resets through `0x030536a6`(0, 0), the same final
handoff as the shutdown path. What launches module 21, and whether
the sync-then-reset branch also runs after a *successful* install on
some path, are open (see below).

## What this means for running two different firmwares

The stock flow is designed to converge the slots: an update writes
fw2, copies it over fw1, and the sync mirrors whichever image booted
into the other slot. Divergent-slot stability requires device validation and a complete
census of installer and sync callers. Subject to unverified early boot
and physical geometry assumptions, slot selection suggests:

- the traced validator may select a valid custom second image with a
  newer header date, subject to earlier boot behavior;
- potentially select stock if the second header is invalid or older;
  damaging a header is not a demonstrated recovery procedure;
- lose the divergence if the stock firmware-update applet ever runs
  to the sync step, e.g. if an update file (`DP3_VnnnIMG` /
  `RKNANOFWIMG`) is present and the update flow is triggered. Keep
  update files off the card on a dual-boot unit.

The validator's relative geometry also fits the Rockusb tools:
its first fw2 candidate is relative sector 0x6800 and it steps
0x800; the restore tool's slot-2 write at Rockusb sector 30720
(0x7800) is the third candidate if device-3 logical sector 0 in
the firmware area equals Rockusb LBA 0, plausible given the NANO
layout fix-up, but the logical↔physical identity is not proven
from the image alone. It settles with one read-back from a real
unit (dump sectors 0, 0x6800, 0x7000, 0x7800 via Rockusb and compare
headers).

## Open items

- Boot ROM / first-stage behaviour before module 1 runs (not in the
  update image; the validator's caller and the initial
  `[0x0302327c]` for the boot package itself are set up before the
  traced code; module 1's boot function computes the pointer from
  the FWUP block, but who loads module 1 to run it is unresolved).
- What launches module 21 (menu, update-file detection at boot, or
  both) and its success branch at `0x0307d434`.
- The loader argument "7" semantics (load mask hypothesis).
- `[0x03024350]` / `[0x03024352]` (two halfwords from the NANO block):
  consumers unknown.
- `NanoCRebootFlag` (string in module 1 data at `0x0307d6fc`): a
  named flag in the NANO/IDB area nobody in the traced code reads by
  that name; possibly a boot-count/reboot marker written by the ROM.

# Firmware slots and the case for reclaiming one copy

## Finding and recommendation

The stock V137 code describes two complete installed firmware packages,
and the normal updater writes the second then copies it over the first.
The other copy is therefore redundant during ordinary operation, but it is
also part of boot selection, fallback and the stock update process. There
is **no demonstrated safe way to reclaim it** for a larger firmware or
for user files. Keep both copies until the actual device geometry, early
boot path, recovery and every writer have been measured. Removing a slot
does not by itself enlarge the image's RAM execution windows.

This assessment uses the pinned update image, not a flash dump or a device
test. The arithmetic below describes the code's *logical* sector space;
it is not a RockUSB write map or an instruction to modify a device.

## What is measured

`audit_layout.py` verifies the stock input SHA-256, the quoted instruction
byte ranges, the header mirror and both zero-padding spans. It makes no
writes to the image or a device. Run it from the repository root:

```sh
python3 analysis/slot_reclamation/audit_layout.py
```

| Quantity | V137 finding | Meaning |
| --- | ---: | --- |
| Update file | 13,631,492 bytes (`0xD00004`) | File, not a dump of physical flash |
| Mirrored header | `0xC94000`, 512 bytes | Duplicate of the first sector |
| Updater's rounded transfer | 13,631,488 bytes (`0xD00000`, 13 MiB) | Calculated from mirror offset; 4-byte file CRC follows this transfer |
| Image resources end | `0xC92E10` | 4,592 zero bytes precede the mirror |
| Zero region after mirror | 441,856 bytes to `0xD00000` | File padding, not automatically executable or free device storage |
| First fw2 candidate from a valid V137 fw1 | `0x6800` sectors = 13 MiB | Minimum candidate spacing in the validator's device-3 logical coordinates, not measured flash geometry |
| Candidate increment | `0x800` sectors = 1 MiB | Search granularity, not proof that each candidate is a reserved partition |
| External restore-tool fw2 address | 30,720 sectors = 15 MiB | Reported RockUSB address; relationship to device-3 sectors is unverified |

The initializer reads an NANO block field as a 16-bit number, shifts it
left by 11 sectors for `[0x0302433c]` (1 MiB per field unit), and assigns
half that value to the initial fw2 candidate `[0x03024340]`. These are
derived **runtime** values, not fixed physical slot sizes. The value for
an actual unit is unknown without its ID block and runtime observation.

The known validator computes the first candidate from fw1's mirror offset:
`((mirror + 0x104000) >> 9) & 0xFFFFF800`. For the pinned image this is
`0x6800` sectors. This is a lower-bound candidate, not a proven actual
slot location. An external restore tool uses a 15 MiB RockUSB address,
but even though its sector number happens to be the third 1 MiB candidate,
the coordinates are different and must not be equated without readback.

## Package headroom is not a safe new slot size

For a sector-aligned mirror offset, the largest offset that still yields
the stock updater's **13 MiB** calculated transfer is `0xCFBE00`, which is
425,472 bytes after the existing mirror. This is a mathematical ceiling
for mirror movement under that particular rounding expression, not an
approved payload budget. A useful change must also preserve the complete
512-byte mirrored header, keep all content inside the transferred range,
respect sector alignment, handle all dependent offsets, and produce an
image that the relevant validator accepts. The current insertion rebuild
shifts the file trailer and grows the file; an output would need its own
appropriate padding, length and CRC handling rather than blindly assuming
the updater writes the extra bytes. No such enlarged image has been
installed or tested here.

The payload-to-RAM issue is separate. The loader copies module segments to
their declared execution addresses and windows; placement cannot exceed a
resident allocation merely because file space exists. The repository's
`patches/framework/space_budget.md` describes current overlaps and verified
homes. Enlarging package storage, merging slots, or shortening zeros does
not establish spare SRAM or make module overlays coexist.

## Slot behavior and direct instruction evidence

* Module 1's validator checks fw1 and scans fw2 candidates. Each candidate
  check reads the `RKnanoFW` magic and compares 512 bytes at the primary
  header with the header sector found using offset `+0x1F4 >> 9`. Header
  equality here is not validation of every code/data byte and is not a
  signature. The stock traces do not prove the ROM or another earlier
  stage accepts arbitrary modifications.
* The active-package pointer `[0x0302327c]` feeds the module loader, so
  its overlays are read on demand from the selected package. An idle
  second slot is not a general heap and the selected slot must remain
  intact throughout operation.
* The module 8 updater calculates `r6 = (mirror + 0x104000) & ~0xFFFFF`
  at `0x0307E718`–`0x0307E720`, uses the mirror offset as an absolute
  seek argument at `0x0307E724`–`0x0307E726`, then reads and compares
  the second header. It invalidates the fw2 header, writes and verifies
  chunks, writes the header last, and calls the copy routine from fw2
  to fw1. Module 8's sync entry at `0x0307E5B0`–`0x0307E5C8` copies
  the booted slot to the other over `fw2_base << 9` bytes. Any separate
  filesystem or appended data placed there may be overwritten.
* When a new rounded transfer exceeds the existing fw2 base in sectors,
  `0x0307E764`–`0x0307E76C` substitutes the new transfer size as the
  second-slot start. This is not evidence that the resulting area is
  reserved or safe: actual partition geometry and available capacity have
  not been measured. The updater still copies to fw1 afterward.
* In the device-3 read routine, the subdevice-0 branch at `0x0305E038`
  skips the additions used for later subdevices, then `0x0305E07A` adds
  the fixed `0x2000` sectors before the drive-1 read. The field at
  `0x0302433c` supplies the preceding subdevice size for **later**
  subdevices. This corrects `boot_slots.md`'s claim that this field is
  added to subdevice-0 reads. The internal drive's coordinates still
  cannot be assumed identical to RockUSB's address space.

## Two material documentation discrepancies

1. `analysis/boot_slots.md` says the updater seeks to zero before its
   second header comparison. The code at `0x0307E718`–`0x0307E73E`
   instead leaves the mirror offset in r0, passes absolute-seek mode 0,
   reads there, and compares 512 bytes. `analysis/flash_security_and_port.md`
   describes the mirror read. A short-read return is not checked before
   the comparison on that path, so its actual behavior remains open.
2. Existing documents say the fw2 scan tries up to 20 candidates and then
   stops. The disassembly at `0x0307E31C`–`0x0307E32C` increments or
   decrements the candidate and jumps directly back to `0x0307E2FC` on a
   magic mismatch; the `0x14` comparison at `0x0307E32E` is bypassed by
   that loop. It is reached when the candidate is zero or after a
   candidate with matching magic has had its mirror compared. A mirror
   mismatch goes to that comparison and then leaves the scan rather than
   resuming at the next candidate. The number of unsuccessful probes and
   error handling need execution-level validation; do not assume a bounded
   twenty-read fallback or that invalidating a header quickly selects the
   other slot. This finding is from the pinned instruction sequence, not
   from a physical boot experiment.

## What would have to be established before reclaiming capacity

1. Obtain a read-only complete original-media backup and establish an
   independently tested, exact-board recovery route. Determine medium
   capacity and block geometry, the NANO fields and which addresses the
   ROM, internal device layer, and recovery tool each use. Verify both
   headers and mirror locations by non-destructive readback.
2. Trace and emulate the **actual** validator and updater, including
   failed reads, corrupt primary or mirror, absent secondary, oversized
   headers, interrupted writes, equal/different dates, every call to slot
   sync, and early-boot selection. Add regression tests for the scan-loop
   discrepancy and for maximum-size arithmetic and alignments. Emulator
   proof must not be mistaken for device proof.
3. Prove, on the exact device and with recovery established, what region
   is reserved for firmware versus settings and user storage. A single-slot
   design would need explicit changes to all readers and writers, including
   ROM/first-stage expectations, validator, update/sync paths, partition
   definitions, power-loss behavior and any recovery tool that assumes two
   slots. Prove that operation on the modified layout does not erase the
   only bootable image. There is no such implementation here.
4. Before offering a larger image, perform independently checked offline
   builds that validate the installed-layout representation, compare every
   affected offset and module segment, and explicitly model the updater's
   rounded transfer. Follow with hardware load/overlay and recovery tests;
   do not interpret a successful package CRC as a boot or recovery test.

Keeping the second slot as recovery is the recommended near-term choice.
No flash erase, partition edit, boot-sector write or on-device update was
performed in this investigation.

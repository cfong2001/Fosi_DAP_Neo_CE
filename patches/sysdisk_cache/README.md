# System-disk read cache

The block reader at `0x03067510` is the SDK's `MDReadData`
(`Common/System/ModuleOverlay/ModuleOverlay.c`). Reads shorter than a
sector from the data disk (device `0x00030001`) use three 512-byte
buffers at `0x03023D3C`, tagged by the sector numbers at `0x03005878`.
Reads from the system disk (device `0x00030000`) did not. Each one read a
whole sector into the first buffer, copied the requested bytes and set
that buffer's tag to -1.

The system disk holds the fonts and image resources. A glyph is a 34-byte
read at font base + 33 × code, measuring a string reads each glyph again,
and a partial image draws row by row. So every character drawn cost two
or more eMMC sector reads, each with interrupts disabled.

| Patch | Site | Change |
|---|---|---|
| 0290 | `0x0306D450` | 108 bytes of code in an unreached stock routine (census tier 1) |
| 0291 | `0x03067562` | Route system-disk partial reads to the cached path with the sector tagged by bit 31 |
| 0292 | `0x030675E0` | Strip the tag before `MDRead`; retry a failed system read once, as stock does |
| 0293 | `0x0306767A` | Strip the tag before the whole-sector path |
| 0294 | `0x0306792E` | Clear all three tags at the start of every device write |

A tagged sector never equals a data-disk sector, a free slot (-1) or the
tag of another system sector. The stock victim choice and the data-disk
path are unchanged. Writes below sector 0x1C00 of drive 1 that skip the
device wrapper (`0x0305D96A`, `0x0305D9B8`) sit under the +0x2000-sector
start of every device-3 partition, so they never alias a cached sector.

`test_sysdisk_cache.py` runs the stock and patched module 0 reader against
a fake disk. It checks that random read and write mixes return the disk's
bytes and the stock return values, and that the system-disk retry and the
uncached path for other devices are unchanged. It also counts sector reads
on glyph traces. `build_sysdisk_cache.py` regenerates the patch files.

# Storage stack: from update package to the DW-MMC controller

Scope: stock `DP3_V137.img` (SHA-256 `fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`), system core (module 0) unless noted. All addresses are system-core Thumb execution addresses. Method: Capstone disassembly of the original instructions (`work/main/disasm.py`); no device was touched.

This closes the prior repo's open question "physical storage controller beneath device-3 callbacks."

## The chain, top to bottom

```
module 8 updater / module 1 slot validator
  -> generic device wrappers   read 0x030678ca, write 0x03067912
  -> dispatcher 0x030678b0, vtable base literal 0x03067b50 -> 0x0306e958
       device 3 record @0x0306e958   (partitioned internal device)
       device 4 record @0x0306e980   (raw single-medium device)
  -> generic drive layer: object table 0x03005674, read 0x0305dd32, write 0x0305fb64
       drive 0 -> channel 0 -> DW-MMC @ 0x60020000
       drive 1 -> channel 1 -> DW-MMC @ 0x60030000
  -> per-drive methods installed by card init:
       read 0x0305dc80, write 0x0305fae4
  -> command engine 0x0305e390 -> Synopsys DesignWare MMC registers
```

## Generic device layer (vtables)

The dispatcher at `0x030678b0` computes `selector >> 16`, walks 0x28-byte records from the table at `0x0306e958`, and matches the ID word at record `+0x24`. Two records exist:

Device 3 record @ `0x0306e958` (ID 3):

| slot | value | meaning |
|---|---|---|
| +0x00 | 0x0305ebe5 | init (see below) |
| +0x04 | 0x0305e021 | read |
| +0x08 | 0x0305fc09 | write |
| +0x0c | 0x0305e009 | none |
| +0x18 | 0x0305e09b | none |
| +0x1c | 0x0305dfdd | set medium-type word at 0x03023048 |
| +0x20 | 0x0305d9c9 | none |
| +0x24 | 3 | device ID |

Device 4 record @ `0x0306e980` (ID word `0x00010004`):

| slot | value | meaning |
|---|---|---|
| +0x00 | 0x03054275 | register drive-0 object |
| +0x04 | 0x0305de87 | read |
| +0x08 | 0x0305fbb5 | write |
| +0x0c | 0x0305decf | none |
| +0x10 | 0x0305df19 | subdevice-offset helper |
| +0x14 | 0x030542e1 | probe/init (calls card init for drive 0) |
| +0x18 | 0x030542a3 | remove/close |
| +0x24 | 0x00010004 | device ID 4 |

Device 3's read/write take a subdevice selector (0..3, or 0xff for "whole rest") and add a partition offset computed by `0x0305df72` from runtime globals at `0x0302433c` (subdev 0), `0x03024348` (subdev 1), `0x0302434c` (subdev 3); subdev 2 is the sum of the three, subtracted from the usable drive-1 size. On top of the partition offset, both device-3 callbacks add a fixed +0x2000 sectors (4 MiB) before calling the generic drive layer with drive index 1.

Device 4's write (`0x0305fbb4`) forces drive index 0. It is the raw, unpartitioned view of the other medium.

The device-3 write wrapper at `0x0305fc46` compares the medium-type word at `0x03023048` against `0x444e414e` ("NAND"): internal-medium geometry handling is runtime-branched on a detected medium type. The MMC command path below is the one this firmware actually drives for both drives; "NAND" is an SDK alternative the type word can take, not a second traced stack.

## Generic drive layer (objects)

- Object-pointer table at `0x03005674` (module 0 data; entries statically zero, populated at runtime).
- Gatekeeper `0x0305dd06`: only drives 0 and 1 exist (`cmp r0,#2; bge fail`); a drive is present when its object's first word + 1 != 0.
- Read dispatch `0x0305dd32` / write dispatch `0x0305fb64`: object = table[drive]; sector count at obj+0x10; flags byte at obj+0x04 tested against 0x84 selects the sector-unit shift (byte units vs 512-byte units); the call tail-branches (`BX ip`) through the function pointer at obj+0x20 (read) or obj+0x24 (write). obj+0x28 holds a channel byte; obj[0] holds the drive ID (a mismatch returns error 0x1000).
- Registration `0x0305e9c6(index, obj, arg)`: zeroes obj+0x04..+0x30, sets obj[0] = -1, calls config init `0x0305f96e(index, arg)`, stores the object into the table.
- Drive 0 has an inlined registration at `0x03054274`: object at the fixed address `0x03022874`, config init `0x0305f96e(0, 0)`, stored to table[0]. Its probe entry `0x030542e0` then runs card init for drive 0 and `0x0305e34c(0, 2)`.

## Card init (per drive): `0x0305e9fa(drive, type)`

Called for drive 0 from `0x030542e8` (module 0 boot path) and for drive 1 from device-3 init (below). Sequence:

1. Zero the object, obj[0] = -1, store the drive index byte to obj+0x28 (channel = drive index).
2. Controller power `0x0305e318(channel, 1)`, `0x0305f88c(channel, 1)`, clock setup `0x0305e21c(channel, 0x190 = 400)`, delay.
3. CMD0 (command descriptor `0x8100`, arg 0) through the command engine.
4. CMD8 (`0x2148`, arg `0x1aa`, SEND_IF_COND), CMD55 (`0x2177`), ACMD41 (descriptor `0x2045`) polled with 100 ms delays (`0x0305e7b0(0x64)`), helpers `0x0305f200` (capacity/bus configuration), `0x0305ed20`, `0x0305f8d0`. Response words are parsed with UBFX on bits 28-30 and bit 27 (CSD/OCR-style fields).
5. On the card-present branch at `0x0305ea9a` it installs the transfer methods: obj+0x20 = `0x0305dc81` (read), obj+0x24 = `0x0305fae5` (write).

Config init `0x0305f96e(channel, arg)` builds a 36-byte per-channel struct at `0x03024358 + channel*36`: controller base at struct+4 (`0x60020000` / `0x60030000`), byte at struct+9 set to 4 or 8 (bus width), then calls `0x0305fa54`, `0x0305fa14`, `0x0305fa50`, `0x0305f8d0`, `0x03057110`.

## Device-3 init: `0x0305ebe4`

1. Takes semaphore 0x6c via `0x030525ac`.
2. Checks whether drive 1 is already registered (`0x0305e9bc(1, [0x0302304c])`); if not, runs card init `0x0305e9fa(1, 0)`.
3. Scans the start of drive 1 through the generic read (`0x0305dd32`) in a loop (byte offset `count<<10 + 0x40`, bound 0x1800) looking at two magic constants held in registers: `0xfcdc8c3b` and `0x4f4e414e` ("NANO" little-endian). This is the Rockchip ID-block / NANO partition-info scan; it is what populates the subdevice offset globals at `0x0302433c/48/4c` used by the device-3 callbacks. The same IDB magic `0xFCDC8C3B` is the one NeoPod's inherited `emmc_layout.c` describes. Here it is confirmed in stock code rather than only inherited from documentation.

## Transfer methods and the command engine

Read `0x0305dc80(obj, lba, count, buf)`:

- count == 1: descriptor `0x2351` = CMD17 READ_SINGLE_BLOCK
- count > 1: descriptor `0x2352` = CMD18 READ_MULTIPLE_BLOCK, then `0x414c` = CMD12 STOP_TRANSMISSION
- byte count = count << 9; block size word 0x200

Write `0x0305fae4`:

- count == 1: `0x2758` = CMD24 WRITE_SINGLE; count > 1: `0x2759` = CMD25 WRITE_MULTIPLE; then CMD12 (`0x414c`)

Descriptor encoding: bits [5:0] = MMC command index; 0x40 = response expected; 0x100 = CRC check; 0x200 = data expected; the engine also tests bits 0x2000, 0x4000 and `(desc & 0xe00) == 0x600` when setting up data transfer (high-bit semantics partially mapped).

Command engine `0x0305e390(channel, descriptor, arg, resp_ptr)`:

- Controller base = `0x60020000` if channel == 0, else `0x60030000` (literals at `0x0305e4e8` / `0x0305e4ec`).
- Register use matches the Synopsys DesignWare MMC (DW-MMC / MSHC) map: BLKSIZ at +0x1C, BYTCNT at +0x20, CMDARG at +0x28, CMD at +0x2C (written with start bit 0x80000000), STATUS at +0x48 polled for bit 0x200 (data busy) with timeout counter 0x004c4b40 and 1-unit delays via `0x0305e7b0`.
- Controller power `0x0305e318(channel, on)` writes `[base+0x04] = on` (DW-MMC PWREN) and calls reset helper `0x0305e954`.

## Conclusions

- The updater's logical device 3 resolves, through two dispatch layers and a partition-offset stage, to drive 1 → DW-MMC controller at 0x60030000, speaking the standard SD/MMC command set. Drive 0 maps to the same controller family at 0x60020000.
- Drive 1 is the internal medium: it carries the NANO partition info, the firmware slots the validator scans, and the user volume. Drive 0 is registered separately at boot and is the removable card by elimination (the binary does not label it; board-level confirmation is still a hardware question).
- The protocol is MMC, so the internal medium is an eMMC-class part (or an internal SD-style device on the MMC bus); the "NAND" medium-type branch is an SDK alternative, not evidence of raw NAND on this board.

## Persistent system-state region

Addresses roughly `0x03022800-0x030243xx` are not covered by any module-table data segment, yet hold live state: the drive-0 object at `0x03022874`, the medium-type word at `0x03023048`, RTC date/time bytes at `0x030230a8/0x030230ac` (read and range-checked by the module-0 reset handler at `0x03061f8a`, which defaults them to 2026-06-26 when invalid), the partition globals at `0x0302433c-0x0302434c`, and the per-channel MMC config structs at `0x03024358`. Treat this range as a reserved system/device state region (plausibly loader- or RTC-backed SRAM) in any memory-map documentation.

## Slot-geometry reconciliation (open)

- The module-1 validator works in device-3 logical sectors: slot 1 at 0; first slot-2 candidate at 0x6800 sectors (13 MiB); scan step 0x800 sectors (1 MiB), up to 0x14 candidates.
- The restore tool and NeoPod's `flash-neo.py` write slot 2 at Rockusb sector 30720 (15 MiB) and slot 1 at sector 0. Numerically, 30720 = 26624 + 2×2048, the validator's third scan candidate, so a header written there is findable by the stock validator on its third probe.
- But device-3 logical sectors pass through the +0x2000-sector offset and the partition stage, while Rockusb LBAs are maskrom-level. The two numberings cannot be equated from the image alone; the exact logical↔physical mapping still requires a read-back of a real unit's slots.

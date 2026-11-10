# Update block-device dispatch, DP3_V137

The updater in module 8 calls a generic block-device dispatcher in module 0, which selects a statically allocated callback table. It does not directly write a hard-coded flash-controller register.

The selector is `0x00030000`. At `0x030678b0`, the dispatcher computes `selector >> 16`, iterates two records of size `0x28`, and compares that ID against the 16-bit field at record offset `+0x24`. The table base is stored as a literal at `0x03067b50`, whose value is `0x0306e958`. The table is present in the original module 0 code bytes.

| Record | ID at +0x24 | Callback at +0x04 | Callback at +0x08 |
| --- | ---: | --- | --- |
| `0x0306e958` | `3` | `0x0305e021` | `0x0305fc09` |
| `0x0306e980` | `4` | `0x0305de87` | `0x0305fbb5` |

Callback addresses have bit 0 set for Thumb. Actual function entrypoints are even addresses.

`0x030678ca` calls the callback at `+0x04` with `BLX r12`. `0x03067912` calls `+0x08`. For device ID 3, the former enters `0x0305e020` (read) and the latter enters `0x0305fc08` (write). The updater passes a scratch-buffer destination to the former and firmware source bytes to the latter, then verifies with `memcmp`.

The two callbacks share a sector addressing structure.

- At `0x0305e020`, a subdevice selector in `r0` chooses an offset by summing values from `0x0305df72`. It queries sector count via `0x0305dd74` with drive index `1`, subtracts `0x2000` sectors in its range check, adds `0x2000` to the logical sector, and calls `0x0305dd32` with `r0=1`, `r1=logical_sector+0x2000`, `r2=count`, `r3=destination`.
- At `0x0305fc08`, the analogous path calls `0x0305fb64` with `r0=1`, `r1=logical_sector+0x2000`, `r2=count`, `r3=source`.

For 512-byte sectors, `0x2000` sectors correspond to 4 MiB. This is a **logical addressing offset** imposed by the callback. It is not yet a proven partition boundary or a physical NAND flash offset. The underlying treatment of bad blocks, ECC and wear leveling remains unknown. Do not use these addresses as a flashing procedure.

Cross-module call chain from original instructions:

```
module8  0x0307e64c  update file handler
             |
module8  0x0307e53c  block write/readback comparator
             |                 |
module0  0x03067912  write     0x030678ca  read
             |                 |
module0  0x0305fc08            0x0305e020
             |                 |
module0  0x0305fb64            0x0305dd32

module0 dispatch constant table: 0x0306e958, record ID = 3
```

The next question is which physical controller is reached from `0x0305fb64` and `0x0305dd32`, and whether the updater writes the entire rounded 13 MiB package or has a more specific length limit. The installed bootloader or a device trace is needed to establish the full install/boot sequence.

Reproduce the resolved table:

```sh
python3 tools/device_dispatch.py DP3_V137.img --device 3
```

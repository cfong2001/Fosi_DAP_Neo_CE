# USB mass-storage descriptor path, DP3_V137

Module 12 holds a USB Mass Storage Class implementation, with code loaded from file offset `0x8124c` to CPU address `0x0307f018` (length `0xfc4`). Its initialized data is at file `0x82210`, executing at `0x030373e8` (length `0x114`). Both are in the module table.

The configuration descriptor at file `0x8221c` (CPU address `0x030373f4`) declares one interface, class `0x08` (Mass Storage), subclass `0x06` (SCSI transparent), protocol `0x50` (Bulk-Only Transport). Endpoint `0x81` is IN bulk and endpoint `0x01` is OUT bulk, each with a 64-byte maximum packet. At file `0x82240` (CPU `0x03037418`) the same endpoints specify 512-byte packets. Each configuration has `wTotalLength=34` and `bMaxPower=200`, nominally 400 mA in 2 mA units. Both endpoint descriptors use `bLength=8` rather than the usual 7, so a strict USB compliance check requires care.

These descriptor arrays are not merely unreferenced strings. At `0x0307f88e`, module 12 reads a byte through a state pointer at `[r4+0x7c]` and compares it with `3`. The `IT EQ` at `0x0307f894` selects the high-speed descriptor address from literal `0x0307f96c` (`0x03037418`), otherwise the full-speed descriptor address from literal `0x0307f970` (`0x030373f4`). The caller subsequently uses offsets `+0x1a` and `+0x12` in calls to `0x0307d3d8` at `0x0307f8a4` and `0x0307f8b2`, respectively. These offsets correspond to the OUT endpoint address and the IN endpoint address in the selected 34-byte configuration descriptor. This is direct control-flow evidence that the descriptor variants are consumed by the implementation.

At file `0x82282`, the initialized data includes the 28-byte SCSI inquiry identity `Fosi    Audio DSP Neo   1.00`. This is an SCSI identifier, not a USB product ID. The USB vendor/product IDs, physical USB peripheral and whether USB Audio Class uses another module or operating mode still need verification. UI strings labelled `USB Audio` and `USB DAC Mode` do not establish any particular USB audio endpoint or driver.

For a deterministic read-only descriptor report, run:

```sh
python3 tools/usb_descriptors.py DP3_V137.img
```

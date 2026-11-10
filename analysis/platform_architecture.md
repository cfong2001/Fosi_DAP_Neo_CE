# Platform reconstruction and hardware boundaries (DP3_V137)

This is a best-supported architecture model, not a claim to have identified every populated component on the board. Findings from `DP3_V137.img` are distinguished below from the [Rockchip RKNanoD datasheet, revision 1.8](https://rockchip.fr/RKNanoD%20datasheet%20V1.8.pdf), the RKNanoD Technical Reference Manual (revision 1.0; what it settles is in [rknanod_trm.md](rknanod_trm.md)) and the [Fosi Audio DAP Neo specification](https://fosiaudio.com/products/dap-neo-mp3-player).

## SoC and processor

High-confidence inference: Rockchip RKNanoD-family, with two ARM Cortex-M3/Thumb-2 processing environments. Firmware evidence is the `RKnano SDK 1.0` package, a system executable with an M-profile vector at `0x03050000`, and ten alternate executable images at `0x01000000` with their own exception vectors. This architecture agrees with Rockchip's dual-core RKNanoD, called *system core* and *calculation core*. The update image does not identify a silicon part/package marking, revision, board strapping or running clock speed.

The RKNanoD datasheet describes an on-chip 16 KiB boot ROM, 320 KiB SYSRAM0, 256 KiB SYSRAM1, 128 KiB HIGHRAM0, 256 KiB HIGHRAM1 and 64 KiB PMU SRAM (its block-diagram PMURAM annotation differs, so confirm by actual memory probing). The ordinary system/hi-core SRAM totals 960 KiB, before reserved system space and application use. This is a significant Rockbox constraint.

The SoC supports, but the supplied update image does not independently prove all are populated or connected: eMMC/SPI NOR/NAND boot, SD/MMC, USB 2.0 OTG, mailbox intercore communication, two I2S interfaces, an internal codec, hardware MP3/lossless acceleration, three I2C controllers, two SPI controllers, six UARTs, PWM, GPIO, LCD controller, timers, DMA, ADC, clock/reset and watchdog. See the Rockchip datasheet for availability and electrical detail.

## Firmware-visible address layout

| Region | Firmware evidence | Interpretation |
| --- | --- | --- |
| `0x03004000` | Module 0 initialized-data destination; first vector SP `0x03004000` | System-side SRAM/data and stack boundary |
| `0x030059ac` | Module 0 BSS begins; length 126,484 bytes | Resident system state |
| `0x03050000` | Module 0 code VMA; 171,028 initialized bytes; reset vector `0x03061f8b` | System Cortex-M3 resident image; reset Thumb address `0x03061f8a` |
| `0x0307d164` and other nearby windows | Modules 1-62 and 81 share executable VMAs | Overlays/mutually exclusive services, not simultaneous fixed regions |
| `0x03024xxx` through `0x0304xxxx` | Overlay data/BSS VMAs | Reused system SRAM for service-specific state |
| `0x01000000` | Modules 71-80 code destination, own initial vector table | Calculation/HiFi core code window or remappable alias |
| `0x01020000` | Modules 71-80 data destination; vector SP `0x01022000` | Calculation-core data and stack |
| `0x0000298d` (module 71) | Reset vector has Thumb bit, despite nominal code VMA `0x01000000` | Low-address alias: the TRM's address map (Fig 2-1) likely shows HIGHRAM0 at `0x00000000` in the calculation core's view as well as at `0x01000000` ([rknanod_trm.md](rknanod_trm.md)); the figure's extracted text is garbled, so this is likely, not proven |
| `0x60080800` | Loaded literal in module 11 USB audio callback | MMIO peripheral base; registers `+0x340` and `+0x350` accessed |
| `0x60070000` | Multiple module-0 PC-relative literal loads | Peripheral/MMIO region, exact controller functions not all assigned |

There are 82 module records, but not 82 independently running processes. Modules 63-69 have no normal CPU execution address and contain compact tables/packed data. Module 70 is empty. Modules 71-80 each start with a second-core vector and contain `HifiFileOpen: timeout!!`, `HifiFileSeek: timeout!!`, `HifiFileRead: timeout!!`, `HifiFileWrite: timeout!!`, `HifiFileClose: timeout!!` strings. Their code and data windows overlap, consistent with alternate audio-decoder/service programs. The exact codec-to-module mapping and mailbox messages are not recovered yet.

## Boot, update and logical storage

The stock package is 13 MiB of payload plus a four-byte CRC, not a disk image. The module table maps load addresses to file offsets. The updater (module 8) and slot validator (module 1) are separate execution paths. The slot validator checks `RKnanoFW` magic and a 512-byte header mirror. It scans secondary candidate slots in 1 MiB steps starting at logical sector `0x6800` (13 MiB) and uses a four-byte BCD date for precedence. Both paths are documented at instruction addresses in [flash_security_and_port.md](flash_security_and_port.md).

The storage vtable at `0x0306e958` contains logical device ID 3 and callback entries `0x0305e021` (read) and `0x0305fc09` (write). Its callbacks add `0x2000` logical sectors to address arguments before lower-level I/O. Device ID 4 uses a different vtable at `0x0306e980`. Do not equate these to the storage medium's physical LBAs.

The first-stage boot ROM, flash loader, hardware boot pins, installed slot occupancy, partitioning, ECC/wear leveling, RockUSB PID and any secure-boot fuse policy cannot be established from this user-update file.

## Audio path

```text
TF card / other media source
    |
module 0 filesystem, input handling, UI and service overlay manager
    |
system-core decoder/file service [codec mapping incomplete]
    |              <mailbox/shared RAM inferred from dual-core image>
calculation-core modules 71..80 [HiFi file RPC strings, codec code candidates]
    |
decoded audio / sample rate conversion / EQ / volume [not fully mapped]
    |
I2S / digital audio serial link [wiring unverified]
    |
external Cirrus Logic CS43198 DAC [Fosi's published hardware specification]
    |
3.5 mm analog output
```

Fosi specifies one CS43198 DAC, a 3.5 mm single-ended output, Bluetooth SBC, and a 2.4-inch 320 x 240 display. The Cirrus [CS43198 product information](https://www.cirrus.com/products/cs43198) lists I2S/DSD-style digital audio inputs and an I2C control port. The image has not yet supplied an identified CS43198 I2C address, register-write trace, or a definitively traced PCM-to-I2S handoff. Do **not** assume the RKNanoD built-in analog codec drives the headphone jack.

The recovered USB DAC personality is a distinct input path. Module 11 advertises UAC1.0 stereo 16-bit/48 kHz over endpoint `0x02` with a 36 KiB PCM receive ring. Its HID consumer controls advertise play/pause, next/previous, mute and volume. The associated USB device descriptor gives VID/PID `0x071a:0x3289`. Module 12 separately provides full-speed and high-speed Mass Storage Class and an SCSI inquiry identity; its own device descriptor gives `0x071b:0x3203`. Host-side modes must be switched, not treated as simultaneous functions without evidence.

USB DAC 16-bit/48 kHz describes the USB host interface, not the maximum playback rate or the CS43198's intrinsic limits.

## Display, input, radio and Bluetooth

A 456-entry image resource section contains RGB565 assets; full-screen 240x320 images match the vendor's panel resolution in portrait orientation. The update image does not establish SPI versus 8080 parallel display wiring, LCD controller model or touchscreen. Button and volume control GPIO/ADC mappings need cross-referenced MMIO writes and a board trace.

Bluetooth/SBC support is an official Fosi claim. The SoC's serial interfaces support an external module, but no specific radio IC, pinout or HCI/UART connection has been proved from this binary. Strings for FM radio, games or recording also appear in shared RKNano resource tables and are not sufficient to assert supported hardware.

## Software organization and port cost

This is a tightly coupled MCU firmware, not a Linux system with userspace ELF applications. It has a resident system image, many address-overlapping overlays, filesystem and block-device wrappers, USB class implementations, a second-core HiFi program family, and fixed UI resource tables. Flash address mapping and peripheral ownership are not the same as in the Linux Rockchip RK27xx targets.

A practical first customization should patch a known UI string/function or load a small alternate overlay while keeping stock storage, media decoders, DMA, mailbox and DAC setup. A complete Rockbox port requires dual-core scheduling/IPC, memory budgeting, a link or replacement for audio decoders and CS43198 transport, a verified boot path, LCD/buttons, power management, USB, storage and recovery. The low SRAM budget, overlay dependence and missing bootloader are major barriers; cryptographic image signing is **not** the currently observed barrier.

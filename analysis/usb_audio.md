# USB DAC audio and HID, DP3_V137

The stock firmware contains an executable USB Audio Class (UAC) 1.0 function. Its descriptors and the code that configures endpoints live in module 11, not the USB mass-storage module 12.

Module 11 code executes at `0x0307e3c8` (file `0x804e4`, length `0xc50`), and initialized data executes at `0x03024ac0` (file `0x81134`, length `0x117`). It has `0x12810` bytes of BSS starting at `0x03024bd8`.

## Descriptor-level audio capability

The configuration at file `0x8113c` (CPU `0x03024ac8`, size `0x90`) declares three interfaces:

| Interface | Alternate setting | Meaning | Endpoint |
| --- | --- | --- | --- |
| 0 | 0 | AudioControl, USB Audio 1.0 | Control only |
| 1 | 0 | AudioStreaming idle | None |
| 1 | 1 | AudioStreaming active, PCM type I | `0x02` isochronous OUT |
| 2 | 0 | HID consumer control | `0x83` interrupt IN, `0x03` interrupt OUT |

The AudioControl descriptors form a concrete signal graph. Input Terminal ID `1` has terminal type `0x0101` (USB streaming), two channels with front-left/front-right channel configuration `0x0003`. Feature Unit ID `3` consumes Terminal `1` and has master mute and volume bits (`bmaControls=0x03`). Output Terminal ID `2` has terminal type `0x0301` (speaker) and takes its source from Feature Unit `3`. This describes the firmware's host-facing feature topology, not the separate physical headphone circuitry.

The AudioStreaming alternate setting declares stereo, 16-bit signed PCM at one listed sampling frequency: 48,000 Hz. Its endpoint `0x02` has attributes `0x09` (isochronous adaptive, OUT), a 192-byte maximum packet and one-millisecond interval. The packet budget matches 48 samples × two channels × two bytes per millisecond exactly. The descriptors provide **no second rate or 24-bit/192-kHz USB DAC alternate setting** in this module. This does not limit standalone playback formats, nor does it prove whether another firmware module can expose different configurations.

The device descriptor at file `0x81238` (CPU `0x03024bc4`) advertises USB vendor ID `0x071a`, product ID `0x3289`, and device release BCD `0x0200`. These are values from the update image; they have not been verified against actual enumeration of a physical device. The MSC module has a different device descriptor (`0x071b:0x3203`), consistent with alternate USB personalities.

## HID media-key function

The class descriptor at file `0x811b3` claims a 33-byte HID report descriptor, which exists at file `0x811cc` (CPU `0x03024b58`). It describes Consumer Control with eight one-bit input usages (`Report Count=8`, `Report Size=1`):

`E9` volume up, `EA` volume down, `E2` mute, `CD` play/pause, `B5` scan next track, `B6` scan previous track, `B3` fast-forward and `B7` stop.

The interrupt endpoints `0x83` and `0x03` each advertise two-byte maximum packets with interval two. This is affirmative firmware evidence for a USB HID media-control interface. It does not establish that every advertised action is physically mapped to a key on the DAP.

## Executed control paths and the PCM ring buffer

Original Thumb instructions in module 11 connect the descriptors to runtime handling. At `0x0307e56a`, the USB SET_CONFIGURATION branch loads the configuration pointer from literal `0x0307e7d0` (`0x03024ac8`), passes the address of its isochronous OUT endpoint descriptor (`+0x5e`) to endpoint setup routine `0x0307d3d8`, and then passes the HID IN descriptor (`+0x80`) to that routine. At `0x0307e532`, the GET_DESCRIPTOR dispatch checks descriptor type `0x22` (HID report) and sends at most `0x21` bytes from the report literal at `0x0307e7cc` (`0x03024b58`) through copy routine `0x03054e34`. These are explicit code references, not guesses from nearby strings.

At `0x0307e3c8`, the code calculates the free space in a `0x9000`-byte (36 KiB) circular buffer using read/write indexes at state-pointer offsets `+0x14` and `+0x18`. At `0x0307e3ec` it copies an incoming byte sequence into that ring, wraps at `0x9000`, and advances its write index. At `0x0307e64e` a callback path for endpoint/device selector `2`, mode `1`, consumes a buffer pointer from state `+0x4c`, checks available ring capacity, then copies bytes into the same ring at `0x03024c48` (literal `0x0307e7c0`). This is concrete evidence for an inbound USB PCM staging buffer, although the downstream DAC/I2S consumer has not yet been mapped.

The same callback at `0x0307e66e` loads a memory-mapped register base `0x60080800` (literal `0x0307e7d8`) and reads/modifies registers at base offsets `+0x340` and `+0x350` (`0x60080b40` and `0x60080b50`) while changing streaming state. These are actual peripheral register accesses. Identifying the register block or claiming a specific silicon implementation will require the corresponding Rockchip register reference or an on-device trace.

A USB Audio control handler at `0x0307e438` handles two request selectors and writes state bytes for volume/mute. The routine compares values against `0x8000`, `0x80ff`, and `0x8010`, and updates a shared state record. Exact physical gain conversion and downstream mixer/DAC volume control remain unverified.

## Reproduction

```sh
python3 tools/usb_audio.py DP3_V137.img
python3 tools/rknano_image.py DP3_V137.img elf 11 module11.elf
llvm-objdump --mcpu=cortex-m3 -d module11.elf
```

`tools/usb_audio.py` reads actual descriptors from module 11, verifies firmware SHA-256, returns full offset/byte provenance, and never accesses a connected USB device.

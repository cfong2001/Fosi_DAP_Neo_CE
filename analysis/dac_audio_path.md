# DAC control path: CS43198 over I2C0, register API, init data, executed frames

Scope: stock `DP3_V137.img`, module 0 (system core) unless noted. Evidence is (a) Capstone disassembly of the original instructions and (b) Unicorn execution of the original `dac_write`/`dac_read` machine code with only the bus-layer callees stubbed (`work/main/emu_dac.py`). The executed frames below are the original code's output, not a reimplementation.

## Register access API

- `dac_write(map, value)` at `0x03060c4c`
- `dac_read(map, &out)` at `0x03060d28`

Both build the Cirrus MAP frame on the stack: `[map>>16, map>>8, map, 0x01, value]`. The frame is a 24-bit big-endian register address, then the 0x01 auto-increment byte, then data. Writes pass 5 bytes to the transfer function `0x03060622` (mode argument 3 on the stack); reads pass the 4-byte address phase, then take 1 byte back through the read-phase function `0x030608d0`.

Bus sequence in both helpers:

1. If the error-counter byte at `[0x0300411d + 1]` is ≥ 2, the access is silently skipped and 0 returned. (A failed transfer increments this byte; nothing in these helpers ever decrements it. After two lifetime I2C failures, DAC control is dead until reboot. Worth knowing for any custom-firmware work.)
2. Bus select `0x0306021c(bus=0, addr=0x66, param=0x190=400)`. The address immediate is hard-coded: `movs r1, #0x66` at `0x03060cfa` (write) and `0x03060d52` (read). 0x66 is the address byte as placed on the wire (7-bit address 0x33, write direction).
3. Transfer; bus release `0x0306043a(0)`.
4. `dac_read` also calls `0x0306d8f0` after the read, a logging call taking a format string, the map, and the value read. The stock firmware logs every DAC read.

Executed verification (Unicorn, original code, bus callees stubbed; bus-select arguments captured as `(0, 0x66, 400)`):

| call | frame on the wire |
|---|---|
| dac_write(0x020000, 0xF6) | `02 00 00 01 F6` |
| dac_write(0x0F0010, 0xE7) | `0F 00 10 01 E7` |
| dac_write(0x010010, 0x99) | `01 00 10 01 99` |
| dac_write(0x080032, 0x20) | `08 00 32 01 20` |
| dac_read(0x0F0000) | address phase `0F 00 00 01`, then 1-byte read phase |

## The volume transform hidden inside dac_write

`dac_write` does not send the value unchanged for the two PCM volume registers. It reads a state byte at `[0x030232a0 + 0x2e8]` and computes `r2 = 12 − state` (if state < 12) and `r3 = state − 12` (if state > 12):

- map `0x090001`: sends value + r2, or value − r3
- map `0x090002`: sends value − r2, or value + r3 (mirror image)
- value `0xFF` passes through unchanged for both maps (mute sentinel)

Executed results (original code):

| state byte | dac_write(0x090001, 0x78) | dac_write(0x090002, 0x78) |
|---:|---|---|
| 0 | 0x84 | 0x6C |
| 6 | 0x7E | 0x72 |
| 12 | 0x78 | 0x78 |

That is a balance-style L/R trim, centered at 12, range 0-24, applied symmetrically to the two channel volume registers every time volume is written. The byte lives in the same state block as the playback-mode byte (+0x2e3, which selects the `0x090000` value in the init routine) and the gain byte (+0x2e4). Cross-track resolution (see `analysis/ui_controls.md`) shows the block at 0x030232A0 is the persistent SAVEINFO settings record. Its boot validator clamps exactly this byte to 0-24 with default 12, and the settings UI exposes it too (language string 172 is 'Channel Balance', sitting immediately before 173 'EQ Settings' in the menu's string-ID-keyed item table). So +0x2E8 is the Channel Balance setting, fully wired from UI to DAC. Either way, a custom firmware that writes volume through `dac_write` inherits the trim, and one that bypasses `dac_write` must apply it deliberately or accept a channel imbalance when the setting is non-12.

Channel-config special cases, also inside `dac_write` and confirmed by execution:

- dac_write(0x05000A, 0xFF) sends value 0x07
- dac_write(0x05000B, 0xFF) sends value 0x0F

i.e. the 0xFF sentinel on those two maps is replaced by fixed channel values (the same 0x07/0x0F pair the unrolled init sequence writes literally).

## I2C controller and pins

The transfer function `0x03060622` takes the controller base from a 12-entry table at `0x0306dd7c`, indexed by bus number: bus 0 → 0x40040000. Register usage matches the Rockchip I2C IP block: IEN at +0x18 (written 0), IPD at +0x1C (written 0x7f to clear pending), CON at +0x00 (OR-ed with 9: enable + start). TXDATA/RXDATA sit at +0x100/+0x200 per the same register map in NeoPod's driver.

The bus-select function's bus-0 case performs the pin mux through the GPIO config helper `0x030526f8(2, 10, 1)` and `0x030526f8(2, 11, 1)`: I2C0 on GPIO2.10 / GPIO2.11.

Address-view note: the peripheral base table lives in 0x40xxxxxx space (0x40040000, 0x40050000, 0x40060000, 0x40160000, 0x40170000, 0x50030000, 0x400a0000, 0x400b0000, 0x400c0000, 0x40130000, 0x40140000, 0x40150000), while the MMC and USB blocks are addressed in 0x60xxxxxx space in the same firmware. Both views are stock behavior; which core/bus alias each represents is not resolved by this image.

## Static init table (73 register writes)

At `0x0306ddac` (file 0x47458) sits a table of 73 `(u32 map, u32 value)` pairs, ending at file 0x476a0 where the clock table (below) begins. Full dump: `work/main/dac_table.txt`. Highlights:

- PLL group: `0x040010=0x01, 0x040012=0x08, 0x040014=0x1F, 0x040016=0x3F, 0x040018=0x0C, 0x040019=0x0A` (and the mirrored 0x04002x group). These match the values the unrolled init writes and NeoPod replays.
- `0x01000C=0x04`, `0x020000=0xFE`, `0x020052=0x04`, `0x0D0000=0x04`, `0x0F0010..14=0xFF` (interrupt mask writes).
- `0x080000=0x30` (gain map; the unrolled init uses 0x31/0x10 for high/low gain) and PCM volume defaults `0x090001=0x090002=0x78`.
- `0x05000A=0x06`, `0x05000B=0x0E`. Note these differ by exactly 1 from the 0x07/0x0F pair used by the unrolled init and the dac_write sentinel substitution. The table's consumer is a function in the DAC-init cluster (its base pointer sits in the literal pool at file 0x2b074 / exec 0x030519c8, alongside the map constant 0x000F0010), but which playback mode plays this table (and why its channel values are one step lower) is unresolved. Do not merge the two lists.

Immediately after the table (file 0x476a0) is a per-rate clock table of 6-word records in two series. First series (48 kHz family): `(24000, 30720, 0, 24, 25, 10)`, `(24000, 30720, 0, 24, 25, 10)`, `(24000, 61440, 0, 48, 25, 10)`, `(24000, 122880, 0, 48, 25, 9)`, `(24000, 122880, 0, 48, 25, 9)`. The second column is the master clock in 100 Hz units (30720 → 3.072 MHz, 122880 → 12.288 MHz). After a zero record, the second series (44.1 kHz family, file 0x47730): `(24000, 28224, 3, 18, 25, 3)`, `(24000, 28224, 3, 18, 25, 3)`, `(24000, 56448, 6, 36, 25, 3)`, where 28224 = 44.1 k × 640 and 56448 = 88.2 k × 640. Field semantics beyond the rate/clock columns are not decoded. (An earlier draft of this analysis read the first clock records as extra DAC pairs on the 8-byte grid and reported 88 pairs; the 6-word record structure shows the DAC table proper is 73 pairs.)

## Unrolled init and power sequencing

The main init routine at `0x0305175e` performs the register list literally (cross-referenced in full against NeoPod in `work/neopod-xref/neopod_xref.md` §A9, including one variance: stock's `0x090000` write is mode-conditional (0x02 for mode 0, else 0x42/0x82/0xC2/0x22), where NeoPod hard-codes 0x02). Its continuation (`0x030518f0`-`0x03051a6x`) does the output release:

1. Read `0x020000`, clear bit 0x40, write back; delay.
2. `0x010010 = 0x99`; `0x080032 = 0x20`.
3. Read `0x020000`, clear bit 0x10, write back; delay 10 (`0x03064944`).
4. `0x080032 = 0x00`; `0x010010 = 0x00`; further writes to `0x01000D`, `0x010010` region.
5. Tail at `0x03051a62`: GPIO1.4 (amp enable) muxed, set to output, driven high via `0x030526f8 / 0x03056098 / 0x030560d2`.

Before that common path, both playback overlays (module 11 at `0x0307ea46` and module 33 at `0x03089e5c`, byte-identical in substance) contain a pin pre-sequence: DAC RESET (GPIO2.1) high, AMP (GPIO1.4) low, ENABLE_B (GPIO2.2) high, delays of 2 ms, 1 ms, 8 ms, RESET low, then call into the common routine via `0x030611e0`. In module 33's codec open (`0x03089e2e`) this sequence and the DAC start are guarded: if the byte at `[0x03023125]` is non-zero, open branches to `0x03089f2a` and skips both entirely. The byte is set on first open and cleared only by the stop/close function (`0x0308a926`, at `0x0308a94c`). The natural end-of-track path never calls that function. So the pin sequence + DAC configure run **once per playback session** (first play after boot, or after any full stop / mode switch), not per track. Staged delays in the full sequence total 11 + 80 + 80 + 10 = 181 ms plus I2C transfer time for ~50 register writes, and the configure writes the PCM volume registers muted (0xFF) before release. What runs on *every* codec open, guard or not, is cheaper but not free: I2S re-config initialised at a fixed 48000 (`0x03089f06`), a fixed `delay_ms(100)` (`0x03089f16`), and a position-sync polling loop (15 ms polls, 200-iteration cap). Full transition trace: `analysis/gapless.md`.

## What is proven vs open

Proven (instructions + execution): the API addresses and frame format; the hard-coded 0x66 address byte; the error-counter gate; the volume/balance transform and the 0x05000A/B sentinel substitutions (executed); the I2C0 base 0x40040000 and GPIO2.10/2.11 mux; the 73-entry table's contents and location; the overlay pre-sequence pins and delays.

Open: which mode plays the 73-entry table; the clock-table field semantics. (The balance byte's UI exposure is resolved: it is the 'Channel Balance' settings item, string ID 172; see above.)

Resolved since first draft (see `analysis/gapless.md`): the PCM consumer path. Local playback and USB audio share one DMA feed. Module 0's DMA config `0x0305ff74` is called from module 33 at `0x0308a8f6` with channel 5, source = ring pointer at `[0x03023928]`, destination = `0x40030024` (the I2S TX data register in the 0x40xxxxxx peripheral view; NeoPod's I2S1 base is likewise 0x40030000), length at `[0x03023938]`. The decoder core never touches the I2S FIFO itself (no decoder module contains the register literal); it fills the shared-SRAM ring and the system core owns the DMA. The 0x60082000 references in modules 71-80 are the decoder core's own view of its audio/control interface, not the system core's I2S path.

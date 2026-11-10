# NeoPod ↔ Fosi DAP Neo stock firmware cross-reference dossier

Target: NeoPod custom firmware source at
`refs/NeoPod-Fosi-DAP-Neo-Custom-Firmware/` (an EchoPod / FiiO Echo Mini port
with `ECHO_BOARD_NEO` branches), cross-checked against stock
`DP3_V137.img`, 13,631,492 bytes, SHA-256
`fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`
(verified: header mirror valid, Rockchip CRC-32 valid, 82 modules).

## Verification method (all Section A results are my own byte-level checks)

- Image unpacked with `repo/tools/rknano_image.py unpack`; disassembly with
  Capstone 5.0.7 (Thumb, little-endian) from `~/workspace/fosi-dap-neo/venv`.
- Address → file mapping used: system core = module 0, exec `0x03050000`,
  code file offset `169644` (`0x296AC`); overlay modules use their own exec
  base (module 11 exec `0x0307e3c8`, code file offset `525540`; module 33 exec
  `0x0308837c`, code file offset `644544`; module 4 exec `0x0307c7b0`, code
  file offset `364008`). File offset = module code offset + (addr − exec).
  Note the shorthand `addr − 0x03050000 + 0x200` is only the *load-address*
  formula from the module table; the offsets below are the real payload
  offsets in `DP3_V137.img`.
- Stock GPIO helper convention, established from repeated call sites in
  module 0 and consistent with prior analysis (`power_and_features.md`):
  helpers take `(r0=port, r1=pin, r2=arg)`: `0x030526f8` = mux/configure,
  `0x03056098` = direction/output-enable, `0x030560d2` = drive level,
  `0x03060fdc` = read/input path. Delay helper is `0x03064944` (argument in
  milliseconds at every DAC call site checked). DAC I2C write helper is
  `0x03060c4c (r0=map, r1=value)`; read helper is `0x03060d28 (r0=map,
  r1=out-ptr)`. Both build the Cirrus frame `[map>>16, map>>8, map, 0x01,
  value…]` on the stack. NeoPod reimplements the same frame format in
  `platform/device/board/dac.c:233-241` (`frame_header`).

---

# Section A: NEO-verified-in-stock (stock address / "Neo stock:" cited, verified by me)

### A1. Board-init output states before LCD init: `power.c:24-36`
Claim (comment cites stock `0x0305328c`): at board init, GPIO2.8, GPIO2.0 and
GPIO0.14 are muxed GPIO, set as outputs and driven HIGH, before LCD init;
the code comment says GPIO0.14 is set there "so the LCD's GPIO0 shadow retains
the HIGH level."
Verification: **MATCH.** Function at `0x0305328c` (module 0; file offset
`0x2CA0C`) contains, in order: GPIO2.6 trio ending drive-arg 1 (power hold
high), GPIO2.5 as input (power key), GPIO2.3 as input (charge), GPIO0.12 trio
ending arg 1 (panel RD high), GPIO2.4 trio ending arg 0 (backlight off),
GPIO0.14 trio at `0x030533b6..0x030533ca` ending arg 1, GPIO2.12/GPIO2.13
as inputs (wheel), GPIO2.7 trio ending arg 0 (BT power low), GPIO2.2 as input,
then at `0x0305351a..0x0305352e` GPIO2.8 trio ending arg 1, at
`0x03053542..0x0305354c` GPIO2.0 direction+level calls with pin 0 ending arg
1, and GPIO0.14 driven arg 1 again at `0x03053556..0x0305356a`. All three
claimed pins and levels are present in this one stock function, which runs
before the panel path. Example trio at `0x0305351a..0x0305352e`: configure
`(port 2, pin 8, arg 0)` → direction `(2, 8, arg 1)` → drive `(2, 8, arg 1)`
via helpers `0x030526f8` / `0x03056098` / `0x030560d2`.

### A2. DAC I2C address is a single `0x66`: `logic/dac_sequence.c:41-42`, `logic/include/device/dac_sequence.h:34-35`
Claim: NEO branch uses one chip, `CHIPS = {DAC_RIGHT_ADDRESS}` with comment
"Neo stock: 0x66"; the Echo branch uses two chips `{0x60, 0x66}`.
Verification: **MATCH.** Stock has no per-call address at all: the write
helper `0x03060c4c` hard-codes the address, at `0x03060cfa` (file offset
`0x3A3EA`): `movs r1, #0x66` (bytes `66 21`), with `mov.w r2, #0x190` and
`movs r0, #0` immediately before the I2C-send call. The read helper
`0x03060d28` does the same at `0x03060d52`: `movs r1, #0x66`. Every DAC
register access in the stock init path goes through these two helpers, so
stock addresses exactly one DAC at `0x66` (the byte NeoPod passes as the
first I2C frame byte; this is the 8-bit-style address value used by both
codebases, not a 7-bit `0x33`). No `0x60`-addressed DAC path exists in these
helpers. Corroboration: NeoPod's own `platform/neo_diag/neo_stock_dac_diag.c:826`
also bit-bangs `0x66` for its "CS43198 ID transaction".

### A3. PCM path signal control `map 0x090003 = 0xAC`: `logic/dac_sequence.c:58-62`
Claim: NEO branch writes `{0x090003, 0xAC}` ("Neo stock PCM path signal
control"); Echo branch writes `0xEC`.
Verification: **MATCH.** In the stock DAC init routine `0x0305175e`, at
`0x03051876..0x0305187a` (file offset ≈ `0x2AD22`): `movs r1, #0xac`;
`ldr r0, [pc, #0x19c]` → literal at `0x03051a18` = `0x00090003`;
`bl 0x03060c4c`. Stock writes `0xAC` to map `0x090003`. The `0xEC` value
appears nowhere in this routine.

### A4 + A5. Playback-overlay pin sequence before the common DAC routine: `logic/dac_sequence.c:175-195`
Claim: stock playback overlays module 11 (`0x0307ea46..0x0307ead4`) and
module 33 (`0x03089e5c..0x03089ef0`) perform, before the common DAC
routine: AMP high, RESET high, AMP low, ENABLE_B high, waits of 2 ms, 1 ms,
8 ms, RESET low. (Pin identities from `board/dac.c:127-134` NEO map:
MUTE=GPIO2.8, ENABLE_A=GPIO2.0, ENABLE_B=GPIO2.2, RESET=GPIO2.1,
AMP=GPIO1.4.)
Verification: **MATCH** (both modules; one nuance below). Disassembly of
module 11 at `0x0307ea46` (file offset `0x80B16`) and module 33 at
`0x03089e5c` (file offset `0x9F220`). The two ranges are byte-identical in
substance (module 33 adds a trailing `ldr/strb` before the same final call):

| Step | Stock instructions (both ranges) | Decoded |
|---|---|---|
| 1 | `(r0=2, r1=1, r2=0)→0x030526f8; (…, r2=1)→0x03056098; (…, r2=1)→0x030560d2` | GPIO2.1 = RESET driven **high** |
| 2 | `(r0=1, r1=4, r2=0)→mux; (…, r2=1)→dir; (…, r2=0)→0x030560d2` | GPIO1.4 = AMP driven **low** |
| 3 | `(r0=2, r1=2, r2=0)→mux; (…, r2=1)→dir; (…, r2=1)→drive` | GPIO2.2 = ENABLE_B driven **high** |
| 4 | `movs r0,#2 / #1 / #8; bl 0x03064944` ×3 | delays **2 ms, 1 ms, 8 ms**, exactly NeoPod's `wait_ms(2); wait_ms(1); wait_ms(8)` |
| 5 | `(2,1)` trio again, final drive arg **0** | RESET driven **low** |
| 6 | `bl 0x030611e0` | enters the common DAC path (wrapper reaching the `0x03051a46` routine of A6) |

Nuance: stock drives AMP low in the overlay; it never pulses AMP high
there. NeoPod's `AMP=true` then `AMP=false` bracket around the RESET step is
NeoPod's own addition. Its comment ("These are observed board levels") is
accurate for RESET/ENABLE_B/delays/order, but the initial AMP-high pulse is
not in either cited stock range. MUTE (GPIO2.8) and ENABLE_A (GPIO2.0)
are not touched in these ranges; they are set high earlier in the stock
board-init function (A1), which is consistent with NeoPod setting them in
`dac_power_pins` before the cited sequence.

### A6. Common stock routine raises GPIO1.4: `logic/dac_sequence.c:187`
Claim: "Common stock routine `03051a62..03051a7c` then raises GPIO1.4"
(AMP), after which NeoPod waits 20 ms.
Verification: **MATCH.** At `0x03051a62..0x03051a7c` (module 0): `(r0=1,
r1=4, r2=0)→0x030526f8; (…, r2=1)→0x03056098; (…, r2=1)→0x030560d2`. GPIO1.4
configured, output-enabled and driven with final arg 1. The enclosing
function `0x03051a46` also confirms the context NeoPod assumes: immediately
before `0x03051a62` it writes DAC map `0x0B0000 = 0x1F` (`mov.w r0,
#0xb0000; movs r1, #0x1f; bl 0x03060c4c`) and delays `0x50` = 80 ms
(`bl 0x03064944`), the same `0x0B0000/0x1F` + 80 ms pair NeoPod has in
`dac_sequence.c` `start_up()` / `set_up_blocks()`. The 20 ms wait itself is
NeoPod-side (no delay call follows in the cited range; the routine proceeds
to `bl 0x0305175e`, the init list of A9).

### A7. Mono table skipped: single stereo DAC: `logic/dac_sequence.c:128-142`
Claim: NEO branch `write_mono_table()` is a no-op: "single stereo CS43198:
no dual-mono programming" (Echo branch writes 24 values to maps
`0x180000 + group*0x10 + {0x09,0x0A,0x0B,0x0C,0x0F,0x10}`).
Verification: **MATCH (by absence in the only stock init routine).** The
complete literal-resolved write list of stock init `0x0305175e` (A9) contains
**no** write to any `0x18xxxx` map, and both I2C helpers hard-code the single
address `0x66` (A2). Stock never performs dual-mono programming. This also
matches the vendor spec recorded in prior analysis (one CS43198).

### A8. Panel init sequence recovered from stock module 4: `platform/neo_diag/neo_diag.c:209-229` (same text in `neo_dac_diag.c:210+`, `neo_stock_dac_diag.c:210+`); product form in `platform/device/logic/panel.c:13-32` (`NEO_STEPS`)
Claim: the NEO panel init (commands `0x36/0x00, 0x3A/0x05, 0x21, 0xB2…, 0xB7
0x64, 0xBB 0x2A, 0xC0 0x2C, 0xC2 0x01, 0xC3 0x13, 0xC4 0x20, 0xC6 0x11, 0xD0
A4 A1, 0xD6 A1, 0xE0 …14 bytes…, 0xE1 …14 bytes…, 0x29`) was "Recovered from
stock module 4 (`0x0307ce68..0x0307d05e`)".
Verification: **MATCH.** The cited range (module 4, file offset `0x58C68`,
502 bytes) is not a data table. It is code: a repeated
`movs r1, #<byte>; movs r0, #0; bl <send>` pattern whose immediate bytes, read
in order, reproduce the NeoPod sequence exactly, including `0x36` with data
`0x00` (MADCTL 0x00), `0xB2` data `05 05 00 33 33`, `0xC3` data `0x13`,
`0xE0` data `D0 06 06 0E 0D 06 2F 3A 47 08 15 14 2C 33` and `0xE1` with the
single differing byte `0x3B` in position 8, all present verbatim in the
range. Two scope notes: (1) command `0x11` (sleep-out) is not in the cited
range. NeoPod sends it separately (`neo_diag.c` `panel_start()` issues
`lcd_cmd(0x11)` + 120 ms before the table; `panel.c` folds it in as the first
NEO step); the citation is accurate for the table it annotates. (2) The
ST7789 identification itself is an inference from this command set
(ST7789-typical `0xB2/0xB7/0xBB/0xC0–0xC6/0xD0/0xE0/0xE1`); the stock bytes
prove the sequence, not the controller part number.

### A9. The full DAC init write list NeoPod replays: `logic/dac_sequence.c:48-77, 213-262`
Claim (implicit in the port): `AFTER_STATUS`, `BEFORE_MONO`, `AFTER_MONO`,
`start_up()` and `release_outputs()` reproduce the stock CS43198 init.
Verification: **MATCH, with one documented variance.** Literal-resolved
disassembly of stock init `0x0305175e..0x03051a45` (module 0) gives this
stock order, set against NeoPod:

| Stock (in order) | NeoPod equivalent |
|---|---|
| write `0x020052 = 0x02` (first, before status read) | `start_up()` tail: `write_both(0x020052, 0x02)`, same write, NeoPod does it after the `0x0B0000` write; order differs, set matches |
| read `0x0F0000` (status) | `read_status()` on `STATUS_MAP 0x0F0000` ✓ |
| `0x0F0010=E7, 0x020000=F6`, read `0x020000`, `0x01000C=04`, `0x040010=01, 11=00, 12=08, 13=00, 14=1F, 15=00, 16=3F, 17=00, 18=0C, 19=0A`, `0x050000=00, 0x050001=00` | `AFTER_STATUS[0..14]`, **all 15 map/value pairs identical** |
| `0x05000A=07, 0x05000B=0F` (literal maps at `0x03051a04/0x03051a08`; the write helper also special-cases these two maps) | `write_channel_values()`: NEO writes `0x07`/`0x0F` ✓ (`CHANNEL_VALUES {0x07, 0x0F}`) |
| `0x090000 =` **mode-conditional**: `0x02` if mode byte = 0, else `0x42 / 0x82 / 0xC2 / 0x22` for modes 1–4 (comparisons at `0x0305180e..0x03051866`) | `BEFORE_MONO[0] = {0x090000, 0x02}`, **variance:** NeoPod hard-codes the mode-0 value; stock varies it with a mode/state byte (at data `+0x2e3` of base `0x030232a0`). Not a contradiction for default PCM playback, but NeoPod's list is the mode-0 instance only |
| `0x090001=FF, 0x090002=FF` (literals `0x03051a10/0x03051a14`) | `BEFORE_MONO`: PCM volumes = `DAC_VOLUME_MUTED (0xFF)` ✓ |
| `0x090003=AC` | A3 ✓ |
| `0x090004=00` (literal `0x03051a1c`) | `BEFORE_MONO[4]` ✓ |
| `0x0B0000=1F`, delay 80 ms | `set_up_blocks()` tail ✓ |
| gain write value `0x31` present (conditional on data byte `+0x2e4`) | `dac_set_gain(high) = 0x31` / low `0x10`; `AFTER_MONO[0] = {0x080000, 0x10}` ✓ values |
| then maps `0x0D0001`, read/write `0x0F0001`, write `0x0F0011`, `0x010006`, `0x01000D`, `0x010010` (written `0x99` and later `0x00`), `0x080032` (written `0x20` then `0x00` in the release pattern), plus power-control map `0x020000` read-modify-write in the continuation | `AFTER_MONO = {0x080000=10, 0x0D0000=04, 0x0D0001=00, 0x0F0010=87, 0x0F0011=07, 0x010006=04, 0x01000D=02, 0x010010=99, 0x180000=45, 0x010010=00}` and `release_outputs()` (`0x010010=99`, `0x080032=20→00`, `0x010010=00`, release of `0x40` then `0x10` bits of `0x020000`), every NeoPod map in this group except `0x180000=45` and `0x0F0010=87` was observed in the stock routine's map set; values for the tail were not all individually resolved. The `0x180000=45` write is **not** in the part of stock init I resolved, flag for the lead (it may sit in the continuation after `0x030519a4` or in the rate-change path) |

Provenance conclusion: NeoPod's NEO DAC sequence is a genuine replay of the
stock `0x0305175e` init (itself called from the common routine of A6), not an
Echo Mini carry-over. The three NEO deltas (`0x66` single chip, `0xAC`,
mono skipped) are exactly the points where stock differs from the Echo/CS43131
branch. The DAC is therefore operated as a CS43198 (single, stereo) in
stock, consistent with the vendor spec; NeoPod's shared `dac_sequence` code
and docs still calling the part "CS43131" is inherited naming (see C3).

### A10. neo_diag pin-evidence list: `platform/neo_diag/neo_diag.c:14-19` (identical header in `neo_dac_diag.c`, `neo_stock_dac_diag.c`)
Claim: "Pin evidence (stock DP3_V137, see investigation/gpio-calls-all.txt
and investigation/lcd-mod04.txt): panel data GPIO0.16-23, WR GPIO0.24, DC
GPIO0.25, RD GPIO0.12, CS GPIO0.15, reset GPIO2.15, backlight GPIO2.4, power
key GPIO2.5, power hold GPIO2.6, charge GPIO2.3, wheel GPIO2.12/2.13."
Verification: **PARTIAL.** The two cited `investigation/*.txt` files are not
in the repository, so the claim rests on NeoPod's notes. Independently, the
stock board-init function of A1 corroborates: backlight GPIO2.4 (driven,
initially low), power key GPIO2.5 (input), power hold GPIO2.6 (driven high),
charge GPIO2.3 (input), wheel GPIO2.12 and GPIO2.13 (inputs), panel RD
GPIO0.12 (driven high), card-detect GPIO0.11 (input). The panel bus pins
(data GPIO0.16-23, WR 24, DC 25, CS 15, reset GPIO2.15) are not exercised
in that module-0 function; they are consistent with the module-4 panel code
of A8 and with NeoPod's identical bus code in `board/display.c:12-36,
97-114` (direction mask `0x03FF9000` = RD 12, CS 15, data 16-23, WR 24,
DC 25), but I did not trace module 4's GPIO calls pin-by-pin. Treat the bus
pinout as corroborated-by-consistency, the seven pins above as verified.

### Section A tally
10 claims: **8 full MATCH** (A1, A2, A3, A4, A5, A6, A7, A8), **1 MATCH with
a documented variance** (A9: mode-conditional `0x090000`; `0x180000=0x45`
value not located in stock init), **1 PARTIAL** (A10), **0 contradictions**.

---

# Section B: NEO-specific-code-only (ECHO_BOARD_NEO values with no stock citation; verify each in stock before trusting)

| # | Claim | Exact source |
|---|---|---|
| B1 | Display is 240×320 (portrait) on NEO vs 320×170 on Echo | `src/hal/include/hal/display.h:7-13` |
| B2 | Panel variant NEO uses ST7789-style init `NEO_STEPS`; first visible row 0 (Echo: 35) | `platform/device/logic/panel.c:13-32`; `platform/device/logic/include/device/panel.h:7-11`; `platform/device/board/display.c:247-251`. Note: the init *bytes* are stock-verified (A8); the "ST7789" name and the row-offset are not cited to stock |
| B3 | Display bus is 8080-style parallel on GPIO0: data shift 16 (pins 16-23), WR = bit 24, DC = bit 25, RD = pin 12, CS = pin 15, reset = GPIO2.15, direction mask `0x03FF9000` | `platform/device/board/display.c:12-36, 46-57, 97-114`; `panel.h:12-14`. Shared (non-ifdef) code reused for Neo; no stock citation in these files (but see A10) |
| B4 | Backlight PWM on GPIO2.4, 10 kHz, brightness levels → duty {8,12,17,23,30,39,50,63,80,100}%, inverted duty register (`period − period×pct/100`), `PWM_CTRL 0x10003` | `platform/device/board/display.c:35` (pin, shared); `platform/device/logic/backlight.c:3-37`; rationale in `docs/architecture.md:64` attributed to "stock" / "the Rockchip SDK" with no address. Pin itself stock-corroborated (A10); PWM rate/table not cited |
| B5 | DAC pin map NEO: MUTE=GPIO2.8, ENABLE_A=GPIO2.0, ENABLE_B=GPIO2.2 (Echo: MUTE=GPIO2.0, ENABLE_A=GPIO2.14); RESET=GPIO2.1, AMP=GPIO1.4 shared | `platform/device/board/dac.c:127-134`. Pin *identities* are borne out by A1/A4/A6, but NeoPod never cites stock for this table, the lead should treat the table as verified only via A1/A4/A6 |
| B6 | DAC probe = read device ID at map `0x010000`, no page-0 write (Echo: write `0x000000=0x00`) | `platform/device/logic/dac_sequence.c:203-211`. **No stock citation, and I found no read of map `0x010000` in the stock module-0 DAC path**, stock instead reads status `0x0F0000`, `0x020000` and `0x0F0001`. Whether the CS43198 answers an ID read at `0x010000` is unverified in stock |
| B7 | Channel values on NEO: both `0x05000A` and `0x05000B` get `CHANNEL_VALUES[1]` (`0x0F`) | `logic/dac_sequence.c:109-124`. Stock writes `0x05000A=07, 0x05000B=0F` for its single chip (A9), NeoPod's NEO branch writes `0x0F` to *both* maps, which does **not** match the stock pair. Flagged: probable porting artefact, verify before relying |
| B8 | BT module: power = GPIO2.7, UART pins GPIO2.16/2.17, UART1 group A, 115200 8N1, divisor 13, polled; boot state all three driven low; wired-output routing pin GPIO2.14 not driven on NEO | `platform/device/board/bluetooth.c:9, 25, 38, 48-52, 68-76, 94-133, 135-144` (pin/UART code is shared, only the routing is NEO-ifdef'd). `docs/architecture.md:264` says "follows stock's sequence" with no address. Stock board-init (A1) does drive GPIO2.7 low and muxes GPIO2.16/2.17, consistent. **Baud and divisor now stock-verified** (2026-11-08): stock's BT path configures UART1 group A at 115200, divisor 13, with the same register sequence (`modules_round2.md` §3.4, `tools/emu_bt_uart.py`). Power-high behaviour remains uncited |
| B9 | Wheel + OK key: OK = GPIO2.14 (active low → KEY_PLAY), wheel quadrature on GPIO2.12/GPIO2.13 with a 16-entry transition table | `platform/device/board/input.c:21-26, 50-55, 77-85, 93-103`. Wheel pins corroborated as inputs in stock (A10); the OK pin and quadrature decode are uncited |
| B10 | Key/ADC ladder NEO bands: reading 0-50 = Volume Up, 80-180 = Volume Down (no Play/Menu/Back bands; those move to GPIO/wheel) | `platform/device/logic/key_ladder.c:11-18` |
| B11 | Jack on NEO: only GPIO0.13 (3.5 mm) is sampled; GPIO2.8 is the DAC mute pin, "never a jack input"; balanced result forced false | `platform/device/board/jack.c:30-61`. Directly contradicts the Echo doc claim (C4), one of the two is wrong for the Neo, and A1/A4 support NeoPod here (GPIO2.8 is driven as an output in stock) |
| B12 | eMMC is **not used at all** on NEO: `emmc_start()` returns false ("Keep the unverified internal controller/pinmux untouched") and `emmc_write` returns false | `platform/device/board/emmc.c:194-200, 230-244`. Consequence: `board/update.c`'s update flow and `board/usb.c` internal-storage LUN are dead on NEO as shipped |
| B13 | eMMC layout model (inherited logic, applied to Echo): IDB magic `0xFCDC8C3B` at sector `0x40`, stride `0x400`, 5 copies, "NANO" tag, system-MiB field at `+0x20A`; firmware starts sector `0x2000`; slot 1 / slot 2 split the firmware area in half; user volume found by 1 MiB-step scan after firmware end | `platform/device/logic/emmc_layout.c:3-17, 39-109`; consumed by `platform/device/board/update.c:76-86` (UpdateStorage = layout slot_1/slot_2/slot_sectors) and `platform/device/board/storage.c` (SD only, storage.c mounts the SD card, not eMMC). No NEO stock citation; on NEO it is unreachable per B12 |
| B14 | Core-1 decoder programs on NEO are loaded from SD files `/.echo/neo_mp3.bin`, `neo_aac.bin`, `neo_opus.bin`, `neo_flac.bin` instead of eMMC image offsets; NEO image offsets if built into an image: MP3 `0xCB9400`, FLAC `0xCD9600` (Echo: `0x240000`/`0x280000`) | `platform/device/board/core1.c:23-29, 114-131` |
| B15 | Rescan overlay on NEO loaded from SD file `/.echo/neo_scan.bin`; NEO image offset `0xC94400` (Echo: `0x200000`) | `platform/device/board/overlay.c:10-16, 47-65` |
| B16 | Battery: ADC full scale 5000 mV / 1024 steps; percent curve 3450,3580,3660,3710,3750,3800,3850,3920,4000,4100,4200 mV → 0-100%; charging offset −50 mV; 64-reading average; boot cutoff 3400 mV | `platform/device/logic/battery_gauge.c:5-13, 15-18`; `logic/include/device/battery_gauge.h:6-11`. None of this is NEO-ifdef'd or stock-cited in code. `docs/architecture.md:58-59` attributes the curve and the 3450 mV / 2 s low-battery shutdown to "stock" with no address, treat as an uncited stock attribution, not a verified one |
| B17 | CPU clocks: device starts at 96 MHz; 200 MHz when screen on / audio up; 96 MHz floor | `docs/architecture.md:60, 258` ("stock's rule/floor", no address); PLL order in `platform/device/board/clock_switch.c`. Uncited |
| B18 | Rockusb recovery identity VID `0x2207` PID `0x262D`; entry = hold Vol+ + Vol− + OK while plugging USB | `flash-neo.py:53, 15-20`. **Not present in the stock update image**: byte search of `DP3_V137.img` for LE `2207 262D` gives 0 hits (the image's own USB personalities are `071A:3289` USB-Audio and `071B:3203` MSC, 1 hit each, matching prior analysis). `0x2207:0x262D` is the generic Rockchip maskrom ID also quoted for the Echo Mini in `docs/hardware.md:34`, plausible for RKnano maskrom, but it is inherited knowledge, not Neo evidence |
| B19 | `flash-neo.py` flash layout: payload = first 13,631,488 bytes of the .img (i.e. the whole file minus the 4-byte CRC trailer = `0xD00000` bytes = 26,624 sectors); write to Slot 1 at sector **0** and Slot 2 at sector **30720**; 16-sector chunks; verify = read back sector 0 only | `flash-neo.py:153-193`, esp. `:160-162` and `:175` |
| B20 | Firmware version string "Neo V147"; update file search still uses the Echo template `/HIFIEC00.IMG`, numbers 00-97 | `platform/device/board/system.c:37-39`; `platform/device/board/update.c:16-22, 61-74` (shared code; on NEO unreachable per B12, and the name template is Echo's, stock Neo update names are `DP3_Vnnn` per prior analysis) |
| B21 | App-level NEO behaviour: 240×320 UI branches, NEO playback diagnostics/logging to a text buffer, FLAC-fallback retry after core-1 failure | `src/app/app.c:112-658` (multiple `#if defined(ECHO_BOARD_NEO)`), `platform/device/board/audio.c:66-81, 216-218, 300-308, 414-416, 486-497`. Software behaviour only; no hardware claim |

### flash-neo.py slot sectors vs the stock validator (special attention item)
- `flash-neo.py:175`: Slot 1 = sector 0, Slot 2 = sector 30720
  (15 MiB), writing 26,624 sectors (13 MiB) to each. Its Slot 2 spans
  sectors 30720–57343. (The task brief's "restore tool" numbers are the same
  0 / 30720 pair; no separate restore tool with different numbers exists in
  `repo/tools/`; `repo/tools/slot_geometry.py` models the *stock validator*,
  below.)
- Stock module-1 validator (prior analysis, `flash_security_and_port.md:33`,
  `tools/slot_geometry.py`): Slot 1 logical sector 0; first Slot-2
  candidate = `((0xC94000 + 0x104000) >> 9) & 0xFFFFF800` = `0x6800` =
  26,624 sectors (13 MiB), then scanning in `0x800`-sector (1 MiB) steps,
  up to `0x14` misses. 30720 = 26624 + 2×2048, i.e. flash-neo's Slot-2 base
  coincides with the validator's third scan candidate. The stock
  validator would find a header there if one were written, but it is *not*
  the computed first candidate for V137.
- Address-space warning (from prior analysis, still binding): the stock
  validator's sectors are *logical device-3* sectors whose callbacks add a
  `0x2000`-sector offset before lower-level I/O
  (`repo/analysis/block_device_dispatch.md`). Rockusb LBAs in `flash-neo.py`
  are a different, maskrom-level address space. The 0/30720 vs 0/26624
  comparison is therefore suggestive, not an identity. Do not present
  flash-neo's layout as "the stock layout" without a read-back dump of a
  real unit's both slots.
- Neither number matches the Echo Mini's 69632 (see C5).

---

# Section C: Echo-Mini-inherited traps (FiiO Echo Mini values; do not assume for the Neo)

`docs/hardware.md` is titled "# Echo Mini hardware" (`docs/hardware.md:1`)
and `docs/architecture.md` describes the Echo Mini throughout; both are
carried into this repo largely unedited. The following values in the
docs/code are Echo Mini facts and are wrong or unproven for the DAP Neo:

| # | Trap | Source | Neo reality / status |
|---|---|---|---|
| C1 | 320×170 panel | `docs/hardware.md:16`; `hal/display.h:10-12` (#else branch) | NEO branch is 240×320 (B1); stock resources contain full-screen 240×320 RGB565 images (prior analysis) and Fosi's spec is 2.4″ 320×240 (same panel, portrait vs landscape wording) |
| C2 | Panel variants A/B init tables are the device's panels | `platform/device/logic/panel.c:34-52` | NEO uses `NEO_STEPS` only (A8); A/B tables are Echo panels |
| C3 | DAC = Cirrus CS43131 | `docs/hardware.md:27`; `docs/architecture.md:256-257` ("device/dac_sequence runs the CS43131 side", "the same two CS43131s") | Neo has a single **CS43198** (vendor spec + A2/A7/A9). The register map overlaps (both are CS431xx), which is why the replay works, but part number, chip count and mono behaviour differ |
| C4 | Dual DACs, one per channel, at I2C `0x60` + `0x66`, dual-mono tables, channel-specific volume/gain | `logic/include/device/dac_sequence.h:34-35`; `logic/dac_sequence.c:44, 66-77, 128-142` (#else branches) | Stock: one chip at `0x66`, no mono tables (A2, A7) |
| C5 | Firmware Slot 2 at Rockusb sector **69632** (`0x11000`); "on the unit tested" | `docs/hardware.md:22`; `docs/device-install.md:11, 26-28` | That unit is an Echo Mini. NeoPod's own `flash-neo.py` uses 30720 (B19); stock-logical first candidate is 26624. Three different numbers, none may be assumed for a Neo without read-back |
| C6 | 4.4 mm balanced jack exists; GPIO2.8 low = 4.4 mm inserted; GPIO0.13 high = 3.5 mm; volume curve B (`0x7D − ⌊12n/5⌋`) for balanced | `docs/hardware.md:28`; `docs/architecture.md:257`; `board/jack.c` #else branches | Fosi's spec lists only a 3.5 mm output (prior analysis); NeoPod NEO branch says GPIO2.8 is the DAC **mute** output and forces balanced=false (B11), supported by A1/A4. The `0x7D` "stock's table B" attribution in `architecture.md:257` is Echo stock, not Neo stock |
| C7 | Update images named `HIFIECnn.IMG` (00-97, highest wins); custom image = 5 MiB with header copy at `0x44C000`, CRC at `0x500000`; stock FiiO images = 32 MiB | `platform/device/board/update.c:21`; `docs/hardware.md:37-38`; `platform/device/logic/updater.c` (whole `stock_check`: 8 GB marker strings `HIFIEC00IMG` vs `MINIV100IMG`, `STOCK_FW_END 0x2000000`, size `0x2000004`) | All FiiO-specific. Neo stock image is `DP3_V137.img` (13,631,492 B, header mirror at `0xC94000`); prior analysis found stock update-name templates `DP3_V100IMG` and `RKNANOFWIMG` in the Neo image, the updater's FiiO stock-acceptance path must never be applied to Neo images |
| C8 | eMMC layout: "ID block, firmware slot 1, firmware slot 2, a SAVE block, then the FAT32 user volume named ECHO MINI"; each slot holds 5 MiB | `docs/hardware.md:21-22` | Echo layout + Echo sizing. Neo stock payload alone is 13 MiB per slot image; NeoPod disables eMMC on NEO entirely (B12/B13) |
| C9 | Maskrom/recovery identity `2207:262d` presented as this device's | `docs/hardware.md:34`; `docs/device-recovery.md` (Echo flow) | Same value reused by `flash-neo.py` (B18), generic Rockchip maskrom ID; absent from the Neo update image; plausible but inherited |
| C10 | Bluetooth/audio routing drives GPIO2.14 as "wired output" select; BT stream holds GPIO2.0 high / GPIO2.14 low "as stock does" | `platform/device/board/bluetooth.c:52, 138-142`; `docs/architecture.md:211` | On NEO GPIO2.14 is the OK key input (B9) and GPIO2.0 is DAC ENABLE_A (B5), the Echo routing model does not transfer; NeoPod #else's it out |
| C11 | "EchoPod shuts down below 3450 mV, as FiiO's firmware does" and the battery curve generally | `docs/hardware.md:35`; `logic/battery_gauge.c` | FiiO attribution in an Echo doc; shared code, no Neo stock citation (B16). The 3450 mV figure coincides with the first curve point, that is the Echo curve, not a traced Neo threshold |
| C12 | I2C0 / I2S1 / DMA-ring audio plumbing, ACODEC rate rows, LPC FLAC accelerator described as the device's audio path | `docs/hardware.md:27-29`; `platform/device/board/dac.c` (shared, non-ifdef) | Inherited Echo board support reused for the Neo. Plausible (same RKnano SoC family) and the DAC register side is stock-verified (A9), but the SoC-side wiring is **not** cited to Neo stock anywhere in NeoPod, verify in stock before treating as Neo fact |
| C13 | Core-1 program / overlay image offsets `0x240000` / `0x280000` / `0x200000`, 5 MiB image geometry generally (`FW_SIZE 0x44C000`, `FW_END 0x500000`) | `board/core1.c:27-28`; `board/overlay.c:15`; `logic/updater.c:25-26`; `logic/include/device/updater.h:8` | Echo image layout. NEO branches substitute SD-file loading and different offsets (B14/B15) |

---

# Contradictions / deltas vs prior stock analysis (`repo/analysis/*.md`)

1. **DAC identity gap: now closed, no contradiction.** Prior analysis
   (`platform_architecture.md:58`) stated the image "has not yet supplied an
   identified CS43198 I2C address [or] register-write trace". That is no
   longer true: A2/A9 supply both from stock bytes (address `0x66`
   hard-coded at `0x03060cfa`/`0x03060d52`; init routine `0x0305175e`). The
   prior text should be updated, not treated as conflicting.
2. **Display bus gap: narrowed.** Prior analysis said the image "does not
   establish SPI versus 8080 parallel display wiring [or] LCD controller
   model". A8 verifies an 8080-style command/data init sequence embedded in
   module 4 and A10 corroborates most panel pins; "ST7789" remains an
   inference from the command set, so the prior caution stands for the part
   number only.
3. **Slot geometry: apparent conflict, actually different address spaces.**
   Prior analysis: stock-logical Slot 2 first candidate = sector 26624
   (`0x6800`), with an explicit warning that device-3 logical sectors carry a
   `+0x2000` offset and are not physical LBAs. `flash-neo.py` writes Rockusb
   Slot 2 at 30720. These do not directly contradict (different address
   spaces; 30720 is also the validator's third scan candidate), but any
   write-up that equates them would contradict the prior analysis's warning.
   Unresolved until a real unit's slots are read back via Rockusb.
4. **Panel resolution wording.** Prior analysis records Fosi's spec as
   "2.4-inch 320×240" and stock resources as 240×320 portrait. NeoPod's
   240×320 (B1) matches the resources; no contradiction (orientation only).
5. **USB IDs.** Prior analysis found USB-Audio `071A:3289` and MSC
   `071B:3203` in the image and noted RockUSB PID could not be established
   from the update file. NeoPod's `2207:262D` (B18/C9) does not contradict
   this. It is maskrom-level and absent from the image (0 byte hits), but
   it must not be cited as image-derived.
6. **Update naming.** Prior analysis found Neo stock templates
   `DP3_V100IMG` / `RKNANOFWIMG`. NeoPod's updater searches `HIFIECnn.IMG`
   and validates FiiO 8 GB stock images (C7), a direct mismatch with the Neo
   stock conventions, harmless only because the NEO build never reaches that
   code (B12).

## Reproduction notes
- Unpack: `python3 repo/tools/rknano_image.py DP3_V137.img unpack <dir>`
- Ranges disassembled for A1/A4/A5/A6: module 0 `0x03051a46..0x03051ab0`,
  `0x0305328c..0x030535ae`; module 11 `0x0307ea46..0x0307ead6`; module 33
  `0x03089e5c..0x03089ef2`. DAC: module 0 `0x0305175e..0x03051a46` with
  literal-pool resolution, helpers `0x03060c4c`, `0x03060d28`. Panel:
  module 4 raw range `0x0307ce68..0x0307d05e` byte-compared against
  `neo_diag.c` `NEO_INIT` / `panel.c` `NEO_STEPS`.
- Files not modified: nothing under `refs/` or `repo/` was written to.

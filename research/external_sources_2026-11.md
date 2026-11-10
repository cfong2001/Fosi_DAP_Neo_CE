# External sources, second pass

Survey date 2026-11-08. The first survey (`community_landscape.md`,
`patch_technique_and_sdk.md`, `neopod_echopod.md`) is dated 2026-10-31,
and a lot happened in the week after it. I went looking for public SDKs,
datasheets, manuals and sibling projects that give CE something it does
not already have, then checked the main finding against the stock image.
Nothing was flashed or built for this pass.

Labels follow the project's evidence order. Proven means checked this pass
against the stock image or a primary source. Likely means supported by
someone else's report or by strong inference. Open means not established.

## Outcome (added after the work was done)

The list below was worked through in order of ratio on 2026-11-08. What
each item became:

| Rank | Work | Result |
|---|---|---|
| 1 | DAC filter build option | Done, #73: `--dac-filter`, one byte, builder menu |
| 2 | Cite the TRM | Done, #74: `analysis/rknanod_trm.md` |
| 3 | Bluetooth UART evidence | Done, #75: proven from stock code, not just NeoPod: UART1, 115200, divisor 13 |
| 4 | Bluetooth that stays selected | Done, #77. The cause was not the boot path guessed in section 4: stock switches Bluetooth off after 5 minutes without a connection and saves it as Off. `--bt-auto-off 10min|never` |
| 5 | Accelerator models in the harness | Not done. Bigger than scored: the harness is FLAC-specific, the APE filter model is unverified, and APE test files need an encoder |
| 6 | Pause on unplug | No patch needed, #76: stock already reacts to unplug (flag `0x2B`, command `0xE6`); a device test would confirm it pauses |
| 7 | EQ preset curves | Done as AutoEQ and custom curves, #78. Easier than scored once the EQ was decoded (31 bands, ±12 dB), and it exposed a stock bug: three presets played another preset's curve or none |
| 8 | DAC filter as a menu item | Not done: still needs a free settings item |
| 9 to 11 | M3U diff, Vorbis on the FFT, scrobbler log | Not done (ratio under 1) |

## How the scores work

Each candidate gets two scores from 1 to 5, and the ratio of the two.
These are my estimates from reading the sources and the CE code, not
measurements. The time estimates assume someone who already knows the
framework.

Difficulty:

1. A data patch at a site that is already pinned. Under a day.
2. A small piece of RE, then a data patch. One to three days.
3. New cave code or new harness code at a known hook. About a week.
4. RE across several modules, or a binary diff of a whole firmware, plus
   code. Two to four weeks.
5. Large unknowns, or it cannot finish without hardware.

Reward:

1. Documentation or bookkeeping. No user sees it.
2. Makes later work faster or more accurate.
3. A user-visible change that is small or subtle, or it closes one open
   gate.
4. A feature users have asked for, or it unblocks a shipped option.
5. Changes what CE can do in a way most owners would notice.

The ratio is reward divided by difficulty. Anything at 1.0 or above earns
its keep. Anything well under 1.0 needs a reason beyond the score.

## The ranked list

| Rank | Work | Difficulty | Reward | Ratio | Blocked by |
|---|---|:---:|:---:|:---:|---|
| 1 | DAC filter as a build option (one byte) | 1 | 3 | 3.0 | Nothing |
| 2 | Get the RKNanoD TRM, cite it in `analysis/` | 1 | 2 | 2.0 | Getting a copy |
| 3 | Record NeoPod's Bluetooth UART evidence | 1 | 1 | 1.0 | Nothing |
| 4 | Bluetooth output that stays selected after a power cycle | 3 | 3 | 1.0 | RE of the boot path |
| 5 | Port newfw's accelerator models into the harness | 3 | 3 | 1.0 | Nothing |
| 6 | Pause on headphone unplug | 3 | 3 | 1.0 | Checking whether stock already does it |
| 7 | Replace stock EQ preset curves by data patch | 4 | 4 | 1.0 | The module 35 coefficient format |
| 8 | DAC filter as a settings menu item | 4 | 4 | 1.0 | A free settings item, the same gap that stalls battery profiles |
| 9 | Diff Echo Nano V1.7.0 against V2.0.0 for the vendor's M3U | 4 | 3 | 0.75 | Both images, time |
| 10 | Move the Vorbis IMDCT onto the HIFIACC FFT | 4 | 2 | 0.5 | Fidelity risk |
| 11 | Scrobbler log | 4 | 1 | 0.25 | File writes from a stock hook |

Rank 1 is the clear winner. Ranks 3 through 8 sit at the same ratio, so
choose among them by what unblocks other work: the harness models (5)
feed the clock-table hardware gate, and the free settings item (8) would
also unblock battery profiles. I would skip 10 and 11 for now.

---

## 1. The DAC has five filters and stock only ever uses one

Difficulty 1 as a build option, 4 as a menu item. Reward 3 and 4.

Sources are the Cirrus Logic CS43198 datasheet DS1156F2 (December 2022,
sections 4.7, 5.8 and 7.5.2) and the Linux `cs43130` driver (GPL-2.0,
which supports the CS43198 by chip ID). echo-mini-newfw's `docs/CS43131.md`
reaches the same reading for the sister chip.

CE already knew that stock writes DAC register `0x090000` with one of
five values, picked by the settings byte at `+0x2E3` (base `0x030232A0`).
That is in `analysis/neopod_xref.md` A9. What the values meant was never
written down.

The datasheet settles it (proven). In register `0x090000`, bit 7 picks
slow or fast roll-off, bit 6 picks linear phase or low latency, bit 5
turns on NOS emulation, bit 1 is the DC high-pass filter and bit 0 is
de-emphasis. The chip has exactly five PCM filter combinations, and
stock's five values are those five.

| Mode | Value | Filter | Group delay at single speed |
|---|---|---|---|
| 0 | `0x02` | Fast roll-off, low latency (minimum phase) | 6.3/Fs |
| 1 | `0x42` | Fast roll-off, linear phase | 39.5/Fs |
| 2 | `0x82` | Slow roll-off, low latency | datasheet Table 3-7 |
| 3 | `0xC2` | Slow roll-off, linear phase | datasheet Table 3-7 |
| 4 | `0x22` | NOS emulation | n/a |

All five keep the high-pass filter on and de-emphasis off. Mode 0 is the
chip's power-on default.

Then the stock image (proven, this pass). The code at exec
`0x0305180E..0x03051866` in module 0 reads `+0x2E3` five times and writes
one value per mode. The mode-0 write is `movs r1, #2` at `0x03051814`
(bytes `02 21`). A scan of the whole image for `.W` byte loads and stores
at offset `#0x2E3` finds those five loads and no store. The English
settings strings list Channel Balance, EQ Settings with six presets, Gain
Setting, screen, power and sleep options, and UAC Power. There is no
filter string. So the selector is very likely dead code that Fosi never
wired to a menu, and every unit plays through mode 0 (likely, since a
writer through another base would not show up in that scan).

### The build option (difficulty 1)

Change the `0x02` byte at `0x03051814` to `0x42`, `0x82`, `0xC2` or
`0x22`, and offer it in the configurator. It is one byte at a site that
is already pinned, and it writes a value stock's own code already writes
in another branch. The DAC init runs per playback session, so there is no
mid-track switch and no pop sequence to worry about. The one thing to
test is the configurator wiring and the verify suite, which is why it is
a day and not an hour.

It is a 3 and not higher for a reason. The audible differences between
these filters are small and argued over, and the only objective
difference is group delay. Offer it as "the chip's five filter
choices", not as better sound.

### The menu item (difficulty 4)

Adding a "Digital filter" item to the settings menu needs a free settings
item and string, and CE has not proven one exists. That gap already
blocks battery profiles, where the only candidate ID turned out to be
the stock "20%" brightness label. There is a second problem too.
`+0x2E3` sits outside the verbatim block `+0x1C7..+0x2D5`, so according to
`saveinfo_lock.md` section 1.6 it only survives a reboot if module 1's
load pass restores it by name. Nobody has checked that. If it doesn't,
the fix is one more restore in the load pass, which the document already
describes.

Two cautions from the datasheet for anyone who goes further. Switching
into or out of NOS while playing should follow the pop-free sequence in
section 5.8 (soft-ramp mute, mute both channels, wait 150 ms, write,
restore, unmute). And bit 2, wideband flatness, is for 192 kHz only and
can only change with the headphone amplifier powered down. Leave it
alone.

## 2. The chip's reference manual is public

Difficulty 1, reward 2.

"Rockchip RKNanoD Technical Reference Manual, Revision 1.0, May 2015"
runs to 28 chapters. Firefly, a Rockchip board partner, hosted it for its
Fireduino board at `t-firefly.com/images/0/0b/Fireduino_MCU_TRM.pdf`, and
rockchip.fr indexes it. It is Rockchip's copyright, so cite it and don't
commit the PDF.

Neither host would serve the file to this environment. Firefly's link now
redirects to a storefront, and rockchip.fr reset the connection. What I
know of the contents comes from the indexed text, which includes the
full table of contents.

No CE document cites a TRM today. `analysis/platform_architecture.md`
points at "the Rockchip datasheet", and CE's register facts come from
disassembly, NeoPod and the leaked SDK. The chapters that matter for CE:

- Chapter 3, clock and reset unit, including PLL usage. This is the
  hardware behind the solver CE replicated in `clock_v1.md`.
- Chapter 5, power management, with power domains `PD_PMU`, `PD_LOGIC`
  and `PD_HIGH`. `PD_HIGH` holds core B, its RAM and the accelerators.
  Whether stock powers it down when paused is the natural next question
  after `power.md` found no idle WFI loop to patch.
- Chapter 12, embedded SRAM, which confirms CE's memory map (SYSRAM0
  320 KB at `0x03000000`, SYSRAM1 256 KB at `0x03050000`, HIGHRAM at
  `0x01000000` and `0x01020000`).
- Chapters 8 and 13, DMA and I2S, which name the decoder-side DMA
  registers the harness models.
- Chapter 17, SAR-ADC, the battery measurement path.
- Chapter 23, UART, an independent check on section 4 below.
- Chapters 26 to 28, the HIFIACC, SYNTH and Imdct36 accelerators. The
  TRM lists their functions but gives no register map. newfw fills that
  gap (section 3).

The work is getting a copy from outside this environment, recording its
SHA-256, and adding section references to the clock, power and platform
documents. That is cheap, and it makes every later register claim easier
to check.

## 3. The decode accelerators now have names, models and measured loads

Porting the models is difficulty 3, reward 3. Vorbis on the FFT is
difficulty 4, reward 2.

The source is berettavexee/echo-mini-newfw, MIT licensed, at version
0.102 (2026-11-07). It has three pieces worth having. `docs/HIFIACC.md`
and `docs/MP3ACC.md` give register maps rebuilt from Echo Mini stock and
checked on a device. `tools/emu_accel.c` and `emu_host.py` model the FLAC
LPC filter, the ALAC adaptive filter, the FFT, SYNTH and Imdct36. And the
README has a table of measured core-B load per format.

CE got partway there on its own. `patches/harness/milestone2.md` Finding
3 shows the Neo's stock FLAC module hands LPC reconstruction to "the
audio block" at `0x0106B000`, and the harness rebuilds those frames in
Python. newfw names it. It is HIFIACC at `0x01060000`, in the `PD_HIGH`
domain, fed by DMAC2 at `0x01070000`. Its block-length field is 13 bits,
so blocks over 8,191 samples cannot use it. The coefficient memory is
reversed, which CE's harness also found. ALAC coefficients live at
`0x01069000`. SYNTH and Imdct36 are the MP3 accelerators.

newfw's measured loads, on the same SoC with its own decoders and the
screen off, are FLAC 16/44.1 at 9 to 12 MHz of core B, MP3 at 20 to 25,
Vorbis at 29 to 36, AAC-LC at 23, ALAC 24/96 at 27 and Opus (libopus
1.5.2) at 50 to 55. CE's clock table v1 gives core B 288 MHz for
FLAC/ALAC/APE/DSD, 240 for Vorbis and 144 for MP3, AAC, WAV and Opus.

That gap is big, but don't read too much into it. These are different
decoders, and stock already uses at least the FLAC accelerator. What the
numbers do show is that v1 sits far above the chip's floor, which is the
right side to be on before anyone has a device. For Opus, CE's `opus72`
carries the same libopus 1.5.2, and newfw's 50 to 55 MHz matches the
donor figure CE already cites (at most 56 million instructions per second
in the worst case). That is a second, independent confirmation that the
144 MHz row fits.

### Porting the models (difficulty 3)

Bring the `emu_accel.c` models into `patches/harness/` (MIT, with
attribution) so the stock ALAC, APE and MP3 modules run under Unicorn.
The prize is an instruction count for APE, which is one of the two loads
`clock_v1.md` flag 3 calls unmeasured. It won't settle the gate.
Unicorn counts instructions, not cycles, and knows nothing about bus wait
states. DSD may not touch the accelerators at all, which would make it a
separate job. Still, it turns "unmeasured" into "estimated" before the
hardware run, and the models stay useful for every codec afterwards.

### Vorbis on the FFT (difficulty 4, I'd skip it)

newfw runs the Tremor IMDCT on HIFIACC's FFT. CE's full-precision
transplant does it on the CPU at 240 MHz. The FFT is fixed point with
undocumented internal precision, and fidelity is CE's best Vorbis result.
The only gain is battery life on one codec. If anyone tries it, the corpus
harness has to show every file still within 0.21 dB of its 16-bit
ceiling, or it goes.

## 4. NeoPod runs Bluetooth audio on the Neo

Recording the evidence is difficulty 1, reward 1. Bluetooth that stays
selected is difficulty 3, reward 3.

The source is danielNZ27/NeoPod-Fosi-DAP-Neo-Custom-Firmware, GPL-3.0.
Version 1.7.0 (2026-10-31) added Bluetooth audio and saved devices, and
1.8.2 shipped the next day. The code is in
`platform/device/board/bluetooth.c` and `platform/device/logic/bt_module.c`.

The first survey said NeoPod had dropped Bluetooth. That was true for a
day. NeoPod now drives the module on UART1 at `0x400B0000`, pins
GPIO2.16 and 2.17, 115200 8N1 with divisor 13, and module power on
GPIO2.7, with scan, connect, reconnect and stream commands. CE's
`modules_round2.md` section 3.4 still lists the baud rate as not
established. If NeoPod users confirm Bluetooth works, that is device
evidence (likely, not checked by CE). It also fits stock's own divisor
code at `0x0305134C`, which computes `0x16E360 / baud`, and
1,500,000 / 115,200 rounds to 13.

The more interesting item is a user request. On Audio Science Review on
2026-11-03, a DAP Neo owner asked Fosi to make Bluetooth output stay
selected after a power cycle. Stock keeps Bluetooth state at SAVEINFO
`+0x2D4`, inside the block that survives a reboot, so the setting is
probably saved and then ignored at boot. Finding where the boot path
drops it is a contained piece of RE next to CE's existing Bluetooth
shortcut, patch 0032.

NeoPod is GPL-3.0. Facts about the hardware and protocol are fine to use.
Its code is not, unless CE accepts the GPL.

## 5. FiiO shipped M3U in SDK-family stock firmware

Difficulty 4, reward 3.

FiiO's Snowsky Echo Mini V4.0.0 and Echo and Echo Nano V2.0.0 came out
between late October and 2026-11-05. The Nano V2.0.0 notes list M3U
playlists, a fix for wrong album sorting, and faster playback response.
These are stock firmwares from the same Rockchip SDK line as the Neo's.

This matters because CE's browser builder still disables its combined
M3U and lock-screen option "pending a tested playlist playback
lifecycle", and the vendor now has a stock-native one. The Nano is the
cheapest to study, because nanitecfw already mapped V1.7.0. Diffing
V1.7.0 against V2.0.0 should locate the parser and its hooks into the
browser and playback modules. From there, compare where FiiO enters and
leaves playlist mode with CE's exit hooks 0060 to 0062.

I scored it 4 because a whole-firmware diff with shifted addresses is
real work, and the payoff is a design to compare against, not code CE can
use. The binaries are proprietary, so facts only. As a side job, check
whether FiiO's album-sort fix touches sort code the Neo shares. CE has
already replaced that comparator, so this is probably moot, but it is
worth a look.

## 6. EQ

Replacing preset curves is difficulty 4, reward 4. A full parametric EQ
would be a 5.

BasilSkyWalk/echopod 0.11.0 and brnomt/ReChord (both GPL-3.0) now import
AutoEQ and Equalizer APO presets, with shelves, ten bands, preamp set from
the real cascade response, and a Thumb-2 biquad loop tuned for core B.
ReChord measured the load. Together they show a ten-band cascade fits on
this core, and that AutoEQ text is the format users show up with. If CE
ever needs its own kernel, Arm's CMSIS-DSP (Apache-2.0) has Cortex-M3
Q31 biquads.

One negative I checked. ReChord's `docs/re/dsp-hook-map.md` claims Echo
Mini stock does EQ on an external "GOODE" DSP loaded over SPI. The Neo
image has none of its markers (`GOODEF`, `WOOOOON`, `RockEQ` are all
absent), so it doesn't apply here, and CE's assumption that EQ runs on
the SoC stands.

The practical CE route is narrower than a new EQ. Stock already has six
presets (Pop, Jazz, Rock, Classical, Bass Boost, Heavy Metal). Module 35
is 51,252 bytes of fixed-point word pairs, which looks like coefficient
tables. Work out that format and CE can swap in better curves as a data
patch. The format is the hard part, which is why this is a 4.

## 7. Smaller items

Pause on headphone unplug, difficulty 3, reward 3. newfw 0.101 and RECHO
both do it, and the Neo's 3.5 mm sense pin is GPIO0.13 per
`neopod_xref.md` B11. I don't know whether Neo stock already pauses.
Check on a device or in the jack-poll code first. If it doesn't, this is
a producer-side cave of the nanitecfw kind.

Scrobbler log, difficulty 4, reward 1. EchoPod 0.11.0 writes Rockbox's
`/.scrobbler.log` when a computer connects. CE has avoided file writes
from stock hooks so far, and that is a good habit to keep.

Three new Echo Mini RE repos (`iamcheyan/echo-mini-firmware-research`,
`IhitplayzYT/OpenEchoMini`, `bRuttaZz/better-pod`) appeared between
2026-11-01 and 11-03, all unlicensed. They hold static notes and early
decompilation, and nothing CE lacks.

`hjjhhd/rp2040_cs43198`, also unlicensed, is a MicroPython CS43198
driver. It is a third init sequence to compare against stock's 73-entry
table if a register is ever in doubt, though the datasheet is the better
source.

Fosi's latest DAP Neo firmware is still V1.3.7 (owner report on ASR,
2026-10-31), so CE's pinned base is current.

## 8. Proprietary and leaked material

The request behind this pass mentioned leaked sources. Two exist for this
chip, and the policy in `patch_technique_and_sdk.md` section 3 covers
both. Read them as a dictionary. Never copy from them or commit them.

- `EACHAN-YIN/RKNanoD_MP3_V1.3_20161102` and its `xinghuaman` mirror,
  the MP3 SDK CE already uses.
- `averyling82/wifi-bt-audio` (2016-12-14), new to CE. It is a Rockchip
  Wi-Fi and Bluetooth audio SDK for the same chip, and every file says
  "Copyright (c) Fuzhou Rockchip Electronics Co., Ltd, All rights
  reserved". It has accelerator driver source (`Cpu/NanoD/lib/hifi.c`,
  `hifi_alac.c`, `hifi_ape.c`), prebuilt core-B decoder images, and two
  eval-board schematics (`rknanod_sdk_main_v01_20150126.pdf`,
  `rknanod_sdk_main_v22_20150908_n.pdf`). It is good for confirming a
  register meaning newfw leaves open, and that's all.

The public sources in this pass (the datasheet, the TRM and newfw's MIT
documentation) now cover most of what the leaked trees were opened for.
Cite those instead where possible, so CE's documents don't lean on
material nobody can share.

## Sources

- Cirrus Logic, CS43198 datasheet DS1156F2, December 2022:
  https://statics.cirrus.com/pubs/proDatasheet/CS43198_DS1156F2.pdf
- Linux `sound/soc/codecs/cs43130.c` and `cs43130.h` (GPL-2.0):
  https://github.com/torvalds/linux/blob/master/sound/soc/codecs/cs43130.c
- Rockchip RKNanoD TRM V1.0, May 2015:
  https://www.t-firefly.com/images/0/0b/Fireduino_MCU_TRM.pdf (index at
  https://rockchip.fr/)
- berettavexee/echo-mini-newfw (MIT), version 0.102, 2026-11-07:
  https://github.com/berettavexee/echo-mini-newfw
- danielNZ27/NeoPod-Fosi-DAP-Neo-Custom-Firmware (GPL-3.0), v1.8.2:
  https://github.com/danielNZ27/NeoPod-Fosi-DAP-Neo-Custom-Firmware
- BasilSkyWalk/echopod (GPL-3.0), 0.11.0: https://github.com/BasilSkyWalk/echopod
- brnomt/ReChord (GPL-3.0): https://github.com/brnomt/ReChord
- FiiO Japan, Echo Nano FW V2.0.0 notes, 2026-11-05:
  https://support.fiio.jp/hc/ja/articles/63997056288537
- FiiO, Echo Mini V4.0.0 announcement: http://www.fiio.com/newsinfo/1150611.html
- Audio Science Review, "New Fosi Neo DAP" thread:
  https://www.audiosciencereview.com/forum/index.php?threads/new-fosi-neo-dap.74204/
- Arm CMSIS-DSP (Apache-2.0): https://github.com/ARM-software/CMSIS-DSP

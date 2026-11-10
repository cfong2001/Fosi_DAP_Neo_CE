# Battery life and functional changes: V137 engineering targets

Firmware: `DP3_V137.img` (SHA-256 `fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`).

## What V137 actually changed

The published October 2026 V137 release notes list a switch to disable the lock screen, a folder-repeat fix, a track-count display, and display fixes. They **do not claim better battery endurance**. Source: [October 24 release announcement](https://www.reddit.com/r/DigitalAudioPlayer/comments/1xe7cal/a_firmware_update_for_the_fosi_dap_neo_is_now/), pointing to [Fosi support](https://support.fosiaudio.com/products/dapneo). A before/after power comparison requires a prior firmware image and current measurements; the uploaded V137 image by itself cannot establish energy improvements.

Fosi advertises up to 12 hours, not an assured runtime under every format or usage mode. See [Fosi product specification](https://fosiaudio.com/products/dap-neo-mp3-player).

## Verified firmware anchors

| Address / source | Original binary evidence | Interpretation and limit |
| --- | --- | --- |
| English language section, IDs `188..195` | `Auto Screen Off` followed by `10 seconds`, `20 seconds`, `30 seconds`, `1 minute`, `5 minutes`, `10 minutes`, `Always On` | Existing UI choices, **not** the LCD/backlight driver |
| English IDs `196..201` | `Screen Brightness` and `20%`, `40%`, `60%`, `80%`, `100%` | Existing display-brightness options |
| English IDs `202..214` | `Auto Power Off` and `Sleep Timer`, with multiple time values | Existing shutoff controls; their event/timer handlers need xrefs |
| English IDs `167..169`, `181..183` | Bluetooth switch and low/high gain choices | Existing mode settings, physical radio/gain power deltas unknown |
| System module 0, `0x03055b70` | `bf30 4770` (`WFI; BX LR`) | CPU interrupt-wait primitive is present |
| System module 0, `0x030564e0` | `BL 0x03055b70`; caller checks a byte after the wait and decrements a timeout | **This WFI call is in a peripheral transfer wait**, not proof that the RTOS idle task sleeps |
| System module 0, `0x03067c1c` | `SUB SP,#8`, `ADR` to `system powerdown!` and calls into subsystem cleanup | A concrete shutdown path to trace, not a verified low-leakage power state |
| System module 0, `0x03067c7e`-`0x03067c98` | Calls into `0x030526f8`, `0x03056098`, `0x030560d2` with specific pin parameters | GPIO configuration/control during shutdown; physical pin map unresolved |
| System module 0, `0x03067d12`-`0x03067d1a` | Calls `0x030536a6(0,0)`, then an infinite branch | Final system power-down handoff; if the power-control action fails the CPU spins, but battery-drain implications are unmeasured |

Code addresses are system-core Thumb execution addresses, not file offsets. `0x03055b70` is backed by input file `0x2f21c`, `0x030564e0` by `0x2fb8c`, `0x03067c1c` by `0x412c8`, and `0x03067d1a` by `0x413c6`.

The English strings come from the language section, index 2, as decoded by `tools/rknano_image.py`. Shared stock SDK strings still require menu/state-handler xrefs before they can be attributed to active hardware.

## Power opportunities, ordered by risk and likely payoff

1. Display/backlight policy. Trace the code handling IDs 188 and 196 to the backlight PWM/GPIO or LCD power control. Reduce brightness and backlight-on duration; make sure the backlight really turns off, rather than merely drawing black. Verify screen wake, button input, and playback continuity. The added lock-screen disable option does not inherently turn off the backlight.
2. Quiescent audio and wireless. Trace playback, pause, headphone detection, USB DAC, Bluetooth, and power-off transitions. Confirm that a paused or stopped player actually releases the CS43198 playback path and disables unused radio/USB functions. Avoid muting samples while keeping the DAC and clocks active. Restore clocks in the required sequence before unmuting.
3. MCU idle and clock gates. The TRM (chapter 5, summarised in [rknanod_trm.md](rknanod_trm.md)) puts the decoder core, HIFIACC and both HIGHRAM banks in `PD_HIGH`, which only software powers down (`PMU_PWRDN_CON` bit 1), and lets each 32 KB SRAM sub-block's clock be gated. Whether stock powers `PD_HIGH` down when paused is the first thing to check. Identify RTOS scheduler idle, system tick, timer interrupt, CRU clock gates, per-core active flags and PMU domains. One known `WFI` wrapper is used in a peripheral wait; do not patch it indiscriminately. Only gate peripheral clocks after quiescence and interrupt/wake source inspection.
4. Storage burst sizing and UI work. Profile microSD wake/idle cycles, library scanning, metadata polling, album-art redraws and UI periodic timers. Batch reads and avoid unnecessary redraws without increasing underruns or delaying commands. Measure rather than assume that larger read bursts save power.
5. Frequency scheduling and decoder occupancy. Compare MP3, FLAC, high-rate PCM, and DSD loads. The RKNanoD has separate cores and dedicated audio hardware; the goal is to complete decode bursts at safe clocks and sleep between them, not blindly underclock the CPU and cause dropouts.

The RKNanoD datasheet explicitly supports separate software-controlled power domains, individually gated clocks and 64 KiB SRAM bank clock gating: [RKNanoD Rev. 1.8](https://rockchip.fr/RKNanoD%20datasheet%20V1.8.pdf). These capabilities belong to the *SoC family*; the exact board power rails and pin connections are unproven.

The DAC also offers adaptive Class-H output supply selection (`ADPT_PWR=111`), which automatically lowers the analog rail when the audio signal allows it. Verify the stock value and physical output stage before proposing a change. This mode is not supported for Direct DSD; do not enable it globally.

The CS43198 datasheet describes `PDN_HP`, `PDN_xSP`, `PDN_PLL` and other controlled shutdowns. The order matters: power down the headphone path and await completion before disabling serial ports, and do not disable a live clock source. The board-specific I2C bus/voltage sequencer has not been found. See [CS43198 datasheet](https://statics.cirrus.com/pubs/proDatasheet/CS43198_DS1156F2.pdf).

## Measurements needed before patching

Record supply current and listening runtime on stock V137 under matching conditions. At minimum: device on/paused screen bright; on/paused screen off; wired MP3 screen off; wired FLAC screen off; Bluetooth playback screen off; and nominally powered off. Hold volume, headphone impedance, card, file set, battery state, and ambient conditions constant. Gather average and peak current and, if accessible, CPU idle/time-in-state counters. An external battery-path current measurement is necessary to quantify real battery savings; USB charge-port current is not equivalent.

Each candidate patch should have a precise original-byte precondition and a rollback/recovery path. Measure current, audio underruns, pop/noise, reconnect behavior, wake latency, RTC operation and battery charge state. No power-register edits or device-side experiments have been performed.

## Functionality candidates

The V137 release itself demonstrates the feasibility of changing UI policy, folder-repeat behavior and playback counters. Other sensible firmware targets include lock-screen track metadata, direct Bluetooth toggling, customizable wheel/button actions, improved alphabetic browse and persistent resume, M3U import, and gapless transitions. None of these is demonstrated by the resource strings alone. Gapless and playlist import require deeper state-machine/filesystem changes; Bluetooth codec expansion also requires proof of radio firmware, capabilities and licensing.

The short-term project goal is to identify the actual LCD/backlight control path and the DAC power-state transition before writing binary patches. This is more likely to deliver a measurable gain than modifying the update metadata or guessing CPU clock registers.

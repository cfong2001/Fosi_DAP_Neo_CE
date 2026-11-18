# Power: wheel timer and power profiles

The wheel timer patch ships in both images (Standard and Minimal) as patch
0050 in [`../framework/patches/`](../framework/patches/): the wheel sampling
period goes from 400 to 1000 µs (2,500 to 1,000 wakes per second). Keys use a
separate SysTick path and are unaffected; worst-case wheel-step latency rises
by about 1.2 ms. Battery-life gains have not been measured.

The Standard image adds a Power Profile item to System Settings
([`profiles/`](profiles/README.md)). Its three options set brightness, auto
screen off and auto power off together.

- [`power.md`](power.md): the wheel timer patch, the idle analysis and the first battery-profile design.
- [`build/`](build/): that first design's build (apply routine, clock caps, selector caves). It was never stacked. It had no proven settings item, it lowered decoder clocks below Rockchip's figures, and its timer and clock changes had no boot path. `profiles/` replaces it.

## Unintended restart after shutdown

If the board stays powered after the firmware releases the power-hold GPIO,
the stock shutdown code waits for the Power button to be released, then
accepts eleven back-to-back high reads as a new press. A short pulse can pass
that check and trigger a software reset.

Pass `--debounce-power-on` to [`tools/prepare_flash.py`](../../tools/prepare_flash.py)
to build a Standard or Minimal CE candidate with a fix. It polls every 10 ms,
requires a release followed by eleven consecutive pressed samples, and
restarts the count on any release. The patch applies to the firmware's
post-shutdown polling loop. A cold boot after the board has lost power follows
the device's hardware and bootloader behavior.

The emulation test reproduces a restart on stock code with a brief pulse and
verifies that the patched code ignores it and restarts after a sustained press.
Physical-device verification is pending. Use the matching recovery source
and date described in the [flash review](../../release/FLASH_REVIEW.md).

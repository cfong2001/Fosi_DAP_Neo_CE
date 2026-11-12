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

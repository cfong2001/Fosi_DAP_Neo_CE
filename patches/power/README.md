# Power: wheel timer and battery profiles

The wheel timer patch ships in both images (Standard and Minimal) as patch
0050 in [`../framework/patches/`](../framework/patches/): the wheel sampling
period goes from 400 to 1000 µs (2,500 to 1,000 wakes per second). Keys use a
separate SysTick path and are unaffected; worst-case wheel-step latency rises
by about 1.2 ms. Battery-life gains have not been measured.

Battery profiles are built ([`build/`](build/)) but not shipped: no free
settings item has been proven for the selector.

- [`power.md`](power.md): the wheel timer patch, the idle analysis and the battery profiles design.

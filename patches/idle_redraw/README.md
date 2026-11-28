# Idle repaint gate

While the Now Playing controls are shown, every change of the displayed
elapsed second ran three repaints. The 0x40 segment drew the time. Then it
posted 0x4D, which redrew the progress bar, and the bar posted 0x43, which
redrew the transport row and the play-mode indicator. The flush then sent
rows 5 to 307 to the panel. The bar moves only every total/147 seconds and the
transport row changes only with its state, so most of those repaints wrote
the pixels already on screen. Under emulation the transport row was 530,000
of the 675,000 instructions in an idle second.

| Patch | Site | Change |
|---|---|---|
| 0350 | `0x03052F90` (40 B, unreached stock code after 0276's table) | `fingerprint`: play state halfword, transport state A and B; `fp_store` |
| 0351 | `0x030645B6` (42 of 42 B, an unreached stock function) | `tick_gate`: fingerprint and mode checks |
| 0352 | `0x0305C9CE` (42 of 46 B, head of an unreached stock function) | `tick_gate`: bar position |
| 0353 | `0x0307F5BC` | The 0x40 segment's per-second post of 0x4D calls `tick_gate` |
| 0354 | `0x0307F696` | The 0x4D segment's second position store calls `fp_store` |

`tick_gate` posts 0x4D as before unless the bar position (the 0x4D segment's
own multiply and `0x03054D90` divide) equals the stored one and the
fingerprint equals the one stored with it. It always posts in seek preview
(halfword `0x030247EA` = 6, where the 0x4D segment rewrites the elapsed time)
and in the sub-track timebase (word `0x030239C4` = 1, a different formula).
The word `0x030247F4` was a second copy of the bar position that nothing
reads; it now holds the fingerprint. No other poster of 0x4D or 0x43 changes,
so full repaints, seeks, track changes, keys and the playback engine's own
posts draw exactly as before.

`idle_machine.py` runs the player's Service, Display and flush per 10 ms tick
on real module 0, 18 and 27 code. Only the sector driver, the interrupt mask,
the LCD row transfer and the artwork request are modelled. The block reader
runs for real, so its calls and sector reads are counted.
`test_idle_redraw.py` compares the framebuffer, the display context and the
modelled panel after every tick against the same image with 0350 to 0354
reverted, across 14 scenarios, and writes `idle_redraw_report.json`. The
store-window fields of the display context (+0x18..+0x23) hold the last
draw's rectangle and are excluded; the test checks that no pixel is stored
in a tick before the window setup has run in that tick.

```
python patches/idle_redraw/build_idle_redraw.py
python patches/idle_redraw/test_idle_redraw.py [release/DP3_V137_CE.img]
```

Not verified on hardware.

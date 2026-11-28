# Wheel acceleration in the file browser

Turning the wheel quickly now moves the browser highlight by more than
one row per step. Single, slow steps still move exactly one row.
Patches 0330 to 0333, in the Standard image only. Thresholds are
untuned on hardware.

## The stock path

The wheel decoder (module 0, `0x03061936`) counts steps. The key fetch
`0x03061B16` turns one pending step into one event word per Key
callback call, `0x40000200` or `0x40000400`, from `0x03061E78`. The
browser Key callback (module 31, `0x0307E5B8`) routes them through its
compare tree to `0x0307E6B0` and `0x0307E6DA`. In the browse mode
(`[0x03025928 + 8] == 0`) these call the step functions:

| Event | Call site | Step function | Moves |
|---|---|---|---|
| `0x40000200` | `0x0307E6D4` | `0x0307E474` | selection + 1 |
| `0x40000400` | `0x0307E6FA` | `0x0307E3BA` | selection - 1 |

Browser context `0x030228A8`: `+0x1CC` level, `+0x1CE + 2 x level`
top row, `+0x1EE` selection, `+0x1F0` previous selection,
`+0xC + 56 x level` entry count. A step that stays inside the seven
visible rows posts `0x144`, and the painter (`0x0307E8F2`) repaints the
previous and the new row. A step that crosses the edge shifts the
framebuffer one row (`0x030646A0`), moves the top row by one, reloads
the visible nodes (`0x0307D254`, a directory walk from the start of
the folder up to the top row), and posts `0x144`. Both ends clamp; the
list does not wrap. The other mode (`[0x03025928 + 8] != 0`) handles
the wheel inline and is unchanged.

## The change

Patches 0332 and 0333 replace the two call sites with calls into the
stub. The stub stamps each step with the 100 Hz OS clock
(`0x03023298`) and keeps a streak:

- A step less than 10 ticks (100 ms) after the previous one, in the
  same direction, extends the streak, up to 12.
- Any other step resets it to 0.
- Rows per step are 1, 2, 4, 8 for streaks 0 to 3, 4 to 7, 8 to 11, 12.

A one-row step tail-calls the stock step function with nothing
changed. A larger step:

1. Puts the selection one row short of the target, clamped to the list.
2. If the target is outside the visible rows, sets the top row so that
   the stock edge scroll lands the target on the edge row.
3. Runs the stock step function for the last row. It does the one
   directory reload for the final window.
4. Clears the `0x144` it posted and posts `0x143`, the stock full-list
   repaint used on folder entry. The painter must not get both in one
   pass: it walks a single node pointer through its two-row pass and
   then its full pass.

At an end (selection already at the first or last row) a larger step
falls back to the stock step, so it clamps exactly as stock does.
Lists of two rows or fewer always take the stock step.

Crossing 500 entries now takes about 70 fast steps instead of 499.
Each accelerated step costs one reload and one seven-row repaint,
where stock spends one reload and one two-row repaint per row moved.

## Space

The code fills two dead module 0 functions:

| Home | Bytes | Stock content |
|---|---|---|
| `0x03052728`..`0x030527A0` | 112 code, 8 state | GPIO pull read/write accessors; their only stock callers were in `0x03052F40`, which patch 0276 replaced |
| `0x0305DDD8`..`0x0305DE20` | 72 code | an unreferenced lookup leaf |

A scan of every module of the stock and the Standard image finds no
branch, call or literal that reaches either range from outside it. No
file in the repository or in open PRs 42 to 45 names an address in
either range. The census pocket `0x0306D304` was offered for this
work but is not used: `tools/runtime_diagnostics.py` places its entry
there, and its test builds from the Standard image.

The 8-byte state (last step tick, streak and direction) lives in home
A. It relies on module 0's code segment being writable SRAM, as the
gapless gate's state already does.

## Tests

`python3 patches/wheel_accel/test_wheel_accel.py` runs the real Key
callback and painter of the Standard image under Unicorn against a
copy with the stock call sites restored. See its docstring for the
gates.

## Open on hardware

- The 100 ms threshold and four steps per level are guesses. Whether
  a hand spin produces steps faster than 10 per second, and whether a
  deliberate click rate stays below it, needs the device.
- The decoder keeps at most two pending steps; steps beyond that are
  dropped while the browser repaints. Acceleration does not change
  that.
- The music library lists (module 23) have their own wheel code and
  context and are not accelerated by this change.

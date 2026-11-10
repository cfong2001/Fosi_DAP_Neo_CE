# Portrait sampling and browser interference

The portrait-sampling change is integrated into the standalone theater
variant and the everything build.

The sampler now bounds each sampled row to the scaled artwork width and
starts at the renderer's centered horizontal inset, so the padding around a
portrait cover no longer feeds the average. It also skips sampling when the
recorded artwork width is zero or wider than the target. The regression in
`test_theater_lifecycle.py` renders a red 18-by-30 JPEG into a 16-by-16
target: the artwork span is 9 pixels and the derived dark background is
0x7000. The landscape, duplicate-row, sync, no-art and host-C cross-check
scenarios pass unchanged.

| | Before | Now |
|---|---|---|
| Standalone payload | 642 bytes, `26c9efab…` | 676 bytes, `96931a93…` |
| Hook patches 0100 to 0104 | unchanged | unchanged (the trampoline entry did not move) |
| Theater variant image (builder case k) | `6ad01b38…` | `523f57f1…` |
| Everything build | 642 bytes at 0x0307C376 | 676 bytes at 0x0307C354, `17a558dd…` |

The everything build had 4 tail bytes to spare until its playlist hooks were
rewritten (410 to 216 bytes); the payload now sits directly below the
Bluetooth blob. `patches/full/build/tests/test_theater_full.py` runs the
portrait case on the composed image.

## Open question: other callers of artwork setup

The reset hook sits at module 18's shared artwork setup, so any decode
through setup outside the player resets player sampling and writes the
theme default to the player background. In the everything build the only
static caller outside module 18 is the player; two module 18 loaders that
call setup are reached only through computed addresses. `audit_browser_interference.py` reproduces this on a built image
with a modeled browser-sized setup request. It is a known-defect reproducer,
not an isolation test. The no-art branches that skip artwork setup are
fixed in the everything build (patches 0045 and 0046,
`test_theater_noart.py`); the standalone variant does not carry that fix.

To run the suites locally, with the stock image and decoder inputs
configured:

```sh
python3 patches/theater/build/build_theater.py
python3 patches/theater/build/test_theater_lifecycle.py
python3 patches/theater/build/audit_browser_interference.py
```

No device testing was performed.

# Gapless fast path

Shipped armed in both images (Standard and Minimal): patches 0020 to 0025
install the machinery and 0026 (`0026-gapless-arm.patch` in
[`../framework/patches/`](../framework/patches/)) arms it. When the next track
uses the same codec, the transition keeps the loaded decoder and skips the
image copy, the decoder-core reset and the ready poll, saving at least 85 ms.

The decoder side is proven in emulation: a resident decoder decoded a second
file bit-exact after end of stream, across a sample-rate change
([`../harness/milestone2.md`](../harness/milestone2.md)). The system side of
the transition does not run in the harness and is unobserved until hardware.

- [`gapless_patch.md`](gapless_patch.md): the design and build as first delivered
  (disarmed); its status line predates arming.
- [`../../analysis/gapless.md`](../../analysis/gapless.md): the stock track-transition path.

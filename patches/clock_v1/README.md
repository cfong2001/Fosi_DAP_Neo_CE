# Clock table v1

Shipped in both images (Standard and Minimal) as patches 0003 to 0018 in
[`../framework/patches/`](../framework/patches/). Data only, no code changes.

Per-codec decoder clock rows are lowered from the stock table (top row
480 MHz) to 144 MHz for MP3, WMA, AAC and WAV, 240 MHz for Vorbis and
288 MHz for FLAC, ALAC, APE and DSD. APE and DSD128 decode loads are
unmeasured, so they are the first hardware check.

- [`clock_v1.md`](clock_v1.md): the targets, the solver replica that verifies them, and the open flags.
- [`../../analysis/clock_table.md`](../../analysis/clock_table.md): the stock clock table and solver.
- `build_clock_v1.py`, `verify_clock_v1.py`: generator and offline check.

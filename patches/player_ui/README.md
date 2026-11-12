# Player typography and labels

Standard CE draws elapsed and total time with the same text renderer and
font as the player title. The existing 148-byte time routine now formats
`MM:SS` into a bounded stack buffer and draws in a 66 by 16 pixel rectangle.
The stock 99-minute display limit and total-time state reset are preserved.
The sprite-digit resources are no longer used by this routine.

The shared marquee registrar starts with a 150-tick pause (1.5 seconds).
Only after an actual scroll draw does the stepper select 50 ticks between
steps (0.5 seconds, versus stock's 0.3). Registration resets the pause;
the existing 16-bit tick arithmetic handles wrap. This timing also applies
to scrolling browser rows and track information using the shared engine.
No new persistent state is allocated. The stamp helper occupies 10 bytes
of the census's unused 20-byte routine at `0x03053114`; its two original
instructions and the new interval store execute under Unicorn.

English resources 82 and 83 read **Artists** and **Albums**. The album
list's inline action reads **Play All Albums**, fitting its original
32-byte slot, including the terminator. Other languages retain their labels.

Build with the reference ARM toolchain:

```
python patches/player_ui/build_typography.py
python patches/player_ui/test_typography.py
```

The generator verifies the pinned stock SHA and emits expected-byte patches
and label runs. `patches/full/manifest.txt` and `build_theme.py` compose them
into Standard CE; Minimal and recovery retain their existing behavior.
The SDK mirror documented in `research/patch_technique_and_sdk.md` was used
only to identify text-rendering and scrolling semantics. These routines are
original CE code. Device rendering and timing remain untested on hardware.

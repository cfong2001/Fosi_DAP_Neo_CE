# Improvement concepts, ranked by value for effort

This is a bounded catalogue of the practical opportunities identified in
this firmware, not a claim that every possible future feature is known.
Value is user impact (1–5); effort is relative engineering work (1–5).
Higher value/effort goes first, with protocol and hardware dependencies
called out rather than hidden behind a score.

| Priority | Concept | Value | Effort | Implementation / dependency |
|---|---|---:|---:|---|
| 0 | First-flash review, read-only backup and matching recovery preparation | 5 | 2 | Implemented offline tooling; physical backup/restore qualification remains required |
| 1 | Remove redundant USB connection text | 3 | 1 | Implemented in USB screen PR |
| 2 | Show the actual USB PCM format and data rate | 4 | 1 | Implemented in USB screen PR; source-file tags are unavailable over UAC |
| 3 | Row-based fills, clears and opaque blits | 5 | 2 | Implemented in drawing engine PR; byte-parity and bounds tests |
| 4 | Row-based keyed sprites and unsmoothed glyphs | 4 | 2 | Implemented in drawing engine PR; preserve both keys, draw modes and fallback |
| 5 | Direct flash reads into full-screen framebuffer | 4 | 2 | Implemented in drawing engine PR; preserve byte swapping and split framebuffer banks |
| 6 | V155 60/120 volume steps | 4 | 2 | Trace gain scaling, limits, persistence and UI together |
| 7 | V155 startup autoplay toggle | 4 | 2 | Trace cold boot, resume state and USB/charge boots |
| 8 | V155 slow/fast wheel sensitivity | 3 | 2 | Trace wheel accumulator and repeat timing; keep key debounce intact |
| 9 | V155 power-saving battery mode | 5 | 4 | Identify actual power policy; endurance claims require current measurements |
| 10 | V155 grouped playback, power and display settings | 3 | 3 | Menu hierarchy and localized label mapping |
| 11 | V155 three independent library slots | 5 | 5 | Database filenames, scan/update/select lifecycle, migration and resume ownership |
| 12 | V155 decoder changes | 4 | 5 | Codec identification, ABI checks and decode vectors; binary differences alone are insufficient |
| 13 | USB host title/artist/album readback | 4 | 5 | New host companion + device protocol; standard UAC/HID does not carry tags |
| 14 | USB stream activity meter | 3 | 3 | Sample live PCM safely; distinguish silence, stream open, mute and paused host |
| 15 | Dirty-region redraw / idle frame suppression | 4 | 3 | Trace display flush ownership; preserve wake, dialogs and status updates |
| 16 | Persistent volume limit / hearing-friendly startup level | 4 | 3 | Trace gain, resume and headphone state; bounded persisted setting |
| 17 | ReplayGain and loudness normalization | 4 | 5 | Tag parsing, headroom and fixed-point PCM gain without clipping |
| 18 | More complete gapless transitions | 5 | 5 | Decoder IPC, delay/padding and PCM continuity; existing warm path is not universal gapless |
| 19 | Queue duration and remaining time | 3 | 3 | Reliable per-track durations and queue lifecycle |
| 20 | Library search and fast alphabet navigation | 4 | 4 | Input UI, Unicode matching, memory and large-library indexes |
| 21 | Album-aware shuffle / queue editing | 4 | 4 | Stable queue ownership, repeat modes and persistence |
| 22 | Accessibility: high contrast, larger text, reduced motion | 4 | 4 | Alternate layouts, glyph widths, localized text and persistent settings |
| 23 | Rich lock screen with metadata and progress | 3 | 3 | Extend existing snapshot without waking the backlight on every tick |
| 24 | Broader artwork decoding / embedded-cover selection | 3 | 4 | Decoder memory limits and malformed-image tests |
| 25 | Bluetooth connection diagnostics / reconnect policy | 3 | 4 | UART state, timeout and power sequencing evidence |
| 26 | Battery calibration and honest time estimates | 4 | 5 | Physical discharge curves under repeatable loads |
| 27 | On-device diagnostics / crash breadcrumb | 4 | 4 | Proven spare persistent bytes and nonintrusive error capture |
| 28 | Crossfade / DSP equalizer expansion | 3 | 5 | Single decoder window and no established mixer; major architecture work |

Every shipped change must have a concrete behavior test, reproducible
firmware output and passing PR workflows before merge. Hardware-dependent
concepts remain experiments until their dependencies can be verified.

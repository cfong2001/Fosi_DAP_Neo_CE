# Firmware work list

## Additional requested work

- [ ] Remove the “USB Connected” text from the USB screen while preserving
  connection state and USB operation.
- [ ] Accelerate the drawing engine in a separate PR:
  - Write complete rows for box fills, opaque images, transparent images
    and screen clears.
  - Accelerate transparent images and characters outside the smoothed set.
  - Read full-screen backgrounds directly from flash.
  - Retain the stock paths when rotated or when a shape extends off-screen.
  - Compare framebuffer output and memory bounds against stock, including
    transparent keys, clipping edges and every supported rotation.
- [ ] Port the features of official Fosi firmware V155 (1.5.5), in focused
  changes with validation against the supplied image.

## V155 reference and initial findings

The user supplied `DP3_V155.img` on 2026-11-12. It is 13,631,492 bytes with
SHA-256 `4713a2eb4b523d49ad003ac2df159c1c596339aef1a9a060e6ea6bbbf18e1332`.
The external source was Fosi's support download; use the verified image
rather than relying on the time-limited download URL. Do not silently
replace the V137 input or transplant relocated modules wholesale.

The English resource additions identify these porting candidates; the
labels establish that controls exist, not their full runtime behavior:

- Update Library / Select Library / Library 1, 2 and 3.
- Playback Settings, Volume Steps (60 / 120), Auto Play on Startup (Off / On).
- System & Power, Battery Mode (Normal / Power Saving), Scroll Sensitivity
  (Slow / Fast), Display & Language.
- Investigate the changes to decoder modules 76, 77 and 78; do not infer
  codec correctness or performance solely from a binary difference.

V155 relocates the primary overlay base from `0x0307D164` to `0x0307CEF0`
and the common window data base from `0x030247C4` to `0x030247F4`. Resident
module 0 changes from 171,028 to 170,400 code bytes. All image resources,
Font A, codepage data and system defaults are byte-identical by section;
Font B, language resources and many code modules differ. A port requires
new call-site and state-field evidence, plus the project's normal build,
byte-parity and emulation checks. Hardware behavior remains unverified.

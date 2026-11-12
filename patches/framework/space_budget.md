# Firmware space budget

Every code home the enhanced firmware uses, what occupies it, and
what room remains. Sizes are measured from the builds named; the
census behind the two large homes is analysis/resident_home/. The
rule the budget enforces: no feature ships in a home whose free
space has not been censused, and no build step may place code
outside the homes listed here.

## The homes

| Home | Capacity | Occupants | Spare |
|---|---|---|---|
| Module 0 stub-farm caves | about 84 B of verified-dead stub slots | DAC fix trampoline (14 B, patch 0002), gapless gate, its tail, core-1 flag literal and state (48 B, patches 0020 to 0026), gapless warm start (16 B at 0x03051504, patch 0034) | 14 B: the old three scraps (4 + 2 + 2), 0x030514FE (2 B) and 0x03051514 to 0x03051517 (4 B) |
| Module 39 sort cave (0x0309F000) | 1,196 B | Natural sort blob, 1,052 B (patch 0031) | about 140 B |
| Gap tail (exec 0x0307BFB4 to 0x0307C7B0) | 2,044 B | Full build: M3U staging 552 B (zeros), focus mode 340 B, theater 676 B, Bluetooth toggle 436 B | 40 B (36 free after focus, 4 spare) |
| Module 31 segment extension (exec 0x0307EE48 to 0x03080B54) | 7,436 B | Browser-hook trampoline 64 B (patch 0040), M3U bridge plus parser linked together 6,644 B, lock-screen routine 406 B (patch 0033) | 322 B |
| Module 32 segment extension (exec 0x030804AC to 0x03080B54) | 1,704 B | Battery-profile blob, 540 B (apply routine, defaults writer, selector entry, cave stubs, constants; patches 0051, 0052) | 1,164 B |
| Module 0 dead-code pockets ([`patches/space/`](../space/README.md)) | 8,508 B in 150 pockets, largest 256 B; 5,530 B in pockets of 64 B or more | Playlist hooks (216 B at 0x0306C878), theater no-art exits (100 B at 0x03063CDC), transport ground wrapper (52 B at 0x030539B4); patches 0047 to 0049 in the full build | about 8,140 B; a hardware tripwire build is still the proof |
| SAVEINFO verbatim block (+0x1C7 to +0x2D5) | about 270 B of settings space | Battery profiles, 32 B at +0x290 to +0x2AF (apply routine built; see patches/power/) | about 238 B |

The two segment extensions overlap in exec space: the module 31
payload runs to 0x03080A12, past module 32's extension base. That
is the stock design of this span, not a new hazard: every window
overlay in the family is loaded by a destructive copy on
activation and windows are mutually exclusive, and stock module
9's span (from 0x0307FFDC) already sits inside the range module
31 grows into. Each activation re-copies the module's full
segment, stock bytes plus extension, so no window ever executes
another window's extension bytes. The settling test is the
Phase E window-cycle soak, which cycles every window including
USB and settings and verifies the extension bytes after.

## Delivery mechanisms, one per home class

- In-segment caves take ordinary manifest patches. Nothing about
  them changes the image length or any module record.
- The gap tail takes the framework's `--tail` step and nothing
  else. The step accepts only the tail payload (2,044 bytes at
  most) and constructs the gap span itself: zeros across the
  workspace zone, payload at exec 0x0307BFB4, module 0 code_len
  extended over the whole span. The step it replaced (`--extension`,
  removed) let a caller place code at the gap base, exec
  0x03079C14, which the census proved is live runtime workspace
  (the file descriptor table, the directory stack, FAT fields).
  That target no longer exists in the build.
- Segment extensions take the `--grow` step (insertion rebuild):
  the payload is appended to a module's segment storage, its
  declared length grows, and every dependent offset in the package
  is recomputed. Grown builds validate with
  tools/validate_grown.py, because the stock validator pins the
  stock layout constants.

## Image-level accounting

- Stock image: 13,631,492 bytes.
- The default unified build (32 manifest patches plus the
  vorbis75 transplant) is the same length: byte patches and the
  transplant are size-neutral by construction (the transplanted
  module 75 is 116,572 bytes before and after).
- A tail build is the same length again: the gap is inside the
  image, so the step edits the code_len record and fills existing
  zero space.
- A grown build adds its payload length, rounded up to a whole
  512-byte sector: the insertion step pads zeros before the header
  mirror so the boot validator, which reads the mirror by sector,
  finds it (a 1,000-byte module 31 growth produces a 13,632,516-byte
  image in verify check 9). The mirror may move to `0xCFBE00` at most
  before the installer's rounded transfer grows past 13 MiB. The whole firmware with every feature composed is
  therefore the stock length plus the module 31 payload, about
  5 KB over stock, with the update package layout otherwise
  unchanged.

## The whole-firmware build

The resident half of the whole firmware builds today with one
command (default manifest, vorbis75 transplant, the real tail
composition as the `--tail` payload):

    build.py --tail tail_payload.bin --output whole.img

Measured result: output SHA-256
23aeb45121dca68c409a7ddf25dacde72e1bfc23684d277fc116a63165efd2a1,
32 patches applied, transplant applied, tail payload 2,044 bytes
delivered at exec 0x0307BFB4 (first nonzero byte at payload offset
1,192, exactly where the staging area ends and the hook code
begins), module 0 code_len 0x29C14 to 0x2C7B0, total diff versus
stock 72,317 bytes, validate() passed. The overlay half joins it when
the module 31 composition build lands; the two steps compose
because the tail step resolves its offsets from the image's own
records rather than constants.

## What is not a home

- The gap base and middle (exec 0x03079C14 to 0x0307BFB4):
  runtime workspace, settled by the census. The one live word at
  0x0307BFB0 is a counter and is also off limits.
- Module 0's remaining zero runs: named tables and buffers (the
  SAVEINFO mirror, the clock table) or uncensused holes between
  named bases; the census rated them worse candidates than the
  tail on the same evidence standard.
- The ebook reader's window slot (module 30): a shared window
  VMA, so code hosted there exists only while that window is
  active and evicts the browser. Available for a feature that is
  itself a window, at 8,288 bytes; nothing current needs it.
- Module 39's span above the sort cave: computed array bases of
  unknown extent (0x03099206, 0x0309C024) and the module's own
  live cells at its top.

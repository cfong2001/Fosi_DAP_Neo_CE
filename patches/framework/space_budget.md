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
| Former module 39 sort cave (0x0309F000) | Not available | Inside a live 64 KiB scratch array cleared by stock library initialization | No code may be allocated here |
| Module 39 explicit code extension (0x0309F4AC) | 1,052 B | Standard natural-sort prefix builder, comparator and fold table | Fully allocated |
| Gap tail (exec 0x0307BFB4 to 0x0307C7B0) | 2,044 B | Full build: M3U staging 552 B, focus 340 B, constructor restore 26 B, theater 680 B, Bluetooth 436 B, alignment 6 B | 4 B |
| Module 31 segment extension (exec 0x0307EE48 to 0x03080B54) | 7,436 B | Combined pinned browser/playlist/lock-screen/navigation payload, 6,616 B | 820 B |
| Module 32 segment extension (exec 0x030804AC to 0x03080B54) | 1,704 B | Unused. The earlier battery-profile blob (540 B, `patches/power/build/`) was never stacked; the power profile item now lives in module 0 pockets | 1,704 B |
| Module 0 dead-code pockets ([`patches/space/`](../space/README.md)) | 8,508 B in 150 pockets, largest 256 B; 5,530 B in pockets of 64 B or more | Playlist hooks (216 B at 0x0306C878), theater no-art exits (100 B at 0x03063CDC), transport ground wrapper (52 B at 0x030539B4), power profile lookups (104 B at 0x0305168C), value hook and presets (76 B at 0x03054668), commit hook (60 B at 0x03067064); patches 0047 to 0049 and 0140, 0141, 0146 in the full build | about 7,900 B; a hardware tripwire build is still the proof |
| SAVEINFO verbatim block (+0x1C7 to +0x2D5) | about 270 B of settings space | Theater at +0x1C8 (28 B), focus at +0x1E4 (12 B), optional browser diagnostic at +0x1F0 (4 B); profiles use stock settings only | Preserve these explicit owners |
| Image resource padding (after the images section, before the header mirror) | 4,592 B | Power profile records: four 58-byte headers and 84 label slots of 48 B (4,264 B) | 328 B |

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

The optional runtime diagnostic image reserves 100 bytes at `0x0306D304`,
64 at `0x030643C8`, and 56 at `0x03061638`, within censused pockets.
Its four-byte last-browser trace is at `SAVEINFO+0x1F0` (`0x03023490`),
immediately after the theater/focus state. These sites are not allocated
by the normal release. The utility refuses occupied sites and preserves
the input; see [runtime diagnostics](../../release/RUNTIME_DIAGNOSTICS.md).

Standard's Opus content detector also owns 66 bytes in the released ASF
tag case at `0x0306C5B0` and 48 bytes at `0x03065534`. These are code,
not tag-parser allocator space. The bounded checks preserve the native
Vorbis route and final seek reset.

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

## USB and row drawing allocations

USB card: 72 bytes at 0x0306004C and 144 bytes at 0x03054404. The
row drawing series uses only explicitly bounded unreferenced pockets;
`patches/drawing_engine/build_rows.py:PARTS` is the exact allocation map.
The C routines and saved-prologue wrappers total 1430 bytes (no persistent
RAM and no module growth). The framebuffer remains split at row 240;
unsupported geometry and display banks resume stock. Re-run the census
on the composed image before allocating further homes.

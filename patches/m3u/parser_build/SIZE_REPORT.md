# Parser placement size report (job 3)

Target: Cortex-M3 Thumb-2, linked at exec 0x03079C14 (module 0
extension), budget 11,164 bytes (extension cap EXT_MAX).

## Toolchain status: BLOCKED

No ARM C compiler exists in this environment (checked 2026-10-31):
- `arm-none-eabi-gcc`: not in /usr/bin, not in tools-local/bin, not
  anywhere on the filesystem (find /).
- `clang` / LLVM tools: not installed.
- tools-local/bin contains only the Rizin suite (rizin, rz-asm,
  rz-bin, ...). Ghidra 12.2 is present but bundles no C compiler.
- Host gcc is x86-64 only.

So no target object exists yet. What is pinned: the placement
address and layout (extension base 0x03079C14, hook trampoline at
+0x00, bridge entry `m3u_bridge_node_action` at +0x80, parser and
bridge code after), the build command (in bridge/m3u_bridge.c's
header), and the budget enforcement in the build step itself
(framework check 8 proves an 11,165-byte blob is refused).

## Host-section estimate (the design's method, reproduced)

`gcc -Os -std=c99 -ffreestanding -fno-builtin -c m3u.c` (x86-64,
this session; artifact m3u_host.o beside this file):

| section        | bytes |
|----------------|-------|
| .text          | 4,430 |
| .rodata        |   352 |
| .rodata.str1.1 |    31 |
| code+const     | 4,813 |

Whole object file: 5,339 bytes (adds .eh_frame 468 and ELF
metadata). The design's "5,426 B host object" figure was the whole
object under a slightly different host build; the section sum is
the meaningful number. `m3u_import` alone is 2,744 bytes of the
.text. No .data/.bss.

## What remains unproven

- The true Thumb-2 size. For this code class (table-light string
  and path logic) Thumb-2 is typically comparable to or denser
  than x86-64 -Os, and the budget has ~6.3 KB of headroom over the
  host section sum, with the trampoline at 132 bytes and the
  bridge (bridge/m3u_bridge.c) still to add. That is an estimate,
  not a measurement: no target size is claimed until
  arm-none-eabi-gcc is installed and the link is run.
- The link step itself (a linker script placing .text at
  0x03079C14 and the bridge entry at +0x80) is specified in the
  bridge source header but has never been executed.

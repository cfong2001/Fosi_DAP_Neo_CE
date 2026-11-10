# Parser target build (job 3, unblocked)

**Placement erratum (2026-10-31): the sizes in this document stand; the placement does not.** The extension base 0x03079C14 is live runtime workspace (file descriptor table, directory stack, FAT driver fields), established by the SRAM census in `resolver_design.md` and confirmed from the registrar disassembly at 0x0305C514. The composed blob measured here must not be placed at that base. The parser object itself (3,601 B, zero undefined symbols) is placement-independent and carries over to whatever home the follow-up census proves.

Toolchain: arm-none-eabi-gcc 13.2.1 (15:13.2.rel1-2), installed
2026-10-31. This supersedes the BLOCKED status in SIZE_REPORT.md:
the true Thumb-2 size is now measured, not estimated.

Source: work/patches/m3u/src/m3u.c (identical copy in this
directory). Flags, matching the design's build discipline:
`-std=c99 -mcpu=cortex-m3 -mthumb -ffreestanding -fno-builtin
-nostdlib`. Artifacts in `target/` beside this file.

## Object sizes (per section, bytes)

| section        | -Os   | -O2   | -Oz   |
|----------------|-------|-------|-------|
| .text          | 3,504 | 4,696 | 3,504 |
| .rodata        |    68 |    68 |    68 |
| .rodata.str1.x |    31 |    36 |    31 |
| .data          |     0 |     0 |     0 |
| .bss           |     0 |     0 |     0 |
| code+const     | 3,603 | 4,800 | 3,603 |

-Oz is byte-identical in size to -Os for this source. Largest
function at -Os: `m3u_import`, 2,018 B (host -Os measured 2,744 B;
the host section sum was 4,813 B against the target's 3,603 B, so
Thumb-2 came in 1,210 B denser than the x86-64 estimate).
No .ARM.exidx/.eh_frame is emitted. `.comment` and
`.ARM.attributes` are non-allocating metadata, excluded from the
image.

## Undefined symbols: none

`arm-none-eabi-nm -u` is empty at -Os, -O2 and -Oz. The only global
symbol is `m3u_import` (T). The parser makes no libc calls at all:
no memcpy/memset/strlen (it carries its own x_strlen/x_strcpy
helpers), no __aeabi_* runtime calls, no libgcc requirement. The
filesystem reaches it only through the M3uFs function-pointer table
passed in by the caller, so the object is fully self-contained and
position-fixed only by its link address.

## Link at the real placement

Linker script `target/parser.ld`: image linked at 0x03079C94
(extension base 0x03079C14 + 0x80).

| linked image (-Os) | bytes | address    |
|--------------------|-------|------------|
| .text              | 3,504 | 0x03079C94 |
| .rodata (merged)   |    97 | 0x0307AA44 |
| flat binary total  | 3,601 |            |

(String merging at link saves 2 B against the object section sum.)
`m3u_import` lands at 0x0307A260. The -O2 image is 4,804 B total.

## Fit against the 11,164 B cap

Composed extension blob (`target/extension_blob_full.bin`):
bytes +0x00..+0x7F of the scratch trampoline blob (64 B trampoline
+ 64 B NOP padding; the 4 B return-0 stub that sat at +0x80 is
replaced by the parser image), then the -Os parser binary at +0x80.

| component                | bytes  |
|--------------------------|--------|
| trampoline + NOP pad     |    128 |
| parser image (-Os)       |  3,601 |
| composed blob            |  3,729 |
| cap (EXT_MAX)            | 11,164 |
| headroom                 |  7,435 |

**Verdict: fits**, with 7,435 B left in the shared region for the
bridge and future UI code. Even the -O2 parser (blob 4,932 B)
fits. Note on layout: in the final design +0x80 is the bridge
entry `m3u_bridge_node_action` and the parser sits behind the
bridge; this measurement places the parser image itself at +0x80
to size the composed blob, per the work order. The bridge's own
compiled size is still open (see below), but the headroom is
larger than the whole parser, and the bridge at -O0 is 892 B of
.text plus 2,056 B of .bss (the 2 KB playlist buffer and statics;
.bss does not consume extension flash, it needs RAM, which is
blocker B2's question, not the cap's).

## Scratch framework build

Live framework build.py, `--extension target/extension_blob_full.bin`,
with a scratch manifest (copy of the live manifest plus
`0040-m3u-browser-hook.patch` appended; the live manifest was not
touched). Reference image: same live manifest, no extension, no
0040 (SHA-256 15990d8d9d7378e073597bb422388451384ca05d07325c9fc078245fad097b22;
this is the current 32-patch live state including 0050, so it
differs from the older 31-patch pin 7d9d6b30...).

Scratch image SHA-256:
**f2a6f34a0dbf206325f26759cf0417ee6062edb6f0f0eb2a399f7a9abe1dc466**

Build report: extension blob 3,729 B at file 0x532C0 (exec
0x03079C14); module 0 code_len 0x29C14 -> 0x2AAA5; 75,083 bytes
changed vs stock (reference: 71,515).

Exact diff, scratch vs reference (3,572 B in 168 ranges), confined
to four regions and nothing else:

| file range | bytes | what |
|---|---|---|
| 0x000210..0x000211 | 2 | module 0 code_len record (0x00029C14 -> 0x0002AAA5; high 2 bytes unchanged) |
| 0x0532C1..0x05414F | 3,565 | inside the extension blob span 0x532C0..0x54151 (164 blob bytes coincide with stock gap bytes) |
| 0x0908F6, 0x0908F8..0x0908F9 | 3 | patch 0040 hook site (fff76df9 -> fbf77bbe; byte 0x908F7 is 0xF7 in both) |
| 0xD00000..0xD00003 | 4 | trailer CRC (derived) |

The image bytes at the extension file offset equal the composed
blob exactly (verified byte for byte), and no byte past the blob
end differs.

## Bridge compile state (job 4 cross-check)

bridge/m3u_bridge.c compiled for the same target:

- As shipped: stops at the documented `#error` for STAGE_BASE
  (blocker B2), exactly as m3u_bridge.md states. Nothing else
  fails first.
- With a dummy `-DSTAGE_BASE=0x03030000` (compile probe only, no
  blocker fixed): compiles clean at -Os and -O0.
  - At -Os the object is a 4-byte `m3u_bridge_node_action` and
    nothing else: blocker B1's stub (`bridge_playlist_path`
    returns 0 unconditionally) lets the compiler prove the early
    return and dead-code-eliminate the whole import path. The
    bridge's effective compiled behaviour today is therefore
    identical to the 4-byte return-0 stub in the scratch blob,
    which is what patch 0040's gate promises (stock behaviour
    until the bridge is real).
  - At -O0 (no elimination): .text 892, .bss 2,056, .rodata 44.
    Undefined symbols are exactly `m3u_import` (the parser, now
    built) plus `stock_fs_acquire`, `stock_file_size`,
    `stock_file_read` - the extern wrappers m3u_bridge.h declares
    against the pinned stock addresses 0x030611E0 / 0x030545D4 /
    0x030693EA, to be bound at link time in the pinning pass.
- B1, B3 and B5 appear in the source as runtime stubs (return 0 /
  return -1 / empty library), not compile errors, matching the
  doc. B4 (.m3u8 LFN) remains a fall-through to stock in the
  trampoline's SFN name test. Compile state matches the
  documentation on every point checked.

## Framework verify

Live verify.py run after this work: 8/8 checks passed, including
check 7 (unified build: outside module 75 == framework-only build,
module 75 == pinned transplant hash, diff confined, reproducible)
and check 8 (extension build: confined diff, code_len extended,
oversize/overlap/dirty-gap refused). Check 7's unified image is
SHA-256 15990d8d..., byte-identical to the reference build above,
which cross-confirms both. One transient note: a first verify run
during this session reported check 7 FAIL with no detail while the
live tree was being edited concurrently (the 0050 integration);
the re-run on the settled tree passes 8/8, and nothing in this
workstream writes to the live tree.

## Stock image integrity

DP3_V137.img SHA-256 verified before and after this work:
fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef
(unchanged; all builds read it, none write it).

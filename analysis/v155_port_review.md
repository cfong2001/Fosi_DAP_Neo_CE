# V155 feature port review

Verified reference: `DP3_V155.img`, SHA-256
`4713a2eb4b523d49ad003ac2df159c1c596339aef1a9a060e6ea6bbbf18e1332`,
13,631,492 bytes; header date 2026-11-02. The reference is retained
unchanged. The older Rockchip SDK is useful for structure definitions and
API semantics, but is not source for this exact device or release.

## Runtime findings beyond labels

The V155 SAVEINFO base is 0x030232A4; the V137 base is 0x030232A0.
The fields below are **V155 offsets**, not free bytes in V137.

| Feature | Runtime evidence in V155 | Required coherent port |
|---|---|---|
| 60/120 volume steps | Module 32 at 0x0307FBE0..0x0307FC3A switches field +0x311, halves/doubles the saved volume and re-applies it. Resident 0x03060F14..0x03060F24 doubles physical gain input for 60-step mode. Resident 0x03052EE4 clamps to 60 or 120. | Every increment/decrement limit, display, gain path, boot normalization and switching conversion must agree. A label or one max-volume patch would be incorrect. |
| Startup autoplay | Module 32 option writes +0x310 at 0x0307FD4A. Resident 0x030624DE..0x030624F0 tests it and saved state +0x7E before posting event 0x16D. | Verify the V137 event consumer and saved-state semantics, then handle cold boot, USB/charge boot, missing media and resume together. |
| Scroll sensitivity | Module 32 writes +0x30F at 0x0307FD42. Resident 0x03061CA2..0x03061CBC selects between quadrature decoders at 0x0306195A and 0x03061B0C. The former accumulates five samples; V137's decoder at 0x03061936 accumulates three. | Port the actual decoder and sampling contract. Changing only the wheel timer does not reproduce V155 sensitivity. |
| Battery mode | Module 32 writes +0x312 at 0x0307FC40 and calls resident 0x03060EE4. That routine chooses DAC control value 0x31 or 0x10 at selector 0x80000, jointly with gain field +0x302. The clock solver at 0x03067284..0x030672AA also selects a different limiting row. | Preserve gain/headroom and decoder clock requirements; validate both DAC and clock policy. The existing CE Power Profile only groups timeouts/brightness and is not this feature. |
| Three library slots | Startup 0x030624AE..0x030624C8 clamps +0x316 to 0..2 and derives a library address using stride 0x174A0. Settings selection at 0x0307D94A..0x0307D952 reads that field. Module 38 scanner changes as well. | Trace all database read/write, scan/update/select, playback resume and removable-media paths. Do not redirect only a menu or one database pointer. |

The V137 autoplay-equivalent insertion area is near 0x03062288, but its
existing boot behavior, event numbering and stored fields must be proven
against its own consumer. No V155 address is used directly as a V137 hook.

## Why the SDK does not make a blind transplant valid

The SDK's `MENU_TEXT_INFO_STRUCT` identifies each 58-byte menu header;
the existing CE Power Profile implementation already reuses that format
and stock resource reader. V155 has a different language-table layout,
menu hierarchy, overlay base (0x0307CEF0 versus 0x0307D164), shared window
base (0x030247F4 versus 0x030247C4), resident code and settings fields.
Its whole menu overlay is not position-independent.

V137 boot also restores settings selectively. The apparent
+0x1C7..+0x2D5 area has both a memcpy branch and a string-copy branch.
A new persistent setting needs a proven unused range and a round-trip
under **both** boot branches, or an explicit normalized load/save change.
Treating a nominal gap as spare would risk settings loss or overwritten
state. See `saveinfo_lock.md`.

Decoder modules 76 (FLAC), 77 (ALAC/MP4, likely identification) and 78
(APE) change code and initialized data. Required checks include the core-1
loader/IPC ABI, file callbacks, format info, seek, malformed input,
16/24-bit sample vectors, end-of-stream and rate changes. A smaller binary
is not evidence of a faster or corrected decoder. The supplied image's
fonts, codepages, system defaults and image assets can be compared safely;
they do not prove runtime feature compatibility.

## Release disposition

The USB and drawing changes are implemented and independently tested.
The V155 feature ports above are **not implemented or marked complete**.
This review records concrete port entry points and dependencies, rather
than shipping menu items without their behavior or untested power/decoder
changes in an image intended for a first hardware flash.

Before a V155 port can be qualified: complete persistent-setting migration
vectors, full menu/resource relocation checks, library round-trips,
codec vectors and the device recovery qualification in
`release/FLASH_REVIEW.md`. The ranked concept list in `IMPROVEMENTS.md`
retains these as follow-up work with explicit dependencies.

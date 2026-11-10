#!/usr/bin/env python3
"""Round-to-nearest fix for the transplanted module 75 output conversion.

The full-precision Tremor build spliced in by transplant.py converts
its fixed-point synthesis output to s16 by flooring (arithmetic shift
or sign-extending extraction immediately before saturation). On the
pinned 40-file corpus (patches/vorbis_swap/corpus/) that costs a fixed
6.02 dB of delivered SNR against the round-to-nearest s16 ceiling,
while the decoder arithmetic underneath measures 102 to 123 dB.

Four conversion sites exist in the transplanted code segment (offsets
are code-segment relative; isolation evidence and the harness proof
are in vorbis_rounding.md):

  A 0x58D2  sbfx r3, r3, #8, #0x17   steady state, first overlap region
  B 0x590C  sbfx r0, r0, #8, #0x17   steady state, second region
  C 0x5892  asrs r3, r3, #9 + ssat   first-decode path (never fired in
                                     the isolation censuses; patched on
                                     structural identity with D)
  D 0x5922  asrs r2, r2, #9 + ssat   first-decode path

No site has spare bytes inline, so each detours (b.w) to a cave in the
verified all-zero tail of the transplanted code region
(0xDEE0..0xE054). Each cave adds half an output LSB to the
pre-extraction value (+0x80 on the high-word scale at A/B, +0x100 on
the Q24 scale at C/D; at D the bias applies to the post-negation
value, so it acts on the value being shifted), performs the site's
original extraction and saturation, and branches back. Total change:
70 bytes, all inside the code segment.

Branch encodings below are constants of this fixed layout (sites and
caves are pinned offsets in the transplanted code) and were verified
two ways in the isolation workstream: assembled with rz-asm and
re-decoded with capstone, and the composed output reproduced the
harness-verified module byte for byte.
"""

# (offset, expect_bytes, replacement_bytes)
_WRITES = [
    # detours at the four sites
    (0x58D2, bytes.fromhex("43f31623"),
     bytes.fromhex("08f005bb")),
    (0x590C, bytes.fromhex("40f31620"),
     bytes.fromhex("08f0f0ba")),
    (0x5892, bytes.fromhex("5b1203f30f03"),
     bytes.fromhex("08f035bb00bf")),
    (0x5922, bytes.fromhex("521202f30f02"),
     bytes.fromhex("08f0f5ba00bf")),
    # cave A at 0xDEE0: add.w r3, r3, #0x80; sbfx r3; b.w 0x58D6
    (0xDEE0, bytes(12),
     bytes.fromhex("03f1800343f31623f7f7f5bc")),
    # cave B at 0xDEF0: add.w r0, r0, #0x80; sbfx r0; b.w 0x5910
    (0xDEF0, bytes(12),
     bytes.fromhex("00f1800040f31620f7f70abd")),
    # cave C at 0xDF00: add.w r3, r3, #0x100; asrs r3, #9; ssat r3; b.w 0x5898
    (0xDF00, bytes(14),
     bytes.fromhex("03f580735b1203f30f03f7f7c5bc")),
    # cave D at 0xDF10: add.w r2, r2, #0x100; asrs r2, #9; ssat r2; b.w 0x5928
    (0xDF10, bytes(14),
     bytes.fromhex("02f58072521202f30f02f7f705bd")),
]


def apply_rounding(code):
    """Return the transplanted code segment with the rounding fix
    applied. Raises AssertionError if any expect-bytes or cave-zero
    precondition does not hold (the input is then not the pinned
    transplanted code and the fix must not be applied blind)."""
    code = bytearray(code)
    seen = []
    for off, expect, repl in _WRITES:
        for o2, r2 in seen:
            assert off + len(repl) <= o2 or o2 + len(r2) <= off, \
                "rounding writes overlap"
        seen.append((off, repl))
        assert bytes(code[off:off + len(expect)]) == expect, \
            f"rounding expect mismatch at {off:#x}"
        code[off:off + len(repl)] = repl
    return bytes(code)

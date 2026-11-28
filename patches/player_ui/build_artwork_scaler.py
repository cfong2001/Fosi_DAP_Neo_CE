"""Replace soft arithmetic in the cover scaler with equal integer results.

Module 19 resamples every artwork pixel with 24 calls to a 16.16 multiply
helper and, per channel, an int -> double -> 2^-16 -> float -> int chain.
The helper becomes UMULL; it has no other caller in the 82 modules. Each
channel sum is at most 255 * 0x10000 < 2^24, where the stock chain equals
v >> 16 (checked for every v in 0..2^24 by test_artwork_scaler.py), so the
chain becomes one shift. Code stays at its stock addresses.

The x source coordinate was a float divide per pixel: A = f2uiz(ldexp(
fl(x / s), 16)) and xi = f2iz(fl(x / s)), 236 instructions. With
s = ms * 2^(e - 23) and G = 39 - e, A depends only on x * 2^G / ms. Once per
row, a hook stores ms and R = floor(2^G / ms) in two stack slots: the one
holding s, which only the divide read per pixel, and a duplicate of the
source width.
Per pixel, x * rho = -(x * R * ms) mod 2^32 (G >= 32), so one UDIV gives
P0 = floor(x * 2^G / ms). One compare then repeats the float's
round-to-nearest. test_cover_decode.py checks every column of every scale
the painter can reach against the stock helpers.
"""
from pathlib import Path
import hashlib
import sys
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB, KS_MODE_V8
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image

MULHI = 0x0306D8CE
# (first byte of the conversion, its closing uxtb, bytes to keep: a literal pool)
CHAINS = ((0x03087780, 0x03087794, None),
          (0x030877E8, 0x030877FC, None),
          (0x03087850, 0x03087874, (0x0308785E, 0x0308786C)))
NOP = b'\x00\xbf'


def payloads():
    ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)
    mulhi = bytes(ks.asm('umull r0, r1, r0, r1; lsrs r0, r0, #16; orr.w r0, r0, r1, lsl #16; bx lr', MULHI)[0])
    out = [(0, MULHI, mulhi + NOP * ((32 - len(mulhi)) // 2))]
    for start, end, keep in CHAINS:
        code = bytes(ks.asm(f'lsrs r0, r0, #16; b.n {end:#x}', start)[0])
        if keep is None:
            code += NOP * ((end - start - len(code)) // 2)
        else:
            code += NOP * ((keep[0] - start - len(code)) // 2)
        out.append((19, start, code))
    for start, end, keep in CHAINS:
        if keep:
            out.append((19, keep[1], NOP * ((end - keep[1]) // 2)))
    return out


POCKET = 0x03056442    # module 0 dead routine, 46 B (patches/space census tier 1)
ROUND = 0x0306D8DA     # module 0, NOP tail of the 0279 multiply helper
ROW = (0x03087784, 0x030877EC, 0x03087854, 0x0308786C)   # the NOP runs 0280 to 0283 left
F2IZ = 0x03055304


def coord_payloads():
    ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB | KS_MODE_V8)    # V8 for UDIV, as build_theater.py
    def asm(src, at, size):
        code = bytes(ks.asm(src, at)[0])
        assert len(code) <= size, (hex(at), len(code), size)
        return code + NOP * ((size - len(code)) // 2)
    a, b, c, d = ROW
    return [
        # Per row, after the y divide: R and ms into [sp, #4] and [sp, #0x40].
        (19, 0x03087530, asm(f'bl {a:#x}; mov r8, r0; adds r0, r0, #1; ldr r1, [sp]', 0x03087530, 10)),
        (19, a, asm(f'ldr r0, [sp, #0x40]; lsrs r2, r0, #23; rsb r2, r2, #166; ubfx r1, r0, #0, #23;'
                    f'movs r3, #1; b {c:#x}', a, 16)),
        (19, c, asm(f'orr r1, r1, #0x800000; str r1, [sp, #0x40]; movs r0, #0; b {b:#x}', c, 10)),
        (19, b, asm(f'loop: lsls r3, r3, #1; cmp r3, r1; it hs; subhs r3, r3, r1; adcs r0, r0;'
                    f'subs r2, #1; bne loop; b {d:#x}', b, 16)),
        (19, d, asm(f'str r0, [sp, #4]; ldr r0, [sp, #0x44]; b.w {F2IZ:#x}', d, 8)),
        # Per pixel: A to [sp, #0x20], where the float quotient was, and xi in r0.
        (19, 0x03087552, asm(f'ldr r3, [sp, #4]; ldr r2, [sp, #0x40]; muls r3, r0, r3; bl {POCKET:#x};'
                             'str r3, [sp, #0x20]; lsrs r0, r3, #16', 0x03087552, 16)),
        (19, 0x0308757C, asm('ldr r0, [sp]', 0x0308757C, 2)),
        (19, 0x0308770E, asm('ldr r0, [sp, #0x20]; b 0x0308771a', 0x0308770E, 12)),
        # r3 = x * R, r2 = ms -> r3 = A. Below 2^23, fl(v) rounds up to the next
        # 2^-16 step exactly when the gap to it is at most half an ulp; above,
        # the ulp is 2^k steps and the remainder decides (ties cannot occur).
        (0, POCKET, asm('mul r1, r3, r2; negs r1, r1; udiv r1, r1, r2; add r3, r1; clz r0, r3;'
                        'subs r0, #8; ble big; mla r1, r3, r2, r2; lsrs r2, r0; cmp.w r1, r2, lsr #1;'
                        f'it ls; addls r3, #1; bx lr; big: negs r0, r0; lsrs r3, r0; lsls r3, r0; b.w {ROUND:#x}',
                        POCKET, 46)),
        (0, ROUND, asm('mul r1, r3, r2; lsls r2, r0; add.w r2, r2, r1, lsl #1; lsrs r2, r2, #31;'
                       'lsls r2, r0; add r3, r2; bx lr', ROUND, 20)),
    ]


COORD_NAMES = ('0370-scaler-row-hook', '0371-scaler-row-setup', '0372-scaler-row-mantissa',
               '0373-scaler-row-reciprocal', '0374-scaler-row-store', '0375-scaler-x-coord',
               '0376-scaler-width-slot', '0377-scaler-x-weight', '0378-scaler-x-divide',
               '0379-scaler-x-round')
COORD_WHY = ('The cover scaler computes each column\'s source coordinate with integer arithmetic '
             'instead of a soft float divide per pixel: a per-row reciprocal in two stack slots and '
             'one UDIV per pixel give the stock value for every column and scale the painter reaches. '
             'Code lives in the NOP runs 0280 to 0283 left, a census tier 1 dead routine and the '
             'multiply helper\'s tail. No new RAM.')

NAMES = ('0279-scaler-multiply', '0280-scaler-channel-r', '0281-scaler-channel-g',
         '0282-scaler-channel-b', '0283-scaler-channel-b-tail')


def main():
    raw = bytearray((ROOT / 'DP3_V137.img').read_bytes())
    assert hashlib.sha256(raw).hexdigest() == 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
    image = Image(bytes(raw))
    groups = ((NAMES, payloads(), 'stock bytes; exhaustive conversion check and artwork framebuffer parity in test_artwork_scaler.py',
               'The cover scaler computes the same integers without soft arithmetic: UMULL for the 16.16 '
               'multiply helper and a shift for the per-channel float round trip. No new code home or RAM.'),
              (COORD_NAMES, coord_payloads(), 'bytes after 0279 to 0283; exhaustive column check and artwork '
               'framebuffer parity in test_cover_decode.py', COORD_WHY))
    for names, edits, gate, why in groups:
        assert len(names) == len(edits)
        for name, (module, address, code) in zip(names, edits):
            offset, size = image.module_region(module, 'code')
            base = image.modules[module]['code_exec']
            assert base <= address and address + len(code) <= base + size
            at = offset + address - base
            expected = bytes(raw[at:at + len(code)])
            raw[at:at + len(code)] = code
            (HERE / (name + '.patch')).write_text(
                '# Generated by build_artwork_scaler.py.\n'
                f'name: {name}\nkind: module\nmodule: {module}\nregion: code\naddress: {address:#x}\n'
                f'expect: {expected.hex()}\nreplace: {code.hex()}\ngate: {gate}\nrationale: {why}\n')
    print('scaler patches:', ', '.join(NAMES + COORD_NAMES))


if __name__ == '__main__':
    main()

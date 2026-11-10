#!/usr/bin/env python3
"""Route (b) evidence gate: the browser's icon draw path is opaque.

The browser window's status helper (module 31, 0x0307E804) and its
Service battery draw (0x0307DB60) call DrawImage (0x03063700),
which takes only a resource id; the position comes from the display
context. The keyed helpers (0x03063A08 and family) take (id, x, y),
so the v4 repoint pattern does not apply to these sites. What
matters instead is what DrawImage emits: this gate runs the real
module 0 draw code under Unicorn (the prove_keying.py harness
pattern: the pixel store 0x03063E60 is intercepted and recorded,
the DMA copy primitive is modelled as a plain copy) and shows that
DrawImage emits every pixel of a resource, ground included, for
stock art and for the redrawn browser set alike. Ground matching
is therefore the correct and sufficient condition for the redesign.

Control: the same charging battery frame (150, authored with a
0xF800 field) through the keyed helper emits only its outline and
bars, which is what the charging frames are for on the screen that
draws them keyed; through DrawImage the field lands as magenta,
so the frames module 31 can reach opaquely are the level frames.
"""
import hashlib
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORK = ROOT.parent
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image  # noqa: E402
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE  # noqa: E402
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1,  # noqa: E402
                               UC_ARM_REG_R2, UC_ARM_REG_R3,
                               UC_ARM_REG_SP, UC_ARM_REG_LR,
                               UC_ARM_REG_PC)

raw = (ROOT / 'DP3_V137.img').read_bytes()
assert hashlib.sha256(raw).hexdigest() == \
    'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
im = Image(raw)
EXT = WORK / 'extracted'
CODE = (EXT / 'module_00_code_03050000.bin').read_bytes()
DATA = (EXT / 'module_00_data_03004000.bin').read_bytes()
END = 0x030EF000
STORE = 0x03063E60
RES_CELL = 0x0302328C
SAVEINFO = 0x030232A0
RES = 0x03080000
STACK = 0x030F0000
DRAWIMAGE = 0x03063700
KEYED = 0x03063A08

sec = im.sections['images']
imgs = {e['id']: e for e in im.images()}
TEST_IDS = (39, 143, 150, 262, 266)


def make_uc():
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x03000000, 0x500000)
    u.mem_map(0xE000E000, 0x1000)
    u.mem_write(0x03050000, CODE)
    u.mem_write(0x03004000, DATA)
    emitted = []

    def hook(uc, addr, size, user):
        if addr == STORE:
            emitted.append(uc.reg_read(UC_ARM_REG_R0) & 0xFFFF)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif addr == 0x03053F5E:
            src = uc.reg_read(UC_ARM_REG_R0)
            dst = uc.reg_read(UC_ARM_REG_R1)
            n = uc.reg_read(UC_ARM_REG_R2)
            if n:
                uc.mem_write(dst, bytes(uc.mem_read(src, n)))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    u.hook_add(UC_HOOK_CODE, hook)
    return u, emitted


def call(u, addr, r0=0, r1=0, r2=0, r3=0):
    sp = STACK - 0x100
    for reg, val in ((UC_ARM_REG_R0, r0), (UC_ARM_REG_R1, r1),
                     (UC_ARM_REG_R2, r2), (UC_ARM_REG_R3, r3),
                     (UC_ARM_REG_SP, sp), (UC_ARM_REG_LR, END | 1)):
        u.reg_write(reg, val)
    u.emu_start(addr | 1, END, count=20000000)
    assert u.reg_read(UC_ARM_REG_PC) == END, \
        f'call to {addr:#x} did not return'


def stage(u, pixel_source):
    """Stage the descriptor table plus the test resources' pixels.
    pixel_source(id) returns the resource's file bytes."""
    n = struct.unpack_from('<I', raw, sec['offset'] + 16)[0]
    u.mem_write(RES, raw[sec['offset']:sec['offset'] + 0x20 + n * 16])
    u.mem_write(RES_CELL, struct.pack('<I', RES))
    for rid in TEST_IDS:
        e = imgs[rid]
        u.mem_write(RES + (e['data_offset'] - sec['offset']),
                    pixel_source(rid))
    u.mem_write(SAVEINFO + 0x2D8, b'\x00')   # dark theme: no remap


def words_of(data):
    le = struct.unpack(f'<{len(data) // 2}H', data)
    return [((v & 0xFF) << 8) | (v >> 8) for v in le]


def main():
    failures = 0
    for label, source in (
            ('stock', lambda rid: raw[imgs[rid]['data_offset']:
                                       imgs[rid]['data_offset'] +
                                       imgs[rid]['size']]),
            ('browser set', lambda rid:
             (HERE / 'icon_set_browser' / f'asset_{rid}.bin')
             .read_bytes())):
        for rid in TEST_IDS:
            u, em = make_uc()
            stage(u, source)
            call(u, DRAWIMAGE, rid)
            want = words_of(source(rid))
            ok = em == want
            failures += not ok
            print(f'{label} DrawImage {rid}: emitted {len(em)} of '
                  f'{len(want)} pixels, sequence exact: {ok}')
    # control: charging frame 150 through the keyed helper
    u, em = make_uc()
    stage(u, lambda rid: raw[imgs[rid]['data_offset']:
                            imgs[rid]['data_offset'] + imgs[rid]['size']])
    call(u, KEYED, 150, 10, 20)
    want = [v for v in words_of(raw[imgs[150]['data_offset']:
                                     imgs[150]['data_offset'] +
                                     imgs[150]['size']]) if v != 0xF800]
    ok = em == want
    failures += not ok
    print(f'control keyed helper 150: emitted {len(em)} non-key '
          f'pixels of {len(want)} expected, exact: {ok}')
    print('PASS: DrawImage is opaque for stock and redrawn art; '
          'the ground is what lands' if not failures else 'FAIL')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())

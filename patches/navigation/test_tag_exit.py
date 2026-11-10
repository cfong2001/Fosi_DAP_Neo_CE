#!/usr/bin/env python3
"""Check proposed module-24 tag-library context hook against stock."""
import argparse
import hashlib
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rknano_image import Image
from build_tag_exit import build, BASE
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
    UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
    UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_R12,
    UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_CPSR)

SITE, CONT, CTX, STAGE = 0x0307ec72, 0x0307ec76, 0x03023980, 0x0307bfb4
REGS = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
        UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
        UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
        UC_ARM_REG_R12, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_CPSR]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prefix', default='arm-none-eabi-')
    p.add_argument('--stock', type=Path, default=ROOT / 'DP3_V137.img')
    a = p.parse_args()
    raw = a.stock.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
    im = Image(raw)
    m = im.modules[24]
    off, length = im.module_region(24, 'code')
    code = raw[off:off + length]
    assert m['code_exec'] + length == BASE
    assert code[SITE - m['code_exec']:SITE - m['code_exec'] + 4].hex() == 'a5f8f2c0'
    blob, patch = build(a.prefix)

    def run(patched, armed, category):
        u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        u.mem_map(0x03000000, 0x100000)
        u.mem_write(m['code_exec'], code)
        u.mem_write(BASE, blob)
        if patched:
            u.mem_write(SITE, patch)
        u.mem_write(STAGE, bytes([armed]))
        for i, reg in enumerate(REGS[:13]):
            u.reg_write(reg, 0x1000 + i)
        u.reg_write(UC_ARM_REG_R5, CTX)
        u.reg_write(UC_ARM_REG_R12, category)
        u.reg_write(UC_ARM_REG_SP, 0x030f0000)
        u.reg_write(UC_ARM_REG_LR, 0x030ed001)
        u.reg_write(UC_ARM_REG_CPSR, 0xa0000033)
        u.emu_start(SITE | 1, CONT, count=100)
        assert u.reg_read(UC_ARM_REG_PC) == CONT
        return ([u.reg_read(r) for r in REGS], bytes(u.mem_read(STAGE, 1))[0],
                struct.unpack('<H', u.mem_read(CTX + 0xf2, 2))[0])

    for category in (1, 2, 3, 4, 5, 6, 7, 8, 9, 100):
        for armed in (0, 1):
            old, oldflag, oldcat = run(False, armed, category)
            new, newflag, newcat = run(True, armed, category)
            assert old == new and oldcat == newcat == category
            assert oldflag == armed and newflag == 0
    print('PASS: category commit preserves stock state and clears both flag states (10 categories)')

    # The same-track fast path exits before the context commit. An armed
    # flag must survive this path because no new play context was built.
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x03000000, 0x100000)
    u.mem_write(m['code_exec'], code)
    u.mem_write(BASE, blob)
    u.mem_write(SITE, patch)
    u.mem_write(STAGE, b'\x01')
    category_ptr, list_ptr, save = 0x03018000, 0x03019000, 0x0301a000
    u.mem_write(category_ptr, struct.pack('<H', 2))
    u.mem_write(CTX + 0xf2, struct.pack('<H', 2))
    u.mem_write(CTX + 2, struct.pack('<H', 5))
    u.mem_write(list_ptr + 0xa, struct.pack('<H', 0))
    u.mem_write(list_ptr + 0xc, struct.pack('<H', 4))
    u.mem_write(list_ptr + 2, struct.pack('<H', 3))
    u.mem_write(CTX + 0x110, struct.pack('<H', 3))
    u.mem_write(save + 0x50, struct.pack('<H', 0))
    u.reg_write(UC_ARM_REG_R4, category_ptr)
    u.reg_write(UC_ARM_REG_R5, CTX)
    u.reg_write(UC_ARM_REG_R6, list_ptr)
    u.reg_write(UC_ARM_REG_R8, save)
    u.reg_write(UC_ARM_REG_SP, 0x030f0000)
    u.emu_start(0x0307ea3b, 0x0307ea78, count=100)
    assert u.reg_read(UC_ARM_REG_PC) == 0x0307ea78
    assert bytes(u.mem_read(STAGE, 1)) == b'\x01'
    print('PASS: stock same-track early return preserves the flag')
    print('LIMIT: module-24 growth, loader residency and full playback remain unverified')


if __name__ == '__main__':
    main()

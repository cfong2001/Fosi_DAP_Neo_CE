#!/usr/bin/env python3
"""Compare candidate disarm stubs with stock instructions in Unicorn.

This tests instruction-level state, not a full playback transition. It is
not evidence for hardware behavior and does not install a firmware patch.
"""
import argparse
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rknano_image import Image
from build_exit import build, BASE
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
    UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
    UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_R12,
    UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_CPSR)

STAGE = 0x0307bfb4
REGS = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
        UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
        UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
        UC_ARM_REG_R12, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_CPSR]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prefix', default='arm-none-eabi-')
    p.add_argument('--stock', type=Path, default=ROOT / 'DP3_V137.img')
    a = p.parse_args()
    image = a.stock.read_bytes()
    assert hashlib.sha256(image).hexdigest() == 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
    im = Image(image)
    m = im.modules[31]
    off, size = im.module_region(31, 'code')
    module = image[off:off + size]
    code, syms, patches = build(a.prefix)

    def run(which, patched, armed):
        site, stop = ((0x0307e04e, 0x0307e052) if which == 'folder'
                      else (0x0307e1cc, 0x0307e1d2))
        actual = module[site-m['code_exec']:site-m['code_exec'] + (4 if which == 'folder' else 6)]
        assert actual.hex() == ('01252846' if which == 'folder' else 'e648d8f769ff')
        u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        u.mem_map(0x03000000, 0x100000)
        u.mem_write(m['code_exec'], module)
        u.mem_write(BASE, code)
        if patched:
            u.mem_write(site, patches[which])
        u.mem_write(STAGE, bytes([armed]))
        for i, reg in enumerate(REGS[:13]):
            u.reg_write(reg, 0x1000 + i)
        u.reg_write(UC_ARM_REG_SP, 0x030f0000)
        u.reg_write(UC_ARM_REG_LR, 0x030ed001)
        u.reg_write(UC_ARM_REG_CPSR, 0xa0000033)  # seed flags and Thumb mode
        calls = []
        def intercept(uc, address, length, user):
            if address == 0x030570a4:
                calls.append(uc.reg_read(UC_ARM_REG_R0))
                for reg, value in ((UC_ARM_REG_R0, 0x1234), (UC_ARM_REG_R1, 0x4321),
                                   (UC_ARM_REG_R2, 0x9876), (UC_ARM_REG_R3, 0xabc),
                                   (UC_ARM_REG_R12, 0x2468)):
                    uc.reg_write(reg, value)
                uc.reg_write(UC_ARM_REG_CPSR, 0x60000033)
                uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        u.hook_add(UC_HOOK_CODE, intercept)
        u.emu_start(site | 1, stop, count=100)
        assert u.reg_read(UC_ARM_REG_PC) == stop
        return [u.reg_read(r) for r in REGS], bytes(u.mem_read(STAGE, 1))[0], calls

    for kind in ('folder', 'file'):
        for armed in (0, 1):
            baseline, old_flag, expected_calls = run(kind, False, armed)
            current, new_flag, actual_calls = run(kind, True, armed)
            assert current == baseline, (kind, armed, baseline, current)
            assert old_flag == armed and new_flag == 0
            assert expected_calls == actual_calls
            assert actual_calls == ([] if kind == 'folder' else [0x03023d38])
            print(f'PASS {kind} start: flag {armed} -> 0, register and call state match stock')

    # Enter a child directory while an M3U is playing. Follow the actual
    # stock branch from class dispatch up to the first directory-loader
    # call; playback-start hooks must not disarm just for navigation.
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x03000000, 0x100000)
    u.mem_write(m['code_exec'], module)
    u.mem_write(BASE, code)
    u.mem_write(0x0307e04e, patches['folder'])
    u.mem_write(0x0307e1cc, patches['file'])
    u.mem_write(STAGE, b'\x01')
    state, node, mode = 0x03018000, 0x03019000, 0x0301a000
    u.mem_write(state + 56 + 0x0c, b'\x01\x00')
    u.mem_write(state + 0x1cc, b'\x01\x00')
    u.mem_write(state + 0x1f4, (0x0301b000).to_bytes(4, 'little'))
    u.reg_write(UC_ARM_REG_R1, 0)
    u.reg_write(UC_ARM_REG_R2, 1)
    u.reg_write(UC_ARM_REG_R3, state + 2)
    u.reg_write(UC_ARM_REG_R4, node)
    u.reg_write(UC_ARM_REG_R5, 0)  # directory class
    u.reg_write(UC_ARM_REG_R7, state)
    u.reg_write(UC_ARM_REG_R9, 0)
    u.reg_write(UC_ARM_REG_R10, mode)
    u.reg_write(UC_ARM_REG_R12, 1)  # not the folder-play special case
    u.reg_write(UC_ARM_REG_SP, 0x030f0000)
    u.emu_start(0x0307df17, 0x0307dffc, count=100)
    assert u.reg_read(UC_ARM_REG_PC) == 0x0307dffc
    assert bytes(u.mem_read(STAGE, 1)) == b'\x01'
    print('PASS child directory traversal preserves the active playlist flag')
    print(f'candidate uses {len(code)} of {0x03080b54 - BASE} remaining module-31 bytes')
    print('LIMIT: downstream playback and hardware behavior not exercised')


if __name__ == '__main__':
    main()

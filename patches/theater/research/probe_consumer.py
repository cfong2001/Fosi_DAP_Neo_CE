#!/usr/bin/env python3
"""Drive stock JPEG service and module-17 painter with seeded geometry.

The generated fixture and firmware SHA gate are shared with probe_jpeg.py.
We model file reads and intercept the final LCD blit; all service, event and
painter instructions execute. Geometry and event scheduling are synthesized,
so this is not an end-to-end proof of playback-window artwork behavior.
"""
from pathlib import Path
import runpy
import struct

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
    UC_ARM_REG_R3, UC_ARM_REG_PC, UC_ARM_REG_SP, UC_ARM_REG_LR)

# Run the decoder-only proof and reuse its original generated JPEG fixture.
fixture = runpy.run_path(str(Path(__file__).resolve().parent / 'probe_jpeg.py'))
im, raw, jpeg = fixture['im'], fixture['raw'], fixture['JPEG']
u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
u.mem_map(0x03000000, 0x100000)
for module in (0, 17, 18, 19):
    m = im.modules[module]
    for kind in ('code', 'data'):
        off, size = im.module_region(module, kind)
        if size:
            u.mem_write(m[kind + '_exec'], raw[off:off + size])


def w32(addr, value):
    u.mem_write(addr, struct.pack('<I', value))


ctx, row, callback, end = 0x030282A8, 0x03027DA8, 0x030E0000, 0x030EF000
cursor = 0
blits = []
w32(0x03025944, 1)  # synthetic file handle
w32(0x0302598C, 30)
w32(0x03025990, 18)
w32(0x03025948, callback | 1)
w32(0x03025994, 0)  # screen x
w32(0x03025998, 0)  # screen y
w32(0x030247E4, 0)  # first row
w32(0x030247F0, 30)  # width
w32(0x03024800, 18)  # row count


def intercept(uc, addr, size, user):
    global cursor
    if addr == callback:
        dest = uc.reg_read(UC_ARM_REG_R0)
        count = uc.reg_read(UC_ARM_REG_R1)
        assert uc.reg_read(UC_ARM_REG_R2) == 1 and count <= 4096
        block = jpeg[cursor:cursor + count]
        cursor += len(block)
        if block:
            uc.mem_write(dest, block)
        uc.reg_write(UC_ARM_REG_R0, len(block))
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    elif addr == 0x0306333E:
        args = [uc.reg_read(reg) for reg in (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                             UC_ARM_REG_R2, UC_ARM_REG_R3)]
        mode, ptr = struct.unpack('<II', uc.mem_read(uc.reg_read(UC_ARM_REG_SP), 8))
        pixels = bytes(uc.mem_read(ptr, min(2 * args[2], 60)))
        blits.append((args, mode, ptr, pixels))
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))


u.hook_add(UC_HOOK_CODE, intercept)


def call(addr, r0):
    for reg, value in ((UC_ARM_REG_R0, r0), (UC_ARM_REG_R1, 0),
                       (UC_ARM_REG_R2, 0), (UC_ARM_REG_R3, 0),
                       (UC_ARM_REG_SP, 0x030F0000), (UC_ARM_REG_LR, end | 1)):
        u.reg_write(reg, value)
    u.emu_start(addr | 1, end, count=5000000)
    assert u.reg_read(UC_ARM_REG_PC) == end
    return u.reg_read(UC_ARM_REG_R0)


assert call(0x03085A4C, 9) == 1
# Manually trigger each service event and then the module-17 painter. The
# painter itself posts its next event; the scheduler is not emulated.
for _ in range(18):
    call(0x03080C92, 0x150)
    call(0x0307D546, 0)
assert len(blits) == 18
assert [entry[0][1] for entry in blits] == list(range(17)) + [16]
assert all(args[0] == 0 and args[2:] == [30, 1] and mode == 0x10 and ptr == row
           for args, mode, ptr, _ in blits)
assert all(len(pixels) == 60 for _, _, _, pixels in blits)
print('PASS: manually driven service and module-17 painter; final destination repeats in seeded scenario')

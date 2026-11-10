#!/usr/bin/env python3
"""Synthetic, instruction-level probes of V137 module 19's row path.

This seeds the decoded/interpolation working area; it does not decode a JPEG
or establish the file/metadata protocol or the correct production hooks.
Requires Unicorn and the SHA-pinned stock image (FOSI_STOCK_IMAGE supported).
"""
import hashlib
import os
from pathlib import Path
import struct
import sys

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
    UC_ARM_REG_R3, UC_ARM_REG_R11, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC)

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image

raw = Path(os.environ.get('FOSI_STOCK_IMAGE', ROOT / 'DP3_V137.img')).read_bytes()
assert hashlib.sha256(raw).hexdigest() == 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
im = Image(raw)
CTX = 0x030282A8
ROW = 0x03027DA8
RET = 0x030EF000


def instance():
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x03000000, 0x100000)
    for module in (0, 19):
        m = im.modules[module]
        for kind in ('code', 'data'):
            off, size = im.module_region(module, kind)
            if size:
                u.mem_write(m[kind + '_exec'], raw[off:off + size])
    return u


def write32(u, addr, val):
    u.mem_write(addr, struct.pack('<I', val))


def read32(u, addr):
    return struct.unpack('<I', u.mem_read(addr, 4))[0]


def call(u, pc, r0, r1=0, r2=0, r3=0):
    for reg, val in ((UC_ARM_REG_R0, r0), (UC_ARM_REG_R1, r1),
                     (UC_ARM_REG_R2, r2), (UC_ARM_REG_R3, r3),
                     (UC_ARM_REG_SP, 0x030F0000), (UC_ARM_REG_LR, RET | 1)):
        u.reg_write(reg, val)
    u.emu_start(pc | 1, RET, count=1000000)
    assert u.reg_read(UC_ARM_REG_PC) == RET, 'instruction limit or unexpected return'
    return u.reg_read(UC_ARM_REG_R0)


def row_case(source, expected, width, height):
    u = instance()
    desc = 0x03026CEC
    u.mem_write(desc + 6, struct.pack('<HH', width, height))
    write32(u, desc + 0x1C, 1)  # Seeded interpolation lines are ready.
    write32(u, desc + 0x20, CTX)
    for offset, value in ((0x0C, width), (0x10, height), (0x14, width),
                          (0x18, height), (0x24, 0), (0x28, ROW)):
        write32(u, CTX + offset, value)
    # The renderer's already-decoded input lines use 4 bytes per pixel.
    for i in range(4 * width):
        u.mem_write(0x0302AF78 + i * 4, bytes(source))
    for y in range(4):
        write32(u, 0x0302EF78 + y * 4, y)
    writes = []
    def observe(uc, addr, size, user):
        if addr == 0x030878AC:
            writes.append((uc.reg_read(UC_ARM_REG_R0),
                           uc.reg_read(UC_ARM_REG_R11),
                           uc.reg_read(UC_ARM_REG_R2)))
    u.hook_add(UC_HOOK_CODE, observe)
    for y in range(height):
        assert call(u, 0x03085A4C, 11) == (1 if y + 1 < height else 0)
        assert read32(u, CTX + 0x24) == y + 1
        assert bytes(u.mem_read(ROW, width * 2)) == struct.pack('<' + 'H' * width, *([expected] * width))
    assert writes == [(ROW, x, expected) for x in range(width)] * height


# Solid RGB channels in the seeded working-line format. The output is
# native little-endian RGB565, checked at the actual STRH instruction.
row_case((0, 255, 0, 0), 0xF800, 2, 2)
row_case((0, 0, 255, 0), 0x07E0, 3, 3)
row_case((0, 0, 0, 255), 0x001F, 2, 2)

# Dispatch command 9 with a missing file: it resets the row counter and
# returns failure, but leaves the old row bytes and cursor in memory.
u = instance()
write32(u, 0x03025944, 0xFFFFFFFF)
write32(u, CTX + 0x24, 11)
write32(u, CTX + 0x2C, 0x12345678)
u.mem_write(ROW, bytes.fromhex('aabbccdd'))
assert call(u, 0x03085A4C, 9) == 0
assert read32(u, CTX + 0x24) == 0
assert read32(u, CTX + 0x2C) == 0x12345678
assert bytes(u.mem_read(ROW, 4)) == bytes.fromhex('aabbccdd')

# A header/decode setup error reaches the same false return after resetting
# the row counter. Stub only that helper's failure; keep the dispatcher real.
u = instance()
write32(u, 0x03025944, 1)
write32(u, CTX + 0x24, 11)
write32(u, CTX + 0x2C, 0x12345678)
u.mem_write(ROW, bytes.fromhex('aabbccdd'))
def fail_header(uc, addr, size, user):
    if addr == 0x03086330:
        uc.reg_write(UC_ARM_REG_R0, 1)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE, fail_header)
assert call(u, 0x03085A4C, 9) == 0
assert read32(u, CTX + 0x24) == 0
assert read32(u, CTX + 0x2C) == 0x12345678
assert bytes(u.mem_read(ROW, 4)) == bytes.fromhex('aabbccdd')
print('PASS: synthetic RGB565 row reuse, completion and no-file/failure stale state')

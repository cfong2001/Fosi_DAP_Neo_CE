#!/usr/bin/env python3
"""Exercise the stock module-18 helper used by the module-19 picture path.

The helper is often described as returning bitmap pointers. It actually
orders two global *values* into the caller's output words. The test uses
small dimensions so the writes cannot be valid ARM SRAM pointers.
"""
import hashlib
import os
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR

raw = Path(os.environ.get('FOSI_STOCK_IMAGE', ROOT / 'DP3_V137.img')).read_bytes()
assert hashlib.sha256(raw).hexdigest() == 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
im = Image(raw)
m = im.modules[18]
off, size = im.module_region(18, 'code')

def run(first, second, a, b):
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x03000000, 0x100000)
    u.mem_write(m['code_exec'], raw[off:off + size])
    u.mem_write(0x0302598c, struct.pack('<II', first, second))
    u.reg_write(UC_ARM_REG_R0, 0x03020000)
    u.reg_write(UC_ARM_REG_R1, 0x03020004)
    u.reg_write(UC_ARM_REG_R2, a)
    u.reg_write(UC_ARM_REG_R3, b)
    u.reg_write(UC_ARM_REG_SP, 0x030f0000)
    u.reg_write(UC_ARM_REG_LR, 0x030ef001)
    u.emu_start(0x03080b55, 0x030ef000, count=100)
    return struct.unpack('<II', u.mem_read(0x03020000, 8)), u.reg_read(UC_ARM_REG_R0)

assert run(200, 100, 2, 1) == ((200, 100), 0)
assert run(200, 100, 1, 2) == ((100, 200), 1)
assert run(100, 200, 2, 1) == ((200, 100), 1)
print('PASS: module 18 helper orders synthetic scalar inputs')

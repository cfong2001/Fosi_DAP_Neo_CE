#!/usr/bin/env python3
"""Trace the stock player's full-background redraw and event dispatch.

The original event flag routines execute; display calls are intercepted.
This is a control-flow test, not evidence that a caller schedules the
player task, or that the LCD has repainted on physical hardware.
"""
from pathlib import Path
import hashlib
import os
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                               UC_ARM_REG_R3, UC_ARM_REG_LR, UC_ARM_REG_PC,
                               UC_ARM_REG_SP)

raw = Path(os.environ.get('FOSI_STOCK_IMAGE', ROOT / 'DP3_V137.img')).read_bytes()
if hashlib.sha256(raw).hexdigest() != 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef':
    raise ValueError('stock image SHA-256 mismatch')
im = Image(raw)


def run(post_redraw, media_state, color):
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x03000000, 0x100000)
    for i in (0, 27):
        off, size = im.module_region(i, 'code')
        u.mem_write(im.modules[i]['code_exec'], raw[off:off + size])
    event_base = 0x03023cf8
    if post_redraw:
        addr = event_base + (0x39 // 32) * 4
        u.mem_write(addr, struct.pack('<I', 1 << (0x39 % 32)))
    u.mem_write(0x030232a0 + 0x1a, bytes([media_state]))
    u.mem_write(0x03004400, struct.pack('<H', color))
    u.reg_write(UC_ARM_REG_SP, 0x030f0000)
    calls = []
    def intercept(uc, address, _size, _user):
        if address not in (0x030632fa, 0x03063700, 0x0306354a, 0x03063642):
            return
        args = [uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                        UC_ARM_REG_R2, UC_ARM_REG_R3)]
        if address == 0x030632fa:
            args.append(struct.unpack('<H', uc.mem_read(uc.reg_read(UC_ARM_REG_SP), 2))[0])
        calls.append((address, args))
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    u.hook_add(UC_HOOK_CODE, intercept)
    u.emu_start(0x0307ef7b, 0x0307f084, count=10000)
    title_word = struct.unpack('<I', u.mem_read(event_base + (0x4a // 32) * 4, 4))[0]
    return calls, bool(title_word & (1 << (0x4a % 32)))


def main():
    calls, title = run(False, 1, 0x1357)
    assert not calls and not title
    calls, title = run(True, 1, 0x1357)
    fills = [args for addr, args in calls if addr == 0x030632fa]
    assert fills == [[0, 0, 239, 319, 0x1357]] and title, (calls, title)
    calls, title = run(True, 1, 0x2468)
    fills = [args for addr, args in calls if addr == 0x030632fa]
    assert fills == [[0, 0, 239, 319, 0x2468]] and title
    calls, title = run(True, 0, 0x1357)
    assert not [args for addr, args in calls if addr == 0x030632fa]
    assert [args[0] for addr, args in calls if addr == 0x03063700] == [138] and title
    print('PASS: posted redraw reads the current ground and schedules title; no-media draws stock image')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Theater background on the player's no-art exits, composed image.

Runs module 27 and the merged tail of patches/full/out/DP3_V137_CE_full.img
under Unicorn from the two artwork-loader exits that skip artwork setup
(patches 0045 and 0046). Before each run the background cell holds a
previous track's derived color and sampling is armed. Each scenario checks
that the exit stores 0 to the art-present cell, restores the theme default
background, disarms sampling, requests one repaint, closes the file when
it was open, and returns through the loader's own frame. A second run with
the default already in place must not request a repaint.
"""
import hashlib
import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4,
                               UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
                               UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_SP,
                               UC_ARM_REG_LR, UC_ARM_REG_PC)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'tools'))
from rknano_image import Image  # noqa: E402

IMAGE = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    REPO / 'patches' / 'full' / 'out' / 'DP3_V137_CE_full.img'
STATE = 0x03023468
SAVEINFO = 0x030232A0
PALCELL = 0x030235B4
BGCELL = 0x03004400
EVWORD = 0x03023CFC
EVMASK = 0x02000000
CLOSE = 0x03058E8E
ART_CELL = 0x030E3000
HANDLE_CELL = 0x030E3010
DONE = 0x030E1000
EXIT_CLOSE, EXIT_OPEN = 0x0307E972, 0x0307E96C
DARK_DEFAULT = 0x10A2
LIGHT_DEFAULT = 0xEF5D
STALE = 0x7000


def machine(raw, light):
    image = Image(raw)
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x03000000, 0x100000)
    for mod in (0, 27):
        for kind in ('code', 'data'):
            off, ln = image.module_region(mod, kind)
            u.mem_write(image.modules[mod][kind + '_exec'], raw[off:off + ln])
    u.mem_write(SAVEINFO + 0x2D8, bytes([1 if light else 0]))
    u.mem_write(PALCELL, struct.pack('<H', LIGHT_DEFAULT))
    return u


def run_exit(u, entry, background, handle=0x85):
    u.mem_write(BGCELL, struct.pack('<H', background))
    u.mem_write(EVWORD, struct.pack('<I', 0x00000010))
    u.mem_write(STATE + 25, b'\x05')              # armed and latched
    u.mem_write(ART_CELL, struct.pack('<I', 1))
    u.mem_write(HANDLE_CELL, struct.pack('<I', handle))
    closed = []
    fills = []

    def hook(uc, address, size, data):
        if address in (0x030632FA, 0x03062CEE):
            if address == 0x030632FA:
                fills.append(tuple(uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif address == CLOSE:
            closed.append(uc.reg_read(UC_ARM_REG_R0) & 0xFFFFFFFF)
            uc.reg_write(UC_ARM_REG_R0, 0)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    h = u.hook_add(UC_HOOK_CODE, hook)
    # The loader's frame: push.w {r3, r4, r5, r6, r7, r8, sb, lr}.
    saved = [0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, DONE | 1]
    sp = 0x030E0000 - 0x40
    u.mem_write(sp, struct.pack('<8I', *saved))
    for reg, value in ((UC_ARM_REG_R4, 0), (UC_ARM_REG_R5, 0x5555),
                       (UC_ARM_REG_R6, ART_CELL), (UC_ARM_REG_R8, HANDLE_CELL),
                       (UC_ARM_REG_SP, sp), (UC_ARM_REG_LR, 0xDEAD0001)):
        u.reg_write(reg, value)
    u.emu_start(entry | 1, DONE, count=50000)
    u.hook_del(h)
    regs = [u.reg_read(r) for r in (UC_ARM_REG_R3, UC_ARM_REG_R4,
                                     UC_ARM_REG_R5, UC_ARM_REG_R6,
                                     UC_ARM_REG_R7, UC_ARM_REG_R8,
                                     UC_ARM_REG_R9)]
    return {
        'pc': u.reg_read(UC_ARM_REG_PC),
        'sp': u.reg_read(UC_ARM_REG_SP) - sp,
        'regs': regs,
        'background': struct.unpack('<H', u.mem_read(BGCELL, 2))[0],
        'event': struct.unpack('<I', u.mem_read(EVWORD, 4))[0],
        'flags': u.mem_read(STATE + 25, 1)[0],
        'art': struct.unpack('<I', u.mem_read(ART_CELL, 4))[0],
        'handle': struct.unpack('<I', u.mem_read(HANDLE_CELL, 4))[0],
        'closed': closed,
        'fills': fills,
    }


def main():
    raw = IMAGE.read_bytes()
    print(f'image sha256 {hashlib.sha256(raw).hexdigest()}')
    for light, default in ((False, DARK_DEFAULT), (True, LIGHT_DEFAULT)):
        theme = 'light' if light else 'dark'
        for entry, label in ((EXIT_CLOSE, 'no picture'),
                             (EXIT_OPEN, 'file did not open')):
            u = machine(raw, light)
            got = run_exit(u, entry, STALE)
            assert got['pc'] == DONE and got['sp'] == 32, got
            assert got['regs'] == [0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99], got
            assert got['art'] == 0, got
            assert got['fills'] and all(48 <= x0 <= x1 <= 191 and 36 <= y0 <= y1 <= 179 for x0,y0,x1,y1 in got['fills']), got['fills']
            assert got['background'] == default, hex(got['background'])
            assert got['event'] == 0x10 | EVMASK, hex(got['event'])
            assert got['flags'] == 0, got['flags']
            if entry == EXIT_CLOSE:
                # sxtb of the handle byte, then the stock close; r5 is
                # stored back to the handle cell afterwards
                assert got['closed'] == [0xFFFFFF85], got['closed']
                assert got['handle'] == 0x5555, hex(got['handle'])
            else:
                assert got['closed'] == [], got['closed']
            again = run_exit(machine(raw, light), entry, default)
            assert again['background'] == default
            assert again['event'] == 0x10, hex(again['event'])
            print(f'PASS {theme}, {label}: background {STALE:#06x} -> '
                  f'{default:#06x}, one repaint, sampling disarmed, frame intact')
    print('ALL PASS: theater no-art exits')


if __name__ == '__main__':
    main()

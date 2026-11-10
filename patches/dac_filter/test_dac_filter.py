#!/usr/bin/env python3
"""Run the DAC init's filter selection under Unicorn for stock and for
each --dac-filter build, and check the value written to CS43198
register 0x090000 (PCM Filter Option).

The emulated range is the original module 0 code from 0x0305180C (the
load of the settings base) to 0x03051866 (the first instruction after
the five mode branches). dac_write (0x03060C4C) is the only stub: it
records (register, value) and returns. Everything between, the
settings-byte loads, the compares and the immediates, is the firmware's
own Thumb code.

For every image the settings byte at 0x030232A0+0x2E3 is set to 0..5.
Expected: modes 1..4 write stock's values in every image; mode 0 writes
0x02 in stock and the selected filter's value in a variant; mode 5
writes nothing (stock has no branch for it).

Usage: python3 test_dac_filter.py [STOCK_IMAGE]
Needs unicorn. Builds byte-patch-only images in memory; writes nothing.
"""
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / 'patches' / 'framework'))
sys.path.insert(0, str(REPO / 'tools'))
import build as fw  # noqa: E402
from rknano_image import Image  # noqa: E402
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_CODE  # noqa: E402
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_LR,  # noqa: E402
                               UC_ARM_REG_PC, UC_ARM_REG_SP)

START, END = 0x0305180C, 0x03051866
DAC_WRITE = 0x03060C4C
MODE_BYTE = 0x030232A0 + 0x2E3
FILTER_REG = 0x090000
STOCK_VALUES = {0: 0x02, 1: 0x42, 2: 0x82, 3: 0xC2, 4: 0x22}
VARIANTS = {'fast-linear-phase': 0x42, 'slow-low-latency': 0x82,
            'slow-linear-phase': 0xC2, 'nos': 0x22}


def filter_writes(raw, mode):
    img = Image(raw)
    m0 = img.modules[0]
    code_off, _ = img.module_region(0, 'code')
    code = raw[code_off:code_off + m0['code_len']]
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
    uc.mem_map(0x03050000, 0x2C000)
    uc.mem_write(0x03050000, code)
    uc.mem_map(0x03020000, 0x8000)        # SAVEINFO live struct region
    uc.mem_map(0x03003000, 0x1000)        # stack
    uc.reg_write(UC_ARM_REG_SP, 0x03003F00)
    uc.mem_write(MODE_BYTE, bytes([mode]))
    writes = []

    def hook(uc, address, size, _):
        if address == DAC_WRITE:
            writes.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    uc.hook_add(UC_HOOK_CODE, hook)
    uc.emu_start(START | 1, END, count=200)
    return [(r, v) for r, v in writes if r == FILTER_REG]


def main():
    stock_path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / 'DP3_V137.img'
    stock = stock_path.read_bytes()
    base = fw.load_manifest(REPO / 'patches' / 'framework' / 'patches' / 'manifest.txt')
    images = {'stock': (stock, 0x02)}
    for name, value in VARIANTS.items():
        out, _ = fw.build_image(stock, base + [fw.dac_filter_patch(name)], fw.DEFAULT_BUILD_DATE)
        images[name] = (out, value)
    failures = 0
    print(f'{"image":<20}' + ''.join(f'  mode {m}' for m in range(6)))
    for name, (raw, mode0) in images.items():
        row = []
        for mode in range(6):
            got = filter_writes(raw, mode)
            want = [] if mode == 5 else [(FILTER_REG, mode0 if mode == 0 else STOCK_VALUES[mode])]
            ok = got == want
            failures += not ok
            row.append(('  ' + (f'0x{got[0][1]:02X}' if got else ' -- ') + ('' if ok else '!')).ljust(8))
        print(f'{name:<20}' + ''.join(row))
    if failures:
        raise SystemExit(f'FAIL: {failures} case(s) wrote the wrong filter value')
    print('OK: mode 0 writes the selected filter; modes 1-4 keep stock values; mode 5 writes none')


if __name__ == '__main__':
    main()

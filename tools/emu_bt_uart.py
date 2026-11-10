#!/usr/bin/env python3
"""Run the stock Bluetooth UART set-up under Unicorn and log every
peripheral register it writes.

Stock calls the generic UART configure routine 0x0305654E with
(r0 = 3, r1 = 115200, r2 = 8, r3 = 0, stack = 2) from every Bluetooth
power-on path (patches/ui_features/build/evidence/bt_side_effects.md,
item 2). This script runs that routine from its entry. Its leaf
helpers execute as stock code: the pin-group select 0x030528D6, the
pin-mux helper 0x030526F8 and the UART hardware init 0x0305134C. Every
other call is stubbed to return 0 and recorded, because those touch
clocks, delays and interrupt registration, which this check does not
need.

Peripheral space (0x40000000-0x5FFFFFFF) is plain RAM with a write
hook, so the log shows the exact (address, value) pairs stock produces.
The script checks the UART1 divisor latch and the pin mux against
NeoPod's independent driver (analysis/neopod_xref.md B8) and the TRM's
baud formula, baud = sclk / (16 x divisor).

Usage: python3 tools/emu_bt_uart.py [STOCK_IMAGE]   (needs unicorn)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rknano_image import Image  # noqa: E402
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_CODE, UC_HOOK_MEM_WRITE  # noqa: E402
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,  # noqa: E402
                               UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC)

ENTRY = 0x0305654E
RUN_AS_STOCK = {0x030528D6, 0x030526F8, 0x0305134C}
UART1 = 0x400B0000
SENTINEL = 0x03050000      # return address for the top-level call


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / 'DP3_V137.img'
    raw = path.read_bytes()
    img = Image(raw)
    m0 = img.modules[0]
    code_off, _ = img.module_region(0, 'code')
    data_off, _ = img.module_region(0, 'data')
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
    uc.mem_map(0x03000000, 0x90000)                  # SYSRAM0 + SYSRAM1
    uc.mem_write(0x03050000, raw[code_off:code_off + m0['code_len']])
    uc.mem_write(m0['data_exec'], raw[data_off:data_off + m0['data_len']])
    uc.mem_map(0x40000000, 0x20000000)               # peripherals as RAM
    sp = 0x03003F00
    uc.mem_write(sp, (2).to_bytes(4, 'little'))      # 5th argument
    uc.reg_write(UC_ARM_REG_SP, sp)
    for reg, val in ((UC_ARM_REG_R0, 3), (UC_ARM_REG_R1, 115200),
                     (UC_ARM_REG_R2, 8), (UC_ARM_REG_R3, 0)):
        uc.reg_write(reg, val)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL | 1)

    writes, stubbed = [], []
    calls_seen = set()

    def on_write(uc, access, address, size, value, _):
        if 0x40000000 <= address < 0x60000000:
            writes.append((address, value & ((1 << (8 * size)) - 1)))

    def on_code(uc, address, size, _):
        if address == SENTINEL:
            uc.emu_stop()
            return
        # stub any call target outside the stock leaves we execute
        lr = uc.reg_read(UC_ARM_REG_LR)
        if address in calls_seen or address == ENTRY or address in RUN_AS_STOCK:
            return
        if address == (lr & ~1) - 4 or address == (lr & ~1) - 2:
            return
        # a function entry is reached by bl: detect by LR pointing just past a bl
        try:
            prev = bytes(uc.mem_read((lr & ~1) - 4, 4))
        except Exception:
            return
        hw1 = int.from_bytes(prev[0:2], 'little')
        hw2 = int.from_bytes(prev[2:4], 'little')
        is_bl = (hw1 & 0xF800) == 0xF000 and (hw2 & 0xD000) == 0xD000
        if is_bl and address not in RUN_AS_STOCK and address != ENTRY:
            target = bl_target((lr & ~1) - 4, hw1, hw2)
            if target == address:
                stubbed.append(address)
                uc.reg_write(UC_ARM_REG_R0, 0)
                uc.reg_write(UC_ARM_REG_PC, lr)

    uc.hook_add(UC_HOOK_MEM_WRITE, on_write)
    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.emu_start(ENTRY | 1, 0, count=20000)

    for addr, val in writes:
        print(f'  write {addr:#010x} = {val:#010x}')
    print('stubbed calls:', ', '.join(sorted({f'{a:#010x}' for a in stubbed})))

    last = {}
    for addr, val in writes:
        last.setdefault(addr, []).append(val)
    dll = last.get(UART1 + 0x00, [None])[-1]
    dlh = last.get(UART1 + 0x04, [None])[-1]
    lcr = last.get(UART1 + 0x0C, [])
    grf_bc = [v for a, v in writes if a & 0xFFFF == 0x00BC and a >> 16 == 0x5001]
    checks = {
        'UART1 divisor latch low = 13': dll == 13,
        'UART1 divisor latch high = 0': dlh == 0,
        'UART1 LCR DLAB set then cleared': any(v & 0x80 for v in lcr) and not (lcr[-1] & 0x80),
        'GRF+0xBC = 0x02000000 (UART1 pin group A)': 0x02000000 in grf_bc,
    }
    for name, ok in checks.items():
        print(('PASS ' if ok else 'FAIL ') + name)
    if dll:
        print(f'baud with a 24 MHz UART clock: 24e6 / (16 x {dll}) = {24e6 / (16 * dll):,.0f} '
              f'({(24e6 / (16 * dll) / 115200 - 1) * 100:+.2f}% from 115,200)')
    if not all(checks.values()):
        raise SystemExit(1)


def bl_target(pc, hw1, hw2):
    s = (hw1 >> 10) & 1
    imm10 = hw1 & 0x3FF
    j1, j2 = (hw2 >> 13) & 1, (hw2 >> 11) & 1
    imm11 = hw2 & 0x7FF
    i1, i2 = 1 - (j1 ^ s), 1 - (j2 ^ s)
    off = (s << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm11 << 1)
    if s:
        off -= 1 << 25
    return pc + 4 + off


if __name__ == '__main__':
    main()

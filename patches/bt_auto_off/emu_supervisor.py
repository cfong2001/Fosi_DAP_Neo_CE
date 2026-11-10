#!/usr/bin/env python3
"""Run module 0's Bluetooth supervisor (0x03065FD4) under Unicorn and
report whether it switches Bluetooth off.

The supervisor runs from the system loop. While Bluetooth is on
(SAVEINFO +0x2D4 = 1) and no device is connected (+0x2D3 = 0), it
compares the 10 ms tick at 0x03023298 against the timestamp at
0x03004168+0x10; past the limit it clears event flag 0x1CB, clears +0x2D3 and
+0x2D4 and drives the module's power pin low. This harness runs the
whole function from its entry with every call stubbed to return 0, and
reports the two SAVEINFO bytes afterwards.

Usage: python3 emu_supervisor.py [IMAGE]          (prints a table)
       import and call auto_off(raw, elapsed, connected)
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tools'))
from rknano_image import Image  # noqa: E402
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_CODE  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC  # noqa: E402

ENTRY = 0x03065FD4
SAVEINFO = 0x030232A0
TICK = 0x03023298
STATE = 0x03004168          # supervisor struct; +0x10 = last-connected timestamp
SENTINEL = 0x03050000
T0 = 100000


def _bl_target(pc, hw1, hw2):
    s = (hw1 >> 10) & 1
    j1, j2 = (hw2 >> 13) & 1, (hw2 >> 11) & 1
    off = (s << 24) | ((1 - (j1 ^ s)) << 23) | ((1 - (j2 ^ s)) << 22) \
        | ((hw1 & 0x3FF) << 12) | ((hw2 & 0x7FF) << 1)
    return pc + 4 + off - ((1 << 25) if s else 0)


def auto_off(raw, elapsed, connected=0):
    """Return (+0x2D4, +0x2D3, flag 0x1CB cleared) after one supervisor
    pass with Bluetooth on, `connected` in +0x2D3 and `elapsed` ticks
    since the last connected timestamp."""
    img = Image(raw)
    m0 = img.modules[0]
    code_off, _ = img.module_region(0, 'code')
    data_off, _ = img.module_region(0, 'data')
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
    uc.mem_map(0x03000000, 0x90000)
    uc.mem_write(0x03050000, raw[code_off:code_off + m0['code_len']])
    uc.mem_write(m0['data_exec'], raw[data_off:data_off + m0['data_len']])
    uc.mem_map(0x40000000, 0x20000000)
    uc.mem_write(SAVEINFO + 0x2D3, bytes([connected, 1]))
    uc.mem_write(TICK, (T0 + elapsed).to_bytes(4, 'little'))
    uc.mem_write(STATE + 0x10, T0.to_bytes(4, 'little'))
    uc.reg_write(UC_ARM_REG_SP, 0x03003F00)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL | 1)
    events = []

    def on_code(uc, address, size, _):
        if address == SENTINEL:
            uc.emu_stop()
            return
        lr = uc.reg_read(UC_ARM_REG_LR) & ~1
        if address == ENTRY:
            return
        try:
            hw = bytes(uc.mem_read(lr - 4, 4))
        except Exception:
            return
        h1, h2 = int.from_bytes(hw[:2], 'little'), int.from_bytes(hw[2:], 'little')
        if (h1 & 0xF800) == 0xF000 and (h2 & 0xD000) == 0xD000 \
                and _bl_target(lr - 4, h1, h2) == address:
            events.append((address, uc.reg_read(UC_ARM_REG_R0)))
            uc.reg_write(UC_ARM_REG_R0, 0)
            uc.reg_write(UC_ARM_REG_PC, lr | 1)

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.emu_start(ENTRY | 1, 0, count=5000)
    on, link = bytes(uc.mem_read(SAVEINFO + 0x2D3, 2))[::-1]
    cleared = any(addr == 0x0306727E and r0 == 0x1CB for addr, r0 in events)
    return on, link, cleared


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / 'DP3_V137.img'
    raw = path.read_bytes()
    print(f'{"elapsed":>25}  {"connected":>9}  Bluetooth after')
    for connected in (0, 1):
        for elapsed in (0, 29999, 30001, 59999, 60001, 1000000):
            on, _, cleared = auto_off(raw, elapsed, connected)
            print(f'{elapsed:>7} ticks ({elapsed / 100:>8.2f} s)  {connected:>9}  {"on" if on else "OFF (flag 0x1CB cleared)" if cleared else "OFF"}')


if __name__ == '__main__':
    main()

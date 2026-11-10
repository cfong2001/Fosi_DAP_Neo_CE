#!/usr/bin/env python3
"""Unicorn emulation of the patched dispatcher return path (patch
0032-tail) against the scratch tail image: the Bluetooth blob
relinked at its gap-tail base, reached through the regenerated
dispatcher branch at 0x03061E5E.

This is the UI build's emu_bt.py suite, unchanged in cases and
checks, pointed at the tail image. delay_ms (0x03064944) is
intercepted and recorded, as in the original: its busy loop derives
its count from a clock word that reads 0 in this bare map. Every
other instruction runs for real.
"""
import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_LITTLE_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *

HERE = Path(__file__).resolve().parent
TB = HERE.parent
WS = TB.parents[1]
IMG = TB / 'scratch' / 'out_tail.img'

RAM_BASE, RAM_SIZE = 0x03000000, 0x100000
MMIO1_BASE, MMIO1_SIZE = 0x40000000, 0x400000
MMIO2_BASE, MMIO2_SIZE = 0x60000000, 0x400000
MMIO3_BASE, MMIO3_SIZE = 0x50000000, 0x1000000
MMIO4_BASE, MMIO4_SIZE = 0xE0000000, 0x100000
SAVEINFO = 0x030232A0
SI_ON, SI_MODE = 0x2D4, 0x2D3
BITMAP = 0x03023CF8
RESP_BUF = 0x0300642C
VER_BYTE = 0x03023124
STATUS_BYTE = 0x0300411C
B416C, B416E, B416F = 0x0300416C, 0x0300416E, 0x0300416F
TICK_COPY, TICK_SRC = 0x03004174, 0x03023298
DELAY_MS = 0x03064944
HOOK_SITE = 0x03061E5E
RET_ADDR = 0x030F8000
FRAME = 0x030E0000


def module0_regions(img_path):
    sys.path.insert(0, str(WS / 'repo' / 'tools'))
    import rknano_image as rk
    img = rk.Image(open(img_path, 'rb').read())
    m = img.modules[0]
    regions = {}
    for kind in ('code', 'data'):
        off, size = img.module_region(0, kind)
        regions[kind] = (m[kind + '_exec'], img.raw[off:off + size])
    return regions


class Run:
    def __init__(self, regions):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_LITTLE_ENDIAN)
        uc = self.uc
        uc.mem_map(RAM_BASE, RAM_SIZE)
        uc.mem_map(MMIO1_BASE, MMIO1_SIZE)
        uc.mem_map(MMIO2_BASE, MMIO2_SIZE)
        uc.mem_map(MMIO3_BASE, MMIO3_SIZE)
        uc.mem_map(MMIO4_BASE, MMIO4_SIZE)
        for base, blob in regions.values():
            uc.mem_write(base, blob)
        uc.mem_write(RET_ADDR, bytes.fromhex('fee7'))
        self.writes = []
        self.delay_calls = []
        self.reached = False
        uc.hook_add(UC_HOOK_CODE, self._code)
        uc.hook_add(UC_HOOK_MEM_WRITE, self._memw)

    def _code(self, uc, address, size, _):
        if address == DELAY_MS:
            self.delay_calls.append(uc.reg_read(UC_ARM_REG_R0))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif address == RET_ADDR:
            self.reached = True
            uc.emu_stop()

    def _memw(self, uc, access, address, size, value, _):
        if (MMIO1_BASE <= address < MMIO1_BASE + MMIO1_SIZE or
                MMIO2_BASE <= address < MMIO2_BASE + MMIO2_SIZE or
                MMIO3_BASE <= address < MMIO3_BASE + MMIO3_SIZE or
                SAVEINFO <= address < SAVEINFO + 0x300 or
                0x03004100 <= address < 0x03004200 or
                address in (VER_BYTE, TICK_COPY)):
            self.writes.append((address, size, value))

    def flag_word(self, flag):
        return BITMAP + 4 * (flag >> 5), flag & 31

    def set_flag(self, flag):
        addr, bit = self.flag_word(flag)
        cur = struct.unpack('<I', self.uc.mem_read(addr, 4))[0]
        self.uc.mem_write(addr, struct.pack('<I', cur | (1 << bit)))

    def get_flag(self, flag):
        addr, bit = self.flag_word(flag)
        cur = struct.unpack('<I', self.uc.mem_read(addr, 4))[0]
        return (cur >> bit) & 1

    def byte(self, addr):
        return self.uc.mem_read(addr, 1)[0]

    def word(self, addr):
        return struct.unpack('<I', self.uc.mem_read(addr, 4))[0]

    def run(self, event_word):
        uc = self.uc
        sent = {r: 0x5E000000 + 0x111 * i for i, r in enumerate(
            [UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8,
             UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_R12])}
        frame = [0x44444444] + [sent[r] for r in
                 [UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8,
                  UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_R12]]
        frame.append(RET_ADDR | 1)
        uc.mem_write(FRAME, b''.join(struct.pack('<I', w) for w in frame))
        uc.reg_write(UC_ARM_REG_SP, FRAME)
        uc.reg_write(UC_ARM_REG_R4, event_word)
        for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3):
            uc.reg_write(r, 0xDEAD0000)
        uc.reg_write(UC_ARM_REG_LR, 0x03050001)
        uc.emu_start(HOOK_SITE | 1, RET_ADDR, count=20_000_000)
        self.reached = (uc.reg_read(UC_ARM_REG_PC) & ~1) == RET_ADDR
        regs = {r: uc.reg_read(r) for r in sent}
        return {
            'reached': self.reached,
            'r0': uc.reg_read(UC_ARM_REG_R0),
            'r4': uc.reg_read(UC_ARM_REG_R4),
            'restored': all(regs[r] == sent[r] for r in sent),
            'frame_r4_restored': uc.reg_read(UC_ARM_REG_R4) == 0x44444444,
            'delay_total': sum(self.delay_calls),
            'delay_calls': list(self.delay_calls),
            'mmio_writes': [w for w in self.writes
                            if MMIO1_BASE <= w[0] < MMIO1_BASE + MMIO1_SIZE
                            or MMIO2_BASE <= w[0] < MMIO2_BASE + MMIO2_SIZE
                            or MMIO3_BASE <= w[0] < MMIO3_BASE + MMIO3_SIZE],
        }


def gpio_port2(uc):
    tbl = struct.unpack('<I', uc.mem_read(0x0305622C, 4))[0]
    base = struct.unpack('<I', uc.mem_read(tbl + 8, 4))[0]
    return base, base + 4


def case(regions, name, event, setup, checks):
    run = Run(regions)
    setup(run)
    lvl_addr, dir_addr = gpio_port2(run.uc)
    out = run.run(event)
    lvl = run.word(lvl_addr)
    print(f'--- {name} (event 0x{event:08X}) ---')
    print(f'    reached return pad: {out["reached"]}, r0 = {out["r0"]:#x}, '
          f'frame restored: {out["restored"] and out["frame_r4_restored"]}')
    print(f'    delay total {out["delay_total"]} ms in {len(out["delay_calls"])} calls; '
          f'MMIO writes: {len(out["mmio_writes"])}; port2 level reg @{lvl_addr:#x} = {lvl:#010x}')
    ok = True
    for desc, cond in checks(run, out, lvl):
        print(f'    [{"PASS" if cond else "FAIL"}] {desc}')
        ok = ok and cond
    print(f'    => {"PASS" if ok and out["reached"] and out["restored"] else "FAIL"}')
    return ok and out['reached'] and out['restored']


def main():
    regions = module0_regions(IMG)
    results = []

    def setup_on(run):
        run.uc.mem_write(SAVEINFO + SI_ON, b'\x00')
        run.uc.mem_write(RESP_BUF, b'CV15' + b'\x00' * 12)
        run.set_flag(0x1B2)
        run.uc.mem_write(TICK_SRC, struct.pack('<I', 0x11223344))

    results.append(case(
        regions, 'long-press Power, BT off -> on (banner CV15)',
        0x20000001, setup_on,
        lambda r, o, lvl: [
            ('return value 0 (event swallowed)', o['r0'] == 0),
            ('SAVEINFO +0x2D4 == 1 (on)', r.byte(SAVEINFO + SI_ON) == 1),
            ('result byte 0x03023124 == 5', r.byte(VER_BYTE) == 5),
            ('status byte == 0', r.byte(STATUS_BYTE) == 0),
            ('port2 level bit 7 set', (lvl >> 7) & 1 == 1),
            ('0x0300416C == 1, 0x0300416E/6F == 0',
             (r.byte(B416C), r.byte(B416E), r.byte(B416F)) == (1, 0, 0)),
            ('tick copy == tick source', r.word(TICK_COPY) == 0x11223344),
            ('flag 0x123 posted', r.get_flag(0x123) == 1),
            ('flag 0x1B8 posted (cmd send)', r.get_flag(0x1B8) == 1),
            ('delay: 100 settle + 10 success (+1 inside stock UART init)',
             o['delay_total'] == 111 and o['delay_calls'].count(100) == 1
             and o['delay_calls'].count(10) == 1),
        ]))

    def setup_off(run):
        run.uc.mem_write(SAVEINFO + SI_ON, b'\x01')
        run.uc.mem_write(SAVEINFO + SI_MODE, b'\x01')

    results.append(case(
        regions, 'long-press Power, BT on -> off',
        0x20000001, setup_off,
        lambda r, o, lvl: [
            ('return value 0 (event swallowed)', o['r0'] == 0),
            ('SAVEINFO +0x2D4 == 0 (off)', r.byte(SAVEINFO + SI_ON) == 0),
            ('SAVEINFO +0x2D3 == 0', r.byte(SAVEINFO + SI_MODE) == 0),
            ('port2 level bits 7/17/16 all 0', lvl & ((1 << 7) | (1 << 17) | (1 << 16)) == 0),
            ('delay total == 200', o['delay_total'] == 200),
            ('no flag 0x123 post', r.get_flag(0x123) == 0),
        ]))

    def setup_timeout(run):
        run.uc.mem_write(SAVEINFO + SI_ON, b'\x00')
        run.uc.mem_write(RESP_BUF, b'\x00' * 16)

    results.append(case(
        regions, 'long-press Power, BT off -> on, banner never arrives',
        0x20000001, setup_timeout,
        lambda r, o, lvl: [
            ('return value 0 (event swallowed)', o['r0'] == 0),
            ('SAVEINFO +0x2D4 back to 0 (timeout)', r.byte(SAVEINFO + SI_ON) == 0),
            ('status byte == 7 (timeout)', r.byte(STATUS_BYTE) == 7),
            ('port2 level bit 7 back to 0', (lvl >> 7) & 1 == 0),
            ('delay: 100 + 5000x1 poll + 10 (+1 inside stock UART init)',
             o['delay_total'] == 5111),
            ('no post-on writes (0x0300416C untouched 0)', r.byte(B416C) == 0),
        ]))

    for ev, nm in [(0x10000001, 'T1 Power (short press)'),
                   (0x20000010, 'T2 other key'),
                   (0x40004000, 'T4 OK-release')]:
        def setup_none(run, ev=ev):
            run.uc.mem_write(SAVEINFO + SI_ON, b'\x00')
        results.append(case(
            regions, f'non-target event passes through: {nm}',
            ev, setup_none,
            lambda r, o, lvl, ev=ev: [
                ('return value == event word (not swallowed)', o['r0'] == ev),
                ('no MMIO writes', len(o['mmio_writes']) == 0),
                ('no delays', o['delay_total'] == 0),
                ('SAVEINFO +0x2D4 still 0', r.byte(SAVEINFO + SI_ON) == 0),
            ]))

    print()
    print('ALL PASS' if all(results) else 'SOME CASES FAILED')
    return 0 if all(results) else 1


if __name__ == '__main__':
    raise SystemExit(main())

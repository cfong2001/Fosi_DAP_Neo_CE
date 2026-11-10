#!/usr/bin/env python3
"""Unicorn emulation of the battery-profile blob (work/power_build).

Loads the compiled blob at its link base (0x030804AC, the module 32
segment extension) in a bare RAM map. The four stock callees
(TimerPeriodSet 0x030510A2, backlight apply 0x03064964, flag post
0x0306723C, saver 0x0306CA10) are intercepted with recording stubs
that return at once; everything in the blob itself runs for real,
including the defaults writer and the dispatch cave stubs, whose
stock continuation addresses are recorded as the run's exit point.

Cases (power_build.md):
  (a) magic absent: profiles_apply writes nothing and calls nothing.
  (b) three profiles with distinct entries: exact call sequence,
      SAVEINFO fields, and clock table B fields per policy.
  (c) selector cycle through the dispatch A cave: active id follows
      the presented option 1, 2, 0 and persists each time; the
      dispatch B cave and the non-profile fall-throughs behave.
  (d) first selection with magic absent: the defaults block is
      written exactly once; a later selection does not rewrite it.
"""
import struct
import subprocess
import sys
import hashlib
from pathlib import Path

from unicorn import (Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE,
                     UC_HOOK_MEM_WRITE)
from unicorn.arm_const import *

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent
BLOB = BUILD / 'out' / 'blob.bin'
ELF = BUILD / 'out' / 'profiles.elf'
REPO = BUILD.parents[2]
sys.path.insert(0, str(REPO / 'tools'))
import fosi_paths
from rknano_image import Image

STOCK_SHA256 = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'


def stock_segment():
    path = fosi_paths.stock_image_path(REPO)
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA256:
        raise ValueError('stock image does not match the pinned V137 SHA-256')
    im = Image(raw)
    off, length = im.module_region(0, 'code')
    return raw[off:off + length]

RAM_BASE, RAM_SIZE = 0x03000000, 0x100000
SAVEINFO = 0x030232A0
CLOCK_TAB = 0x03079824
EXT_BASE = 0x030804AC
SP = 0x030E0000
RET = 0x030F8000
REC = 0x030D0000  # fake settings item record for the cave tests

TIMER = 0x030510A2
BACKLIGHT = 0x03064964
FLAGPOST = 0x0306723C
SAVER = 0x0306CA10
STUBS = {TIMER: 'TimerPeriodSet', BACKLIGHT: 'BacklightApply',
         FLAGPOST: 'FlagPost', SAVER: 'Saver'}
CONTINUATIONS = {0x0307DF84: 'A:brightness', 0x0307DF8C: 'A:generic',
                 0x0307E010: 'B:brightness', 0x0307E198: 'B:exit'}

HZ = {'288M': 288000000, '240M': 240000000, '140M': 140000000,
      '72M': 72000000, '36M': 36000000}


def symbols():
    out = subprocess.run(['arm-none-eabi-nm', str(ELF)],
                         capture_output=True, text=True, check=True).stdout
    syms = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3:
            syms[parts[2]] = int(parts[0], 16)
    return syms


SYMS = symbols()
APPLY = SYMS['profiles_apply']
SELECT = SYMS['profile_select']
HOOK_A = SYMS['hook_dispatch_a']
HOOK_B = SYMS['hook_dispatch_b']
DEFAULTS = SYMS['profile_defaults']


class Run:
    def __init__(self):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        uc = self.uc
        uc.mem_map(RAM_BASE, RAM_SIZE)
        uc.mem_write(EXT_BASE, BLOB.read_bytes())
        # Stock clock table bytes (module 0 segment) so ids, PLL and
        # A fields start from their true values.
        seg0 = stock_segment()
        uc.mem_write(CLOCK_TAB, seg0[CLOCK_TAB - 0x03050000:
                                     CLOCK_TAB - 0x03050000 + 36 * 28])
        # Model the shipped state: clock v1 set rows 18..22 B fields
        # to 288 MHz (framework patches 0014..0018).
        for row in range(18, 23):
            for word in (5, 6):
                uc.mem_write(CLOCK_TAB + row * 28 + word * 4,
                             struct.pack('<I', HZ['288M']))
        uc.reg_write(UC_ARM_REG_SP, SP)
        self.calls = []       # (name, r0, r1, r2, r3, stack_arg)
        self.writes = []      # (addr, size, value) in watched ranges
        self.continuation = None
        uc.hook_add(UC_HOOK_CODE, self._code)
        uc.hook_add(UC_HOOK_MEM_WRITE, self._write)

    def _code(self, uc, address, size, _):
        if address in STUBS:
            r = [uc.reg_read(x) for x in
                 (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                  UC_ARM_REG_R3)]
            stack_arg = struct.unpack(
                '<I', uc.mem_read(uc.reg_read(UC_ARM_REG_SP), 4))[0]
            self.calls.append((STUBS[address], *r, stack_arg))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif address in CONTINUATIONS:
            self.continuation = CONTINUATIONS[address]
            uc.emu_stop()

    def _write(self, uc, access, address, size, value, _):
        if (SAVEINFO <= address < SAVEINFO + 0x400 or
                CLOCK_TAB <= address < CLOCK_TAB + 36 * 28):
            self.writes.append((address, size, value))

    # -- helpers -----------------------------------------------------
    def si(self, off, data=None):
        if data is None:
            return self.uc.mem_read(SAVEINFO + off, 1)[0]
        self.uc.mem_write(SAVEINFO + off, bytes([data]))

    def si_bytes(self, off, n):
        return bytes(self.uc.mem_read(SAVEINFO + off, n))

    def clock_b(self, row):
        base = CLOCK_TAB + row * 28
        core = struct.unpack('<I', self.uc.mem_read(base + 20, 4))[0]
        bus = struct.unpack('<I', self.uc.mem_read(base + 24, 4))[0]
        return core, bus

    def call(self, fn, r0=0, r4=0, r6=SAVEINFO):
        self.uc.reg_write(UC_ARM_REG_R0, r0)
        self.uc.reg_write(UC_ARM_REG_R4, r4)
        self.uc.reg_write(UC_ARM_REG_R6, r6)
        self.uc.reg_write(UC_ARM_REG_LR, RET)
        self.uc.emu_start(fn | 1, RET)

    def write_profile_area(self, active, entries, flags=1):
        hdr = bytes([0x50, 0x46, 1, active, flags, 0, 0, 0])
        self.uc.mem_write(SAVEINFO + 0x290, hdr + b''.join(
            bytes(e) for e in entries))


PASS, FAIL = [], []


def check(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    print(f"    [{'PASS' if cond else 'FAIL'}] {name}"
          + (f" -- {detail}" if detail and not cond else ''))


def case_a():
    print('--- (a) magic absent: apply is a no-op ---')
    r = Run()
    r.call(APPLY)
    check('no stock calls', r.calls == [], str(r.calls))
    check('no writes to SAVEINFO or the clock table', r.writes == [],
          str(r.writes[:4]))
    check('struct still all zero', r.si_bytes(0, 0x2B0) == bytes(0x2B0))


def case_b():
    print('--- (b) three profiles, distinct entries ---')
    # b0: Performance slot values but every lever live, cap A.
    r = Run()
    r.si(0x68, 0x03)
    r.write_profile_area(0, [
        [0, 5, 1, 6, 1, 0, 0, 0],
        [1, 0xFF, 0xFF, 0xFF, 0, 0, 0, 0],
        [1, 0xFF, 0xFF, 0xFF, 0, 0, 0, 0]])
    r.call(APPLY)
    names = [c[0] for c in r.calls]
    check('b0 call order: timer, backlight, flag, saver',
          names == ['TimerPeriodSet', 'BacklightApply', 'FlagPost',
                    'Saver'], str(names))
    check('b0 timer args (0, -, 400, 0, ns=0)',
          r.calls[0][1] == 0 and r.calls[0][3] == 400 and
          r.calls[0][4] == 0 and r.calls[0][5] == 0, str(r.calls[0]))
    check('b0 backlight arg is the level',
          r.calls[1][1] == 5, str(r.calls[1]))
    check('b0 flag post is 0xFB', r.calls[2][1] == 0xFB,
          str(r.calls[2]))
    check('b0 saver arg is 1 and saver is last',
          r.calls[3][1] == 1, str(r.calls[3]))
    check('b0 SAVEINFO fields written',
          (r.si(0x14), r.si(0x68), r.si(0x2D4)) == (5, 6, 1),
          str((r.si(0x14), r.si(0x68), r.si(0x2D4))))
    check('b0 cap A: rows 18..22 B = 240 MHz',
          all(r.clock_b(row) == (HZ['240M'], HZ['240M'])
              for row in range(18, 23)),
          str([r.clock_b(row) for row in range(18, 23)]))
    check('b0 cap A: EQ rows keep base values',
          [r.clock_b(row) for row in (23, 24, 25)] ==
          [(HZ['36M'],) * 2, (HZ['72M'],) * 2, (HZ['140M'],) * 2],
          str([r.clock_b(row) for row in (23, 24, 25)]))

    # b1: leave bytes honoured, EQ value equal to current (no post),
    # cap B.
    r = Run()
    r.si(0x68, 6)
    r.si(0x14, 5)
    r.si(0x2D4, 1)
    r.write_profile_area(1, [
        [0, 0xFF, 0xFF, 0xFF, 0, 0, 0, 0],
        [1, 0xFF, 0xFF, 6, 2, 0, 0, 0],
        [1, 0xFF, 0xFF, 0xFF, 0, 0, 0, 0]])
    r.call(APPLY)
    names = [c[0] for c in r.calls]
    check('b1 calls: timer and saver only',
          names == ['TimerPeriodSet', 'Saver'], str(names))
    check('b1 timer period 1000',
          r.calls[0][3] == 1000, str(r.calls[0]))
    check('b1 leave bytes: +0x14 and +0x2D4 untouched',
          (r.si(0x14), r.si(0x2D4)) == (5, 1),
          str((r.si(0x14), r.si(0x2D4))))
    check('b1 cap B: lossless 240 MHz, EQ capped at 72 MHz tier',
          all(r.clock_b(row) == (HZ['240M'], HZ['240M'])
              for row in range(18, 23)) and
          [r.clock_b(row) for row in (23, 24, 25)] ==
          [(HZ['36M'],) * 2, (HZ['72M'],) * 2, (HZ['72M'],) * 2],
          str([r.clock_b(row) for row in range(18, 26)]))

    # b2: policy 0 restores the base set over a dirtied table.
    r = Run()
    r.si(0x68, 0x00)
    for row in range(18, 23):
        for word in (5, 6):
            r.uc.mem_write(CLOCK_TAB + row * 28 + word * 4,
                           struct.pack('<I', HZ['240M']))
    r.uc.mem_write(CLOCK_TAB + 25 * 28 + 20, struct.pack('<I', HZ['72M']))
    r.uc.mem_write(CLOCK_TAB + 25 * 28 + 24, struct.pack('<I', HZ['72M']))
    r.write_profile_area(2, [
        [0, 0xFF, 0xFF, 0xFF, 0, 0, 0, 0],
        [1, 0xFF, 0xFF, 0xFF, 0, 0, 0, 0],
        [1, 1, 0, 4, 0, 0, 0, 0]])
    r.call(APPLY)
    names = [c[0] for c in r.calls]
    check('b2 call order: timer, backlight, flag, saver',
          names == ['TimerPeriodSet', 'BacklightApply', 'FlagPost',
                    'Saver'], str(names))
    check('b2 restore: rows 18..22 B = 288 MHz',
          all(r.clock_b(row) == (HZ['288M'], HZ['288M'])
              for row in range(18, 23)),
          str([r.clock_b(row) for row in range(18, 23)]))
    check('b2 restore: EQ rows back to 36/72/140 MHz',
          [r.clock_b(row) for row in (23, 24, 25)] ==
          [(HZ['36M'],) * 2, (HZ['72M'],) * 2, (HZ['140M'],) * 2],
          str([r.clock_b(row) for row in (23, 24, 25)]))
    seg0 = stock_segment()
    untouched = True
    for row in range(36):
        for word in range(7):
            off = CLOCK_TAB - 0x03050000 + row * 28 + word * 4
            want = struct.unpack('<I', seg0[off:off + 4])[0]
            if 18 <= row <= 22 and word in (5, 6):
                want = HZ['288M']
            got = struct.unpack(
                '<I', r.uc.mem_read(CLOCK_TAB + row * 28 + word * 4, 4))[0]
            if got != want:
                untouched = False
    check('b2 ids, PLL, A fields and other rows untouched', untouched)


def case_c():
    print('--- (c) selector cycle through the caves ---')
    r = Run()
    entries = [[1, 1, 0xFF, 0xFF, 0, 0, 0, 0],
               [1, 2, 0xFF, 0xFF, 0, 0, 0, 0],
               [1, 3, 0xFF, 0xFF, 0, 0, 0, 0]]
    r.write_profile_area(0, entries)

    def select(hook, chosen):
        r.uc.mem_write(REC + 5, bytes([chosen]))
        before = len([c for c in r.calls if c[0] == 'Saver'])
        r.continuation = None
        r.call(hook, r0=0xC5, r4=REC)
        savers = len([c for c in r.calls if c[0] == 'Saver'])
        return savers - before

    n = select(HOOK_A, 1)
    check('c select 1: active id 1, persisted once, applied (2)',
          (r.si(0x293), n, r.si(0x14)) == (1, 1, 2),
          str((r.si(0x293), n, r.si(0x14))))
    check('c select 1: exit via A generic post',
          r.continuation == 'A:generic', str(r.continuation))
    n = select(HOOK_A, 2)
    check('c select 2: active id 2, persisted once, applied (3)',
          (r.si(0x293), n, r.si(0x14)) == (2, 1, 3),
          str((r.si(0x293), n, r.si(0x14))))
    n = select(HOOK_A, 0)
    check('c select 0: active id 0, persisted once, applied (1)',
          (r.si(0x293), n, r.si(0x14)) == (0, 1, 1),
          str((r.si(0x293), n, r.si(0x14))))
    n = select(HOOK_B, 2)
    check('c B cave select 2: active id 2, exit via B epilogue',
          (r.si(0x293), n, r.continuation) == (2, 1, 'B:exit'),
          str((r.si(0x293), n, r.continuation)))

    for hook, item, want in ((HOOK_A, 0xC4, 'A:brightness'),
                             (HOOK_A, 0xAD, 'A:generic'),
                             (HOOK_B, 0xC4, 'B:brightness'),
                             (HOOK_B, 0xAD, 'B:exit')):
        calls_before, writes_before = len(r.calls), len(r.writes)
        r.continuation = None
        r.call(hook, r0=item, r4=REC)
        check(f'c fall-through item {item:#x} via {want}',
              r.continuation == want and
              len(r.calls) == calls_before and
              len(r.writes) == writes_before,
              str((r.continuation, len(r.calls), len(r.writes))))


def case_d():
    print('--- (d) first selection writes the defaults exactly once ---')
    r = Run()
    expected_entries = bytes(r.uc.mem_read(DEFAULTS, 24))
    r.uc.mem_write(REC + 5, bytes([2]))
    r.call(HOOK_A, r0=0xC5, r4=REC)
    area = r.si_bytes(0x290, 32)
    want = bytes([0x50, 0x46, 1, 2, 1, 0, 0, 0]) + expected_entries
    check('d defaults block written with chosen id 2',
          area == want, area.hex())
    area_writes = [w for w in r.writes
                   if SAVEINFO + 0x290 <= w[0] < SAVEINFO + 0x2B0]
    counts = {}
    for addr, size, _ in area_writes:
        for a in range(addr, addr + size):
            counts[a] = counts.get(a, 0) + 1
    check('d every profile-area byte written exactly once',
          len(counts) == 32 and all(v == 1 for v in counts.values()),
          str({hex(k): v for k, v in counts.items() if v != 1}))
    check('d exit via A generic post, saver called once',
          r.continuation == 'A:generic' and
          len([c for c in r.calls if c[0] == 'Saver']) == 1,
          str((r.continuation, r.calls)))
    # A later selection must not rewrite the entries.
    r.si(0x298, 0)  # user-changed entry 0 wheel byte, by hand
    r.uc.mem_write(REC + 5, bytes([1]))
    r.call(HOOK_A, r0=0xC5, r4=REC)
    check('d second selection keeps user entry edits, sets active 1',
          (r.si(0x298), r.si(0x293)) == (0, 1),
          str((r.si(0x298), r.si(0x293))))


def case_invalid():
    print('--- (e) invalid persisted fields do not reach stock consumers ---')
    r = Run()
    r.si(0x14, 3)
    r.si(0x68, 2)
    r.si(0x2D4, 1)
    r.write_profile_area(0, [[0, 6, 2, 7, 0, 0, 0, 0]] * 3)
    r.call(APPLY)
    check('invalid brightness, Bluetooth and EQ fields are ignored',
          (r.si(0x14), r.si(0x68), r.si(0x2D4)) == (3, 2, 1) and
          [c[0] for c in r.calls] == ['TimerPeriodSet', 'Saver'],
          str((r.calls, r.si(0x14), r.si(0x68), r.si(0x2D4))))


def main():
    case_a()
    case_b()
    case_c()
    case_d()
    case_invalid()
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())

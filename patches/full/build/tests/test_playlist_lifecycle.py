#!/usr/bin/env python3
"""Playlist playback through the real source 6 code of the composed image.

Runs module 0 of patches/full/out/DP3_V137_CE_full.img under Unicorn: the
playlist hooks in the merged tail, the hook sites 0041 to 0044, and the
stock source 6 initializer (0x0305D048) and step function (0x0305D124).
Only the folder iterator is modeled: reset (0x0305AA44) selects a folder's
first file and next (0x0305AA18) moves to the following file. The stock
count (0x03059D58 body) is modeled when a call falls through to it.

Each scenario asserts the folder (play context +0x34) and the 1-based file
ordinal the iterator ends on, which is what stock then opens. This covers
start, forward steps across folders, wrap at the end, a backward step at
the start, and the unarmed (stock folder play) path. It does not cover the
message path into module 33, repeat-folder mode, the decoder or hardware.
"""
import hashlib
import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                               UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR,
                               UC_ARM_REG_PC)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'tools'))
from rknano_image import Image  # noqa: E402

IMAGE = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    REPO / 'patches' / 'full' / 'out' / 'DP3_V137_CE_full.img'
STAGE = 0x0307BFB4
CTX = 0x03023980
TABLE = 0x03005714
RESET, NEXT = 0x0305AA44, 0x0305AA18
COUNT_BODY = 0x03059D5C            # stock count after the displaced push
FETCH_BODY = 0x0305B2C6            # stock fetch after the displaced push
RESOLVE_BODY = 0x03059DB0          # stock resolver after the displaced push
STOCK_FOLDER = 0x33333333
INIT, STEP = 0x0305D048, 0x0305D124
COMPANION_SITE = 0x0305B2C2
RET_START = 0x0307E065
DONE = 0x030E1000

RUNS = [(0x11111111, 5), (0x22222222, 4)]          # (cluster, files)
ENTRIES = [(2, 0), (0, 1), (3, 0)]                  # (0-based ordinal, run)
STOCK_COUNT = 9                                      # folder-tree length


def staging(armed):
    s = bytearray(552)
    s[0] = 1 if armed else 0
    s[1] = len(ENTRIES)
    struct.pack_into('<H', s, 2, 0xFFFF)
    s[6] = len(RUNS)
    for i, (cluster, files) in enumerate(RUNS):
        struct.pack_into('<IHH', s, 16 + 50 * i, cluster, files, 0)
        s[16 + 50 * i + 8:16 + 50 * i + 50] = bytes([0x40 + i]) * 42
    for i, (ordinal, run) in enumerate(ENTRIES):
        struct.pack_into('<HBB', s, 316 + 4 * i, ordinal, run, 0)
    return bytes(s)


class Player:
    def __init__(self, raw, armed, modules=(0,)):
        image = Image(raw)
        self.u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.u.mem_map(0x03000000, 0x100000)
        for mod in modules:
            for kind in ('code', 'data'):
                off, ln = image.module_region(mod, kind)
                self.u.mem_write(image.modules[mod][kind + '_exec'],
                                 raw[off:off + ln])
        self.u.mem_write(STAGE, staging(armed))
        self.w16(CTX + 0xF2, 6)            # source 6
        self.w16(CTX + 0x0A, 0)            # repeat mode
        self.w16(CTX + 0x0C, 0)            # shuffle off
        self.w16(CTX + 0xF4, 0)
        self.folder = None
        self.ordinal = 0
        self.log = []
        self.u.hook_add(UC_HOOK_CODE, self.model)

    def w16(self, a, v):
        self.u.mem_write(a, struct.pack('<H', v))

    def r16(self, a):
        return struct.unpack('<H', self.u.mem_read(a, 2))[0]

    def r32(self, a):
        return struct.unpack('<I', self.u.mem_read(a, 4))[0]

    def ret(self, value):
        self.u.reg_write(UC_ARM_REG_R0, value)
        self.u.reg_write(UC_ARM_REG_PC, self.u.reg_read(UC_ARM_REG_LR))

    def model(self, uc, address, size, data):
        if address == RESET:
            self.folder = self.r32(CTX + 0x34)
            self.ordinal = 1
            self.log.append('reset')
            self.ret(0)
        elif address == NEXT:
            self.ordinal += 1
            self.log.append('next')
            self.ret(0)
        elif address in (0x0306727E,):
            self.ret(0)                    # module 33 event clear
        elif address == RESOLVE_BODY:
            # stock resolver after its push.w {r4-r8, sb, sl, lr}
            sp = uc.reg_read(UC_ARM_REG_SP)
            lr = struct.unpack('<I', uc.mem_read(sp + 28, 4))[0]
            uc.reg_write(UC_ARM_REG_SP, sp + 32)
            out = uc.reg_read(UC_ARM_REG_R1)
            uc.mem_write(out, struct.pack('<I', STOCK_FOLDER))
            self.log.append('stock resolver')
            uc.reg_write(UC_ARM_REG_R0, 1)
            uc.reg_write(UC_ARM_REG_PC, lr)
        elif address == FETCH_BODY:
            self.log.append('stock fetch')
            uc.emu_stop()
        elif address == COUNT_BODY:
            # stock count after its push: unwind the push, return a length
            sp = uc.reg_read(UC_ARM_REG_SP)
            lr = struct.unpack('<I', uc.mem_read(sp + 20, 4))[0]
            uc.reg_write(UC_ARM_REG_SP, sp + 24)
            self.log.append('stock count')
            uc.reg_write(UC_ARM_REG_R0, STOCK_COUNT)
            uc.reg_write(UC_ARM_REG_PC, lr)

    def call(self, entry, r0, r1=0, r2=0, r3=0, lr=DONE | 1, stack=()):
        sp = 0x030E0000 - 0x40
        self.u.mem_write(sp, b''.join(struct.pack('<I', v) for v in stack)
                         or b'\0' * 4)
        for reg, v in ((UC_ARM_REG_R0, r0), (UC_ARM_REG_R1, r1),
                       (UC_ARM_REG_R2, r2), (UC_ARM_REG_R3, r3),
                       (UC_ARM_REG_SP, sp), (UC_ARM_REG_LR, lr)):
            self.u.reg_write(reg, v)
        self.u.emu_start(entry | 1, lr & ~1, count=20000)
        return self.u.reg_read(UC_ARM_REG_R0)

    def start(self, position):
        self.log.clear()
        return self.call(INIT, CTX, position, 0, 0, stack=(TABLE,))

    def step(self, direction):
        self.log.clear()
        self.w16(CTX + 0xC, 0)
        self.u.mem_write(CTX + 0x10, struct.pack('<I', TABLE))
        return self.call(STEP, CTX, direction & 0xFFFFFFFF)

    def where(self):
        return self.r16(CTX + 2), self.folder, self.ordinal


def expect(player, label, position, entry):
    ordinal, run = ENTRIES[entry]
    want = (position, RUNS[run][0], ordinal + 1)
    got = player.where()
    assert got == want, f'{label}: got {got}, want {want}'
    ctxt = bytes(player.u.mem_read(CTX + 0x50, 42))
    assert ctxt == bytes([0x40 + run]) * 42, f'{label}: folder context'
    print(f'PASS {label}: position {position} plays entry {entry} '
          f'(folder {want[1]:#x}, file {want[2]})')


def main():
    raw = IMAGE.read_bytes()
    print(f'image sha256 {hashlib.sha256(raw).hexdigest()}')

    p = Player(raw, armed=True)
    first = p.call(COMPANION_SITE, 1, 0x0BADF00D, TABLE, 1, lr=RET_START)
    assert first == 1, first
    print('PASS start: the playlist start fetch returns position 1')

    p.start(first)
    assert p.r16(CTX) == len(ENTRIES), p.r16(CTX)
    assert 'stock count' not in p.log
    expect(p, 'start', 1, 0)

    p.step(1)
    expect(p, 'next into the second folder', 2, 1)
    p.step(1)
    expect(p, 'next back to the first folder', 3, 2)
    p.step(1)
    expect(p, 'next wraps to the first entry', 1, 0)
    p.step(-1)
    expect(p, 'previous wraps to the last entry', 3, 2)
    p.step(-1)
    expect(p, 'previous', 2, 1)

    # The playlist start message reaches module 33's initializer, which
    # normalizes the payload and calls 0x0305D048 (entry at 0x03089F2A,
    # after its hardware setup; r4 = message, r8 = 1, r9 = 0).
    m = Player(raw, armed=True, modules=(0, 33))
    m.u.mem_write(0x030E2000, struct.pack('<H', first))
    from unicorn.arm_const import UC_ARM_REG_R4, UC_ARM_REG_R8, UC_ARM_REG_R9
    m.u.reg_write(UC_ARM_REG_R4, 0x030E2000)
    m.u.reg_write(UC_ARM_REG_R8, 1)
    m.u.reg_write(UC_ARM_REG_R9, 0)
    m.u.reg_write(UC_ARM_REG_SP, 0x030E0000)
    m.u.reg_write(UC_ARM_REG_LR, DONE | 1)
    try:
        m.u.emu_start(0x03089F2B, 0x0305D0DA, count=20000)
    except Exception as exc:
        raise SystemExit(f'module 33 path stopped at '
                         f'{m.u.reg_read(UC_ARM_REG_PC):#x}: {exc}; '
                         f'log {m.log}')
    assert m.r16(CTX) == len(ENTRIES), m.r16(CTX)
    expect(m, 'module 33 start message', 1, 0)

    # Unarmed: stock folder play, untouched by the hooks.
    q = Player(raw, armed=False)
    q.start(1)
    assert q.r16(CTX) == STOCK_COUNT, q.r16(CTX)
    assert q.log == ['stock count', 'stock resolver', 'reset'], q.log
    assert q.where() == (1, STOCK_FOLDER, 1), q.where()
    q.step(1)
    assert q.log == ['next'], q.log
    assert q.r16(CTX + 2) == 2 and q.ordinal == 2
    print('PASS unarmed: stock count and a plain folder-iterator next')

    # A fetch from any other caller runs the stock fetch even when armed.
    r = Player(raw, armed=True)
    r.log.clear()
    r.call(COMPANION_SITE, 7, 0x12345678, TABLE, 1, lr=0x0307E171)
    assert r.log == ['stock fetch'], r.log
    print('PASS other fetch callers fall through to the stock fetch')
    print('ALL PASS: playlist lifecycle through the composed image')


if __name__ == '__main__':
    main()

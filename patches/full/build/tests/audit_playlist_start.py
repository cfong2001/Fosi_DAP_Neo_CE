#!/usr/bin/env python3
"""Extended playlist lifecycle audit for the FULL build.

Extends patches/navigation/audit_playlist_lifecycle.py, which proved
the REVIEWED composition skips playback start, to the full build's
trampoline, whose handled exit enters the stock folder-play sequence
at 0x0307E052. Runs the real patched code from the composed image
under Unicorn with the external callees modeled:

  S1 a non-playlist file name bypasses the hook (the trampoline
     matches the M3U extension itself; flag untouched, no bridge);
  S2 a playlist action the bridge declines (modeled return 0; the
     bridge clears the flag at entry and re-arms only on a committed
     import, per m3u_bridge.c) resumes stock behavior;
  S3 modelled successful import: the bridge entry is intercepted
     returning 1 (staging and resolution are covered by the host
     bridge test), and the audit asserts the whole stock start
     sequence then executes: classifier, directory fetch returning
     a halfword destination stored at [sp+4], source 6 committed at
     play context +0xF2, current-directory global updated, the
     +0x60 byte written, events 0x17D and 0x17B cleared, event
     0x14D posted, message 3 sent with r1 = sp+4 pointing at the
     fetch result, return value 1 at the common exit, and the
     staging flag still set (start does not disarm);
  S4 folder action disarms (flag cleared) and proceeds to the same
     stock sequence entry;
  S5 file action disarms, replays the displaced load and call, and
     resumes at 0x0307E1D2 with lr restored to 0x0307E1D3;
  S6 tag-library action commits the category from ip at play
     context +0xF2, disarms, and resumes at 0x0307EC76.

Offline instruction-level evidence only; hardware playback remains
a Phase E gate.
"""
import hashlib
import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                               UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5,
                               UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9,
                               UC_ARM_REG_R10, UC_ARM_REG_R12, UC_ARM_REG_SP,
                               UC_ARM_REG_LR, UC_ARM_REG_PC)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'tools'))
from rknano_image import Image  # noqa: E402

FULL_SHA256 = '6305014618c35c6c78d573dfda760ee75cd1978a9448961fed5d0fe04015f2b7'
TRAMP = 0x0307EE48
BRIDGE = 0x0307EE88
RESUME = 0x0307DF1E
STAGE = 0x0307BFB4
CLASSIFY = 0x0307D1F8
FETCH = 0x0305B2C2
PATHFILL = 0x030630C2
CMP = 0x030570E8
COPY = 0x03057040
FILEFN = 0x030570A4
EVCLEAR = 0x0306727E
EVPOST = 0x0306723C
MSG = 0x03067452
START = 0x0307E052
COMMON_EXIT = 0x0307E0C8
# Model buffers sit above every loaded segment (module 0 code ends
# at 0x0307C7B0, the grown module 31 code at 0x030808D8).
NODE = 0x03090000
LEVELREC = 0x03091000
STATE = 0x03092000
CTX = 0x03093000
LEVEL = 0x03094000
SP0 = 0x030E0000
RET = 0x030ED001
FETCH_RESULT = 0x002A
DIR_SENTINEL = 0x0BADF00D


def load(modidx):
    raw = (REPO / 'patches' / 'full' / 'out' / 'DP3_V137_CE_full.img').read_bytes()
    if hashlib.sha256(raw).hexdigest() != FULL_SHA256:
        raise SystemExit('full image SHA-256 mismatch; rebuild first')
    img = Image(raw)
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x03000000, 0x100000)
    for idx, kinds in ((0, ('code', 'data')), (modidx, ('code',))):
        m = img.modules[idx]
        for kind in kinds:
            off, ln = img.module_region(idx, kind)
            u.mem_write(m[kind + '_exec'], raw[off:off + ln])
    return u


def seed_common(u, flag, ext=b'MP3'):
    u.mem_write(STAGE, bytes([flag]))
    u.mem_write(NODE + 0x57, ext + b'\x00')
    u.mem_write(NODE + 8, struct.pack('<I', LEVELREC))
    u.mem_write(STATE + 0x14, struct.pack('<I', DIR_SENTINEL))
    u.mem_write(LEVEL + 4, b'\x37')
    u.reg_write(UC_ARM_REG_R4, NODE)
    u.reg_write(UC_ARM_REG_R7, STATE)
    u.reg_write(UC_ARM_REG_R8, CTX)
    u.reg_write(UC_ARM_REG_R9, 0)
    u.reg_write(UC_ARM_REG_R10, LEVEL)
    u.reg_write(UC_ARM_REG_SP, SP0)
    u.reg_write(UC_ARM_REG_LR, RET)


class Calls:
    def __init__(self):
        self.seq = []

    def hook(self, models):
        def on_code(uc, address, size, user):
            if address in models:
                name, fn = models[address]
                args = tuple(uc.reg_read(r) for r in
                             (UC_ARM_REG_R0, UC_ARM_REG_R1,
                              UC_ARM_REG_R2, UC_ARM_REG_R3))
                self.seq.append((name, args, uc.reg_read(UC_ARM_REG_SP)))
                uc.reg_write(UC_ARM_REG_R0, fn(uc, *args))
                uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        return on_code


def ret(v):
    return lambda uc, *a: v


def names(calls):
    return [c[0] for c in calls.seq]


def test_s1():
    u = load(31)
    seed_common(u, 1)
    u.reg_write(UC_ARM_REG_R5, 1)
    c = Calls()
    u.hook_add(UC_HOOK_CODE, c.hook({CLASSIFY: ('classify', ret(1)),
                                     BRIDGE: ('bridge', ret(1))}))
    u.emu_start(TRAMP | 1, RESUME, count=200)
    assert names(c) == ['classify'], names(c)
    assert bytes(u.mem_read(STAGE, 1)) == b'\x01'
    print('PASS S1: non-playlist name bypasses the hook, flag '
          'untouched, bridge not called')


def test_s2():
    u = load(31)
    seed_common(u, 0, ext=b'M3U')
    u.reg_write(UC_ARM_REG_R5, 1)
    c = Calls()
    u.hook_add(UC_HOOK_CODE, c.hook({BRIDGE: ('bridge', ret(0)),
                                     CLASSIFY: ('classify', ret(1))}))
    u.emu_start(TRAMP | 1, RESUME, count=4000)
    assert names(c) == ['bridge', 'classify'], names(c)
    assert bytes(u.mem_read(STAGE, 1)) == b'\x00'
    print('PASS S2: bridge decline reproduces the displaced call '
          'and resumes; flag still clear')


def test_s3():
    u = load(31)
    seed_common(u, 1, ext=b'M3U')
    u.reg_write(UC_ARM_REG_R5, 1)
    g2 = struct.unpack('<I', u.mem_read(0x0307E0FC, 4))[0]
    u.mem_write(g2 + 0x60, b'\xee')
    seen = {}

    def msg(uc, r0, r1, r2, r3):
        seen['msg_hw'] = struct.unpack('<H', uc.mem_read(r1, 2))[0]
        return 0

    c = Calls()
    u.hook_add(UC_HOOK_CODE, c.hook({
        BRIDGE: ('bridge', ret(1)),
        CLASSIFY: ('classify', ret(1)),
        FETCH: ('fetch', ret(FETCH_RESULT)),
        PATHFILL: ('pathfill', ret(0)),
        CMP: ('cmp', ret(1)),
        COPY: ('copy', ret(0)),
        EVCLEAR: ('evclear', ret(0)),
        EVPOST: ('evpost', ret(0)),
        MSG: ('msg', msg)}))
    u.emu_start(TRAMP | 1, COMMON_EXIT, count=4000)
    assert names(c) == ['bridge', 'classify', 'fetch', 'pathfill',
                        'cmp', 'copy', 'evclear', 'evclear', 'evpost',
                        'msg'], names(c)
    by = {n: a for n, a, s in c.seq if n != 'evclear'}
    assert by['classify'][0] == 1
    f = by['fetch']
    assert f[0] == 1 and f[1] == LEVELREC and f[2] == SP0 + 0x20 \
        and f[3] == 0x37, f
    assert by['pathfill'][0] == 4 and by['pathfill'][2] == 0x80
    clears = [a[0] for n, a, s in c.seq if n == 'evclear']
    assert clears == [0x17D, 0x17B], clears
    assert by['evpost'][0] == 0x14D
    m = [x for x in c.seq if x[0] == 'msg'][0]
    assert m[1][0] == 3 and m[1][1] == SP0 + 4, m
    assert seen['msg_hw'] == FETCH_RESULT
    assert struct.unpack('<H', u.mem_read(SP0 + 4, 2))[0] == FETCH_RESULT
    assert struct.unpack('<H', u.mem_read(CTX + 0xF2, 2))[0] == 6
    g1 = struct.unpack('<I', u.mem_read(0x0307E148, 4))[0]
    assert struct.unpack('<I', u.mem_read(g1, 4))[0] == DIR_SENTINEL
    assert bytes(u.mem_read(g2 + 0x60, 1)) == b'\x00'
    assert u.reg_read(UC_ARM_REG_R0) == 1
    assert bytes(u.mem_read(STAGE, 1)) == b'\x01'
    print('PASS S3: modelled import runs the full stock start '
          'sequence; flag still armed')


def test_s4():
    u = load(31)
    seed_common(u, 1)
    c = Calls()
    u.hook_add(UC_HOOK_CODE, c.hook({CLASSIFY: ('classify', ret(1))}))
    u.emu_start(0x0307E04E | 1, START + 2, count=200)
    assert bytes(u.mem_read(STAGE, 1)) == b'\x00'
    assert names(c) == ['classify'], names(c)
    print('PASS S4: folder action disarms and enters the stock '
          'sequence (classifier reached at 0x0307E052)')


def test_s5():
    u = load(31)
    seed_common(u, 1)
    for i, r in enumerate((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                           UC_ARM_REG_R3)):
        u.reg_write(r, 0x1000 + i)
    c = Calls()
    u.hook_add(UC_HOOK_CODE, c.hook({FILEFN: ('filefn', ret(0))}))
    u.emu_start(0x0307E1CC | 1, 0x0307E1D2, count=200)
    assert bytes(u.mem_read(STAGE, 1)) == b'\x00'
    assert names(c) == ['filefn'], names(c)
    assert c.seq[0][1][0] == 0x03023D38, c.seq[0][1]
    assert u.reg_read(UC_ARM_REG_LR) == 0x0307E1D3
    assert u.reg_read(UC_ARM_REG_R1) == 0x1001
    assert u.reg_read(UC_ARM_REG_R2) == 0x1002
    print('PASS S5: file action disarms, displaced load and call '
          'replayed, resume 0x0307E1D2 with lr restored')


def test_s6():
    u = load(24)
    seed_common(u, 1)
    u.reg_write(UC_ARM_REG_R5, CTX)
    u.reg_write(UC_ARM_REG_R12, 9)
    u.reg_write(UC_ARM_REG_R0, 0x11223344)
    u.emu_start(0x0307EC72 | 1, 0x0307EC76, count=200)
    assert bytes(u.mem_read(STAGE, 1)) == b'\x00'
    assert struct.unpack('<H', u.mem_read(CTX + 0xF2, 2))[0] == 9
    assert u.reg_read(UC_ARM_REG_R0) == 0x11223344
    print('PASS S6: tag action commits the category, disarms, resumes')


def main():
    test_s1()
    test_s2()
    test_s3()
    test_s4()
    test_s5()
    test_s6()
    print('ALL PASS: playlist lifecycle audit for the full build')


if __name__ == '__main__':
    main()

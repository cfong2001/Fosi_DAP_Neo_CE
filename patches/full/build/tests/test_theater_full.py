#!/usr/bin/env python3
"""Emulator lifecycle test for theater mode in the FULL build.

Adapted from patches/theater/build/test_theater_lifecycle.py with
the tail base moved to the merged tail layout (payload and
trampoline addresses read from out/layout_tail.json); the image under test is the
composed everything image, not the standalone variant.

Loads modules 0, 18 and 19 from the FULL image and runs the real
patched code paths under Unicorn:

  * artwork setup 0x0308389E enters through the reset stub;
  * both row consumers (painter 0x03083B36, sync 0x0308399C) call
    the blit trampoline, which calls the stock bitmap entry; only
    the bitmap leaf itself is modeled (it is display hardware
    access), along with the file-read callback and the overlay
    loader, exactly as in patches/theater/research/probe_player.py.
    Every modeled bitmap call must arrive from inside the tail
    (return address in the trampoline), proving the patched path
    executed.

Assertions: the background cell 0x03004400 ends at the derived
RGB565 an independent Python port of frame_average.c (little
endian) plus the docs/theater-core.mjs mix computes from the rows
the bitmap hook observed; the repaint event bit is set; a second
setup restores the theme default; a no-art setup leaves the
default; the stock double-blit of the last row does not corrupt
the average.

Also included: a host cross-check that runs the assembled
trampoline alone against frame_average.c compiled for the host,
over random rows, comparing accumulator state after every row.

And a tall case: the full build's sampler cap is 64 rows (the
standalone variant keeps 48), so a scaled height of 190 (the
focus geometry) must latch rows_needed = ceil(190/3) = 64, count
all 64 rows across both bitmask words, and finalize to the value
the independent port computes over exactly those rows.
"""
import base64
import ctypes
import hashlib
import random
import json
import runpy
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                               UC_ARM_REG_R3, UC_ARM_REG_PC, UC_ARM_REG_SP,
                               UC_ARM_REG_LR)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
THEATER = REPO / 'patches' / 'theater'
sys.path.insert(0, str(REPO / 'tools'))
import fosi_paths  # noqa: E402
from rknano_image import Image  # noqa: E402

STATE = 0x03023468
CTX = 0x03026CA0
ROWBUF = 0x03026A20
BGCELL = 0x03004400
SAVEINFO = 0x030232A0
PALCELL = 0x030235B4
EVWORD = 0x03023CFC
EVMASK = 0x02000000
_LAYOUT = json.loads((HERE.parents[1] / 'out' / 'layout_tail.json').read_text())
_THEATER = next(p for p in _LAYOUT['pieces'] if p['name'].startswith('theater'))
TAIL_LO = int(_THEATER['address'], 16)
TAIL_HI = TAIL_LO + _THEATER['bytes']
TRAMP = int(_THEATER['trampoline'], 16)
END = 0x030EF000

fixture = runpy.run_path(str(THEATER / 'research' / 'probe_jpeg.py'))
JPEG = fixture['JPEG']


# ------------------------------------------------ independent port

def port_average(rows):
    """frame_average.c, little-endian, over the given rows."""
    width = len(rows[0])
    sums = [0, 0, 0]
    for row in rows:
        for w in row:
            sums[0] += ((w >> 11) & 31) * 255 // 31
            sums[1] += ((w >> 5) & 63) * 255 // 63
            sums[2] += (w & 31) * 255 // 31
    count = width * len(rows)
    return tuple((s + count // 2) // count for s in sums)


def port_rgb565(r, g, b):
    """docs/theme-core.mjs rgb565()."""
    return (((r * 31 + 127) // 255) << 11
            | ((g * 63 + 127) // 255) << 5
            | ((b * 31 + 127) // 255))


def port_derived(rows, light):
    avg = port_average(rows)
    if light:
        mixed = tuple((a * 25 + t * 75 + 50) // 100
                      for a, t in zip(avg, (242, 237, 230)))
    else:
        mixed = tuple((a * 45 + 50) // 100 for a in avg)
    return port_rgb565(*mixed), avg, mixed


# ------------------------------------------------ variant build

def build_variant(tmp):
    img = REPO / 'patches' / 'full' / 'out' / 'DP3_V137_CE_full.img'
    if not img.exists():
        raise SystemExit('full image missing; run '
                         'patches/full/build/build_full.py first')
    return img.read_bytes()


# ------------------------------------------------ emulator harness

class Player:
    def __init__(self, raw, width, height, light=False, serve=True):
        self.raw = raw
        self.im = Image(raw)
        self.u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.u.mem_map(0x03000000, 0x100000)
        for module in (0, 18, 19):
            m = self.im.modules[module]
            for kind in ('code', 'data'):
                off, size = self.im.module_region(module, kind)
                if size:
                    self.u.mem_write(m[kind + '_exec'], raw[off:off + size])
        self.width = width
        self.serve = serve
        self.cursor = 0
        self.blits = []
        w32 = self.w32
        for addr, val in ((0x0302598C, width), (0x03025990, height),
                          (0x03025994, 23), (0x03025998, 36),
                          (0x030259DC, 1)):
            w32(addr, val)
        if light:
            self.u.mem_write(SAVEINFO + 0x2D8, b'\x01')
            self.u.mem_write(PALCELL, struct.pack('<H', 0xEF5D))
        self.u.hook_add(UC_HOOK_CODE, self._hook)

    def w32(self, addr, val):
        self.u.mem_write(addr, struct.pack('<I', val))

    def r32(self, addr):
        return struct.unpack('<I', self.u.mem_read(addr, 4))[0]

    def r16(self, addr):
        return struct.unpack('<H', self.u.mem_read(addr, 2))[0]

    def state(self):
        b = self.u.mem_read(STATE, 28)
        sums = struct.unpack_from('<III', b, 0)
        mask = struct.unpack_from('<II', b, 12)
        width, needed = struct.unpack_from('<HH', b, 20)
        return {'sums': sums, 'mask': mask, 'width': width,
                'needed': needed, 'seen': b[24], 'flags': b[25]}

    def _hook(self, uc, addr, size, user):
        if addr == 0x03058FA8:                      # file read
            dest, count, handle = (uc.reg_read(r) for r in
                                   (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                    UC_ARM_REG_R2))
            assert handle == 1 and count <= 4096
            block = JPEG[self.cursor:self.cursor + count] \
                if self.serve else b''
            self.cursor += len(block)
            if block:
                uc.mem_write(dest, block)
            uc.reg_write(UC_ARM_REG_R0, len(block))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif addr == 0x03067870:                    # overlay loader
            # Model the loader's documented job (copy the module's
            # segments, clear its BSS) for the requested module, so a
            # second setup sees the same fresh overlay a reload on
            # hardware would produce.
            idx = uc.reg_read(UC_ARM_REG_R0)
            if 0 <= idx < len(self.im.modules):
                m = self.im.modules[idx]
                for kind in ('code', 'data'):
                    off, size = self.im.module_region(idx, kind)
                    if size:
                        uc.mem_write(m[kind + '_exec'],
                                     self.raw[off:off + size])
                if m.get('bss_len'):
                    uc.mem_write(m['bss_exec'], bytes(m['bss_len']))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif addr == 0x0306333E:                    # bitmap leaf (modeled)
            args = [uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                             UC_ARM_REG_R2, UC_ARM_REG_R3)]
            mode, ptr = struct.unpack('<II', uc.mem_read(
                uc.reg_read(UC_ARM_REG_SP), 8))
            lr = uc.reg_read(UC_ARM_REG_LR)
            pixels = struct.unpack('<%dH' % args[2],
                                   uc.mem_read(ptr, args[2] * 2)) \
                if args[2] else ()
            self.blits.append({'args': args, 'mode': mode, 'ptr': ptr,
                               'lr': lr, 'pixels': pixels})
            uc.reg_write(UC_ARM_REG_R0, 0)
            uc.reg_write(UC_ARM_REG_PC, lr)

    def call(self, addr, r0=0, r1=0):
        for reg, value in ((UC_ARM_REG_R0, r0), (UC_ARM_REG_R1, r1),
                           (UC_ARM_REG_R2, 0), (UC_ARM_REG_R3, 0),
                           (UC_ARM_REG_SP, 0x030F0000),
                           (UC_ARM_REG_LR, END | 1)):
            self.u.reg_write(reg, value)
        self.u.emu_start(addr | 1, END, count=5000000)
        assert self.u.reg_read(UC_ARM_REG_PC) == END, \
            'instruction limit or unexpected return'
        return self.u.reg_read(UC_ARM_REG_R0)

    def setup(self):
        return self.call(0x0308389E, 1, 0)


def check_blits_from_trampoline(p):
    assert p.blits, 'no bitmap calls recorded'
    for b in p.blits:
        assert TAIL_LO <= (b['lr'] & ~1) - 4 < TAIL_HI, \
            f"bitmap call did not come from the trampoline: lr {b['lr']:#x}"
        assert b['mode'] == 0x10 and b['ptr'] == ROWBUF


def scenario_portrait(raw):
    global JPEG
    previous = JPEG
    JPEG = base64.b64decode(
        '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAIBAQEBAQIBAQECAgICAgQDAgICAgUEBAMEBgUGBgYFBgYGBwkIBgcJBwYGCAsICQoKCgoKBggLDAsKDAkKCgr/2wBDAQICAgICAgUDAwUKBwYHCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgr/wAARCAAeABIDAREAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAj/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFgEBAQEAAAAAAAAAAAAAAAAAAAgJ/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEQMRAD8Ai9KbfwAAAAAAAAAAB//Z')
    try:
        p = Player(raw, 16, 16)
        assert p.setup() == 1
        for _ in range(16):
            p.call(0x03083B36)
        check_blits_from_trampoline(p)
        assert p.r32(CTX + 0x14) == 9
        print('portrait state:', p.state(), 'color:', hex(p.r16(BGCELL)))
        assert p.r16(BGCELL) == 0x7000
    finally:
        JPEG = previous


def scenario_painter(raw, width, height, scaled_height, light):
    p = Player(raw, width, height, light=light)
    default = 0xEF5D if light else 0x10A2
    p.u.mem_write(BGCELL, struct.pack('<H', 0xBEEF))   # pre-dirtied cell
    assert p.setup() == 1
    st = p.state()
    assert p.r16(BGCELL) == default, \
        f'reset stub: cell {p.r16(BGCELL):#x} != theme default {default:#x}'
    assert st['flags'] == 1 and st['sums'] == (0, 0, 0) and st['seen'] == 0, st
    returns = [p.call(0x03083B36) for _ in range(scaled_height)]
    assert len(p.blits) == scaled_height, (returns, len(p.blits))
    check_blits_from_trampoline(p)
    needed = (scaled_height + 2) // 3
    rows = [b['pixels'] for b in p.blits[:needed]]
    expected, avg, mixed = port_derived(rows, light)
    cell = p.r16(BGCELL)
    st = p.state()
    print(f'  painter {"light" if light else "dark"} {width}x{height}: '
          f'avg {avg} mixed {mixed} expected cell {expected:#06x} '
          f'actual {cell:#06x} state {st}')
    assert cell == expected, (cell, expected)
    assert p.r32(EVWORD) & EVMASK, 'event bit 0x39 not set'
    assert st['flags'] == 7 and st['seen'] == needed \
        and st['width'] == width and st['needed'] == needed, st
    sums = [0, 0, 0]
    for row in rows:
        for w in row:
            sums[0] += ((w >> 11) & 31) * 255 // 31
            sums[1] += ((w >> 5) & 63) * 255 // 63
            sums[2] += (w & 31) * 255 // 31
    assert st['sums'] == tuple(sums), (st['sums'], sums)
    # extra consumer call: the stock double-blit must not corrupt
    before = len(p.blits)
    extra = p.call(0x03083B36)
    print(f'  extra painter call: return {extra}, '
          f'additional blits {len(p.blits) - before}, cell still '
          f'{p.r16(BGCELL):#06x}')
    assert p.r16(BGCELL) == expected
    assert p.state()['sums'] == tuple(sums)
    return p, expected, default


def scenario_track_change(raw):
    p, expected, default = scenario_painter(raw, 30, 18, 18, light=False)
    p.cursor = 0
    assert p.setup() == 1
    st = p.state()
    assert p.r16(BGCELL) == default, 'track change did not restore default'
    assert st['flags'] == 1 and st['sums'] == (0, 0, 0) and st['seen'] == 0, st
    for _ in range(18):
        p.call(0x03083B36)
    assert p.r16(BGCELL) == expected, 're-armed accumulation did not repeat'
    print('  track change: default restored, state cleared, '
          'second accumulation reproduced the derived cell')


def scenario_sync(raw):
    p = Player(raw, 30, 18)
    assert p.setup() == 1
    calls = 0
    while calls < 40:
        before = len(p.blits)
        p.call(0x0308399C, 1)
        calls += 1
        if len(p.blits) == before and calls > 20:
            break
    # The sync consumer blits the final row twice (rows 0..17 then
    # 17 again, 19 blits): the duplicate is the case the row
    # bitmask exists for, and the sums below prove it was rejected.
    ys = [b['args'][1] - 36 for b in p.blits]
    assert ys == list(range(18)) + [17], ys
    check_blits_from_trampoline(p)
    rows = [b['pixels'] for b in p.blits[:6]]
    expected, avg, mixed = port_derived(rows, light=False)
    cell = p.r16(BGCELL)
    print(f'  sync dark 30x18: {calls} calls, avg {avg} mixed {mixed} '
          f'expected cell {expected:#06x} actual {cell:#06x}')
    assert cell == expected
    assert p.r32(EVWORD) & EVMASK
    assert p.state()['flags'] == 7


def scenario_no_art(raw):
    p = Player(raw, 30, 18, serve=False)
    p.u.mem_write(BGCELL, struct.pack('<H', 0xBEEF))
    ret = p.setup()
    cell = p.r16(BGCELL)
    st = p.state()
    print(f'  no-art: setup returned {ret}, cell {cell:#06x}, state {st}, '
          f'blits {len(p.blits)}')
    assert cell == 0x10A2, 'reset stub did not restore the theme default'
    for _ in range(3):
        p.call(0x03083B36)
        p.call(0x0308399C, 1)
    st = p.state()
    assert st['seen'] == 0 and p.r16(BGCELL) == 0x10A2, st
    print('  no-art: no rows accumulated, default left in place')


# ------------------------------------------------ accumulate cross-check

class Average(ctypes.Structure):
    _fields_ = [('sum', ctypes.c_uint64 * 3), ('width', ctypes.c_uint32),
                ('rows_needed', ctypes.c_uint32),
                ('rows_seen', ctypes.c_uint32), ('big_endian', ctypes.c_int)]


def crosscheck_accumulate(raw):
    tmp = tempfile.TemporaryDirectory()
    so = str(Path(tmp.name) / 'avg.so')
    subprocess.run(['cc', '-shared', '-fPIC', '-o', so,
                    str(THEATER / 'frame_average.c')], check=True)
    avg = ctypes.CDLL(so)
    avg.theater_top_init.argtypes = [ctypes.POINTER(Average),
                                     ctypes.c_uint32, ctypes.c_uint32,
                                     ctypes.c_int]
    avg.theater_top_row.argtypes = [ctypes.POINTER(Average),
                                    ctypes.c_void_p, ctypes.c_size_t]
    im = Image(raw)
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x03000000, 0x100000)
    m = im.modules[0]
    off, size = im.module_region(0, 'code')
    u.mem_write(m['code_exec'], raw[off:off + size])
    off, size = im.module_region(0, 'data')
    u.mem_write(m['data_exec'], raw[off:off + size])
    width, height, rows_n = 37, 21, 7
    rng = random.Random(20261104)
    rows = [[rng.randrange(0x10000) for _ in range(width)]
            for _ in range(rows_n)]

    def w32(a, v): u.mem_write(a, struct.pack('<I', v))
    w32(CTX + 0x18, height)
    w32(CTX + 0x0c, width)                       # rendered target width
    w32(CTX + 0x14, width)                       # scaled artwork width
    state = Average()
    assert avg.theater_top_init(ctypes.byref(state), width, height, 0)
    seen_bitmap = []

    def hook(uc, addr, size_, user):
        if addr == 0x0306333E:
            mode, ptr = struct.unpack('<II', uc.mem_read(
                uc.reg_read(UC_ARM_REG_SP), 8))
            seen_bitmap.append((mode, ptr))
            uc.reg_write(UC_ARM_REG_R0, 0)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    u.hook_add(UC_HOOK_CODE, hook)
    # arm the device state directly (the lifecycle scenarios cover
    # the reset stub): flags = armed
    u.mem_write(STATE + 25, b'\x01')
    sp0 = 0x030F0000 - 0x100

    def feed(row_idx, pixels):
        u.mem_write(ROWBUF, struct.pack('<%dH' % width, *pixels))
        w32(CTX + 0x2C, row_idx)
        u.mem_write(sp0, struct.pack('<II', 0x10, ROWBUF))
        for reg, val in ((UC_ARM_REG_R0, 23), (UC_ARM_REG_R1, 36 + row_idx),
                         (UC_ARM_REG_R2, width), (UC_ARM_REG_R3, 1),
                         (UC_ARM_REG_SP, sp0), (UC_ARM_REG_LR, END | 1)):
            u.reg_write(reg, val)
        u.emu_start(TRAMP | 1, END, count=1000000)
        assert u.reg_read(UC_ARM_REG_PC) == END

    def dev_state():
        b = u.mem_read(STATE, 28)
        return {'sums': struct.unpack_from('<III', b, 0),
                'mask': struct.unpack_from('<II', b, 12),
                'seen': b[24], 'flags': b[25]}
    for i, row in enumerate(rows):
        feed(i, row)
        data = struct.pack('<%dH' % width, *row)
        assert avg.theater_top_row(ctypes.byref(state), data, len(data))
        dev = dev_state()
        assert dev['sums'] == tuple(state.sum), (i, dev, tuple(state.sum))
        assert dev['seen'] == state.rows_seen == i + 1
        # duplicate feed of the same row: bitmask must reject it
        feed(i, row)
        assert dev_state() == dev, f'duplicate row {i} changed state'
    assert seen_bitmap and all(s == (0x10, ROWBUF) for s in seen_bitmap), \
        seen_bitmap[:3]
    dev = dev_state()
    assert dev['flags'] & 2, 'done flag not set after final row'
    assert u.mem_read(BGCELL, 2) != b'\x00\x00'
    print(f'  cross-check: {rows_n} random rows x {width}px, device sums '
          f'{dev["sums"]} == host C sums, duplicates rejected, '
          f'{len(seen_bitmap)} bitmap calls all with (0x10, row buffer)')


# ------------------------------------------------ tall case (cap 64)

def scenario_tall(raw):
    """Feed 70 distinct rows at scaled height 190 directly to the
    trampoline (the cross-check's method). With the full build's
    cap at 64, rows_needed latches at 64, rows 48..63 land in the
    second bitmask word, rows past 63 are rejected once done, and
    the finalize cell equals the port over the first 64 rows. At
    the standalone cap of 48 this scenario fails at the latch."""
    im = Image(raw)
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x03000000, 0x100000)
    m = im.modules[0]
    for kind in ('code', 'data'):
        off, size = im.module_region(0, kind)
        u.mem_write(m[kind + '_exec'], raw[off:off + size])
    width, scaled_height = 30, 190
    rng = random.Random(20261105)
    rows = [[rng.randrange(0x10000) for _ in range(width)]
            for _ in range(70)]

    def w32(a, v): u.mem_write(a, struct.pack('<I', v))
    w32(CTX + 0x18, scaled_height)
    w32(CTX + 0x0c, width)
    w32(CTX + 0x14, width)

    def hook(uc, addr, size_, user):
        if addr == 0x0306333E:                    # bitmap leaf (modeled)
            uc.reg_write(UC_ARM_REG_R0, 0)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    u.hook_add(UC_HOOK_CODE, hook)
    u.mem_write(STATE + 25, b'\x01')              # armed
    sp0 = 0x030F0000 - 0x100

    def feed(row_idx, pixels):
        u.mem_write(ROWBUF, struct.pack('<%dH' % width, *pixels))
        w32(CTX + 0x2C, row_idx)
        u.mem_write(sp0, struct.pack('<II', 0x10, ROWBUF))
        for reg, val in ((UC_ARM_REG_R0, 25), (UC_ARM_REG_R1, 8 + row_idx),
                         (UC_ARM_REG_R2, width), (UC_ARM_REG_R3, 1),
                         (UC_ARM_REG_SP, sp0), (UC_ARM_REG_LR, END | 1)):
            u.reg_write(reg, val)
        u.emu_start(TRAMP | 1, END, count=1000000)
        assert u.reg_read(UC_ARM_REG_PC) == END

    def dev_state():
        b = u.mem_read(STATE, 28)
        return {'sums': struct.unpack_from('<III', b, 0),
                'mask': struct.unpack_from('<II', b, 12),
                'width': struct.unpack_from('<H', b, 20)[0],
                'needed': struct.unpack_from('<H', b, 22)[0],
                'seen': b[24], 'flags': b[25]}
    for i, row in enumerate(rows):
        feed(i, row)
        st = dev_state()
        if i == 0:
            assert st['needed'] == 64, \
                f"rows_needed latched at {st['needed']}, expected 64 " \
                f'(cap lift missing?)'
            assert st['width'] == width
        if i < 64:
            assert st['seen'] == i + 1, (i, st)
    st = dev_state()
    assert st['seen'] == 64 and st['needed'] == 64, st
    assert st['mask'] == (0xFFFFFFFF, 0xFFFFFFFF), st
    assert st['flags'] == 7, st
    expected, avg, mixed = port_derived(rows[:64], light=False)
    cell = struct.unpack('<H', u.mem_read(BGCELL, 2))[0]
    print(f'  tall 190: rows_needed 64, seen 64, mask full, avg {avg} '
          f'mixed {mixed} expected cell {expected:#06x} actual {cell:#06x}')
    assert cell == expected, (cell, expected)
    sums = [0, 0, 0]
    for row in rows[:64]:
        for w in row:
            sums[0] += ((w >> 11) & 31) * 255 // 31
            sums[1] += ((w >> 5) & 63) * 255 // 63
            sums[2] += (w & 31) * 255 // 31
    assert st['sums'] == tuple(sums), (st['sums'], sums)
    assert struct.unpack('<I', u.mem_read(EVWORD, 4))[0] & EVMASK, \
        'event bit 0x39 not set'


def main():
    tmp = tempfile.mkdtemp(prefix='neo-theater-test-')
    raw = build_variant(tmp)
    print(f'full image sha256 {hashlib.sha256(raw).hexdigest()}')
    scenario_painter(raw, 30, 18, 18, light=False)
    print('PASS lifecycle: painter, dark, 30x18')
    scenario_painter(raw, 16, 16, 9, light=True)
    print('PASS lifecycle: painter, light, 16x16 scaled to 9 rows')
    scenario_track_change(raw)
    print('PASS lifecycle: track change reset and re-arm')
    scenario_sync(raw)
    print('PASS lifecycle: sync consumer, dark, 30x18')
    scenario_no_art(raw)
    print('PASS lifecycle: no-art setup leaves the theme default')
    scenario_portrait(raw)
    print('PASS lifecycle: portrait uses art width without padding')
    crosscheck_accumulate(raw)
    print('PASS cross-check: assembled trampoline vs host frame_average.c')
    scenario_tall(raw)
    print('PASS tall case: scaled height 190, cap 64, true top third')


if __name__ == '__main__':
    main()

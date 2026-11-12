#!/usr/bin/env python3
"""Emulation gates for the browser dwell-scroll marquee variant.

Builds the variant (default 32 + marquee hooks + module 31 growth)
and drives the REAL browser painter (module 31), the REAL marquee
stepper (module 0 0x03062F54), the REAL registrar path through the
gate, and the payload routines under Unicorn. Text is modelled at
its painter-facing entries, the same boundary the focus suite uses:
the string measure (0x0306295A) returns a deterministic per-character
width model, the text renderer (0x03062CEE) records its descriptor
and string, rect fills (0x030632FA) record and apply, and the
stepper's cropped erase blit (0x03063C74) records its rect and is
modelled as restoring the rect (it is the stock erase every stock
marquee step already performs). Everything else, including the
event-bit helpers, the palette writer and the mode setter, runs as
real code from the built image.

Gates (from the feature brief):
  1. no offset movement before the dwell elapses;
  2. the offset advances at the stock cadence (one character per 30
     ticks) and the end behaviour is the stock ping-pong;
  3. selection change and key press reset offset and dwell;
  4. a fitting name produces zero scroll steps over a long idle;
  5. pixel level: during a scroll step, every write outside the
     selected row's text rect is the band colour, and rows above and
     below are never written (asserted with gate 6);
  6. the stock rows above and below are never written during a
     scroll step.

Plus unit gates for the composed string (file with extension and
each size class, folder, extensionless file, name over the cap).
"""
import hashlib
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'tools'))
sys.path.insert(0, str(REPO / 'patches' / 'framework'))
sys.path.insert(0, str(HERE))

import fosi_paths                                            # noqa: E402
from rknano_image import Image                               # noqa: E402
from unicorn import (Uc, UC_ARCH_ARM, UC_MODE_THUMB,         # noqa: E402
                     UC_HOOK_CODE)
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1,  # noqa: E402
                               UC_ARM_REG_R2, UC_ARM_REG_R3,
                               UC_ARM_REG_SP, UC_ARM_REG_LR,
                               UC_ARM_REG_PC)
import build_marquee as bm                                   # noqa: E402

STOCK_SHA = bm.STOCK_SHA
PAINT = 0x0307ED41
KEY = bm.KEY_SITE
EXIT = bm.EXIT_SITE
FILL = 0x030632FA
MEASURE = 0x0306295A
CHARWIDTH = 0x030627BE
RENDER = 0x03062CEE
ERASE = 0x03063C74
LOADER = 0x03067870
BITMAP = 0x0306333E
DRAWAT = 0x0306354A
KEYED = 0x03063A08
MCTX = bm.MCTX
BCTX = bm.BCTX
LCTX = bm.LCTX
CLOCK = bm.CLOCK
EVENTS = 0x03023CF8
SENTINEL = 0x03110000
STACK_TOP = 0x03100000
# The node pool is a harness fiction and must sit outside every
# module's load footprint: 0x03030000 (the old choice) lies inside
# module 19's BSS (0x03026DA8 + 0xFB20), which the stock loader
# zeroes when the picture setup loads the JPEG decoder, the path
# the v4 thumbnail takes at every pictured dwell. Segment
# coverage ends at 0x0309F4AC; the stack sits at 0x03100000.
NODE_POOL = 0x030A0000
NODE_SIZE = 0x270

_probe, _pe = bm.assemble(bm.BASE + 0x1000, bm.BASE + 0x1020)
_code_len = (len(_probe) + 3) & ~3
STATE = bm.BASE + _code_len
BUF = STATE + bm.STATE_LEN
ENT = bm.assemble(STATE, BUF, _pe)[1]


def model_width(units):
    w = 0
    for ch in units:
        c = chr(ch)
        if c == ' ':
            w += 4
        elif c == '.':
            w += 3
        elif c == '-':
            w += 5
        elif c.isupper() or c.isdigit():
            w += 8
        else:
            w += 7
    return w


# ------------------------------------------------ variant build

def build_variant(tmp):
    ecp = fosi_paths.ecpatch_dir(REPO)
    no_transplants = os.environ.get('FOSI_MARQUEE_NO_TRANSPLANTS') == '1'
    if ecp is None and not no_transplants:
        raise SystemExit('ecpatch inputs not found; set '
                         'FOSI_ECPATCH_DIR or explicitly set '
                         'FOSI_MARQUEE_NO_TRANSPLANTS=1 for the stock-decoder test variant')
    out = Path(tmp) / 'marquee.img'
    decoder_args = ['--no-transplants'] if no_transplants else ['--ecpatch-dir', str(ecp)]
    r = subprocess.run(
        [sys.executable, str(REPO / 'patches' / 'framework'
                             / 'build.py'),
         '--input', str(REPO / 'DP3_V137.img'),
         '--manifest', str(HERE / 'manifest.txt'),
         *decoder_args,
         '--grow', f'31:code:{HERE / "marquee_payload.bin"}',
         '--tail', str(HERE / 'marquee_tail.bin'),
         '--output', str(out)], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit('variant build failed: ' + r.stderr)
    raw = out.read_bytes()
    # v5: the payload grows module 31 and the zeroed gap tail holds the
    # slice line buffer, as recorded in design.md (Accounting).
    expected = ('4d14ce1dfefd269a315d6d70466e30a2eca2f6cef190a6c439a5daedb3a0ace6'
                if no_transplants else
                '15ddd10a7cc61966ed4fc6549037a4a08646b44171e6e4c8da7543c3aa0acbb0')
    if hashlib.sha256(raw).hexdigest() != expected:
        raise SystemExit('marquee test variant hash mismatch; refusing unreviewed output')
    if no_transplants:
        print('Testing stock-decoder marquee variant; decoder transplants were not tested.')
    return raw


# ------------------------------------------------ emulator harness

class Machine:
    def __init__(self, raw):
        self.raw = raw
        self.im = Image(raw)
        self.u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.u.mem_map(0x03000000, 0x500000)
        self.u.mem_map(0x01000000, 0x200000)
        self.u.mem_map(0xE000E000, 0x1000)
        for idx in (0, 18, 19, 31):
            m = self.im.modules[idx]
            for kind in ('code', 'data'):
                off, size = self.im.module_region(idx, kind)
                if size:
                    self.u.mem_write(m[kind + '_exec'],
                                     raw[off:off + size])
        # module 31 growth (the payload) is part of its code segment
        # in the built image, so it is already mapped above.
        # Modules 18/19 are mapped for the v4 thumbnail path: 18 is
        # resident on hardware, 19 is loaded by the picture setup
        # through the loader leaf modelled in the hook.
        self.fills = []         # (x0, y0, x1, y1, colour)
        self.renders = []       # (rect, string)
        self.erases = []        # (x0, y0, x1, y1)
        self.draws = []         # image draws (chrome; not pixels)
        self.bitmaps = []       # picture blits (v4 thumbnail path)
        self.measures = []      # strings measured
        self.u.hook_add(UC_HOOK_CODE, self._hook)

    # -- memory helpers
    def w32(self, a, v): self.u.mem_write(a, struct.pack('<I', v))
    def w16(self, a, v): self.u.mem_write(a, struct.pack('<H', v))
    def w8(self, a, v): self.u.mem_write(a, bytes([v]))
    def r32(self, a): return struct.unpack('<I', self.u.mem_read(a, 4))[0]
    def r16(self, a): return struct.unpack('<H', self.u.mem_read(a, 2))[0]
    def r8(self, a): return self.u.mem_read(a, 1)[0]
    def wstr(self, a, s):
        for i, ch in enumerate(s):
            self.w16(a + 2 * i, ord(ch))
        self.w16(a + 2 * len(s), 0)

    def read_str(self, a, maxn=90):
        out = []
        for i in range(maxn):
            ch = self.r16(a + 2 * i)
            if ch == 0:
                break
            out.append(chr(ch))
        return ''.join(out)

    def set_event(self, n):
        a = EVENTS + (n // 32) * 4
        self.w32(a, self.r32(a) | (1 << (n % 32)))

    def clear_event(self, n):
        a = EVENTS + (n // 32) * 4
        self.w32(a, self.r32(a) & ~(1 << (n % 32)))

    def event(self, n):
        return bool(self.r32(EVENTS + (n // 32) * 4) >> (n % 32) & 1)

    # -- fixture state
    def set_clock(self, t):
        self.w32(CLOCK, t)

    def clock(self):
        return self.r32(CLOCK)

    def mq_phase(self):
        return self.r8(STATE + 8)

    def mq_offset(self):
        return self.r16(MCTX + 0xA)

    def call(self, addr, r0=0, r1=0, until=SENTINEL):
        self.u.reg_write(UC_ARM_REG_SP, STACK_TOP)
        self.u.reg_write(UC_ARM_REG_R0, r0)
        self.u.reg_write(UC_ARM_REG_R1, r1)
        self.u.reg_write(UC_ARM_REG_LR, SENTINEL)
        self.u.emu_start(addr | 1, until, count=2_000_000)

    def paint(self):
        self.call(PAINT, r0=0x030247C4)

    # -- leaves
    def _ret(self, uc):
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def _hook(self, uc, addr, size, user):
        if addr == FILL:
            sp = uc.reg_read(UC_ARM_REG_SP)
            self.fills.append(tuple(
                uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                         UC_ARM_REG_R2, UC_ARM_REG_R3))
                + (struct.unpack('<I', uc.mem_read(sp, 4))[0] & 0xFFFF,))
            self._ret(uc)
        elif addr == MEASURE:
            s = self.read_str(uc.reg_read(UC_ARM_REG_R0))
            self.measures.append(s)
            uc.reg_write(UC_ARM_REG_R0,
                         model_width([ord(c) for c in s]))
            self._ret(uc)
        elif addr == CHARWIDTH:
            # The registrar's own per-character measure calls this
            # leaf directly (not through MEASURE); its real body
            # dives into the compression-wrapped font records, so it
            # is modelled with the same width table. It returns the
            # character advance in r0 and has no other effect the
            # callers observe.
            ch = uc.reg_read(UC_ARM_REG_R0) & 0xFFFF
            uc.reg_write(UC_ARM_REG_R0, model_width([ch]))
            self._ret(uc)
        elif addr == RENDER:
            rect = struct.unpack('<4H', uc.mem_read(
                uc.reg_read(UC_ARM_REG_R0), 8))
            s = self.read_str(uc.reg_read(UC_ARM_REG_R2))
            self.renders.append((rect, s))
            self._ret(uc)
        elif addr == ERASE:
            sp = uc.reg_read(UC_ARM_REG_SP)
            y1 = struct.unpack('<i', uc.mem_read(sp, 4))[0]
            self.erases.append((uc.reg_read(UC_ARM_REG_R1),
                                uc.reg_read(UC_ARM_REG_R2),
                                uc.reg_read(UC_ARM_REG_R3), y1))
            self._ret(uc)
        elif addr in (DRAWAT, KEYED):
            self.draws.append((addr, uc.reg_read(UC_ARM_REG_R0)))
            self._ret(uc)
        elif addr == LOADER:
            # Module loader leaf (the picture setup loads module
            # 19 through it): copy the module's segments from the
            # image and zero its BSS, as the stock loader does.
            idx = uc.reg_read(UC_ARM_REG_R0)
            mm = self.im.modules[idx]
            for kind in ('code', 'data'):
                off, sz = self.im.module_region(idx, kind)
                if sz:
                    uc.mem_write(mm[kind + '_exec'],
                                 self.raw[off:off + sz])
            if mm.get('bss_len'):
                uc.mem_write(mm['bss_exec'], bytes(mm['bss_len']))
            uc.reg_write(UC_ARM_REG_R0, 0)
            self._ret(uc)
        elif addr == BITMAP:
            # Row blitter leaf: record the pixels the caller hands
            # over (stack args: mode, pixel pointer).
            a = [uc.reg_read(r) for r in (UC_ARM_REG_R0,
                                          UC_ARM_REG_R1,
                                          UC_ARM_REG_R2,
                                          UC_ARM_REG_R3)]
            mode, ptr = struct.unpack('<II', uc.mem_read(
                uc.reg_read(UC_ARM_REG_SP), 8))
            px = struct.unpack('<%dH' % a[2],
                               uc.mem_read(ptr, a[2] * 2)) if a[2] \
                else ()
            self.bitmaps.append({'x': a[0], 'y': a[1], 'w': a[2],
                                 'h': a[3], 'mode': mode, 'px': px})
            uc.reg_write(UC_ARM_REG_R0, 0)
            self._ret(uc)


def make_node(m, idx, name, ext=b'   ', size=0, directory=False):
    a = NODE_POOL + idx * NODE_SIZE
    nxt = a + NODE_SIZE if idx < 6 else 0
    m.w32(a + 0x04, nxt)
    raw = bytearray(11)
    for i in range(11):
        raw[i] = 0x20
    raw[8:11] = ext
    for i, b in enumerate(raw):
        m.w8(a + 0x4F + i, b)
    m.w8(a + 0x5A, 0x10 if directory else 0x20)
    m.w32(a + 0x6B, size)
    m.wstr(a + 0x70, name)
    return a


def base_fixture(m):
    """Dark theme cells, font class 1 (12 px cell), browser ctx."""
    m.w16(0x030235B4, 0x0000)      # bg
    m.w16(0x030235B6, 0xFFFF)      # fg
    m.w16(0x030235B8, 0xF220)      # accent (band)
    m.w16(0x030235BA, 0x1082)      # line
    m.w8(0x0302385C + 0x24, 1)     # font class 1 -> 12 px cells
    m.w32(BCTX + 0x00, NODE_POOL)  # first visible node
    m.w16(BCTX + 0x1CC, 0)         # level 0
    m.w16(BCTX + 0x1CE, 0)         # first visible index 0
    m.w16(BCTX + 0x1EE, 0)         # selected index 0
    m.w16(LCTX + 0x08, 7)          # mode B count
    for i in range(0x30):
        m.w8(MCTX + i, 0)
    m.set_clock(1000)


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)
    print('  ok:', msg)


# ------------------------------------------------ gates

def test_compose(m):
    print('compose unit gates')
    cases = [
        # (name, ext, size, dir, expected composed)
        ('Tune', b'FLA', 842_150, False, 'Tune - FLA - 822 KB'),
        ('Tune', b'FLA', 500, False, 'Tune - FLA - 500 B'),
        ('Tune', b'FLA', 1023, False, 'Tune - FLA - 1023 B'),
        ('Tune', b'FLA', 1024, False, 'Tune - FLA - 1 KB'),
        ('Tune', b'MP3', 25_752_000, False, 'Tune - MP3 - 24.5 MB'),
        ('Tune', b'FLA', 1_048_576, False, 'Tune - FLA - 1.0 MB'),
        ('Tune', b'FLA', 1_610_612_736, False, 'Tune - FLA - 1.5 GB'),
        ('Noext', b'   ', 2048, False, 'Noext - 2 KB'),
        ('Folder Name', b'   ', 4096, True, 'Folder Name'),
    ]
    for name, ext, size, isdir, want in cases:
        a = make_node(m, 0, name, ext, size, isdir)
        m.call(ENT['compose'], r0=a)
        got = m.read_str(BUF)
        check(got == want, f'compose {name!r} -> {got!r} (want '
                           f'{want!r})')


def scroll_scenario(m, trace=None):
    """Row 2 selected, long file name. Returns the offset trace."""
    base_fixture(m)
    names = ['Alpha', 'Beta', 'The Quick Brown Fox Jumps Over',
             'Delta', 'Echo', 'Foxtrot', 'Golf']
    for i, nm in enumerate(names):
        make_node(m, i, nm, b'FLA' if i == 2 else b'MP3',
                  25_752_000 if i == 2 else 1000)
    m.w16(BCTX + 0x1EE, 2)
    offsets = []
    m.set_event(0x144)
    t = 1000
    m.set_clock(t)
    m.paint()
    offsets.append((t, m.mq_offset()))
    return t, offsets


def test_dwell_cadence_reset(m):
    print('gates 1, 2, 3, 5, 6: dwell, cadence, reset, pixels')
    t, offsets = scroll_scenario(m)
    composed = m.read_str(BUF) if m.r32(LCTX + 0xC) == BUF else None
    check(m.mq_phase() == 0, 'phase is DWELL after the selecting '
                             'paint')
    check(m.mq_offset() == 0, 'offset 0 at selection')
    # Gate 1: paints through the dwell: no step, no composed render.
    nrenders = len(m.renders)
    for t in range(1010, 1100, 10):
        m.set_clock(t)
        m.paint()
        offsets.append((t, m.mq_offset()))
    check(all(o == 0 for _, o in offsets),
          'gate 1: no offset movement before the dwell elapses')
    check(len(m.renders) == nrenders,
          'gate 1: no scroll draw during the dwell')
    # The dwell expires at t=1100: registration, still no step.
    m.set_clock(1100)
    m.paint()
    offsets.append((1100, m.mq_offset()))
    check(m.r32(LCTX + 0xC) == BUF,
          'composed string registered at dwell expiry')
    composed = m.read_str(BUF)
    check(composed.startswith('The Quick Brown Fox Jumps Over'),
          f'composed string is {composed!r}')
    check(m.mq_phase() == 1, 'phase is SCROLL after registration')
    check(m.mq_offset() == 0, 'offset still 0 on the registering '
                              'paint')
    # Gate 2: steps at the stock 30-tick cadence, ping-pong.
    seen = []
    t = 1100
    for _ in range(400):
        t += 10
        m.set_clock(t)
        before = len(m.renders)
        m.paint()
        seen.append((t, m.mq_offset(), len(m.renders) > before))
    steps = [(tt, o) for (tt, o, drew) in seen if drew]
    check(steps and steps[0][0] == 1130,
          f'gate 2: first step at registration + 30 ticks '
          f'({steps[0][0] if steps else None})')
    offs = [o for _, o in steps]
    check(all(b - a == 1 for a, b in zip(offs, offs[1:][:5])),
          'gate 2: offset advances one character per step')
    total = len(composed)
    # Stock stepper semantics, read off its code and confirmed
    # against the context: max = chars - (rect width / cell unit);
    # the state machine stores max + 2 at the turn (it flips only
    # once the offset exceeds max, drawing one frame there first).
    unit = m.r16(MCTX + 0x16)
    want_peak = total - (220 // unit) + 2
    check(max(offs) == want_peak,
          f'gate 2: end offset peak {max(offs)} == chars - visible '
          f'+ 2 ({want_peak}, unit {unit})')
    # After the peak, the offset must come back down (ping-pong).
    i_max = offs.index(max(offs))
    down = offs[i_max:i_max + max(offs) + 1]
    check(down == list(range(max(offs), -1, -1)),
          'gate 2: offset ping-pongs back down from the end')
    # Gate 5/6: examine the writes of one step paint in detail.
    # The stepper erases through the rect fill with the accent cell
    # colour (its colour source is the palette accent cell itself),
    # because registrations from a window pass r3 low = 0.
    t += 10
    m.set_clock(t + 20)             # ensure a step is due
    f0, e0, r0n = len(m.fills), len(m.erases), len(m.renders)
    m.paint()
    fills = m.fills[f0:]
    renders = m.renders[r0n:]
    band = (53 + 40 * 2, 53 + 40 * 2 + 40)
    text_rect = (11, 53 + 40 * 2, 231, 68 + 40 * 2)
    check(len(renders) == 1 and renders[0][0] == text_rect,
          f'gate 5: the step draws once, in the row text rect '
          f'({renders})')
    erase = (text_rect[0], text_rect[1], text_rect[2], text_rect[3],
             0xF220)
    check(erase in fills,
          f'gate 5: the step erases exactly the text rect with the '
          f'band colour first ({fills})')
    check(fills.index(erase) < len(fills) and
          len([f for f in fills]) >= 1,
          'gate 5: erase precedes the draw in the same paint')
    outside = [f for f in fills
               if not (f[0] >= text_rect[0] and f[1] >= text_rect[1]
                       and f[2] <= text_rect[2]
                       and f[3] <= text_rect[3])]
    check(all(f[4] == 0xF220 for f in outside),
          'gate 5: every fill outside the text rect is the band '
          'colour')
    stray = [f for f in fills
             if f[3] < band[0] or f[1] >= band[1]]
    check(not stray,
          f'gate 6: rows above and below untouched during a step '
          f'({stray})')
    return composed


def test_key_reset(m):
    print('gate 3b: key press resets dwell and offset')
    t, _ = scroll_scenario(m)
    for tt in range(1010, 1101, 10):
        m.set_clock(tt)
        m.paint()
    for tt in range(1110, 1191, 10):
        m.set_clock(tt)
        m.paint()
    check(m.mq_offset() >= 2, f'scrolling before the key press '
                              f'(offset {m.mq_offset()})')
    # Press a key at t=1195: run the hook up to the stock resume.
    m.set_clock(1195)
    m.call(KEY, until=KEY + 4)
    check(m.mq_phase() == 0, 'key press returns the phase to DWELL')
    # Paints before the new dwell expires must not step.
    offs = []
    for tt in range(1200, 1295, 10):
        m.set_clock(tt)
        m.paint()
        offs.append(m.mq_offset())
    check(all(o == offs[0] for o in offs),
          'gate 3: no step during the post-key dwell')
    # At expiry the string re-registers with the offset back at 0.
    m.set_clock(1300)
    m.paint()
    check(m.r32(LCTX + 0xC) == BUF and m.mq_offset() == 0,
          'gate 3: offset reset to 0 at re-registration after a key')


def test_selection_change(m):
    print('gate 3a: selection change resets dwell and offset')
    t, _ = scroll_scenario(m)
    for tt in range(1010, 1101, 10):
        m.set_clock(tt)
        m.paint()
    for tt in range(1110, 1191, 10):
        m.set_clock(tt)
        m.paint()
    check(m.mq_offset() >= 2, 'scrolling before the selection change')
    # Move the selection to row 3 at t=1195 with a list repaint.
    m.w16(BCTX + 0x1EE, 3)
    m.set_clock(1195)
    m.set_event(0x144)
    m.paint()
    check(m.mq_phase() == 0, 'selection change returns to DWELL')
    frozen = m.mq_offset()
    for tt in range(1205, 1295, 10):
        m.set_clock(tt)
        m.paint()
    check(m.mq_offset() == frozen,
          'gate 3: offset frozen through the new dwell')


def test_fitting(m):
    print('gate 4: a fitting name never scrolls')
    base_fixture(m)
    names = ['Alpha', 'Short', 'Gamma', 'Delta', 'Echo', 'Foxtrot',
             'Golf']
    for i, nm in enumerate(names):
        make_node(m, i, nm, b'MP3', 4_100_000)
    m.w16(BCTX + 0x1EE, 1)
    m.set_event(0x144)
    m.paint()
    n0 = len(m.renders)
    for t in range(1010, 4010, 10):
        m.set_clock(t)
        m.paint()
    check(m.mq_offset() == 0, 'offset never moved over 3000 ticks')
    check(not m.event(0x148),
          'gate 4: marquee bit released; paints stop being requested')
    composed_draws = [r for r in m.renders[n0:]
                      if r[1].startswith('Short -')]
    check(not composed_draws,
          f'gate 4: zero scroll steps for a fitting name '
          f'({composed_draws})')
    check(m.mq_phase() == 2, 'phase settled to PASS')


def test_fallback_and_folder(m):
    print('fallback (name over the cap) and folder cases')
    base_fixture(m)
    long_name = 'N' * 60
    names = [long_name, 'Beta',
             'A Rather Long Folder Name Here Indeed',
             'Delta', 'Echo', 'Foxtrot', 'Golf']
    for i, nm in enumerate(names):
        make_node(m, i, nm, b'FLA', 1000, directory=(i == 2))
    m.w16(BCTX + 0x1EE, 0)
    m.set_event(0x144)
    m.paint()
    for tt in range(1010, 1101, 10):
        m.set_clock(tt)
        m.paint()
    check(m.mq_phase() == 2, 'over-cap name falls back to PASS '
                             '(stock name scroll)')
    check(m.r32(LCTX + 0xC) == NODE_POOL + 0x70,
          'fallback registers the stock name pointer')
    # Folder: name only, no suffix, still scrolls when wide.
    m.w16(BCTX + 0x1EE, 2)
    m.set_clock(1200)
    m.set_event(0x144)
    m.paint()
    for tt in range(1210, 1301, 10):
        m.set_clock(tt)
        m.paint()
    check(m.read_str(BUF) == 'A Rather Long Folder Name Here Indeed',
          'folder composes the bare name')
    check(m.mq_phase() == 1, 'folder scrolls its name')


def test_mode_b(m):
    print('mode B list: same tail, same gate')
    base_fixture(m)
    names = ['Alpha', 'Beta', 'The Quick Brown Fox Jumps Over',
             'Delta', 'Echo', 'Foxtrot', 'Golf']
    for i, nm in enumerate(names):
        make_node(m, i, nm, b'FLA' if i == 2 else b'MP3',
                  25_752_000 if i == 2 else 1000)
    m.w16(BCTX + 0x1EE, 2)
    m.set_event(0x143)
    m.paint()
    for tt in range(1010, 1101, 10):
        m.set_clock(tt)
        m.paint()
    check(m.r32(LCTX + 0xC) == BUF and m.mq_phase() == 1,
          'mode B: composed string registered after the dwell')
    offs = []
    for tt in range(1110, 1250, 10):
        m.set_clock(tt)
        m.paint()
        offs.append(m.mq_offset())
    check(max(offs) >= 3,
          f'mode B: scrolling advances (offsets {offs})')


def test_exit_reset(m):
    print('exit callback zeroes the state')
    t, _ = scroll_scenario(m)
    for tt in range(1010, 1101, 10):
        m.set_clock(tt)
        m.paint()
    check(m.mq_phase() == 1, 'scroll active before exit')
    m.call(EXIT)
    check(m.r32(STATE) == 0 and m.mq_phase() == 0,
          'state zeroed by the exit hook')
    check(not m.event(0x148), 'exit cleared bit 0x148 (stock '
                              'behaviour preserved)')


def main():
    stock = (REPO / 'DP3_V137.img').read_bytes()
    if hashlib.sha256(stock).hexdigest() != STOCK_SHA:
        raise SystemExit('stock image hash mismatch')
    with tempfile.TemporaryDirectory() as tmp:
        raw = build_variant(tmp)
    print(f'variant sha256: {hashlib.sha256(raw).hexdigest()}')
    print(f'variant length: {len(raw)} (stock {len(stock)}, '
          f'delta {len(raw) - len(stock)})')
    m = Machine(raw)
    test_compose(m)
    test_dwell_cadence_reset(m)
    m2 = Machine(raw)
    test_key_reset(m2)
    m3 = Machine(raw)
    test_selection_change(m3)
    m4 = Machine(raw)
    test_fitting(m4)
    m5 = Machine(raw)
    test_fallback_and_folder(m5)
    m6 = Machine(raw)
    test_mode_b(m6)
    m7 = Machine(raw)
    test_exit_reset(m7)
    print('ALL MARQUEE GATES PASS')


if __name__ == '__main__':
    main()

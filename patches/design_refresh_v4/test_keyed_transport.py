#!/usr/bin/env python3
"""Emulation gates for the design refresh v4 transport repoint.

Runs real module 0, 18 and 27 code from the stock image and from
an image built in memory with the default manifest plus the eight
repoint patches plus v4-glyphs.json (the documented recipe; the
built image is not written to disk). The pixel store 0x03063E60
and the staging copy 0x03053F5E are modelled as in prove_keying.py.

Gates:
  (a)  chunking: a synthetic 32x32 resource (1024 pixels, over the
       wrapper's 600-halfword staging chunk) through the keyed
       helper 0x03063A08 emits exactly its non-0xF800 pixels, each
       at the correct coordinate, black pixels included.
  (a2) the helper applies the light theme +166 remap exactly like
       DrawImageAt (shared descriptor resolver).
  (b)  the patched painter's transport segment emits no surround:
       every store a family glyph draw produces is one of that
       glyph's ink pixels, and the pre-rendered row composites
       (resources 155 and 156 are 240x32 row images) land as
       exactly their ink pixels through the keyed path, the two
       always-overlaid slots contributing nothing. Stock control
       included.
  (c)  ghosting: the transport row is painted twice over a
       modelled framebuffer that starts at the theater-derived
       ground 0x7222, flipping one state-driven glyph between
       paints, under three paint cycles (see the case prints).
  (d)  the keyed composites in the B=0 and B=1 states, dark and
       light: nothing outside the glyph shapes lands, the glyph
       ink matches the generated composites exactly, the slots
       the segment overlays show the overlay glyph, and in B=0
       the centre overlay still draws its v4 glyph.

Also prints an informational census of event posters outside the
painter, from a byte scan of every module code segment.

Needs FOSI_ECPATCH_DIR for the vorbis75 transplant in the build.
"""
import hashlib
import importlib.util
import json
import os
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import *

STOCK_SHA = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
END = 0x030EF000
STORE, DMA = 0x03063E60, 0x03053F5E
DRAWAT, HELPER, FILL = 0x0306354A, 0x03063A08, 0x030632FA
RES, RES_CELL = 0x03080000, 0x0302328C
SAVEINFO, EVENTS = 0x030232A0, 0x03023CF8
STATE_A, STATE_B, PLAY_CELL = 0x0302314A, 0x0302314B, 0x03023924
GROUND_CELL, DSTRUCT = 0x03004400, 0x030238D0
PAINTER, SEG_END = 0x0307EF7B, 0x0307F8F4
KEY, GROUND = 0xF800, 0x7222

RAW = (ROOT / 'DP3_V137.img').read_bytes()
assert hashlib.sha256(RAW).hexdigest() == STOCK_SHA, 'stock SHA gate'


def build_v4_image():
    spec = importlib.util.spec_from_file_location(
        'fwbuild', ROOT / 'patches' / 'framework' / 'build.py')
    fb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fb)
    patches = fb.load_manifest(HERE / 'manifest-v4.txt')
    names = fb.load_transplant_names(
        ROOT / 'patches' / 'framework' / 'patches' / 'transplants.txt')
    assert names == ['vorbis75'], names
    theme = json.loads((HERE / 'v4-glyphs.json').read_text())
    ecp = os.environ.get('FOSI_ECPATCH_DIR')
    out, report = fb.build_image(
        RAW, patches, fb.DEFAULT_BUILD_DATE, transplants=names,
        ecpatch_dir=Path(ecp) if ecp else None, theme_config=theme)
    return out, report['output_sha256']


class Machine:
    def __init__(self, image_bytes, real_store=False):
        self.im = Image(image_bytes)
        self.raw = image_bytes
        self.entries = {e['id']: e for e in self.im.images()}
        u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        u.mem_map(0x03000000, 0x500000)
        u.mem_map(0xE000E000, 0x1000)
        for idx in (0, 18, 27):
            m = self.im.modules[idx]
            for kind in ('code', 'data'):
                off, size = self.im.module_region(idx, kind)
                if size:
                    u.mem_write(m[f'{kind}_exec'],
                                image_bytes[off:off + size])
        self.u = u
        self.stores = []        # (col, row, colour)
        self.store_tags = []    # drawlog length at each store
        self.drawlog = []       # ('draw', fn, id, x, y) / ('fill', ...)
        self.real_store = real_store

        def hook(uc, addr, size, user):
            if addr == STORE:
                # record only: the store itself must execute, because
                # it advances the display cursor after each pixel
                # (the mode 0x10 bitmap path depends on that)
                col = struct.unpack('<H', uc.mem_read(DSTRUCT + 8, 2))[0]
                row = struct.unpack('<H', uc.mem_read(DSTRUCT + 0xA, 2))[0]
                self.stores.append(
                    (col, row, uc.reg_read(UC_ARM_REG_R0) & 0xFFFF))
                self.store_tags.append(len(self.drawlog))
            elif addr == DMA:
                src, dst, n = (uc.reg_read(r) for r in
                               (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2))
                if n:
                    uc.mem_write(dst, bytes(uc.mem_read(src, n)))
                uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
            elif addr in (DRAWAT, HELPER):
                self.drawlog.append(('draw', addr,
                                     uc.reg_read(UC_ARM_REG_R0),
                                     uc.reg_read(UC_ARM_REG_R1),
                                     uc.reg_read(UC_ARM_REG_R2)))
            elif addr == FILL:
                sp = uc.reg_read(UC_ARM_REG_SP)
                self.drawlog.append(('fill',) + tuple(
                    uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                             UC_ARM_REG_R2, UC_ARM_REG_R3))
                    + (struct.unpack('<I', uc.mem_read(sp, 4))[0],))
            elif addr == SEG_END:
                uc.emu_stop()
        u.hook_add(UC_HOOK_CODE, hook)

    def stage(self, ids):
        """Stage descriptors and pixel data for the given resource
        ids from this machine's image, at compact offsets."""
        self.u.mem_write(RES_CELL, struct.pack('<I', RES))
        off = 0x2000
        for rid in ids:
            e = self.entries[rid]
            data = self.raw[e['data_offset']:e['data_offset'] + e['size']]
            desc = struct.pack('<4H2I', e['width'], e['height'], 0, 0,
                               e['size'], off)
            self.u.mem_write(RES + 0x20 + rid * 16, desc)
            self.u.mem_write(RES + off, data)
            off += e['size'] + 0x40

    def call(self, addr, r0=0, r1=0, r2=0):
        u = self.u
        sp = 0x030F0000 - 0x100
        for reg, val in ((UC_ARM_REG_R0, r0), (UC_ARM_REG_R1, r1),
                         (UC_ARM_REG_R2, r2), (UC_ARM_REG_SP, sp),
                         (UC_ARM_REG_LR, END | 1)):
            u.reg_write(reg, val)
        u.emu_start(addr | 1, END, count=20000000)
        assert u.reg_read(UC_ARM_REG_PC) == END

    def set_event(self, n):
        addr = EVENTS + (n // 32) * 4
        word = struct.unpack('<I', self.u.mem_read(addr, 4))[0]
        self.u.mem_write(addr, struct.pack('<I', word | (1 << (n % 32))))

    def painter(self, state_a, state_b, play, mode=0, media=0, theme=0,
                events=(0x43,), ground=None):
        u = self.u
        sp = 0x030F0000
        u.mem_write(sp - 0x100, bytes(0x200))
        u.mem_write(sp + 0x3C, struct.pack('<I', 320))
        u.mem_write(sp + 0x38, struct.pack('<I', 240 << 16))
        u.mem_write(sp + 0x64, struct.pack('<I', END | 1))
        u.mem_write(STATE_A, bytes([state_a]))
        u.mem_write(STATE_B, bytes([state_b]))
        u.mem_write(PLAY_CELL, struct.pack('<H', play))
        u.mem_write(SAVEINFO + 0x1A, bytes([media]))
        u.mem_write(SAVEINFO + 0x61, bytes([mode]))
        u.mem_write(SAVEINFO + 0x2D8, bytes([theme]))
        if ground is not None:
            u.mem_write(GROUND_CELL, struct.pack('<H', ground))
        for n in events:
            self.set_event(n)
        for reg, val in ((UC_ARM_REG_R5, 0x03026CA0),
                         (UC_ARM_REG_R8, 0x030043FC),
                         (UC_ARM_REG_R9, 0x030247E4),
                         (UC_ARM_REG_R10, SAVEINFO),
                         (UC_ARM_REG_R11, sp - 0x100),
                         (UC_ARM_REG_SP, sp), (UC_ARM_REG_LR, END | 1)):
            u.reg_write(reg, val)
        self.stores.clear()
        self.store_tags.clear()
        self.drawlog.clear()
        u.emu_start(PAINTER | 1, END, count=60000000)


def glyph_words(image_bytes, rid):
    im = Image(image_bytes)
    e = {x['id']: x for x in im.images()}[rid]
    return struct.unpack_from('>1024H', image_bytes, e['data_offset'])


def ink_set(words, x0, y0):
    return {(x0 + i % 32, y0 + i // 32) for i, w in enumerate(words)
            if w != KEY}


def fb_addr(m, col, row):
    """The store's address math, from its disassembly: the display
    is two surfaces (rows 0..239 and 240..319), paged by the
    halfword at 0x030238B8 (0 in these runs)."""
    a = struct.unpack('<H', m.u.mem_read(0x030238B8, 2))[0]
    if row < 240:
        return 0x030065A8 + a * 115200 + row * 480 + col * 2
    return 0x0306F224 + a * 38400 + (row - 240) * 480 + col * 2


def fb_fill(m, colour):
    u = m.u
    for row in range(320):
        base = fb_addr(m, 0, row)
        u.mem_write(base, struct.pack('<H', colour) * 240)


def fb_read(m, x0, y0, w, h):
    out = {}
    for y in range(y0, y0 + h):
        data = m.u.mem_read(fb_addr(m, x0, y), w * 2)
        for x in range(w):
            out[(x0 + x, y)] = struct.unpack_from('<H', data, x * 2)[0]
    return out


# ---------------------------------------------------------------- gates

def gate_a():
    """(a) chunking and (a2) remap, on the stock image."""
    px = []
    for i in range(1024):
        if i % 5 == 4:
            px.append(KEY)
        elif i % 97 == 0:
            px.append(0x0000)
        else:
            px.append(0x2000 + (i & 0x3FF))
    m = Machine(RAW)
    m.u.mem_write(RES_CELL, struct.pack('<I', RES))
    desc = struct.pack('<4H2I', 32, 32, 0, 0, 2048, 0x2000)
    m.u.mem_write(RES + 0x20 + 3 * 16, desc)
    m.u.mem_write(RES + 0x2000, struct.pack('>1024H', *px))
    m.call(HELPER, 3, 10, 20)
    want = [(10 + i % 32, 20 + i // 32, v) for i, v in enumerate(px)
            if v != KEY]
    assert m.stores == want, 'chunked helper emission mismatch'
    print(f'(a) PASS: helper emitted {len(m.stores)} of 1024 pixels '
          f'({1024 - len(want)} key pixels skipped), every non-key '
          f'pixel at its exact coordinate, black pixels included')
    # (a2) remap parity between DrawImageAt and the helper
    for fn, name in ((DRAWAT, 'DrawImageAt'), (HELPER, 'helper')):
        got = {}
        for theme in (0, 1):
            m = Machine(RAW)
            m.u.mem_write(RES_CELL, struct.pack('<I', RES))
            for rid, base in ((159, 0xAAAA), (325, 0xBBBB)):
                d = struct.pack('<4H2I', 4, 2, 0, 0, 16,
                                0x2000 + (rid - 159) * 0x100)
                m.u.mem_write(RES + 0x20 + rid * 16, d)
                m.u.mem_write(RES + 0x2000 + (rid - 159) * 0x100,
                              struct.pack('>8H', *([base] * 8)))
            m.u.mem_write(SAVEINFO + 0x2D8, bytes([theme]))
            m.call(fn, 159, 7, 9)
            got[theme] = [c for _, _, c in m.stores]
        assert got[0] == [0xAAAA] * 8 and got[1] == [0xBBBB] * 8, name
        print(f'(a2) {name}: id 159 resolves to 159 in the dark theme '
              f'and to 325 in the light theme')
    print('(a2) PASS: the keyed helper shares the resolver remap')


def res_words(image_bytes, rid):
    im = Image(image_bytes)
    e = {x['id']: x for x in im.images()}[rid]
    return (e['width'], e['height'],
            struct.unpack_from(f'>{e["size"] // 2}H', image_bytes,
                               e['data_offset']))


def last_wins(stores, x0, y0, w, h):
    out = {}
    for c, r, v in stores:
        if x0 <= c < x0 + w and y0 <= r < y0 + h:
            out[(c, r)] = v
    return out


def first_wins(stores, x0, y0, w, h):
    out = {}
    for c, r, v in stores:
        if x0 <= c < x0 + w and y0 <= r < y0 + h:
            out.setdefault((c, r), v)
    return out


def gate_b(v4):
    ids = [155, 156] + list(range(157, 182)) + list(range(286, 290))
    # stock control: the centre play draw is opaque
    m = Machine(RAW)
    m.stage(ids)
    m.painter(state_a=0, state_b=0, play=1)
    stock_play = glyph_words(RAW, 169)
    want = {(104 + i % 32, 275 + i // 32): w for i, w in
            enumerate(stock_play)}
    got = last_wins(m.stores, 104, 275, 32, 32)
    assert got == want, 'stock centre mismatch'
    print(f'(b) stock control: the centre rect ends as the full '
          f'1024-pixel resource 169 under DrawImageAt, including '
          f'its {sum(1 for w in stock_play if w == 0x10A2)} surround '
          f'pixels of 0x10A2')
    # patched: same configuration
    m = Machine(v4)
    m.stage(ids)
    m.painter(state_a=0, state_b=0, play=1)
    assert not any(v == KEY for _, _, v in m.stores), 'a key pixel landed'
    # resources 155/156 are pre-rendered 240x32 row composites (the
    # B=0 and B=1 row states). In the v4 set they are keyed like
    # the single glyphs, so the composite draw must emit exactly
    # its ink pixels and nothing else; the centre slot is all
    # key (the 168/169 overlay is the centre glyph), so the centre
    # rect ends as the overlay's ink alone.
    sw, sh, strip_words = res_words(v4, 155)
    assert (sw, sh) == (240, 32)
    strip_ink = {(i % 240, 275 + i // 240): w
                 for i, w in enumerate(strip_words) if w != KEY}
    kc = next(i for i, e in enumerate(m.drawlog)
              if e[0] == 'draw' and e[2] == 155)
    comp_stores = [s for s, g in zip(m.stores, m.store_tags)
                   if g == kc + 1]
    assert {(c, r): v for c, r, v in comp_stores} == strip_ink, \
        'composite ink mismatch'
    assert len(comp_stores) == len(strip_ink)
    v4_play = glyph_words(v4, 169)
    ink = ink_set(v4_play, 104, 275)
    want = {pos: 0xFFFF for pos in ink}
    got = last_wins(m.stores, 104, 275, 32, 32)
    assert got == want, 'patched centre mismatch'
    # attribute stores to the play draw itself via the draw tags:
    # during draw entry k the drawlog already holds k + 1 entries
    k = next(i for i, e in enumerate(m.drawlog)
             if e[0] == 'draw' and e[2] == 169)
    play_stores = [s for s, g in zip(m.stores, m.store_tags)
                   if g == k + 1]
    assert {(c, r, v) for c, r, v in play_stores} == \
        {(x, y, 0xFFFF) for x, y in ink}
    assert len(play_stores) == len(ink)
    n_ink = len(play_stores)
    mw, mh, res286 = res_words(v4, 286)
    k286 = next(i for i, e in enumerate(m.drawlog)
                if e[0] == 'draw' and e[2] == 286)
    mode = [s for s, g in zip(m.stores, m.store_tags) if g == k286 + 1]
    want_mode = {(53 + i % mw, 5 + i // mw) for i, w in enumerate(res286)
                 if w != KEY}
    assert {(c, r) for c, r, _ in mode} == want_mode
    print(f'(b) PASS: patched segment: the pre-rendered row '
          f'composite (resource 155, 240x32) emits exactly its '
          f'{len(strip_ink)} ink pixels through the keyed path '
          f'({7680 - len(strip_ink)} key pixels skipped, none '
          f'outside the glyph shapes); the centre play draw '
          f'emitted exactly its {n_ink} ink pixels and no '
          f'surround; the pre-existing keyed mode indicator '
          f'emitted {len(mode)} pixels; no 0xF800 store anywhere '
          f'in {len(m.stores)} stores')
    # second configuration: three family draws in one segment pass
    m = Machine(v4)
    m.stage(ids)
    m.painter(state_a=1, state_b=2, play=1)
    assert not any(v == KEY for _, _, v in m.stores)
    regions = {'slot0 chevron 157': ink_set(glyph_words(v4, 157), 0, 275),
               'repeat 174': ink_set(glyph_words(v4, 174), 54, 275),
               'plus 180': ink_set(glyph_words(v4, 180), 104, 275),
               'computed chevron 157': ink_set(glyph_words(v4, 157),
                                               4, 275)}
    landed = {(c, r) for c, r, v in m.stores if v == 0xFFFF and r >= 275}
    union = set().union(*regions.values())
    assert landed == union, (sorted(landed - union)[:5],
                             sorted(union - landed)[:5])
    counts = {k: len(v) for k, v in regions.items()}
    print(f'(b) PASS: state A=1, B=2 pass: ink stores in the row '
          f'regions match the union of the four glyph shapes '
          f'exactly ({counts}); nothing else landed in the row')


def gate_c(v4):
    ids = [155, 156] + list(range(157, 182)) + list(range(286, 290))
    centre_rect = (104, 275, 32, 32)
    slot_rect = (4, 275, 32, 32)

    # C1: B=0 states. The row strip redraw precedes the glyphs.
    m = Machine(v4, real_store=True)
    m.stage(ids)
    fb_fill(m, GROUND)
    m.painter(state_a=0, state_b=0, play=1, ground=GROUND)
    # validate the framebuffer address model against the recorded
    # stores before trusting any screen readback in this gate
    last = {}
    for c, r, v in m.stores:
        if r >= 275:
            last[(c, r)] = v
    bad = [(p, v) for p, v in last.items()
           if struct.unpack('<H', m.u.mem_read(fb_addr(m, *p), 2))[0] != v]
    assert not bad, f'framebuffer model mismatch at {bad[:4]}'
    print(f'(c) framebuffer model validated: all {len(last)} '
          f'last-store values in the row match RAM readback')
    m.painter(state_a=0, state_b=0, play=0, ground=GROUND)
    snap = fb_read(m, *centre_rect)
    v4_pause = glyph_words(v4, 168)
    v4_play = glyph_words(v4, 169)
    want = {}
    for i in range(1024):
        pos = (104 + i % 32, 275 + i // 32)
        want[pos] = 0xFFFF if (v4_pause[i] != KEY
                               or v4_play[i] != KEY) else GROUND
    ghosts = {p: v for p, v in snap.items() if v != want[p]}
    assert not ghosts, ghosts
    leftover = sum(1 for i in range(1024)
                   if v4_play[i] != KEY and v4_pause[i] == KEY)
    print(f'(c1) B=0, play to pause, segment-only repaint: the '
          f'centre rect ends as ground plus the union of the two '
          f'centre glyphs exactly, so {leftover} play-ink pixels '
          f'survive under the pause glyph. With the keyed '
          f'composite the B=0 centre slot carries no ink of its '
          f'own (the 168/169 overlay is the centre glyph), so a '
          f'segment-only flip leaves the old glyph\'s uncovered '
          f'ink, the same ghosting class as (c2); the full '
          f'repaint cycle of (c3) covers it. With the stock '
          f'composite this cycle left 0 ghosts, because the '
          f'opaque composite redraw erased the centre first.')

    # C2: B=2 states. No strip; segment-only repaint of a flip at
    # the state-driven computed slot (A selects id and x).
    m = Machine(v4, real_store=True)
    m.stage(ids)
    fb_fill(m, GROUND)
    m.painter(state_a=1, state_b=2, play=1, ground=GROUND)
    before = fb_read(m, *slot_rect)
    m.painter(state_a=11, state_b=2, play=1, ground=GROUND)
    after = fb_read(m, *slot_rect)
    chev0 = ink_set(glyph_words(v4, 157), 0, 275)
    pause4 = ink_set(glyph_words(v4, 167), 4, 275)
    ghosts = {p: v for p, v in after.items()
              if v == 0xFFFF and p not in chev0 and p not in pause4
              and p in ink_set(glyph_words(v4, 157), 4, 275)}
    print(f'(c2) B=2, chevron to pause at the computed slot, '
          f'segment-only repaint: {len(ghosts)} ghost pixels '
          f'survive. They are exactly the first glyph\'s ink '
          f'positions that the second paint\'s draws (chevron at '
          f'(0,275), pause at (4,275)) do not cover:')
    for p in sorted(ghosts)[:12]:
        print(f'      ghost at ({p[0]}, {p[1]}): paint 1 left '
              f'{before[p]:#06x} (ink), paint 2 left it at '
              f'{after[p]:#06x} instead of restoring the ground')
    assert ghosts, 'expected ghosting in the segment-only B=2 cycle'

    # C3: the same flip under a full repaint cycle (event 0x39).
    # The cycle is staged as its row-relevant sequence, because a
    # single end-to-end call cannot complete in this harness: after
    # the ground fill, the painter's track-info path dereferences
    # the storage volume table (null with no card mounted) and
    # faults at 0x0305DD10. That limit is in the info path, not the
    # transport path; what the cycle does to the row is executed
    # here in order: paint 1 (segment only), paint 2 (the real
    # full-repaint call, which fills the whole screen from the
    # ground cell first, then faults in the info path), paint 3
    # (the segment the repaint block posts event 0x43 for, run
    # over the filled framebuffer: a fresh machine initialised to
    # the filled screen, which is pixel-identical to what paint
    # 2's fill left, since the fill covers the whole screen).
    from unicorn import UcError
    m = Machine(v4, real_store=True)
    m.stage(ids + [133, 282])
    m.u.mem_map(0x40000000, 0x200000)   # peripheral register page
    fb_fill(m, GROUND)
    m.painter(state_a=1, state_b=2, play=1, ground=GROUND)
    fault = None
    try:
        m.painter(state_a=11, state_b=2, play=1, media=1,
                  events=(0x39,), ground=GROUND)
    except UcError as e:
        fault = (str(e), m.u.reg_read(UC_ARM_REG_PC))
    log = list(m.drawlog)
    fill_stores = [s for s, g in zip(m.stores, m.store_tags) if g == 1]
    assert log and log[0][0] == 'fill' and log[0][1:5] == (0, 0, 239, 319), log[:2]
    assert len(fill_stores) == 240 * 320 and \
        all(v == GROUND for _, _, v in fill_stores), len(fill_stores)
    print(f'(c3) full repaint call: the first draw of the call is '
          f'the full-screen ground fill (0, 0, 239, 319) from the '
          f'cell value 0x7222, executed as {len(fill_stores)} '
          f'stores before any other draw. The call then faults in '
          f'the track-info path ({fault[0]} at {fault[1]:#x}: the '
          f'storage glue reads a null volume entry; no card is '
          f'mounted in this harness), before the transport segment. '
          f'The repaint block at 0x0307F104..0x0307F132 posts event '
          f'0x43 in the same call, so the segment runs after the '
          f'fill in a real cycle.')
    m = Machine(v4, real_store=True)
    m.stage(ids)
    fb_fill(m, GROUND)
    m.painter(state_a=11, state_b=2, play=1, ground=GROUND)
    after = fb_read(m, *slot_rect)
    want = {p: (0xFFFF if p in chev0 or p in pause4 else GROUND)
            for p in after}
    ghosts = {p: v for p, v in after.items() if v != want[p]}
    assert not ghosts, ghosts
    print('(c3) the segment posted by that cycle, run over the '
          'filled framebuffer: 0 ghost pixels; the rect ends as '
          'ground plus the second paint\'s glyph ink exactly.')
    print('(c) verdict: ghosting is real under a segment-only '
          'repaint in the B>=2 states (no composite, no fill '
          'precedes the segment); the stock full repaint cycle '
          'refills the ground first and leaves no ghosts. Which '
          'events a real state change posts outside the painter is '
          'not provable from the painter alone; see the poster '
          'census below.')


def gate_d(v4):
    """(d) the keyed composites in the B=0 and B=1 states, dark
    and light, over a framebuffer that starts at ground 0x7222:
    the composite draw emits exactly the composite's ink, no
    pixel outside the glyph shapes lands (the framebuffer keeps
    the ground there), and the slots the segment overlays show
    the overlay glyph."""
    ids = ([155, 156] + list(range(157, 182)) + list(range(286, 290))
           + [321, 322] + list(range(323, 348)) + list(range(452, 456)))
    row = (0, 275, 240, 32)

    def run(state_b, theme):
        m = Machine(v4, real_store=True)
        m.stage(ids)
        fb_fill(m, GROUND)
        m.painter(state_a=0, state_b=state_b, play=1, theme=theme,
                  ground=GROUND)
        assert not any(v == KEY for _, _, v in m.stores), \
            'a key pixel landed'
        return m

    def inkmap(rid, w, x0=0):
        _, _, words = res_words(v4, rid)
        return {(x0 + i % w, 275 + i // w): v
                for i, v in enumerate(words) if v != KEY}

    def comp_stores(m, passed_id):
        k = next(i for i, e in enumerate(m.drawlog)
                 if e[0] == 'draw' and e[2] == passed_id)
        return {(c, r): v for s, g in zip(m.stores, m.store_tags)
                if g == k + 1 for c, r, v in [s]}

    def check(fb, want):
        bad = {p: (fb[p], want.get(p, GROUND)) for p in fb
               if fb[p] != want.get(p, GROUND)}
        assert not bad, dict(list(bad.items())[:6])

    for theme, shift in ((0, 0), (1, 166)):
        name = 'light' if theme else 'dark'
        c0 = inkmap(155 + shift, 240)
        c1 = inkmap(156 + shift, 240)
        # B=0: the composite plus the centre overlay (169)
        m = run(0, theme)
        stores = comp_stores(m, 155)
        assert stores == c0, f'{name} B=0 composite emission'
        centre = inkmap(169 + shift, 32, x0=104)
        check(fb_read(m, *row), {**c0, **centre})
        print(f'(d) {name} B=0: composite {155 + shift} emitted '
              f'{len(stores)} ink pixels ({7680 - len(c0)} key '
              f'pixels skipped); the row framebuffer is the '
              f'composite ink plus the centre overlay '
              f'{169 + shift} ({len(centre)} ink pixels) over '
              f'ground {GROUND:#06x}, ground preserved at '
              f'{7680 - len(c0) - len(centre)} of 7680 positions')
        # B=1: the composite, with slot 1 overlaid by the play
        # mode's repeat (174 at mode 0) and slot 2 by the plus
        # (180) over the baked minus
        m = run(1, theme)
        stores = comp_stores(m, 156)
        assert stores == c1, f'{name} B=1 composite emission'
        rep = inkmap(174 + shift, 32, x0=54)
        plus = inkmap(180 + shift, 32, x0=104)
        minus = {p: v for p, v in c1.items() if 104 <= p[0] < 136}
        assert set(minus) <= set(plus), 'minus escapes the plus'
        want = {**c1, **rep, **plus}
        check(fb_read(m, *row), want)
        print(f'(d) {name} B=1: composite {156 + shift} emitted '
              f'{len(stores)} ink pixels ({7680 - len(c1)} key '
              f'pixels skipped); slot 1 shows the repeat overlay '
              f'{174 + shift} ({len(rep)} ink pixels), slot 2 the '
              f'plus overlay {180 + shift} ({len(plus)} ink '
              f'pixels, the baked minus inside it at '
              f'{len(minus)} positions); ground preserved at '
              f'{7680 - len(want)} of 7680 positions')
    print('(d) PASS: the B=0 and B=1 rows are glyph ink on the '
          'ground in both themes; no part of the composite '
          'rectangle outside the glyph shapes lands')


def poster_census():
    im = Image(RAW)
    post = 0x0306723C
    hits = {0x39: [], 0x43: []}
    for idx in range(82):
        try:
            off, size = im.module_region(idx, 'code')
        except Exception:
            continue
        base = im.modules[idx]['code_exec']
        code = RAW[off:off + size]
        for p in range(0, len(code) - 8, 2):
            hw1, hw2 = struct.unpack_from('<HH', code, p)
            if (hw1 & 0xF800) != 0xF000 or (hw2 & 0xD000) != 0xD000:
                continue
            s = (hw1 >> 10) & 1
            j1, j2 = (hw2 >> 13) & 1, (hw2 >> 11) & 1
            i1, i2 = (~(j1 ^ s)) & 1, (~(j2 ^ s)) & 1
            delta = ((s << 24) | (i1 << 23) | (i2 << 22)
                     | ((hw1 & 0x3FF) << 12) | ((hw2 & 0x7FF) << 1))
            if s:
                delta -= 1 << 25
            if base + p + 4 + delta != post:
                continue
            for back in (2, 4, 6):
                if p - back < 0:
                    break
                prev = struct.unpack_from('<H', code, p - back)[0]
                if prev in (0x2000 + 0x39, 0x2000 + 0x43):
                    hits[prev - 0x2000].append((idx, base + p))
                    break
    for ev, sites in hits.items():
        outside = [(i, a) for i, a in sites if i != 27]
        print(f'census: event {ev:#x} post sites: {len(sites)} total, '
              f'{len(outside)} outside the painter module: '
              + ', '.join(f'module {i} at {a:#x}' for i, a in outside))


def main():
    v4, sha = build_v4_image()
    print(f'built the documented v4 image in memory: SHA-256 {sha}')
    gate_a()
    gate_b(v4)
    gate_c(v4)
    gate_d(v4)
    poster_census()
    print('ALL GATES DONE')


if __name__ == '__main__':
    main()

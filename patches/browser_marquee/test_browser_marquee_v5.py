#!/usr/bin/env python3
"""Browser marquee v5 gates: the full-screen background model.

The title-led label gates live in the v1 to v3 suites (the tag
suite carries the composition rules). This suite gates what v5
adds: the selected file's album art decoded on the selecting
paint into a single darkened store in the payload window, drawn
behind the whole browser menu through fill substitution.

Gates:
- install: a pictured file's selecting paint ends with the
  background active, the store equal to the reference pipeline's
  raster centre-cropped, sampled and darkened by the payload's
  own integer mixes, and the framebuffer equal to the store's
  expansion (plain slices in the bands, the accent-tinted slice
  in the selected band, the stock text rect on top).
- the enriched label renders on that same first paint, at the
  stock x=11 rect (no shift anywhere in this model).
- darkening and contrast: the per-theme mixes reproduce exactly
  in Python, and the worst-case contrast of the theme text
  colour over the stored pixels clears the floor on the
  brightest and darkest covers constructible.
- fallback: a folder, a picture-less file and an unsupported
  file each end their selecting paint with no background, no
  slice draws, and flat stock fills; moving from a pictured
  selection to a folder restores the exact flat ground.
- creep: a long scripted session (selection moves across two
  albums, scroll steps in both directions, marquee runs to the
  wrap, view toggles) leaves every sampled background pixel
  equal to the current selection's expansion.
- discipline: reselecting the same node costs no second decode;
  A to B to A costs one decode per selection change (the store
  holds one entry); window exit zeroes the state and the key
  entry, and returning re-renders from the current selection.
- restoration: the player pipeline state after a browser
  decode matches the pre-decode snapshot byte for byte.
- mode B: the accent fill site substitutes there too.
"""
import base64
import hashlib
import io
import re
import struct
import sys
import tempfile
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1,
                               UC_ARM_REG_R2, UC_ARM_REG_R3,
                               UC_ARM_REG_SP)

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
import build_marquee as bm
import test_browser_marquee as t1
import test_browser_marquee_tags as t2

check = t2.check
setup = t2.setup
scene = t2.scene
name11 = t2.name11
run_dwell = t2.run_dwell

BCTX = bm.BCTX
LCTX = bm.LCTX
MCTX = bm.MCTX
SENTINEL = t1.SENTINEL
STATE = t2.STATE
MODE = t2.STATE + 0x18
FSOPEN = bm.FSOPEN
FSCLOSE = 0x03058E8E
SEEK = 0x030594A0
SCAN = 0x03082BF6
SETUP = 0x0308389E
CONSUMER = 0x03083B36
SET_D4, SET_D8 = 0x03083A90, 0x03083A8A
REQ = 0x0302598C
DESC, CTX = 0x030259D4, 0x03026CA0
MODE_STR = 0x0306E828
OUTCELL = 0x0304AE00
SAVEINFO = 0x030232A0
PAL_ACCENT3 = 0x030235B8
BG_ACTIVE = bm.BG_ACTIVE
BG_W, BG_H = bm.BG_W, bm.BG_H
ART_Y0, ART_W, ART_H = bm.ART_Y0, bm.ART_W, bm.ART_H

# Layout entries for the payload's locator helper, recomputed
# from the builder's constants in main()'s order.
_probe, _pe = bm.assemble(bm.BASE + 0x1000, bm.BASE + 0x1020)
_code_len = (len(_probe) + 3) & ~3
_st = bm.BASE + _code_len
_bf = _st + bm.STATE_LEN
_et = _bf + bm.BUF_UNITS * 2
_ts = (_et + len(bm.TAG_EXTS) * 3 + 3) & ~3
_kt = (_ts + bm.STRUCT_SPAN + 3) & ~3
_ca = _kt + bm.KEY_ENTRIES * bm.KEY_LEN
_px = _ca + bm.CACHE_ENTRIES * bm.CACHE_ENTRY_LEN
TSTRUCT = _ts
KEYTAB = _kt
ENT = bm.assemble(_st, _bf, _pe,
                  {'struct': _ts, 'cache': _ca, 'keytab': _kt,
                   'exttab': _et, 'picext': _px})[1]
LOCCASE = ENT['loccase']


# ------------------------------------------------ fixtures

_src = (REPO / 'patches' / 'theater' / 'research'
        / 'probe_jpeg.py').read_text()
JPEG = base64.b64decode(
    re.search(r'b64decode\("([A-Za-z0-9+/=]+)"\)', _src).group(1))


def pil_jpeg(rgb, size=(96, 96)):
    from PIL import Image
    im = Image.new('RGB', size, rgb)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=92)
    return buf.getvalue()


BRIGHT_JPEG = pil_jpeg((248, 246, 242))
DARK_JPEG = pil_jpeg((6, 6, 9))


def apic_body(jpeg):
    return b'\x00image/jpeg\x00\x03\x00' + jpeg


def id3(frames):
    body = b''
    for fid, payload in frames:
        body += fid + struct.pack('>I', len(payload)) + b'\x00\x00' \
            + payload
    n = len(body)
    hdr = b'ID3\x03\x00\x00' + bytes([(n >> 21) & 0x7F,
                                      (n >> 14) & 0x7F,
                                      (n >> 7) & 0x7F, n & 0x7F])
    return hdr + body


def cover_mp3(jpeg, title='Cover Title', artist='Cover Artist',
              album='Cover Album'):
    frames = [(b'TIT2', t2.tf(title)), (b'TPE1', t2.tf(artist)),
              (b'TALB', t2.tf(album)), (b'APIC', apic_body(jpeg))]
    return id3(frames) + b'\xff\xfb' + bytes(2048)


PHOTO_MP3 = cover_mp3(JPEG)
BRIGHT_MP3 = cover_mp3(BRIGHT_JPEG, 'Bright Title', 'Bright Artist',
                       'Bright Album')
DARK_MP3 = cover_mp3(DARK_JPEG, 'Dark Title', 'Dark Artist',
                     'Dark Album')


# ------------------------------------------------ machine

class BGMachine(t2.Machine):
    """The v2 machine plus a framebuffer and picture stats. The
    framebuffer is fed from the same leaf arguments the parent
    hook records, observed before the parent models the leaf."""

    def __init__(self, raw):
        super().__init__(raw)
        self.fb = {}
        self.stats = {'open': 0, 'setup': 0, 'consumer': 0,
                      'scan': 0}
        self.u.hook_add(UC_HOOK_CODE, self._stats)

    def _stats(self, uc, addr, size, user):
        if addr == FSOPEN:
            self.stats['open'] += 1
        elif addr == SETUP:
            self.stats['setup'] += 1
        elif addr == CONSUMER:
            self.stats['consumer'] += 1
        elif addr == SCAN:
            self.stats['scan'] += 1

    def _fb_fill(self, x0, y0, x1, y1, val):
        for y in range(max(0, y0), min(320, y1 + 1)):
            for x in range(max(0, x0), min(240, x1 + 1)):
                self.fb[(x, y)] = val

    def _hook(self, uc, addr, size, user):
        if addr == t1.FILL:
            sp = uc.reg_read(UC_ARM_REG_SP)
            args = [uc.reg_read(r) for r in (UC_ARM_REG_R0,
                                             UC_ARM_REG_R1,
                                             UC_ARM_REG_R2,
                                             UC_ARM_REG_R3)]
            colour = struct.unpack('<I', uc.mem_read(sp, 4))[0] \
                & 0xFFFF
            self._fb_fill(args[0], args[1], args[2], args[3],
                          colour)
        elif addr == t1.BITMAP:
            a = [uc.reg_read(r) for r in (UC_ARM_REG_R0,
                                          UC_ARM_REG_R1,
                                          UC_ARM_REG_R2,
                                          UC_ARM_REG_R3)]
            _mode, ptr = struct.unpack('<II', uc.mem_read(
                uc.reg_read(UC_ARM_REG_SP), 8))
            if a[2] and a[3] == 1:
                px = struct.unpack('<%dH' % a[2],
                                   uc.mem_read(ptr, a[2] * 2))
                for i, v in enumerate(px):
                    self.fb[(a[0] + i, a[1])] = v
        elif addr == t1.RENDER:
            rect = struct.unpack('<4H', uc.mem_read(
                uc.reg_read(UC_ARM_REG_R0), 8))
            self._fb_fill(rect[0], rect[1], rect[2], rect[3], -1)
        elif addr == t1.ERASE:
            sp = uc.reg_read(UC_ARM_REG_SP)
            y1 = struct.unpack('<i', uc.mem_read(sp, 4))[0]
            self._fb_fill(uc.reg_read(UC_ARM_REG_R1),
                          uc.reg_read(UC_ARM_REG_R2),
                          uc.reg_read(UC_ARM_REG_R3), y1, -1)
        super()._hook(uc, addr, size, user)

    def bg_active(self):
        return self.r8(STATE + BG_ACTIVE)

    def key_result(self):
        return self.r8(KEYTAB + 0x11)

    def store_rows(self):
        data = bytes(self.u.mem_read(TSTRUCT, BG_W * BG_H * 2))
        px = struct.unpack('<%dH' % (BG_W * BG_H), data)
        return [tuple(px[y * BG_W:(y + 1) * BG_W])
                for y in range(BG_H)]


# ------------------------------------------------ reference

def callx(m, addr, r0=0, r1=0, r2=0, r3=0):
    m.u.reg_write(UC_ARM_REG_SP, t1.STACK_TOP)
    m.u.reg_write(UC_ARM_REG_R0, r0)
    m.u.reg_write(UC_ARM_REG_R1, r1)
    m.u.reg_write(UC_ARM_REG_R2, r2)
    m.u.reg_write(UC_ARM_REG_R3, r3)
    from unicorn.arm_const import UC_ARM_REG_LR
    m.u.reg_write(UC_ARM_REG_LR, SENTINEL)
    m.u.emu_start(addr | 1, SENTINEL, count=6_000_000)
    return m.u.reg_read(UC_ARM_REG_R0)


def open_file(m, cluster, index):
    sp = t1.STACK_TOP - 0x100
    m.u.mem_write(OUTCELL, bytes(0x40))
    for reg, v in ((UC_ARM_REG_R0, OUTCELL),
                   (UC_ARM_REG_R1, cluster),
                   (UC_ARM_REG_R2, index), (UC_ARM_REG_R3, 3),
                   (UC_ARM_REG_SP, sp)):
        m.u.reg_write(reg, v)
    m.u.mem_write(sp, struct.pack('<I', MODE_STR))
    from unicorn.arm_const import UC_ARM_REG_LR
    m.u.reg_write(UC_ARM_REG_LR, SENTINEL | 1)
    m.u.emu_start(FSOPEN | 1, SENTINEL, count=2_000_000)
    return m.u.reg_read(UC_ARM_REG_R0)


def direct_rows(raw, data, ext=b'MP3'):
    """Reference decode at the payload's own request geometry
    (BG_BOX square, destination at the client area's top left):
    the rows the consumer blits."""
    m = BGMachine(raw)
    setup(m)
    scene(m, {0: ('Cover Song', ext, len(data), 0)})
    m.add_file(7, 0, data, name11(ext), 2)
    h = open_file(m, 7, 0)
    assert h >= 0, 'reference open failed'
    callx(m, SEEK, r0=0, r1=0, r2=h)
    m.w32(DESC, 0)
    route = dict(bm.PIC_ROUTES)[ext]
    if route == SCAN:
        size = callx(m, SCAN, r0=h, r1=OUTCELL)
    else:
        size = callx(m, LOCCASE, r0=route, r1=h, r2=OUTCELL)
    check(size and size < 0x80000000, f'reference locate {size}')
    mode = m.r32(OUTCELL)
    m.w32(REQ, bm.BG_BOX)
    m.w32(REQ + 4, bm.BG_BOX)
    m.w32(REQ + 8, 0)
    m.w32(REQ + 0xC, ART_Y0)
    callx(m, SET_D4, r0=0)
    callx(m, SET_D8, r0=1)
    sret = callx(m, SETUP, r0=h, r1=mode)
    check(sret == 1, 'reference setup')
    n0 = len(m.bitmaps)
    for _ in range(80):
        if callx(m, CONSUMER) == 0:
            break
    rows = [b['px'] for b in m.bitmaps[n0:]]
    callx(m, FSCLOSE, r0=h)
    return rows


def mix_dark(px):
    r = ((px >> 11) * 45) // 100
    g = (((px >> 5) & 63) * 45) // 100
    b = ((px & 31) * 45) // 100
    return (r << 11) | (g << 5) | b


def mix_light(px):
    r = ((px >> 11) * 25 + 29 * 75) // 100
    g = (((px >> 5) & 63) * 25 + 59 * 75) // 100
    b = ((px & 31) * 25 + 28 * 75) // 100
    return (r << 11) | (g << 5) | b


def expected_store(rows, light=False):
    """The payload's capture, mirrored: centre crop at the
    store aspect, nearest sample, per-theme mix."""
    mix = mix_light if light else mix_dark
    ph = len(rows)
    pw = len(rows[0])
    if pw * BG_H > ph * BG_W:
        cw, ch = ph * BG_W // BG_H, ph
    else:
        cw, ch = pw, pw * BG_H // BG_W
    x0 = (pw - cw) // 2
    y0 = (ph - ch) // 2
    return [[mix(rows[y0 + (sy * ch) // BG_H][x0 + (sx * cw) // BG_W])
             for sx in range(BG_W)] for sy in range(BG_H)]


def expand(store, x, y):
    """The slice expansion of the store at a panel pixel."""
    return store[(y - ART_Y0) * BG_H // ART_H][x * BG_W // ART_W]


def tint(px, accent):
    r = (((px >> 11) + (accent >> 11)) // 2) << 11
    g = ((((px >> 5) & 63) + ((accent >> 5) & 63)) // 2) << 5
    b = ((px & 31) + (accent & 31)) // 2
    return r | g | b


def luminance(px):
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r = lin((px >> 11) / 31)
    g = lin(((px >> 5) & 63) / 63)
    b = lin((px & 31) / 31)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(px, text):
    la, lb = luminance(px), luminance(text)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# Sample points per band: below the text rect (text occupies
# y 53+40i..68+40i), at the left edge, centre and right edge.
def band_points(i, sel=False):
    y = 40 + 40 * i + 30
    return [(2, y), (120, y), (237, y)]


def check_bands(m, store, sel_row):
    accent = m.r16(PAL_ACCENT3)
    for i in range(7):
        for (x, y) in band_points(i):
            want = expand(store, x, y)
            if i == sel_row:
                want = tint(want, accent)
            got = m.fb.get((x, y))
            check(got == want,
                  f'band {i} pixel ({x},{y}): {got!r} != {want!r}')


# ------------------------------------------------ gates

def test_install(raw, ref):
    print('install: the selecting paint ends with the background '
          'up and the label rendered')
    m = BGMachine(raw)
    setup(m)
    scene(m, {0: ('Cover Song', b'MP3', len(PHOTO_MP3), 0)})
    m.add_file(7, 0, PHOTO_MP3, name11(b'MP3'), 2)
    m.w16(BCTX + 0x1EE, 0)
    m.set_event(0x144)
    m.set_clock(1000)
    m.paint()
    check(m.fetches == [(7, 0), (7, 0)],
          f'parse plus one decode probe ({m.fetches})')
    check(m.bg_active() == 1, 'background active after one paint')
    check(m.key_result() == 1, 'key entry holds the picture')
    store = m.store_rows()
    want = expected_store(ref)
    check([list(r) for r in store] == want,
          'store equals the reference capture (crop, sample, '
          'dark mix)')
    check_bands(m, store, sel_row=0)
    labels = [s for (_rect, s) in m.renders]
    check('Cover Title - Cover Artist - Cover Album' in labels,
          f'the enriched label rendered on the selecting paint '
          f'({labels})')
    rects = [r for (r, s) in m.renders
             if s == 'Cover Title - Cover Artist - Cover Album']
    check(rects and rects[0][0] == 11,
          f'the label rect keeps the stock left edge '
          f'({rects})')


def test_darkening_and_contrast(raw, refs):
    print('darkening: exact mixes per theme; contrast floors on '
          'the extreme covers')
    for label, data, ref in (('bright', BRIGHT_MP3, refs['bright']),
                             ('dark', DARK_MP3, refs['dark'])):
        m = BGMachine(raw)
        setup(m)
        scene(m, {0: ('Cover Song', b'MP3', len(data), 0)})
        m.add_file(7, 0, data, name11(b'MP3'), 2)
        m.w16(BCTX + 0x1EE, 0)
        m.set_event(0x144)
        m.paint()
        check(m.bg_active() == 1, f'{label}: background active')
        store = [list(r) for r in m.store_rows()]
        check(store == expected_store(ref),
              f'{label}: dark-theme store matches the mix')
        worst = min(contrast(px, 0xFFFF) for row in store
                    for px in row)
        print(f'    {label} cover, dark theme: worst contrast '
              f'{worst:.2f} (white text)')
        check(worst >= 4.0,
              f'{label}: dark-theme contrast floor ({worst:.2f})')
        # Light theme: selector byte set before the decode.
        m2 = BGMachine(raw)
        setup(m2)
        m2.w8(SAVEINFO + 0x2D8, 1)
        scene(m2, {0: ('Cover Song', b'MP3', len(data), 0)})
        m2.add_file(7, 0, data, name11(b'MP3'), 2)
        m2.w16(BCTX + 0x1EE, 0)
        m2.set_event(0x144)
        m2.paint()
        store2 = [list(r) for r in m2.store_rows()]
        check(store2 == expected_store(ref, light=True),
              f'{label}: light-theme store matches the paper mix')
        worst2 = min(contrast(px, 0x0000) for row in store2
                     for px in row)
        print(f'    {label} cover, light theme: worst contrast '
              f'{worst2:.2f} (black text)')
        check(worst2 >= 7.0,
              f'{label}: light-theme contrast floor ({worst2:.2f})')


def test_fallback(raw):
    print('fallback: unpictured selections keep the exact stock '
          'ground')
    cases = (
        ('folder', ('Some Folder', b'   ', 4096, 0, 2, True), None),
        ('picture-less MP3', ('Plain Song', b'MP3',
                              len(t2.TAGGED_MP3), 0), t2.TAGGED_MP3),
    )
    for label, subj, data in cases:
        m = BGMachine(raw)
        setup(m)
        scene(m, {0: subj})
        if data is not None:
            m.add_file(7, 0, data, name11(b'MP3'), 2)
        m.w16(BCTX + 0x1EE, 0)
        m.set_event(0x144)
        m.paint()
        check(m.bg_active() == 0, f'{label}: no background')
        check(m.key_result() == 2, f'{label}: negative entry')
        check(not m.bitmaps, f'{label}: no slice draws at all')
        accent = m.r16(PAL_ACCENT3)
        check(m.fb.get((120, 70)) == accent,
              f'{label}: selected band is the flat accent')
        # Every pixel the paint did write inside the client
        # area is a stock colour (ground, accent, separator or
        # a text marker): no slice values anywhere. (Points
        # the harness scene never paints read as None and are
        # not the payload's doing.)
        stock_vals = {m.r16(0x030235B4 + 2 * i) for i in range(4)}
        stock_vals |= {0, -1}
        bad = [(pt, v) for pt, v in m.fb.items()
               if 40 <= pt[1] <= 319 and v not in stock_vals]
        check(not bad,
              f'{label}: only stock colours in the client area '
              f'({bad[:3]})')
    # Pictured, then folder: the ground comes back exactly.
    m = BGMachine(raw)
    setup(m)
    nodes = scene(m, {0: ('Cover Song', b'MP3', len(PHOTO_MP3), 0),
                      1: ('Some Folder', b'   ', 4096, 1, 2, True)})
    m.add_file(7, 0, PHOTO_MP3, name11(b'MP3'), 2)
    m.w16(BCTX + 0x1EE, 0)
    m.set_event(0x144)
    m.paint()
    check(m.bg_active() == 1, 'pictured first')
    m.w16(BCTX + 0x1EE, 1)
    m.set_event(0x144)
    m.set_clock(2000)
    m.paint()
    check(m.bg_active() == 0, 'folder selection drops the art')
    for pt in [(2, 70), (120, 110), (237, 310), (60, 200)]:
        check(m.fb.get(pt) == 0,
              f'ground restored at {pt} ({m.fb.get(pt)!r})')
    # The transitional paint ends all-ground (the restore is
    # its final word): every written pixel in the client area
    # is the ground or a text marker, which is the exact stock
    # ground the brief asks for. Later stock behaviour with no
    # background installed is the v1 suite's parity ground.
    bad = [(pt, v) for pt, v in m.fb.items()
           if 40 <= pt[1] <= 319 and v not in (0, -1)]
    check(not bad,
          f'the whole client area is stock ground again '
          f'({bad[:3]})')


def test_discipline(raw, ref):
    print('discipline: same node free, A to B to A re-decodes, '
          'exit clears, return re-renders')
    m = BGMachine(raw)
    setup(m)
    nodes = scene(m, {0: ('Cover Song', b'MP3', len(PHOTO_MP3), 0),
                      1: ('Bright Song', b'MP3', len(BRIGHT_MP3), 1)})
    m.add_file(7, 0, PHOTO_MP3, name11(b'MP3'), 2)
    m.add_file(7, 1, BRIGHT_MP3, name11(b'MP3'), 2)
    m.w16(BCTX + 0x1EE, 0)
    m.set_event(0x144)
    m.paint()
    check(m.stats['setup'] == 1, 'one decode for A')
    # Extra paints on the same selection: no second decode.
    for t in range(1010, 1060, 10):
        m.set_clock(t)
        m.paint()
    check(m.stats['setup'] == 1 and m.fetches == [(7, 0), (7, 0)],
          'reselecting the same node is free')
    # B: one decode. Back to A: one more (single-entry store).
    m.w16(BCTX + 0x1EE, 1)
    m.set_event(0x144)
    m.set_clock(2000)
    m.paint()
    check(m.stats['setup'] == 2, 'one decode for B')
    m.w16(BCTX + 0x1EE, 0)
    m.set_event(0x144)
    m.set_clock(3000)
    m.paint()
    check(m.stats['setup'] == 3,
          'A decoded again after B (the store holds one entry)')
    # Exit: state and key entry cleared.
    m.call(t1.EXIT)
    check(m.bg_active() == 0, 'exit drops the background flag')
    check(m.key_result() == 0, 'exit clears the key entry')
    check(bytes(m.u.mem_read(STATE, bm.STATE_LEN)) == bytes(52),
          'exit zeroes the payload state')
    # Return: the selecting paint re-renders from the selection.
    setup(m)
    m.set_event(0x144)
    m.set_clock(4000)
    m.paint()
    check(m.bg_active() == 1, 'return re-installs the background')
    check([list(r) for r in m.store_rows()] == expected_store(ref),
          'the store is rebuilt on return')


def test_creep(raw, refs):
    print('creep: a long scripted session leaves the background '
          'exact')
    m = BGMachine(raw)
    setup(m)
    nodes = scene(m, {0: ('Cover Song', b'MP3', len(PHOTO_MP3), 0),
                      1: ('Bright Song', b'MP3', len(BRIGHT_MP3), 1),
                      2: ('Cover Song Two', b'MP3', len(PHOTO_MP3),
                          2)})
    m.add_file(7, 0, PHOTO_MP3, name11(b'MP3'), 2)
    m.add_file(7, 1, BRIGHT_MP3, name11(b'MP3'), 2)
    m.add_file(7, 2, PHOTO_MP3, name11(b'MP3'), 2)
    photo = expected_store(refs['photo'])
    bright = expected_store(refs['bright'])

    def select(i, t):
        m.w16(BCTX + 0x1EE, i)
        m.set_event(0x144)
        m.set_clock(t)
        m.paint()

    def idle(t0, t1_):
        for t in range(t0, t1_, 10):
            m.set_clock(t)
            m.paint()

    select(0, 1000)
    check_bands(m, photo, sel_row=0)
    idle(1010, 1400)                       # dwell + scroll steps
    check_bands(m, photo, sel_row=0)
    select(2, 2000)                        # same album, next track
    check_bands(m, photo, sel_row=2)
    idle(2010, 2600)                       # marquee runs on
    check_bands(m, photo, sel_row=2)
    select(1, 3000)                        # different album: swap
    check_bands(m, bright, sel_row=1)
    # View toggles keep the same file selected: art unchanged.
    from test_browser_marquee_v3 import key_event
    key_event(m, 0x20000010, 4000)
    m.set_event(0x144)
    idle(4010, 4200)
    check_bands(m, bright, sel_row=1)
    key_event(m, 0x20000010, 5000)
    m.set_event(0x144)
    idle(5010, 5200)
    check_bands(m, bright, sel_row=1)
    select(0, 6000)                        # back to the first album
    idle(6010, 7000)
    check_bands(m, photo, sel_row=0)


def test_mode_b(raw, ref):
    print('mode B: the accent site substitutes there too')
    m = BGMachine(raw)
    setup(m)
    scene(m, {0: ('Cover Song', b'MP3', len(PHOTO_MP3), 0)})
    m.add_file(7, 0, PHOTO_MP3, name11(b'MP3'), 2)
    m.w16(BCTX + 0x1EE, 0)
    m.set_event(0x143)
    m.set_clock(1000)
    m.paint()
    check(m.bg_active() == 1, 'mode B selecting paint installs')
    store = [list(r) for r in m.store_rows()]
    check(store == expected_store(ref), 'mode B store matches')


def player_snapshot(m, data):
    h = open_file(m, 7, 0)
    assert h >= 0, 'player open failed'
    callx(m, SEEK, r0=0, r1=0, r2=h)
    m.w32(DESC, 0)
    size = callx(m, SCAN, r0=h, r1=OUTCELL)
    assert size and size < 0x80000000, 'player locate failed'
    mode = m.r32(OUTCELL)
    m.w32(REQ, 144)
    m.w32(REQ + 4, 144)
    m.w32(REQ + 8, 23)
    m.w32(REQ + 0xC, 36)
    callx(m, SET_D4, r0=0)
    callx(m, SET_D8, r0=1)
    sret = callx(m, SETUP, r0=h, r1=mode)
    assert sret == 1, 'player setup failed'
    snap = (bytes(m.u.mem_read(CTX, 0x40)),
            bytes(m.u.mem_read(DESC, 0x10)))
    for _ in range(200):
        if callx(m, CONSUMER) == 0:
            break
    callx(m, FSCLOSE, r0=h)
    return snap


def test_restoration(raw):
    print('restoration: player state byte-identical around a '
          'browser decode')
    m = BGMachine(raw)
    setup(m)
    scene(m, {0: ('Cover Song', b'MP3', len(PHOTO_MP3), 0)})
    m.add_file(7, 0, PHOTO_MP3, name11(b'MP3'), 2)
    before = player_snapshot(m, PHOTO_MP3)
    m.w16(BCTX + 0x1EE, 0)
    m.set_event(0x144)
    m.paint()
    check(m.bg_active() == 1, 'browser decode ran')
    after = player_snapshot(m, PHOTO_MP3)
    check(before == after,
          'artwork context and descriptor restored byte for byte')


def main():
    stock = (REPO / 'DP3_V137.img').read_bytes()
    if hashlib.sha256(stock).hexdigest() != bm.STOCK_SHA:
        raise SystemExit('stock image hash mismatch')
    with tempfile.TemporaryDirectory() as tmp:
        raw = t1.build_variant(tmp)
    print(f'variant sha256: {hashlib.sha256(raw).hexdigest()}')
    print(f'variant length: {len(raw)} (stock {len(stock)}, '
          f'delta {len(raw) - len(stock)})')
    refs = {'photo': direct_rows(raw, PHOTO_MP3),
            'bright': direct_rows(raw, BRIGHT_MP3),
            'dark': direct_rows(raw, DARK_MP3)}
    for k, rows in refs.items():
        print(f'reference {k}: produced {len(rows[0])}x{len(rows)}')
    test_install(raw, refs['photo'])
    test_darkening_and_contrast(raw, refs)
    test_fallback(raw)
    test_discipline(raw, refs['photo'])
    test_creep(raw, refs)
    test_mode_b(raw, refs['photo'])
    test_restoration(raw)
    print('ALL MARQUEE V5 BACKGROUND GATES PASS')


if __name__ == '__main__':
    main()

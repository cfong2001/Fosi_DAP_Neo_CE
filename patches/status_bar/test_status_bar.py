#!/usr/bin/env python3
"""The player's status bar on theater and default grounds.

Runs real firmware code (module 0, 18 and 27, the real fill, DrawImageAt,
keyed helper and sprite string routine, real pixel stores) through the
machine in patches/design_refresh_v4/test_keyed_transport.py, on the
standard image (default patches/full/out/DP3_V137_CE_full.img, or the
path given as the first argument) and on stock.

Bluetooth icon (resident status routine 0x03063642), each gate on a
framebuffer pre-filled with the ground:
  g1  music window, theater ground, dark and light themes: Bluetooth off
      leaves the 18 by 18 icon rectangle all ground; on, every pixel is
      the glyph's ink or the ground.
  g2  music window, on then off: no glyph ink remains.
  g3  music window, ground cell at the theme default: the rectangle
      equals stock's opaque draw pixel for pixel, in both themes.
  g4  other windows (window byte not 3, or flag 0x1A8 set) are drawn
      exactly as stock: the black-surround resources, opaque.
  g5  no store carries the key colour 0xF800.
  control: stock leaves the 18 by 18 box on a theater ground.

Track counter (module 27 call at 0x0307E458 to the counter wrapper):
  c0  the call site branches to the wrapper.
  c1  theater ground, both themes, with stale ink across the field: the
      field (90, 8)..(170, 19) ends as the ground plus the digits' ink;
      no blank cell is drawn.
  c2  dark theme on the default ground: equals stock pixel for pixel.
      Light theme: differs from stock only inside stock's dark grey blank
      cells, which become the ground.
  control: stock draws the 9 by 12 blank cell on a theater ground.

Volume speaker (resource 133, light 299, at (10, 7) through the volume
wrapper):
  v0  the player's call (module 27, 0x0307F024) reaches the keyed helper
      (it follows the player's full-screen ground fill); the shared status
      routine's call (module 0, 0x03063ACC) reaches the wrapper.
  v1  music window, theater ground, both themes: the 8 by 14 rectangle is
      the ground plus the speaker's ink; no store carries the key colour.
  v2  other windows: equals stock's opaque draw pixel for pixel.
  v3  music window, default ground: differs from stock only in the
      speaker's surround pixels, which become the ground.
  control: stock leaves the black (light: white) surround on a theater
      ground.
"""
import importlib.util
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location(
    'kt', ROOT / 'patches' / 'design_refresh_v4' / 'test_keyed_transport.py')
kt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kt)

IMAGE = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    ROOT / 'patches' / 'full' / 'out' / 'DP3_V137_CE_full.img'
STOCK = (ROOT / 'DP3_V137.img').read_bytes()
STATUS = 0x03063642          # resident status routine (Bluetooth icon)
STRINGS = 0x030639A8         # sprite string routine (stock counter draw)
COUNTER = 0x03062EB8         # counter wrapper (0281)
COUNTER_SITE = 0x0307E458    # module 27 counter call (0282)
FIELD = (90, 8, 81, 12)      # x, y, width, height of the counter field
VOLUME = VOLUME_WRAPPER = 0x0306944E   # volume speaker wrapper (0283)
VOLUME_SITES = ((27, 0x0307F024, 0x03063A08), (0, 0x03063ACC, VOLUME_WRAPPER))
SPEAKER = {0: 133, 1: 299}   # resolved id per theme (the call passes 133)
TEXT = 0x030E0000            # scratch for the counter string
CALL_SP = 0x030F0000 - 0x100  # Machine.call's stack pointer
WINDOW = 0x030057E0          # current window index byte (3: music)
STATE = 0x03004154           # last drawn Bluetooth state
X, Y, SIZE = 176, 5, 18
IDS = (282, 283, 284, 285, 448, 449, 450, 451)
THEATER = {0: 0x8C60, 1: 0xBDD3}     # olive dark ground, warm light ground
DEFAULT = {0: 0x10A2, 1: 0xFFFF}     # stock player grounds


def run(raw, *, theme, ground, window=3, flag_1a8=False, sequence=(True,)):
    """Draw the icon for each Bluetooth state in `sequence` (True = on)."""
    m = kt.Machine(raw, real_store=True)
    m.stage(IDS)
    kt.fb_fill(m, ground)
    u = m.u
    u.mem_write(kt.GROUND_CELL, struct.pack('<H', ground))
    u.mem_write(kt.SAVEINFO + 0x2D8, bytes([theme]))
    u.mem_write(WINDOW, bytes([window]))
    if flag_1a8:
        m.set_event(0x1A8)
    stores = []
    for on in sequence:
        # +0x2D4 enables Bluetooth; +0x2D3 selects state 2 (drawn as "on").
        u.mem_write(kt.SAVEINFO + 0x2D3, bytes([1 if on else 0]))
        u.mem_write(kt.SAVEINFO + 0x2D4, bytes([1 if on else 0]))
        u.mem_write(STATE, bytes([0xFF]))          # force a redraw
        m.stores.clear()
        m.call(STATUS, 0)
        stores += m.stores
    return kt.fb_read(m, X, Y, SIZE, SIZE), stores


def run_counter(raw, fn, *, theme, ground, text, stale=False):
    """Draw `text` the way the player's counter call does (base id 249,
    step 9, x 0x5A, y 8 on the stack) through `fn`."""
    m = kt.Machine(raw, real_store=True)
    m.stage(list(range(249, 261)) + list(range(415, 427)))
    kt.fb_fill(m, ground)
    u = m.u
    if stale:   # ink from an earlier, longer counter across the whole field
        x, y, w, h = FIELD
        for row in range(y + 2, y + h - 2):
            u.mem_write(kt.fb_addr(m, x, row), struct.pack('<H', 0xFFFF) * w)
    u.mem_write(kt.GROUND_CELL, struct.pack('<H', ground))
    u.mem_write(kt.SAVEINFO + 0x2D8, bytes([theme]))
    u.mem_write(TEXT, text.encode('utf-16-le') + b'\0\0')
    u.mem_write(CALL_SP, struct.pack('<I', 8))       # y, the stack argument
    u.reg_write(kt.UC_ARM_REG_R3, 0x5A)
    m.stores.clear()
    m.call(fn, 249, TEXT, 9)
    return kt.fb_read(m, *FIELD), m.stores


def counter_want(raw, theme, ground, text):
    """The ground plus each digit's non-key pixels; blank cells add nothing."""
    x0, y0, w, h = FIELD
    want = {(x, y): ground for y in range(y0, y0 + h) for x in range(x0, x0 + w)}
    for k, ch in enumerate(text):
        if ch == ':':
            break
        rid = ord(ch) - 0x30 + 249 + (166 if theme else 0)
        cw, ch_h, words = kt.res_words(raw, rid)
        for i, v in enumerate(words):
            p = (0x5A + 9 * k + i % cw, 8 + i // cw)
            if v != kt.KEY and p in want:
                want[p] = v
    return want


def run_speaker(raw, fn, *, theme, ground, window=3):
    """Draw the speaker (id 133 at (10, 7)) through `fn`."""
    m = kt.Machine(raw, real_store=True)
    m.stage([133, 299])
    kt.fb_fill(m, ground)
    u = m.u
    u.mem_write(kt.GROUND_CELL, struct.pack('<H', ground))
    u.mem_write(kt.SAVEINFO + 0x2D8, bytes([theme]))
    u.mem_write(WINDOW, bytes([window]))
    m.stores.clear()
    m.call(fn, 133, 10, 7)
    return kt.fb_read(m, 10, 7, 8, 14), m.stores


def resource(raw, rid):
    w, h, words = kt.res_words(raw, rid)
    assert (w, h) == (SIZE, SIZE)
    return words


def check(name, ok, detail=''):
    print(f"{'PASS' if ok else 'FAIL'}  {name}{(' - ' + detail) if detail else ''}")
    if not ok:
        raise SystemExit(1)


def main():
    raw = IMAGE.read_bytes()
    print(f'image: {IMAGE}')
    key_stores = 0
    for theme in (0, 1):
        g = THEATER[theme]
        off_id, on_id = (284, 285) if theme == 0 else (450, 451)

        fb, st = run(raw, theme=theme, ground=g, sequence=(False,))
        key_stores += sum(1 for *_, v in st if v == kt.KEY)
        check(f'g1 theme {theme}: Bluetooth off leaves only ground',
              set(fb.values()) == {g}, f'{len(set(fb.values()))} colours')

        fb, st = run(raw, theme=theme, ground=g, sequence=(True,))
        key_stores += sum(1 for *_, v in st if v == kt.KEY)
        glyph = resource(raw, on_id)
        want = {(X + i % SIZE, Y + i // SIZE): (g if v == kt.KEY else v)
                for i, v in enumerate(glyph)}
        ink = sum(1 for v in glyph if v != kt.KEY)
        check(f'g1 theme {theme}: Bluetooth on is glyph ink over ground',
              fb == want and 0 < ink < SIZE * SIZE, f'{ink} ink pixels')

        fb, st = run(raw, theme=theme, ground=g, sequence=(True, False))
        key_stores += sum(1 for *_, v in st if v == kt.KEY)
        check(f'g2 theme {theme}: on then off leaves no ink',
              set(fb.values()) == {g})

        for on in (False, True):
            d = DEFAULT[theme]
            new, _ = run(raw, theme=theme, ground=d, sequence=(on,))
            old, _ = run(STOCK, theme=theme, ground=d, sequence=(on,))
            check(f'g3 theme {theme} {"on" if on else "off"}: default ground equals stock',
                  new == old)

        for window, flag in ((0, False), (3, True)):
            for on in (False, True):
                new, _ = run(raw, theme=theme, ground=g, window=window,
                             flag_1a8=flag, sequence=(on,))
                old, _ = run(STOCK, theme=theme, ground=g, window=window,
                             flag_1a8=flag, sequence=(on,))
                check(f'g4 theme {theme} window {window} flag 0x1A8 {flag} '
                      f'{"on" if on else "off"}: drawn as stock', new == old)

        # Control: stock leaves the opaque surround on a theater ground.
        fb, _ = run(STOCK, theme=theme, ground=g, sequence=(False,))
        check(f'control theme {theme}: stock shows a {SIZE}x{SIZE} box',
              set(fb.values()) == {DEFAULT[theme]})
    check('g5 no store carries the key colour', key_stores == 0)

    image = kt.Image(raw)
    offset, _ = image.module_region(27, 'code')
    base = image.modules[27]['code_exec']
    insn = next(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(
        raw[offset + COUNTER_SITE - base:offset + COUNTER_SITE - base + 4], COUNTER_SITE))
    check('c0 the player counter call reaches the wrapper',
          (insn.mnemonic, insn.op_str) == ('bl', f'#{COUNTER:#x}'))

    for theme in (0, 1):
        g = THEATER[theme]
        for text in ('167;205:', '9;1200', '1;9:::'):
            fb, st = run_counter(raw, COUNTER, theme=theme, ground=g, text=text, stale=True)
            check(f'c1 theme {theme} "{text}": stale ink erased, ground plus digits',
                  fb == counter_want(raw, theme, g, text)
                  and not any(v == kt.KEY for *_, v in st))
        d = DEFAULT[theme]
        new, _ = run_counter(raw, COUNTER, theme=theme, ground=d, text='167;205:')
        old, _ = run_counter(STOCK, STRINGS, theme=theme, ground=d, text='167;205:')
        if theme == 0:
            check('c2 theme 0: default ground equals stock', new == old)
        else:
            blank = {(x, y) for x in range(0x5A + 63, 0x5A + 72) for y in range(8, 20)}
            diff = {p for p in new if new[p] != old[p]}
            check('c2 theme 1: differs from stock only in the blank cell',
                  diff == blank and {old[p] for p in blank} == {0x2945}
                  and {new[p] for p in blank} == {d})
        fb, _ = run_counter(STOCK, STRINGS, theme=theme, ground=g, text='167;205:')
        cell = {fb[(x, y)] for x in range(0x5A + 63, 0x5A + 72) for y in range(8, 20)}
        check(f'control theme {theme}: stock draws the blank cell',
              cell == {0x10A2 if theme == 0 else 0x2945})
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    for module, site, target in VOLUME_SITES:
        offset, _ = image.module_region(module, 'code')
        base = image.modules[module]['code_exec']
        insn = next(md.disasm(raw[offset + site - base:offset + site - base + 4], site))
        check(f'v0 module {module} speaker call at {site:#x} reaches {target:#x}',
              (insn.mnemonic, insn.op_str) == ('bl', f'#{target:#x}'))
    for theme in (0, 1):
        g = THEATER[theme]
        words = kt.res_words(raw, SPEAKER[theme])[2]
        want = {(10 + i % 8, 7 + i // 8): (g if v == kt.KEY else v) for i, v in enumerate(words)}
        fb, st = run_speaker(raw, VOLUME, theme=theme, ground=g)
        check(f'v1 theme {theme}: speaker ink over the theater ground',
              fb == want and not any(v == kt.KEY for *_, v in st)
              and sum(1 for v in words if v == kt.KEY) > 0)
        for window in (0, 1, 5):
            new, _ = run_speaker(raw, VOLUME, theme=theme, ground=g, window=window)
            old, _ = run_speaker(STOCK, kt.DRAWAT, theme=theme, ground=g, window=window)
            check(f'v2 theme {theme} window {window}: drawn as stock', new == old)
        d = DEFAULT[theme]
        new, _ = run_speaker(raw, VOLUME, theme=theme, ground=d)
        old, _ = run_speaker(STOCK, kt.DRAWAT, theme=theme, ground=d)
        surround = {(10 + i % 8, 7 + i // 8) for i, v in enumerate(words) if v == kt.KEY}
        diff = {p for p in new if new[p] != old[p]}
        check(f'v3 theme {theme}: default ground differs from stock only in the surround',
              diff <= surround and all(new[p] == d for p in surround))
        fb, _ = run_speaker(STOCK, kt.DRAWAT, theme=theme, ground=g)
        check(f'control theme {theme}: stock keeps the speaker surround',
              {fb[p] for p in surround} == {0x0000 if theme == 0 else 0xFFFF})
    print('ALL GATES PASSED')


if __name__ == '__main__':
    main()

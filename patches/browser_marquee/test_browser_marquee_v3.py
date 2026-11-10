#!/usr/bin/env python3
"""Emulation gates for the browser marquee v3 changes.

Change 1 (uncapped tag string): a fixture whose artist, title and
album all exceed the v2 caps (24/24/13) scrolls the full fields.
The expectation is composed from the dispatcher struct bytes in
payload memory after the parse, applying the documented field
rules in Python, so the gate compares against the struct contents
rather than any truncation.

Change 2 (long-press view toggle): the toggle stub at the Key
handler site where r4 holds the final event word flips the view
mode only for the long-press Vol+ event (0x20000010); an
integration run drives the real Key callback (mq_key hook, the
stock event fetch FUN_03061B16 and the stock dispatch) with that
event in the key state cell and shows the mode flipped with no
stock action taken; paint-level runs then show the tag view and
the file view alternating on the same file, with no re-read in
either direction (the file view never parses; the return to the
tag view is served by the cache), the dwell and scroll offset
reset by the toggle, and the mode reset by the exit hook.

The cover thumbnail is not part of v3: design.md records the
feasibility verdict and its evidence.
"""
import hashlib
import struct
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'tools'))
sys.path.insert(0, str(REPO / 'patches' / 'framework'))
sys.path.insert(0, str(HERE))

import build_marquee as bm                                   # noqa: E402
import test_browser_marquee as t1                            # noqa: E402
import test_browser_marquee_tags as t2                       # noqa: E402
from test_browser_marquee_tags import (Machine, check,        # noqa: E402
                                       make_node2, name11, scene,
                                       setup, run_dwell)

PAINT = t1.PAINT
KEY = t1.KEY
EXIT = t1.EXIT
BCTX = bm.BCTX
LCTX = bm.LCTX
SENTINEL = t1.SENTINEL

# Payload layout, recomputed exactly as build_marquee.main does.
_probe, _pe = bm.assemble(bm.BASE + 0x1000, bm.BASE + 0x1020)
_code_len = (len(_probe) + 3) & ~3
STATE = bm.BASE + _code_len
BUF = STATE + bm.STATE_LEN
EXTTAB = BUF + bm.BUF_UNITS * 2
TSTRUCT = (EXTTAB + len(bm.TAG_EXTS) * 3 + 3) & ~3
KEYTAB = (TSTRUCT + bm.STRUCT_SPAN + 3) & ~3  # v5: the window
# key table sits between the struct span and the tag cache
CACHE = KEYTAB + bm.KEY_ENTRIES * bm.KEY_LEN
ENT = bm.assemble(STATE, BUF, _pe,
                  {'struct': TSTRUCT, 'cache': CACHE,
                   'exttab': EXTTAB, 'keytab': KEYTAB})[1]
TOGGLE = ENT['toggle']
MODE = STATE + 0x18
KEY_EVENT_CELL = 0x030230D0        # key state struct +0x34
KEY_FLAG_BYTE = 0x030230EC         # sequencer flag byte (bit 0 path)
SAVEINFO_VOL = 0x030232A0 + 0x12

# Worst case on purpose: all three fields at the struct's 127-unit
# bound, so the composed string is 127 + 3 + 127 + 3 + 127 = 387
# units and the entry buffer holds exactly 388 with the terminator.
# Frame order matters: the stock ID3 parser terminates each field
# in place, and a full title's terminator lands on artist unit 0
# (struct +0x60 + 2*127 = +0x15E), so the artist frame is placed
# after the title frame and its own write wins the shared byte;
# the same applies to artist -> album at +0x25C.
LONG_MP3 = t2.mp3([(b'TIT2', t2.tf('T' * 127)),
                   (b'TPE1', t2.tf('A' * 127)),
                   (b'TALB', t2.tf('L' * 127))])


def entry_buf(node):
    idx = (node >> 4) & (bm.CACHE_ENTRIES - 1)
    return CACHE + idx * bm.CACHE_ENTRY_LEN + 0x14


def struct_fields(m):
    """The four text fields of the dispatcher struct in memory."""
    out = {}
    for name, off in (('title', 0x060), ('artist', 0x15E),
                      ('album', 0x25C), ('album_artist', 0x458)):
        units = []
        for i in range(127):
            ch = m.r16(TSTRUCT + off + 2 * i)
            if ch == 0:
                break
            units.append(ch)
        out[name] = units
    return out


def trim(units):
    while units and units[0] <= 0x20:
        units = units[1:]
    while units and units[-1] <= 0x20:
        units = units[:-1]
    return units


def expected_tag_string(m):
    """The field rules applied to the struct contents, with the
    v5 composition order: title first, then the artist (with the
    album-artist fallback), then the album. Fields are read in
    full; the joined string is bounded by the entry buffer.
    (v2 to v4 led with the artist.) This suite's fixture has a
    title, so the name-lead case does not arise here."""
    f = struct_fields(m)
    title = trim(f['title'])
    artist = trim(f['artist']) or trim(f['album_artist'])
    parts = []
    if title:
        parts.append(title)
        if artist:
            parts.append(artist)
        album = trim(f['album'])
        if album:
            parts.append(album)
    elif artist:
        raise AssertionError('name-lead case not modelled here')
    s = []
    for i, p in enumerate(parts):
        if i:
            s += [0x20, 0x2D, 0x20]
        s += p
    return ''.join(chr(c) for c in s)


def key_event(m, event, t):
    """Deliver one key event through the real Key callback: the
    event word sits in the key state cell, the sequencer flag byte
    takes the direct path in FUN_03061B16, and the stock handler
    runs to completion (its dispatch for the toggle event is the
    default exit)."""
    m.w32(KEY_EVENT_CELL, event)
    m.w8(KEY_FLAG_BYTE, 1)
    m.set_clock(t)
    m.call(KEY)


def test_uncapped(m):
    print('uncapped: long fields scroll in full, from the struct')
    setup(m)
    a = scene(m, {0: ('Long Song', b'MP3', len(LONG_MP3), 0)})[0]
    m.add_file(7, 0, LONG_MP3, name11(b'MP3'), 2)
    m.w16(BCTX + 0x1EE, 0)
    sp = run_dwell(m)
    check(sp == entry_buf(a), 'the cache entry buffer is registered')
    want = expected_tag_string(m)
    check(len(want) == 127 + 3 + 127 + 3 + 127,
          f'struct-derived expectation is the full 387 units '
          f'({len(want)})')
    # v5: the fields are still read in full (the expectation
    # above), but the joined label is bounded by the entry
    # buffer: TAG_BUF_UNITS - 1 = 263 units, enforced in
    # field_put. The v3-era buffer held the whole 387.
    want = want[:bm.TAG_BUF_UNITS - 1]
    got = m.read_str(entry_buf(a), 400)
    check(got == want, 'registered string equals the struct contents '
                       'with the field rules applied, bounded by '
                       'the entry buffer')
    check(m.r16(entry_buf(a) + (bm.TAG_BUF_UNITS - 1) * 2) == 0,
          'the bounded worst case stays inside the entry buffer')
    offs = []
    for t in range(1110, 1110 + 10 * 340, 10):
        m.set_clock(t)
        m.paint()
        offs.append(m.mq_offset())
    check(max(offs) >= 100,
          f'scroll offset passes any capped length ({max(offs)})')


def test_toggle_stub(m):
    print('toggle stub: only the long Vol+ event flips the mode')
    setup(m)
    scene(m, {0: ('Some Song', b'MP3', 1000, 0)})
    from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                   UC_ARM_REG_R2, UC_ARM_REG_R3,
                                   UC_ARM_REG_R4, UC_ARM_REG_SB)
    u = m.u

    def call_stub(event):
        from unicorn.arm_const import (UC_ARM_REG_SP, UC_ARM_REG_LR,
                                       UC_ARM_REG_PC)
        m.w32(STATE, t1.NODE_POOL)       # state.node = a node
        for reg, val in ((UC_ARM_REG_R0, 0x11111111),
                         (UC_ARM_REG_R1, 0x22222222),
                         (UC_ARM_REG_R2, 0x03023D38),
                         (UC_ARM_REG_R3, 0x44444444),
                         (UC_ARM_REG_R4, event),
                         (UC_ARM_REG_SB, 0xDEADBEEF),
                         (UC_ARM_REG_SP, t1.STACK_TOP),
                         (UC_ARM_REG_LR, SENTINEL)):
            u.reg_write(reg, val)
        u.emu_start(TOGGLE | 1, SENTINEL, count=100000)
        assert u.reg_read(UC_ARM_REG_PC) == SENTINEL
        return (u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1),
                u.reg_read(UC_ARM_REG_R2), u.reg_read(UC_ARM_REG_R3),
                u.reg_read(UC_ARM_REG_R4), u.reg_read(UC_ARM_REG_SB))

    m.w8(MODE, 0)
    r = call_stub(0x20000010)
    check(m.r8(MODE) == 1, 'long Vol+ flips tag view to file view')
    check(m.r32(STATE) == 0, 'toggle clears state.node (re-resolve)')
    check(r[:5] == (0x11111111, 0x22222222, 0x03023D38, 0x44444444,
                    0x20000010),
          f'r0-r4 preserved across the stub ({r[:5]})')
    check(r[5] == LCTX, 'displaced instruction performed (sb = LCTX)')
    r = call_stub(0x20000010)
    check(m.r8(MODE) == 0, 'second long Vol+ flips back to tag view')
    for ev, label in ((0x10000010, 'short Vol+ press'),
                      (0x30000010, 'Vol+ repeat'),
                      (0x40000010, 'Vol+ release'),
                      (0x50000010, 'Vol+ long release'),
                      (0x20000020, 'long Vol-'),
                      (0x20000001, 'long Power'),
                      (0x20004000, 'long OK (stock action)'),
                      (0x40004000, 'OK release (open)')):
        m.w8(MODE, 0)
        m.w32(STATE, t1.NODE_POOL)
        call_stub(ev)
        check(m.r8(MODE) == 0 and m.r32(STATE) == t1.NODE_POOL,
              f'{label} does not toggle ({ev:#x})')


def test_toggle_views(m):
    print('toggle: views alternate on one file, cache serves both '
          'ways, dwell and offset reset, exit resets the mode')
    setup(m)
    # The name is long enough that the file view string is also
    # over-wide and registers; with a short name both views would
    # fit and nothing would scroll in the file view at all.
    scene(m, {0: ('A Rather Long Fixture Song Name', b'MP3',
                  len(t2.TAGGED_MP3), 0)})
    m.add_file(7, 0, t2.TAGGED_MP3, name11(b'MP3'), 2)
    m.w16(BCTX + 0x1EE, 0)
    vol0 = m.r8(SAVEINFO_VOL)
    # Tag view (default): parse on the selecting paint, tags
    # scroll. The selecting paint also probes the selected
    # file once for the background.
    sp = run_dwell(m)
    win = [(7, 0), (7, 0)]
    check(m.fetches == win,
          f'parsed once, probed once ({m.fetches})')
    check(m.read_str(sp) ==
          'Fixture Title - Fixture Artist - Fixture Album',
          'tag view scrolls the tags')
    # Advance the scroll so the reset is observable.
    for t in range(1110, 1250, 10):
        m.set_clock(t)
        m.paint()
    check(m.mq_phase() == 1 and m.mq_offset() >= 3,
          f'scrolling before the toggle (phase {m.mq_phase()}, '
          f'offset {m.mq_offset()})')
    # Long Vol+ through the real Key callback.
    key_event(m, 0x20000010, 2000)
    check(m.r8(MODE) == 1, 'mode is file view after the long press')
    check(m.r8(SAVEINFO_VOL) == vol0,
          'no stock action fired (volume byte unchanged)')
    check(m.mq_phase() == 0, 'dwell phase reset by the toggle key')
    # File view: the v1 string, composed from the node, no re-read.
    sp = run_dwell(m, 3000)
    check(m.fetches == win,
          f'no re-read in tag-to-file ({m.fetches})')
    got = m.read_str(sp)
    check(got.startswith('A Rather Long Fixture Song Name - MP3 - '),
          f'file view scrolls the dirent string ({got!r})')
    # Back to tag view: the cache serves it, still no re-read.
    key_event(m, 0x20000010, 5000)
    check(m.r8(MODE) == 0, 'mode is tag view after the second press')
    sp = run_dwell(m, 6000)
    check(m.fetches == win,
          f'no re-read in file-to-tag ({m.fetches})')
    check(m.read_str(sp) ==
          'Fixture Title - Fixture Artist - Fixture Album',
          'tag view restored from the cache')
    # A short press does not toggle.
    key_event(m, 0x10000010, 8000)
    check(m.r8(MODE) == 0, 'short Vol+ press does not toggle')
    # The exit hook resets the mode (and the cache, as in v2).
    key_event(m, 0x20000010, 9000)
    check(m.r8(MODE) == 1, 'file view again before exit')
    m.call(EXIT)
    check(m.r8(MODE) == 0, 'mode resets to tag view on window exit')


def main():
    stock = (REPO / 'DP3_V137.img').read_bytes()
    if hashlib.sha256(stock).hexdigest() != bm.STOCK_SHA:
        raise SystemExit('stock image hash mismatch')
    with tempfile.TemporaryDirectory() as tmp:
        raw = t1.build_variant(tmp)
    print(f'variant sha256: {hashlib.sha256(raw).hexdigest()}')
    print(f'variant length: {len(raw)} (stock {len(stock)}, '
          f'delta {len(raw) - len(stock)})')
    test_uncapped(Machine(raw))
    test_toggle_stub(Machine(raw))
    test_toggle_views(Machine(raw))
    print('ALL MARQUEE V3 GATES PASS')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Emulation gates for browser wheel acceleration.

Drives the real module 31 Key callback (0x0307E5B8) and the real
browser painter (Display entry 0x0307ED40) from the Standard image,
with module 0 resident, under Unicorn. Two machines run side by side:
STOCK has the two hook sites restored to their stock BL bytes, ACCEL
has patches 0330 to 0333. Leaves modelled at the painter boundary, as
in the browser marquee suite: the key fetch (0x03061B16) returns the
wheel event word, the directory loader (0x0307D254) writes names for
the requested top row into the visible node chain, the framebuffer row
shift (0x030646A0) and the rect fill and text renderer are recorded.
Event flags, the OS clock cell, the selection arithmetic, the stock
step functions and the painter run as firmware code.

Gates:
  1. slow steps (and steps exactly FAST_TICKS apart) produce the same
     calls, state and paint as stock, one row per step, both ways;
  2. a same-direction burst moves by the ROWS table, four steps per
     level, and a pause or a reversal returns to one row;
  3. every accelerated step loads the stock window for the target and
     paints the same rows as a stock full-list paint of that state;
  4. bursts clamp at both list ends exactly where stock stops, and
     steps at an end are byte-identical to stock (no wrap in either);
  5. lists of 0 to 9 entries stay in range under bursts;
  6. the patch bytes are embedded in release/DP3_V137_CE.img.
"""
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(HERE)]
from rknano_image import Image  # noqa: E402
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE  # noqa: E402
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,  # noqa: E402
                               UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR,
                               UC_ARM_REG_PC)
import build_wheel_accel as wa  # noqa: E402

KEY, PAINT = 0x0307E5B8, 0x0307ED40
KEYFETCH, DIRLOAD, SHIFT = 0x03061B16, 0x0307D254, 0x030646A0
FILL, MEASURE, CHARWIDTH, RENDER = 0x030632FA, 0x0306295A, 0x030627BE, 0x03062CEE
ERASE, DRAWAT, KEYED, BITMAP = 0x03063C74, 0x0306354A, 0x03063A08, 0x0306333E
CTX, LCTX, CLOCK, EVENTS = wa.CTX, 0x03025928, wa.CLOCK, 0x03023CF8
DOWN, UP = 0x40000200, 0x40000400
ACCENT = 0xF220     # selection band colour cell 0x030235B8
NODE_POOL, NODE_SIZE, AUX = 0x030A0000, 0x270, 0x030A2000
STACK_TOP, SENTINEL = 0x03100000, 0x03110000
STOCK_BL = {wa.DOWN_SITE: bytes.fromhex('fff7cefe'), wa.UP_SITE: bytes.fromhex('fff75efe')}


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)
    print('  ok:', msg)


class Machine:
    def __init__(self, raw, accel):
        self.im = Image(raw)
        self.u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.u.mem_map(0x03000000, 0x200000)
        for idx in (0, 31):
            m = self.im.modules[idx]
            for kind in ('code', 'data'):
                off, size = self.im.module_region(idx, kind)
                if size:
                    self.u.mem_write(m[kind + '_exec'], raw[off:off + size])
        if accel:
            for _, _, _, address, code in wa.patches():
                self.u.mem_write(address, code)
        else:
            for address, code in STOCK_BL.items():
                self.u.mem_write(address, code)
        self.log = []
        self.event_word = 0
        for leaf in (KEYFETCH, DIRLOAD, SHIFT, FILL, RENDER, MEASURE, CHARWIDTH,
                     ERASE, DRAWAT, KEYED, BITMAP):
            self.u.hook_add(UC_HOOK_CODE, self._hook, begin=leaf, end=leaf)

    def w(self, a, v, n):
        self.u.mem_write(a, v.to_bytes(n, 'little'))

    def r(self, a, n):
        return int.from_bytes(self.u.mem_read(a, n), 'little')

    def _ret(self, uc, r0=None):
        if r0 is not None:
            uc.reg_write(UC_ARM_REG_R0, r0)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def _str(self, a):
        out = []
        while len(out) < 90:
            try:
                ch = self.r(a + 2 * len(out), 2)
            except Exception:
                return f'<unmapped {a:#x}>'
            if not ch:
                break
            out.append(chr(ch))
        return ''.join(out)

    def _hook(self, uc, addr, size, user):
        regs = [uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)]
        sp = uc.reg_read(UC_ARM_REG_SP)
        if addr == KEYFETCH:
            self._ret(uc, self.event_word)
        elif addr == DIRLOAD:
            top = regs[3]
            self.log.append(('load', top))
            node = regs[1]
            for k in range(7):
                if not node:
                    break
                self._name(node, top + k)
                node = self.r(node + 4, 4)
            self._ret(uc, 0)
        elif addr == SHIFT:
            self.log.append(('shift', regs[1]))
            self._ret(uc)
        elif addr == FILL:
            self.log.append(('fill', tuple(regs), self.r(sp, 4) & 0xFFFF))
            self._ret(uc)
        elif addr == RENDER:
            rect = struct.unpack('<4H', uc.mem_read(regs[0], 8))
            self.log.append(('text', rect, self._str(regs[2])))
            self._ret(uc)
        elif addr == MEASURE:
            self._ret(uc, 6 * len(self._str(regs[0])))
        elif addr == CHARWIDTH:
            self._ret(uc, 6)
        elif addr in (ERASE, DRAWAT, KEYED, BITMAP):
            self.log.append(('draw', addr, regs[0], regs[1]))
            self._ret(uc, 0)

    def _name(self, node, index):
        name = f'Track {index:03d}'
        for i, ch in enumerate(name):
            self.w(node + 0x70 + 2 * i, ord(ch), 2)
        self.w(node + 0x70 + 2 * len(name), 0, 2)

    def call(self, addr, r0=0):
        self.u.reg_write(UC_ARM_REG_SP, STACK_TOP)
        self.u.reg_write(UC_ARM_REG_R0, r0)
        self.u.reg_write(UC_ARM_REG_LR, SENTINEL | 1)
        self.u.emu_start(addr | 1, SENTINEL, count=3_000_000)
        if self.u.reg_read(UC_ARM_REG_PC) != SENTINEL:
            raise AssertionError(f'call {addr:#x} did not return')

    def event(self, n):
        return bool(self.r(EVENTS + n // 32 * 4, 4) >> (n % 32) & 1)

    def clear_events(self):
        self.u.mem_write(EVENTS, bytes(64))

    def fixture(self, count, sel=0, top=0, clock=1000):
        self.clear_events()
        for i in range(7):
            a = NODE_POOL + i * NODE_SIZE
            self.u.mem_write(a, bytes(NODE_SIZE))
            self.w(a + 4, a + NODE_SIZE if i < 6 else 0, 4)
            self.u.mem_write(a + 0x4F, b'        MP3')
            self.w(a + 0x5A, 0x20, 1)
        self.w(CTX, NODE_POOL, 4)
        self.w(CTX + 0x1CC, 0, 2)
        self.w(CTX + 0x0C, count, 2)
        self.w(CTX + 0x1CE, top, 2)
        self.w(CTX + 0x1EE, sel, 2)
        self.w(CTX + 0x1F0, sel, 2)
        self.w(CTX + 0x1F4, AUX, 4)
        self.w(LCTX + 8, 0, 2)
        self.w(CLOCK, clock, 4)
        for cell, colour in ((0x030235B4, 0x0000), (0x030235B6, 0xFFFF),
                             (0x030235B8, ACCENT), (0x030235BA, 0x1082)):
            self.w(cell, colour, 2)
        self.u.mem_write(wa.assemble()[2]['state'], bytes(8))
        node = NODE_POOL
        for k in range(7):
            self._name(node, top + k)
            node += NODE_SIZE

    def state(self):
        return self.r(CTX + 0x1EE, 2), self.r(CTX + 0x1CE, 2)

    def step(self, word, dt):
        """One wheel event dt ticks after the last, then one paint."""
        self.w(CLOCK, self.r(CLOCK, 4) + dt, 4)
        self.clear_events()
        self.log = []
        self.event_word = word
        self.call(KEY)
        key_log = self.log
        flags = (self.event(0x144), self.event(0x143))
        self.log = []
        self.call(PAINT)
        return key_log, flags, self.log


def screen(paint_log):
    """Last fill colour and text per list row (y of each 40 px row)."""
    rows = {}
    for entry in paint_log:
        if entry[0] == 'fill':
            (x0, y0, x1, y1), colour = entry[1], entry[2]
            for k in range(7):
                if y0 <= 40 + 40 * k + 20 <= y1:
                    rows.setdefault(k, {})['fill'] = colour
        elif entry[0] == 'text':
            y = entry[1][1]
            k = (y - 40) // 40
            if 0 <= k < 7:
                rows.setdefault(k, {})['text'] = entry[2]
    return rows


def reference_paint(m, sel, top):
    """Stock full-list paint of state (sel, top), no key involved."""
    old = m.state()
    m.w(CTX + 0x1EE, sel, 2)
    m.w(CTX + 0x1CE, top, 2)
    m.clear_events()
    m.log = []
    m.u.mem_write(CTX + 0x1F0, sel.to_bytes(2, 'little'))
    flag = 0x143
    a = EVENTS + flag // 32 * 4
    m.w(a, m.r(a, 4) | 1 << (flag % 32), 4)
    m.call(PAINT)
    got = screen(m.log)
    m.w(CTX + 0x1EE, old[0], 2)
    m.w(CTX + 0x1CE, old[1], 2)
    return got


def model(count, sel, top, dts_dirs):
    """Expected (sel, top, rows) after each step; mirrors the documented rule."""
    streak, last_dir, out = 0, None, []
    elapsed = None
    for dt, d in dts_dirs:
        fast = elapsed is not None and dt < wa.FAST_TICKS and d == last_dir
        streak = min(streak + 1, wa.STREAK_CAP) if fast else 0
        last_dir, elapsed = d, dt
        rows = wa.ROWS[streak // wa.STEPS_PER_LEVEL]
        if count:
            sel = max(0, min(count - 1, sel + rows * d))
        if sel > top + 6:
            top = sel - 6
        if sel < top:
            top = sel
        out.append((sel, top, rows))
    return out


def run_pair(stock, accel, count, sel, top, steps):
    stock.fixture(count, sel, top)
    accel.fixture(count, sel, top)
    return [(stock.step(w, dt), accel.step(w, dt)) for w, dt in steps]


def main():
    raw = (ROOT / 'release/DP3_V137_CE.img').read_bytes()
    stock, accel = Machine(raw, False), Machine(raw, True)
    seq = lambda word, dt, n: [(word, dt)] * n

    print('gate 1: slow steps are stock')
    steps = seq(DOWN, 500, 1) + seq(DOWN, 30, 12) + seq(DOWN, wa.FAST_TICKS, 6) \
        + seq(UP, 25, 9) + seq(UP, wa.FAST_TICKS, 4)
    pairs = run_pair(stock, accel, 500, 0, 0, steps)
    for i, (s, a) in enumerate(pairs):
        if s != a:
            raise AssertionError(f'slow step {i} differs from stock:\n{s}\n{a}')
    check(True, f'{len(steps)} slow steps: calls, flags, loads, shifts and paint equal stock')
    stock.fixture(500)
    path = []
    for w, dt in steps:
        stock.step(w, dt)
        path.append(stock.state()[0])
    check(path == [p for p, _, _ in model(500, 0, 0, [(dt, 1 if w == DOWN else -1) for w, dt in steps])],
          'stock moves one row per slow step, as the model says')

    print('gate 2 and 3: bursts follow the table and paint the stock window')
    for count, start, word, dt, n in ((500, 0, DOWN, 5, 40), (500, 499, UP, 3, 40),
                                      (500, 250, DOWN, 9, 12), (40, 0, DOWN, 1, 30)):
        d = 1 if word == DOWN else -1
        top0 = max(0, start - 6)
        accel.fixture(count, start, top0)
        want = model(count, start, top0, [(dt, d)] * n)
        moved, full_paints = [], 0
        for i, (wsel, wtop, rows) in enumerate(want):
            before = accel.state()
            key_log, (two_row, full), paint = accel.step(word, dt)
            got = accel.state()
            moved.append(abs(got[0] - before[0]))
            if got != (wsel, wtop):
                raise AssertionError(f'step {i}: state {got}, model {(wsel, wtop)}')
            loads = [e[1] for e in key_log if e[0] == 'load']
            if got[1] != before[1]:
                assert loads == [got[1]], (i, loads, got)
            else:
                assert not loads, (i, loads)
            if rows > 1 and got[0] != before[0]:
                assert full and not two_row, f'step {i}: accelerated step must leave only 0x143 pending'
                ref = reference_paint(accel, *got)
                assert len(ref) == 7 and all('text' in r and 'fill' in r for r in ref.values()), ref
                assert [k for k, r in ref.items() if r['fill'] == ACCENT] == [got[0] - got[1]], ref
                assert [r['text'] for _, r in sorted(ref.items())] == [f'Track {got[1] + k:03d}' for k in range(7)]
                assert screen(paint) == ref, f'step {i}: rows differ from the stock full paint'
                full_paints += 1
        table = [r for _, _, r in want]
        check(table[:13] == [1, 1, 1, 1, 2, 2, 2, 2, 4, 4, 4, 4, 8][:len(table[:13])],
              f'count {count} from {start} {"down" if d > 0 else "up"} every {dt} ticks: '
              f'rows per step {sorted(set(moved) - {0})}, state matches the model at every step, '
              f'{full_paints} accelerated paints equal the stock full paint of their state')

    print('gate 2: pause and reversal reset the streak')
    accel.fixture(500)
    for _ in range(14):
        accel.step(DOWN, 4)
    s0 = accel.state()[0]
    accel.step(DOWN, 4)
    check(accel.state()[0] - s0 == 8, 'fifteenth fast step moves 8 rows')
    s0 = accel.state()[0]
    accel.step(UP, 4)
    check(s0 - accel.state()[0] == 1, 'a fast reversal moves 1 row')
    accel.step(UP, 4)
    s0 = accel.state()[0]
    accel.step(UP, wa.FAST_TICKS)
    check(s0 - accel.state()[0] == 1, f'a step {wa.FAST_TICKS} ticks after the last moves 1 row')
    accel.fixture(500)
    for _ in range(14):
        accel.step(DOWN, 4)
    s0 = accel.state()[0]
    accel.step(DOWN, 200)
    check(accel.state()[0] - s0 == 1, 'a step after a 2 s pause moves 1 row')

    print('gate 4: ends clamp as stock, no wrap')
    for count, word in ((500, DOWN), (500, UP), (9, DOWN), (9, UP)):
        start = max(0, count - 20) if word == DOWN else min(19, count - 1)
        top0 = max(0, start - 6)
        accel.fixture(count, start, top0)
        for _ in range(30):
            accel.step(word, 2)
        end = (count - 1, max(0, count - 7)) if word == DOWN else (0, 0)
        check(accel.state() == end, f'count {count} burst {"down" if word == DOWN else "up"} stops at {end}')
        stock.fixture(count, *end)
        accel_at_end = accel.step(word, 2)
        stock_at_end = stock.step(word, 2)
        check(accel_at_end == stock_at_end and accel.state() == end,
              'a further fast step at the end is byte-identical to stock and does not wrap')

    print('gate 5: short lists')
    for count in range(0, 10):
        for word in (DOWN, UP):
            for start in range(max(count, 1)):
                accel.fixture(count, start, 0)
                stock.fixture(count, start, 0)
                for _ in range(16):
                    accel.step(word, 2)
                    stock.step(word, 30)
                assert accel.state() == stock.state(), (count, word, start, accel.state(), stock.state())
    check(True, 'counts 0 to 9, every start, both directions: burst ends where 16 stock steps end')

    print('gate 6: release image')
    image = Image(raw)
    for number, label, module, address, code in wa.patches():
        off, _ = image.module_region(module, 'code')
        base = image.modules[module]['code_exec']
        check(raw[off + address - base:off + address - base + len(code)] == code,
              f'{number:04d}-{label} is in release/DP3_V137_CE.img')
    print('all wheel acceleration gates pass')


if __name__ == '__main__':
    main()

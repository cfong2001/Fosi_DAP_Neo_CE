#!/usr/bin/env python3
"""Idle repaint gate: the same screen with less work.

Runs Now Playing tick by tick (idle_machine.py) twice: on the image under
test, and on the same image with patches 0350..0354 reverted to their stock
bytes, which is the image before this change. After every tick it compares
both framebuffer surfaces, the display context and the modelled panel (the
rows each flush transferred, applied in order). Scenarios: idle playback with
a short and a scrolling title, a short and a long track, pause and resume,
a seek, a track change, a battery level change, hold, the focus hide and
wake, a theater ground change, the sub-track timebase and seek preview. It
also checks that nothing but the two new routines reads the word 0x030247F4.

Prints instructions, block-reader calls, sector reads and LCD rows per idle
second, before and after.
"""
import json
import re
import struct
import sys
from pathlib import Path

from unicorn import UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_PC

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import idle_machine as im  # noqa: E402

FP_WORD = 0x030247F4
SETUP = 0x03063F10          # sets the store window (context +0x18..+0x23) for each draw
# The store window is per-draw scratch: each draw sets it through SETUP before
# its first pixel. It holds the last draw's rectangle, so it legitimately
# differs when a draw is skipped. Run.tick checks that no pixel is stored in
# a tick before SETUP has run in that tick, so the old window is never used.
WINDOW = slice(0x18, 0x24)
OWN = ((0x03052F90, 0x03052FB8), (0x03056442, 0x03056470), (0x0305C9CE, 0x0305C9FC))
LONG = 'A Much Longer Title That Will Need To Scroll Across The Screen'


def patch_rows():
    rows = []
    for path in sorted(HERE.glob('035*.patch')):
        text = path.read_text()
        field = lambda k: re.search(rf'^{k}: (\S+)', text, re.M)[1]
        rows.append((int(field('module')), int(field('address'), 16),
                     bytes.fromhex(field('expect')), bytes.fromhex(field('replace'))))
    assert len(rows) == 5, rows
    return rows


def before_image(raw):
    """The image under test with this change's five patches reverted."""
    image = im.Image(raw)
    out = bytearray(raw)
    for module, address, expect, replace in patch_rows():
        offset, _ = image.module_region(module, 'code')
        at = offset + address - image.modules[module]['code_exec']
        assert out[at:at + len(replace)] == replace, f'{address:#x} is not patched'
        out[at:at + len(expect)] = expect
    return bytes(out)


class Panel(im.Machine):
    """The machine plus the panel contents the flushes leave."""

    def __init__(self, raw, watch=False):
        super().__init__(raw)
        self.panel = bytearray(320 * 480)
        self.foreign_reads = []
        self.window_set = True
        self.stale_window_stores = 0
        bank = self.r16(im.DCTX)
        for base, length in ((im.TOP + bank * 115200, 115200), (im.LOWER + bank * 38400, 38400)):
            self.u.hook_add(UC_HOOK_MEM_WRITE, self._pixel, begin=base, end=base + length - 1)
        if watch:
            self.u.hook_add(UC_HOOK_MEM_READ, self._read, begin=FP_WORD, end=FP_WORD + 3)

    def _read(self, uc, access, address, size, value, _):
        pc = uc.reg_read(UC_ARM_REG_PC)
        if not any(lo <= pc < hi for lo, hi in OWN):
            self.foreign_reads.append(pc)

    def _pixel(self, uc, access, address, size, value, _):
        if not self.window_set:
            self.stale_window_stores += 1

    def tick(self, playing=True):
        self.window_set = False
        super().tick(playing)

    def _hook(self, uc, addr, size, data):
        if addr == SETUP:
            self.window_set = True
        elif addr == im.LCD_ROWS:
            top, bottom = (uc.reg_read(r) for r in (im.UC_ARM_REG_R1, im.UC_ARM_REG_R3))
            frame, _ = self.screen()
            self.panel[top * 480:(bottom + 1) * 480] = frame[top * 480:(bottom + 1) * 480]
        super()._hook(uc, addr, size, data)

    def state(self):
        frame, context = self.screen()
        return frame, context[:WINDOW.start] + context[WINDOW.stop:], bytes(self.panel)


def battery(m, level):
    """A battery level change as the status code reports it: level cell, then 0x1F."""
    m.w16(0x03023904, level)
    m.post(0x1F)


def hold(m, on):
    m.w8(0x030235BC, 1 if on else 0)
    m.post(0x1F)


def scenario(name):
    """(setup kwargs, list of (ticks, action, playing)) for one scenario."""
    s = {
        'idle short title': ({}, [(700, None, True)]),
        'idle scrolling title': ({'title': LONG}, [(700, None, True)]),
        'idle long track': ({'total_ms': 3_600_000}, [(400, None, True)]),
        'pause and resume': ({}, [(150, None, True),
                                  (1, lambda m: (m.w16(im.PLAY_STATE, 1), m.post(0x43)), False),
                                  (150, None, False),
                                  (1, lambda m: (m.w16(im.PLAY_STATE, 0), m.post(0x43)), True),
                                  (150, None, True)]),
        'silent play state change': ({}, [(150, None, True), (1, lambda m: m.w16(im.PLAY_STATE, 3), True),
                                          (250, None, True)]),
        'seek': ({}, [(120, None, True), (1, lambda m: (m.w32(im.TIME + 4, 150_000), m.post(0x4D)), True),
                      (200, None, True)]),
        'track change': ({}, [(120, None, True),
                              (1, lambda m: (m.u.mem_write(im.TITLE, 'Next Track'.encode('utf-16-le') + b'\0\0'),
                                             m.w32(im.TIME, 199_000), m.w32(im.TIME + 4, 0), m.post(0x39)), True),
                              (250, None, True)]),
        'battery level change': ({}, [(120, None, True), (1, lambda m: battery(m, 2), True), (150, None, True),
                                      (1, lambda m: battery(m, 1), True), (150, None, True)]),
        'hold on and off': ({}, [(120, None, True), (1, lambda m: hold(m, True), True), (150, None, True),
                                 (1, lambda m: hold(m, False), True), (150, None, True)]),
        'focus hide and wake': ({}, [(650, None, True), (1, lambda m: m.wake(), True), (300, None, True)]),
        'theater ground change': ({}, [(120, None, True), (1, lambda m: (m.w16(im.GROUND, 0x7222), m.post(0x39)), True),
                                       (150, None, True), (1, lambda m: (m.w16(im.GROUND, 0x0000), m.post(0x39)), True),
                                       (150, None, True)]),
        'transport cursor': ({}, [(120, None, True), (1, lambda m: (m.w8(im.STATE_A, 2), m.post(0x43)), True),
                                  (150, None, True), (1, lambda m: (m.w8(im.STATE_A, 0), m.post(0x43)), True),
                                  (150, None, True)]),
        'sub-track timebase': ({}, [(1, lambda m: (m.w32(0x030239C4, 1), m.w32(0x030239C8, 30_000),
                                                   m.w32(0x030239CC, 3_000_000)), True), (300, None, True)]),
        'seek preview': ({}, [(120, None, True), (1, lambda m: m.w16(0x030247EA, 6), True), (300, None, True)]),
    }
    return s[name]


SCENARIOS = ('idle short title', 'idle scrolling title', 'idle long track', 'pause and resume',
             'silent play state change', 'seek', 'track change', 'battery level change',
             'hold on and off', 'focus hide and wake', 'theater ground change', 'transport cursor',
             'sub-track timebase', 'seek preview')


def run_pair(before, after, name):
    kwargs, steps = scenario(name)
    machines = [Panel(before), Panel(after, watch=True)]
    for m in machines:
        m.player(**kwargs)
        m.tick()
    work = [dict(instructions=0, reads=0, sectors=0, lcd_rows=0) for _ in machines]
    ticks = 0
    for count, action, playing in steps:
        for _ in range(count):
            for m, w in zip(machines, work):
                if action:
                    action(m)
                got = m.measure(1, playing=playing)
                for k in w:
                    w[k] += got[k]
            ticks += 1
            a, b = (m.state() for m in machines)
            assert a[0] == b[0], f'{name}: framebuffer differs after tick {ticks}'
            assert a[1] == b[1], f'{name}: display context differs after tick {ticks}'
            assert not any(m.stale_window_stores for m in machines), f'{name}: store before window setup'

            assert a[2] == b[2], f'{name}: panel differs after tick {ticks}'
            action = None
    assert not machines[1].foreign_reads, [hex(pc) for pc in machines[1].foreign_reads]
    return ticks, work


def idle_seconds(raw, title, total_ms, seconds, shown=True):
    """Work per idle second. shown=True restamps the focus activity cell each
    tick, as wheel movement does, so the controls stay up; shown=False measures
    after the 5 s focus timeout has hidden them."""
    m = Panel(raw)
    m.player(title=title, total_ms=total_ms)
    m.measure(101 if shown else 700)
    total = dict(instructions=0, reads=0, sectors=0, lcd_rows=0)
    for _ in range(100 * seconds):
        if shown:
            m.w32(im.FOCUS, m.r32(im.CLOCK))
        for k, v in m.measure(1).items():
            total[k] += v
    return {k: v / seconds for k, v in total.items()}


def main():
    raw = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'release/DP3_V137_CE.img').read_bytes()
    before = before_image(raw)
    report = {'parity': {}, 'per_idle_second': {}}
    for name in SCENARIOS:
        ticks, (w0, w1) = run_pair(before, raw, name)
        report['parity'][name] = {'ticks': ticks, 'before': w0, 'after': w1}
        print(f'PASS {name}: {ticks} ticks identical; instructions {w0["instructions"]} -> {w1["instructions"]}')
    for label, title, total, shown in (('controls shown, short title, 4:05 track', 'Short Title', 245_000, True),
                                       ('controls shown, short title, 60:00 track', 'Short Title', 3_600_000, True),
                                       ('controls shown, scrolling title, 4:05 track', LONG, 245_000, True),
                                       ('controls hidden, short title', 'Short Title', 245_000, False),
                                       ('controls hidden, scrolling title', LONG, 245_000, False)):
        b, a = (idle_seconds(img, title, total, 60 if shown else 10, shown) for img in (before, raw))
        per = {k: (round(b[k]), round(a[k])) for k in b}
        report['per_idle_second'][label] = per
        print(f'{label}: ' + ', '.join(f'{k} {x} -> {y}' for k, (x, y) in per.items()))
    out = HERE / 'idle_redraw_report.json'
    out.write_text(json.dumps(report, indent=1) + '\n')
    print(f'ALL PASS; report {out.relative_to(ROOT)}')


if __name__ == '__main__':
    main()

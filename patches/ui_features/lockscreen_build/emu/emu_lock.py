#!/usr/bin/env python3
"""Unicorn emulation of the patched module 31 painter tail (patch 0033).

Maps module 0 code+data and module 31 code from the stock extracted
segments at their load addresses, writes the lock-screen blob at its
scratch link base (the module 31 segment extension base 0x0307EE48)
and the patch 0033 branch bytes at the site, and enters at the site
0x0307E89E with the entry state renderer.md pins: flag 0x2E already
test-cleared, {r4, lr} already popped, r0 = 0x26 + bit 2 of the byte
at 0x030230EC, lr = the painter caller's return address.

Two tiers:
- Tier 1 intercepts DrawImage (0x03063700) and the text routine
  (0x03062CEE) at entry and records their arguments; the display-mode
  function 0x0306316E is observed but runs for real (it is ten
  instructions and touches only the display context struct).
- Tier 2 runs the real text routine, glyph routine, and blitter, with
  a synthetic class-0 font seeded at the font base cell 0x03023280
  (records of 33 bytes, width code 0x88, bitmap rows 0x7F80: bits at
  mask columns 1..8). The stock ink-width helper returns
  min + max + 2 = 11 for the letter glyphs, so they plot 8 bits x 16
  rows = 128 points each; the digit keeps the width-code width 8 and
  plots 7 x 16 = 112 points; 368 points in total for "Ab3". The
  framebuffer store 0x03063E60 and DrawImage are intercepted; plotted
  points are counted at the store. The copy primitive the glyph path
  uses (0x03064314, class-1 sibling 0x030642FE) is also intercepted
  and performed as a plain copy: in the firmware it delegates to the
  copy engine at 0x03067510, which dispatches through the device
  table at 0x03005674, all-zero until boot-time registration, so the
  engine cannot run in a bare map. Its contract at these call sites
  is a synchronous copy of r2 bytes from r0 to r1, and the harness
  performs exactly that; the sources read are the real font records.
"""
import struct
import sys
import hashlib
import os
from pathlib import Path

from unicorn import (Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_LITTLE_ENDIAN,
                     UC_HOOK_CODE, UC_HOOK_MEM_INVALID)
from unicorn.arm_const import *

HERE = Path(__file__).resolve().parent
BLD = HERE.parent
ROOT = BLD.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image

stock = Path(os.environ.get('FOSI_STOCK_IMAGE', ROOT / 'DP3_V137.img')).read_bytes()
if hashlib.sha256(stock).hexdigest() != 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef':
    raise ValueError('stock image does not match the pinned V137 SHA-256')
image = Image(stock)
BLOB = (BLD / 'scratch' / 'lockscreen.bin').read_bytes()
SITE_BYTES = (BLD / 'scratch' / 'site33.bin').read_bytes()

RAM_BASE, RAM_SIZE = 0x03000000, 0x100000
MMIO = [(0x40000000, 0x400000), (0x60000000, 0x400000),
        (0x50000000, 0x1000000), (0xE0000000, 0x100000)]

SITE = 0x0307E89E
EXT_BASE = 0x0307EE48
DRAW_IMAGE = 0x03063700
TEXT_DRAW = 0x03062CEE
MODE_FN = 0x0306316E
GLYPH_FN = 0x03062582
MEMCPY = 0x03064314
MEMCPY1 = 0x030642FE
BLIT = 0x0306333E
FB_STORE = 0x03063E60

SAVEINFO = 0x030232A0
NAME_BUF = 0x030235CE
CTX = 0x0302385C
COLOR_A_CELL = 0x030235B6
COLOR_B_CELL = 0x03023144
STATE_BYTE = 0x030230EC
FILEINFO = 0x03023980
CODEC_PP = 0x0304AD78
FONT_CELL = 0x03023280
FONT = 0x03090000
CODEC_OBJ = 0x03095000
RET_ADDR = 0x030F8000
STACK_TOP = 0x030E8000

CALLEE = [UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
          UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11]


def seg(module, kind, expected_exec):
    if image.modules[module][kind + '_exec'] != expected_exec:
        raise ValueError(f'unexpected module {module} {kind} address')
    off, size = image.module_region(module, kind)
    return stock[off:off + size]


SEGMENTS = [
    (0x03050000, seg(0, 'code', 0x03050000)),
    (0x03004000, seg(0, 'data', 0x03004000)),
    (0x0307D164, seg(31, 'code', 0x0307D164)),
]


class Run:
    def __init__(self, tier, patched=True):
        self.tier = tier
        uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_LITTLE_ENDIAN)
        self.uc = uc
        uc.mem_map(RAM_BASE, RAM_SIZE)
        for base, size in MMIO:
            uc.mem_map(base, size)
        for base, blob in SEGMENTS:
            uc.mem_write(base, blob)
        if patched:
            uc.mem_write(SITE, SITE_BYTES)
            uc.mem_write(EXT_BASE, BLOB)
        uc.mem_write(RET_ADDR, bytes.fromhex('fee7'))  # b .
        self.draw_calls = []
        self.text_calls = []
        self.mode_args = []
        self.glyph_chars = []
        self.memcpy_srcs = []
        self.blit_calls = []
        self.fb_count = 0
        self.fault = None
        self.reached = False
        uc.hook_add(UC_HOOK_CODE, self._code)
        uc.hook_add(UC_HOOK_MEM_INVALID, self._fault)

    def _fault(self, uc, access, address, size, value, _):
        self.fault = (access, address)
        return False

    def _skip(self):
        self.uc.reg_write(UC_ARM_REG_PC, self.uc.reg_read(UC_ARM_REG_LR))

    def _code(self, uc, address, size, _):
        if address == RET_ADDR:
            self.reached = True
            uc.emu_stop()
        elif address == DRAW_IMAGE:
            self.draw_calls.append(uc.reg_read(UC_ARM_REG_R0))
            self._skip()
        elif address == MODE_FN:
            self.mode_args.append(uc.reg_read(UC_ARM_REG_R0))
        elif self.tier == 1 and address == TEXT_DRAW:
            r0 = uc.reg_read(UC_ARM_REG_R0)
            self.text_calls.append({
                'r0': r0, 'r1': uc.reg_read(UC_ARM_REG_R1),
                'r2': uc.reg_read(UC_ARM_REG_R2),
                'r3': uc.reg_read(UC_ARM_REG_R3),
                'desc': list(struct.unpack('<4H', uc.mem_read(r0, 8))),
                'str': read_utf16(uc, uc.reg_read(UC_ARM_REG_R2)),
                'ctx_fg': hw(uc, CTX), 'ctx_bg': hw(uc, CTX + 2),
                'mode_stored': hw(uc, CTX + 0x20),
            })
            self._skip()
        elif self.tier == 2 and address == GLYPH_FN:
            self.glyph_chars.append(uc.reg_read(UC_ARM_REG_R0))
        elif self.tier == 2 and address in (MEMCPY, MEMCPY1):
            src = uc.reg_read(UC_ARM_REG_R0)
            dst = uc.reg_read(UC_ARM_REG_R1)
            n = uc.reg_read(UC_ARM_REG_R2)
            if n == 0x22:
                self.memcpy_srcs.append(src)
            uc.mem_write(dst, bytes(uc.mem_read(src, n)))
            self._skip()
        elif self.tier == 2 and address == BLIT:
            sp = uc.reg_read(UC_ARM_REG_SP)
            self.blit_calls.append({
                'x': uc.reg_read(UC_ARM_REG_R0), 'y': uc.reg_read(UC_ARM_REG_R1),
                'w': uc.reg_read(UC_ARM_REG_R2), 'h': uc.reg_read(UC_ARM_REG_R3),
                'mode': word(uc, sp), 'src': word(uc, sp + 4),
            })
        elif self.tier == 2 and address == FB_STORE:
            self.fb_count += 1
            self._skip()

    def run(self, image_arg):
        uc = self.uc
        sent = {r: 0x5E000000 + 0x111 * (i + 1) for i, r in enumerate(CALLEE)}
        sent[UC_ARM_REG_R4] = 0x44444444
        for r, v in sent.items():
            uc.reg_write(r, v)
        uc.reg_write(UC_ARM_REG_R12, 0x5E000999)
        for i, r in enumerate((UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)):
            uc.reg_write(r, 0xDEAD0001 + i)
        uc.reg_write(UC_ARM_REG_R0, image_arg)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, RET_ADDR | 1)
        uc.emu_start(SITE | 1, RET_ADDR, count=50_000_000)
        self.reached = self.reached or (uc.reg_read(UC_ARM_REG_PC) & ~1) == RET_ADDR
        return {
            'reached': self.reached and self.fault is None,
            'fault': self.fault,
            'sp': uc.reg_read(UC_ARM_REG_SP),
            'callee_ok': all(uc.reg_read(r) == v for r, v in sent.items()),
        }


def hw(uc, addr):
    return struct.unpack('<H', uc.mem_read(addr, 2))[0]


def word(uc, addr):
    return struct.unpack('<I', uc.mem_read(addr, 4))[0]


def read_utf16(uc, addr, maxn=64):
    out = []
    for i in range(maxn):
        v = hw(uc, addr + 2 * i)
        if v == 0:
            break
        out.append(v)
    return ''.join(chr(v) for v in out)


def put_utf16(uc, addr, s):
    for i, ch in enumerate(s):
        uc.mem_write(addr + 2 * i, struct.pack('<H', ord(ch)))
    uc.mem_write(addr + 2 * len(s), b'\x00\x00')


RESULTS = []


def case(name, fn):
    try:
        ok, lines = fn()
    except Exception as exc:  # harness error is a failed case, reported
        ok, lines = False, [f'harness exception: {exc!r}']
    print(f'--- {name} ---')
    for ln in lines:
        print(f'    {ln}')
    print(f'    => {"PASS" if ok else "FAIL"}')
    RESULTS.append(ok)


def checks(lines, *conds):
    ok = True
    for desc, cond in conds:
        lines.append(f'[{"PASS" if cond else "FAIL"}] {desc}')
        ok = ok and cond
    return ok


def base_setup(run, gate, state_bit2):
    uc = run.uc
    uc.mem_write(SAVEINFO + 0x60, bytes([gate]))
    uc.mem_write(STATE_BYTE, bytes([0x04 if state_bit2 else 0x00]))
    put_utf16(uc, NAME_BUF, 'Ab3')
    uc.mem_write(CTX + 0, struct.pack('<H', 0xAAAA))
    uc.mem_write(CTX + 2, struct.pack('<H', 0xBBBB))
    uc.mem_write(COLOR_A_CELL, struct.pack('<H', 0x1111))
    uc.mem_write(COLOR_B_CELL, struct.pack('<H', 0x2222))
    uc.mem_write(CTX + 0x20, struct.pack('<H', 0x0005))  # previous mode value


def main():
    # ---- (a) gate off: stock behaviour only; tier 1, plus stock baseline
    def case_a():
        lines = []
        run = Run(tier=1)
        base_setup(run, gate=0, state_bit2=False)
        out = run.run(0x26)
        stock = Run(tier=1, patched=False)
        base_setup(stock, gate=0, state_bit2=False)
        sout = stock.run(0x26)
        ok = checks(
            lines,
            ('patched run reaches the return pad', out['reached']),
            ('stock baseline reaches the return pad', sout['reached']),
            ('DrawImage called exactly once, r0 = 0x26',
             run.draw_calls == [0x26] and stock.draw_calls == [0x26]),
            ('text routine never called', run.text_calls == []),
            ('mode function never called', run.mode_args == []),
            ('pen colours untouched (0xAAAA / 0xBBBB)',
             hw(run.uc, CTX) == 0xAAAA and hw(run.uc, CTX + 2) == 0xBBBB),
            ('stored mode untouched (5)', hw(run.uc, CTX + 0x20) == 5),
            ('callee-saved registers as stock',
             out['callee_ok'] and sout['callee_ok']),
            ('stack pointer as stock', out['sp'] == STACK_TOP and sout['sp'] == STACK_TOP),
        )
        return ok, lines
    case('(a) SAVEINFO +0x60 == 0: DrawImage only, stock-identical', case_a)

    # ---- (b) gate on, bit 2 clear and set
    def make_b(bit2, image):
        def fn():
            lines = []
            run = Run(tier=1)
            base_setup(run, gate=1, state_bit2=bit2)
            out = run.run(image)
            tc = run.text_calls
            ok = checks(
                lines,
                ('reaches the return pad', out['reached']),
                (f'DrawImage called once with r0 = {image:#x}', run.draw_calls == [image]),
                ('text routine called once (stage 2 gated off)', len(tc) == 1),
            )
            if tc:
                t = tc[0]
                ok = checks(
                    lines,
                    ('r0 == r1 == descriptor pointer', t['r0'] == t['r1']),
                    ('descriptor == {11, 24, 231, 39}', t['desc'] == [11, 24, 231, 39]),
                    ('r2 == name buffer 0x030235CE', t['r2'] == NAME_BUF),
                    ('r3 == 0 (left aligned)', t['r3'] == 0),
                    ('string at r2 is the seeded title', t['str'] == 'Ab3'),
                    ('pen colours are Display values during the call (0x1111 / 0x2222)',
                     t['ctx_fg'] == 0x1111 and t['ctx_bg'] == 0x2222),
                    ('mode stored == 1 during the call', t['mode_stored'] == 1),
                ) and ok
            ok = checks(
                lines,
                ('mode bracket: set(1) then set(saved=5)', run.mode_args == [1, 5]),
                ('stored mode restored to 5', hw(run.uc, CTX + 0x20) == 5),
                ('pen colours restored (0xAAAA / 0xBBBB)',
                 hw(run.uc, CTX) == 0xAAAA and hw(run.uc, CTX + 2) == 0xBBBB),
                ('callee-saved registers restored', out['callee_ok']),
                ('stack pointer restored', out['sp'] == STACK_TOP),
            ) and ok
            return ok, lines
        return fn
    case('(b1) +0x60 == 1, bit 2 clear: title call contract', make_b(False, 0x26))
    case('(b2) +0x60 == 1, bit 2 set: image 0x27, same contract', make_b(True, 0x27))

    # ---- (d) stage 2 formatting, tier 1 intercept of the text routine
    def stage2_setup(run, state, latched, total, obj_ptr, live):
        uc = run.uc
        uc.mem_write(FILEINFO + 0x44, struct.pack('<I', state))
        uc.mem_write(FILEINFO + 0x48, struct.pack('<I', latched))
        uc.mem_write(FILEINFO + 0x4C, struct.pack('<I', total))
        uc.mem_write(CODEC_PP, struct.pack('<I', obj_ptr))
        if obj_ptr:
            uc.mem_write(obj_ptr + 0, struct.pack('<I', total))
            uc.mem_write(obj_ptr + 4, struct.pack('<I', live))

    def case_d():
        lines = []
        run = Run(tier=1)
        base_setup(run, gate=1, state_bit2=False)
        # latched 60,000 ms; live 814,000 -> elapsed 754,000 ms = 12:34
        # total 3,427,000 -> segment total 3,367,000 ms = 56:07
        stage2_setup(run, 1, 60000, 3427000, CODEC_OBJ, 814000)
        out = run.run(0x26)
        tc = run.text_calls
        ok = checks(lines, ('reaches the return pad', out['reached']),
                    ('text routine called twice', len(tc) == 2))
        if len(tc) == 2:
            t = tc[1]
            ok = checks(
                lines,
                ('stage 2 descriptor == {11, 40, 231, 55}', t['desc'] == [11, 40, 231, 55]),
                ('stage 2 r0 == r1, r3 == 0', t['r0'] == t['r1'] and t['r3'] == 0),
                ('stage 2 r2 == the routine time buffer in the blob',
                 EXT_BASE <= t['r2'] < EXT_BASE + len(BLOB)),
                ('formatted text == "12:34 / 56:07"', t['str'] == '12:34 / 56:07'),
            ) and ok
        return ok, lines
    case('(d) stage 2: elapsed/total formatted from seeded position words', case_d)

    def case_d2():
        lines = []
        ok_all = True
        for name, kw in [('state +0x44 == 0', dict(state=0, latched=60000, total=3427000, obj_ptr=CODEC_OBJ, live=814000)),
                         ('codec object pointer null', dict(state=1, latched=60000, total=3427000, obj_ptr=0, live=0)),
                         ('live behind latch clamps to 0:00', None)]:
            run = Run(tier=1)
            base_setup(run, gate=1, state_bit2=False)
            if kw is None:
                stage2_setup(run, 1, 60000, 3427000, CODEC_OBJ, 30000)
                run.run(0x26)
                good = (len(run.text_calls) == 2 and
                        run.text_calls[1]['str'] == '0:00 / 56:07')
            else:
                stage2_setup(run, **kw)
                run.run(0x26)
                good = len(run.text_calls) == 1
            lines.append(f'[{"PASS" if good else "FAIL"}] {name}: text calls = {len(run.text_calls)}'
                         + (f', stage 2 text = {run.text_calls[1]["str"]!r}' if len(run.text_calls) == 2 else ''))
            ok_all = ok_all and good
        return ok_all, lines
    case('(d2) stage 2 gates: inactive state, null codec object, negative elapsed', case_d2)

    # ---- (c) tier 2: the real text path renders the seeded string
    def case_c():
        lines = []
        run = Run(tier=2)
        base_setup(run, gate=1, state_bit2=False)
        uc = run.uc
        font = bytearray(256 * 33 + 2)   # record stride is 33 bytes
        for c in range(256):
            rec = c * 33
            for row in range(16):
                font[rec + 2 * row] = 0x80
                font[rec + 2 * row + 1] = 0x7F  # halfword 0x7F80: columns 1..7 set
            font[rec + 0x21] = 0x88             # width code: width 8
        uc.mem_write(FONT, bytes(font))
        uc.mem_write(FONT_CELL, struct.pack('<I', FONT))
        out = run.run(0x26)
        want_srcs = {FONT + 0x41 * 33, FONT + 0x62 * 33, FONT + 0x33 * 33}
        blits = run.blit_calls
        ok = checks(
            lines,
            ('reaches the return pad with no memory fault', out['reached']),
            ('DrawImage called once with r0 = 0x26', run.draw_calls == [0x26]),
            ('mode bracket ran (set 1, restore 5)', run.mode_args == [1, 5]),
            ('glyph routine entered once per character, in order "Ab3"',
             run.glyph_chars == [0x41, 0x62, 0x33]),
            ('glyph record copies read exactly the three seeded records',
             set(run.memcpy_srcs) == want_srcs and len(run.memcpy_srcs) >= 3),
            ('one mode-1 blit per glyph', len(blits) == 3 and all(b['mode'] == 1 for b in blits)),
            ('blits at y = 24 (descriptor y_top), heights 16',
             all(b['y'] == 24 and b['h'] == 16 for b in blits)),
            ('blit x starts at 11 and advances by the measured widths',
             len(blits) == 3 and [b['x'] for b in blits] == [11, 22, 33]),
            ('blit widths: 11, 11 (ink width of the letters), 8 (width code)',
             [b['w'] for b in blits] == [11, 11, 8]),
            ('framebuffer store plotted every set bit in the blit boxes: 128 + 128 + 112 = 368 points',
             run.fb_count == 368),
        )
        lines.append(f'    glyph chars: {[hex(c) for c in run.glyph_chars]}, '
                     f'memcpy(0x22) calls: {len(run.memcpy_srcs)}, '
                     f'blits: {[(b["x"], b["y"], b["w"], b["h"]) for b in blits]}, '
                     f'fb points: {run.fb_count}')
        return ok, lines
    case('(c) tier 2: real renderer consumes and plots the seeded title', case_c)

    print()
    print('ALL PASS' if all(RESULTS) else 'SOME CASES FAILED')
    return 0 if all(RESULTS) else 1


if __name__ == '__main__':
    raise SystemExit(main())

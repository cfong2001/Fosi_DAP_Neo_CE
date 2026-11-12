#!/usr/bin/env python3
"""Emulator gates for the focus-mode variant (auto-hide controls).

Builds the composed variant (default 32 + vorbis75 + theater 5 +
focus 12, tail = theater 676 B + focus payload) in a temp dir and
runs the real patched code under Unicorn. Only the established
leaf models are used: the file-read callback and the overlay
loader serve module 18's decoder (as in the theater lifecycle
test), the pixel store executes for real and is recorded (as in
the design refresh v4 test), and the text layer is modelled at
its two painter-facing entries: the renderer is recorded and
returned (the painter ignores its return value at both call
sites), and the title measure is recorded and returns a fit
width (its glyph metrics come from a boot-loaded font resource
the harness does not stage; what the gates assert is the rect
the painter's stack carries into the call, which is the rect
the draw and marquee code then consume).

Gates:
  0  wiring: every focus hook site in the variant image is a BL
     to the assembled stub; the same sites in the stock image are
     the displaced stock calls.
  1  tick and key: the tick stub posts the displaced 0x40, hides
     at exactly 500 idle ticks (100 Hz clock), treats a wheel
     total change as activity, and stays hidden without reposting;
     the key stub passes the displaced function's result through
     while visible, and while hidden wakes, posts 0x39 + 0x3B,
     and swallows the key (neither key handler is entered, the
     wrapper's saved registers are restored).
  2  painter, hidden: the gated segment event bits are not
     consumed, no transport or progress drawing happens (no
     segment fill calls, no draw calls for the transport ids or
     in the vacated bands), the artwork request issues with the
     grown geometry (the four request globals read back as box
     190x190, dest (25, 8)), and the title and artist renderer
     calls carry the shifted rects (tops 232 and 257). A stock
     control run shows the same paint with the segments drawing.
     The request's own probe/open path needs a mounted card
     volume, which the established harnesses do not model, so
     the request is observed up to the geometry write (its head,
     before the open) and the drawing side of the grown geometry
     is proven at setup level in gate 4.
  3  wake restores: after a wake key, the next paint re-issues
     the artwork at stock geometry, the transport segment draws
     and consumes its event bit, the progress track fill appears,
     and the text rects are back at the stock positions.
  4  theater interplay: with the focus geometry preset (as the
     geometry stub writes it), setup re-arms theater sampling
     with rows_needed latched from the grown scaled height (114
     rows -> 38 sampled rows, the theater 48-row cap not yet
     binding at this size but the latch value following the new
     height), and the finalize writes the port-computed derived
     cell over those rows. Stock-geometry control: 86 -> 29.
"""
import hashlib
import os
import runpy
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                               UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_SP,
                               UC_ARM_REG_LR, UC_ARM_REG_PC)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'tools'))
sys.path.insert(0, str(HERE))
import fosi_paths  # noqa: E402
from rknano_image import Image  # noqa: E402
import build_focus  # noqa: E402

STOCK = (REPO / 'DP3_V137.img').read_bytes()
STOCK_SHA = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
assert hashlib.sha256(STOCK).hexdigest() == STOCK_SHA, 'stock SHA gate'

# FOCUS_FULL_IMAGE=path runs every gate on the full build instead of the
# standalone theater variant; there the payload sits at 0x0307C1DC, where
# the full build's tail places it (patches/full/build/build_tail.py).
FULL_IMAGE = os.environ.get('FOCUS_FULL_IMAGE')
if FULL_IMAGE:
    build_focus.FOCUS_BASE = 0x0307C1DC
PAYLOAD, ENTRIES = build_focus.assemble()
FOCUS = {name: addr for name, addr in ENTRIES.items()}
STATE = 0x03023484
TSTATE = 0x03023468
CTX = 0x03026CA0
BGCELL = 0x03004400
SAVEINFO = 0x030232A0
EVENTS = 0x03023CF8
CLOCK = 0x03023298
WHEEL = 0x0302317C
GLOBALS = (0x0302598C, 0x03025990, 0x03025994, 0x03025998)
PAINTER = 0x0307EF4E
WRAPPER = 0x03080AF4
KEYFN = 0x03061B16
HANDLER_MAIN = 0x030800BE
HANDLER_ALT = 0x030809A8
STORE = 0x03063E60
DMA = 0x03053F5E
FILL = 0x030632FA
RENDER = 0x03062CEE
MEASURE = 0x0306295A
DRAWAT = 0x0306354A
KEYED = 0x03063A08
FILEREAD = 0x03058FA8
OVERLAY = 0x03067870
DSTRUCT = 0x030238D0
END = 0x030EF000

fixture = runpy.run_path(str(REPO / 'patches' / 'theater' / 'research'
                             / 'probe_jpeg.py'))
JPEG = fixture['JPEG']


# ------------------------------------------------ independent port

def port_average(rows):
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
    return (((r * 31 + 127) // 255) << 11
            | ((g * 63 + 127) // 255) << 5
            | ((b * 31 + 127) // 255))


def port_derived_dark(rows):
    avg = port_average(rows)
    mixed = tuple((a * 45 + 50) // 100 for a in avg)
    return port_rgb565(*mixed), avg, mixed


# ------------------------------------------------ variant build

def build_variant(tmp):
    ecp = fosi_paths.ecpatch_dir(REPO)
    if ecp is None:
        raise SystemExit('ecpatch inputs not found; set FOSI_ECPATCH_DIR')
    out = Path(tmp) / 'focus.img'
    r = subprocess.run(
        [sys.executable, str(REPO / 'patches' / 'framework' / 'build.py'),
         '--input', str(REPO / 'DP3_V137.img'),
         '--manifest', str(HERE / 'manifest.txt'),
         '--ecpatch-dir', str(ecp),
         '--tail', str(HERE / 'focus_tail.bin'),
         '--output', str(out)], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit('variant build failed: ' + r.stderr)
    return out.read_bytes()


# ------------------------------------------------ emulator harness

class Machine:
    def __init__(self, raw, modules=(0, 18, 19, 27)):
        self.raw = raw
        self.im = Image(raw)
        self.u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.u.mem_map(0x03000000, 0x500000)
        self.u.mem_map(0x01000000, 0x200000)   # decoder overlay window
        self.u.mem_map(0xE000E000, 0x1000)
        for idx in modules:
            m = self.im.modules[idx]
            for kind in ('code', 'data'):
                off, size = self.im.module_region(idx, kind)
                if size:
                    self.u.mem_write(m[kind + '_exec'],
                                     raw[off:off + size])
        self.cursor = 0
        self.dma = []           # (src, dst, n, lr) staging copies
        self.stores = []        # (col, row, colour, fill_tag)
        self.fills = []         # (x0, y0, x1, y1, colour)
        self.renders = []       # (rect tuple, string)
        self.measures = []      # (rect tuple, string) at measure entry
        self.draws = []         # (fn, id, x, y) image draw calls
        self.counts = {'keyfn': 0, 'main': 0, 'alt': 0}
        self.entries = {e['id']: e for e in self.im.images()}
        self.u.hook_add(UC_HOOK_CODE, self._hook)
        self.u.hook_add(UC_HOOK_MEM_WRITE, self._record_write)

    def _record_write(self,uc,access,address,size,value,user):
        bank=self.r16(0x030238B8)
        for base,rows,y0 in ((0x030065A8+bank*115200,240,0),
                             (0x0306F224+bank*38400,80,240)):
            if base<=address and address+size<=base+rows*480:
                for offset in range(0,size,2):
                    pixel=(address+offset-base)//2
                    self.stores.append((pixel%240,pixel//240+y0,
                                        (value>>(offset*8))&0xFFFF,len(self.fills)))
                break

    # -- memory helpers
    def w32(self, a, v): self.u.mem_write(a, struct.pack('<I', v))
    def w16(self, a, v): self.u.mem_write(a, struct.pack('<H', v))
    def w8(self, a, v): self.u.mem_write(a, bytes([v]))
    def r32(self, a): return struct.unpack('<I', self.u.mem_read(a, 4))[0]
    def r16(self, a): return struct.unpack('<H', self.u.mem_read(a, 2))[0]
    def r8(self, a): return self.u.mem_read(a, 1)[0]

    def set_event(self, n):
        a = EVENTS + (n // 32) * 4
        self.w32(a, self.r32(a) | (1 << (n % 32)))

    def clear_event(self, n):
        a = EVENTS + (n // 32) * 4
        self.w32(a, self.r32(a) & ~(1 << (n % 32)))

    def event(self, n):
        return bool(self.r32(EVENTS + (n // 32) * 4) >> (n % 32) & 1)

    def hidden(self):
        return self.r8(STATE + 8)

    def _hook(self, uc, addr, size, user):
        if addr == 0x0306D13C and FULL_IMAGE:
            # Theater samples the source before the display-only contrast mask.
            width = uc.reg_read(UC_ARM_REG_R2)
            ptr = struct.unpack('<I', uc.mem_read(uc.reg_read(UC_ARM_REG_SP) + 4, 4))[0]
            if not hasattr(self, 'art_source_rows'):
                self.art_source_rows = []
            self.art_source_rows.append(struct.unpack(f'<{width}H', uc.mem_read(ptr, width * 2)))
        if addr == DMA:
            src, dst, n = (uc.reg_read(r) for r in
                           (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2))
            self.dma.append((src, dst, n, uc.reg_read(UC_ARM_REG_LR)))
            if n:
                uc.mem_write(dst, bytes(uc.mem_read(src, n)))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif addr == FILL:
            sp = uc.reg_read(UC_ARM_REG_SP)
            self.fills.append(tuple(
                uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                         UC_ARM_REG_R2, UC_ARM_REG_R3))
                + (struct.unpack('<I', uc.mem_read(sp, 4))[0],))
        elif addr == MEASURE:
            sp = uc.reg_read(UC_ARM_REG_SP)
            rect = struct.unpack('<4H', uc.mem_read(sp + 0x10, 8))
            sptr = uc.reg_read(UC_ARM_REG_R0)
            chars = []
            for i in range(48):
                ch = struct.unpack('<H', uc.mem_read(sptr + 2 * i, 2))[0]
                if ch == 0:
                    break
                chars.append(ch)
            self.measures.append((rect, ''.join(map(chr, chars))))
            uc.reg_write(UC_ARM_REG_R0, 100)   # fits: below the 238 gate
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif addr in (DRAWAT, KEYED):
            self.draws.append((addr, uc.reg_read(UC_ARM_REG_R0),
                               uc.reg_read(UC_ARM_REG_R1),
                               uc.reg_read(UC_ARM_REG_R2)))
        elif addr == RENDER:
            rect = struct.unpack('<4H', uc.mem_read(
                uc.reg_read(UC_ARM_REG_R0), 8))
            sptr = uc.reg_read(UC_ARM_REG_R2)
            chars = []
            for i in range(48):
                ch = struct.unpack('<H', uc.mem_read(sptr + 2 * i, 2))[0]
                if ch == 0:
                    break
                chars.append(ch)
            self.renders.append((rect, ''.join(map(chr, chars))))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif addr == FILEREAD:
            dest, count, handle = (uc.reg_read(r) for r in
                                   (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                    UC_ARM_REG_R2))
            assert handle == 1 and count <= 4096
            block = JPEG[self.cursor:self.cursor + count]
            self.cursor += len(block)
            if block:
                uc.mem_write(dest, block)
            uc.reg_write(UC_ARM_REG_R0, len(block))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif addr == OVERLAY:
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
        elif addr == KEYFN:
            self.counts['keyfn'] += 1
        elif addr == HANDLER_MAIN:
            self.counts['main'] += 1
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif addr == HANDLER_ALT:
            self.counts['alt'] += 1
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def call(self, addr, r0=0, r1=0, sp=0x030F0000):
        u = self.u
        for reg, val in ((UC_ARM_REG_R0, r0), (UC_ARM_REG_R1, r1),
                         (UC_ARM_REG_SP, sp), (UC_ARM_REG_LR, END | 1)):
            u.reg_write(reg, val)
        u.emu_start(addr | 1, END, count=60000000)
        assert u.reg_read(UC_ARM_REG_PC) == END, \
            f'call to {addr:#x} did not return cleanly'
        return u.reg_read(UC_ARM_REG_R0)

    # -- painter driver ------------------------------------------------
    def stage(self, ids):
        # The resource arena must not overlap any loaded module:
        # module 18's code window starts at 0x03080B54, so the
        # 0x03080000 arena the v4 harness used (it never executed
        # module 18) would overwrite the artwork engine here.
        RES, RES_CELL = 0x030A0000, 0x0302328C
        self.w32(RES_CELL, RES)
        off = 0x2000
        for rid in ids:
            e = self.entries[rid]
            data = self.raw[e['data_offset']:e['data_offset'] + e['size']]
            desc = struct.pack('<4H2I', e['width'], e['height'], 0, 0,
                               e['size'], off)
            self.u.mem_write(RES + 0x20 + rid * 16, desc)
            self.u.mem_write(RES + off, data)
            off += e['size'] + 0x40

    def pool(self, at, disp):
        """Resolve an ldr-literal pool value from the loaded image."""
        tgt = (at & ~3) + 4 + disp
        off, _ = self.im.module_region(27, 'code')
        rel = tgt - self.im.modules[27]['code_exec']
        return struct.unpack_from('<I', self.raw, off + rel)[0]

    def setup_player(self, title='Focus Title', artist='Focus Artist'):
        self.w8(SAVEINFO + 0x1A, 0)          # artwork view
        self.w8(SAVEINFO + 0x61, 0)          # play mode: repeat all
        self.w8(SAVEINFO + 0x2D8, 0)         # dark theme
        self.w8(0x0302314A, 0)               # transport state A
        self.w8(0x0302314B, 0)               # transport state B
        self.w16(0x03023924, 1)              # play state: playing
        self.w32(0x03023980 + 0x44, 0)       # request gate open
        self.w32(0x0304AD78, 0x0304C100)     # elapsed-time struct ptr
        self.u.mem_write(0x0304C100, struct.pack('<II', 46000, 45000)
                         + bytes(0x38))      # total, elapsed (ms)
        src = self.pool(0x0307F9CC, 0x108)   # title source field
        self.u.mem_write(src, title.encode('utf-16-le') + b'\0\0')
        self.u.mem_write(0x0304AF24 + 0x15E,
                         artist.encode('utf-16-le') + b'\0\0')
        self.stage(sorted(self.entries))

    def paint(self, events):
        for n in events:
            self.set_event(n)
        self.stores.clear()
        self.fills.clear()
        self.renders.clear()
        self.measures.clear()
        self.draws.clear()
        self.call(PAINTER)


# ------------------------------------------------ gate 0: wiring

DISPLACED = {
    'focus-init-reset-hook': 0x0306723C,
    'focus-service-tick-hook': 0x0306723C,
    'focus-key-hook': 0x03061B16,
    'focus-geometry-hook': 0x03083A90,
    'focus-gate-status-1f': 0x03067258,
    'focus-gate-progress-41': 0x03067258,
    'focus-gate-progress-40': 0x03067258,
    'focus-gate-progress-4d': 0x03067258,
    'focus-gate-transport-43': 0x03067258,
    'focus-gate-volume-19a': 0x03067258,
    'focus-title-shift-hook': 0x0306295A,
    'focus-artist-shift-hook': 0x03062CEE,
}


def bl_target(raw, site):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
    im = Image(raw)
    off, _ = im.module_region(27, 'code')
    rel = site - im.modules[27]['code_exec']
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    ins = next(md.disasm(raw[off + rel:off + rel + 4], site))
    assert ins.mnemonic == 'bl', (site, ins.mnemonic)
    return int(ins.op_str.lstrip('#'), 16)


def gate0(variant):
    for _num, name, site, target, _note in build_focus.PATCH_DEFS:
        got = bl_target(variant, site)
        assert got == FOCUS[target], (name, hex(got), target)
        want = bl_target(STOCK, site)
        assert want == DISPLACED[name], (name, hex(want))
    print('PASS gate 0: all 12 hook sites in the variant are BLs to '
          'the focus stubs; the stock sites are the displaced calls')


# ------------------------------------------------ gate 1: tick + key

def gate1(variant):
    m = Machine(variant, modules=(0, 27))
    # reset stub: Init's displaced post runs, state initialised
    m.w32(CLOCK, 777)
    m.w32(WHEEL, 55)
    m.w8(STATE + 8, 1)                       # dirty the flag first
    m.call(FOCUS['focus_reset'], r0=0x39)
    assert m.event(0x39), 'reset did not perform the displaced post'
    assert m.hidden() == 0, 'reset left the hidden flag set'
    assert m.r32(STATE) == 777 and m.r32(STATE + 4) == 55, \
        'reset did not stamp activity / snapshot the wheel'
    print('  reset: post(0x39) performed, hidden cleared, '
          'last_tick=777, wheel_seen=55')

    # tick: threshold is exactly 500 ticks
    m.w32(STATE, 1000)
    m.w32(STATE + 4, 7)
    m.w32(WHEEL, 7)
    m.w32(CLOCK, 1499)
    m.call(FOCUS['focus_tick'], r0=0x40)
    assert m.event(0x40), 'tick stub did not perform the displaced post'
    assert m.hidden() == 0, 'hid before the threshold (499 ticks)'
    m.w32(CLOCK, 1500)
    m.call(FOCUS['focus_tick'], r0=0x40)
    assert m.hidden() == 1, 'did not hide at 500 idle ticks'
    assert m.event(0x39) and m.event(0x3B), \
        'hide did not post the repaint pair'
    m.clear_event(0x39)
    m.clear_event(0x3B)
    m.w32(CLOCK, 9999)
    m.call(FOCUS['focus_tick'], r0=0x40)
    assert m.hidden() == 1 and not m.event(0x39) and not m.event(0x3B), \
        'tick stub reposted or cleared state while hidden'
    print('  tick: no hide at 499 ticks, hide at 500 (5 s at the '
          '100 Hz clock), repaint pair posted once, frozen while hidden')

    # tick: a wheel total change counts as activity
    m.w8(STATE + 8, 0)
    m.w32(STATE, 1000)
    m.w32(STATE + 4, 7)
    m.w32(WHEEL, 9)
    m.w32(CLOCK, 6000)
    m.call(FOCUS['focus_tick'], r0=0x40)
    assert m.hidden() == 0 and m.r32(STATE) == 6000 \
        and m.r32(STATE + 4) == 9, 'wheel movement did not restamp'
    print('  tick: wheel total change restamped activity at 6000')

    # key, visible: pass-through with the displaced result. The
    # reference value is whatever the displaced function itself
    # returns on an identical machine; the stub must return it
    # unchanged.
    def keyed_machine():
        mm = Machine(variant, modules=(0, 27))
        mm.w32(0x03023284, 0x0304C000)       # per-key state struct
        mm.u.mem_write(0x0304C000, bytes(0x100))
        mm.w16(0x03023924, 1)
        mm.w32(CLOCK, 4242)
        mm.w32(WHEEL, 3)
        return mm
    ref = keyed_machine()
    want = ref.call(KEYFN, r0=0)
    m2 = keyed_machine()
    ret = m2.call(FOCUS['focus_key'], r0=0)
    assert ret == want, \
        f'pass-through returned {ret:#x}, function returns {want:#x}'
    assert m2.counts['keyfn'] == 1, 'displaced function not called'
    assert m2.r32(STATE) == 4242 and m2.hidden() == 0
    print(f'  key (visible): displaced function ran once, its '
          f'result {want:#x} returned unchanged, activity restamped')

    # key, hidden: wake and swallow through the real wrapper
    m2.w8(STATE + 8, 1)
    m2.clear_event(0x39)
    m2.clear_event(0x3B)
    m2.w32(CLOCK, 5000)
    sp0 = 0x030F0000
    m2.u.reg_write(UC_ARM_REG_R4, 0xCAFECAFE)
    m2.call(WRAPPER, r0=0, sp=sp0)
    assert m2.counts['keyfn'] == 2, 'wake key skipped the function'
    assert m2.counts['main'] == 0 and m2.counts['alt'] == 0, \
        'a key handler ran for a swallowed key'
    assert m2.hidden() == 0 and m2.event(0x39) and m2.event(0x3B), \
        'wake did not clear the state or post the repaint pair'
    assert m2.u.reg_read(UC_ARM_REG_R4) == 0xCAFECAFE, \
        'wrapper saved r4 not restored on the swallow path'
    assert m2.u.reg_read(UC_ARM_REG_SP) == sp0, 'stack not balanced'
    print('  key (hidden): woke, posted the repaint pair, neither '
          'handler entered, r4 and sp restored: the key was swallowed')

    # key, visible through the wrapper: handler reached normally
    m2.call(WRAPPER, r0=0, sp=sp0)
    assert m2.counts['main'] == 1 and m2.counts['keyfn'] == 3, \
        'visible key did not flow to the main handler'
    print('  key (visible, wrapper): main handler entered as stock')
    print('PASS gate 1: tick threshold, wheel activity, key '
          'pass-through and wake-and-swallow')


# ------------------------------------------------ gates 2+3: painter

GATED = (0x1F, 0x41, 0x40, 0x4D, 0x43, 0x19A)


TRANSPORT_IDS = set(range(155, 182)) | set(range(286, 290))


def gate2(variant):
    m = Machine(variant)
    m.setup_player()
    m.w8(STATE + 8, 1)                       # hidden
    m.paint({0x39} | set(GATED))
    for n in GATED:
        assert m.event(n), f'gated event {n:#x} was consumed'
    rects = [f[:4] for f in m.fills]
    if FULL_IMAGE:
        rects = [r for r in rects if not (25 <= r[0] <= r[2] <= 214 and 8 <= r[1] <= r[3] <= 197)]
    assert rects == [], f'segment fill calls leaked: {rects}'
    bad = [d for d in m.draws
           if d[1] in TRANSPORT_IDS or d[3] >= 254]
    assert not bad, f'transport/progress draw calls leaked: {bad}'
    got = tuple(m.r32(a) for a in GLOBALS)
    assert got == (190, 190, 25, 8), f'request globals {got}'
    by_text = {text: rect for rect, text in m.renders}
    assert by_text.get('Focus Title') == (0, 232, 239, 247), \
        f"title rect {by_text.get('Focus Title')}"
    assert by_text.get('Focus Artist') == (0, 257, 239, 272), \
        f"artist rect {by_text.get('Focus Artist')}"
    measured = {text: rect for rect, text in m.measures}
    assert measured.get('Focus Title') == (0, 232, 239, 247), \
        f"rect at the measure call {measured.get('Focus Title')}"
    print(f'  hidden paint: gated bits {", ".join(hex(n) for n in GATED)} '
          f'all still pending; zero segment fills; draw calls '
          f'{[(hex(f), i, x, y) for f, i, x, y in m.draws]}; request '
          f'globals (190, 190, 25, 8); title top 232, artist top 257')
    # stock control: the same paint on the stock image draws the
    # segments (bits consumed, erase and track fills present)
    s = Machine(STOCK)
    s.setup_player()
    s.paint({0x39} | set(GATED))
    srects = [f[:4] for f in s.fills]
    assert not s.event(0x43), 'stock control consumed nothing?'
    assert (53, 5, 78, 24) in srects and (40, 254, 201, 268) in srects, \
        f'stock control fills unexpected: {srects}'
    assert any(d[1] in TRANSPORT_IDS and d[3] == 275 for d in s.draws), \
        'stock control drew no transport row'
    sby = {text: rect for rect, text in s.renders}
    assert sby.get('Focus Title') == (0, 198, 239, 213)
    assert sby.get('Focus Artist') == (0, 223, 239, 238)
    print('  stock control: 0x43 consumed, transport erase and '
          'progress track fills present, transport draws at y=275, '
          'title top 198, artist top 223')
    print('PASS gate 2: hidden paint suppresses the segments, '
          'grows the art request, shifts the text')
    return m


def gate3(m):
    # wake through the real wrapper (hidden set by gate 2's paint)
    assert m.hidden() == 1
    m.call(WRAPPER, r0=0)
    assert m.hidden() == 0 and m.counts['main'] == 0, 'wake key acted'
    # The wake paint is the full repaint the key stub posted; it
    # consumes the very segment bits the hidden period left
    # pending, which is the stock choreography for free.
    m.paint({0x39})
    got = tuple(m.r32(a) for a in GLOBALS)
    expected_x = 48 if FULL_IMAGE else 23
    assert got == (144, 144, expected_x, 36), f'restored globals {got}'
    by_text = {text: rect for rect, text in m.renders}
    assert by_text.get('Focus Title') == (0, 198, 239, 213)
    assert by_text.get('Focus Artist') == (0, 223, 239, 238)
    measured = {text: rect for rect, text in m.measures}
    assert measured.get('Focus Title') == (0, 198, 239, 213)
    assert not m.event(0x43), 'transport bit not consumed on wake paint'
    rects = [f[:4] for f in m.fills]
    assert (40, 254, 201, 268) in rects, 'progress track not redrawn'
    assert any(d[1] in TRANSPORT_IDS and d[3] == 275 for d in m.draws), \
        'transport row did not redraw'
    row = [s for s in m.stores if 275 <= s[1] <= 307]
    assert len(row) > 1000, f'transport row stores missing: {len(row)}'
    print(f'  wake paint: globals back to {got}, text '
          f'rects stock, 0x43 consumed, progress track fill '
          f'present, {len(row)} transport stores')
    print('PASS gate 3: wake restores the full stock layout')


# ------------------------------------------------ gate 4: theater

def gate4(variant):
    def run(box, dest):
        m = Machine(variant, modules=(0, 27, 18, 19))
        for a, v in zip(GLOBALS, (box, box, dest[0], dest[1])):
            m.w32(a, v)
        m.w32(0x030259DC, 1)
        m.w16(BGCELL, 0xBEEF)
        assert m.call(0x0308389E, r0=1, r1=0) == 1
        st = m.u.mem_read(TSTATE, 28)
        assert m.r16(BGCELL) == 0x10A2, 'setup did not restore default'
        assert st[25] == 1, f'sampling not re-armed: flags {st[25]}'
        scaled_h = m.r16(CTX + 0x18)
        for _ in range(scaled_h):
            m.call(0x03083B36)
        page = struct.unpack('<H', m.u.mem_read(0x030238B8, 2))[0]
        assert page == 0
        st = m.u.mem_read(TSTATE, 28)
        needed = struct.unpack_from('<H', st, 22)[0]
        rows = []
        for i in range(needed):
            y = dest[1] + i
            base = 0x030065A8 + y * 480 + dest[0] * 2
            rows.append(struct.unpack(f'<{box}H',
                                      m.u.mem_read(base, box * 2)))
        if FULL_IMAGE:
            rows = m.art_source_rows[:needed]
        expected, avg, mixed = port_derived_dark(rows)
        cell = m.r16(BGCELL)
        print(f'  box {box} dest {dest}: scaled height {scaled_h}, '
              f'rows_needed {needed}, avg {avg} mixed {mixed} '
              f'expected {expected:#06x} actual {cell:#06x}')
        assert cell == expected, (cell, expected)
        st = m.u.mem_read(TSTATE, 28)
        assert st[25] == 7 and m.event(0x39), 'finalize incomplete'
        return needed
    n_focus = run(190, (25, 8))
    n_stock = run(144, (48 if FULL_IMAGE else 23, 36))
    assert n_focus == 38 and n_stock == 29, (n_focus, n_stock)
    print('PASS gate 4: geometry change re-arms theater sampling; '
          'rows_needed follows the new scaled height (114 -> 38 '
          'vs 86 -> 29) and the derived cell matches the port')


def main():
    tmp = tempfile.mkdtemp(prefix='neo-focus-test-')
    variant = (Path(FULL_IMAGE).read_bytes() if FULL_IMAGE
               else build_variant(tmp))
    print(f'variant image sha256 {hashlib.sha256(variant).hexdigest()}')
    gate0(variant)
    gate1(variant)
    m = gate2(variant)
    gate3(m)
    gate4(variant)
    print('ALL FOCUS GATES PASS')


if __name__ == '__main__':
    main()
